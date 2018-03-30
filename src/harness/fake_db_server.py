#    Copyright 2018 SAS Project Authors. All Rights Reserved.
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

"""A fake implementation of database server."""

import logging
import threading
import urllib
from urllib2 import URLError
from urlparse import urlparse
from datetime import datetime
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler


class FakeDatabaseTestHarness(threading.Thread):
  """Implements a fake database server.

  A HTTP Server is created to serve PULL/GET requests from SAS UUT.
  """

  def __init__(self, database_file, host_name='localhost', port=80):
    """Initializes the FakeDatabaseTestHarness with the host name and port.

    Args:
      host_name: Host name where the Fake Database Test Harness is executed.
      port: Port number to be used for Fake Database Test Harness.
    """

    super(FakeDatabaseTestHarness, self).__init__()
    self.host_name = host_name
    self.port = port
    self.db_url = "http://" + host_name + ':' + str(port) + '/' + 'db_sync'
    self.db_file_path = database_file
    self.setDaemon(True)
    self.server = FakeDatabaseHttpServer(urlparse(self.db_url).path,
                                         self.db_file_path,
                                         (self.host_name, self.port),
                                         FakeDatabaseTestHarnessHandler)

  def getBaseUrl(self):
    return self.db_url

  def run(self):
    """Starts the HTTP Server as background thread.

    The run() method is an overridden method from thread class and it gets
    invoked when the thread is started using thread.start().
    """

    # Start HTTP server
    logging.info("Started Fake Database Server")
    self.server.serve_forever()

  def shutdown(self):
    """Used to stop HTTPServer.

    The shutdown() method is an overridden method from HTTPServer class and
    it stops the serve_forever() loop.
    """

    # Shut down HTTP Server
    self.server.shutdown()
    logging.info("Stopped Fake Database Harness Server")

  def setDatabaseFile(self, new_database_file):
    """Sets the path of database file.
    
    Takes the parameter new_database_file and sets the variable 
    FakeDatabaseTestHarness class variable db_file_path to point 
    a new file with modified records
    """

    self.db_file_path = new_database_file
    

class FakeDatabaseHttpServer(HTTPServer):
  """FakeDatabaseHttpServer class overrides built-in HTTPServer and takes the 
     parameters db_url_path and db_file_path used to serve the file.
  """

  def __init__(self, db_url_path, db_file_path, server_address, RequestHandlerClass):
    self.db_url_path = db_url_path
    self.db_file_path = db_file_path
    HTTPServer.__init__(self, server_address, RequestHandlerClass)


class FakeDatabaseTestHarnessHandler(BaseHTTPRequestHandler):
  """FakeDatabaseTestHarnessHandler class is inherited with
     BaseHTTPRequestHandler to serve HTTP Response.
  """

  def do_GET(self):
    """Handles PULL/GET requests"""

    parsed_path = urlparse(self.path)
    # If the GET request path does not match the Database URL path then respond
    # with 404 response.
    if parsed_path.path != self.server.db_url_path:
      self.log_message('Requested url :{0} does not match with Database Server URL '
                       'path:{1}'.format(parsed_path.path, self.server.db_url_path))
      self.send_response(404)
      return

    # Downloads the database records in the current directory and 
    # writes 200 OK response in HTTP response stream.
    # If any exception occurs while reading then log the error
    # and respond with 404 'Not Found'.
    try:
      urllib.urlretrieve(self.server.db_file_path, "db_file")
    except URLError:
      self.log_message('There is an error reading file:{}'.format(
          self.server.db_file_path))
      self.send_response(404)
      return
    else:
      self.send_response(200)
      self.end_headers()
      return
