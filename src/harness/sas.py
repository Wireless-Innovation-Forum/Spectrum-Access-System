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
import os

import pycurl
import sas_interface

HTTP_TIMEOUT_SECS = 30
CA_CERT = os.path.join('certs', 'ca.cert')
CIPHERS = [
    'AES128-GCM-SHA256',              # TLS_RSA_WITH_AES_128_GCM_SHA256
    'AES256-GCM-SHA384',              # TLS_RSA_WITH_AES_256_GCM_SHA384
    'ECDHE-ECDSA-AES128-GCM-SHA256',  # TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
    'ECDHE-ECDSA-AES256-GCM-SHA384',  # TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
    'ECDHE-RSA-AES128-GCM-SHA256',    # TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
]


def GetTestingSas():
  config_parser = ConfigParser.RawConfigParser()
  config_parser.read(['sas.cfg'])
  base_url = config_parser.get('SasConfig', 'BaseUrl')
  version = config_parser.get('SasConfig', 'Version')
  return SasImpl(base_url, version), SasAdminImpl(base_url)

def _RequestPost(url, request, ssl_cert, ssl_key):
  """Sends HTTPS POST request.

  Args:
    url: Destination of the HTTPS request.
    request: Content of the request.
    ssl_cert: Path of SSL cert used in HTTPS request.
    ssl_key: Path of SSL key used in HTTPS request.
  Returns:
    A dictionary represents the JSON response received from server.
  Raises:
    AssertionError: with args[0] is an integer code representing:
      * libcurl SSL code response, if code < 100:
        https://curl.haxx.se/libcurl/c/libcurl-errors.html
      * HTTP code response, if code >= 100:
        https://en.wikipedia.org/wiki/List_of_HTTP_status_codes)
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
  try:
    conn.perform()
  except pycurl.error as e:
    # e contains a tuple (libcurl_error_code, string_description).
    # See https://curl.haxx.se/libcurl/c/libcurl-errors.html
    raise AssertionError(e.args[0])
  http_code = conn.getinfo(pycurl.HTTP_CODE)
  conn.close()
  body = response.getvalue()
  logging.debug('Response:\n' + body)
  assert http_code == 200, http_code
  if body:
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

def _DownloadFile(url, ssl_cert, ssl_key):
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

  def GetSasImplementationRecord(self, request, ssl_cert=None, ssl_key=None):
    return self._SasRequest('sas_impl', request, ssl_cert, ssl_key)

  def GetFullActivityDump(self, ssl_cert=None, ssl_key=None):
      return self._SasRequest('dump', None, ssl_cert, ssl_key)
    
  def GetEscSensorRecord(self, request, ssl_cert=None, ssl_key=None):
    return self._SasRequest('esc_sensor', request, ssl_cert, ssl_key)

  def _SasRequest(self, method_name, request, ssl_cert=None, ssl_key=None):
    return _RequestGet('https://%s'%'/'.join(value for value in
                        [self._base_url, self._sas_version, method_name, request] if value),
                        ssl_cert if ssl_cert else self._GetDefaultSasSSLCertPath(),
                        ssl_key if ssl_key else self._GetDefaultSasSSLKeyPath())

  def _CbsdRequest(self, method_name, request, ssl_cert=None, ssl_key=None):
    return _RequestPost('https://%s/%s/%s' %
                        (self._base_url, self._sas_version, method_name), request,
                        ssl_cert if ssl_cert else self._GetDefaultCbsdSSLCertPath(),
                        ssl_key if ssl_key else self._GetDefaultCbsdSSLKeyPath())

  def DownloadFile(self, url, ssl_cert=None, ssl_key=None):
    return _DownloadFile('%s' % url,
                 ssl_cert if ssl_cert else self._GetDefaultAdminSSLCertPath(),
                 ssl_key if ssl_key else self._GetDefaultAdminSSLKeyPath())

  def _GetDefaultCbsdSSLCertPath(self):
    return os.path.join('certs', 'client.cert')

  def _GetDefaultCbsdSSLKeyPath(self):
    return os.path.join('certs', 'client.key')

  def _GetDefaultSasSSLCertPath(self):
    return os.path.join('certs', 'client.cert')

  def _GetDefaultSasSSLKeyPath(self):
    return os.path.join('certs', 'client.key')

class SasAdminImpl(sas_interface.SasAdminInterface):
  """Implementation of SasAdminInterface for SAS certification testing."""

  def __init__(self, base_url):
    self._base_url = base_url

  def Reset(self):
    _RequestPost('https://%s/admin/reset' % self._base_url, None,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def InjectFccId(self, request):
    if 'fccMaxEirp' not in request:
      request['fccMaxEirp'] = 47
    _RequestPost('https://%s/admin/injectdata/fcc_id' % self._base_url, request,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def InjectUserId(self, request):
    _RequestPost('https://%s/admin/injectdata/user_id' % self._base_url,
                 request,
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

  def TriggerMeasurementReportRegistration(self):
    _RequestPost('https://%s/admin/trigger/meas_report_in_registration_response' %
                 self._base_url, None,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def TriggerMeasurementReportHeartbeat(self):
    _RequestPost('https://%s/admin/trigger/meas_report_in_heartbeat_response' %
                 self._base_url, None,
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

  def TriggerFullActivityDump(self):
      _RequestPost('https://%s/admin/trigger/create_full_activity_dump' % self._base_url, None,
                   self._GetDefaultAdminSSLCertPath(),
                   self._GetDefaultAdminSSLKeyPath())

  def TriggerPpaCreation(self, request):
    return _RequestPost('https://%s/admin/trigger/create_ppa' %
                        self._base_url, request,
                        self._GetDefaultAdminSSLCertPath(),
                        self._GetDefaultAdminSSLKeyPath())

  def TriggerDailyActivitiesImmediately(self):
    _RequestPost('https://%s/admin/trigger/daily_activities_immediately' %
                 self._base_url, None,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def GetDailyActivitiesStatus(self):
    return _RequestPost('https://%s/admin/get_daily_activities_status' %
                 self._base_url, None,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def InjectCpiUser(self, request):
    _RequestPost('https://%s/admin/injectdata/cpi_user' %
                 self._base_url, request,
                 self._GetDefaultAdminSSLCertPath(),
                 self._GetDefaultAdminSSLKeyPath())

  def _GetDefaultAdminSSLCertPath(self):
    return os.path.join('certs', 'admin_client.cert')

  def _GetDefaultAdminSSLKeyPath(self):
    return os.path.join('certs', 'admin_client.key')
