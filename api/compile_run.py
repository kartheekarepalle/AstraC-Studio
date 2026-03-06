from http.server import BaseHTTPRequestHandler
import json
import os
import sys

# Import compiler_pipeline from same directory
sys.path.insert(0, os.path.dirname(__file__))
from compiler_pipeline import run_pipeline


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

            # Runtime: GCC not available on Vercel
            pipeline_result['runtime'] = {
                'stdout': '',
                'stderr': 'Execution unavailable in deployed mode (no GCC). The 6-phase compilation pipeline above shows the full analysis of your code.',
                'exit_code': None,
                'execution_time_ms': None,
            }

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
