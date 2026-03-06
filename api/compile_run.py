from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import re
import time

# Import compiler_pipeline from same directory
sys.path.insert(0, os.path.dirname(__file__))
from compiler_pipeline import run_pipeline


# ── TAC Interpreter ──────────────────────────────────────────────────
# Executes Three-Address Code produced by the compiler pipeline
# so programs can run on Vercel without GCC.

class TACInterpreter:
    """Interprets the optimized TAC (list[str]) and produces stdout."""

    MAX_STEPS = 50000  # safety limit

    def __init__(self, tac_lines):
        self.lines = tac_lines
        self.funcs = {}       # name -> (param_names, start_idx)
        self.stdout = []
        self.steps = 0
        self._parse_functions()

    # ── parse function boundaries ────────────────────────────────────
    def _parse_functions(self):
        i = 0
        while i < len(self.lines):
            m = re.match(r'FUNC_BEGIN\s+(\w+)', self.lines[i])
            if m:
                fname = m.group(1)
                # scan backward from current func to find param decls
                # params appear as PARAM lines or extracted from source
                # In our TAC, params are just used as names inside the func
                start = i + 1
                # find FUNC_END
                end = start
                while end < len(self.lines) and not re.match(r'FUNC_END\s+' + fname, self.lines[end]):
                    end += 1
                self.funcs[fname] = {
                    'body': self.lines[start:end],
                    'name': fname,
                }
            i += 1

    # ── run the program (calls main) ─────────────────────────────────
    def run(self):
        if 'main' not in self.funcs:
            return {'stdout': '', 'stderr': 'No main() function found', 'exit_code': 1}
        try:
            ret = self._exec_func('main', {})
            return {
                'stdout': ''.join(self.stdout),
                'stderr': '',
                'exit_code': ret if isinstance(ret, int) else 0,
                'execution_time_ms': None,
            }
        except _StepLimitError:
            return {
                'stdout': ''.join(self.stdout),
                'stderr': 'Execution limit reached (possible infinite loop)',
                'exit_code': 1,
            }
        except Exception as e:
            return {
                'stdout': ''.join(self.stdout),
                'stderr': f'Runtime error: {e}',
                'exit_code': 1,
            }

    # ── execute a function body ──────────────────────────────────────
    def _exec_func(self, fname, args_map):
        if fname not in self.funcs:
            return 0
        body = self.funcs[fname]['body']
        env = dict(args_map)  # local variables
        # build label index
        labels = {}
        for i, line in enumerate(body):
            lm = re.match(r'^(L\d+):$', line)
            if lm:
                labels[lm.group(1)] = i

        pc = 0
        while pc < len(body):
            self.steps += 1
            if self.steps > self.MAX_STEPS:
                raise _StepLimitError()

            line = body[pc].strip()
            if not line:
                pc += 1
                continue

            # ── Label ──
            if re.match(r'^L\d+:$', line):
                pc += 1
                continue

            # ── DECL var ──
            dm = re.match(r'^DECL\s+(\w+)$', line)
            if dm:
                env.setdefault(dm.group(1), 0)
                pc += 1
                continue

            # ── RETURN [value] ──
            rm = re.match(r'^RETURN\s*(.*)?$', line)
            if rm:
                val = rm.group(1).strip() if rm.group(1) else ''
                if val:
                    return self._eval(val, env)
                return 0

            # ── GOTO label ──
            gm = re.match(r'^GOTO\s+(L\d+)$', line)
            if gm:
                lbl = gm.group(1)
                if lbl in labels:
                    pc = labels[lbl]
                    continue
                pc += 1
                continue

            # ── IF_FALSE cond GOTO label ──
            ifm = re.match(r'^IF_FALSE\s+(.+?)\s+GOTO\s+(L\d+)$', line)
            if ifm:
                cond_str = ifm.group(1)
                lbl = ifm.group(2)
                cond_val = self._eval(cond_str, env)
                if not cond_val:
                    if lbl in labels:
                        pc = labels[lbl]
                        continue
                pc += 1
                continue

            # ── CALL func(args) (no return capture) ──
            cm = re.match(r'^CALL\s+(\w+)\((.*)?\)$', line)
            if cm:
                fn = cm.group(1)
                raw_args = cm.group(2) or ''
                self._handle_call(fn, raw_args, env)
                pc += 1
                continue

            # ── var = CALL func(args) ──
            tcm = re.match(r'^(\w+)\s*=\s*CALL\s+(\w+)\((.*)?\)$', line)
            if tcm:
                dest = tcm.group(1)
                fn = tcm.group(2)
                raw_args = tcm.group(3) or ''
                result = self._handle_call(fn, raw_args, env)
                env[dest] = result if result is not None else 0
                pc += 1
                continue

            # ── var ++ or var -- (as "i ++" or "i --") ──
            incdec = re.match(r'^(\w+)\s*(\+\+|--)$', line)
            if incdec:
                v = incdec.group(1)
                op = incdec.group(2)
                val = self._resolve(v, env)
                env[v] = val + 1 if op == '++' else val - 1
                pc += 1
                continue

            # ── var = expr ──
            am = re.match(r'^(\w+)\s*=\s*(.+)$', line)
            if am:
                dest = am.group(1)
                expr = am.group(2).strip()
                env[dest] = self._eval(expr, env)
                pc += 1
                continue

            # skip unknown
            pc += 1

        return 0

    # ── handle built-in and user-defined calls ───────────────────────
    def _handle_call(self, fn, raw_args, env):
        if fn == 'printf':
            return self._do_printf(raw_args, env)
        # user-defined function
        args = self._split_args(raw_args)
        arg_vals = [self._eval(a.strip(), env) for a in args]
        # find param names from function body usage
        if fn in self.funcs:
            param_names = self._infer_params(fn, len(arg_vals))
            args_map = {}
            for i, pname in enumerate(param_names):
                args_map[pname] = arg_vals[i] if i < len(arg_vals) else 0
            return self._exec_func(fn, args_map)
        return 0

    def _infer_params(self, fname, n_args):
        """Infer parameter names by looking at variables used in the function
        body that aren't declared or assigned before use."""
        body = self.funcs[fname]['body']
        declared = set()
        used_before_decl = []
        for line in body:
            # declared via DECL or assignment
            dm = re.match(r'^DECL\s+(\w+)', line)
            if dm:
                declared.add(dm.group(1))
            am = re.match(r'^(\w+)\s*=', line)
            if am and am.group(1) not in ('IF_FALSE',):
                declared.add(am.group(1))
            # look for names used in conditions, expressions
            # that aren't temps or labels
            for name in re.findall(r'\b([a-zA-Z_]\w*)\b', line):
                if name not in declared and name not in used_before_decl:
                    if not re.match(r'^(FUNC_BEGIN|FUNC_END|DECL|CALL|RETURN|IF_FALSE|GOTO|L\d+|t\d+|printf|scanf|main)$', name):
                        if name not in ('int', 'float', 'char', 'void', 'double'):
                            used_before_decl.append(name)
        # deduplicate preserving order
        seen = set()
        params = []
        for p in used_before_decl:
            if p not in seen:
                seen.add(p)
                params.append(p)
        return params[:n_args]

    # ── printf implementation ────────────────────────────────────────
    def _do_printf(self, raw_args, env):
        args = self._split_args(raw_args)
        if not args:
            return 0
        fmt = args[0].strip()
        # remove surrounding quotes
        if fmt.startswith('"') and fmt.endswith('"'):
            fmt = fmt[1:-1]
        # resolve remaining args
        vals = [self._eval(a.strip(), env) for a in args[1:]]

        # Process format string
        output = []
        vi = 0
        i = 0
        while i < len(fmt):
            if fmt[i] == '\\' and i + 1 < len(fmt):
                esc = fmt[i + 1]
                if esc == 'n':
                    output.append('\n')
                elif esc == 't':
                    output.append('\t')
                elif esc == '\\':
                    output.append('\\')
                elif esc == '"':
                    output.append('"')
                else:
                    output.append(fmt[i])
                    output.append(esc)
                i += 2
                continue
            if fmt[i] == '%' and i + 1 < len(fmt):
                spec = fmt[i + 1]
                if spec == 'd' or spec == 'i':
                    v = vals[vi] if vi < len(vals) else 0
                    output.append(str(int(v)))
                    vi += 1
                    i += 2
                    continue
                elif spec == 'f':
                    v = vals[vi] if vi < len(vals) else 0.0
                    output.append(f'{float(v):.6f}')
                    vi += 1
                    i += 2
                    continue
                elif spec == 'c':
                    v = vals[vi] if vi < len(vals) else 0
                    output.append(chr(int(v)) if isinstance(v, (int, float)) else str(v))
                    vi += 1
                    i += 2
                    continue
                elif spec == 's':
                    v = vals[vi] if vi < len(vals) else ''
                    output.append(str(v))
                    vi += 1
                    i += 2
                    continue
                elif spec == '%':
                    output.append('%')
                    i += 2
                    continue
                elif spec == 'l':
                    # %ld, %lf etc
                    if i + 2 < len(fmt):
                        spec2 = fmt[i + 2]
                        v = vals[vi] if vi < len(vals) else 0
                        if spec2 == 'd':
                            output.append(str(int(v)))
                        elif spec2 == 'f':
                            output.append(f'{float(v):.6f}')
                        else:
                            output.append(str(v))
                        vi += 1
                        i += 3
                        continue
            output.append(fmt[i])
            i += 1

        text = ''.join(output)
        self.stdout.append(text)
        return len(text)

    # ── evaluate an expression string ────────────────────────────────
    def _eval(self, expr, env):
        expr = expr.strip()
        if not expr:
            return 0

        # integer literal
        if re.match(r'^-?\d+$', expr):
            return int(expr)

        # float literal
        if re.match(r'^-?\d+\.\d+$', expr):
            return float(expr)

        # string literal
        if expr.startswith('"') and expr.endswith('"'):
            return expr

        # char literal
        if expr.startswith("'") and expr.endswith("'"):
            ch = expr[1:-1]
            if ch.startswith('\\'):
                return ord({'n': '\n', 't': '\t', '\\': '\\', '0': '\0'}.get(ch[1], ch[1]))
            return ord(ch[0]) if ch else 0

        # single variable or temp
        if re.match(r'^[a-zA-Z_]\w*$', expr):
            return self._resolve(expr, env)

        # binary operation: a op b
        # try to match: operand op operand
        bm = re.match(r'^(.+?)\s+([\+\-\*/%]|==|!=|<=|>=|<|>|&&|\|\||\||&|<<|>>)\s+(.+)$', expr)
        if bm:
            left = self._eval(bm.group(1), env)
            op = bm.group(2)
            right = self._eval(bm.group(3), env)
            return self._binop(left, op, right)

        # unary: !expr
        if expr.startswith('!'):
            return int(not self._eval(expr[1:], env))

        # unary: -expr
        if expr.startswith('-') and not expr[1:].strip()[0].isdigit():
            return -self._eval(expr[1:], env)

        # fallback: try resolving as a variable
        if re.match(r'^[a-zA-Z_]\w*$', expr.strip()):
            return self._resolve(expr.strip(), env)

        return 0

    def _resolve(self, name, env):
        if name in env:
            return env[name]
        return 0

    def _binop(self, l, op, r):
        try:
            if op == '+': return l + r
            if op == '-': return l - r
            if op == '*': return l * r
            if op == '/': return l // r if isinstance(l, int) and isinstance(r, int) and r != 0 else (l / r if r != 0 else 0)
            if op == '%': return l % r if r != 0 else 0
            if op == '==': return int(l == r)
            if op == '!=': return int(l != r)
            if op == '<': return int(l < r)
            if op == '>': return int(l > r)
            if op == '<=': return int(l <= r)
            if op == '>=': return int(l >= r)
            if op == '&&': return int(bool(l) and bool(r))
            if op == '||': return int(bool(l) or bool(r))
            if op == '&': return int(l) & int(r)
            if op == '|': return int(l) | int(r)
            if op == '<<': return int(l) << int(r)
            if op == '>>': return int(l) >> int(r)
        except Exception:
            return 0
        return 0

    # ── split function args respecting parens and quotes ─────────────
    def _split_args(self, raw):
        if not raw or not raw.strip():
            return []
        args = []
        depth = 0
        current = []
        in_str = False
        for ch in raw:
            if ch == '"' and (not current or current[-1] != '\\'):
                in_str = not in_str
                current.append(ch)
            elif in_str:
                current.append(ch)
            elif ch == '(':
                depth += 1
                current.append(ch)
            elif ch == ')':
                depth -= 1
                current.append(ch)
            elif ch == ',' and depth == 0:
                args.append(''.join(current).strip())
                current = []
            else:
                current.append(ch)
        if current:
            args.append(''.join(current).strip())
        return [a for a in args if a]


class _StepLimitError(Exception):
    pass


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            source = data.get('source', '')
            if not source.strip():
                self._json_response(400, {'error': 'No source code provided'})
                return

            # Run the 6-phase compiler visualization pipeline (pure Python)
            pipeline_result = run_pipeline(source)

            # Execute via TAC interpreter (no GCC needed)
            tac = pipeline_result.get('optimized_ir') or pipeline_result.get('ir') or []
            if tac and not pipeline_result.get('errors'):
                interp = TACInterpreter(tac)
                runtime = interp.run()
            else:
                runtime = {
                    'stdout': '',
                    'stderr': '\n'.join(e.get('message', str(e)) for e in pipeline_result.get('errors', [])) or 'Compilation failed',
                    'exit_code': 1,
                    'execution_time_ms': None,
                }

            pipeline_result['runtime'] = runtime
            self._json_response(200, pipeline_result)
        except Exception as e:
            self._json_response(500, {'error': str(e)})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def _json_response(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
