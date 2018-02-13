"""A fake implementation of database.

A local test server could be run by using "python fake_db_server.py".

"""

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import json
import threading


class FakeDatabaseTestHarness(threading.Thread):
  """Test Harness acting as a Http Server to receive Pull/GET
  Requests from SAS Under Test
  parameters: is the dict variable for database.
  schema of parameters: {
  "path": path to the database file
  "url": actual url 
  "hostName" : 
  "databaseFile" : actual database file
  "PORT" : port number at which fake database server will run 
  """
  
  def __init__(self, url = None, databaseFile = None, path = None, hostName = None, Port = None):
  
    super(FakeDatabaseTestHarness, self).__init__()
    self.parameters = {
        "path" : ''.join( ('/', url.split('/',3)[3]) ) ,
        "url" : url ,
        "hostName" : (url.split('/')[2]).split(':')[0] ,
        "databaseFile" : databaseFile ,
        "PORT" : int( (url.split('/')[2]).split(':')[1] )
    }
    self.daemon = True

  def run(self):
   self.startServer()

  def startServer(self):
    request_handler = FakeDatabaseTestHarnessHandler()
    request_handler.setupParameters(self.parameters)
    server = HTTPServer( (request_handler._parameters['hostName'],request_handler._parameters['PORT'] ), request_handler )
    print ('Will start Fake DB server at :', request_handler._parameters['PORT'])
    server.serve_forever()
    logging.info('Started Test Harness Server')


class FakeDatabaseTestHarnessHandler(BaseHTTPRequestHandler):
  def __init__(self):
    pass

  def setupParameters(self, parameters):
    self._parameters = parameters

  def do_POST(self):
    """Handles POST requests"""
    pass 

  def do_GET(self):
    """Handles GET requests"""
    print self.path    
    if self.path == _parameters['path']:
      data = json.load(open(_parameters['databaseFile']))
      self.wfile.write(data)
      self.wfile.write("\n")
            
    else:
      self.wfile.write("\n DB NOT FOUND \n")
      self.send_response(404)
      return
        
    self.wfile.write("\n\n")
    self.send_response(200)
