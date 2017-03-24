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
from util import winnforum_testcase


class RegistrationTestcase(unittest.TestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @winnforum_testcase
  def test_WINFF_FT_S_REG_1(self):
    """New Multi-Step registration for CBSD Cat A (No existing CBSD ID).

    The response should be SUCCESS.
    """

    # Pre-load conditional parameters
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    conditionals = {'registrationData': [
        {'cbsdCategory': 'A',
         'fccId': device_a['fccId'],
         'cbsdSerialNumber': device_a['cbsdSerialNumber'],
         'airInterface': device_a['airInterface'], 
         'installationParam': device_a['installationParam']}
    ]}
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.PreloadRegistrationData(conditionals)
    # Register the device
    del device_a['cbsdCategory']
    del device_a['airInterface']
    del device_a['installationParam']
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    
    # Check registration response
    self.assertTrue('cbsdId' in response)
    self.assertFalse('measReportConfig' in response)
    self.assertEqual(response['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINFF_FT_S_REG_2(self):
    """New Multi-Step registration for CBSD Cat B (No existing CBSD ID).

    The response should be SUCCESS.
    """

    # Pre-load conditional parameters
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    conditionals = {'registrationData': [
        {'cbsdCategory': 'B', 'fccId': device_b['fccId'],
         'cbsdSerialNumber': device_b['cbsdSerialNumber'],
         'airInterface': device_b['airInterface'], 
         'installationParam': device_b['installationParam']}
    ]}
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    self._sas_admin.PreloadRegistrationData(conditionals)
    # Register the device
    del device_b['cbsdCategory']
    del device_b['airInterface']
    del device_b['installationParam']
    request = {'registrationRequest': [device_b]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertTrue('cbsdId' in response)
    self.assertFalse('measReportConfig' in response)
    self.assertEqual(response['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINFF_FT_S_REG_6(self):
    """ Single-Step registration (Cat A CBSD with no existing CBSD ID)

    The response should be SUCCESS.
    """

    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a['measCapability'] = []
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertTrue('cbsdId' in response)
    self.assertFalse('measReportConfig' in response)
    self.assertEqual(response['response']['responseCode'], 0)

  @winnforum_testcase
  def test_10_3_4_2_1(self):
    """CBSD registration request with missing required parameter.

    The required parameter 'userId' is missing in a registration request,
    the response should be FAIL.
    """

    # Register the device, make sure at least one required parameter is missing
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    del device_a['userId']
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 102)

  @winnforum_testcase
  def test_WINFF_FT_S_REG_12(self):
    """Pending registration for Cat A CBSD (responseCode 200)

    The response should be FAILURE.
    """

    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    # Make sure one conditional parameter is missing
    del device_a['installationParam']['heightType']
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertFalse('cbsdId' in response)
    self.assertEqual(response['response']['responseCode'], 200)
    
  @winnforum_testcase
  def test_10_3_4_2_5_1(self):
    """CBSD registration request with invalid required parameter.

    The value of required parameter 'fccId' is invalid(exceeds its max
    length) in the registration request, the response should be FAIL.
    """

    # Register the device, make sure at least one required parameter is invalid
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    device_a['fccId'] = 'abcdefghijklmnopqrstuvwxyz'
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertFalse('cbsdId' in response)
    self.assertEqual(response['response']['responseCode'], 103)

  @winnforum_testcase
  def test_10_3_4_2_5_3(self):
    """CBSD registration request with invalid conditional parameter.

    The value of conditional parameter 'radioTechnology' of airInterface
    object is invalid in the registration request, the response should be FAIL.
    """
    # Register the device, make sure at least one conditional parameter is
    # invalid
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    device_a['airInterface']['radioTechnology'] = 'invalid value'
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertFalse('cbsdId' in response)
    self.assertEqual(response['response']['responseCode'], 103)

@winnforum_testcase
  def test_WINFF_FT_S_REG_23(self):
    """CBSD Cat A attempts to register with HAAT >6m

    The response should be FAILURE.
    """

    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    device_a['installationParam']['latitude'] = 38.882162
    device_a['installationParam']['longitude'] = 77.113755
    device_a['installationParam']['height'] = 8
    device_a['installationParam']['heightType'] = 'AGL'
    device_a['installationParam']['indoorDeployment'] = False
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 202)
    self.assertTrue('cbsdId' in response)

  @winnforum_testcase
  def test_WINFF_FT_S_REG_24(self):
    """CBSD Cat A attempts to register with eirpCapability > 30 dBm/10MHz

    The response should be FAILURE.
    """

    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    device_a['installationParam']['eirpCapability'] = 31
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 202)
    self.assertTrue('cbsdId' in response)

  @winnforum_testcase
  def test_WINFF_FT_S_REG_25(self):
    """CBSD Cat B attempts to register as Indoors deployment

    The response should be FAILURE.
    """

    # Register the device
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    device_b['installationParam']['indoorDeployment'] = True
    request = {'registrationRequest': [device_b]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 202)
    self.assertTrue('cbsdId' in response)

  @winnforum_testcase
  def test_WINFF_FT_S_REG_26(self):
    """Category Error in Array request (responseCode 202)

    The response should be SUCCESS for the first CBSD,
    CATEGORY_ERROR for the second, third, and fourth CBSDs.
    """

    device_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_3 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    device_4 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Device A category A
    self.assertEqual(device_1['cbsdCategory'], 'A')
    
    # Device 2 category A
    device_2['installationParam']['latitude'] = 38.882162
    device_2['installationParam']['longitude'] = 77.113755
    device_2['installationParam']['height'] = 8
    device_2['installationParam']['heightType'] = 'AGL'
    device_2['installationParam']['indoorDeployment'] = False
    self.assertEqual(device_2['cbsdCategory'], 'A')

    # Device 3 category A eirpCapability > 30 dBm/10MHz
    device_3['installationParam']['eirpCapability'] = 31
    self.assertEqual(device_3['cbsdCategory'], 'A')

    # Device 4 category B indoorDeployment true
    device_4['installationParam']['indoorDeployment'] = True
    self.assertEqual(device_4['cbsdCategory'], 'B')

    # Pre-load conditionals for Device 4
    conditionals_4 = {'registrationData': [
        {'cbsdCategory': device_4['cbsdCategory'], 
         'fccId': device_4['fccId'],
         'cbsdSerialNumber': device_4['cbsdSerialNumber'],
         'airInterface': device_4['airInterface'], 
         'installationParam': device_4['installationParam']}
    ]}
    self._sas_admin.PreloadRegistrationData([conditionals_4])

    # Inject FCC IDs
    self._sas_admin.InjectFccId({'fccId': device_1['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_2['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_3['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_4['fccId']})
    devices = [device_1, device_2, device_3, device_4]
    request = {'registrationRequest': devices}
    # Register devices
    response = self._sas.Registration(request)

    # First device success
    self.assertTrue('cbsdId' in response['registrationResponse'][0])
    self.assertFalse('measReportConfig' in response['registrationResponse'][0])
    self.assertEqual(response['registrationResponse'][0]['response']['responseCode'], 0)

    # Second, third, fourth devices failure 202
    for x in range (1,4):
        self.assertEqual(response['registrationResponse'][x]['response']['responseCode'], 202)
