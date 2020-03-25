from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import _thread
import sys


# Start a simple http server to publish the cerberus status file content
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    requests_served = 0

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        f = open('/tmp/cerberus_status', 'rb')
        self.wfile.write(f.read())
        SimpleHTTPRequestHandler.requests_served = \
            SimpleHTTPRequestHandler.requests_served + 1


def start_server(address):
    server = address[0]
    port = address[1]
    httpd = HTTPServer(address, SimpleHTTPRequestHandler)
    logging.info("Starting http server at http://%s:%s" % (server, port))
    try:
        _thread.start_new_thread(httpd.serve_forever, ())
    except Exception:
        logging.error("Failed to start the http server \
                      at http://%s:%s" % (server, port))
        sys.exit(1)
