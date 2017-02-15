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
""" CBSD Registration User Part """

import json
import os
import unittest
import cbsd_sas as sas
import time


class TestRegistration(unittest.TestCase):
    """ CBSD - SAS Registration Test Suite """

    def setUp(self):
        self._sas, self._sas_admin = sas.GetTestingSas()
        # self._sas_admin.Reset()
        pass

    def tearDown(self):
        pass

    # Test Cases

    def test_10_3_4_1_1_1(self):
        self._sas.logger.info(
            '10.3.4.1.1.1 New Multi-Step registration for CBSD Cat A '
            '(No existing CBSD ID)')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'reg1_a.json')))

        # Register
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertIn('cbsdId', response[0])

    def test_10_3_4_1_1_2(self):
        self._sas.logger.info(
            '10.3.4.1.1.2 New Multi-Step registration for CBSD Cat B '
            '(No existing CBSD ID)')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'reg1_b.json')))

        # Register
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertIn('cbsdId', response[0])

    def test_10_3_4_1_1_3(self):
        self._sas.logger.info(
            '10.3.4.1.1.3 New Array Multi-Step registration for CBSD Cat A&B '
            '(No existing CBSD ID)')

        device1_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'reg1_a.json')))
        device1_b = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'reg1_b.json')))
        device2_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'reg2_a.json')))

        # Register
        devices = [device1_a, device1_b, device2_a]
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[1]['response']['responseCode'], 0)
        self.assertEqual(response[2]['response']['responseCode'], 0)
        self.assertIn('cbsdId', response[0])
        self.assertIn('cbsdId', response[1])
        self.assertIn('cbsdId', response[2])

    def test_10_3_4_1_1_4(self):
        self._sas.logger.info(
            '10.3.4.1.1.4 Re-registration of Multi-step-registered CBSD '
            '(CBSD ID exists)')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'reg1_b.json')))

        # Register
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)

        # Simulate CBSD power-cycle; do not send deregistration and send
        #   registration again
        #   re-registration is 2nd registration
        time.sleep(1)

        # 2nd Registration (re-registration)
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertIn('cbsdId', response[0])

    def test_10_3_4_1_1_5(self):
        self._sas.logger.info(
            '10_3.4.1.1.5 Array Re-registration of Multi-step-registered CBSD '
            '(CBSD ID exists)')

        device1_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'reg1_a.json')))
        device2_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'reg2_a.json')))
        device3_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'reg3_a.json')))

        # Register
        devices = [device1_a, device2_a]
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[1]['response']['responseCode'], 0)

        # Simulate CBSD power-cycle; do not send deregistration and send
        #   registration again
        #   re-registration is 2nd registration
        time.sleep(1)

        # Register
        devices = [device1_a, device2_a, device3_a]
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[1]['response']['responseCode'], 0)
        self.assertEqual(response[2]['response']['responseCode'], 0)
        self.assertIn('cbsdId', response[0])
        self.assertIn('cbsdId', response[1])
        self.assertIn('cbsdId', response[2])

    def test_10_3_4_1_2_1(self):
        self._sas.logger.info(
            '10.3.4.1.2.1 New Single-Step registration '
            '(CAT A CBSD with no existing CBSD ID)')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a_singlestep.json')))

        # Register
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertIn('cbsdId', response[0])

    def test_10_3_4_1_2_2(self):
        self._sas.logger.info(
            '10.3.4.1.2.2 New Array Single-Step registration '
            '(CAT A CBSD with no existing CBSD ID)')

        device1_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a_singlestep.json')))
        device2_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg2_a_singlestep.json')))
        device3_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg3_a_singlestep.json')))

        # Register
        devices = [device1_a, device2_a, device3_a]
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[1]['response']['responseCode'], 0)
        self.assertEqual(response[2]['response']['responseCode'], 0)
        self.assertIn('cbsdId', response[0])
        self.assertIn('cbsdId', response[1])
        self.assertIn('cbsdId', response[2])

    def test_10_3_4_1_2_3(self):
        self._sas.logger.info(
            '10.3.4.1.2.3 Re-registration of Single-step-registered CBSD '
            '(CBSD ID exists)')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a_singlestep.json')))

        # Register
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)

        # 2nd Registration (re-registration)
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertIn('cbsdId', response[0])

    def test_10_3_4_1_2_4(self):
        self._sas.logger.info(
            '10.3.4.1.2.4 Array Re-registration of Single-step-registered '
            'CBSD (CBSD ID exists)')

        device1_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a_singlestep.json')))
        device2_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg2_a_singlestep.json')))
        device3_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg3_a_singlestep.json')))

        # Register
        devices = [device1_a, device2_a]
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[1]['response']['responseCode'], 0)

        # Simulate CBSD power-cycle; do not send deregistration and send
        #   registration again
        #   re-registration is 2nd registration
        time.sleep(1)

        # Register
        devices = [device1_a, device2_a, device3_a]
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[1]['response']['responseCode'], 0)
        self.assertEqual(response[2]['response']['responseCode'], 0)
        self.assertIn('cbsdId', response[0])
        self.assertIn('cbsdId', response[1])
        self.assertIn('cbsdId', response[2])

    def test_10_3_4_2_1(self):
        self._sas.logger.info(
            '10.3.4.2.1 Missing Required parameters (responseCode 102)')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a.json')))

        # Register
        del devices['fccId']
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 102)
        self.assertNotIn('cbsdId', response[0])

    def test_10_3_4_2_2(self):
        self._sas.logger.info(
            '10.3.4.2.2 Missing Required parameters in Array request '
            '(responseCode 102)')

        device1_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a.json')))
        device2_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg2_a.json')))
        device3_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg3_a.json')))

        # Register
        del device3_a['userId']
        devices = [device1_a, device2_a, device3_a]
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[1]['response']['responseCode'], 0)
        self.assertEqual(response[2]['response']['responseCode'], 102)
        self.assertIn('cbsdId', response[0])
        self.assertIn('cbsdId', response[0])
        self.assertNotIn('cbsdId', response[0])

    def test_10_3_4_2_3(self):
        self._sas.logger.info(
            '10.3.4.2.3 Pending registration (responseCode 200)')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a_singlestep.json')))

        # Register
        del devices['airInterface']['radioTechnology']
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 200)
        self.assertNotIn('cbsdId', response[0])

    def test_10_3_4_2_4(self):
        self._sas.logger.info(
            '10.3.4.2.4 Pending registration in Array request '
            '(responseCode 200)')

        device1_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a_singlestep.json')))
        device2_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg2_a_singlestep.json')))
        device3_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg3_a_singlestep.json')))

        # Register
        del device3_a['measCapability']
        devices = [device1_a, device2_a, device3_a]
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[0]['response']['responseCode'], 200)
        self.assertIn('cbsdId', response[0])
        self.assertIn('cbsdId', response[0])
        self.assertNotIn('cbsdId', response[0])

    def test_10_3_4_2_5_1(self):
        self._sas.logger.info(
            '10.3.4.2.5.1 Invalid Required parameters (responseCode 103)')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a_singlestep.json')))

        # Register
        devices['cbsdSerialNumber'] = 10000
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 103)
        self.assertNotIn('cbsdId', response[0])

    def test_10_3_4_2_5_2(self):
        self._sas.logger.info(
            '10.3.4.2.5.2 Invalid Required parameters in Array request '
            '(responseCode 103)')

        device1_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a_singlestep.json')))
        device2_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg2_a_singlestep.json')))
        device3_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg3_a_singlestep.json')))

        # Register
        device3_a['fccId'] = 10000
        devices = [device1_a, device2_a, device3_a]
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[1]['response']['responseCode'], 0)
        self.assertEqual(response[2]['response']['responseCode'], 103)
        self.assertIn('cbsdId', response[0])
        self.assertIn('cbsdId', response[1])
        self.assertNotIn('cbsdId', response[2])

    def test_10_3_4_2_5_3(self):
        self._sas.logger.info(
            '10.3.4.2.5.3 Invalid Conditional parameters (responseCode 103)')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a_singlestep.json')))

        # Register
        devices['measCapability'] = 10000
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 103)
        self.assertNotIn('cbsdId', response[0])

    def test_10_3_4_2_5_4(self):
        self._sas.logger.info(
            '10.3.4.2.5.4 Invalid Conditional parameters in Array request '
            '(responseCode 103)')

        device1_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a_singlestep.json')))
        device2_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg2_a_singlestep.json')))
        device3_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg3_a_singlestep.json')))

        # Register
        device3_a['airInterface']['radioTechnology'] = 10000
        devices = [device1_a, device2_a, device3_a]
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[1]['response']['responseCode'], 0)
        self.assertEqual(response[2]['response']['responseCode'], 103)
        self.assertIn('cbsdId', response[0])
        self.assertIn('cbsdId', response[1])
        self.assertNotIn('cbsdId', response[2])

    def test_10_3_4_2_6(self):
        self._sas.logger.info(
            '10.3.4.2.6 Revoked CBSD (responseCode 101)')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a_singlestep.json')))

        # Register
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)

        # Manually revoke the herein used cbsdId
        #
        # Simulate CBSD power-cycle; do not send deregistration and send
        #   registration again
        #   re-registration is 2nd registration
        time.sleep(1)

        # 2nd Registration (re-registration)
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 101)
        self.assertNotIn('cbsdId', response[0])

    def test_10_3_4_2_7(self):
        self._sas.logger.info(
            '10.3.4.2.7 Revoked CBSD in Array request (responseCode 101)')

        device1_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a_singlestep.json')))
        device2_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg2_a_singlestep.json')))
        device3_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg3_a_singlestep.json')))

        # Register
        devices = [device1_a, device2_a, device3_a]
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[1]['response']['responseCode'], 0)
        self.assertEqual(response[2]['response']['responseCode'], 0)

        # Manually revoke the herein used 3rd cbsdId
        #
        # Simulate CBSD power-cycle; do not send deregistration and send
        #   registration again
        #   re-registration is 2nd registration
        time.sleep(1)

        # 2nd Registration (re-registration)
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[1]['response']['responseCode'], 0)
        self.assertEqual(response[2]['response']['responseCode'], 101)
        self.assertIn('cbsdId', response[0])
        self.assertIn('cbsdId', response[1])
        self.assertNotIn('cbsdId', response[2])

    def test_10_3_4_2_8(self):
        self._sas.logger.info(
            '10.3.4.2.8 Unsupported SAS protocol version (responseCode 100)')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a_singlestep.json')))

        # Register
        self._sas.SetVersionNumber('v10.0')
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 100)
        self.assertNotIn('cbsdId', response[0])

    def test_10_3_4_2_9(self):
        self._sas.logger.info(
            '10.3.4.2.9 Unsupported SAS protocol version in Array request '
            '(responseCode 100)')

        device1_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a_singlestep.json')))
        device2_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg2_a_singlestep.json')))
        device3_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg3_a_singlestep.json')))

        # Register
        self._sas.SetVersionNumber('v10.0')
        devices = [device1_a, device2_a, device3_a]
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 100)
        self.assertEqual(response[1]['response']['responseCode'], 100)
        self.assertEqual(response[2]['response']['responseCode'], 100)
        self.assertNotIn('cbsdId', response[0])
        self.assertNotIn('cbsdId', response[1])
        self.assertNotIn('cbsdId', response[2])

    def test_10_3_4_2_10(self):
        self._sas.logger.info(
            '10.3.4.2.10 Group Error (responseCode 201)')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a_singlestep.json')))

        # Register
        devices['groupingParam'] = [
            {"groupType": "interference-coordination",
             "groupId": "some-group-id"}]
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertIn(response[0]['response']['responseCode'], (103, 201))
        self.assertNotIn('cbsdId', response[0])

    def test_10_3_4_2_11(self):
        self._sas.logger.info(
            '10_3.4.2.11 Group Error in Array request (responseCode 201)')

        device1_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a_singlestep.json')))
        device2_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg2_a_singlestep.json')))
        device3_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg3_a_singlestep.json')))

        # Register
        device3_a['groupingParam'] = [
            {"groupType": "interference-coordination",
             "groupId": "some-group-id"}]
        devices = [device1_a, device2_a, device3_a]
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[1]['response']['responseCode'], 0)
        self.assertIn(response[2]['response']['responseCode'], (103, 201))
        self.assertIn('cbsdId', response[0])
        self.assertIn('cbsdId', response[1])
        self.assertNotIn('cbsdId', response[2])

    def test_10_3_4_2_12_1(self):
        self._sas.logger.info(
            '10.3.4.2.12.1 CBSD CAT A attempts to register with HAAT >6m, '
            'Category Error (responseCode 202)')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a_singlestep.json')))

        # Register
        devices['installationParam']['latitude'] = 38.8821619
        devices['installationParam']['longitude'] = -77.1159437
        devices['installationParam']['height'] = 8
        devices['installationParam']['indoorDeployment'] = False
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 202)
        self.assertNotIn('cbsdId', response[0])

    def test_10_3_4_2_12_2(self):
        self._sas.logger.info(
            '10.3.4.2.12.2 CBSD CAT A attempts to register with '
            'eirpCapability > 30 dBm/10MHz')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a_singlestep.json')))

        # Register
        devices['installationParam']['eirpCapability'] = 50
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 202)
        self.assertNotIn('cbsdId', response[0])

    def test_10_3_4_2_12_3(self):
        self._sas.logger.info(
            '10.3.4.2.12.3 CBSD CAT B attempts to register with '
            'eirpCapability > 47 dBm/10MHz',
            'TC_10_3_4_2_12_3_REGISTER_SEND',
            'TC_10_3_4_2_12_3_REGISTER_EXPECT')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_b_singlestep.json')))

        # Register
        devices['installationParam']['eirpCapability'] = 50
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 202)
        self.assertNotIn('cbsdId', response[0])

    def test_10_3_4_2_12_4(self):
        self._sas.logger.info(
            '10.3.4.2.12.4 CBSD CAT B attempts a Single-step registration')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_b_singlestep.json')))

        # Register
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 202)
        self.assertNotIn('cbsdId', response[0])

    def test_10_3_4_2_13(self):
        self._sas.logger.info(
            '10.3.4.2.13 Category Error in Array request (responseCode 202)')

        device1_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_a_singlestep.json')))

        device2_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg2_a_singlestep.json')))
        device2_a['installationParam']['latitude'] = 38.882161
        device2_a['installationParam']['longitude'] = -77.115943
        device2_a['installationParam']['height'] = 8
        device2_a['installationParam']['indoorDeployment'] = False

        device3_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg3_a_singlestep.json')))
        device3_a['installationParam']['eirpCapability'] = 50

        device1_b = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg1_b_singlestep.json')))
        device1_b['installationParam']['eirpCapability'] = 50

        device2_b = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests',
                'testdata', 'registration', 'reg2_b_singlestep.json')))

        # Register
        devices = [device1_a, device2_a, device3_a, device1_b, device2_b]
        response = self._sas.Registration(devices)

        # Check registration response
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[1]['response']['responseCode'], 203)
        self.assertEqual(response[2]['response']['responseCode'], 203)
        self.assertIn(response[3]['response']['responseCode'], (103, 203))
        self.assertEqual(response[4]['response']['responseCode'], 203)
        self.assertIn('cbsdId', response[0])
        self.assertNotIn('cbsdId', response[1])
        self.assertNotIn('cbsdId', response[2])
        self.assertNotIn('cbsdId', response[3])
        self.assertNotIn('cbsdId', response[4])


if __name__ == '__main__':
    unittest.main()
