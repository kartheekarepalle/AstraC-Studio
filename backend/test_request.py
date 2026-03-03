import json
import sys
import urllib.request
import urllib.error


def main() -> None:
    url = 'http://127.0.0.1:8001/api/compile-run'
    source = 'int main() { int a; int b; a = 2 + 3; b = a * 4; return b; }'
    req = urllib.request.Request(url, data=json.dumps({'source': source}).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print('HTTP', resp.status)
            print(resp.read().decode())
    except urllib.error.HTTPError as e:
        print('HTTPERR', e.code)
        try:
            print(e.read().decode())
        except Exception:
            pass
    except Exception as e:
        print('ERROR', e)
        sys.exit(1)


if __name__ == '__main__':
    main()
