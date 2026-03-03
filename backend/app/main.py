from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .services.tinyc_adapter import TinyCAdapter
from .services.executor import Executor
import tempfile
import shutil
import os
import logging
import json
import re
import sys

# ensure project root is on sys.path so `src` package imports work when running backend
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ---- local compiler pipeline imports ----
# Simple pipeline (handles trivial "x = 3 + 4;" style code)
try:
    from src.lexer import Lexer as SimpleLexer
    from src.parser import Parser as SimpleParser
    from src.semantic import SemanticAnalyzer as SimpleSemanticAnalyzer
    from src.ir import IRGenerator as SimpleIRGenerator
    from src.optimizer import Optimizer as SimpleOptimizer
    from src.codegen import CodeGenerator as SimpleCodeGenerator
except Exception:
    SimpleLexer = SimpleParser = SimpleSemanticAnalyzer = SimpleIRGenerator = SimpleOptimizer = SimpleCodeGenerator = None

# Full C lexer (handles real C programs – braces, strings, preprocessor directives etc.)
try:
    from src.c_compiler.lexer import CLexer
except Exception:
    CLexer = None

# AST builder from C token stream
try:
    from src.c_compiler.ast_builder import build_ast_from_tokens
except Exception:
    build_ast_from_tokens = None


def _load_dotenv_if_present(path=None):
    """Simple .env loader: reads KEY=VALUE lines and sets them in os.environ
    only if not already present. Does not require python-dotenv.
    """
    env_path = path or os.path.join(os.getcwd(), '.env')
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass

logger = logging.getLogger('uvicorn')
app = FastAPI(title="TinyC Platform API")


@app.on_event('startup')
def _startup():
    _load_dotenv_if_present()
    try:
        adapter = TinyCAdapter()
        resolved = getattr(adapter, 'tinyc_path', None)
        logger.info(f'Resolved tinyc path: {resolved}')
    except Exception:
        logger.warning('Unable to resolve tinyc path at startup')
    # log gcc path for debugging
    from .services.executor import find_gcc
    logger.info(f'Resolved gcc path: {find_gcc()}')


@app.get('/api/health')
def health_check():
    from .services.executor import find_gcc
    gcc_path = find_gcc()
    gcc_ok = bool(gcc_path and os.path.exists(gcc_path))
    return {
        'ok': gcc_ok,
        'gcc_path': gcc_path,
        'gcc_found': gcc_ok,
        'pipeline': 'local',
        'hint': None if gcc_ok else 'GCC not found. Install MinGW-w64 or set GCC path.'
    }


class CompileRunRequest(BaseModel):
    source: str
    stdin: str = ''
    timeout: int = 5
    mode: str = 'auto'  # 'auto' | 'local'


# ── helpers ───────────────────────────────────────────────────────────────

def _looks_like_simple_code(source: str) -> bool:
    """Heuristic: is this the trivial 'x = 3 + 4;' style the simple pipeline handles?"""
    if '#include' in source or '{' in source or 'int main' in source:
        return False
    return True


def _extract_symbols_from_tokens(tokens):
    """Walk the token list and extract declared variable names (best effort)."""
    symbols = {}
    type_keywords = {'int', 'float', 'double', 'char', 'long', 'short', 'void', 'unsigned', 'signed'}
    i = 0
    while i < len(tokens):
        tok_type, tok_val = tokens[i]
        if tok_type == 'KEYWORD' and tok_val in type_keywords:
            # look for an ID after the type keyword
            j = i + 1
            while j < len(tokens) and tokens[j][0] in ('KEYWORD',):
                j += 1  # skip extra type qualifiers
            if j < len(tokens) and tokens[j][0] == 'ID':
                symbols[tokens[j][1]] = tok_val
        i += 1
    return symbols


def _simple_ir_from_tokens(tokens):
    """Generate a very simple three-address-code style IR from token stream."""
    lines = []
    i = 0
    while i < len(tokens):
        # pattern: TYPE ID = EXPR ;
        if tokens[i][0] == 'KEYWORD' and i + 1 < len(tokens) and tokens[i + 1][0] == 'ID':
            type_name = tokens[i][1]
            var_name = tokens[i + 1][1]
            # check for assignment
            if i + 2 < len(tokens) and tokens[i + 2][1] == '=':
                # collect RHS until SEMICOLON
                j = i + 3
                rhs_parts = []
                while j < len(tokens) and tokens[j][0] != 'SEMICOLON':
                    rhs_parts.append(tokens[j][1])
                    j += 1
                rhs = ' '.join(rhs_parts) if rhs_parts else '?'
                lines.append(f"{var_name} = {rhs}")
                i = j + 1
                continue
            else:
                lines.append(f"DECL {type_name} {var_name}")
                i += 2
                continue
        # pattern: ID = EXPR ;
        if tokens[i][0] == 'ID' and i + 1 < len(tokens) and tokens[i + 1][1] == '=':
            var_name = tokens[i][1]
            j = i + 2
            rhs_parts = []
            while j < len(tokens) and tokens[j][0] != 'SEMICOLON':
                rhs_parts.append(tokens[j][1])
                j += 1
            rhs = ' '.join(rhs_parts) if rhs_parts else '?'
            lines.append(f"{var_name} = {rhs}")
            i = j + 1
            continue
        # pattern: return EXPR ;
        if tokens[i][0] == 'KEYWORD' and tokens[i][1] == 'return':
            j = i + 1
            rhs_parts = []
            while j < len(tokens) and tokens[j][0] != 'SEMICOLON':
                rhs_parts.append(tokens[j][1])
                j += 1
            lines.append(f"RETURN {' '.join(rhs_parts)}")
            i = j + 1
            continue
        # pattern: function call  ID ( ... )
        if tokens[i][0] == 'ID' and i + 1 < len(tokens) and tokens[i + 1][0] == 'LPAREN':
            fname = tokens[i][1]
            j = i + 2
            depth = 1
            args = []
            while j < len(tokens) and depth > 0:
                if tokens[j][0] == 'LPAREN':
                    depth += 1
                elif tokens[j][0] == 'RPAREN':
                    depth -= 1
                if depth > 0:
                    args.append(tokens[j][1])
                j += 1
            lines.append(f"CALL {fname}({', '.join(args)})")
            i = j
            continue
        i += 1
    return lines


# ── main endpoint ─────────────────────────────────────────────────────────

@app.post("/api/compile-run")
async def compile_and_run(req: CompileRunRequest):
    build_dir = tempfile.mkdtemp(prefix="tinyc_build_")
    try:
        src_path = os.path.join(build_dir, "input.c")
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(req.source)

        execer = Executor(build_dir)

        # ── Phase 1: Tokenization ────────────────────────────────────────
        tokens_list = []
        analysis_errors = []

        is_simple = _looks_like_simple_code(req.source)

        if is_simple and SimpleLexer:
            # Simple single-line expressions
            try:
                lexer = SimpleLexer(req.source)
                toks = lexer.tokenize()
                tokens_list = [{'type': t[0], 'value': t[1]} for t in toks]
            except Exception as e:
                analysis_errors.append(f'Simple lexer: {e}')
        
        if (not tokens_list) and CLexer:
            # Full C lexer
            try:
                clexer = CLexer(req.source)
                toks = clexer.tokenize()
                tokens_list = [{'type': t[0], 'value': t[1]} for t in toks]
            except Exception as e:
                analysis_errors.append(f'C lexer: {e}')
                toks = []

        # ── Phase 2: Symbol Table ────────────────────────────────────────
        symbol_table = []
        if is_simple and SimpleLexer and SimpleParser and SimpleSemanticAnalyzer:
            try:
                lexer2 = SimpleLexer(req.source)
                toks2 = lexer2.tokenize()
                parser = SimpleParser(toks2)
                ast = parser.parse()
                analyzer = SimpleSemanticAnalyzer()
                analyzer.analyze(ast)
                symbol_table = list(analyzer.symbol_table.keys()) if isinstance(analyzer.symbol_table, dict) else list(analyzer.symbol_table)
            except Exception:
                pass

        if not symbol_table and CLexer:
            # Extract symbols from C token stream
            try:
                clexer2 = CLexer(req.source)
                toks2c = clexer2.tokenize()
                syms = _extract_symbols_from_tokens(toks2c)
                symbol_table = [f"{name}: {typ}" for name, typ in syms.items()]
            except Exception:
                pass

        # ── Phase 2b: AST ────────────────────────────────────────────────
        ast_tree = None
        if build_ast_from_tokens and CLexer:
            try:
                clexer_ast = CLexer(req.source)
                toks_ast = clexer_ast.tokenize()
                ast_tree = build_ast_from_tokens(toks_ast)
            except Exception as e:
                analysis_errors.append(f'AST builder: {e}')

        # ── Phase 3 & 4: IR + Optimized IR ───────────────────────────────
        ir_lines = []
        opt_lines = []

        if is_simple and SimpleLexer and SimpleParser and SimpleIRGenerator and SimpleOptimizer:
            try:
                lexer3 = SimpleLexer(req.source)
                toks3 = lexer3.tokenize()
                parser3 = SimpleParser(toks3)
                ast3 = parser3.parse()
                irgen = SimpleIRGenerator()
                irgen.generate(ast3)
                instrs = irgen.get_instructions()
                optimizer = SimpleOptimizer(instrs)
                optimized = optimizer.optimize()

                for ins in instrs:
                    op, left, right, dest = ins
                    ir_lines.append(f"{dest} = {left}" if op == 'ASSIGN' else f"{dest} = {left} {op} {right}")
                for ins in optimized:
                    op, left, right, dest = ins
                    opt_lines.append(f"{dest} = {left}" if op == 'ASSIGN' else f"{dest} = {left} {op} {right}")
            except Exception:
                pass

        if not ir_lines and CLexer:
            try:
                clexer3 = CLexer(req.source)
                toks3c = clexer3.tokenize()
                ir_lines = _simple_ir_from_tokens(toks3c)
                opt_lines = list(ir_lines)  # same for now
            except Exception:
                pass

        # ── Phase 5: Assembly (gcc -S) ───────────────────────────────────
        asm_lines = []
        asm_res = execer.compile_to_asm(src_path, optimized=False, timeout=15)
        if asm_res.get('success'):
            # strip GCC metadata lines (starting with .) for a cleaner view
            raw_asm = asm_res.get('asm', '')
            asm_lines = raw_asm.splitlines()

        # ── Phase 6: Compile + Run ───────────────────────────────────────
        # detect if program needs stdin
        needs_stdin = any(kw in req.source for kw in ['scanf', 'gets(', 'getchar(', 'fgets(', 'getc(', 'fgetc('])
        stdin_to_pass = req.stdin if req.stdin else None

        host_gcc = execer.compile_c(src_path, timeout=20)
        run_res = None
        if host_gcc.get('success'):
            run_res = execer.run_executable_host(host_gcc['exe_path'], timeout=req.timeout, stdin_text=stdin_to_pass)
            # If timed out and program needs stdin, add helpful message
            if run_res.get('error') == 'timeout' and needs_stdin and not req.stdin:
                run_res['stderr'] = ('Program timed out waiting for input. '
                                     'This program uses scanf/gets — provide input via the Stdin panel below the editor.\n'
                                     + (run_res.get('stderr') or ''))
        else:
            run_res = {
                'success': False,
                'stdout': '',
                'stderr': host_gcc.get('stderr') or host_gcc.get('error', 'gcc compilation failed'),
                'returncode': host_gcc.get('returncode'),
            }

        # ── Assemble response ────────────────────────────────────────────
        phases = {
            'tokens': tokens_list,
            'ast': ast_tree,
            'symbol_table': symbol_table,
            'intermediate_code': ir_lines,
            'optimized_code': opt_lines,
            'assembly': asm_lines,
            'errors': analysis_errors if analysis_errors else [],
        }
        runtime = {
            'stdout': run_res.get('stdout', '') if run_res else '',
            'stderr': run_res.get('stderr', '') if run_res else '',
            'exit_code': run_res.get('returncode') if run_res else None,
            'execution_time_ms': run_res.get('execution_time_ms') if run_res else None,
        }
        return {'phases': phases, 'runtime': runtime}

    finally:
        try:
            shutil.rmtree(build_dir)
        except Exception:
            pass
