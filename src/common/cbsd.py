#!/usr/bin/env python
# -- encoding: utf-8 --

# Project: CBSD to SAS interface
__author__ = "Francisco Benavides (francisco.benavides@federatedwireless.com)"
"""
    CBSD Message Response
    Federated Wireless

    SAS to User Protocol Technical Specification
    WINNF-16-S-0016 SAS to CBSD v0.3.10, 12 July 2016

    9.2     Message Transport
            HTTP v1.1, Content-type: application/json
            JSON objects shall use UTF-8 enconding
            All requests from CBSD to SAS shall use the HTTP POST method

    10      Parameters for SAS-CBSD messages
"""

# Imports
import unittest
import logging
from datetime import datetime
import pytz

# Constants

# Log format
LOG_FORMAT = logging.Formatter(
    '%(asctime)-15s - CBSD - '
    '%(funcName)s - %(levelname)s - %(message)s')
# MeasCapability allowed values
MEAS_CAPABILITY_ALLOWED_VALUES = (
    'EutraCarrierRssiNonTx',
    'EutraCarrierRssiAlways')
CHANNEL_TYPE_ALLOWED_VALUES = (
    'PAL',
    'GAA')
PARAMETER_RESPONSE = (
    'response',
    'responseCode',
    'responseData',
    'responseMessage')
PARAMETER_FREQUENCYRANGE = (
    'lowFrequency',
    'highFrequency')
PARAMETER_OPERATIONPARAM = (
    'operationParam',
    'maxEirp',
    'operationFrequencyRange') + PARAMETER_FREQUENCYRANGE
MESSAGE_PARAMETERS_REGISTRATION = (
    'registrationResponse',
    'cbsdId',
    'measReportConfig') + PARAMETER_RESPONSE
MESSAGE_PARAMETERS_DEREGISTRATION = (
    'deregistrationResponse',
    'cbsdId') + PARAMETER_RESPONSE
MESSAGE_PARAMETERS_SPECTRUMINQUIRY = (
    'spectrumInquiryResponse',
    'cbsdId',
    'availableChannel',
    'frequencyRange',
    'channelType',
    'ruleApplied') + PARAMETER_RESPONSE + PARAMETER_FREQUENCYRANGE
MESSAGE_PARAMETERS_GRANT = (
    'grantResponse',
    'cbsdId',
    'grantId',
    'grantExpireTime',
    'heartbeatInterval',
    'measReportConfig',
    'channelType') + PARAMETER_RESPONSE + PARAMETER_OPERATIONPARAM
MESSAGE_PARAMETERS_HEARTBEAT = (
    'heartbeatResponse',
    'cbsdId',
    'grantId',
    'transmitExpireTime',
    'grantExpireTime',
    'heartbeatInterval',
    'measReportConfig') + PARAMETER_RESPONSE + PARAMETER_OPERATIONPARAM
MESSAGE_PARAMETERS_RELINQUISHMENT = (
    'relinquishmentResponse',
    'cbsdId',
    'grantId') + PARAMETER_RESPONSE
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

# Classes


class CBSD(object):
    """ Class CBSD
        Incoming response message and parameter verification and validation
    """

    def __init__(self, logger, handler, sas):

        self.handler = handler
        self.logger = logger

        self.utc = pytz.timezone('UTC')
        self.fmt = '%Y-%m-%dT%H:%M:%SZ'

        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('*** CBSD ****')

    def utest(self, utest):
        self.utest = utest

    # Assert patterns

    def AssertIncomingStringParam(self, tag, obj, expected_obj=None):
        """ Verify and validate incoming string parameter """
        self.handler.setFormatter(LOG_FORMAT)

        try:
            self.utest.assertIsInstance(obj, basestring)
            if(expected_obj is not None):
                self.utest.assertEqual(obj, expected_obj)

        except Exception as e:
            if(expected_obj is not None):
                self.logger.error(
                    '{} {} :: [{}] >< x[{}]'.format(tag, e, obj, expected_obj))
            else:
                self.logger.error('{} {} :: {}'.format(tag, e, obj))
            raise
        self.logger.debug('{} {}'.format(tag, obj))

    def AssertIncomingIntegerParam(self, tag, obj, expected_obj=None):
        """ Verify and validate integer number parameter """
        self.handler.setFormatter(LOG_FORMAT)

        try:
            self.utest.assertIsInstance(obj, int)
            if(expected_obj is not None):
                self.utest.assertEqual(obj, expected_obj)

        except Exception as e:
            if(expected_obj is not None):
                self.logger.error(
                    '{} {} :: [{}] >< x[{}]'.format(tag, e, obj, expected_obj))
            else:
                self.logger.error('{} {} :: {}'.format(tag, e, obj))
            raise
        self.logger.debug('{} {}'.format(tag, obj))

    def AssertIncomingFloatParam(self, tag, obj, expected_obj=None):
        """ Verify and validate float number parameter """
        self.handler.setFormatter(LOG_FORMAT)

        try:
            self.utest.assertIsInstance(obj, float)
            if(expected_obj is not None):
                self.utest.assertEqual(obj, expected_obj)

        except Exception as e:
            if(expected_obj is not None):
                self.logger.error(
                    '{} {} :: [{}] >< x[{}]'.format(tag, e, obj, expected_obj))
            else:
                self.logger.error('{} {} :: {}'.format(tag, e, obj))
            raise
        self.logger.debug('{} {}'.format(tag, obj))

    def AssertIncomingTime(self, tag, obj, expected_obj=None):
        """ Verify and validate incoming response time parameters """
        self.handler.setFormatter(LOG_FORMAT)

        try:
            self.utest.assertIsInstance(obj, basestring)
            datetime.strptime(obj, self.fmt)
            if(expected_obj is not None):
                self.utest.assertLessEqual(
                    self.utc.localize(
                        datetime.strptime(obj, self.fmt)),
                    self.utc.localize(
                        datetime.strptime(expected_obj, self.fmt)))

        except Exception as e:
            if(expected_obj is not None):
                self.logger.error(
                    '{} {} :: [{}] >< x[{}]'.format(tag, e, obj, expected_obj))
            else:
                self.logger.error('{} {} :: {}'.format(tag, e, obj))
            raise
        self.logger.debug('{} {}'.format(tag, obj))

    # Parameter verification and validation

    def assertResponseMessage(self, obj, expected_obj=None):
        """ Verify and validate 'responseMessage' parameter """
        self.AssertIncomingStringParam(
            'assertResponseMessage', obj, expected_obj)

    def assertResponseDataArrayOfString(self, obj, expected_obj=None):
        """ Verify and validate 'responseData' as an array of strings
            parameter """
        self.handler.setFormatter(LOG_FORMAT)

        try:
            self.utest.assertIsInstance(obj, list)
            for o in obj:
                self.utest.assertIsInstance(o, basestring)

            if(expected_obj is not None):
                self.utest.assertEqual(len(obj), len(expected_obj))
                for o in obj:
                    self.utest.assertIn(o, expected_obj)

        except Exception as e:
            if(expected_obj is not None):
                self.logger.error(
                    'assertResponseDataArrayOfString {} :: [{}] >< x[{}]'
                    .format(e, obj, expected_obj))
            else:
                self.logger.error(
                    'assertResponseDataArrayOfString {} :: {}'.format(e, obj))
            raise
        self.logger.debug('assertResponseDataArrayOfString {}'.format(obj))

    def assertResponseDataString(self, obj, expected_obj=None):
        """ Verify and validate 'responseData' as string parameter """
        self.AssertIncomingStringParam(
            'assertResponseMessage', obj, expected_obj)

    def assertResponseCode(self, obj, expected_obj):
        """ Verify and validate 'responseCode' parameter """
        if(isinstance(expected_obj, basestring)):
            self.utest.assertIn(obj, [int(x) for x in expected_obj.split(',')])
        else:
            self.AssertIncomingIntegerParam(
                'assertResponseCode', obj, expected_obj)

    def assertResponse(self, obj, expected_obj):
        """ Verify and validate 'responseCode' parameter """
        self.handler.setFormatter(LOG_FORMAT)

        try:
            # Required parameter
            self.utest.assertIsInstance(obj, dict)
            self.utest.assertIn('responseCode', obj)
            self.assertResponseCode(
                obj['responseCode'], expected_obj['responseCode'])
            self.logger.debug(
                'assertResponse r[{}] x[{}]'
                .format(obj['responseCode'], expected_obj['responseCode']))
            # Optional parameters
            if('responseMessage' in obj):
                if('responseMessage' in expected_obj):
                    self.assertResponseMessage(
                        obj['responseMessage'],
                        expected_obj['responseMessage'])
                else:
                    self.assertResponseMessage(obj['responseMessage'])
            if('responseData' in obj):
                if(obj['responseCode'] in
                    (VERSION,
                     MISSING_PARAM,
                     INVALID_VALUE,
                     REG_PENDING)):
                    if('responseData' in expected_obj):
                        self.assertResponseDataArrayOfString(
                            obj['responseData'], expected_obj['responseData'])
                    else:
                        self.assertResponseDataArrayOfString(
                            obj['responseData'])

                elif(obj['responseCode'] in (UNSUPPORTED_SPECTRUM,
                                             GRANT_CONFLICT)):
                    self.utest.assertIn('responseData', obj)
                    if('responseData' in expected_obj):
                        self.assertResponseDataString(
                            obj['responseData'], expected_obj['responseData'])
                    else:
                        self.assertResponseDataString(obj['responseData'])
                else:
                    raise Exception(
                        "'responseCode' {} should not have 'responseData' "
                        "present"
                        .format(obj['responseCode']))

        except Exception as e:
            self.logger.error(
                'assertResponse {} :: {} >< {}'.format(e, obj, expected_obj))
            raise
        self.logger.debug('assertResponse {}'.format(obj))

    def assertLowFrequency(self, obj, expected_obj=None):
        """ Verify and validate 'lowFrequency' parameter """
        self.AssertIncomingFloatParam('assertLowFrequency', obj, expected_obj)

    def assertHighFrequency(self, obj, expected_obj=None):
        """ Verify and validate 'highFrequency' parameter """
        self.AssertIncomingFloatParam('assertHighFrequency', obj, expected_obj)

    def assertFrequencyRange(self, obj, expected_obj=None):
        """ Verify and validate 'Frequency Range' object """
        self.handler.setFormatter(LOG_FORMAT)

        try:
            # Required parameters
            self.utest.assertIsInstance(obj, dict)
            self.utest.assertIn('lowFrequency', obj)
            self.utest.assertIn('highFrequency', obj)
            if('lowFrequency' in expected_obj):
                self.assertLowFrequency(
                    obj['lowFrequency'], expected_obj['lowFrequency'])
            else:
                self.assertLowFrequency(obj['lowFrequency'])
            if('highFrequency' in expected_obj):
                self.assertHighFrequency(
                    obj['highFrequency'], expected_obj['highFrequency'])
            else:
                self.assertHighFrequency(obj['highFrequency'])

        except Exception as e:
            self.logger.error(
                'assertFrequencyRange {} :: [{}] >< x[{}]'
                .format(e, obj, expected_obj))
            raise
        self.logger.debug('assertFrequencyRange {}'.format(obj))

    def assertChannelType(self, obj, expected_obj=None):
        """ Verify and validate 'channelType' object """
        self.handler.setFormatter(LOG_FORMAT)

        try:
            self.utest.assertIsInstance(obj, basestring)
            self.utest.assertIn(obj, CHANNEL_TYPE_ALLOWED_VALUES)
            if(expected_obj is not None):
                self.utest.assertEqual(obj, expected_obj)

        except Exception as e:
            if(expected_obj is not None):
                self.logger.error(
                    'assertChannelType {} :: [{}] >< x[{}]'
                    .format(e, obj, expected_obj))
            else:
                self.logger.error('assertChannelType {} :: {}'.format(e, obj))
            raise
        self.logger.debug('assertChannelType {}'.format(obj))

    def assertRuleApplied(self, obj, expected_obj):
        """ Verifyand validate 'ruleApplied' object """
        self.AssertIncomingStringParam('assertRuleApplied', obj, expected_obj)

    def assertAvailableChannel(self, obj, expected_obj):
        """ Verify and validate 'availableChannel' parameter """
        self.handler.setFormatter(LOG_FORMAT)

        try:
            self.utest.assertIsInstance(obj, list)
            self.utest.assertEqual(len(obj), len(expected_obj))
            for (o, x) in zip(obj, expected_obj):
                # Required parameters
                self.utest.assertIn('frequencyRange', o)
                self.utest.assertIn('channelType', o)
                self.utest.assertIn('ruleApplied', o)
                self.assertFrequencyRange(
                    o['frequencyRange'], x['frequencyRange'])
                self.assertChannelType(o['channelType'], x['channelType'])
                self.assertRuleApplied(o['ruleApplied'], x['ruleApplied'])

        except Exception as e:
            self.logger.error(
                'assertAvailableChannel {} :: [{}] >< x[{}]'
                .format(e, obj, expected_obj))
            raise
        self.logger.debug('assertAvailableChannel {}'.format(obj))

    def assertMaxEirp(self, obj, expected_obj=None):
        """ Verify and validate 'maxEirp' parameter """
        self.AssertIncomingFloatParam('assertMaxEirp', obj, expected_obj)

    def assertOperationParam(self, obj, expected_obj=None):
        """ Verify and validate 'operationParam' parameter """
        self.handler.setFormatter(LOG_FORMAT)

        try:
            # Required parameters
            self.utest.assertIsInstance(obj, dict)
            self.utest.assertIn('maxEirp', obj)
            self.utest.assertIn('operationFrequencyRange', obj)
            self.assertMaxEirp(obj['maxEirp'], expected_obj['maxEirp'])
            self.assertFrequencyRange(
                obj['operationFrequencyRange'],
                expected_obj['operationFrequencyRange'])

        except Exception as e:
            self.logger.error(
                'assertOperationParam {} :: [{}] >< x[{}]'
                .format(e, obj, expected_obj))
            raise
        self.logger.debug('assertOperationParam {}'.format(obj))

    def assertCbsdId(self, obj, expected_obj=None):
        """ Verify and valide 'cbsdId' parameter """
        self.AssertIncomingStringParam('assertCbsdId', obj, expected_obj)

    def assertGrantId(self, obj, expected_obj=None):
        """ Verify and validate 'grantId' paramter """
        self.AssertIncomingStringParam('assertGrantId', obj, expected_obj)

    def assertMeasReportConfig(self, obj, expected_obj=None):
        """ Verify and validate 'measReportConfig' parameter """
        self.handler.setFormatter(LOG_FORMAT)

        try:
            self.utest.assertIsInstance(obj, list)
            for o in obj:
                self.utest.assertIsInstance(o, basestring)
            for o in obj:
                self.utest.assertIn(o, MEAS_CAPABILITY_ALLOWED_VALUES)

            if(expected_obj is not None):
                self.utest.assertEqual(len(obj), len(expected_obj))
                for o in obj:
                    self.utest.assertIn(o, expected_obj)

        except Exception as e:
            if(expected_obj is not None):
                self.logger.error(
                    'assertMeasReportConfig {} :: [{}] >< x[{}]'
                    .format(e, obj, expected_obj))
            else:
                self.logger.error(
                    'assertMeasReportConfig {} :: {}'.format(e, obj))
            raise
        self.logger.debug('assertMeasReportConfig {}'.format(obj))

    def assertGrantExpireTime(self, obj, expected_obj=None):
        """ Verify and validate 'grantExpireTime' parameter """
        self.AssertIncomingTime('assertGrantExpireTime', obj, expected_obj)

    def assertHeartbeatInterval(self, obj, expected_obj=None):
        """ Verify and validate 'heartbeatInterval' parameter """
        self.AssertIncomingFloatParam(
            'assertHeartbeatInterval', obj, expected_obj)

    def assertTransmitExpireTime(self, obj, expected_obj=None):
        """ Verify and validate 'transmitExpireTime' parameter """
        self.AssertIncomingTime('assertTransmitExpireTime', obj, expected_obj)

    def assertGrantResponseCheck(self, r, g, x):
        """ Verify and validate 'operationStatusReq' parameter """

        try:

            # Required parameters
            self.utest.assertIn('response', g)
            self.assertResponse(g['response'], x['response'])

            # Conditional parameters
            if(g['response']['responseCode'] == SUCCESS):

                self.utest.assertIn('cbsdId', g)
                self.utest.assertIn('grantId', g)
                self.utest.assertIn('channelType', g)
                self.utest.assertIn('grantExpireTime', g)
                self.utest.assertIn('heartbeatInterval', g)

                self.utest.assertEqual(g['cbsdId'], r['cbsdId'])
                if('grantId' in x):
                    self.assertGrantId(g['grantId'], x['grantId'])
                else:
                    self.assertGrantId(g['grantId'])
                if('channelType' in x):
                    self.assertChannelType(g['channelType'], x['channelType'])
                else:
                    self.assertChannelType(g['channelType'])
                if('grantExpireTime' in x):
                    self.assertGrantExpireTime(
                        g['grantExpireTime'], x['grantExpireTime'])
                else:
                    self.assertGrantExpireTime(g['grantExpireTime'])
                if('heartbeatInterval' in x):
                    self.assertHeartbeatInterval(
                        g['heartbeatInterval'], x['heartbeatInterval'])
                else:
                    self.assertHeartbeatInterval(g['heartbeatInterval'])

            elif(g['response']['responseCode'] in (VERSION,
                                                   MISSING_PARAM,
                                                   INVALID_VALUE,
                                                   GRANT_CONFLICT)):
                self.utest.assertIn('responseData', g['response'])
                if(g['response']['responseCode'] != VERSION):
                    if('cbsdId' in g['response']['responseData']):
                        self.utest.assertNotIn('cbsdId', g)
                    else:
                        self.utest.assertIn('cbsdId', g)
                    self.utest.assertNotIn('grantId', g)
                    self.utest.assertNotIn('channelType', g)
                    self.utest.assertNotIn('grantExpireTime', g)
                    self.utest.assertNotIn('heartbeatInterval', g)

            # Optional parameters
            if('operationParam' in x):
                self.utest.assertIn('operationParam', g)
                self.assertOperationParam(
                    g['operationParam'], x['operationParam'])
            elif('operationParam' in g):
                self.assertOperationParam(g['operationParam'])
            if('measReportConfig' in x):
                self.utest.assertIn('measReportConfig', g)
                self.assertMeasReportConfig(
                    g['measReportConfig'], x['measReportConfig'])
            elif('measReportConfig' in g):
                self.assertMeasReportConfig(g['measReportConfig'])

        except Exception as e:
            self.handler.setFormatter(LOG_FORMAT)
            self.logger.error(
                'assertGrantResponseCheck {} :: [{}] >< x[{}]'.format(e, g, x))
            raise
        self.logger.debug('assertGrantResponseCheck {}'.format(g))

    # Message Response verification and validation

    def assertRegistrationResponse(self, reg_obj, expected_obj):
        """ Verify and validate Registration Response received from SAS """
        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('assertRegistrationResponse')

        try:
            if(not isinstance(reg_obj, list)):
                reg_obj = [reg_obj]
            if(not isinstance(expected_obj, list)):
                expected_obj = [expected_obj]

            self.utest.assertEqual(len(reg_obj), len(expected_obj))
            for (r, x) in zip(reg_obj, expected_obj):

                # Required parameters
                self.utest.assertIn('response', r)
                self.assertResponse(r['response'], x['response'])

                # Conditional parameters
                if(r['response']['responseCode'] == SUCCESS):
                    self.utest.assertIn('cbsdId', r)
                    if('cbsdId' in x):
                        self.assertCbsdId(r['cbsdId'], x['cbsdId'])
                    else:
                        self.assertCbsdId(r['cbsdId'])
                elif(r['response']['responseCode'] in
                     (VERSION,
                      BLACKLISTED,
                      MISSING_PARAM,
                      INVALID_VALUE,
                      REG_PENDING)):
                    self.utest.assertNotIn('cbsdId', r)
                    if(r['response']['responseCode'] not in
                        (VERSION,
                         BLACKLISTED)):
                        self.utest.assertIn('responseData', r['response'])

                # Optional parameters
                if('measReportConfig' in x):
                    self.utest.assertIn('measReportConfig', r)
                    self.assertMeasReportConfig(
                        r['measReportConfig'], x['measReportConfig'])
                elif('measReportConfig' in r):
                    self.assertMeasReportConfig(r['measReportConfig'])

                # Check fr any additional incoming parameters, which might
                #   not belong to the message
                try:
                    for param in r:
                        self.utest.assertIn(
                            param, MESSAGE_PARAMETERS_REGISTRATION)
                except Exception as e:
                    self.logger.warning(
                        'assertRegistrationrResponse {}'.format(e))

        except Exception as e:
            self.logger.error(
                'assertRegistrationrResponse {} :: [{}] >< x[{}]'
                .format(e, reg_obj, expected_obj))
            raise

    def assertDeregistrationResponse(self, reg_obj, dereg_obj, expected_obj):
        """ Verify and validate Deregistration Response received from SAS """
        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('assertDeregistrationResponse')

        try:
            if(not isinstance(reg_obj, list)):
                reg_obj = [reg_obj]
            if(not isinstance(dereg_obj, list)):
                dereg_obj = [dereg_obj]
            if(not isinstance(expected_obj, list)):
                expected_obj = [expected_obj]

            self.utest.assertEqual(len(reg_obj), len(dereg_obj))
            self.utest.assertEqual(len(reg_obj), len(expected_obj))

            for (r, d, x) in zip(reg_obj, dereg_obj, expected_obj):

                # Required parameters
                self.utest.assertIn('response', d)
                self.assertResponse(d['response'], x['response'])

                # Conditional parameters
                if(d['response']['responseCode'] == SUCCESS):
                    self.utest.assertIn('cbsdId', d)
                    if('cbsdId' in x):
                        self.asserCbsdId(d['cbsdId'], x['cbsdId'])
                    else:
                        self.assertCbsdId(d['cbsdId'])

                else:
                    self.utest.assertNotIn('cbsdId', d)
                    if(d['response']['responseCode'] in
                        (VERSION,
                         MISSING_PARAM,
                         INVALID_VALUE)):
                        self.utest.assertIn('responseData', d['response'])
                        if(d['response']['responseCode'] != VERSION):
                            self.utest.assertIn(
                                'cbsdId', d['response']['responseData'])

                # Check fr any additional incoming parameters, which might
                #   not belong to the message
                try:
                    for param in d:
                        self.utest.assertIn(
                            param, MESSAGE_PARAMETERS_DEREGISTRATION)
                except Exception as e:
                    self.logger.warning(
                        'assertDeregistrationResponse {}'.format(e))

        except Exception as e:
            self.logger.error(
                'assertDeregistrationResponse {} :: r[{}] >< d[{}] >< x[{}]'
                .format(e, reg_obj, dereg_obj, expected_obj))
            raise

    def assertSpectrumInquiryResponse(self, reg_obj, spec_obj, expected_obj):
        """ Verify and validate Spectrum Inquiry Response received from SAS """
        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('assertSpectrumInquiryResponse')

        try:
            if(not isinstance(reg_obj, list)):
                reg_obj = [reg_obj]
            if(not isinstance(spec_obj, list)):
                spec_obj = [spec_obj]
            if(not isinstance(expected_obj, list)):
                expected_obj = [expected_obj]

            self.utest.assertEqual(len(reg_obj), len(expected_obj))
            self.utest.assertEqual(len(spec_obj), len(expected_obj))

            for (r, s, x) in zip(reg_obj, spec_obj, expected_obj):

                # Required parameters
                self.utest.assertIn('response', s)
                self.assertResponse(s['response'], x['response'])

                # Conditional parameters
                if(s['response']['responseCode'] == SUCCESS):

                    self.utest.assertIn('cbsdId', s)
                    if('cbsdId' in x):
                        self.asserCbsdId(s['cbsdId'], x['cbsdId'])
                    else:
                        self.assertCbsdId(s['cbsdId'])

                    self.utest.assertIn('availableChannel', s)
                    if('availableChannel' in x):
                        self.assertAvailableChannel(
                            s['availableChannel'], x['availableChannel'])
                    else:
                        self.assertAvailableChannel(s['availableChannel'])

                elif(s['response']['responseCode'] in
                     (VERSION,
                      MISSING_PARAM,
                      INVALID_VALUE,
                      UNSUPPORTED_SPECTRUM)):
                    if(s['response']['responseCode'] not in
                        (VERSION,
                         UNSUPPORTED_SPECTRUM)):
                        if('cbsdId' in s['response']['responseData']):
                            self.utest.assertNotIn('cbsdId', s)
                        else:
                            self.utest.assertIn('cbsdId', s)
                        self.utest.assertNotIn('availableChannel', s)
                        self.utest.assertIn('responseData', s['response'])

                # Check fr any additional incoming parameters, which might
                #   not belong to the message
                try:
                    for param in s:
                        self.utest.assertIn(
                            param, MESSAGE_PARAMETERS_SPECTRUMINQUIRY)
                except Exception as e:
                    self.logger.warning(
                        'assertSpectrumInquiryResponse {}'.format(e))

        except Exception as e:
            self.logger.error(
                'assertSpectrumInquiryResponse {} :: r[{}] >< s[{}] >< x[{}]'
                .format(e, reg_obj, spec_obj, expected_obj))
            raise

    def assertGrantResponse(self, reg_obj, grant_obj, expected_obj):
        """ Verify and validate Grant Response received from SAS """
        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('assertGrantResponse')

        try:
            if(not isinstance(reg_obj, list)):
                reg_obj = [reg_obj]
            if(not isinstance(grant_obj, list)):
                grant_obj = [grant_obj]
            if(not isinstance(expected_obj, list)):
                expected_obj = [expected_obj]
            self.logger.debug(
                'Lenght: r[{}] g[{}] x[{}]'
                .format(len(reg_obj), len(grant_obj), len(expected_obj)))

            self.utest.assertEqual(len(reg_obj), len(expected_obj))
            self.utest.assertEqual(len(grant_obj), len(expected_obj))
            for (r, g, x) in zip(reg_obj, grant_obj, expected_obj):
                self.assertGrantResponseCheck(r, g, x)

                # Check fr any additional incoming parameters, which might
                #   not belong to the message
                try:
                    for param in g:
                        self.utest.assertIn(param, MESSAGE_PARAMETERS_GRANT)
                except Exception as e:
                    self.logger.warning('assertGrantResponse {}'.format(e))

        except Exception as e:
            self.logger.error(
                'assertGrantResponse {} :: r[{}] >< g[{}] >< x[{}]'
                .format(e, reg_obj, grant_obj, expected_obj))
            raise

    def assertGrantResponseOneToMore(self, reg_obj, grant_obj, expected_obj):
        """ Verify and validate Grant Response received from SAS """
        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('assertGrantResponseOneToMore')

        try:
            if(not isinstance(reg_obj, list)):
                reg_obj = [reg_obj]
            if(not isinstance(grant_obj, list)):
                grant_obj = [grant_obj]
            if(not isinstance(expected_obj, list)):
                expected_obj = [expected_obj]
            self.logger.debug(
                'Lenght: r[{}] g[{}] x[{}]'
                .format(len(reg_obj), len(grant_obj), len(expected_obj)))

            self.utest.assertEqual(len(grant_obj), len(expected_obj))
            for r in reg_obj:
                for (g, x) in zip(grant_obj, expected_obj):
                    self.assertGrantResponseCheck(r, g, x)

                    # Check fr any additional incoming parameters, which might
                    #   not belong to the message
                    try:
                        for param in g:
                            self.utest.assertIn(
                                param, MESSAGE_PARAMETERS_GRANT)
                    except Exception as e:
                        self.logger.warning(
                            'assertGrantResponseOneToMore {}'.format(e))

        except Exception as e:
            self.logger.error(
                'assertGrantResponseOneToMore {} :: r[{}] >< g[{}] >< x[{}]'
                .format(e, reg_obj, grant_obj, expected_obj))
            raise

    def assertHeartbeatResponse(self, previous_obj, hb_obj, expected_obj):
        """ Verify and validate Heartbeat Response received from SAS """
        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('assertHeartbeatResponse')

        try:
            if(not isinstance(previous_obj, list)):
                previous_obj = [previous_obj]
            if(not isinstance(hb_obj, list)):
                hb_obj = [hb_obj]
            if(not isinstance(expected_obj, list)):
                expected_obj = [expected_obj]

            self.utest.assertEqual(len(previous_obj), len(expected_obj))
            self.utest.assertEqual(len(hb_obj), len(expected_obj))
            for (p, h, x) in zip(previous_obj, hb_obj, expected_obj):

                # Required parameters
                self.utest.assertIn('response', h)
                self.utest.assertIn('transmitExpireTime', h)
                self.assertResponse(h['response'], x['response'])
                if('transmitExpireTime' in x):
                    self.assertTransmitExpireTime(
                        h['transmitExpireTime'], x['transmitExpireTime'])
                else:
                    self.assertTransmitExpireTime(h['transmitExpireTime'])

                # Conditional parameters
                if(h['response']['responseCode'] == MISSING_PARAM):
                    if('cbsdId' in h['response']['responseData']):
                        self.utest.assertNotIn('cbsdId', h)
                    else:
                        self.utest.assertIn('cbsdId', h)
                    if('grantId' in h['response']['responseData']):
                        self.utest.assertNotIn('grantId', h)
                    else:
                        self.utest.assertIn('grantId', h)
                else:
                    self.utest.assertIn('cbsdId', h)
                    self.utest.assertIn('grantId', h)
                    self.assertCbsdId(h['cbsdId'], p['cbsdId'])
                    self.assertGrantId(h['grantId'], p['grantId'])
                    if((h['response']['responseCode'] == SUCCESS) or
                       (h['response']['responseCode'] == SUSPENDED_GRANT)):
                        if('grantRenew' in p):
                            if(p['grantRenew']):
                                self.utest.assertIn('grantExpireTime', h)
                                if('grantExpireTime' in x):
                                    self.assertGrantExpireTime(
                                        h['grantExpireTime'],
                                        x['grantExpireTime'])
                                else:
                                    self.assertGrantExpireTime(
                                        h['grantExpireTime'])
                        elif('grantExpireTime' in h):
                            if('grantExpireTime' in x):
                                self.assertGrantExpireTime(
                                    h['grantExpireTime'], x['grantExpireTime'])
                            else:
                                self.assertGrantExpireTime(
                                    h['grantExpireTime'])
                    else:
                        self.utest.assertNotIn('grantExpireTime', h)

                # Optional parameters
                if('heartbeatInterval' in x):
                    self.utest.assertIn('heartbeatInterval', h)
                    self.assertHeartbeatInterval(
                        h['heartbeatInterval'], x['heartbeatInterval'])
                elif('heartbeatInterval' in h):
                    self.assertHeartbeatInterval(h['heartbeatInterval'])
                if('operationParam' in x):
                    self.utest.assertIn('operationParam', h)
                    self.assertOperationParam(
                        h['operationParam'], x['operationParam'])
                elif('operationParam' in h):
                    self.assertOperationParam(h['operationParam'])
                if('measReportConfig' in x):
                    self.utest.assertIn('measReportConfig', h)
                    self.assertMeasReportConfig(
                        h['measReportConfig'], x['measReportConfig'])
                elif('measReportConfig' in h):
                    self.assertMeasReportConfig(h['measReportConfig'])

                # Check fr any additional incoming parameters, which might
                #   not belong to the message
                try:
                    for param in h:
                        self.utest.assertIn(
                            param, MESSAGE_PARAMETERS_HEARTBEAT)
                except Exception as e:
                    self.logger.warning('assertHeartbeatResponse {}'.format(e))

        except Exception as e:
            self.logger.error(
                'assertHeartbeatResponse {} :: p[{}] >< h[{}] >< x[{}]'
                .format(e, previous_obj, hb_obj, expected_obj))
            raise

    def assertRelinquishmentResponse(self, grant_obj, rel_obj, expected_obj):
        """ Verify and validate Relinquishment Response receibed from SAS """
        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('assertRelinquishmentResponse')

        try:
            if(not isinstance(grant_obj, list)):
                grant_obj = [grant_obj]
            if(not isinstance(rel_obj, list)):
                rel_obj = [rel_obj]
            if(not isinstance(expected_obj, list)):
                expected_obj = [expected_obj]

            self.utest.assertEqual(len(grant_obj), len(expected_obj))
            self.utest.assertEqual(len(rel_obj), len(expected_obj))
            for (g, r, x) in zip(grant_obj, rel_obj, expected_obj):

                # Required parameters
                self.utest.assertIn('response', r)
                self.assertResponse(r['response'], x['response'])

                # Conditional parameters
                if(r['response']['responseCode'] == MISSING_PARAM):
                    if('cbsdId' in r['response']['responseData']):
                        self.utest.assertNotIn('cbsdId', r)
                    else:
                        self.utest.assertIn('cbsdId', r)
                    if('grantId' in r['response']['responseData']):
                        self.utest.assertNotIn('grantId', r)
                    else:
                        self.utest.assertIn('grantId', r)
                else:
                    self.utest.assertIn('cbsdId', r)
                    self.utest.assertIn('grantId', r)
                    self.assertCbsdId(r['cbsdId'], g['cbsdId'])
                    self.assertGrantId(r['grantId'], g['grantId'])

                # Check fr any additional incoming parameters, which might
                #   not belong to the message
                try:
                    for param in r:
                        self.utest.assertIn(
                            param, MESSAGE_PARAMETERS_RELINQUISHMENT)
                except Exception as e:
                    self.logger.warning(
                        'assertRelinquishmentResponse {}'.format(e))

        except Exception as e:
            self.logger.error(
                'assertRelinquishmentResponse {} :: g[{}] >< rl[{}] >< x[{}]'
                .format(e, grant_obj, rel_obj, expected_obj))
            raise


if(__name__ == '__main__'):
    unittest.main()
