#!/usr/bin/env python
# -- encoding: utf-8 --

# Project: CBSD to SAS interface
__author__ = """
    Kaushik Bekkem (kaushik.bekkem@federatedwireless.com),
    Francisco Benavides (francisco.benavides@federatedwireless.com) """
"""
    CBSD to SAS Interface
    Federated Wireless

    SAS to User Protocol Technical Specification
    WINNF-16-S-0016 SAS to CBSD v0.3.10, 12 July 2016

    9.2     Message Transport
            HTTP v1.1, Content-type: application/json
            JSON objects shall use UTF-8 enconding
            All requests from CBSD to SAS shall use the HTTP POST method
"""

# Imports
import logging
import sys
import os
from datetime import datetime
from pytz import timezone
# Import OWN
from sas_interface import SasInterface
from sas_interface import PUSH

# Logging file path
LOG_FILE = 'log/cbsd-to-sas-harness.log'
# Log format
LOG_FORMAT = logging.Formatter(
    '%(asctime)-15s - SasInterfaceImpl - '
    '%(funcName)s - %(levelname)s - %(message)s')
# CBSD to SAS Resources
RESOURCES = {
    'reg': {
        'name': 'REGISTRATION',
        'path': '/registration',
        'req': 'registrationRequest',
        'res': 'registrationResponse',
        'ini': 'REGISTRATION'},
    'dereg': {
        'name': 'DEREGISTRATION',
        'path': '/deregistration',
        'req': 'deregistrationRequest',
        'res': 'deregistrationResponse',
        'ini': 'DEREGISTRATION'},
    'spec': {
        'name': 'SPECTRUM INQUIRY',
        'path': '/spectrumInquiry',
        'req': 'spectrumInquiryRequest',
        'res': 'spectrumInquiryResponse',
        'ini': 'SPECTRUM'},
    'grant': {
        'name': 'GRANT',
        'path': '/grant',
        'req': 'grantRequest',
        'res': 'grantResponse',
        'ini': 'GRANT'},
    'hb': {
        'name': 'HEARTBEAT',
        'path': '/heartbeat',
        'req': 'heartbeatRequest',
        'res': 'heartbeatResponse',
        'ini': 'HEARTBEAT'},
    'rel': {
        'name': 'RELINQUISHMENT',
        'path': '/relinquishment',
        'req': 'relinquishmentRequest',
        'res': 'relinquishmentResponse',
        'ini': 'RELINQUISHMENT'},
    'reset': {
        'name': 'RESET',
        'path': '/reset',
        'req': 'resetRequest',
        'res': 'resetResponse'}}


# Classes

class SasInterfaceImpl(SasInterface):
    """ Class CBSD to SAS Gateway
        Send/Receive messages to/from given URL
    """

    def __init__(self):

        # Logging Instance creation
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        # Handle set-up
        handler = logging.FileHandler(LOG_FILE)
        handler.setLevel(logging.DEBUG)
        # Couple handler to logging instance
        logger.addHandler(handler)

        super(SasInterfaceImpl, self).__init__(logger, handler)

        self.logger = logger
        self.handler = handler

        # Prep SAS to SAS Configuration file set-up section/options
        self.LoadSettings()

        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('*** SasInterfaceImpl ****')

    def GetIniData(self, option, section):
        """ Return the configuration file defined option value """
        self.handler.setFormatter(LOG_FORMAT)

        try:
            return(self.ini[section][option])

        except Exception as e:
            self.logger.error(
                '[{}] {} Bad data retrieval'.format(section, option))
            sys.exit(1)

    def GetLocalTime(self):
        """ Return the local machine time in UTC time zone """

        try:
            utc = timezone('UTC')
            return(utc.localize(datetime.utcnow()))

        except Exception as e:
            self.logger.error('Time Zone error: {}'.format(e))
            sys.exit(1)

    # Message Requests

    def RegistrationRequest(self, reg_obj):
        """ Send Registration Request to SAS """

        # Build the message
        req_array = {}
        if(not isinstance(reg_obj, list)):
            reg_obj = [reg_obj]
        req_array[RESOURCES['reg']['req']] = reg_obj

        # Send request, get response
        results = self.SendMessage(PUSH, RESOURCES['reg'], req_array)
        return(results[RESOURCES['reg']['res']])

    def DeregistrationRequest(self, reg_obj):
        """ Send Deregistration Request to SAS """

        # Initialize request array object
        req_array = {}
        if(not isinstance(reg_obj, list)):
            reg_obj = [reg_obj]
        req_array[RESOURCES['dereg']['req']] = [
            {'cbsdId': r['cbsdId']} if 'cbsdId' in r else {} for r in reg_obj]

        # Send request, get response
        results = self.SendMessage(PUSH, RESOURCES['dereg'], req_array)
        return(results[RESOURCES['dereg']['res']])

    def SpectrumInquiryRequest(self, reg_obj, spec_obj):
        """ Send Spectrum Inquiry Request to SAS """

        # Build the message
        req_array = {}
        if(not isinstance(spec_obj, list)):
            spec_obj = [spec_obj]
        if(not isinstance(reg_obj, list)):
            reg_obj = [reg_obj]
        req_array[RESOURCES['spec']['req']] = []

        for (r, s) in zip(reg_obj, spec_obj):
            tmp = {'cbsdId': r['cbsdId']} if 'cbsdId' in r else {}
            tmp.update(s)
            req_array[RESOURCES['spec']['req']].append(tmp)

        # Send request, get response
        results = self.SendMessage(PUSH, RESOURCES['spec'], req_array)
        return(results[RESOURCES['spec']['res']])

    def GrantRequest(self, reg_obj, grant_obj):
        """ Send Grant Request to SAS """

        # Build the message
        req_array = {}
        if(not isinstance(grant_obj, list)):
            grant_obj = [grant_obj]
        if(not isinstance(reg_obj, list)):
            reg_obj = [reg_obj]
        req_array[RESOURCES['grant']['req']] = []

        for (r, g) in zip(reg_obj, grant_obj):
            tmp = {'cbsdId': r['cbsdId']} if 'cbsdId' in r else {}
            tmp.update(g)
            req_array[RESOURCES['grant']['req']].append(tmp)

        # Send request, get response
        results = self.SendMessage(PUSH, RESOURCES['grant'], req_array)
        return(results[RESOURCES['grant']['res']])

    def GrantRequestOneToMore(self, reg_obj, grant_obj):
        """ Send Grant Request to SAS """

        # Build the message
        req_array = {}
        if(not isinstance(reg_obj, list)):
            reg_obj = [reg_obj]
        if(not isinstance(grant_obj, list)):
            grant_obj = [grant_obj]
        req_array[RESOURCES['grant']['req']] = []

        for r in reg_obj:
            tmp = None
            for g in grant_obj:
                tmp = {'cbsdId': r['cbsdId']} if 'cbsdId' in r else {}
                tmp.update(g)
                req_array[RESOURCES['grant']['req']].append(tmp)

        # Send request, get response
        results = self.SendMessage(PUSH, RESOURCES['grant'], req_array)
        return(results[RESOURCES['grant']['res']])

    def RelinquishmentRequest(self, grant_obj, rel_obj):
        """ Send Relinquishment Request to SAS """

        # Build the message
        req_array = {}
        if(not isinstance(grant_obj, list)):
            grant_obj = [grant_obj]
        if(not isinstance(rel_obj, list)):
            rel_obj = [rel_obj]
        req_array[RESOURCES['rel']['req']] = []

        for (g, r) in zip(grant_obj, rel_obj):
            tmp = {'cbsdId': g['cbsdId']} if 'cbsdId' in g else {}
            tmp.update({'grantId': g['grantId']} if 'grantId' in g else {})
            tmp.update(r)
            req_array[RESOURCES['rel']['req']].append(tmp)

        # Send request, get response
        results = self.SendMessage(PUSH, RESOURCES['rel'], req_array)
        return(results[RESOURCES['rel']['res']])

    def HeartbeatRequest(self, grant_obj, hb_obj):
        """ Send Hearbeat Request to SAS """

        # Build the message
        req_array = {}
        if(not isinstance(grant_obj, list)):
            grant_obj = [grant_obj]
        if(not isinstance(hb_obj, list)):
            hb_obj = [hb_obj]
        req_array[RESOURCES['hb']['req']] = []

        for (g, h) in zip(grant_obj, hb_obj):
            tmp = {'cbsdId': g['cbsdId']} if 'cbsdId' in g else {}
            tmp.update({'grantId': g['grantId']} if 'grantId' in g else {})
            tmp.update(h)
            req_array[RESOURCES['hb']['req']].append(tmp)

        # Send request, get response
        results = self.SendMessage(PUSH, RESOURCES['hb'], req_array)
        return(results[RESOURCES['hb']['res']])

    # Admin Request

    def Reset(self):
        results = self.SendMessage(PUSH, RESOURCES['reset'], None)
        return(results[RESOURCES['reset']['res']])
