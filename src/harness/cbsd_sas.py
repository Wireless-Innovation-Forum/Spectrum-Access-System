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
""" Implementation of SasInterface """

import ConfigParser
import json
import StringIO
import urlparse
import logging

import pycurl
import cbsd_sas_interface

LOG_FILE = 'log/cbsd-sas.log'
LOG_FORMAT = logging.Formatter(
    '%(asctime)-15s - SasInterface - '
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
    config_parser.read(['tests/cbsd_sas.cfg'])
    host = {k: v for (k, v) in config_parser.items('SasConfig')}
    return SasImpl(logger, handler, host), SasAdminImpl(logger, handler, host)


def _Request(logger, url, request, ssl_ca, ssl_cert, ssl_key, ssl_pp):
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
        'Content-Type: application/json'
    ]
    conn.setopt(conn.VERBOSE, 3)
    conn.setopt(conn.SSLVERSION, conn.SSLVERSION_TLSv1_2)
    conn.setopt(conn.SSLCERTTYPE, 'PEM')
    conn.setopt(conn.SSLCERT, 'ssl/' + ssl_cert)
    conn.setopt(conn.SSLKEY, 'ssl/' + ssl_key)
    if(len(ssl_pp) > 0):
        conn.setopt(conn.SSLKEYPASSWD, 'ssl/' + ssl_pp)
    conn.setopt(conn.CAINFO, 'ssl/' + ssl_ca)
    conn.setopt(conn.HTTPHEADER, header)
    conn.setopt(conn.SSL_CIPHER_LIST, CIPHERS)
    conn.setopt(conn.POST, True)
    request = json.dumps(request) if request else ''
    if(len(request) > 0):
        logger.info('Request to URL {}\n{}'.format(url, request))
    else:
        logger.info('Request to URL {}'.format(url))
    conn.setopt(conn.POSTFIELDS, request)
    conn.setopt(conn.TIMEOUT, HTTP_TIMEOUT_SECS)
    conn.perform()
    assert conn.getinfo(pycurl.HTTP_CODE) == 200
    conn.close()
    body = response.getvalue()
    if(body != '""'):
        logger.info('Response\n{}'.format(body))
    else:
        logger.info('Response <empty>')
    return json.loads(body)


class SasImpl(cbsd_sas_interface.SasInterface):
    """Implementation of SasInterface for SAS certification testing."""

    def __init__(self, logger, handler, host):
        self._base_url = host['BaseUrl']
        self._sas_version = host['Version']
        self._ssl_ca = host['CA']
        self._ssl_cert = host['cbsdCert']
        self._ssl_key = host['cbsdKey']
        self._ssl_pp = host['cbsdPP']

        self.logger = logger
        self.handler = handler

        self.logger.debug('*** SasInterfaceImpl ***')
        self.logger.debug(self._ssl_ca)
        self.logger.debug(self._ssl_cert)
        self.logger.debug(self._ssl_key)
        if(len(self._ssl_pp) > 0):
            self.logger.debug(self._ssl_pp)

    def Registration(self, request):
        return self._CbsdRequest(
            'registration',
            {'registrationRequest': [request]})['registrationResponse']

    def SpectrumInquiry(self, request):
        return self._CbsdRequest(
            'spectrumInquiry',
            {'spectrumInquiryRequest': [request]})['spectrumInquiryResponse']

    def Grant(self, request):
        return self._CbsdRequest(
            'grant',
            {'grantRequest': [request]})['grantResponse']

    def Heartbeat(self, request):
        return self._CbsdRequest(
            'heartbeat',
            {'heartbeatRequest': [request]})['heartbeatResponse']

    def Relinquishment(self, request):
        return self._CbsdRequest(
            'relinquishment',
            {'relinquishmentRequest': [request]})['relinquishmentResponse']

    def Deregistration(self, request):
        return self._CbsdRequest(
            'deregistration',
            {'deregistrationRequest': [request]})['deregistrationResponse']

    def _CbsdRequest(self, method_name, request):
        return _Request(
            self.logger,
            'https://%s/cbsd/%s/%s' %
            (self._base_url, self._sas_version, method_name),
            request,
            self._ssl_ca, self._ssl_cert, self._ssl_key, self._ssl_pp)


class SasAdminImpl(cbsd_sas_interface.SasAdminInterface):
    """Implementation of SasAdminInterface for SAS certification testing."""

    def __init__(self, logger, handler, host):
        self._base_url = host['BaseUrl']
        self._ssl_ca = host['CA']
        self._ssl_cert = host['adminCert']
        self._ssl_key = host['adminKey']
        self._ssl_pp = host['adminPP']

        self.logger = logger
        self.handler = handler

        self.logger.debug('*** SasAdminImpl ***')
        self.logger.debug(self._ssl_ca)
        self.logger.debug(self._ssl_cert)
        self.logger.debug(self._ssl_key)
        if(len(self._ssl_pp) > 0):
            self.logger.debug(self._ssl_pp)

    def Reset(self):
        _Request(
            self.logger,
            'https://%s/admin/reset' % self._base_url,
            None,
            self._ssl_ca, self._ssl_cert, self._ssl_key, self._ssl_pp)
