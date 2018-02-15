#    Copyright 2016 SAS Project Authors. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""A fake implementation of database.

A local test server could be run by using "python fake_db_server.py".

"""

import json
import threading
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler


class FakeDatabaseTestHarness(threading.Thread):
  
  def __init__(self, url = None, database_file = None, path = None, host_name = None, port = None):
    """Test Harness acting as a Http Server to receive Pull/GET
    Requests from SAS Under Test
    parameters: is the dict variable for database.
    schema of parameters: {
    "path": path to the database file
    "url": actual url   
    "database_file" : actual database file
    "port" : port number at which fake database server will run
    "host_name":  
    """
    super(FakeDatabaseTestHarness, self).__init__()
    self.parameters = {
        "path" : ''.join( ('/', url.split('/',3)[3]) ) ,
        "url" : url ,
        "host_name" : (url.split('/')[2]).split(':')[0] ,
        "database_file" : database_file ,
        "port" : int( (url.split('/')[2]).split(':')[1] )
    }
    self.daemon = True

  def run(self):
   self.startServer()

  def startServer(self):
    request_handler = FakeDatabaseTestHarnessHandler()
    request_handler.setupParameters(self.parameters)

    self.server = HTTPServer( (request_handler._parameters['host_name'],request_handler._parameters['port'] ), request_handler )
    self.server.serve_forever()
    logging.info('Started Test Harness Server')

class FakeDatabaseTestHarnessHandler(BaseHTTPRequestHandler):

  def __init__(self):
    #pass
    super(FakeDatabaseTestHarnessHandler, self).__init__()

  def setupParameters(self, parameters):
    self._parameters = parameters

  def do_POST(self):
    """Handles POST requests"""
    pass 

  def do_GET(self):
    """Handles GET requests"""
    print self.path    
    if self.path == self._parameters['path']:
      data = json.load(open(self._parameters['database_file']))
      return self.wfile.write(data)     
    else:
      self.wfile.write("\n DB NOT FOUND \n")
      self.send_response(404)
      return
        
    self.wfile.write("\n\n")
    self.send_response(200)
