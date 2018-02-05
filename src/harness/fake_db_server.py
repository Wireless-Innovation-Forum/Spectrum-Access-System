from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import json


 
PORT = 9090


class FakeDBHandler(BaseHTTPRequestHandler):
 
  def do_POST(self):
    """Handles POST requests"""
    pass 


  def do_GET(self):
    """Handles GET requests"""
    
    print self.path    

    if self.path == "/fakedatabase/exclusionZone":
      data = json.load(open("fakedatabase/exclusion_zone_db.json"))
      self.wfile.write(data['record_0'])
      self.wfile.write("\n")
      self.wfile.write(data['record_1'])      
    
    else:
      self.wfile.write("\n DB NOT FOUND \n")
      self.send_response(404)
      return
        
    self.wfile.write("\n\n")
    self.send_response(200)


def RunFakeDBServer():
  server = HTTPServer(('localhost', PORT),FakeDBHandler)
  
  print ('Will start Fake DB server at :', PORT)

  server.serve_forever()
  print 'server started'



if __name__ == '__main__':
   RunFakeDBServer()
