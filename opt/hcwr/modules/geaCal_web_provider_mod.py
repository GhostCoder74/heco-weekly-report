#!/usr/bin/env python3
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import socket


GEACAL_HOST = "127.0.0.1"
GEACAL_PORT = 7777


def query_geacal(sql):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((GEACAL_HOST, GEACAL_PORT))
        s.send(sql.encode())
        data = s.recv(65535)
        s.close()
        return data.decode()
    except Exception as e:
        return json.dumps({"error": str(e)})


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/holidays":
            q = urllib.parse.parse_qs(parsed.query)
            year = q.get("year", ["2024"])[0]

            sql = f"SELECT * FROM holidays WHERE year={year};"
            result = query_geacal(sql)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(result.encode())
        else:
            self.send_error(404, "Unknown endpoint")


def run():
    print("HTTP→geaCal Proxy läuft auf http://127.0.0.1:8800 …")
    server = HTTPServer(("127.0.0.1", 8800), Handler)
    server.serve_forever()


if __name__ == "__main__":
    run()

