"""Simple E2E test: POST /api/compile-run and assert expected fields.
Usage: python tools/e2e_compile_run.py [url]
Default url: http://127.0.0.1:5176 (frontend dev server proxy)
"""
import sys
import json
try:
    # prefer requests if available for nicer output
    import requests
except Exception:
    requests = None

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5176"
HEALTH = f"{URL}/api/health"
COMPILE = f"{URL}/api/compile-run"

def check_health():
    try:
        if requests:
            r = requests.get(HEALTH, timeout=3)
            r.raise_for_status()
            print('health:', r.json())
        else:
            from urllib import request
            resp = request.urlopen(HEALTH, timeout=3)
            body = resp.read().decode('utf-8')
            print('health:', body)
        return True
    except Exception as e:
        print('health check failed:', e)
        return False


def test_compile():
    payload = {"source": "x = 3 + 4;", "mode": "local"}
    try:
        if requests:
            r = requests.post(COMPILE, json=payload, timeout=10)
            r.raise_for_status()
            j = r.json()
        else:
            from urllib import request
            data = json.dumps(payload).encode('utf-8')
            req = request.Request(COMPILE, data=data, headers={"Content-Type": "application/json"})
            resp = request.urlopen(req, timeout=10)
            j = json.loads(resp.read().decode('utf-8'))
        print('compile-run response keys:', list(j.keys()))
        # basic assertions for new response shape
        phases = j.get('phases') or j.get('analysis') or {}
        runtime = j.get('runtime') or j.get('run') or {}
        tokens = phases.get('tokens')
        if tokens is None:
            print('FAIL: phases.tokens missing')
            return False
        if not isinstance(tokens, list):
            print('FAIL: tokens is not a list')
            return False
        print('PASS: compile-run produced tokens (count=%d)' % len(tokens))
        print('runtime:', { 'exit_code': runtime.get('exit_code') or runtime.get('returncode'), 'stdout_len': len((runtime.get('stdout') or '')) })
        return True
    except Exception as e:
        print('compile-run failed:', e)
        return False


if __name__ == '__main__':
    ok = check_health()
    if not ok:
        print('Aborting due to failed health check')
        sys.exit(2)
    ok2 = test_compile()
    sys.exit(0 if ok2 else 3)
