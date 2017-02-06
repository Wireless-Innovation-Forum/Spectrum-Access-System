#!/usr/bin/env python
# -- encoding: utf-8 --

# Project: CBSD test cases
__author__ = """
    Kaushik Bekkem (kaushik.bekkem@federatedwireless.com),
    Francisco Benavides (francisco.benavides@federatedwireless.com) """
"""
    CBSD User Part Interface
    Federated Wireless

    Test Case: CBSD Device Registration

    One of more Test Cases can be selected for execution using the following
    criteria, using one or more of the following selection attributes and their
    corresponding values:
    - result  = Successful or Unsuccessful
    - step    = Multi-step or Single-step
    - array   = True or False
    - general = New-registration or Re-registration, Missing-parameter,
                Invalid-parameter, Revoked-cbsd, Unsupported-protocol-version,
                Group-error, Category-error
"""

# Unit Test
import unittest
import logging
import time
import os
import json

# Logging
LOG_FORMAT = logging.Formatter(
    '%(asctime)-15s - CBSD REGISTRATION - '
    '%(funcName)s - %(levelname)s - %(message)s')


class TestRegistration(unittest.TestCase):
    """ CBSD - SAS Registration Test Suite """

    def __init__(self, *args, **kwargs):

        super(TestRegistration, self).__init__(*args, **kwargs)

        from harness.cbsd_sas_harness import cbsd_to_sas as sas
        from common import cbsd

        # sas.CCBSD_to_SAS(True)  then HTTPS (TLSv1.2)
        # sas.CCBSD_to_SAS(False) then HTTP
        self.req = sas.CBSD_to_SAS(True)
        self.local_time = self.req.GetLocalTime()
        self.logger = self.req.logger
        self.handler = self.req.handler

        self.res = cbsd.CBSD(self.logger, self.handler, sas)
        self.res.utest(self)

        self.handler.setFormatter(LOG_FORMAT)
        self.logger.debug('*** TestRegistration ****')

    # Set-up and Tear-down

    def setUp(self):
        self.handler.setFormatter(LOG_FORMAT)

    def tearDown(self):
        self.handler.setFormatter(LOG_FORMAT)

    # Test Cases

    def test_10_3_4_1_1_1(self):
        self.logger.info(
            '10.3.4.1.1.1 New Multi-Step registration for CBSD Cat A '
            '(No existing CBSD ID)')

        response = ''
        devices = []
        try:
            devices = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests', 'testdata', 'registration', 'device1_a.json')))

            # Register
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                {"response": {"responseCode": 0}})

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_1_1_2(self):
        self.logger.info(
            '10.3.4.1.1.2 New Multi-Step registration for CBSD Cat B '
            '(No existing CBSD ID)')

        response = ''
        devices = []
        try:
            devices = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests', 'testdata', 'registration', 'device1_b.json')))

            # Register
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                {"response": {"responseCode": 0}})

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_1_1_3(self):
        self.logger.info(
            '10.3.4.1.1.3 New Array Multi-Step registration for CBSD Cat A&B '
            '(No existing CBSD ID)')

        response = ''
        devices = []
        try:
            device1_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests', 'testdata', 'registration', 'device1_a.json')))
            device1_b = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests', 'testdata', 'registration', 'device1_b.json')))
            device2_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests', 'testdata', 'registration', 'device2_a.json')))

            # Register
            devices = [device1_a, device1_b, device2_a]
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                [{"response": {"responseCode": 0}},
                 {"response": {"responseCode": 0}},
                 {"response": {"responseCode": 0}}])

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_1_1_4(self):
        self.logger.info(
            '10.3.4.1.1.4 Re-registration of Multi-step-registered CBSD '
            '(CBSD ID exists)')

        response = ''
        devices = []
        try:
            devices = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests', 'testdata', 'registration', 'device1_b.json')))

            # Register
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                {"response": {"responseCode": 0}})

            # Simulate CBSD power-cycle; do not send deregistration and send
            #   registration again
            #   re-registration is 2nd registration
            time.sleep(1)

            # 2nd Registration (re-registration)
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                {"response": {"responseCode": 0}})

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_1_1_5(self):
        self.logger.info(
            '10_3.4.1.1.5 Array Re-registration of Multi-step-registered CBSD '
            '(CBSD ID exists)')

        response = ''
        devices = []
        try:
            device1_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests', 'testdata', 'registration', 'device1_a.json')))
            device2_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests', 'testdata', 'registration', 'device2_a.json')))
            device3_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests', 'testdata', 'registration', 'device3_a.json')))

            # Register
            devices = [device1_a, device2_a]
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                [{"response": {"responseCode": 0}},
                 {"response": {"responseCode": 0}}])

            # Simulate CBSD power-cycle; do not send deregistration and send
            #   registration again
            #   re-registration is 2nd registration
            time.sleep(1)

            # Register
            devices = [device1_a, device2_a, device3_a]
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                [{"response": {"responseCode": 0}},
                 {"response": {"responseCode": 0}},
                 {"response": {"responseCode": 0}}])

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_1_2_1(self):
        self.logger.info(
            '10.3.4.1.2.1 New Single-Step registration '
            '(CAT A CBSD with no existing CBSD ID)')

        response = ''
        devices = []
        try:
            devices = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))

            # Register
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                {"response": {"responseCode": 0}})

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_1_2_2(self):
        self.logger.info(
            '10.3.4.1.2.2 New Array Single-Step registration '
            '(CAT A CBSD with no existing CBSD ID)')

        response = ''
        devices = []
        try:
            device1_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))
            device2_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device2_a_singlestep.json')))
            device3_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device3_a_singlestep.json')))

            # Register
            devices = [device1_a, device2_a, device3_a]
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                [{"response": {"responseCode": 0}},
                 {"response": {"responseCode": 0}},
                 {"response": {"responseCode": 0}}])

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_1_2_3(self):
        self.logger.info(
            '10.3.4.1.2.3 Re-registration of Single-step-registered CBSD '
            '(CBSD ID exists)')

        response = ''
        devices = []
        try:
            devices = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))

            # Register
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                {"response": {"responseCode": 0}})

            # 2nd Registration (re-registration)
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                {"response": {"responseCode": 0}})

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_1_2_4(self):
        self.logger.info(
            '10.3.4.1.2.4 Array Re-registration of Single-step-registered '
            'CBSD (CBSD ID exists)')

        response = ''
        devices = []
        try:
            device1_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))
            device2_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device2_a_singlestep.json')))
            device3_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device3_a_singlestep.json')))

            # Register
            devices = [device1_a, device2_a]
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                [{"response": {"responseCode": 0}},
                 {"response": {"responseCode": 0}}])

            # Simulate CBSD power-cycle; do not send deregistration and send
            #   registration again
            #   re-registration is 2nd registration
            time.sleep(1)

            # Register
            devices = [device1_a, device2_a, device3_a]
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                [{"response": {"responseCode": 0}},
                 {"response": {"responseCode": 0}},
                 {"response": {"responseCode": 0}}])

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_2_1(self):
        self.logger.info(
            '10.3.4.2.1 Missing Required parameters (responseCode 102)')

        response = ''
        devices = []
        try:
            devices = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a.json')))

            # Register
            del devices['fccId']
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                {"response":
                    {"responseCode": 102,
                     "responseData": ["fccId"]}})

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_2_2(self):
        self.logger.info(
            '10.3.4.2.2 Missing Required parameters in Array request '
            '(responseCode 102)')

        response = ''
        devices = []
        try:
            device1_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a.json')))
            device2_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device2_a.json')))
            device3_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device3_a.json')))

            # Register
            del device3_a['userId']
            devices = [device1_a, device2_a, device3_a]
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                [{"response": {"responseCode": 0}},
                 {"response": {"responseCode": 0}},
                 {"response":
                    {"responseCode": 102,
                     "responseData": ["userId"]}}])

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_2_3(self):
        self.logger.info(
            '10.3.4.2.3 Pending registration (responseCode 200)')

        response = ''
        devices = []
        try:
            devices = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))

            # Register
            del devices['airInterface']['radioTechnology']
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                [{"response":
                    {"responseCode": 200,
                     "responseData": ["airInterface/radioTechnology"]}}])

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_2_4(self):
        self.logger.info(
            '10.3.4.2.4 Pending registration in Array request '
            '(responseCode 200)')

        response = ''
        devices = []
        try:
            device1_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))
            device2_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device2_a_singlestep.json')))
            device3_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device3_a_singlestep.json')))

            # Register
            del device3_a['measCapability']
            devices = [device1_a, device2_a, device3_a]
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                [{"responce": {"reponseCode": 0}},
                 {"responce": {"reponseCode": 0}},
                 {"response":
                    {"responseCode": 200,
                     "responseData": ["measCapability"]}}])

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_2_5_1(self):
        self.logger.info(
            '10.3.4.2.5.1 Invalid Required parameters (responseCode 103)')

        response = ''
        devices = []
        try:
            devices = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))

            # Register
            devices['cbsdSerialNumber'] = 10000
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                [{"response":
                    {"responseCode": 103,
                     "responseData": ["cbsdSerialNumber"]}}])

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_2_5_2(self):
        self.logger.info(
            '10.3.4.2.5.2 Invalid Required parameters in Array request '
            '(responseCode 103)')

        response = ''
        devices = []
        try:
            device1_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))
            device2_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))
            device3_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))

            # Register
            device3_a['fccId'] = 10000
            devices = [device1_a, device2_a, device3_a]
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                [{"reponse": {"responceCode": 0}},
                 {"reponse": {"responceCode": 0}},
                 {"response":
                    {"responseCode": 103,
                     "responseData": ["fccId"]}}])

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_2_5_3(self):
        self.logger.info(
            '10.3.4.2.5.3 Invalid Conditional parameters (responseCode 103)')

        response = ''
        devices = []
        try:
            devices = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))

            # Register
            devices['measCapability'] = 10000
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                [{"response":
                    {"responseCode": 103,
                     "responseData": ["measCapability"]}}])

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_2_5_4(self):
        self.logger.info(
            '10.3.4.2.5.4 Invalid Conditional parameters in Array request '
            '(responseCode 103)')

        response = ''
        devices = []
        try:
            device1_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))
            device2_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device2_a_singlestep.json')))
            device3_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device3_a_singlestep.json')))

            # Register
            device3_a['airInterface']['radioTechnology'] = 10000
            devices = [device1_a, device2_a, device3_a]
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                [{"responce": {"responceCode": 0}},
                 {"responce": {"responceCode": 0}},
                 {"response":
                    {"responseCode": 103,
                     "responseData": ["airInterface/radioTechnology"]}}])

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_2_6(self):
        self.logger.info(
            '10.3.4.2.6 Revoked CBSD (responseCode 101)')

        response = ''
        devices = []
        try:
            devices = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))

            # Register
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                [{"responce": {"responceCode": 0}}])

            # Manually revoke the herein used cbsdId
            #

            # Simulate CBSD power-cycle; do not send deregistration and send
            #   registration again
            #   re-registration is 2nd registration
            time.sleep(1)

            # 2nd Registration (re-registration)
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                {"response": {"responseCode": 101}})

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_2_7(self):
        self.logger.info(
            '10.3.4.2.7 Revoked CBSD in Array request (responseCode 101)')

        response = ''
        devices = []
        try:
            device1_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))
            device2_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device2_a_singlestep.json')))
            device3_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device3_a_singlestep.json')))

            # Register
            devices = [device1_a, device2_a, device3_a]
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                [{"responce": {"responceCode": 0}},
                 {"responce": {"responceCode": 0}},
                 {"responce": {"responceCode": 0}}])

            # Manually revoke the herein used 3rd cbsdId
            #

            # Simulate CBSD power-cycle; do not send deregistration and send
            #   registration again
            #   re-registration is 2nd registration
            time.sleep(1)

            # 2nd Registration (re-registration)
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                [{"responce": {"responceCode": 0}},
                 {"responce": {"responceCode": 0}},
                 {"responce": {"responceCode": 101}}])

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_2_8(self):
        self.logger.info(
            '10.3.4.2.8 Unsupported SAS protocol version (responseCode 100)')

        response = ''
        devices = []
        try:
            devices = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))

            # Register
            self.req.SetVersionNumber('v10.0')
            response = self.req.RegistrationRequest(devices)
            self.req.SetVersionNumber('v1.0')

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                {"responce": {"responceCode": 100}})

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_2_9(self):
        self.logger.info(
            '10.3.4.2.9 Unsupported SAS protocol version in Array request '
            '(responseCode 100)')

        response = ''
        devices = []
        try:
            device1_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))
            device2_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device2_a_singlestep.json')))
            device3_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device3_a_singlestep.json')))

            # Register
            self.req.SetVersionNumber('v10.0')
            devices = [device1_a, device2_a, device3_a]
            response = self.req.RegistrationRequest(devices)
            self.req.SetVersionNumber('v1.0')

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                [{"responce": {"responceCode": 100}},
                 {"responce": {"responceCode": 100}},
                 {"responce": {"responceCode": 100}}])

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_2_10(self):
        self.logger.info(
            '10.3.4.2.10 Group Error (responseCode 201)')

        response = ''
        devices = []
        try:
            devices = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))

            # Register
            devices['groupingParam'] = [
                {"groupType": "interference-coordination",
                 "groupId": "some-group-id"}]
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                {"responce": {"responceCode": 201}})

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_2_11(self):
        self.logger.info(
            '10_3.4.2.11 Group Error in Array request (responseCode 201)')

        response = ''
        devices = []
        try:
            device1_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))
            device2_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))
            device3_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))

            # Register
            device3_a['groupingParam'] = [
                {"groupType": "interference-coordination",
                 "groupId": "some-group-id"}]
            devices = [device1_a, device2_a, device3_a]
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                [{"responce": {"responceCode": 0}},
                 {"responce": {"responceCode": 0}},
                 {"responce": {"responceCode": 201}}])

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_2_12_1(self):
        self.logger.info(
            '10.3.4.2.12.1 CBSD CAT A attempts to register with HAAT >6m, '
            'Category Error (responseCode 202)')

        response = ''
        devices = []
        try:
            devices = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))

            # Register
            devices['installationParam']['latitude'] = 38.8821619
            devices['installationParam']['longitude'] = -77.1159437
            devices['installationParam']['height'] = 8
            devices['installationParam']['indoorDeployment'] = False
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                {"responce": {"responceCode": 202}})

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_2_12_2(self):
        self.logger.info(
            '10.3.4.2.12.2 CBSD CAT A attempts to register with '
            'eirpCapability > 30 dBm/10MHz')

        response = ''
        devices = []
        try:
            devices = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))

            # Register
            devices['installationParam']['eirpCapability'] = 50
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                {"responce": {"responceCode": 202}})

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_2_12_3(self):
        self.logger.info(
            '10.3.4.2.12.3 CBSD CAT B attempts to register with '
            'eirpCapability > 47 dBm/10MHz',
            'TC_10_3_4_2_12_3_REGISTER_SEND',
            'TC_10_3_4_2_12_3_REGISTER_EXPECT')

        response = ''
        devices = []
        try:
            devices = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_b_singlestep.json')))

            # Register
            devices['installationParam']['eirpCapability'] = 50
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                {"responce": {"responceCode": 202}})

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_2_12_4(self):
        self.logger.info(
            '10.3.4.2.12.4 CBSD CAT B attempts a Single-step registration')

        response = ''
        devices = []
        try:
            devices = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_b_singlestep.json')))

            # Register
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                {"responce": {"responceCode": 202}})

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise

    def test_10_3_4_2_13(self):
        self.logger.info(
            '10.3.4.2.13 Category Error in Array request (responseCode 202)')

        response = ''
        devices = []
        try:
            device1_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_a_singlestep.json')))

            device2_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device2_a_singlestep.json')))
            device2_a['installationParam']['latitude'] = 38.882161
            device2_a['installationParam']['longitude'] = -77.115943
            device2_a['installationParam']['height'] = 8
            device2_a['installationParam']['indoorDeployment'] = False

            device3_a = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device3_a_singlestep.json')))
            device3_a['installationParam']['eirpCapability'] = 50

            device1_b = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_b_singlestep.json')))
            device1_b['installationParam']['eirpCapability'] = 50

            device2_b = json.load(
                open(os.path.join(
                    os.getcwd(),
                    'tests',
                    'testdata', 'registration', 'device1_b_singlestep.json')))

            # Register
            devices = [device1_a, device2_a, device3_a, device1_b, device2_b]
            response = self.req.RegistrationRequest(devices)

            # Check registration response
            self.res.assertRegistrationResponse(
                response,
                [{"responce": {"responceCode": 0}},
                 {"responce": {"responceCode": 203}},
                 {"responce": {"responceCode": 203}},
                 {"responce": {"responceCode": 203}},
                 {"responce": {"responceCode": 203}}])

        except Exception as e:
            self.logger.error('{} {} :: {}'.format(devices, e, response))
            raise


if __name__ == '__main__':
    unittest.main()
