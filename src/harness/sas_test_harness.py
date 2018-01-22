import ssl
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import sas_test_harness_interface
import logging
import json
import ConfigParser
PORT = 9001
CERT_FILE = 'certs/server.cert'
KEY_FILE = 'certs/server.key'
CA_CERT = 'certs/ca.cert'
CIPHERS = [
    'AES128-GCM-SHA256',              # TLS_RSA_WITH_AES_128_GCM_SHA256
    'AES256-GCM-SHA384',              # TLS_RSA_WITH_AES_256_GCM_SHA384
    'ECDHE-ECDSA-AES128-GCM-SHA256',  # TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
    'ECDHE-ECDSA-AES256-GCM-SHA384',  # TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
    'ECDHE-RSA-AES128-GCM-SHA256',    # TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
]


def GetSasTestHarnessUrl():
  config_parser = ConfigParser.RawConfigParser()
  config_parser.read(['sas.cfg'])
  base_url = config_parser.get('SasTestHarness', 'BaseUrl')
  return base_url


class SasTestHarness(sas_test_harness_interface.HttpServerInterface):
  """Test Harness acting as a Http Server to receive Pull/GET
   Requests from SAS Under Test
   parameters: is the dict variable for different types of dump objects.
   schema of parameters: {
   "full_activity" : dict to store full activity dump objects,
   "cbsd_activity": dict to store cbsd activity dump objects,
   "PPA_activity" : dict to store ppa activity dump objects,
   "esc_activity" : dict to store esc activity dump objects
   }
   schema of full_activity {full activity dump object}
   schema of cbsdActivity {"id": {cbsd activity dump object}}
   schema of ppaActivity {"id": {ppa activity dump object}}
   schema of escActivity {"id": {esc activity dump object}}

  """
  def __init__(self):
    self.parameters = {}

  def setupFullActivity(self, full_activity_dump=None):
    self.parameters['fullActivity'] = full_activity_dump

  def setupCbsdActivity(self, unique_id, Cbsd_activity_dump = None):
    self.parameters['cbsdActivity'][unique_id] = Cbsd_activity_dump

  def setupPpaActivity(self, unique_id, PPA_activity_dump = None):
    self.parameters['ppaActivity'][unique_id] = PPA_activity_dump

  def setupEscActivity(self,unique_id, esc_activity_dump = None):
    self.parameter['escActivity'][unique_id] = esc_activity_dump

  def startServer(self):
    request_handler = SasTestHarnessHandler()
    request_handler.setupParameters(self.parameter)
    self.server = HTTPServer(('localhost', PORT),request_handler)
    self.server.socket = ssl.wrap_socket(
      self.server.socket,
      certfile=CERT_FILE,
      keyfile=KEY_FILE,
      ca_certs=CA_CERT,
      cert_reqs=ssl.CERT_REQUIRED,
      ssl_version=ssl.PROTOCOL_TLSv1_2,
      ciphers=':'.join(CIPHERS),
      server_side=True
      )
    logging.info('Started Test Harness Server')
    # Start Server
    self.server.serve_forever()

  def stopServer(self):
    logging.info('Stopped Test Harness Server')
    self.server.shutdown()

class SasTestHarnessHandler(BaseHTTPRequestHandler):

  def setupParameters(self, parameters):
    self._parameters = parameters

  def do_GET(self):
    """Handles Pull/GET Request and returns Path of the Request to callback Method"""
    if self.path == '/dump':
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps(self._parameters['fullActivity']))
    elif "cbsd_activity" in self.path:
      id = self.path.split('/')[-1]
      if id not in self._parameters['cbsdActivity']:
        self.send_error(404)
        return
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps(self._parameters['cbsdActivity'][id]))
    elif "ppa_activity" in self.path:
      id = self.path.split('/')[-1]
      if id not in self._parameters['ppaActivity']:
        self.send_error(404)
        return
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps(self._parameters['ppaActivity'][id]))
    elif "esc_activity" in self.path:
      id = self.path.split('/')[-1]
      if id not in self._parameters['escActivity']:
        self.send_error(404)
        return
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps(self._parameters['escActivity'][id]))
    else:
      self.send_error(404)
