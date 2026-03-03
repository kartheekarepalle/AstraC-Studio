import subprocess
import os
import sys
import shlex
import shutil
import time
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# GCC discovery – cached at module level
# ---------------------------------------------------------------------------
_gcc_path_cache = None

def find_gcc() -> str:
    """Return the full path to gcc.exe (or 'gcc' on non-Windows).

    Search order:
      1. GCC_PATH environment variable
      2. shutil.which('gcc')   (i.e. system PATH)
      3. <project_root>/mingw64/bin/gcc.exe
      4. Common well-known mingw64 locations on Windows
    """
    global _gcc_path_cache
    if _gcc_path_cache:
        return _gcc_path_cache

    # 1. env override
    env_gcc = os.environ.get('GCC_PATH')
    if env_gcc and os.path.isfile(env_gcc):
        _gcc_path_cache = env_gcc
        return _gcc_path_cache

    # 2. on system PATH already?
    which = shutil.which('gcc')
    if which:
        _gcc_path_cache = which
        return _gcc_path_cache

    # 3. bundled mingw64 inside the project tree
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    bundled = os.path.join(project_root, 'mingw64', 'bin', 'gcc.exe')
    if os.path.isfile(bundled):
        _gcc_path_cache = bundled
        return _gcc_path_cache

    # 4. scan common locations on Windows
    if sys.platform.startswith('win'):
        for base in [
            os.path.expanduser('~\\Downloads'),
            'C:\\',
            'C:\\msys64\\mingw64\\bin',
            'C:\\mingw64\\bin',
        ]:
            if os.path.isdir(base):
                for entry in os.listdir(base):
                    candidate = os.path.join(base, entry, 'mingw64', 'bin', 'gcc.exe')
                    if os.path.isfile(candidate):
                        _gcc_path_cache = candidate
                        return _gcc_path_cache

    # last resort – just return 'gcc' and hope subprocess can find it
    _gcc_path_cache = 'gcc'
    return _gcc_path_cache


class Executor:
    def __init__(self, work_dir):
        self.work_dir = work_dir

    # ── host gcc helpers ──────────────────────────────────────────────────

    def _gcc(self):
        return find_gcc()

    def compile_c(self, c_path, timeout=15):
        """Compile *c_path* with host gcc and return result dict."""
        exe_name = 'prog.exe' if sys.platform.startswith('win') else 'prog'
        exe_path = os.path.join(self.work_dir, exe_name)
        cmd = [self._gcc(), c_path, '-std=c99', '-O2', '-Wall', '-Wextra', '-o', exe_path]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "gcc_timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

        success = proc.returncode == 0
        return {
            "success": success,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "exe_path": exe_path if success else None
        }

    def preprocess_host(self, c_path, timeout=10):
        """Run ``gcc -E`` on the host to expand includes/macros."""
        out_path = os.path.join(self.work_dir, 'preprocessed.c')
        cmd = [self._gcc(), '-E', c_path, '-o', out_path]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "preprocess_timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        success = proc.returncode == 0
        return {
            "success": success,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "out_path": out_path if success else None,
        }

    def compile_to_asm(self, c_path, optimized=False, timeout=15):
        """Run ``gcc -S`` to produce assembly listing."""
        label = 'opt_asm' if optimized else 'asm'
        asm_path = os.path.join(self.work_dir, f'{label}.s')
        opt_flag = '-O2' if optimized else '-O0'
        cmd = [self._gcc(), '-S', opt_flag, '-std=c99', c_path, '-o', asm_path]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "gcc_asm_timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        if proc.returncode != 0:
            return {"success": False, "stderr": proc.stderr, "returncode": proc.returncode}
        try:
            with open(asm_path, 'r', encoding='utf-8', errors='replace') as f:
                asm_text = f.read()
        except Exception:
            asm_text = ''
        return {"success": True, "asm": asm_text}

    def run_executable(self, exe_path, timeout=3):
        # Prefer running inside Docker for sandboxed execution if docker is available.
        if not os.path.exists(exe_path):
            return {"success": False, "error": "exe_not_found"}

        exe_base = os.path.basename(exe_path)
        abs_work = os.path.abspath(self.work_dir)
        docker_cmd = [
            'docker', 'run', '--rm',
            '-v', f'{abs_work}:/work',
            '-w', '/work',
            '--network', 'none',
            '--pids-limit', '64',
            '--memory', '256m',
            'gcc:latest',
            './' + exe_base
        ]
        try:
            start = time.time()
            proc = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=timeout)
            elapsed = int((time.time() - start) * 1000)
            return {
                "success": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "execution_time_ms": elapsed
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "timeout"}
        except FileNotFoundError:
            # Docker not present; fall back to running on host if possible
            return {"success": False, "error": "docker_not_found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_executable_host(self, exe_path, timeout=3, stdin_text=None):
        """Run a native executable on the host (fallback when Docker unavailable)."""
        if not os.path.exists(exe_path):
            return {"success": False, "error": "exe_not_found"}
        cmd = [exe_path]
        try:
            start = time.time()
            proc = subprocess.run(
                cmd,
                input=stdin_text if stdin_text is not None else '',
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.work_dir,
            )
            elapsed = int((time.time() - start) * 1000)
            return {
                "success": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "execution_time_ms": elapsed
            }
        except subprocess.TimeoutExpired as te:
            return {
                "success": False,
                "error": "timeout",
                "stdout": te.stdout if te.stdout else '',
                "stderr": te.stderr if te.stderr else '',
                "returncode": -1,
                "execution_time_ms": int((time.time() - start) * 1000),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def preprocess_in_docker(self, input_path, out_name='preprocessed.c', timeout=10):
        """Run `gcc -E input.c -o preprocessed.c` inside a Docker gcc container.
        Returns dict with success, out_path, stdout, stderr, returncode
        """
        abs_work = os.path.abspath(self.work_dir)
        in_base = os.path.basename(input_path)
        out_base = out_name
        docker_cmd = [
            'docker', 'run', '--rm',
            '-v', f'{abs_work}:/work',
            '-w', '/work',
            '--network', 'none',
            '--pids-limit', '64',
            '--memory', '256m',
            'gcc:latest',
            'gcc', '-E', in_base, '-o', out_base
        ]
        try:
            proc = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "preprocess_timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

        success = proc.returncode == 0
        out_path = os.path.join(self.work_dir, out_base) if success else None
        return {
            "success": success,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "out_path": out_path
        }

    def compile_in_docker(self, c_path, exe_name='prog', timeout=15):
        """Compile `c_path` inside Docker and produce `exe_name` in the work dir."""
        abs_work = os.path.abspath(self.work_dir)
        c_base = os.path.basename(c_path)
        # produce linux binary; run it also in Docker to keep sandbox
        docker_cmd = [
            'docker', 'run', '--rm',
            '-v', f'{abs_work}:/work',
            '-w', '/work',
            '--network', 'none',
            '--pids-limit', '64',
            '--memory', '256m',
            'gcc:latest',
            'gcc', c_base, '-std=c99', '-O2', '-Wall', '-Wextra', '-o', exe_name
        ]
        try:
            proc = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "gcc_timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

        success = proc.returncode == 0
        exe_path = os.path.join(self.work_dir, exe_name) if success else None
        return {
            "success": success,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "exe_path": exe_path
        }
