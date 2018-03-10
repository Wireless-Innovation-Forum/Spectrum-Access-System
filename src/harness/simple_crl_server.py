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

"""
    A implementation of Certificate Revocation list Server.
"""
import logging
import os
import threading
import urlparse
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler


class CrlServerTestHarness(threading.Thread):
  """
  Implements a CRL server by creating a HTTP server and
  serving CRL files The  CRL server runs as a separate thread
  """

  def __init__(self, host_name, port, crl_url, crl_file_name):
    """
    Constructor for  CRL test harness Requests from SAS Under Test
    Args:
        "host_name": Entity hosting the  crl server
        "port"    : Port number at which  crl server will run
        "crl_url" :  Name of the crl url to be validated
        "crl_file_name" : Name of the crl file
    Returns
    """
    super(CrlServerTestHarness, self).__init__()
    self.host_name = host_name
    self.port = int(port)
    self.crl_url = crl_url
    self.crl_file_name = crl_file_name
    self.setDaemon(True)

  def run(self):
    """
    Starts the HTTPServer as background thread.
    The run() method is an overridden method from thread class and it gets invoked
    when the thread is started using thread.start().
    """
    # Setting the parameters for handler class
    logging.info("Started  CRL Server at %s",
                 self.host_name + ":" + str(self.port))
    self.server = CrlHttpServer(self.crl_url, self.crl_file_name,
                                (self.host_name, self.port),
                                CrlServerTestHarnessHandler)
    self.server.serve_forever()

  def stopServer(self):
    """
    This method is used to stop HTTPServer Socket
    """
    self.server.shutdown()
    logging.info('Stopped CRL Server at %s',
                 self.host_name+":" + str(self.port))


class CrlHttpServer(HTTPServer):
  """ The class CrlHttpServer overrides built-in HTTPServer and takes the
  parameter base_path used to serve the files. This is needed to have CRL Server
  to server files from different directories.
  """
  def __init__(self, crl_url, crl_file_name, server_address, RequestHandlerClass):
    self.crl_url = crl_url
    self.crl_file_name = crl_file_name
    HTTPServer.__init__(self, server_address, RequestHandlerClass)


class CrlServerTestHarnessHandler(BaseHTTPRequestHandler):
  """
  CrlServerTestHarnessHandler class is inherited with BaseHTTPRequestHandler
  to serve HTTP Response.
  """

  def do_GET(self):
    """
    Handles Pull/GET Request and returns Path of the Request to callback Method.
    """

    parsed_path = urlparse.urlparse(self.path)
    self.log_message('Received GET Request:{}'.format(parsed_path.path))
    if parsed_path.path == self.server.crl_url:
      # Handles the GET Requests
      if not os.path.exists(self.server.crl_file_name):
        self.log_message('Requested file:{} not found'.format(parsed_path.path))
        self.send_response(404)
        return
      self.send_response(200)
      self.send_header("Content-type", "application/pkix-crl")
      self.end_headers()
      with open(self.server.crl_file_name) as file_handle:
        self.wfile.write(file_handle.read())
