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
""" Implementation of CbsdSasInterface """

import ConfigParser
import json
import StringIO
import urlparse
import logging
import pycurl

import cbsd_sas_interface
import admin_sas_interface

LOG_FILE = 'log/cbsd_sas.log'
LOG_FORMAT = logging.Formatter(
    '%(asctime)-15s - CbsdSas - '
    '%(funcName)s - %(levelname)s - %(message)s')
HTTP_TIMEOUT_SECS = 30
CIPHERS = ':'.join([
    'RSA-AES128-GCM-SHA256',
    'RSA-AES256-GCM-SHA384',
    'ECDHE-ECDSA-AES128-GCM-SHA256',
    'ECDHE-ECDSA-AES256-GCM-SHA384',
    'ECDHE-RSA-AES128-GCM-SHA256'])


def GetTestingSas():

    # Logging Instance creation
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    # Handle set-up
    handler = logging.FileHandler(LOG_FILE)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(LOG_FORMAT)
    # Couple handler to logging instance
    logger.addHandler(handler)

    config_parser = ConfigParser.RawConfigParser()
    config_parser.optionxform = str
    config_parser.read(['tests/sas.cfg'])
    config = {k: v for (k, v) in config_parser.items('SasConfig')}
    return CbsdSasImpl(logger, config), AdminSasImpl(logger, config)


def _Request(logger, url, request, ssl_ca, ssl_cert, ssl_key, ssl_pp):
    """Sends HTTPS request.

    Args:
      url: Destination of the HTTPS request.
      request: Content of the request.
      ssl_ca: Patht of SSL CA cert used in HTTPS request.
      ssl_cert: Path of SSL cert used in HTTPS request.
      ssl_key: Path of SSL key used in HTTPS request.
      ssl_pp: Pahs phrase used in SSL key, if any.
    Returns:
      A dictionary represents the JSON response received from server.
    """

    response = StringIO.StringIO()
    conn = pycurl.Curl()
    conn.setopt(conn.URL, url)
    conn.setopt(conn.WRITEFUNCTION, response.write)
    header = [
        'Host: %s' % urlparse.urlparse(url).hostname,
        'Content-Type: application/json'
    ]
    conn.setopt(conn.VERBOSE, 3)
    conn.setopt(conn.SSLVERSION, conn.SSLVERSION_TLSv1_2)
    conn.setopt(conn.SSLCERTTYPE, 'PEM')
    conn.setopt(conn.SSLCERT, 'ssl/' + ssl_cert)
    conn.setopt(conn.SSLKEY, 'ssl/' + ssl_key)
    if len(ssl_pp) > 0:
        conn.setopt(conn.SSLKEYPASSWD, 'ssl/' + ssl_pp)
    #conn.setopt(conn.CAINFO, 'ssl/' + ssl_ca)
    conn.setopt(conn.HTTPHEADER, header)
    conn.setopt(conn.SSL_CIPHER_LIST, CIPHERS)
    conn.setopt(conn.POST, True)
    request = json.dumps(request) if request else ''
    if len(request) > 0:
        logger.info('Request {}\n{}'.format(url, request))
    else:
        logger.info('Request {}'.format(url))
    conn.setopt(conn.POSTFIELDS, request)
    conn.setopt(conn.TIMEOUT, HTTP_TIMEOUT_SECS)
    conn.setopt(conn.SSL_VERIFYPEER, 0)   
    conn.setopt(conn.SSL_VERIFYHOST, 0)
    conn.perform()
    assert conn.getinfo(pycurl.HTTP_CODE) == 200
    conn.close()
    body = response.getvalue()
    if body != '""':
        logger.info('Response\n{}'.format(body))
    else:
        logger.info('Response <empty>')
    return json.loads(body)


class CbsdSasImpl(cbsd_sas_interface.CbsdSasInterface):
    """Implementation of SasInterface for SAS certification testing."""

    def __init__(self, logger, host):
        self._base_url = host['BaseUrl']
        self._sas_version = host['Version']
        self._ssl_ca = host['CA']
        self._ssl_cert = host['CbsdCert']
        self._ssl_key = host['CbsdKey']
        self._ssl_pp = host['CbsdPassphrase']

        self._logger = logger
        self._logger.debug('*** SasInterfaceImpl ***')
        self._logger.debug(self._ssl_ca)
        self._logger.debug(self._ssl_cert)
        self._logger.debug(self._ssl_key)
        if(len(self._ssl_pp) > 0):
            self._logger.debug(self._ssl_pp)

    def Registration(self, request):
        if(not isinstance(request, list)):
            request = [request]

        return self._CbsdRequest(
            'registration',
            {'registrationRequest': request})['registrationResponse']

    def SpectrumInquiry(self, request):
        if(not isinstance(request, list)):
            request = [request]

        return self._CbsdRequest(
            'spectrumInquiry',
            {'spectrumInquiryRequest': request})['spectrumInquiryResponse']

    def Grant(self, request):
        if(not isinstance(request, list)):
            request = [request]

        return self._CbsdRequest(
            'grant',
            {'grantRequest': request})['grantResponse']

    def Heartbeat(self, request):
        if(not isinstance(request, list)):
            request = [request]

        return self._CbsdRequest(
            'heartbeat',
            {'heartbeatRequest': request})['heartbeatResponse']

    def Relinquishment(self, request):
        if(not isinstance(request, list)):
            request = [request]

        return self._CbsdRequest(
            'relinquishment',
            {'relinquishmentRequest': request})['relinquishmentResponse']

    def Deregistration(self, request):
        if(not isinstance(request, list)):
            request = [request]

        return self._CbsdRequest(
            'deregistration',
            {'deregistrationRequest': request})['deregistrationResponse']

    def SetVersionNumber(self, version):
        self._sas_version = version

    def _CbsdRequest(self, method_name, request):
        return _Request(
            self._logger,
            'https://%s/cbsd/%s/%s' %
            (self._base_url, self._sas_version, method_name),
            request,
            self._ssl_ca, self._ssl_cert, self._ssl_key, self._ssl_pp)


class AdminSasImpl(admin_sas_interface.AdminSasInterface):
    """Implementation of SasAdminInterface for SAS certification testing."""

    def __init__(self, logger, host):
        self._base_url = host['BaseUrl']
        self._ssl_ca = host['CA']
        self._ssl_cert = host['AdminCert']
        self._ssl_key = host['AdminKey']
        self._ssl_pp = host['AdminPassphrase']

        self._logger = logger
        self._logger.debug('*** SasAdminImpl ***')
        self._logger.debug(self._ssl_ca)
        self._logger.debug(self._ssl_cert)
        self._logger.debug(self._ssl_key)
        if(len(self._ssl_pp) > 0):
            self._logger.debug(self._ssl_pp)

    def Reset(self):
        _Request(
            self._logger,
            'https://%s/admin/reset' % self._base_url,
            None,
            self._ssl_ca, self._ssl_cert, self._ssl_key, self._ssl_pp)
