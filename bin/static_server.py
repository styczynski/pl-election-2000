import http.server
import socketserver
import os
import threading

def serverBody():
    #web_dir = os.path.join(os.path.dirname(__file__), '..', 'build')
    #os.chdir(web_dir)

    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("[@] Server: Serving at port", PORT)
        httpd.serve_forever()

class AsyncServer(threading.Thread):
   def __init__(self):
      threading.Thread.__init__(self)
   def run(self):
      print("[@] Server: Starting...")
      serverBody()
      print("[@] Server: Exit.")
