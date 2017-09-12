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
import re
# PycURL
import StringIO
import urllib
import urlparse
import pycurl
# Import OWN
from sas_connector import SAS_Connector


# Constants

# Log format
LOG_FORMAT = logging.Formatter(
    '%(asctime)-15s - SAS Interface - '
    '%(funcName)s - %(levelname)s - %(message)s')
# SAS Interface Settings
INI_FILE = 'tests/sas_settings.ini'
INI_FILE_SECTION = 'HOST'
INI_FILE_OPTIONS = {
    'VERSION': None,
    'HTTP': None,
    'HTTPS': None,
    'CA_CERT': None,
    'CERT': None,
    'KEY': None,
    'KEYPASSWD': None}
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
        Preserv key case format
    """

    def __init__(self):
        """ Initialize configuration file parser """
        ConfigParser.ConfigParser.__init__(self, allow_no_value=True)
        self.optionxform = str

    def Interpolation(self):
        """ Interpolation - replace option values defined with OWN options """
        pattern = re.compile('(\$\{.+\})', re.M)
        defaultOptions = ConfigParser.ConfigParser.defaults(self)

        # Load configuration file
        data = {}
        for section in ConfigParser.ConfigParser.sections(self):
            data[section] = {key: value for (key, value) in ConfigParser.ConfigParser.items(self, section) if key not in defaultOptions.keys()}

        # Interpolate data within same SECTION, if any
        for section in data:
            for key in data[section].keys():
                if(key not in defaultOptions.keys()):
                    match = pattern.findall(data[section][key])
                    for m in match:
                        if(m[2:-1] in data[section].keys()):
                            data[section][key] = data[section][key].replace(
                                m, data[section][m[2:-1]])

        # Interpolate data with DEFAULT section, if any
        for section in data:
            for key in data[section].keys():
                if(key not in defaultOptions.keys()):
                    match = pattern.findall(data[section][key])
                    for m in match:
                        if(m[2:-1] in defaultOptions.keys()):
                            data[section][key] = data[section][key].replace(
                                m, defaultOptions[m[2:-1]])

        # Save changes, if any
        for section in data:
            for key in data[section].keys():
                ConfigParser.ConfigParser.set(
                    self, section, key, data[section][key])

    def read(self, filenames, raw=False):
        """ read - Read the configuration file and interpolate values,
            if any """
        ConfigParser.ConfigParser.read(self, filenames)
        if(not raw):
            self.Interpolation()


class SAS_Interface(SAS_Connector):
    """ Class SAS Interface
        Send/Receive messages to/from given URL
    """

    def __init__(self, tls, logger, handler):

        super(SAS_Interface, self).__init__(logger, handler)

        self.logger = logger
        self.handler = handler

        self.tls = tls
        self.debug_entries = []

        self.cfgFile = os.path.join(os.getcwd(), INI_FILE)
        self.ini = {INI_FILE_SECTION: INI_FILE_OPTIONS}

        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('*** SAS_Interface ****')

    def debug_function(self, t, b):
        self.debug_entries.append((t, b))

    def debug_show(self):
        self.logger.debug(repr(self.debug_entries))

    def LoadSettings(self):
        """ Load configuration settings URL+PORT for
            SAS to SAS communication
        """
        self.handler.setFormatter(LOG_FORMAT)

        cfg = CConfigParser()

        # Read Configuration file
        try:
            if(not os.path.isfile(self.cfgFile)):
                raise IOError('Configuration file could not be found')
            if(not os.access(self.cfgFile, os.R_OK)):
                raise IOError('Configuration file could not be read')
            if(cfg.read(self.cfgFile) == []):
                raise IOError('Configuration file could not be open')

        except IOError as e:
            self.logger.error('{}'.format(e), exc_info=True)
            sys.exit(1)
        except ConfigParser.ParsingError as e:
            self.logger.error(
                'Configuration file parsing error: {}'
                .format(e), exc_info=True)
            sys.exit(1)
        except ConfigParser.MissingSectionHeaderError as e:
            self.logger.error(
                'Configuration file missing section headers: {}'
                .format(e), exc_info=True)
            sys.exit(1)
        except AttributeError as e:
            self.logger.error(
                'Configuration file faulty indentation of multiline values: {}'
                .format(e), exc_info=True)
            sys.exit(1)

        # Configuration file should not be empty
        if(cfg.sections() == []):
            self.handler.setFormatter(LOG_FORMAT)
            self.logger.error('Configuration file seems empty')
            sys.exit(1)

        # Check for required sections and corresponding required options
        missing = False

        # Check for required sections
        requiredCounter = 0
        for section in cfg.sections():
            if(section in self.ini.keys()):
                requiredCounter += 1
        if(requiredCounter != len(self.ini.keys())):
            missing = True
            for section in self.ini:
                if(section not in cfg.sections()):
                    self.handler.setFormatter(LOG_FORMAT)
                    self.logger.error(
                        '[{}] Missing Required section'.format(section))

        # Check for required options, if any
        for section in cfg.sections():
            requiredCounter = 0
            if(section in self.ini.keys()):
                for option in cfg.options(section):
                    if(option in self.ini[section].keys()):
                        requiredCounter += 1
                if(requiredCounter != len(self.ini[section].keys())):
                    missing = True
                    for option in self.ini[section]:
                        if(option not in cfg.options(section)):
                            self.handler.setFormatter(LOG_FORMAT)
                            self.logger.error(
                                '[{}] [{}] Missing Required option'
                                .format(section, option))
                for option in cfg.options(section):
                    if(not cfg.get(section, option)):
                        missing = True
                        self.handler.setFormatter(LOG_FORMAT)
                        self.logger.error(
                            '[{}] [{}: EMPTY] Missing option value '
                            .format(section, option))

        if(missing):
            sys.exit(1)

        # Load configuration file values
        for section in cfg.sections():
            if(section not in self.ini.keys()):
                self.ini[section] = {}
            for option in cfg.options(section):
                self.ini[section][option] = cfg.get(section, option)
                try:
                    self.ini[section][option] = json.loads(
                        self.ini[section][option]
                        .replace('True', 'true')
                        .replace('False', 'false'))
                except Exception as e:
                    pass

        # Load 'SAS' URL configuration file data
        self.SetVersionNumber(self.ini[INI_FILE_SECTION]['VERSION'])
        self.SetHttp(self.ini[INI_FILE_SECTION]['HTTP'])
        self.SetHttps(self.ini[INI_FILE_SECTION]['HTTPS'])

        self.caCert = os.path.join(
            os.getcwd(), 'ssl', self.ini[INI_FILE_SECTION]['CA_CERT'])
        self.cert = os.path.join(
            os.getcwd(), 'ssl', self.ini[INI_FILE_SECTION]['CERT'])
        self.key = os.path.join(
            os.getcwd(), 'ssl', self.ini[INI_FILE_SECTION]['KEY'])
        self.keypasswd = self.ini[INI_FILE_SECTION]['KEYPASSWD']

        self.logger.debug('Http:     {}'.format(self.GetHttp()))
        self.logger.debug('Https:    {}'.format(self.GetHttps()))
        self.logger.debug('Config:   {}'.format(self.cfgFile))
        self.logger.debug('CA Cert:  {}'.format(self.caCert))
        self.logger.debug('Cert:     {}'.format(self.cert))
        self.logger.debug('Key:      {}'.format(self.key))
        self.logger.debug('Password: {}'.format(self.keypasswd))

    def Request(self, pull, tls, url, request, ssl_caCert, ssl_cert, ssl_key):
        """ Sends HTTP/S request
            Args:
                pull: Define True as pull (GET) or False as push (POST)
                tls: Define if request uses TLS or not
                url: Destination of the HTTP/S request
                request: Content of the request
                ssl_caCert: Path to SSL CA cert used in HTTPS request
                ssl_cert: Path of SSL cert used in HTTPS request
                ssl_key: Path of SSL key used in HTTPS request
            Returns:
                A dictionary represents the JSON response received from server
        """
        response = StringIO.StringIO()
        header = [
            'Host: {}'.format(
                urlparse.urlparse(url).hostname),
            'Content-type: application/json'
        ]
        self.logger.debug('Header: {}'.format(header))

        conn = pycurl.Curl()

        # Setup the URL to send the REQuest
        conn.setopt(conn.URL, url.encode('utf8'))
        conn.setopt(conn.WRITEFUNCTION, response.write)
        conn.setopt(conn.HTTPHEADER, header)

        # Diagnostics settings
        conn.setopt(conn.VERBOSE, 1)
        #conn.setopt(conn.DEBUGFUNCTION, self.debug_function)

        # Setup TLS 1.2
        if(tls):
            conn.setopt(conn.SSLVERSION, conn.SSLVERSION_TLSv1_2)
            conn.setopt(conn.SSLCERTTYPE, 'PEM')
            conn.setopt(conn.SSLCERT, ssl_cert)
            conn.setopt(conn.SSLKEY, ssl_key)
            if(self.keypasswd):
                conn.setopt(conn.SSLKEYPASSWD, self.keypasswd)
            conn.setopt(conn.CAINFO, ssl_caCert)
            conn.setopt(conn.SSL_CIPHER_LIST, SSL_CIPHER_LIST)
            # Unsecure settings
            #conn.setopt(conn.SSL_VERIFYPEER, 0)
            #conn.setopt(conn.SSL_VERIFYHOST, 0)

        # Default request is GET
        if(not pull):
            # Otherwise, define request as POST
            conn.setopt(conn.POST, True)
            self.logger.debug('POST')
            try:
                request = json.dumps(request) if request else ''
            except (TypeError, ValueError) as e:
                self.logger.error(
                    'JSON Error: Unable to serialize object {}'
                    .format(e), exc_info=True)
                sys.exit(1)
            conn.setopt(conn.POSTFIELDS, request)

        conn.setopt(conn.CONNECTTIMEOUT, HTTP_TIMEOUT_SECS / 10)
        conn.setopt(conn.TIMEOUT, HTTP_TIMEOUT_SECS)

        try:
            conn.perform()
        except pycurl.error as e:
            #self.debug_show()
            self.logger.error('Connection Error: {}'.format(e), exc_info=True)
            sys.exit(1)
        finally:
            conn.close()

        class results(object):
            def __init__(self, text, status_code):
                self.text = text
                self.status_code = status_code

        return(results(response.getvalue(), conn.getinfo(conn.HTTP_CODE)))

    def SendMessage(
        self, pull, resource, data, id=None, startTime=None, endTime=None):
        """ Send REQuest to a given SAS URL and receive back
            the correspoding RESponse
        """

        # URL set-up
        url = 'https://' + self.GetHttps() if self.tls else 'http://' + self.GetHttp()
        url += resource['path']

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

        self.handler.setFormatter(LOG_FORMAT)
        self.logger.info(
            'Send {} REQuest to SAS - {} {} :: {}'
            .format(
                resource['name'],
                'PULL' if pull else 'PUSH',
                url,
                data if len(data) > 0 else 'EMPTY'))

        try:
            results = self.Request(
                pull, self.tls, url, data, self.caCert, self.cert, self.key)

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

        response = None
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
