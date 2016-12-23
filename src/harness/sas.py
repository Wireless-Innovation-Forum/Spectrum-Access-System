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
import StringIO
import urlparse

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


def _Request(url, request, ssl_cert, ssl_key):
  """Sends HTTPS request.

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
  print 'Request to URL ' + url + ':\n' + request
  conn.setopt(conn.POSTFIELDS, request)
  conn.setopt(conn.TIMEOUT, HTTP_TIMEOUT_SECS)
  conn.perform()
  assert conn.getinfo(pycurl.HTTP_CODE) == 200
  conn.close()
  body = response.getvalue()
  print 'Response:\n' + body
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
    return _Request('https://%s/%s/%s' %
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
    _Request('https://%s/admin/reset' % self._base_url, None,
             self._GetDefaultAdminSSLCertPath(),
             self._GetDefaultAdminSSLKeyPath())

  def _GetDefaultAdminSSLCertPath(self):
    return 'client.cert'

  def _GetDefaultAdminSSLKeyPath(self):
    return 'client.key'
