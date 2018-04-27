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

"""A Generic HTTP Server implementation designed to serve a single file (for faking databases).
"""

import base64
import logging
import os
import ssl
import threading
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

CIPHERS = [
    'AES128-GCM-SHA256',              # TLS_RSA_WITH_AES_128_GCM_SHA256
    'AES256-GCM-SHA384',              # TLS_RSA_WITH_AES_256_GCM_SHA384
    'ECDHE-ECDSA-AES128-GCM-SHA256',  # TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
    'ECDHE-ECDSA-AES256-GCM-SHA384',  # TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
    'ECDHE-RSA-AES128-GCM-SHA256',    # TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
]

class DatabaseServer(threading.Thread):
  """A HTTP server which will serve a given file at the given file path."""

  def __init__(self,
               name,
               host_name,
               port,
               cert_file=None,
               key_file=None,
               ca_cert_file=None,
               authorization=None,
               protocol='https'):
    """
    Args:
      name: The server's name, used for logging purposes.
      host_name: The address the server may be accessed at.
      port: The port to serve requests on.
      path_of_file: The expected path from host_name:port/ to the file. Any
        other path will return a 404 (or other appropriate error).
      initial_file: The file system path of the initial file to serve.
      cert_file: Optional. The file path of the certificate file.
      key_file: Optional. The file path of the key file.
      ca_cert_file: Optional. The file path of the certificate authority
        certificate file.
      authorization: Optional, contains a string. Iff specified requires the
        authorization header to match the string when decoded.
      protocol: Optional, specifies the protocol type (to be prepended to the
        expected url).
    """
    super(DatabaseServer, self).__init__()
    base_url = protocol + '://' + host_name + ':' + str(port) + '/'
    self.name = name
    self.host_name = host_name
    self.setDaemon(True)
    self.server = DatabaseHTTPServer((host_name, port), DatabaseHandler, name, base_url, authorization)
    if protocol == 'https':
      self.server.socket = ssl.wrap_socket(
          self.server.socket,
          certfile=cert_file,
          #keyfile=key_file,
          ca_certs=ca_cert_file,
          ssl_version=ssl.PROTOCOL_TLSv1_2,
          ciphers=':'.join(CIPHERS),
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
                   self.host_name)
      try:
        self.server.serve_forever()
      except:
        traceback.print_exc()
        logging.error('HTTPServer %s at %s died on %s, restarting...',
                      self.name, self.host_name,
                      datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'))
    logging.info('Shutting down Database Server:%s at %s', self.name,
                 self.host_name)

  def setFileToServe(self, file_url, file_path):
    """Add or update a single file url to path mapping.

    Args:
      file_url: The url to provide the file on.
      file_path: The file path to provide on the given url.
    """
    self.server.file_paths[file_url] = file_path

  def setFilesToServe(self, file_url_file_path_dict):
    """Add or update a multiple file url to path mappings.

    Args:
      file_url_file_path_dict: A dictionary of file_url: file_path as described
        in the setFileToServe description.
    """
    self.server.file_paths.update(file_url_file_path_dict)

class DatabaseHTTPServer(HTTPServer):
  def __init__(self, server_address, RequestHandlerClass, name, base_url, authorization):
    HTTPServer.__init__(self, server_address, RequestHandlerClass)
    self.name = name
    self.base_url = base_url
    self.authorization = authorization
    self.server.file_paths = {}

class DatabaseHandler(SimpleHTTPRequestHandler):
  def translate_path(self, path):
    """Translate URL paths into filepaths."""
    print 'request received'
    print self.headers
    if self.authorization and base64.b64decode(self.headers['Authorization']) != self.authorization:
      # Return an error (404 atm because it's easy to do)
      return ""
    return self.server.file_paths[path] if path in self.server.file_paths else ""


logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

d = DatabaseServer(
    'Test',
    'localhost',
    8000,
    'allsitedata',
    os.path.expanduser('~/allsitedata'),
    cert_file=os.path.expanduser('~/dev_certs/test_cert.pem'),
    key_file=os.path.expanduser('~/dev_certs/test_cert.key'),
    ca_cert_file=os.path.expanduser('~/dev_certs/test_cert_root.pem'),
    authorization='Basic test:pass'
    )
d.start()
raw_input('Press enter to continue: ')
