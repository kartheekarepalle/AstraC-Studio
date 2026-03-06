from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .services.tinyc_adapter import TinyCAdapter
from .services.executor import Executor
from .services.compiler_pipeline import run_pipeline
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


# ── main endpoint ─────────────────────────────────────────────────────────

@app.post("/api/compile-run")
async def compile_and_run(req: CompileRunRequest):
    build_dir = tempfile.mkdtemp(prefix="tinyc_build_")
    try:
        src_path = os.path.join(build_dir, "input.c")
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(req.source)

        execer = Executor(build_dir)

        # ── Run the 6-phase compiler visualization pipeline ──────────
        pipeline_phases = run_pipeline(req.source)

        # ── Compile + Run via GCC (for actual execution) ─────────────
        needs_stdin = any(kw in req.source for kw in ['scanf', 'gets(', 'getchar(', 'fgets(', 'getc(', 'fgetc('])
        stdin_to_pass = req.stdin if req.stdin else None

        host_gcc = execer.compile_c(src_path, timeout=20)
        run_res = None
        if host_gcc.get('success'):
            run_res = execer.run_executable_host(host_gcc['exe_path'], timeout=req.timeout, stdin_text=stdin_to_pass)
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

        # ── Assemble response ────────────────────────────────────────
        runtime = {
            'stdout': run_res.get('stdout', '') if run_res else '',
            'stderr': run_res.get('stderr', '') if run_res else '',
            'exit_code': run_res.get('returncode') if run_res else None,
            'execution_time_ms': run_res.get('execution_time_ms') if run_res else None,
        }
        # pipeline_phases is now a flat dict with tokens, syntax_tree,
        # semantic_tree, symbol_table, ir, optimized_ir, assembly, errors, phases
        response = dict(pipeline_phases)
        response['runtime'] = runtime
        return response

    finally:
        try:
            shutil.rmtree(build_dir)
        except Exception:
            pass
