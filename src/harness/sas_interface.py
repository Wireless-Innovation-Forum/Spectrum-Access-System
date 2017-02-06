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
import abc
# PycURL
import StringIO
import urllib
import urlparse
import pycurl
# Import OWN
from sas_connector import SasConnector


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
    'CBSD': None,
    'ADMIN': None,
    'CBSD_CA_CERT': None,
    'CBSD_CERT': None,
    'CBSD_KEY': None,
    'CBSD_KEYPASSWD': None,
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
            if(cfg.read([self.cfgFile]) == []):
                raise IOError('Configuration file could not be open')

        except IOError as e:
            self.logger.error('{}'.format(e))
            sys.exit(1)
        except ConfigParser.ParsingError as e:
            self.logger.error(
                'Configuration file parsing error: {}'.format(e))
            sys.exit(1)
        except ConfigParser.MissingSectionHeaderError as e:
            self.logger.error(
                'Configuration file missing section headers: {}'.format(e))
            sys.exit(1)
        except AttributeError as e:
            self.logger.error(
                'Configuration file faulty indentation of multiline values: {}'
                .format(e))
            sys.exit(1)

        # Configuration file should not be empty
        if(cfg.sections() == []):
            self.logger.error('Configuration file seems empty')
            sys.exit(1)

        # Check for required sections and corresponding required options
        missing = False

        # Check for required section
        if(INI_FILE_SECTION not in cfg.sections()):
            missing = True
            self.logger.error(
                '[{}] Missing Required section'.format(INI_FILE_SECTION))
            sys.exit(1)

        # Check for required option present
        requiredCounter = 0
        for option in cfg.options(INI_FILE_SECTION):
            if(option in self.ini.keys()):
                requiredCounter += 1
        if(requiredCounter != len(self.ini.keys())):
            missing = True
            for option in self.ini:
                if(option not in cfg.options(INI_FILE_SECTION)):
                    self.logger.error(
                        '[{}] Missing Required option'.format(option))
        # Check for required option value present
        for option in cfg.options(INI_FILE_SECTION):
            if(not cfg.get(INI_FILE_SECTION, option)):
                missing = True
                self.logger.error(
                    '[{}: EMPTY] Missing option value '.format(option))

        # any thing missing on the configuration file, exit
        if(missing):
            sys.exit(1)

        # Load configuration file values
        for option in cfg.options(INI_FILE_SECTION):
            self.ini[option] = cfg.get(INI_FILE_SECTION, option)

        # Load 'SAS' URL configuration file data
        self.SetVersionNumber(self.ini['VERSION'])
        self.SetCbsd(self.ini['CBSD'])
        self.SetAdmin(self.ini['ADMIN'])

        self.cbsd_caCert = os.path.join(
            os.getcwd(), 'ssl', self.ini['CBSD_CA_CERT'])
        self.cbsd_cert = os.path.join(
            os.getcwd(), 'ssl', self.ini['CBSD_CERT'])
        self.cbsd_key = os.path.join(
            os.getcwd(), 'ssl', self.ini['CBSD_KEY'])
        self.cbsd_keypasswd = self.ini['CBSD_KEYPASSWD']

        self.logger.debug('CBSD: {}'.format(self.GetCbsd()))
        self.logger.debug('CBSD CA Cert:  {}'.format(self.cbsd_caCert))
        self.logger.debug('CBSD Cert:     {}'.format(self.cbsd_cert))
        self.logger.debug('CBSD Key:      {}'.format(self.cbsd_key))
        self.logger.debug('CBSD Key Pwd:  {}'.format(self.cbsd_keypasswd))

        self.admin_caCert = os.path.join(
            os.getcwd(), 'ssl', self.ini['ADMIN_CA_CERT'])
        self.admin_cert = os.path.join(
            os.getcwd(), 'ssl', self.ini['ADMIN_CERT'])
        self.admin_key = os.path.join(
            os.getcwd(), 'ssl', self.ini['ADMIN_KEY'])
        self.admin_keypasswd = self.ini['ADMIN_KEYPASSWD']

        self.logger.debug('Admin: {}'.format(self.GetAdmin()))
        self.logger.debug('Admin CA Cert: {}'.format(self.admin_caCert))
        self.logger.debug('Admin Cert:    {}'.format(self.admin_cert))
        self.logger.debug('Admin Key:     {}'.format(self.admin_key))
        self.logger.debug('Admin Key Pwd: {}'.format(self.admin_keypasswd))

    def Request(self,
        pull, url, request, ssl_caCert, ssl_cert, ssl_key, ssl_keyPassword=None):
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
        conn.setopt(conn.SSLVERSION, conn.SSLVERSION_TLSv1_2)
        conn.setopt(conn.SSLCERTTYPE, 'PEM')
        conn.setopt(conn.SSLCERT, ssl_cert)
        conn.setopt(conn.SSLKEY, ssl_key)
        if(ssl_keyPassword):
            conn.setopt(conn.SSLKEYPASSWD, ssl_keyPassword)
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
        self.handler.setFormatter(LOG_FORMAT)

        if(resource['name'] != 'RESET'):

            # URL set-up
            url = 'https://' + self.GetCbsd() + resource['path']

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
                    pull, url, data,
                    self.cbsd_caCert,
                    self.cbsd_cert,
                    self.cbsd_key,
                    self.cbsd_keypasswd)

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

        else:

            # URL set-up
            url = 'https://' + self.GetAdmin() + resource['path']

            self.logger.info(
                'Send {} RESET to SAS - {} {} :: {}'
                .format(
                    resource['name'],
                    'PULL' if pull else 'PUSH',
                    url,
                    data if len(data) > 0 else 'EMPTY'))

            try:
                results = self.Request(
                    pull, url, data,
                    self.admin_caCert,
                    self.admin_cert,
                    self.admin_key,
                    self.admin_keypasswd)

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

        self.logger.info(
            "Received {} RESponse from SAS - {}"
            .format(
                resource['name'],
                json.dumps(response) if response is not None else 'EMPTY'))

        return(response)
