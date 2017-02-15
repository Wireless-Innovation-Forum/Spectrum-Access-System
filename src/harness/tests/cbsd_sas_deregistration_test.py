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
import json
import os
import unittest
import cbsd_sas as sas


class TestDeregistration(unittest.TestCase):
    """ CBSD - SAS Deregistration Test Suite """

    def setUp(self):
        self._sas, self._sas_admin = sas.GetTestingSas()
        # self._sas_admin.Reset()

    def tearDown(self):
        pass

    # Test Cases

    def test_10_15_4_1_1(self):
        self._sas._logger.info(
            '10.15.4.1.1 Valid and correct CBSD ID : single '
            'deregistrationRequest object')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'regA.json')))

        # Register
        response = self._sas.Registration(devices)
        self.assertEqual(response[0]['response']['responseCode'], 0)

        # Deregistration
        regResponse = response
        response = self._sas.Deregistration(
            {'cbsdId': regResponse[0]['cbsdId']})
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[0]['cbsdId'], regResponse[0]['cbsdId'])

    def test_10_15_4_1_2(self):
        self._sas._logger.info(
            '10.15.4.1.2 Valid and correct CBSD ID : '
            'two deregistrationRequest objects')

        device1_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'regA.json')))

        device2_a = device1_a
        device2_a['userId'] = 'Robert Dewey'
        device2_a['fccId'] = 'FCCID_DUMMY__CBSD02'
        device2_a['cbsdSerialNumber'] = 'fed891012'

        # Register
        devices = [device1_a, device2_a]
        response = self._sas.Registration(devices)
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[1]['response']['responseCode'], 0)

        # Deregister
        regResponse = response
        devices = [
            {'cbsdId': regResponse[0]['cbsdId']},
            {'cbsdId': regResponse[1]['cbsdId']}]
        response = self._sas.Deregistration(devices)
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[1]['response']['responseCode'], 0)
        self.assertEqual(response[0]['cbsdId'], regResponse[0]['cbsdId'])
        self.assertEqual(response[1]['cbsdId'], regResponse[1]['cbsdId'])

    def test_10_15_4_2_1(self):
        self._sas._logger.info(
            '10.15.4.2.1 Missing CBSD ID (TBD) : '
            'single object in the DeregistrationRequest')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'regA.json')))

        # Register
        response = self._sas.Registration(devices)
        self.assertEqual(response[0]['response']['responseCode'], 0)

        # Deregistration
        response = self._sas.Deregistration({})
        self.assertEqual(response[0]['response']['responseCode'], 102)
        self.assertNotIn('cbsdId', response[0])

    def test_10_15_4_2_2(self):
        self._sas._logger.info(
            '10.15.4.2.2 Missing CBSD ID (TBD) : '
            'two objects in the DeregistrationRequest')

        device1_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'regA.json')))

        device2_a = device1_a
        device2_a['userId'] = 'Robert Dewey'
        device2_a['fccId'] = 'FCCID_DUMMY__CBSD02'
        device2_a['cbsdSerialNumber'] = 'fed891012'

        # Register
        devices = [device1_a, device2_a]
        response = self._sas.Registration(devices)
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[1]['response']['responseCode'], 0)

        # Deregistration
        regResponse = response
        response = self._sas.Deregistration([
            {'cbsdId': regResponse[0]['cbsdId']},
            {}])
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[0]['cbsdId'], regResponse[0]['cbsdId'])
        self.assertEqual(response[1]['response']['responseCode'], 102)
        self.assertNotIn('cbsdId', response[1])

    def test_10_15_4_3_1(self):
        self._sas._logger.info(
            '10.15.4.3.1 CBSD ID Does Not Exist in the SAS : '
            'single request object')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'regA.json')))

        # Register
        response = self._sas.Registration(devices)
        self.assertEqual(response[0]['response']['responseCode'], 0)

        # Deregistration
        response = self._sas.Deregistration({'cbsdId': 'dummy'})
        self.assertEqual(response[0]['response']['responseCode'], 103)

    def test_10_15_4_3_2(self):
        self._sas._logger.info(
            '10.15.4.3.2 CBSD ID Does Not Exist in the SAS : '
            'two request objects')

        device1_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'regA.json')))

        device2_a = device1_a
        device2_a['userId'] = 'Robert Dewey'
        device2_a['fccId'] = 'FCCID_DUMMY__CBSD02'
        device2_a['cbsdSerialNumber'] = 'fed891012'

        # Register
        devices = [device1_a, device2_a]
        response = self._sas.Registration(devices)
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[1]['response']['responseCode'], 0)

        # Deregistration
        regResponse = response
        response = self._sas.Deregistration([
            {'cbsdId': regResponse[0]['cbsdId']},
            {'cbsdId': 'dummy'}])
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[0]['cbsdId'], regResponse[0]['cbsdId'])
        self.assertEqual(response[1]['response']['responseCode'], 103)
        self.assertNotIn('cbsdId', response[1])

    def test_10_15_4_3_3(self):
        self._sas._logger.info(
            '10.15.4.3.3 CBSD ID initially exists, CBSD deregisters first by '
            'sending Deregistration request. Then sends another '
            'Deregistration request to check that SAS has indeed erased the '
            'CBSD information from its database')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'regA.json')))

        # Register
        response = self._sas.Registration(devices)
        self.assertEqual(response[0]['response']['responseCode'], 0)

        # Deregistration
        regResponse = response
        response = self._sas.Deregistration(
            {'cbsdId': regResponse[0]['cbsdId']})
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[0]['cbsdId'], regResponse[0]['cbsdId'])

        # 2nd Deregistration
        response = self._sas.Deregistration(
            {'cbsdId': regResponse[0]['cbsdId']})
        self.assertEqual(response[0]['response']['responseCode'], 103)
        self.assertNotIn('cbsdId', response[0])

    def test_10_15_4_3_4_1(self):
        self._sas._logger.info(
            '10.15.4.3.4.1 CBSD ID value invalid: single request object')

        devices = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'regA.json')))

        # Register
        response = self._sas.Registration(devices)
        self.assertEqual(response[0]['response']['responseCode'], 0)

        # Deregistration
        response = self._sas.Deregistration({'cbsdId': 1000})
        self.assertEqual(response[0]['response']['responseCode'], 103)
        self.assertNotIn('cbsdId', response[0])

    def test_10_15_4_3_4_2(self):
        self._sas._logger.info(
            '10.15.4.3.4.2 CBSD ID value invalid: two request objects')

        device1_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'regA.json')))

        device2_a = json.load(
            open(os.path.join(
                os.getcwd(),
                'tests', 'testdata', 'registration', 'regA.json')))

        # Register
        devices = [device1_a, device2_a]
        response = self._sas.Registration(devices)
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[1]['response']['responseCode'], 0)

        # Deregistration
        regResponse = response
        response = self._sas.Deregistration([
            {'cbsdId': regResponse[0]['cbsdId']},
            {'cbsdId': 1000}])
        self.assertEqual(response[0]['response']['responseCode'], 0)
        self.assertEqual(response[0]['cbsdId'], regResponse[0]['cbsdId'])
        self.assertEqual(response[1]['response']['responseCode'], 103)
        self.assertNotIn('cbsdId', response[1])
