from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            'ok': True,
            'gcc_path': None,
            'gcc_found': False,
            'pipeline': 'serverless',
            'hint': 'Deployed on Vercel — 6-phase compiler pipeline active. GCC execution unavailable in serverless mode.'
        }).encode())
