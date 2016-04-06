# Copyright 2016 SAS Project Authors. All Rights Reserved.
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

# This script runs a mock SAS server on a given port. The object used to
# create the mock may be maintained for external control of responses for
# testing. When run standalone, the script will launch the mock server
# on the passed port.
#
# The mock server is currently a placeholder for a mocking capability which
# will allow different checks and responses to be implemented in future work.

import cgi
import json
import socket
import ssl
import sys
import getopt
import BaseHTTPServer
import SocketServer
import OpenSSL

class SASHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  # Note: this is needed to support HTTPS in the request handler.
  def setup(self):
    self.connection = self.request
    self.rfile = socket._fileobject(self.request, 'rb', self.rbufsize)
    self.wfile = socket._fileobject(self.request, 'wb', self.wbufsize)

  def findmethod(self):
    if self.path.startswith(self.server.sas_cbsd_prefix):
      pieces = self.path[len(self.server.sas_cbsd_prefix):].split('/')
      sas_cbsd_method = pieces[0]
      print 'Calling sas-cbsd method', sas_cbsd_method
      if sas_cbsd_method == 'registration':
        return self.server.handleRegistration
      elif sas_cbsd_method == 'spectrumInquiry':
        return self.server.handleSpectrumInquiry
      elif sas_cbsd_method == 'grant':
        return self.server.handleGrantRequest
      elif sas_cbsd_method == 'heartbeat':
        return self.server.handleHeartbeat
      elif sas_cbsd_method == 'relinquishment':
        return self.server.handleRelinquishRequest
      elif sas_cbsd_method == 'deregistration':
        return self.server.handleDeregistration
      else:
        return None
    elif self.path.startswith(self.server.sas_sas_prefix):
      pieces = self.path[len(self.server.sas_sas_prefix):].split('/')
      sas_sas_method = pieces[0]
      print 'Calling sas-sas method', sas_sas_method
      if sas_sas_method == 'sas_admin':
        return self.server.handleSasAdministrator
      elif sas_sas_method == 'esc_admin':
        return self.server.handleEscAdministrator
      elif sas_sas_method == 'sas':
        return self.server.handleSasImplementation
      elif sas_sas_method == 'esc':
        return self.server.handleEscImplementation
      elif sas_sas_method == 'cbsd_type':
        return self.server.handleCbsdDeviceType
      elif sas_sas_method == 'cbsd':
        return self.server.handleCbsdRecord
      elif sas_sas_method == 'incumbent':
        return self.server.handleIncumbentRecord
      elif sas_sas_method == 'zone':
        return self.server.handleZone
      elif sas_sas_method == 'operator':
        return self.server.handleCbsdOperator
      elif sas_sas_method == 'domain':
        return self.server.handleDomainProxy
      elif sas_sas_method == 'any':
        return self.server.handleWildcard
      elif sas_sas_method == 'dump':
        return self.server.handleActivityDump
      else:
        return None
    else:
      return None


  def send_error(self, code, message):
      self.send_response(code)
      self.send_header('Content-type', 'text/plain')
      self.end_headers()
      self.wfile.write(message)

  def do_GET(self):
    # cert = self.server.socket.getpeercert()
    method = self.findmethod()
    if method == None:
      print 'No method found'
      self.send_error(404, 'Bad request method')
      return

    result = method(self.path, {})

    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    self.wfile.write(json.dumps(result))

  def do_POST(self):
    method = self.findmethod()
    if method == None:
      print 'No method found'
      self.send_error(404, 'Bad request method')
      return

    # cert = self.server.socket.getpeercert()
    print(self.headers)
    ctype = cgi.parse_header(self.headers.getheader('content-type'))
    print ctype[0]
    if ctype[0] == 'application/json':
      try:
        content = self.rfile.read(int(self.headers.getheader('content-length')))
        request = json.loads(content)
      except:
        print 'Error parsing json'
        self.send_error(400, 'Unparseable JSON input')
        return
    else:
      self.send_error(415, 'Must deliver application/json input')
      return

    result = method(self.path, request)

    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    self.wfile.write(json.dumps(result))


class MockSASServer(BaseHTTPServer.HTTPServer):
  def __init__(self, port, certfile, keyfile):
    BaseHTTPServer.HTTPServer.__init__(self, ('', port), SASHandler)
    self.socket = ssl.SSLSocket(
        socket.socket(self.address_family, self.socket_type),
        keyfile=keyfile,
        certfile=certfile)
    # TODO: need to add TLS options to make sure bidirectional auth is supported
    # self.socket.context.options = ssl.SSL.PROTOCOL_TLSv1_2
    # self.socket.context.verify_mode = ssl.SSL.CERT_REQUIRED
    # self.socket.context.verify_flags = ssl.SSL.VERIFY_CRL_CHECK_LEAF
    # self.socket.context.load_verify_locations(cafile=cafile)
    self.server_bind()
    self.server_activate()
    self.msg = 'TALK TO SERVER'
    print 'Configured mock SAS with port=%d' % self.server_port

    # TODO: pull out these parameters and responses into an interface object?
    # If not, set from a config object.
    self.sas_cbsd_prefix = '/cbsd/v1.0/'
    self.sas_sas_prefix = '/sas/v1.0/'

  # SAS-CBSD methods

  def handleRegistration(self, path, requestJson):
    print 'handleRegistration in mock SAS'
    return {'hello': 'world'}

  def handleDeregistration(self, path, requestJson):
    return {}

  def handleSpectrumInquiry(self, path, requestJson):
    return {}

  def handleGrantRequest(self, path, requestJson):
    print 'Got grant request'
    return {}

  def handleRelinquishRequest(self, path, requestJson):
    return {}

  def handleHeartbeat(self, path, requestJson):
    return {}

  # SAS-SAS methods

  def handleSasAdministrator(self, path, requestJson):
    return {}

  def handleSasImplementation(self, path, requestJson):
    return {}

  def handleEscAdministrator(self, path, requestJson):
    return {}

  def handleEscImplementation(self, path, requestJson):
    return {}

  def handleCbsdDeviceType(self, path, requestJson):
    print 'Got request for cbsd device type ' + path
    return {}

  def handleCbsdRecord(self, path, requestJson):
    return {}

  def handleIncumbentRecord(self, path, requestJson):
    return {}

  def handleZone(self, path, requestJson):
    return {}

  def handleCbsdOperator(self, path, requestJson):
    return {}

  def handleDomainProxy(self, path, requestJson):
    return {}

  def handleWildcard(self, path, requestJson):
    return {}

  def handleActivityDump(self, path, requestJson):
    return {}


def runMockSAS():
  portArg = 8008  # default port
  try:
    options, args = getopt.getopt(sys.argv[1:], '', 'port=')
    for o, a in options:
      if o == '--port':
        portArg = int(a)
  except getopt.GetoptError as err:
    print 'Error reading options for Mock SAS Server'
    print str(err)
    sys.exit(2)
  except ValueError as err:
    print 'Error parsing port number. Use a number'
    print str(err)
    sys.exit(2)

  server = MockSASServer(portArg, 'server.crt', 'server.key')
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    pass
  server.server_close()
  print '\nMock server shutdown\n'

if __name__ == '__main__':
  runMockSAS()

