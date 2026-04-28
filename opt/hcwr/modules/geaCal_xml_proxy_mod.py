#!/usr/bin/env python3
import socket
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

GEACAL_HOST = "127.0.0.1"
GEACAL_PORT = 7777


def query_geacal(sql):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((GEACAL_HOST, GEACAL_PORT))
        s.send(sql.encode())
        data = s.recv(65535)
        s.close()
        return json.loads(data.decode())
    except Exception as e:
        return {"error": str(e)}


def to_xml(rows):
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append("<holidays>")
    for r in rows:
        xml.append("  <holiday>")
        for k, v in r.items():
            xml.append(f"    <{k}>{v}</{k}>")
        xml.append("  </holiday>")
    xml.append("</holidays>")
    return "\n".join(xml)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/holidays":
            q = urllib.parse.parse_qs(parsed.query)
            year = q.get("year", ["2025"])[0]

            sql = f"SELECT * FROM holidays WHERE year={year};"
            rows = query_geacal(sql)

            xml = to_xml(rows)

            self.send_response(200)
            self.send_header("Content-Type", "application/xml; charset=utf-8")
            self.end_headers()
            self.wfile.write(xml.encode())
        else:
            self.send_error(404, "Unknown endpoint")


def run():
    print("geaCal XML-Proxy läuft auf http://127.0.0.1:8800/holidays?year=2025 …")
    server = HTTPServer(("127.0.0.1", 8800), Handler)
    server.serve_forever()


if __name__ == "__main__":
    run()

