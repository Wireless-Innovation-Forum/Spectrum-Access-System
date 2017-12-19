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

from datetime import datetime
import json
import os
import sas
import sas_testcase
from util import winnforum_testcase, generateCpiRsaKeys, convertRequestToRequestWithCpiSignature


class RegistrationTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @winnforum_testcase
  def test_WINNF_FT_S_REG_1(self):
    """Array Multi-Step registration for CBSDs (Cat A and B).

    The response should be SUCCESS.
    """

    # Load Devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))

    # Pre-load conditionals
    conditionals_a = {
        'cbsdCategory': device_a['cbsdCategory'],
        'fccId': device_a['fccId'],
        'cbsdSerialNumber': device_a['cbsdSerialNumber'],
        'airInterface': device_a['airInterface'],
        'installationParam': device_a['installationParam'],
        'measCapability': device_a['measCapability']
    }
    conditionals_b = {
        'cbsdCategory': device_b['cbsdCategory'],
        'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'],
        'installationParam': device_b['installationParam'],
        'measCapability': device_b['measCapability']
    }
    conditionals_c = {
        'cbsdCategory': device_c['cbsdCategory'],
        'fccId': device_c['fccId'],
        'cbsdSerialNumber': device_c['cbsdSerialNumber'],
        'airInterface': device_c['airInterface'],
        'installationParam': device_c['installationParam'],
        'measCapability': device_c['measCapability']
    }
    conditionals = {
        'registrationData': [conditionals_a, conditionals_b, conditionals_c]
    }

    # Inject FCC IDs
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_b['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})

    # Inject User IDs
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    self._sas_admin.InjectUserId({'userId': device_b['userId']})
    self._sas_admin.InjectUserId({'userId': device_c['userId']})

    self._sas_admin.PreloadRegistrationData(conditionals)

    # Remove conditionals from registration
    del device_a['cbsdCategory']
    del device_a['airInterface']
    del device_a['installationParam']
    del device_a['measCapability']
    del device_b['cbsdCategory']
    del device_b['airInterface']
    del device_b['installationParam']
    del device_b['measCapability']
    del device_c['cbsdCategory']
    del device_c['airInterface']
    del device_c['installationParam']
    del device_c['measCapability']

    # Register the devices
    devices = [device_a, device_b, device_c]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)
    # Check registration response
    for x in range(0, 3):
      self.assertTrue('cbsdId' in response['registrationResponse'][x])
      self.assertEqual(
          response['registrationResponse'][x]['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINNF_FT_S_REG_2(self):
    """Array Re-registration of multiple CBSDs.

    The response should be SUCCESS for Re-registration.
    """

    # Load devices
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

    # Pre-load conditionals
    conditionals_a = {
        'cbsdCategory': device_a['cbsdCategory'],
        'fccId': device_a['fccId'],
        'cbsdSerialNumber': device_a['cbsdSerialNumber'],
        'airInterface': device_a['airInterface'],
        'installationParam': device_a['installationParam'],
        'measCapability': device_a['measCapability']
    }
    conditionals_c = {
        'cbsdCategory': device_c['cbsdCategory'],
        'fccId': device_c['fccId'],
        'cbsdSerialNumber': device_c['cbsdSerialNumber'],
        'airInterface': device_c['airInterface'],
        'installationParam': device_c['installationParam'],
        'measCapability': device_c['measCapability']
    }
    conditionals_e = {
        'cbsdCategory': device_e['cbsdCategory'],
        'fccId': device_e['fccId'],
        'cbsdSerialNumber': device_e['cbsdSerialNumber'],
        'airInterface': device_e['airInterface'],
        'installationParam': device_e['installationParam'],
        'measCapability': device_e['measCapability']
    }
    conditionals_f = {
        'cbsdCategory': device_f['cbsdCategory'],
        'fccId': device_f['fccId'],
        'cbsdSerialNumber': device_f['cbsdSerialNumber'],
        'airInterface': device_f['airInterface'],
        'installationParam': device_f['installationParam'],
        'measCapability': device_f['measCapability']
    }
    conditionals_g = {
        'cbsdCategory': device_g['cbsdCategory'],
        'fccId': device_g['fccId'],
        'cbsdSerialNumber': device_g['cbsdSerialNumber'],
        'airInterface': device_g['airInterface'],
        'installationParam': device_g['installationParam'],
        'measCapability': device_g['measCapability']
    }
    conditionals = {
        'registrationData': [
            conditionals_a, conditionals_c, conditionals_e, conditionals_f,
            conditionals_g
        ]
    }

    # Inject FCC IDs and User IDs
    for device in [device_a, device_c, device_e, device_f, device_g]:
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})

    self._sas_admin.PreloadRegistrationData(conditionals)

    # Remove conditionals from registration
    for device in [device_a, device_c, device_e, device_f, device_g]:
      del device['cbsdCategory']
      del device['airInterface']
      del device['installationParam']
      del device['measCapability']

    # Register 4 devices.
    devices = [device_a, device_c, device_e, device_f]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response and record cbsdIds
    cbsd_ids = []
    for response_num in range(0, 4):
      self.assertTrue('cbsdId' in response[response_num])
      cbsd_ids.append(response[response_num]['cbsdId'])
      self.assertEqual(response[response_num]['response']['responseCode'], 0)
    del request, response

    # CBSDs C3 and C4 request a grant, exchange heartbeats to enter and stay in
    # Authorized state.
    grant_e = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_f = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_e['cbsdId'] = cbsd_ids[2]
    grant_f['cbsdId'] = cbsd_ids[3]
    request = {'grantRequest': [grant_e, grant_f]}
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), 2)
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[2])
    self.assertEqual(response[1]['cbsdId'], cbsd_ids[3])
    grant_ids = []
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      grant_ids.append(resp['grantId'])
    del request, response

    heartbeat_request = [{
        'cbsdId': cbsd_ids[2],
        'grantId': grant_ids[0],
        'operationState': 'GRANTED'
    }, {
        'cbsdId': cbsd_ids[3],
        'grantId': grant_ids[1],
        'operationState': 'GRANTED'
    }]
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    # Check the heartbeat response
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[2])
    self.assertEqual(response[1]['cbsdId'], cbsd_ids[3])
    for resp_number, resp in enumerate(response):
      self.assertEqual(resp['grantId'], grant_ids[resp_number])
      self.assertEqual(resp['response']['responseCode'], 0)
    del request, response

    # Send Re-registration request as a 5 element array
    devices = [device_a, device_c, device_e, device_f, device_g]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)['registrationResponse']

    # Check Re-registration response
    for response_num in range(0, 5):
      self.assertTrue('cbsdId' in response[response_num])
      self.assertEqual(response[response_num]['response']['responseCode'], 0)
    del request, response

    # CBSDs C3 and C4 send a heartbeat request again.
    heartbeat_request = [{
        'cbsdId': cbsd_ids[2],
        'grantId': grant_ids[0],
        'operationState': 'AUTHORIZED'
    }, {
        'cbsdId': cbsd_ids[3],
        'grantId': grant_ids[1],
        'operationState': 'AUTHORIZED'
    }]
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']

    # Check the heartbeat response
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[2])
    self.assertEqual(response[1]['cbsdId'], cbsd_ids[3])
    for resp in response:
      self.assertTrue(resp['response']['responseCode'] in (103, 500))
      transmit_expire_time = datetime.strptime(resp['transmitExpireTime'],
                                               '%Y-%m-%dT%H:%M:%SZ')
      self.assertLessEqual(transmit_expire_time, datetime.utcnow())

  @winnforum_testcase
  def test_WINNF_FT_S_REG_3(self):
    """Array Single-Step registration for CBSDs (Cat A and B).

    The response should be SUCCESS.
    """

    # Load Devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Inject FCC ID and User ID
    for device in [device_a, device_c, device_b]:
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})

    # (Generate CPI RSA keys and) Load CPI user info
    cpi_id = 'professional_installer_id_1'
    cpi_name = 'a_name'
    cpi_private_key, cpi_public_key = generateCpiRsaKeys()
    self._sas_admin.InjectCpiUser({
        'cpiId': cpi_id,
        'cpiName': cpi_name,
        'cpiPublicKey': cpi_public_key
    })
    # Convert device_b's registration request to embed cpiSignatureData
    convertRequestToRequestWithCpiSignature(cpi_private_key, cpi_id,
                                            cpi_name, device_b)

    # Register the devices
    devices = [device_a, device_c, device_b]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    for x in range(0, 3):
      self.assertTrue('cbsdId' in response[x])
      self.assertEqual(response[x]['response']['responseCode'], 0)

  @winnforum_testcase
  def test_WINNF_FT_S_REG_5(self):
    """Missing Required parameters in Array Registration request.

    The response should be MISSING_PARAM 102.
    """

    # Load Devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    device_f = json.load(
        open(os.path.join('testcases', 'testdata', 'device_f.json')))

    # Pre-load conditionals
    conditionals_a = {
        'cbsdCategory': device_a['cbsdCategory'],
        'fccId': device_a['fccId'],
        'cbsdSerialNumber': device_a['cbsdSerialNumber'],
        'airInterface': device_a['airInterface'],
        'installationParam': device_a['installationParam'],
        'measCapability': device_a['measCapability']
    }
    conditionals_c = {
        'cbsdCategory': device_c['cbsdCategory'],
        'fccId': device_c['fccId'],
        'cbsdSerialNumber': device_c['cbsdSerialNumber'],
        'airInterface': device_c['airInterface'],
        'installationParam': device_c['installationParam'],
        'measCapability': device_c['measCapability']
    }
    conditionals_e = {
        'cbsdCategory': device_e['cbsdCategory'],
        'fccId': device_e['fccId'],
        'cbsdSerialNumber': device_e['cbsdSerialNumber'],
        'airInterface': device_e['airInterface'],
        'installationParam': device_e['installationParam'],
        'measCapability': device_e['measCapability']
    }
    conditionals_f = {
        'cbsdCategory': device_f['cbsdCategory'],
        'fccId': device_f['fccId'],
        'cbsdSerialNumber': device_f['cbsdSerialNumber'],
        'airInterface': device_f['airInterface'],
        'installationParam': device_f['installationParam'],
        'measCapability': device_f['measCapability']
    }
    conditionals = {
        'registrationData': [
            conditionals_a, conditionals_c, conditionals_e, conditionals_f
        ]
    }

    # Inject FCC IDs
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_e['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_f['fccId']})

    # Inject User IDs
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    self._sas_admin.InjectUserId({'userId': device_c['userId']})
    self._sas_admin.InjectUserId({'userId': device_e['userId']})
    self._sas_admin.InjectUserId({'userId': device_f['userId']})

    self._sas_admin.PreloadRegistrationData(conditionals)

    # Remove conditionals from registration
    del device_a['cbsdCategory']
    del device_a['airInterface']
    del device_a['installationParam']
    del device_a['measCapability']
    del device_c['cbsdCategory']
    del device_c['airInterface']
    del device_c['installationParam']
    del device_c['measCapability']
    del device_e['cbsdCategory']
    del device_e['airInterface']
    del device_e['installationParam']
    del device_e['measCapability']
    del device_f['cbsdCategory']
    del device_f['airInterface']
    del device_f['installationParam']
    del device_f['measCapability']

    # Device 2 missing cbsdSerialNumber
    del device_c['cbsdSerialNumber']

    # Device 3 missing fccId
    del device_e['fccId']

    # Device 4 missing userId
    del device_f['userId']

    # Register devices
    devices = [device_a, device_c, device_e, device_f]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)
    # Check registration response
    self.assertTrue('cbsdId' in response['registrationResponse'][0])
    self.assertEqual(
        response['registrationResponse'][0]['response']['responseCode'], 0)
    for x in range(1, 4):
      self.assertEqual(
          response['registrationResponse'][x]['response']['responseCode'], 102)

  @winnforum_testcase
  def test_WINNF_FT_S_REG_7(self):
    """Invalid parameters in Array Registration Request

    The response should be 103.
    """
    
    # Load Devices Data
    device_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_3 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_4 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_4['cbsdSerialNumber'] = 'device_4_serial_number'
    device_5 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_5['cbsdSerialNumber'] = 'device_5_serial_number'
    device_6 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_6['cbsdSerialNumber'] = 'device_6_serial_number'
    device_6['measCapability'] = ['invalid_measCapability']
    device_7 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_8 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    device_8['cbsdSerialNumber'] =  'device_8_serial_number'
    device_9 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_f.json')))
    device_10 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_10['cbsdSerialNumber'] = 'device_10_serial_number'
    device_11 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_11['cbsdSerialNumber'] = 'device_11_serial_number'
    device_12 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_12['cbsdSerialNumber'] = 'device_12_serial_number'
    device_13 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_13['cbsdSerialNumber'] = 'device_13_serial_number'
    device_14 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_14['cbsdSerialNumber'] = 'device_14_serial_number'
    device_15 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_g.json')))
    device_15['cbsdSerialNumber'] =  'device_15_serial_number'    
    device_16 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_16['cbsdSerialNumber'] =  'device_16_serial_number'
    # Devices that contain all necessary Fcc and user data
    devices_with_administrative_data = [device_1, device_2, device_7, device_8,\
                                        device_9, device_15]
    # Inject Fcc Id and User Id for the devices that contain all Fcc and user data data
    for device in devices_with_administrative_data:
        self._sas_admin.InjectFccId({'fccId': device['fccId']})
        self._sas_admin.InjectUserId({'userId': device['userId']})
    # Inject Fcc Id with not default Fcc max Eirp
    self._sas_admin.InjectFccId({'fccId':'fccId_with_approved_eirp',\
                                  'fccMaxEirp': 25})   
    
    # (Generate CPI RSA keys and) Load CPI user info
    cpi_id = 'professional_installer_id_1'
    cpi_name = 'a_name'
    cpi_private_key, cpi_public_key = generateCpiRsaKeys()
    self._sas_admin.InjectCpiUser({
        'cpiId': cpi_id,
        'cpiName': cpi_name,
        'cpiPublicKey': cpi_public_key
    })
    # Pre-load conditionals
    conditionals_12 = {
        'cbsdCategory': device_12['cbsdCategory'],
        'fccId': device_12['fccId'],
        'cbsdSerialNumber': device_12['cbsdSerialNumber'],
        'airInterface': device_12['airInterface'],
        'installationParam': device_12['installationParam'],
        'measCapability': device_12['measCapability']
    }
    conditionals_13 = {
        'cbsdCategory': device_13['cbsdCategory'],
        'fccId': device_13['fccId'],
        'cbsdSerialNumber': device_13['cbsdSerialNumber'],
        'airInterface': device_13['airInterface'],
        'installationParam': device_13['installationParam'],
        'measCapability': device_13['measCapability']
    }
    conditionals_14 = {
        'cbsdCategory': device_14['cbsdCategory'],
        'fccId': device_14['fccId'],
        'cbsdSerialNumber': device_14['cbsdSerialNumber'],
        'airInterface': device_14['airInterface'],
        'installationParam': device_14['installationParam'],
        'measCapability': device_14['measCapability']
    }

    conditionals = {
        'registrationData': [
            conditionals_12, conditionals_13, conditionals_14
        ]
    }
    self._sas_admin.PreloadRegistrationData(conditionals)

    # Remove conditionals from registration
    del device_12['cbsdCategory']
    del device_12['airInterface']
    del device_12['measCapability']
    del device_13['cbsdCategory']
    del device_13['airInterface']
    del device_13['measCapability']
    del device_14['cbsdCategory']
    del device_14['airInterface']
    del device_14['installationParam']
    del device_14['measCapability']
    
    # Modify the configuration of the devices according to the specfications
    # invalid_cbsd serial number with length > 64 octets
    device_2['cbsdSerialNumber'] = 's' * 65
    # invalid_cbsd serial number with length > 20 octets
    device_3['fccId'] = 'f' * 21
    device_4['userId'] = 'invalid_userId_@'
    device_5['installationParam']['latitude'] = 90.01
    device_6['measCapability'] = ['invalid_measCapability']
    device_7['installationParam']['eirpCapability'] = 48
    # Convert device_7's registration request to embed cpiSignatureData
    convertRequestToRequestWithCpiSignature(cpi_private_key, cpi_id,
                                            cpi_name, device_7)
    device_8['installationParam']['latitude'] = 38.882162
    device_8['installationParam']['longitude'] = -77.113755
    device_8['installationParam']['height'] = 4.0
    device_8['installationParam']['heightType'] = 'AGL'
    device_8['installationParam']['indoorDeployment'] = False  
    device_9['installationParam']['eirpCapability'] = 31  
    device_10['installationParam']['indoorDeployment'] = True
    device_10['installationParam']['eirpCapability'] = 31
    # Convert device_10's registration request to embed cpiSignatureData
    convertRequestToRequestWithCpiSignature(cpi_private_key, cpi_id,
                                            cpi_name, device_10)
    installation_param_device_11 = device_11['installationParam']
    # Convert device_11's registration request to embed cpiSignatureData
    convertRequestToRequestWithCpiSignature(cpi_private_key, cpi_id,
                                            cpi_name, device_11)
    # Re-add installationParam to the device 11
    device_11['installationParam'] = installation_param_device_11
    # Convert device_12's' registration request to embed cpiSignatureData
    convertRequestToRequestWithCpiSignature(cpi_private_key,\
                                'Incorrent_installer_id_1', cpi_name, device_12)
    device_13['installationParam']['latitude'] = 38.882162
    device_13['installationParam']['longitude'] = -77.013055
    device_13['installationParam']['height'] = 5.0
    # Convert device_13's' registration request to embed cpiSignatureData    
    convertRequestToRequestWithCpiSignature(cpi_private_key,\
                                cpi_id, cpi_name, device_13)
    
    device_15['fccId'] =  'fccId_with_approved_eirp'
    device_15['installationParam']['eirpCapability'] = 26
    
    device_16['fccId'] =  'fccId_with_approved_eirp'
    device_16['installationParam']['eirpCapability'] = 26
    convertRequestToRequestWithCpiSignature(cpi_private_key,\
                                cpi_id, cpi_name, device_16)  
    # Register devices
    devices = [device_1, device_2, device_3, device_4, device_5, device_6,\
               device_7, device_8, device_9, device_10, device_11, device_12,\
               device_13, device_14, device_15, device_16 ]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)
    # Check registration response
   
    self.assertEqual(
          response['registrationResponse'][0]['response']['responseCode'], 0)
    self.assertEqual(
          response['registrationResponse'][12]['response']['responseCode'], 0)
  for index in range(1, 12) + range(13, 16):
    self.assertEqual(
          response['registrationResponse'][index]['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINNF_FT_S_REG_9(self):
    """Blacklisted CBSD in Array Registration request (responseCode 101).

    The response should be BLACKLISTED 101.
    """

    # Load Devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    devices = [device_a, device_c, device_e]
    for device in devices:
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    for resp in response:
      self.assertTrue('cbsdId' in resp)
      self.assertEqual(resp['response']['responseCode'], 0)
    del request, response

    # Blacklist the third device
    self._sas_admin.BlacklistByFccId({'fccId': device_e['fccId']})

    # Re-register the devices
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)['registrationResponse']

    # Check registration response
    self.assertEqual(len(response), len(devices))
    for resp in response[:2]:
      self.assertEqual(resp['response']['responseCode'], 0)
      self.assertTrue('cbsdId' in resp)
    self.assertEqual(response[2]['response']['responseCode'], 101)

  @winnforum_testcase
  def test_WINNF_FT_S_REG_10(self):
    """Unsupported SAS protocol version in Array request (responseCode 100).

    The response should be FAILURE 100.
    """

    # Use higher than supported version
    self._sas._sas_version = 'v2.0'

    # Load Devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    devices = [device_a, device_c, device_e]
    for device in devices:
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})
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
