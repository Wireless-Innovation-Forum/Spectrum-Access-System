

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer

class MyHandler(BaseHTTPRequestHandler):

  def do_GET(self):
    print 'Handling GET for ' + str(self.headers)
  
    self.send_response(200) 
    self.send_header('Content-Type', 'application/json')
    self.end_headers()
    self.wfile.write('{}') 
  

  def do_POST(self):
    print 'Handling POST for ' + str(self.headers)
    self.send_response(200) 
    self.send_header('Content-Type', 'application/json')
    self.end_headers()
    self.wfile.write('{}') 



PORT = 8000

httpd = HTTPServer(("", PORT), MyHandler)

print "serving at port", PORT
httpd.serve_forever()
