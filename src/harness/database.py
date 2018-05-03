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

"""A Generic HTTP Server implementation designed to serve arbitrary files.

Note: This server is only intended for winnforum testing purposes, do not use
this in a production environment.

Example usage:
d = DatabaseServer(
    'Test',
    'localhost',
    8000,
    cert_file='certs/test_cert.crt',
    key_file='certs/test_cert.key',
    ca_cert_file='certs/test_cert_root.pem'
    )
d.setFileToServe('/allsitedata', 'allsitedata1')
d.start()
# DO SOME TESTING
d.setFilesToServe({
    '/allsitedata': 'allsitedata2',
    '/othersitedata': 'othersitedata1'
})
"""

import base64
import logging
import ssl
import threading
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler


# Create the authorization string.
__USERNAME = 'username'
__PASSWORD = 'password'
__AUTHORIZATION_STRING = 'Basic ' + base64.b64encode(USERNAME+':'+PASSWORD)


class DatabaseServer(threading.Thread):
  """A HTTP server which will serve a given file at the given file path."""

  def __init__(self,
               name,
               host_name,
               port,
               https=True,
               cert_file=None,
               key_file=None,
               ca_cert_file=None,
               authorization=False):
    """
    Args:
      name: The server's name, used for logging purposes.
      host_name: The address the server may be accessed at.
      port: The port to serve requests on.
      https: Optional, if True use https else use http.
      path_of_file: The expected path from host_name:port/ to the file. Any
        other path will return a 404 (or other appropriate error).
      initial_file: The file system path of the initial file to serve.
      cert_file: Optional. The file path of the certificate file.
      key_file: Optional. The file path of the key file.
      ca_cert_file: Optional. The file path of the certificate authority
        certificate file.
      authorization: Optional. Iff True require the request to contain the
        authorization header matching the baked in username/password.
    """
    super(DatabaseServer, self).__init__()
    self.name = name
    self.address = host_name + ':' + str(port)
    self.setDaemon(True)
    self.server = DatabaseHTTPServer((host_name, port), DatabaseHandler, name, authorization)
    if https:
      self.server.socket = ssl.wrap_socket(
          self.server.socket,
          certfile=cert_file,
          keyfile=key_file,
          ca_certs=ca_cert_file,
          ssl_version=ssl.PROTOCOL_TLSv1_2,
          server_side=True)

  def run(self):
    """ Starts the HTTPServer as background thread.
    The run() method is an overridden method from thread class and it gets invoked
    when the thread is started using thread.start().
    """

    # Any exceptions in the server should be caught and handled without
    # intervention and not cause it to stop. This is an added safeguard so
    # any unhandled errors will result in:
    #   1) An error being logged (Most important to diagnose problem).
    #   2) An attempt to restart the server (allowing the test to proceed).
    self.stopped = False
    while not self.stopped:
      logging.info('Started Database Server: %s at %s', self.name,
                   self.address)
      try:
        self.server.serve_forever()
      except:
        traceback.print_exc()
        logging.error('HTTPServer %s at %s died on %s, restarting...',
                      self.name, self.address,
                      datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'))
    logging.info('Shutting down Database Server:%s at %s', self.name,
                 self.address)

  def setFileToServe(self, file_url, file_path):
    """Remove existing path mappings and set a single file url to path mapping.

    Args:
      file_url: The url to provide the file on.
      file_path: The file path to provide on the given url.
    """
    self.server.file_paths = {file_url: file_path}

  def setFilesToServe(self, file_url_file_path_dict):
    """Remove existing path mappings and set multiple file url to path mappings.

    Args:
      file_url_file_path_dict: A dictionary of file_url: file_path as described
        in the setFileToServe description.
    """
    self.server.file_paths = file_url_file_path_dict

class DatabaseHTTPServer(HTTPServer):
  def __init__(self, server_address, RequestHandlerClass, name, authorization):
    HTTPServer.__init__(self, server_address, RequestHandlerClass)
    self.name = name
    self.file_paths = {}
    # Encode the username and password for simple comparison. Expected form is:
    #   'Basic Base64RepresentationOfUsername:Password'
    self.authorization = authorization

class DatabaseHandler(SimpleHTTPRequestHandler):
  def translate_path(self, path):
    """Translate URL paths into filepaths."""
    if self.server.authorization:
      # Failed Authorization will return a 401 error and the reason why.
      if 'Authorization' not in self.headers:
        logging.info('Authorization Failed. No Auth header.')
        self.send_response(401)
        self.end_headers()
        self.wfile.write('no auth header received.\n')
        self.wfile.write('Ignore 404 response below.\n\n')
        return ""
      elif self.headers['Authorization'] != __AUTHORIZATION_STRING:
        logging.info('Authorization Failed. Incorrect username:password.')
        self.send_response(401)
        self.end_headers()
        self.wfile.write('Incorrect username:password.\n')
        self.wfile.write('Ignore 404 response below.\n\n')
        return ""
    return self.server.file_paths[path] if path in self.server.file_paths else ""
