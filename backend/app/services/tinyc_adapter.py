import subprocess
import os
import json
import re
import shutil

class TinyCAdapter:
    def __init__(self, tinyc_path=None):
        # Determine tinyc binary path with this precedence:
        # 1. explicit constructor arg `tinyc_path`
        # 2. environment variable `TINYC_PATH`
        # 3. discovery on PATH via shutil.which('tinyc')
        # 4. fallback to project root `tinyc.exe`
        env_path = os.environ.get('TINYC_PATH')
        if tinyc_path:
            self.tinyc_path = os.path.abspath(tinyc_path)
        elif env_path:
            self.tinyc_path = os.path.abspath(env_path)
        else:
            # try finding tinyc on PATH (portable across platforms)
            which_path = shutil.which('tinyc') or shutil.which('tinyc.exe')
            if which_path:
                self.tinyc_path = os.path.abspath(which_path)
            else:
                self.tinyc_path = os.path.abspath(os.path.join(os.getcwd(), 'tinyc.exe'))

    def run_tinyc(self, source_path):
        """
        Runs tinyc binary on the given source file and parses stdout into sections.
        Returns dict with keys: tokens, symbols, ir, opt_ir, asm, errors
        """
        # ensure tinyc binary exists; if missing, return a structured diagnostic
        if not os.path.exists(self.tinyc_path):
            info = {
                "error": "TinyC binary not found",
                "checked_path": self.tinyc_path,
                "hint": "Set TINYC_PATH environment variable or put tinyc on your PATH"
            }
            # keep older "errors" list for backward compatibility with callers/tests
            return {"errors": [info["error"]], **info}

        # Optionally run tinyc inside a Docker image if configured via env var
        docker_image = os.environ.get('TINYC_DOCKER_IMAGE')
        proc = None
        if docker_image:
            # mount containing directory and run tinyc inside the image
            workdir = os.path.dirname(os.path.abspath(source_path))
            src_base = os.path.basename(source_path)
            docker_cmd = [
                'docker', 'run', '--rm',
                '-v', f"{workdir}:/work",
                '-w', '/work',
                '--network', 'none',
                docker_image,
                os.environ.get('TINYC_DOCKER_CMD', 'tinyc'), '--json', src_base
            ]
            try:
                proc = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=25)
            except FileNotFoundError:
                # docker not installed; fall back to host tinyc
                proc = None
            except Exception as e:
                return {
                    "error": "tinyc_docker_run_failed",
                    "stage": "tinyc_docker",
                    "msg": str(e),
                    "checked_path": self.tinyc_path,
                    "errors": [str(e)]
                }

        # If docker run not used or failed to start, try host tinyc
        if proc is None:
            # prefer structured JSON output from tinyc for robust parsing
            cmd = [self.tinyc_path, "--json", source_path]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            except Exception as e:
                # structured error returned to API caller
                return {
                    "error": "tinyc_run_failed",
                    "stage": "tinyc_run",
                    "msg": str(e),
                    "checked_path": self.tinyc_path,
                    "errors": [str(e)]
                }

        # if tinyc returned a non-zero exit code and no stdout, surface stderr
        if proc.returncode != 0 and not proc.stdout:
            return {
                "error": "tinyc_failed",
                "stage": "tinyc_run",
                "msg": proc.stderr or f"tinyc exited with code {proc.returncode}",
                "checked_path": self.tinyc_path,
                "stderr": proc.stderr,
                "errors": [proc.stderr or f"exit {proc.returncode}"]
            }

        out = proc.stdout
        err = proc.stderr
        # try to parse JSON output
        parsed = None
        if out:
            try:
                parsed = json.loads(out)
            except Exception as e:
                # fall back to text parsing on failure
                parsed = None

        if parsed is not None:
            tokens = parsed.get('tokens', [])
            symbols = parsed.get('symbol_table', parsed.get('symbols', []))
            ir = parsed.get('intermediate_code', [])
            opt_ir = parsed.get('optimized_code', [])
            asm = parsed.get('assembly', [])
            errors = parsed.get('errors', [])
            return {
                'stdout': out,
                'stderr': err,
                'tokens': tokens,
                'symbols': symbols,
                'ir': ir,
                'opt_ir': opt_ir,
                'asm': asm,
                'errors': errors
            }

        # fallback: parse text sections when JSON not available
        sections = self._split_sections(out)
        tokens = self._parse_tokens(sections.get('TOKENS',''))
        symbols = self._parse_symbols(sections.get('SYMBOL TABLE',''))
        ir = self._parse_lines(sections.get('INTERMEDIATE CODE',''))
        opt_ir = self._parse_lines(sections.get('OPTIMIZED CODE',''))
        asm = self._parse_lines(sections.get('ASSEMBLY',''))

        # try to detect return var from tokens or ir
        return_var = self._detect_return_var(sections)

        return {
            'stdout': out,
            'stderr': err,
            'tokens': tokens,
            'symbols': symbols,
            'ir': ir,
            'opt_ir': opt_ir,
            'asm': asm,
            'return_var': return_var,
            'errors': []
        }

    def _split_sections(self, text):
        # headers we care about
        headers = ['TOKENS','PARSE SUCCESS','SYMBOL TABLE','INTERMEDIATE CODE','OPTIMIZED CODE','ASSEMBLY']
        sections = {}
        cur = 'PRE'
        sections[cur] = ''
        for line in text.splitlines():
            h = None
            for header in headers:
                if line.strip().startswith('--- ' + header + ' ---') or line.strip() == ('--- ' + header + ' ---'):
                    h = header
                    break
            if h:
                cur = h
                sections[cur] = ''
            else:
                sections[cur] += line + "\n"
        return sections

    def _parse_tokens(self, text):
        toks = []
        for line in text.splitlines():
            m = re.match(r"\[(\d+)\]\s+(\S+)\s+:\s+(.*)", line.strip())
            if m:
                toks.append({'line':int(m.group(1)),'type':m.group(2),'value':m.group(3)})
        return toks

    def _parse_symbols(self, text):
        syms = []
        for line in text.splitlines():
            s = line.strip()
            if s:
                syms.append(s)
        return syms

    def _parse_lines(self, text):
        return [l for l in (line.strip() for line in text.splitlines()) if l]

    def _detect_return_var(self, sections):
        # look for a line in INTERMEDIATE or TOKENS indicating 'return X'
        toks_text = sections.get('TOKENS','')
        for line in toks_text.splitlines():
            if 'KEYWORD : return' in line:
                # next token likely the identifier on following line(s) in tokens
                pass
        # fallback: search for 'return' in stdout
        for line in sections.get('PRE','').splitlines():
            if 'return' in line:
                m = re.search(r'return\s+(\w+)', line)
                if m:
                    return m.group(1)
        return None

    def ir_to_c(self, ir_lines, symbols, return_var=None):
        """
        Simple translator from TAC-like IR to C. This is conservative and intended
        for the Tiny subset produced by the current compiler.
        """
        # collect variable names (exclude 'main')
        vars = [s for s in symbols if s != 'main']
        temp_vars = set()
        stmts = []
        for line in ir_lines:
            if line.startswith('return'):
                # return X
                parts = line.split()
                if len(parts) >= 2:
                    rv = parts[1]
                    stmts.append(f'printf("%d\\n", {rv});')
                    stmts.append('return 0;')
                continue
            if '=' in line:
                lhs, rhs = [p.strip() for p in line.split('=',1)]
                rhs_parts = rhs.split()
                if len(rhs_parts) == 3:
                    op1, op, op2 = rhs_parts
                    stmts.append(f'{lhs} = {op1} {op} {op2};')
                    if lhs.startswith('t'):
                        temp_vars.add(lhs)
                else:
                    stmts.append(f'{lhs} = {rhs};')
                    if lhs.startswith('t'):
                        temp_vars.add(lhs)
        # build c source
        c_lines = ['#include <stdio.h>','int main() {']
        decls = []
        if vars:
            decls.append('int ' + ', '.join(vars) + ';')
        if temp_vars:
            decls.append('int ' + ', '.join(sorted(temp_vars)) + ';')
        for d in decls:
            c_lines.append('    ' + d)
        for s in stmts:
            c_lines.append('    ' + s)
        # if no return emitted, return 0
        if not any(l.strip().startswith('return') for l in stmts):
            c_lines.append('    return 0;')
        c_lines.append('}')
        return '\n'.join(c_lines)
