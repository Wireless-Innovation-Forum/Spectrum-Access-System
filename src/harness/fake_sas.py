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
"""A fake implementation of SasInterface, based on v1.0 of the SAS-CBSD TS.

A local test server could be run by using "python fake_sas.py".

"""

from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
from datetime import datetime
from datetime import timedelta
import json
import ssl

import sas_interface

# Fake SAS server configurations.
PORT = 9000
CERT_FILE = 'server.cert'
KEY_FILE = 'server.key'
CA_CERT = 'ca.cert'
CIPHERS = [
    'AES128-GCM-SHA256', 'AES256-GCM-SHA384', 'ECDHE-RSA-AES128-GCM-SHA256'
]


class FakeSas(sas_interface.SasInterface):
  """A fake implementation of SasInterface.

  Returns success for all requests with plausible fake values for all required
  response fields.

  """

  def __init__(self):
    pass

  def Registration(self, request, ssl_cert=None, ssl_key=None):
    response = {'registrationResponse': []}
    for req in request['registrationRequest']:
      response['registrationResponse'].append({
          'cbsdId': req['fccId'] + '/' + req['cbsdSerialNumber'],
          'response': self._GetSuccessResponse()
      })
    return response

  def SpectrumInquiry(self, request, ssl_cert=None, ssl_key=None):
    response = {'spectrumInquiryResponse': []}
    for req in request['spectrumInquiryRequest']:
      response['spectrumInquiryResponse'].append({
          'cbsdId': req['cbsdId'],
          'availableChannel': {
              'frequencyRange': {
                  'lowFrequency': 3620000000,
                  'highFrequency': 3630000000
              },
              'channelType': 'GAA',
              'ruleApplied': 'FCC_PART_96'
          },
          'response': self._GetSuccessResponse()
      })
    return response

  def Grant(self, request, ssl_cert=None, ssl_key=None):
    response = {'grantResponse': []}
    for req in request['grantRequest']:
      response['grantResponse'].append({
          'cbsdId': req['cbsdId'],
          'grantId': 'fake_grant_id_%s' % datetime.utcnow().isoformat(),
          'channelType': 'GAA',
          'response': self._GetSuccessResponse()
      })
    return response

  def Heartbeat(self, request, ssl_cert=None, ssl_key=None):
    response = {'heartbeatResponse': []}
    for req in request['heartbeatRequest']:
      transmit_expire_time = datetime.utcnow().replace(
          microsecond=0) + timedelta(minutes=1)
      response['heartbeatResponse'].append({
          'cbsdId': req['cbsdId'],
          'grantId': req['grantId'],
          'transmitExpireTime': transmit_expire_time.isoformat() + 'Z',
          'response': self._GetSuccessResponse()
      })
    return response

  def Relinquishment(self, request, ssl_cert=None, ssl_key=None):
    response = {'relinquishmentResponse': []}
    for req in request['relinquishmentRequest']:
      response['relinquishmentResponse'].append({
          'cbsdId': req['cbsdId'],
          'grantId': req['grantId'],
          'response': self._GetSuccessResponse()
      })
    return response

  def Deregistration(self, request, ssl_cert=None, ssl_key=None):
    response = {'deregistrationResponse': []}
    for req in request['deregistrationRequest']:
      response['deregistrationResponse'].append({
          'cbsdId': req['cbsdId'],
          'response': self._GetSuccessResponse()
      })
    return response

  def _GetSuccessResponse(self):
    return {'responseCode': 0}


class FakeSasHandler(BaseHTTPRequestHandler):

  def do_POST(self):
    """Handles POST requests."""

    length = int(self.headers.getheader('content-length'))
    if length > 0:
      request = json.loads(self.rfile.read(length))
    if self.path == '/v1.0/registration':
      response = FakeSas().Registration(request)
    elif self.path == '/v1.0/spectrumInquiry':
      response = FakeSas().SpectrumInquiry(request)
    elif self.path == '/v1.0/grant':
      response = FakeSas().Grant(request)
    elif self.path == '/v1.0/heartbeat':
      response = FakeSas().Heartbeat(request)
    elif self.path == '/v1.0/relinquishment':
      response = FakeSas().Relinquishment(request)
    elif self.path == '/v1.0/deregistration':
      response = FakeSas().Deregistration(request)
    elif self.path == '/admin/reset':
      response = ''
    elif self.path == '/admin/injectdata/fccId':
      response = ''
    else:
      self.send_response(400)
      return
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    self.wfile.write(json.dumps(response))


if __name__ == '__main__':
  server = HTTPServer(('localhost', PORT), FakeSasHandler)
  server.socket = ssl.wrap_socket(
      server.socket,
      certfile=CERT_FILE,
      keyfile=KEY_FILE,
      ca_certs=CA_CERT,
      cert_reqs=ssl.CERT_REQUIRED,
      ssl_version=ssl.PROTOCOL_TLSv1_2,
      ciphers=':'.join(CIPHERS),
      server_side=True)

  print 'Will start server at localhost:%d, use <Ctrl-C> to stop.' % PORT
  server.serve_forever()
