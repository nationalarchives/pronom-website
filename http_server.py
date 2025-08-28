import http.server
import os
from urllib.parse import urlparse, unquote
from lambdas import submissions_received, results


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):

    def sent_response(self, response):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(response['body'].encode())

    def send_response_from_file(self):
        file_path = self.translate_path(f'site/{self.path}')
        if os.path.isfile(file_path):
            self.send_response(200)
            if file_path.endswith('.css'):
                self.send_header("Content-type", "text/css; charset=utf-8")
            elif file_path.endswith('.js'):
                self.send_header("Content-type", "application/javascript; charset=utf-8")
            elif file_path.endswith('.woff2'):
                self.send_header("Content-type", "font/woff2")
            else:
                self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            with open(file_path, "rb") as file:
                self.wfile.write(file.read())
        else:
            self.send_error(404, "File not found")

    def redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    def do_POST(self):
        if self.path == '/submissions':
            self.redirect("/submissions-received/1")

    def do_GET(self):
        parsed_url = urlparse(self.path)
        self.path = parsed_url.path

        if self.path == '/':
            self.path = '/home'
            self.send_response_from_file()
        elif self.path == '/results':
            search_string = unquote(parsed_url.query.split("=")[1])
            response = results.lambda_handler({'queryStringParameters': {'q': search_string}}, None)
            if response['statusCode'] == 302:
                self.redirect(response['headers']['Location'])
            else:
                self.sent_response(response)
        elif self.path.startswith('/submissions-received'):
            number = self.path.split("/")[-1]
            response = submissions_received.lambda_handler({'rawPath': number}, None)
            self.sent_response(response)
        else:
            self.send_response_from_file()


if __name__ == "__main__":
    PORT = 8084
    DIRECTORY = "."

    os.chdir(DIRECTORY)
    handler = CustomHTTPRequestHandler
    server = http.server.HTTPServer(("", PORT), handler)

    print(f"Serving files from {os.path.abspath(DIRECTORY)} on port {PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()
