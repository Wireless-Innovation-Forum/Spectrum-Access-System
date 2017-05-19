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
from sas_interface import SAS_Interface
from sas_interface import PUSH

# Logging file path
LOG_FILE = 'log/cbsd-to-sas-harness.log'
# Log format
LOG_FORMAT = logging.Formatter(
    '%(asctime)-15s - CBSD to SAS Harness - '
    '%(funcName)s - %(levelname)s - %(message)s')
# CBSD to SAS configuration file sections and options
#INI_FILE_SECTION = 'CBSD-SAS'
#INI_FILE_OPTIONS = {
#    'CAT_A': None,
#    'CAT_B': None,
#    'SPECTRUM_GAA': None,
#    'SPECTRUM_PAL': None,
#    'GRANT': None,
#    'HEARTBEAT': None}
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
        'ini': 'RELINQUISHMENT'}}
# Response Code values
SUCCESS = 0
VERSION = 100
BLACKLISTED = 101
MISSING_PARAM = 102
INVALID_VALUE = 103
CERT_ERROR = 104
DEREGISTER = 105
REG_PENDING = 200
GROUP_ERROR = 201
CATEGORY_ERROR = 202
UNSUPPORTED_SPECTRUM = 300
INTERFERENCE = 400
GRANT_CONFLICT = 401
TOO_MANY_GRANTS = 402
TERMINATED_GRANT = 500
SUSPENDED_GRANT = 501
UNSYNC_OP_PARAM = 502
# Response Code resources
RESPONSE_CODE = {
    # Dictionay where the key is the responseCode value and the next key
    #   represents:
    #   - responseData: None=Not Present | []=String Array | ''=String
    #   - tag:          String short description
    #   - description:  String long  description
    SUCCESS: {
        'responseData': None,
        'tag': 'SUCCESS',
        'description': 'CBSD request is approved by SAS'},
    # 100 – 199: general errors regarding CBSD and protocol
    VERSION: {
        'responseData': [],
        'tag': 'VERSION',
        'description': 'CBSD protocol version not supported by SAS'},
    BLACKLISTED: {
        'responseData': None,
        'tag': 'BLACKLISTED',
        'description': 'CBSD is blacklisted'},
    MISSING_PARAM: {
        'responseData': [],
        'tag': 'MISSING_PARAM',
        'description': 'CBSD list of missing required parameters'},
    INVALID_VALUE: {
        'responseData': [],
        'tag': 'INVALID_VALUE',
        'description': 'CBSD list of parameters with invalid values'},
    CERT_ERROR: {
        'responseData': None,
        'tag': 'CERT_ERROR',
        'description': 'CBSD certicate has error'},
    DEREGISTER: {
        'responseData': None,
        'tag': 'DEREGISTER',
        'description': 'CBSD has been de-registered by SAS'},
    # 200 – 299: error events related to CBSD registration
    REG_PENDING: {
        'responseData': [],
        'tag': 'REG_PENDING',
        'description': 'CBSD list of missing registration parameters'},
    GROUP_ERROR: {
        'responseData': None,
        'tag': 'GROUP_ERROR',
        'description': 'CBSD grouping parameters description of error(s)'},
    CATEGORY_ERROR: {
        'responseData': None,
        'tag': 'CATEGORY_ERROR',
        'description': 'CBSD wrong category registration'},
    # 300 – 399: error events related to spectrum inquiry
    UNSUPPORTED_SPECTRUM: {
        'responseData': '',
        'tag': 'UNSUPPORTED_SPECTRUM',
        'description': 'CBSD spectrum value not supported by SAS'},
    # 400 – 499: error events related to grant
    INTERFERENCE: {
        'responseData': None,
        'tag': 'INTERFERENCE',
        'description': 'CBSD operation causes PAL interference'},
    GRANT_CONFLICT: {
        'responseData': '',
        'tag': 'GRANT_CONFLICT',
        'description': 'CBSD Grant ID that causes conflict'},
    TOO_MANY_GRANTS: {
        'responseData': [],
        'tag': 'TOO_MANY_GRANTS',
        'description':
        'CBSD list of approved Grant IDs, number of maximum allowed grants'},
    # 500 – 599: error events related to heartbeat
    TERMINATED_GRANT: {
        'responseData': None,
        'tag': 'TERMINATED_GRANT',
        'description': 'Grant ID is terminated'},
    SUSPENDED_GRANT: {
        'responseData': None,
        'tag': 'SUSPENDED_GRANT',
        'description': 'Grant ID is suspended'},
    UNSYNC_OP_PARAM: {
        'responseData': None,
        'tag': 'UNSYNC_OP_PARAM',
        'description': 'Grant parameters out of sync with SAS'}}


# Classes

class CBSD_to_SAS(SAS_Interface):
    """ Class CBSD to SAS Gateway
        Send/Receive messages to/from given URL
    """

    def __init__(self, tls):

        # Logging Instance creation
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        # Handle set-up
        handler = logging.FileHandler(LOG_FILE)
        handler.setLevel(logging.DEBUG)
        # Couple handler to logging instance
        logger.addHandler(handler)

        super(CBSD_to_SAS, self).__init__(tls, logger, handler)

        self.logger = logger
        self.handler = handler

        # Prep SAS to SAS Configuration file set-up section/options
        #self.ini[INI_FILE_SECTION] = INI_FILE_OPTIONS
        self.LoadSettings()

        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('*** CBSD_to_SAS ****')

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
        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('REGISTRATION REQuest')

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
        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('DEREGISTRATION REQuest')

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
        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('SPECTRUM INQUIRY REQuest')

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
        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('GRANT REQuest')

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
        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('GRANT REQuest')

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
        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('RELINQUISHMENT REQuest')

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
        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('HEARTBEAT REQuest')

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
