#!/usr/bin/env python
# -- encoding: utf-8 --

__author__ = "Francisco Benavides (francisco.benavides@federatedwireless.com)"
"""
    SAS Interface
    Federated Wireless

    SAS to User Protocol Technical Specification
    WINNF-16-S-0016 SAS to CBSD v0.3.10, 12 July 2016

    9.2     Message Transport
            HTTP v1.1, Content-type: application/json
            JSON objects shall use UTF-8 enconding
            All requests from CBSD to SAS shall use the HTTP POST method

    SAS - SAS Interface Technical Specification
    WINNF-16-S-0096 v0.3.5, 20 September 2016

    6.1     SAS Mutual Authentication and Communication Security
            TLS v1.2 authentication
    7.1     Message encoding
            JSON objects UTF-8 encoding
    7.2     Message Transport
            HTTP 1.1, Content-type: application/json
            GET (Pull) and POST (Push) methods
"""


# Imports
import json
import os
import sys
import ConfigParser
import logging
# PycURL
import StringIO
import urlparse
import pycurl
# Import OWN
from sas_connector import SasConnector


# Constants

# Log format
LOG_FORMAT = logging.Formatter(
    '%(asctime)-15s - SasInterface - '
    '%(funcName)s - %(levelname)s - %(message)s')
# SAS Interface Settings
INI_FILE = 'tests/sas_settings.ini'
INI_FILE_SECTION = 'HOST'
INI_FILE_OPTIONS = {
    'VERSION': None,
    'URL': None,
    'CBSD_CA_CERT': None,
    'CBSD_CERT': None,
    'CBSD_KEY': None,
    'CBSD_KEYPASSWD': None,
    'ADMIN_URL': None,
    'ADMIN_CA_CERT': None,
    'ADMIN_CERT': None,
    'ADMIN_KEY': None,
    'ADMIN_KEYPASSWD': None}
PULL = True
PUSH = not(PULL)
HTTP_TIMEOUT_SECS = 300
# TLS 1.2 Ciphers
SSL_CIPHER_LIST = ':'.join([
    'RSA-AES128-GCM-SHA256',
    'RSA-AES256-GCM-SHA384',
    'ECDHE-ECDSA-AES128-GCM-SHA256',
    'ECDHE-ECDSA-AES256-GCM-SHA384',
    'ECDHE-RSA-AES128-GCM-SHA256'])


# Classes


class CConfigParser(ConfigParser.ConfigParser):
    """ Load initialization file
        Preserv key case format from config file
    """

    def __init__(self):
        """ Initialize configuration file parser """
        ConfigParser.ConfigParser.__init__(self)
        self.optionxform = str


class SasInterface(SasConnector):
    """ Class SAS Interface
        Send/Receive messages to/from given URL
    """

    def __init__(self, logger, handler):

        super(SasInterface, self).__init__(logger, handler)

        self.logger = logger
        self.handler = handler

        self.debug_entries = []

        self.cfgFile = os.path.join(os.getcwd(), INI_FILE)
        self.ini = INI_FILE_OPTIONS

        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('*** SasInterface ****')

    def LoadSettings(self):
        """ Load configuration settings URL+PORT for
            SAS to SAS communication
        """
        self.handler.setFormatter(LOG_FORMAT)

        cfg = CConfigParser()

        # Read Configuration file
        try:
            cfg.read([self.cfgFile])

        except Exception as e:
            self.logger.error('{}'.format(e))
            sys.exit(1)

        # Configuration file should not be empty
        if(cfg.sections() == []):
            self.logger.error('Configuration file seems empty')
            sys.exit(1)

        # Load configuration file values
        for option in cfg.options(INI_FILE_SECTION):
            self.ini[option] = cfg.get(INI_FILE_SECTION, option)
            self.logger.debug('{}: {}'.format(option, self.ini[option]))

        # Load 'SAS' URL configuration file data
        self.SetVersionNumber(self.ini['VERSION'])
        self.SetUrl(self.ini['URL'])

        self.cbsd_caCert = os.path.join(
            os.getcwd(), 'ssl', self.ini['CBSD_CA_CERT'])
        self.cbsd_cert = os.path.join(
            os.getcwd(), 'ssl', self.ini['CBSD_CERT'])
        self.cbsd_key = os.path.join(
            os.getcwd(), 'ssl', self.ini['CBSD_KEY'])
        self.cbsd_keypassword = self.ini['CBSD_KEYPASSWD']

        self.admin_caCert = os.path.join(
            os.getcwd(), 'ssl', self.ini['ADMIN_CA_CERT'])
        self.admin_cert = os.path.join(
            os.getcwd(), 'ssl', self.ini['ADMIN_CERT'])
        self.admin_key = os.path.join(
            os.getcwd(), 'ssl', self.ini['ADMIN_KEY'])
        self.admin_keypassword = self.ini['ADMIN_KEYPASSWD']

    def Request(
        self, pull, url, request, ssl_caCert, ssl_cert, ssl_key,
            ssl_keyPassword=None):
        """ Sends HTTP/S request
            Args:
                pull: Define True as pull (GET) or False as push (POST)
                url: Destination of the HTTP/S request
                request: Content of the request
                ssl_caCert: Path to SSL CA cert used in HTTPS request
                ssl_cert: Path of SSL cert used in HTTPS request
                ssl_key: Path of SSL key used in HTTPS request
            Returns:
                A dictionary represents the JSON response received from server
        """
        self.handler.setFormatter(LOG_FORMAT)

        response = StringIO.StringIO()
        header = [
            'Host: {}'.format(
                urlparse.urlparse(url).hostname),
            'Content-type: application/json'
        ]

        conn = pycurl.Curl()

        # Setup the URL to send the REQuest
        conn.setopt(conn.URL, url.encode('utf8'))
        conn.setopt(conn.WRITEFUNCTION, response.write)
        conn.setopt(conn.HTTPHEADER, header)

        # Diagnostics settings
        conn.setopt(conn.VERBOSE, 1)

        # Setup TLS 1.2
        conn.setopt(conn.SSLVERSION, conn.SSLVERSION_TLSv1_2)
        conn.setopt(conn.SSLCERTTYPE, 'PEM')
        conn.setopt(conn.SSLCERT, ssl_cert)
        conn.setopt(conn.SSLKEY, ssl_key)
        if(ssl_keyPassword):
            conn.setopt(conn.SSLKEYPASSWD, ssl_keyPassword)
        conn.setopt(conn.CAINFO, ssl_caCert)
        conn.setopt(conn.SSL_CIPHER_LIST, SSL_CIPHER_LIST)

        # Default request is GET
        if(not pull):
            # Otherwise, define request as POST
            conn.setopt(conn.POST, True)
            try:
                request = json.dumps(request) if request else ''
            except (TypeError, ValueError) as e:
                self.logger.error(
                    'JSON Error: Unable to serialize object {}'
                    .format(e), exc_info=True)
                sys.exit(1)
            conn.setopt(conn.POSTFIELDS, request)

        # Send request
        conn.setopt(conn.CONNECTTIMEOUT, HTTP_TIMEOUT_SECS / 10)
        conn.setopt(conn.TIMEOUT, HTTP_TIMEOUT_SECS)
        try:
            conn.perform()
        except pycurl.error as e:
            self.logger.error('Connection Error: {}'.format(e))
            sys.exit(1)
        finally:
            conn.close()

        # Results object
        class results(object):
            def __init__(self, text, status_code):
                self.text = text
                self.status_code = status_code

        return(results(response.getvalue(), conn.getinfo(conn.HTTP_CODE)))

    def SendMessage(
        self, pull, resource, data,
            id=None, startTime=None, endTime=None):
        """ Send REQuest to a given SAS URL and receive back
            the correspoding RESponse
        """
        self.handler.setFormatter(LOG_FORMAT)

        # URL set-up
        if(resource['name'] == 'RESET'):
            url = self.GetAdminUrl() + resource['path']
            caCert = self.admin_caCert
            cert = self.admin_cert
            key = self.admin_key
            keyPassword = self.admin_keypassword

        else:
            url = self.GetCbsdUrl() + resource['path']
            caCert = self.cbsd_caCert
            cert = self.cbsd_cert
            key = self.cbsd_key
            keyPassword = self.cbsd_keypassword

        if(id and pull):
            url += '/' + id

        if(startTime or endTime):
            url += ':searchByTime?'
            if(startTime):
                url += 'start_date=' + startTime
                if(endTime):
                    url += '&end_date=' + endTime
            if(endTime):
                url += 'end_date=' + endTime

        self.logger.info(
            'Send {} REQuest to SAS - {} {} :: {}'
            .format(
                resource['name'],
                'PULL' if pull else 'PUSH',
                url,
                data if len(data) > 0 else 'EMPTY'))

        try:
            results = self.Request(
                pull, url, data, caCert, cert, key, keyPassword)
            if(results.status_code != 200):
                self.logger.error(
                    'FAILURE HTTP Status code {} returned'
                    .format(results.status_code))
                raise
            self.logger.debug(
                'SUCCESS HTTP Status Code {} returned'
                .format(results.status_code))

        except Exception as e:
            self.logger.error('Connection Error: {}'.format(e))
            sys.exit(1)

        if(resource['name'] == 'RESET'):
            return(results.text)

        else:
            if(len(results.text) > 0):
                try:
                    response = json.loads(results.text)
                except (TypeError, ValueError) as e:
                    self.logger.error(
                        'Unable to deserialize object: {} :: {}'
                        .format(results.text, e), exc_info=True)
                    sys.exit(1)

            self.logger.info(
                "Received {} RESponse from SAS - {}"
                .format(
                    resource['name'],
                    json.dumps(response) if response is not None else 'EMPTY'))

            return(response)
