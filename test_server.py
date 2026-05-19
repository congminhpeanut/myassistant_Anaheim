import http.server
import socketserver

PORT = 8000

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"""
        <!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body>
        <h1>Connection Test OK</h1>
        <p>If you see this, your phone CAN reach the laptop.</p>
        <p>Wi-Fi IP: 192.168.1.18</p>
        <p>Port: 8000</p>
        </body>
        </html>
        """)

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"Serving test page at http://0.0.0.0:{PORT}/")
    httpd.serve_forever()
