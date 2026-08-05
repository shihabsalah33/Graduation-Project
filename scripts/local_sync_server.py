import os
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_DIR)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from manual_sync_controller import manual_push, manual_pull, LAST_SYNC_STATUS

class SyncRequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        if '/push' in self.path:
            success, msg = manual_push()
            self._set_headers(200 if success else 400)
            res = json.dumps({
                "success": success,
                "message": msg,
                "sync_status": LAST_SYNC_STATUS
            }, ensure_ascii=False)
            self.wfile.write(res.encode('utf-8'))
        elif '/pull' in self.path:
            success, msg = manual_pull()
            self._set_headers(200 if success else 400)
            res = json.dumps({
                "success": success,
                "message": msg,
                "sync_status": LAST_SYNC_STATUS
            }, ensure_ascii=False)
            self.wfile.write(res.encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(b'{"error": "Not Found"}')

def run_server():
    server_address = ('127.0.0.1', 5050)
    httpd = HTTPServer(server_address, SyncRequestHandler)
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
