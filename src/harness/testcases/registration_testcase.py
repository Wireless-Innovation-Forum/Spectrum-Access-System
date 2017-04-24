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
    conditionals_a = {
        'cbsdCategory': 'A',
        'fccId': device_a['fccId'],
        'cbsdSerialNumber': device_a['cbsdSerialNumber'],
        'airInterface': device_a['airInterface'], 
        'installationParam': device_a['installationParam']}
    conditionals = {'registrationData': [conditionals_a]}
    self._sas_admin.PreloadRegistrationData(conditionals)
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
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
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    conditionals_b = {
        'cbsdCategory': 'B', 'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'], 
        'installationParam': device_b['installationParam']}
    conditionals = {'registrationData': [conditionals_b]}
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
    conditionals_a = {
        'cbsdCategory': device_a['cbsdCategory'], 
        'fccId': device_a['fccId'],
        'cbsdSerialNumber': device_a['cbsdSerialNumber'],
        'airInterface': device_a['airInterface'], 
        'installationParam': device_a['installationParam']}
    conditionals_b = {
        'cbsdCategory': device_b['cbsdCategory'],
        'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'], 
        'installationParam': device_b['installationParam']}
    conditionals_c = {
        'cbsdCategory': device_c['cbsdCategory'], 
        'fccId': device_c['fccId'],
        'cbsdSerialNumber': device_c['cbsdSerialNumber'],
        'airInterface': device_c['airInterface'], 
        'installationParam': device_c['installationParam']}
    conditionals = {'registrationData': [conditionals_a, conditionals_b, conditionals_c]};
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
  def test_WINNF_FT_S_REG_4(self):
    """Re-registration of Multi-step-registered CBSD (CBSD ID exists)
    The response should be SUCCESS.
    """

    # Pre-load conditional parameters
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    conditionals_b = {
        'cbsdCategory': device_b['cbsdCategory'], 
        'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'], 
        'installationParam': device_b['installationParam']}
    conditionals = {'registrationData': [conditionals_b]}
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

  @winnforum_testcase
  def test_WINNF_FT_S_REG_5(self):
    """Array Re-registration of Multi-step-registered CBSD (CBSD ID exists)
    The response should be SUCCESS.
    """

    # Pre-load conditional parameters
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    conditionals_a = {
        'cbsdCategory': device_a['cbsdCategory'], 
        'fccId': device_a['fccId'],
        'cbsdSerialNumber': device_a['cbsdSerialNumber'],
        'airInterface': device_a['airInterface'], 
        'installationParam': device_a['installationParam']}
    conditionals_b = {
        'cbsdCategory': device_b['cbsdCategory'],
        'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'], 
        'installationParam': device_b['installationParam']}
    conditionals_c = {
        'cbsdCategory': device_c['cbsdCategory'], 
        'fccId': device_c['fccId'],
        'cbsdSerialNumber': device_c['cbsdSerialNumber'],
        'airInterface': device_c['airInterface'], 
        'installationParam': device_c['installationParam']}
    conditionals = {'registrationData': [conditionals_a, conditionals_b, conditionals_c]};
    self._sas_admin.PreloadRegistrationData(conditionals)

    # Inject FCC IDs for first two devices
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})

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
    devices = [device_a, device_b]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)
    # Check registration response
    for x in range(0, 2):
        self.assertTrue('cbsdId' in response['registrationResponse'][x])
        self.assertFalse('measReportConfig' in response['registrationResponse'][x])
        self.assertEqual(response['registrationResponse'][x]['response']['responseCode'], 0)
    
    del request, response, devices

    # Register the devices
    devices = [device_a, device_b, device_c]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)
    
    # Check registration response
    for x in range(0, 3):
        self.assertTrue('cbsdId' in response['registrationResponse'][x])
        self.assertFalse('measReportConfig' in response['registrationResponse'][x])
        self.assertEqual(response['registrationResponse'][x]['response']['responseCode'], 0)

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
  def test_WINNF_FT_S_REG_7(self):
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

  @winnforum_testcase
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
    self.assertFalse('cbsdId' in response)
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
    conditionals_a = {
        'cbsdCategory': device_a['cbsdCategory'], 
        'fccId': device_a['fccId'],
        'cbsdSerialNumber': device_a['cbsdSerialNumber'],
        'airInterface': device_a['airInterface'], 
        'installationParam': device_a['installationParam']}
    conditionals_b = {
        'cbsdCategory': device_b['cbsdCategory'], 
        'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'], 
        'installationParam': device_b['installationParam']}
    conditionals_c = {
        'cbsdCategory': device_c['cbsdCategory'], 
        'fccId': device_c['fccId'],
        'cbsdSerialNumber': device_c['cbsdSerialNumber'],
        'airInterface': device_c['airInterface'], 
        'installationParam': device_c['installationParam']}
    conditionals_d = {
        'cbsdCategory': device_d['cbsdCategory'], 
        'fccId': device_d['fccId'],
        'cbsdSerialNumber': device_d['cbsdSerialNumber'],
        'airInterface': device_d['airInterface'], 
        'installationParam': device_d['installationParam']}
    conditionals = {'registrationData': [
        conditionals_a, conditionals_b, conditionals_c, conditionals_d]};
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

    The response should be FAILURE 200.
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
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertFalse('cbsdId' in response)
    self.assertEqual(response['response']['responseCode'], 200)

  @winnforum_testcase
  def test_WINNF_FT_S_REG_13(self):
    """Pending registration for Cat B CBSD (responseCode 200)

    The response should be FAILURE 200.
    """

    # Register the device
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    self.assertEqual(device_b['cbsdCategory'], 'B')
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    # Make sure one conditional parameter is missing
    del device_b['installationParam']['antennaDowntilt']
    request = {'registrationRequest': [device_b]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertFalse('cbsdId' in response)
    self.assertEqual(response['response']['responseCode'], 200)

  @winnforum_testcase
  def test_WINNF_FT_S_REG_14(self):
    """Pending registration in Array request (responseCode 200)
    The response should be FAILURE.
    """

    # Register the devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_d = json.load(
        open(os.path.join('testcases', 'testdata', 'device_d.json')))

    # Device #1 is Category A
    self.assertTrue(device_a['cbsdCategory'], 'A')

    # Device #2 is Category A with one conditional parameter missing
    self.assertTrue(device_c['cbsdCategory'], 'A')
    del device_c['installationParam']['indoorDeployment']

    # Device #3 is Category B
    self.assertTrue(device_b['cbsdCategory'], 'B')

    # Device #4 is Category B with one conditional missing and conditionals pre-loaded
    self.assertTrue(device_d['cbsdCategory'], 'B')
    conditionals_d = {
        'cbsdCategory': device_d['cbsdCategory'],
        'fccId': device_d['fccId'],
        'cbsdSerialNumber': device_d['cbsdSerialNumber'],
        'airInterface': device_d['airInterface'],
        'installationParam': device_d['installationParam']}
    del conditionals_d['installationParam']['antennaBeamwidth']
    conditionals = {'registrationData': [conditionals_d]}
    self._sas_admin.PreloadRegistrationData(conditionals)

    # Inject FCC ID's
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_d['fccId']})

    device_a['measCapability'] = []
    device_c['measCapability'] = []
    device_b['measCapability'] = []
    device_d['measCapability'] = []

    # Register devices
    devices = [device_a, device_c, device_b, device_d]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)
    # Check registration response
    self.assertTrue('cbsdId' in response['registrationResponse'][0])
    for resp in response['registrationResponse']:
        self.assertFalse('measReportConfig' in resp)
    self.assertEqual(response['registrationResponse'][0]['response']['responseCode'], 0)
    for resp in response['registrationResponse'][1:]:
        self.assertEqual(resp['response']['responseCode'], 200)

  @winnforum_testcase
  def test_WINNF_FT_S_REG_15(self):
    """Invalid parameters in Array request (responseCode 103)

    The response should be SUCCESS for the first device,
    FAIL for the second, third, fourth, fifth, and sixth devices.
    """

    # Load the devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    device_f = json.load(
        open(os.path.join('testcases', 'testdata', 'device_f.json')))
    device_g = json.load(
        open(os.path.join('testcases', 'testdata', 'device_g.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    devices = [device_a, device_c, device_e, device_f, device_g, device_b]

    for device in devices:
        # meascapability has no value for all devices
        device['measCapability'] = []
        # Inject FCC IDs
        self._sas_admin.InjectFccId({'fccId': device['fccId']})

    # Device 1 Cat A
    self.assertEqual(device_a['cbsdCategory'], 'A')

    # Device 2 Cat A invalid cbsdSerialNumber - above max length of 64 octets
    self.assertEqual(device_c['cbsdCategory'], 'A')
    device_c['cbsdSerialNumber'] = 'a' * 65

    # Device 3 Cat A invalid fccId - above max length of 19 chars
    self.assertEqual(device_e['cbsdCategory'], 'A')
    device_e['fccId'] = 'a' * 20

    # Device 4 Cat A invalid userId - invalid char (RFC-7542 Section 2.2)
    self.assertEqual(device_f['cbsdCategory'], 'A')
    device_f['userId'] = '@'

    # Device 5 Cat A invalid latitude - invalid type
    self.assertEqual(device_g['cbsdCategory'], 'A')
    device_g['installationParam']['latitude'] = 91

    # Device 6 Cat B
    self.assertEqual(device_b['cbsdCategory'], 'B')
    device_b['installationParam']['eirpCapability'] = 48

    # Pre-load conditionals for Device 6
    conditionals_b = {
        'cbsdCategory': device_b['cbsdCategory'],
        'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'],
        'installationParam': device_b['installationParam']}
    conditionals = {'registrationData': [conditionals_b]}
    self._sas_admin.PreloadRegistrationData(conditionals)

    # Register devices
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)
    # Check registration response
    self.assertTrue('cbsdId' in response['registrationResponse'][0])
    self.assertEqual(response['registrationResponse'][0]['response']['responseCode'], 0)
    for resp in response['registrationResponse']:
        self.assertFalse('measReportConfig' in resp)
    for resp in response['registrationResponse'][1:]:
        self.assertEqual(resp['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINNF_FT_S_REG_16(self):
    """Invalid Conditional parameters in Array request (responseCode 103)

    The response should be SUCCESS for the first CBSD,
    FAILURE 103 for the second and third CBSDs.
    """

    # Load devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))

    # Inject FCC IDs
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_e['fccId']})

    # Device 1 Cat A all valid conditionals
    self.assertEqual(device_a['cbsdCategory'], 'A')
    conditionals_a = {
        'cbsdCategory': device_a['cbsdCategory'],
        'fccId': device_a['fccId'],
        'cbsdSerialNumber': device_a['cbsdSerialNumber'],
        'airInterface': device_a['airInterface'],
        'installationParam': device_a['installationParam']}

    # Device 2 Cat A out-of-range or the wrong type azimuth
    self.assertEqual(device_c['cbsdCategory'], 'A')
    conditionals_c = {
        'cbsdCategory': device_c['cbsdCategory'],
        'fccId': device_c['fccId'],
        'cbsdSerialNumber': device_c['cbsdSerialNumber'],
        'airInterface': device_c['airInterface'],
        'installationParam': device_c['installationParam']}
    conditionals_c['installationParam']['antennaAzimuth'] = -1

    # Device 3 Cat A out-of-range, or the wrong Type value for latitude.
    self.assertEqual(device_e['cbsdCategory'], 'A')
    conditionals_e = {
        'cbsdCategory': device_e['cbsdCategory'],
        'fccId': device_e['fccId'],
        'cbsdSerialNumber': device_e['cbsdSerialNumber'],
        'airInterface': device_e['airInterface'],
        'installationParam': device_e['installationParam']}
    conditionals_e['installationParam']['latitude'] = '91'

    conditionals = {'registrationData': [conditionals_a, conditionals_c, conditionals_e]};
    self._sas_admin.PreloadRegistrationData(conditionals)

    # Remove conditionals from registration
    devices = [device_a, device_c, device_e]
    for device in devices:
        del device['cbsdCategory']
        del device['airInterface']
        del device['installationParam']

    # Register the devices
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)
    # Check registration response
    self.assertTrue('cbsdId' in response['registrationResponse'][0])
    for resp in response['registrationResponse']:
        self.assertFalse('measReportConfig' in resp)
    self.assertEqual(response['registrationResponse'][0]['response']['responseCode'], 0)
    for resp in response['registrationResponse'][1:]:
        self.assertEqual(resp['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINNF_FT_S_REG_17(self):
    """Blacklisted CBSD (responseCode 101)
    
    The response should be FAILURE 101.
    """

    # Register device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    # Register the device
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertTrue('cbsdId' in response)
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Blacklist the device
    self._sas_admin.BlacklistByFccId({'fccId':device_a['fccId']})

    # Re-register the device
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]

    # Check registration response
    self.assertFalse('cbsdId' in response)
    self.assertEqual(response['response']['responseCode'], 101)

  @winnforum_testcase
  def test_WINNF_FT_S_REG_18(self):
    """Blacklisted CBSD in Array request (responseCode 101)
    
    The response should be FAILURE 101.
    """

    # Register the devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    devices = [device_a, device_b, device_c]
    for device in devices:
        self._sas_admin.InjectFccId({'fccId': device['fccId']})
        device['measCapability'] = []
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    for resp in response:
        self.assertTrue('cbsdId' in resp)
        self.assertEqual(resp['response']['responseCode'], 0)
    del request, response

    # Blacklist the third device
    self._sas_admin.BlacklistByFccId({'fccId':device_c['fccId']})

    # Re-register the devices
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)['registrationResponse']

    # Check registration response
    self.assertEqual(len(response), len(devices))
    for response_num, resp in enumerate(response[:2]):
        self.assertEqual(resp['response']['responseCode'], 0)
        self.assertTrue('cbsdId' in resp)
        self.assertFalse('measReportConfig' in resp)
    self.assertFalse('measReportConfig' in response[2])
    self.assertEqual(response[2]['response']['responseCode'], 101)

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
  def test_WINNF_FT_S_REG_20(self):
    """Unsupported SAS protocol version in Array request (responseCode 100)
    The response should be FAILURE 100.
    """

    # Save sas version
    version = self._sas._sas_version
    # Use higher than supported version
    self._sas._sas_version = 'v2.0'

    # Register the devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    devices = [device_a, device_b, device_c]
    for device in devices:
        self._sas_admin.InjectFccId({'fccId': device['fccId']})
    request = {'registrationRequest': devices}
    try:
        response = self._sas.Registration(request)
        # Check response
        for resp in response['registrationResponse']:
            self.assertEqual(resp['response']['responseCode'], 100)
            self.assertFalse('cbsdId' in resp)
    except AssertionError as e:
        # Allow HTTP status 404
        self.assertEqual(e.args[0], 404)
    finally:
        # Put sas version back
        self._sas._sas_version = version

  @winnforum_testcase
  def test_WINNF_FT_S_REG_21(self):
    """Group Error (responseCode 201)
    The response should be FAILURE
    """

    # Load device
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))

    # Create invalid group - only 'INTERFERENCE_COORDINATION' allowed
    device_a['groupingParam'] = [
        {'groupType': 'FAKE_GROUP_TYPE',
         'groupId': '1234'}
    ]

    # Inject FCC ID
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})

    # Register device
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check response
    self.assertTrue(response['response']['responseCode'] in (103, 201))
    self.assertFalse('cbsdId' in response)

  @winnforum_testcase
  def test_WINNF_FT_S_REG_22(self):
    """Group Error in Array request (responseCode 201)
    The response should be SUCCESS for the first two devices,
    FAILURE for the third device.
    """

    # Register the devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))

    # Device #3 invalid group - only 'INTERFERENCE_COORDINATION' allowed
    device_c['groupingParam'] = [
        {'groupType': 'FAKE_GROUP_TYPE',
         'groupId': '1234'}
    ]

    # Inject FCC IDs
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})

    # Register devices
    devices = [device_a, device_b, device_c]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)

    # Check response
    for resp in response['registrationResponse'][:2]:
        self.assertEqual(resp['response']['responseCode'], 0)
        self.assertTrue('cbsdId' in resp)
    self.assertTrue(response['registrationResponse'][2]['response']['responseCode'] in (103, 201))

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
    conditionals_4 = {
        'cbsdCategory': device_4['cbsdCategory'], 
        'fccId': device_4['fccId'],
        'cbsdSerialNumber': device_4['cbsdSerialNumber'],
        'airInterface': device_4['airInterface'], 
        'installationParam': device_4['installationParam']}
    conditionals = {'registrationData': [conditionals_4]}
    self._sas_admin.PreloadRegistrationData(conditionals)

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
