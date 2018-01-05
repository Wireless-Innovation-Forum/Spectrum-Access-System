#    Copyright 2017 SAS Project Authors. All Rights Reserved.
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
import logging
import os
import sas
import sas_testcase
from util import winnforum_testcase, configurable_testcase, writeConfig, \
  loadConfig, generateCpiRsaKeys, convertRequestToRequestWithCpiSignature


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
  def test_WINNF_FT_S_REG_8(self):
    """Invalid REG-Conditional parameters in Array Registration Request (responseCode 103)

    The response should be SUCCESS for the first CBSD,
    FAILURE 103 for the second and third CBSDs.
    """

    # Load devices
    device_1 = json.load(open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_2 = json.load(open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_3 = json.load(open(os.path.join('testcases', 'testdata', 'device_e.json')))

    # Inject FCC IDs
    self._sas_admin.InjectFccId({'fccId': device_1['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_2['fccId']})
    self._sas_admin.InjectFccId({'fccId': device_3['fccId']})

    # Inject User IDs
    self._sas_admin.InjectUserId({'userId': device_1['userId']})
    self._sas_admin.InjectUserId({'userId': device_2['userId']})
    self._sas_admin.InjectUserId({'userId': device_3['userId']})

    # Device 2 out-of-range or the wrong type azimuth
    device_2['installationParam']['antennaAzimuth'] = -1

    # Device 3 out-of-range, or the wrong Type value for latitude.
    device_3['installationParam']['latitude'] = 91.0

    # Register the devices
    request = {'registrationRequest': [device_1, device_2, device_3]}
    response = self._sas.Registration(request)['registrationResponse']

    # Check registration response
    # valid cbsdId and responseCode 0 for 1st cbsd
    self.assertTrue('cbsdId' in response[0])
    self.assertEqual(response[0]['response']['responseCode'], 0)

    # responseCode 103 for 2nd and 3rd cbsd
    self.assertEqual(response[1]['response']['responseCode'], 103)
    self.assertEqual(response[2]['response']['responseCode'], 103)
      
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

  def generate_REG_11_default_config(self, filename):
    """Generates the WinnForum configuration for REG.11."""
    # Load device info
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_d = json.load(
        open(os.path.join('testcases', 'testdata', 'device_d.json')))

    # Device #1 is Category A.
    self.assertEqual(device_a['cbsdCategory'], 'A')

    # Device #2 is Category A with one conditional parameter missing.
    self.assertEqual(device_c['cbsdCategory'], 'A')
    del device_c['installationParam']['indoorDeployment']

    # Device #3 is Category B.
    self.assertEqual(device_b['cbsdCategory'], 'B')

    # Device #4 is Category B with one conditional missing and conditionals
    # pre-loaded.
    self.assertEqual(device_d['cbsdCategory'], 'B')
    conditionals_d = {
        'cbsdCategory': device_d['cbsdCategory'],
        'fccId': device_d['fccId'],
        'cbsdSerialNumber': device_d['cbsdSerialNumber'],
        'airInterface': device_d['airInterface'],
        'installationParam': device_d['installationParam']
    }
    del conditionals_d['installationParam']['antennaBeamwidth']
    conditionals = {'registrationData': [conditionals_d]}

    # Create the actual config.
    devices = [device_a, device_c, device_b, device_d]
    config = {
        'fccIds': [(d['fccId'], 47) for d in devices],
        'userIds': [d['userId'] for d in devices],
        'registrationRequests': devices,
        'conditionalRegistrationData': conditionals,
        'expectedResponseCodes': [(0,), (200,), (200,), (200,)]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_REG_11_default_config)
  def test_WINNF_FT_S_REG_11(self, config_filename):
    """[Configurable] One-time registration."""

    config = loadConfig(config_filename)
    # Very light checking of the config file.
    self.assertEqual(
        len(config['registrationRequests']),
        len(config['expectedResponseCodes']))

    # Whitelist N1 FCC IDs.
    for fcc_id, max_eirp_dbm_per_10_mhz in config['fccIds']:
      self._sas_admin.InjectFccId({
          'fccId': fcc_id,
          'fccMaxEirp': max_eirp_dbm_per_10_mhz
      })

    # Whitelist N2 user IDs.
    for user_id in config['userIds']:
      self._sas_admin.InjectUserId({'userId': user_id})

    # Pre-load conditional registration data for N3 CBSDs.
    self._sas_admin.PreloadRegistrationData(
        config['conditionalRegistrationData'])

    # Register N4 CBSDs.
    request = {'registrationRequest': config['registrationRequests']}
    responses = self._sas.Registration(request)['registrationResponse']

    # Check registration responses.
    self.assertEqual(len(responses), len(config['registrationRequests']))
    for i in range(len(responses)):
      response = responses[i]
      expected_response_codes = config['expectedResponseCodes'][i]
      logging.debug('Looking at response number %d', i)
      logging.debug('Expecting to see response code in set %s in response: %s',
                    expected_response_codes, response)
      self.assertIn(response['response']['responseCode'],
                    expected_response_codes)
      if response['response']['responseCode'] == 0:  # SUCCESS
        self.assertTrue('cbsdId' in response)
      else:
        self.assertFalse('cbsdId' in response)
