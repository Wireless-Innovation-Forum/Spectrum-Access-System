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

"""A fake implementation of database.
A local test server could be run by using "python fake_db_server.py".
"""

import json
import logging
import os
import threading
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler


class FakeDatabaseTestHarness(threading.Thread):

  def __init__(self, path, host_name, port, database_file):
    """Test Harness acting as a HTTP Server to receive Pull/GET
    Requests from SAS UUT.

    Args:
      path:          Path to the database file
      host_name:     Host name of Fake Database Test Harness that the SAS UUT
                     should connect to for FDB records.
      database_File: Actual database file
      port:          Port of Fake Database Test Harness host where http server
                     is configured
    """
    super(FakeDatabaseTestHarness, self).__init__()
    self.path = path
    self.host_name = host_name
    self.port = port
    self.database_file = database_file
    self.server = None
    self.setDaemon(True)

  def __del__(self):
    # Delete database file
    os.remove(self.database_file)

  def run(self):
    """ Starts the HTTP Server as background thread.
        The run() method is an overridden method from thread
        class and it gets invoked when the thread is started
        using thread.start().
    """
    self.server = FakeDatabaseHttpServer(
        self.path,
        self.database_file,
        (self.host_name, self.port),
        FakeDatabaseTestHarnessHandler)
    # Start HTTP server
    self.server.serve_forever()
    logging.info("Started Test Harness Server")

  def shutdown(self):
    """The shutdown() method is an overridden method from HTTPServer class and
    it tells the serve_forever() loop to stop.
    """
    # Shut down HTTP Server
    self.server.shutdown()
    logging.info("Stopped Test Harness Server")


class FakeDatabaseHttpServer(HTTPServer):
  """ The class FakeDatabaseHttpServer overrides built-in HTTPServer and
      takes the parameter base_path used to serve the file(s).
  """
  def __init__(self, base_path, database_file, server_address, RequestHandlerClass):
    self.base_path = base_path
    self.database_file = database_file
    HTTPServer.__init__(self, server_address, RequestHandlerClass)


class FakeDatabaseTestHarnessHandler(BaseHTTPRequestHandler):
  """FakeDatabaseTestHarnessHandler class is inherited with
     BaseHTTPRequestHandler to serve HTTP Response
  """
  def do_POST(self):
    """Handles POST requests"""
    raise ValueError('Unexpected POST request is received.')

  def do_GET(self):
    """Handles GET requests"""
    if self.path == self.server.base_path:
      data = json.load(open(self.server.database_file))
      self.wfile.write(json.dumps(data))
    else:
      self.wfile.write("\n DB NOT FOUND \n")
      self.send_response(404)
      return
    self.send_response(200)
