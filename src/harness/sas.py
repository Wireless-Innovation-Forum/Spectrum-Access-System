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
"""Implementation of SasInterface."""

import ConfigParser
import json
import logging
import StringIO
import urlparse
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import ssl
import threading
import pycurl
import sas_interface

HTTP_TIMEOUT_SECS = 30
CA_CERT = 'ca.cert'
CIPHERS = [
    'AES128-GCM-SHA256', 'AES256-GCM-SHA384', 'ECDHE-RSA-AES128-GCM-SHA256'
]


def GetTestingSas():
  config_parser = ConfigParser.RawConfigParser()
  config_parser.read(['sas.cfg'])
  base_url = config_parser.get('SasConfig', 'BaseUrl')
  version = config_parser.get('SasConfig', 'Version')
  return SasImpl(base_url, version), SasAdminImpl(base_url)

def GetServer():
  config_parser = ConfigParser.RawConfigParser()
  config_parser.read(['sas.cfg'])
  server_base_url = config_parser.get('HttpServer', 'BaseUrl')
  server_port = int(config_parser.get('HttpServer', 'Port'))
  return HttpServer({'baseUrl': server_base_url, 'port': server_port})

def _RequestPost(url, request, ssl_cert, ssl_key):
  """Sends HTTPS POST request.

  Args:
    url: Destination of the HTTPS request.
    request: Content of the request.
    ssl_cert: Path of SSL cert used in HTTPS request.
    ssl_key: Path of SSL key used in HTTPS request.
  Returns:
    A dictionary represents the JSON response received from server.
  """
  response = StringIO.StringIO()
  conn = pycurl.Curl()
  conn.setopt(conn.URL, url)
  conn.setopt(conn.WRITEFUNCTION, response.write)
  header = [
      'Host: %s' % urlparse.urlparse(url).hostname,
      'content-type: application/json'
  ]
  conn.setopt(conn.VERBOSE, 3)
  conn.setopt(conn.SSLVERSION, conn.SSLVERSION_TLSv1_2)
  conn.setopt(conn.SSLCERTTYPE, 'PEM')
  conn.setopt(conn.SSLCERT, ssl_cert)
  conn.setopt(conn.SSLKEY, ssl_key)
  conn.setopt(conn.CAINFO, CA_CERT)
  conn.setopt(conn.HTTPHEADER, header)
  conn.setopt(conn.SSL_CIPHER_LIST, ':'.join(CIPHERS))
  conn.setopt(conn.POST, True)
  request = json.dumps(request) if request else ''
  logging.debug('Request to URL ' + url + ':\n' + request)
  conn.setopt(conn.POSTFIELDS, request)
  conn.setopt(conn.TIMEOUT, HTTP_TIMEOUT_SECS)
  conn.perform()
  assert conn.getinfo(pycurl.HTTP_CODE) == 200, conn.getinfo(pycurl.HTTP_CODE)
  conn.close()
  body = response.getvalue()
  logging.debug('Response:\n' + body)
  return json.loads(body)

def _RequestGet(url, ssl_cert, ssl_key):
  """Sends HTTPS GET request.

  Args:
    url: Destination of the HTTPS request.
    ssl_cert: Path of SSL cert used in HTTPS request.
    ssl_key: Path of SSL key used in HTTPS request.
  Returns:
    A dictionary represents the JSON response received from server.
  """
  response = StringIO.StringIO()
  conn = pycurl.Curl()
  conn.setopt(conn.URL, url)
  conn.setopt(conn.WRITEFUNCTION, response.write)
  header = [
      'Host: %s' % urlparse.urlparse(url).hostname,
      'content-type: application/json'
  ]
  conn.setopt(conn.VERBOSE, 3)
  conn.setopt(conn.SSLVERSION, conn.SSLVERSION_TLSv1_2)
  conn.setopt(conn.SSLCERTTYPE, 'PEM')
  conn.setopt(conn.SSLCERT, ssl_cert)
  conn.setopt(conn.SSLKEY, ssl_key)
  conn.setopt(conn.CAINFO, CA_CERT)
  conn.setopt(conn.HTTPHEADER, header)
  conn.setopt(conn.SSL_CIPHER_LIST, ':'.join(CIPHERS))
  logging.debug('Request to URL ' + url)
  conn.setopt(conn.TIMEOUT, HTTP_TIMEOUT_SECS)
  conn.perform()
  assert conn.getinfo(pycurl.HTTP_CODE) == 200, conn.getinfo(pycurl.HTTP_CODE)
  conn.close()
  body = response.getvalue()
  logging.debug('Response:\n' + body)
  return json.loads(body)

class SasImpl(sas_interface.SasInterface):
  """Implementation of SasInterface for SAS certification testing."""

  def __init__(self, base_url, sas_version):
    self._base_url = base_url
    self._sas_version = sas_version

  def Registration(self, request, ssl_cert=None, ssl_key=None):
    return self._CbsdRequest('registration', request, ssl_cert, ssl_key)

  def SpectrumInquiry(self, request, ssl_cert=None, ssl_key=None):
    return self._CbsdRequest('spectrumInquiry', request, ssl_cert, ssl_key)

  def Grant(self, request, ssl_cert=None, ssl_key=None):
    return self._CbsdRequest('grant', request, ssl_cert, ssl_key)

  def Heartbeat(self, request, ssl_cert=None, ssl_key=None):
    return self._CbsdRequest('heartbeat', request, ssl_cert, ssl_key)

  def Relinquishment(self, request, ssl_cert=None, ssl_key=None):
    return self._CbsdRequest('relinquishment', request, ssl_cert, ssl_key)

  def Deregistration(self, request, ssl_cert=None, ssl_key=None):
    return self._CbsdRequest('deregistration', request, ssl_cert, ssl_key)

  def _CbsdRequest(self, method_name, request, ssl_cert=None, ssl_key=None):
    return _RequestPost('https://%s/%s/%s' %
                        (self._base_url, self._sas_version, method_name), request,
                        ssl_cert if ssl_cert else self._GetDefaultCbsdSSLCertPath(),
                        ssl_key if ssl_key else self._GetDefaultCbsdSSLKeyPath())

  def _GetDefaultCbsdSSLCertPath(self):
    return 'client.cert'

  def _GetDefaultCbsdSSLKeyPath(self):
    return 'client.key'


class SasAdminImpl(sas_interface.SasAdminInterface):
  """Implementation of SasAdminInterface for SAS certification testing."""

  def __init__(self, base_url):
    self._base_url = base_url

  def Reset(self):
    _RequestPost('https://%s/admin/reset' % self._base_url, None,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def InjectFccId(self, request):
    _RequestPost('https://%s/admin/injectdata/fccId' % self._base_url, request,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def InjectEscZone(self, request):
    return _RequestPost('https://%s/admin/injectdata/esc_zone' % self._base_url, request,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def InjectZoneData(self, request):
    return _RequestPost('https://%s/admin/injectdata/zone' % self._base_url,
                        request, self._GetDefaultAdminSSLCertPath(),
                        self._GetDefaultAdminSSLKeyPath())

  def InjectPalDatabaseRecord(self, request):
    _RequestPost('https://%s/admin/injectdata/pal_database_record' %
                 self._base_url, request,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def InjectClusterList(self, request):
    _RequestPost('https://%s/admin/injectdata/cluster_list' % self._base_url,
                 request, self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def BlacklistByFccId(self, request):
    _RequestPost('https://%s/admin/injectdata/blacklist_fcc_id' % self._base_url, request,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def BlacklistByFccIdAndSerialNumber(self, request):
    _RequestPost('https://%s/admin/injectdata/blacklist_fcc_id_and_serial_number' %
                 self._base_url, request,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def TriggerEscZone(self, request):
    _RequestPost('https://%s/admin/trigger/esc_detection' % self._base_url, request,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def ResetEscZone(self, request):
    _RequestPost('https://%s/admin/trigger/esc_reset' % self._base_url, request,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())
    
  def PreloadRegistrationData(self, request):
    _RequestPost('https://%s/admin/injectdata/conditional_registration' % self._base_url,
                 request, self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def InjectFss(self, request):
    _RequestPost('https://%s/admin/injectdata/fss' % self._base_url, request,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def InjectWisp(self, request):
    _RequestPost('https://%s/admin/injectdata/wisp' % self._base_url, request,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def InjectSasAdministratorRecord(self, request):
    _RequestPost('https://%s/admin/injectdata/sas_admin' % self._base_url, request,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def TriggerMeasurementReportRegistration(self, request):
    _RequestPost('https://%s/admin/trigger/meas_report_in_registration_response' % self._base_url, request,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def TriggerMeasurementReportHeartbeat(self, request):
    _RequestPost('https://%s/admin/trigger/meas_report_in_heartbeat_response' % self._base_url, request,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def InjectSasImplementationRecord(self, request):
    _RequestPost('https://%s/admin/injectdata/sas_impl' % self._base_url, request,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def InjectEscSensorDataRecord(self, request):
    _RequestPost('https://%s/admin/injectdata/esc_sensor' % self._base_url, request,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def _GetDefaultAdminSSLCertPath(self):
    return 'client.cert'

  def _GetDefaultAdminSSLKeyPath(self):
    return 'client.key'

class HttpServerHandler(BaseHTTPRequestHandler):
  def __init__(self, callbackHandler, getSetupParameters, *args):
    self._parameters = getSetupParameters()
    self._callbackHandler = callbackHandler
    BaseHTTPRequestHandler.__init__(self, *args)

  def do_GET(self):
    """Handles Pull/GET Request and returns Path of the Request to callback Method"""
    if self.path == self._parameters['expectedPath']:
      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps(self._parameters['responseBody']))
      self._callbackHandler(self.path)
    else:
      self.send_response(404)
      self._callbackHandler()

  def do_POST(self):
    """Handles Push/POST Request and returns Request Body to callback Method"""
    length = int(self.headers.getheader('content-length'))
    if length > 0:
      try:
        request_body = json.loads(self.rfile.read(length))
        if self.path == self._parameters['expectedPath']:
          self.send_response(200)
          self.send_header('Content-type', 'application/json')
          self.end_headers()
          self.wfile.write(json.dumps(self._parameters['responseBody']))
          self._callbackHandler(request_body)
          return
        else:
          self.send_response(404)
      except ValueError:
        self.send_response(422)
    self._callbackHandler()

class HttpServer(sas_interface.HttpServerInterface):
  """Test Harness acting as a Http Server to receive Pull/GET and Push/POST 
  Requests from SAS Under Test
  """
  def __init__(self, server_details):
    self._server_details = server_details
    self._request_event = threading.Event()
    self.parameters = {}
    self.response = None

  # Helper Methods Starts

  def _callbackHandler(self, response=None):
    """Release wait initiated by _requestResponse when there is GET/POST Request from 
    SAS Under Test"""
    self.response = response
    self._request_event.set()

  def _handleRequest(self, callbackHandler, getSetupParameters):
    """Returns Http Server Handler Method"""
    return lambda *args: HttpServerHandler(callbackHandler, getSetupParameters, *args)

  def _getSetupParameters(self):
    """Returns Response Body and Expected Path setup by the testcase"""
    return self.parameters

  def _requestResponse(self):
    """Initiate wait till timeout to get the response from SAS Under Test and then 
    return the response as soon as _callbackHandler is called"""
    logging.info("Waiting for the Response from SAS Under Test")
    self._request_event.wait(20.0)
    return self.response

  # Helper Methods Ends

  def setupServer(self, parameters=None):
    self.parameters = parameters
    return self._requestResponse

  def getBaseUrl(self):
    return 'https://%s:%d' % (self._server_details['baseUrl'], self._server_details['port'])

  def StartServer(self):
    request_handler = self._handleRequest(self._callbackHandler, self._getSetupParameters)
    self.server = HTTPServer((self._server_details['baseUrl'], self._server_details['port']),
                             request_handler)
    cert_file = 'server.cert'
    key_file = 'server.key'
    ca_cert = 'ca.cert'
    ciphers = [
      'AES128-GCM-SHA256', 'AES256-GCM-SHA384', 'ECDHE-RSA-AES128-GCM-SHA256'
    ]
    self.server.socket = ssl.wrap_socket(
      self.server.socket,
      certfile=cert_file,
      keyfile=key_file,
      ca_certs=ca_cert,
      cert_reqs=ssl.CERT_REQUIRED,
      ssl_version=ssl.PROTOCOL_TLSv1_2,
      ciphers=':'.join(ciphers),
      server_side=True)

    logging.info('Started Test Harness Server at %s' % self.getBaseUrl())

    # Start Server in a separate thread
    server_start = threading.Thread(target=self.server.serve_forever)
    server_start.daemon = True
    server_start.start()

  def StopServer(self):
    logging.info('Stopped Test Harness Server')
    self.server.shutdown()