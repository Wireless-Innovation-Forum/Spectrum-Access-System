#!/usr/bin/env python
# -- encoding: utf-8 --

__author__ = "Francisco Benavides (francisco.benavides@federatedwireless.com)"
"""
    SAS Connector
    Federated Wireless

    SAS to User Protocol Technical Specification
    WINNF-16-S-0016 SAS to CBSD v0.3.10, 12 July 2016

    9.2     Message Transport
            HTTP v1.1, Content-type: application/json

    SAS - SAS Interface Technical Specification
    WINNF-16-S-0096 v0.3.5, 20 September 2016

    7.2     Message Transport
            HTTP 1.1, Content-type: application/json
"""


# Imports

import os
import logging


# Constants

# Log format
LOG_FORMAT = logging.Formatter(
    '%(asctime)-15s - SAS Connector - '
    '%(funcName)s - %(levelname)s - %(message)s')


# Classes


class SAS_Connector(object):
    """ Class SAS Connector
        Container for SAS Host URL, Port, and Version
    """

    def __init__(self, logger, handler):

        self.http = None
        self.https = None
        self.versionNumber = None

        self.logger = logger
        self.handler = handler

        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('*** SAS_Connector ****')

    def SetHttp(self, url):
        self.http = url

    def GetHttp(self):
        return(self.http + '/' + self.versionNumber if self.http else '')

    def SetHttps(self, url):
        self.https = url

    def GetHttps(self):
        return(self.https + '/' + self.versionNumber if self.https else '')

    def SetVersionNumber(self, versionNumber):
        self.versionNumber = versionNumber

    def GetVersionNumber(self):
        return(self.versionNumber)

