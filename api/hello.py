from http.server import BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write('Hello from Python!'.encode())

def handler(request, response):
    return {
        'statusCode': 200,
        'body': 'Hello from Python!'
    }
