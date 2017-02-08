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

import sas


class RegistrationTestcase(unittest.TestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def test_10_3_4_1_1_1(self):
    """New Multi-Step registration for CBSD Cat A (No existing CBSD ID).

    The response should be SUCCESS.
    """

    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)

  def test_10_3_4_2_1(self):
    """CBSD registration request with missing required parameter.

    The required parameter 'userId' is missing in a registration request,
    the response should be FAIL.
    """

    # Register the device, make sure at least one required parameter is missing
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    del device_a['userId']
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 102)

  def test_10_3_4_2_5_1(self):
    """CBSD registration request with invalid required parameter.

    The value of required parameter 'fccId' is invalid(exceeds its max
    length) in the registration request, the response should be FAIL.
    """

    # Register the device, make sure at least one required parameter is invalid
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a['fccId'] = 'abcdefghijklmnopqrstuvwxyz'
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertFalse('cbsdId' in response)
    self.assertEqual(response['response']['responseCode'], 103)

  def test_10_3_4_2_5_3(self):
    """CBSD registration request with invalid conditional parameter.

    The value of conditional parameter 'radioTechnology' of airInterface
    object is invalid in the registration request, the response should be FAIL.
    """
    # Register the device, make sure at least one conditional parameter is
    # invalid
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a['airInterface']['radioTechnology'] = 'invalid value'
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertFalse('cbsdId' in response)
    self.assertEqual(response['response']['responseCode'], 103)
