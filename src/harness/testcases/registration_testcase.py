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
  def test_WINNF_FT_S_REG_1(self):
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
  def test_WINNF_FT_S_REG_2(self):
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
  def test_WINNF_FT_S_REG_3(self):
    """Array Multi-Step registration for CBSD Cat A&B (No existing CBSD ID)

    The response should be SUCCESS.
    """

    # Pre-load conditional parameters
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    conditionals_a = {'registrationData': [
        {'cbsdCategory': device_a['cbsdCategory'], 
         'fccId': device_a['fccId'],
         'cbsdSerialNumber': device_a['cbsdSerialNumber'],
         'airInterface': device_a['airInterface'], 
         'installationParam': device_a['installationParam']}
    ]}
    conditionals_b = {'registrationData': [
        {'cbsdCategory': device_b['cbsdCategory'],
         'fccId': device_b['fccId'],
         'cbsdSerialNumber': device_b['cbsdSerialNumber'],
         'airInterface': device_b['airInterface'], 
         'installationParam': device_b['installationParam']}
    ]}
    conditionals_c = {'registrationData': [
        {'cbsdCategory': device_c['cbsdCategory'], 
         'fccId': device_c['fccId'],
         'cbsdSerialNumber': device_c['cbsdSerialNumber'],
         'airInterface': device_c['airInterface'], 
         'installationParam': device_c['installationParam']}
    ]}
    conditionals = [conditionals_a, conditionals_b, conditionals_c];
    self._sas_admin.PreloadRegistrationData(conditionals)

    # Inject FCC IDs
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})

    # Remove conditionals from registration
    del device_a['cbsdCategory']
    del device_a['airInterface']
    del device_a['installationParam']
    del device_b['cbsdCategory']
    del device_b['airInterface']
    del device_b['installationParam']
    del device_c['cbsdCategory']
    del device_c['airInterface']
    del device_c['installationParam']

    # Register the devices
    devices = [device_a, device_b, device_c]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)
    # Check registration response
    for x in range (0, 3):
        self.assertTrue('cbsdId' in response['registrationResponse'][x])
        self.assertFalse('measReportConfig' in response['registrationResponse'][x])
        self.assertEqual(response['registrationResponse'][x]['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINFF_FT_S_REG_4(self):
    """Re-registration of Multi-step-registered CBSD (CBSD ID exists)
    The response should be SUCCESS.
    """

    # Pre-load conditional parameters
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    conditionals = {'registrationData': [
        {'cbsdCategory': device_b['cbsdCategory'], 
         'fccId': device_b['fccId'],
         'cbsdSerialNumber': device_b['cbsdSerialNumber'],
         'airInterface': device_b['airInterface'], 
         'installationParam': device_b['installationParam']}
    ]}
    self._sas_admin.PreloadRegistrationData(conditionals)
    
    # Inject FCC ID
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    
    # Remove conditionals from registration
    del device_b['cbsdCategory']
    del device_b['airInterface']
    del device_b['installationParam']
    
    # Register the device
    request = {'registrationRequest': [device_b]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertTrue('cbsdId' in response)
    self.assertFalse('measReportConfig' in response)
    self.assertEqual(response['response']['responseCode'], 0)

    cbsdId = response['cbsdId']
    del request, response

    # Re-register the device
    request = {'registrationRequest': [device_b]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertTrue('cbsdId' in response)
    self.assertFalse('measReportConfig' in response)
    self.assertEqual(response['response']['responseCode'], 0)
    self.assertTrue(cbsdId == response['cbsdId'])

  @winnforum_testcase
  def test_WINNF_FT_S_REG_6(self):
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
  def test_WINFF_FT_S_REG_7(self):
    """ Array Single-Step registration (Cat A CBSD with no existing CBSD ID)
    The response should be SUCCESS.
    """

    # Load the devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    
    # The measCapability contains no value for all array elements
    device_a['measCapability'] = []
    device_c['measCapability'] = []
    device_e['measCapability'] = []
    
    # Inject FCC IDs
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_e['fccId']})
    
    # Register the devices
    devices = [device_a, device_c, device_e]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)
    # Check registration response
    for x in range(0, 3):
        self.assertTrue('cbsdId' in response['registrationResponse'][x])
        self.assertFalse('measReportConfig' in response['registrationResponse'][x])
        self.assertEqual(response['registrationResponse'][x]['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINNF_FT_S_REG_8(self):
    """ Re-registration of Single-step-registered CBSD (CBSD ID exists)

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
    self.assertEqual(response['response']['responseCode'], 0)

    del response

    # Re-register the device
    response = self._sas.Registration(request)['registrationResponse'][0]

    self.assertTrue('cbsdId' in response)
    self.assertFalse('measReportConfig' in response)
    self.assertEqual(response['response']['responseCode'], 0)

  def test_WINNF_FT_S_REG_9(self):
    """ Array Re-registration of Single-step-registered CBSD (CBSD ID exists)

    The response should be SUCCESS.
    """

    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))

    # Inject FCC IDs
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})

    # Make sure measCapability contains no value for all array elements
    device_a['measCapability'] = []
    device_b['measCapability'] = []
    device_c['measCapability'] = []

    # Register two devices
    request = {'registrationRequest': [device_a, device_b]}
    response = self._sas.Registration(request)
    
    # Check registration response
    self.assertEqual(len(response['registrationResponse']), 2)
    for resp in response['registrationResponse']:
        self.assertTrue('cbsdId' in resp)
        self.assertEqual(resp['response']['responseCode'], 0)

    del request, response

    # Re-register two devices, register third device
    devices = [device_a, device_b, device_c]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)

    # Check registration response
    self.assertEqual(len(response['registrationResponse']), len(devices))
    for resp in response['registrationResponse']:
        self.assertTrue('cbsdId' in resp)
        self.assertFalse('measReportConfig' in resp)
        self.assertEqual(resp['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINNF_FT_S_REG_10(self):
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
  def test_WINNF_FT_S_REG_11(self):
    """Missing Required parameters in Array request (responseCode 102)

    The response should be MISSING_PARAM 102.
    """

    # Load devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_d = json.load(
        open(os.path.join('testcases', 'testdata', 'device_d.json')))

    # Inject FCC IDs
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_d['fccId']})

    # Pre-load conditionals
    conditionals_a = {'registrationData': [
        {'cbsdCategory': device_a['cbsdCategory'], 
         'fccId': device_a['fccId'],
         'cbsdSerialNumber': device_a['cbsdSerialNumber'],
         'airInterface': device_a['airInterface'], 
         'installationParam': device_a['installationParam']}
    ]}
    conditionals_b = {'registrationData': [
        {'cbsdCategory': device_b['cbsdCategory'], 
         'fccId': device_b['fccId'],
         'cbsdSerialNumber': device_b['cbsdSerialNumber'],
         'airInterface': device_b['airInterface'], 
         'installationParam': device_b['installationParam']}
    ]}
    conditionals_c = {'registrationData': [
        {'cbsdCategory': device_c['cbsdCategory'], 
         'fccId': device_c['fccId'],
         'cbsdSerialNumber': device_c['cbsdSerialNumber'],
         'airInterface': device_c['airInterface'], 
         'installationParam': device_c['installationParam']}
    ]}
    conditionals_d = {'registrationData': [
        {'cbsdCategory': device_d['cbsdCategory'], 
         'fccId': device_d['fccId'],
         'cbsdSerialNumber': device_d['cbsdSerialNumber'],
         'airInterface': device_d['airInterface'], 
         'installationParam': device_d['installationParam']}
    ]}
    conditionals = [conditionals_a, conditionals_b, conditionals_c, conditionals_d];
    self._sas_admin.PreloadRegistrationData(conditionals)
    
    # Device 2 missing cbsdSerialNumber
    del device_b['cbsdSerialNumber']
    
    # Device 3 missing fccId
    del device_c['fccId']
    
    # Device 4 missing userId
    del device_d['userId']
    
    # Register devices
    devices = [device_a, device_b, device_c, device_d]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)
    # Check registration response
    self.assertTrue('cbsdId' in response['registrationResponse'][0])
    self.assertEqual(response['registrationResponse'][0]['response']['responseCode'], 0)
    for x in range(0, 4):
        self.assertFalse('measReportConfig' in response['registrationResponse'][x])
    for x in range(1, 4):
        self.assertEqual(response['registrationResponse'][x]['response']['responseCode'], 102)

  @winnforum_testcase
  def test_WINNF_FT_S_REG_12(self):
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

    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    device_a['airInterface']['radioTechnology'] = 'invalid value'
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertFalse('cbsdId' in response)
    self.assertEqual(response['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINFF_FT_S_REG_19(self):
    """Unsupported SAS protocol version (responseCode 100 or HTTP status 404)

    The response should be FAILURE.
    """

    # Save sas version
    version = self._sas._sas_version
    # Use higher than supported version
    self._sas._sas_version = 'v2.0'

    # Register the device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    request = {'registrationRequest': [device_a]}
    try:
        # Register
        response = self._sas.Registration(request)['registrationResponse'][0]
        # Check registration response
        self.assertEqual(response['response']['responseCode'], 100)
        self.assertFalse('cbsdId' in response)
    except AssertionError as e:
        # Allow HTTP status 404
        self.assertEqual(e.args[0], 404)
    finally:
        # Put sas version back
        self._sas._sas_version = version

  @winnforum_testcase
  def test_WINNF_FT_S_REG_26(self):
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
