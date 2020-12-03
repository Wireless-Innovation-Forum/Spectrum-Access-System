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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime
import json
import logging
import os
import time

from six import string_types as basestring

from request_handler import HTTPError
import common_strings
import sas
import sas_testcase
from util import winnforum_testcase, configurable_testcase, writeConfig, \
  loadConfig, generateCpiRsaKeys, generateCpiEcKeys, convertRequestToRequestWithCpiSignature, json_load


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
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_c = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))

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
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_c = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_e = json_load(
        os.path.join('testcases', 'testdata', 'device_e.json'))
    device_f = json_load(
        os.path.join('testcases', 'testdata', 'device_f.json'))
    device_g = json_load(
        os.path.join('testcases', 'testdata', 'device_g.json'))

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
    grant_e = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_f = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
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
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_c = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))

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
  def test_WINNF_FT_S_REG_4(self):
    """Array Re-registration of Single-step-registered CBSD (CBSD ID exists).

    The response should be SUCCESS.
    """

    # Load 2 devices
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))

    # Inject FCC ID and User ID
    for device in [device_a, device_b]:
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

    # Convert device_b's request to embed cpiSignatureData
    convertRequestToRequestWithCpiSignature(cpi_private_key, cpi_id,
                                            cpi_name, device_b)
    # Register 2 devices
    request = {'registrationRequest': [device_a, device_b]}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response, store cbsd_ids
    cbsd_ids = []
    for resp in response:
      self.assertTrue('cbsdId' in resp)
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # The 2 CBSDs request grant, heartbeat and stay in Authorized state.
    # Request grant
    grant_request = []
    for cbsd_id in cbsd_ids:
      grant = json_load(
          os.path.join('testcases', 'testdata', 'grant_0.json'))
      grant['cbsdId'] = cbsd_id
      grant_request.append(grant)
    request = {'grantRequest': grant_request}
    # Check grant response.
    response = self._sas.Grant(request)['grantResponse']
    grant_ids = []
    for response_num, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
      self.assertEqual(resp['response']['responseCode'], 0)
      grant_ids.append(resp['grantId'])
    del request, response

    # CBSDs heartbeat to stay in Authorized state.
    heartbeat_request = [{
        'cbsdId': cbsd_ids[0],
        'grantId': grant_ids[0],
        'operationState': 'GRANTED'
    }, {
        'cbsdId': cbsd_ids[1],
        'grantId': grant_ids[1],
        'operationState': 'GRANTED'
    }]
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    # Check the heartbeat response.
    self.assertEqual(len(response), 2)
    transmit_expire_times = []
    for response_num in (0, 1):
      self.assertEqual(response[response_num]['cbsdId'], cbsd_ids[response_num])
      self.assertEqual(response[response_num]['grantId'],
                       grant_ids[response_num])
      self.assertEqual(response[response_num]['response']['responseCode'], 0)
      transmit_expire_times.append(
          datetime.strptime(response[response_num]['transmitExpireTime'],
                            '%Y-%m-%dT%H:%M:%SZ'))
    del request, response

    # Re-register the two devices and register a third device
    device_c = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})
    self._sas_admin.InjectUserId({'userId': device_c['userId']})
    devices = [device_a, device_b, device_c]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)['registrationResponse']

    # Check registration response
    self.assertEqual(len(response), len(devices))
    reregistered_cbsd_ids = []
    for resp in response:
      self.assertTrue('cbsdId' in resp)
      self.assertEqual(resp['response']['responseCode'], 0)
      reregistered_cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Reregistered CBSDs send a heartbeat request again.
    heartbeat_request = [{
        'cbsdId': reregistered_cbsd_ids[0],
        'grantId': grant_ids[0],
        'operationState': 'GRANTED'
    }, {
        'cbsdId': reregistered_cbsd_ids[1],
        'grantId': grant_ids[1],
        'operationState': 'GRANTED'
    }]
    # Wait until the later of the two transmit_expire_times
    transmit_expire_wait_time = (
        transmit_expire_times[1] - datetime.utcnow()).total_seconds()
    time.sleep(transmit_expire_wait_time + 1)
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']

    # Check the heartbeat response
    for resp in response:
      self.assertTrue(resp['response']['responseCode'] in (103, 500))
      transmit_expire_time = datetime.strptime(resp['transmitExpireTime'],
                                               '%Y-%m-%dT%H:%M:%SZ')
      self.assertLessEqual(transmit_expire_time, datetime.utcnow())

  @winnforum_testcase
  def test_WINNF_FT_S_REG_5(self):
    """Missing Required parameters in Array Registration request.

    The response should be MISSING_PARAM 102.
    """
    # (Generate CPI EC keys and) Load CPI user info
    cpi_id = 'professional_installer_id_1'
    cpi_name = 'a_name'
    cpi_private_key, cpi_public_key = generateCpiEcKeys()
    self._sas_admin.InjectCpiUser({
        'cpiId': cpi_id,
        'cpiName': cpi_name,
        'cpiPublicKey': cpi_public_key
    })

    # Load CBSD 1
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    conditionals_a = {
        'cbsdCategory': device_a['cbsdCategory'],
        'fccId': device_a['fccId'],
        'cbsdSerialNumber': device_a['cbsdSerialNumber'],
        'airInterface': device_a['airInterface'],
        'installationParam': device_a['installationParam'],
        'measCapability': device_a['measCapability']
    }

    # Load CBSD 2
    device_c = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    conditionals_c = {
        'cbsdCategory': device_c['cbsdCategory'],
        'fccId': device_c['fccId'],
        'cbsdSerialNumber': device_c['cbsdSerialNumber'],
        'airInterface': device_c['airInterface'],
        'installationParam': device_c['installationParam'],
        'measCapability': device_c['measCapability']
    }

    # Load CBSD 3
    device_e = json_load(
        os.path.join('testcases', 'testdata', 'device_e.json'))
    conditionals_e = {
        'cbsdCategory': device_e['cbsdCategory'],
        'fccId': device_e['fccId'],
        'cbsdSerialNumber': device_e['cbsdSerialNumber'],
        'airInterface': device_e['airInterface'],
        'installationParam': device_e['installationParam'],
        'measCapability': device_e['measCapability']
    }

    # Load CBSD 4
    device_f = json_load(
        os.path.join('testcases', 'testdata', 'device_f.json'))
    conditionals_f = {
        'cbsdCategory': device_f['cbsdCategory'],
        'fccId': device_f['fccId'],
        'cbsdSerialNumber': device_f['cbsdSerialNumber'],
        'airInterface': device_f['airInterface'],
        'installationParam': device_f['installationParam'],
        'measCapability': device_f['measCapability']
    }

    # Load CBSD 5
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    conditionals_b = {
        'cbsdCategory': device_b['cbsdCategory'],
        'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'],
        'installationParam': device_b['installationParam'],
        'measCapability': device_b['measCapability']
    }
    # Convert request to embed cpiSignatureData
    convertRequestToRequestWithCpiSignature(cpi_private_key, cpi_id,
                                            cpi_name, device_b, 'ES256')
    # Device 5 missing digitalSignature
    del device_b['cpiSignatureData']['digitalSignature']

    # Load CBSD 6: Cat B, missing 'cpiId' in 'professionalInstallerData'.
    device_d = json_load(
        os.path.join('testcases', 'testdata', 'device_d.json'))
    conditionals_d = {
        'cbsdCategory': device_d['cbsdCategory'],
        'fccId': device_d['fccId'],
        'cbsdSerialNumber': device_d['cbsdSerialNumber'],
        'airInterface': device_d['airInterface'],
        'installationParam': device_d['installationParam'],
        'measCapability': device_d['measCapability']
    }
    # Convert request to embed cpiSignatureData (without cpiId)
    convertRequestToRequestWithCpiSignature(cpi_private_key, '',
                                            cpi_name, device_d, 'ES256')

    conditionals = {
        'registrationData': [
            conditionals_a, conditionals_c, conditionals_e, conditionals_f,
            conditionals_b, conditionals_d
        ]
    }

    # Inject FCC ID and User ID for all devices
    for device in [device_a, device_c, device_e, device_f, device_b, device_d]:
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})
    self._sas_admin.PreloadRegistrationData(conditionals)

    # Remove conditionals from registration
    for device in [device_a, device_c, device_e, device_f]:
      del device['cbsdCategory']
      del device['airInterface']
      del device['installationParam']
      del device['measCapability']

    # Device 2 missing cbsdSerialNumber
    del device_c['cbsdSerialNumber']

    # Device 3 missing fccId
    del device_e['fccId']

    # Device 4 missing userId
    del device_f['userId']

    # Register devices
    devices = [device_a, device_c, device_e, device_f, device_b, device_d]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    self.assertTrue('cbsdId' in response[0])
    self.assertEqual(response[0]['response']['responseCode'], 0)
    for resp in response[1:]:
      self.assertEqual(resp['response']['responseCode'], 102)


  @winnforum_testcase
  def test_WINNF_FT_S_REG_6(self):
    """Pending registration in Array request (responseCode 200).

    The response should be:
    - responseCode 0 for CBSD 1.
    - responseCode 200 for CBSDs 2 and 3.
    """

    # (Generate CPI EC keys and) Load CPI user info
    cpi_id = 'professional_installer_id_1'
    cpi_name = 'a_name'
    cpi_private_key, cpi_public_key = generateCpiEcKeys()
    self._sas_admin.InjectCpiUser({
        'cpiId': cpi_id,
        'cpiName': cpi_name,
        'cpiPublicKey': cpi_public_key
    })

    # Load CBSD 1: Cat A, Has all required parameters.
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))

    # Load CBSD 2: Cat A, missing 'indoorDeployment' in 'installationParam'.
    device_c = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    del device_c['installationParam']['indoorDeployment']

    # Load CBSD 3: Cat B
    # Missing 'antennaAzimuth' in 'installationParam', both in Conditionals and
    # in the 'installationParam' signed by CPI.
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    del device_b['installationParam']['antennaAzimuth']
    conditionals_b = {
        'cbsdCategory': device_b['cbsdCategory'],
        'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'],
        'installationParam': device_b['installationParam'],
        'measCapability': device_b['measCapability']
    }
    conditionals = {
        'registrationData': [conditionals_b]
    }
    # Convert CBSD 3's request to embed cpiSignatureData
    convertRequestToRequestWithCpiSignature(cpi_private_key, cpi_id,
                                            cpi_name, device_b, 'ES256')

    # Inject FCC ID and User ID for all devices
    for device in [device_a, device_c, device_b]:
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})

    # CBSD 3 conditionals pre-loaded into SAS
    self._sas_admin.PreloadRegistrationData(conditionals)

    # Register devices
    devices = [device_a, device_c, device_b]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    self.assertTrue('cbsdId' in response[0])
    self.assertEqual(response[0]['response']['responseCode'], 0)
    for resp in response[1:]:
      self.assertEqual(resp['response']['responseCode'], 200)

  @winnforum_testcase
  def test_WINNF_FT_S_REG_7(self):
    """Invalid parameters in Array Registration Request

    The response should be 103.
    """

    # Load Devices Data
    device_1 = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_2 = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_3 = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_4 = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_4['cbsdSerialNumber'] = 'device_4_serial_number'
    device_5 = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_5['cbsdSerialNumber'] = 'device_5_serial_number'
    device_6 = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_6['cbsdSerialNumber'] = 'device_6_serial_number'
    device_6['measCapability'] = ['invalid_measCapability']
    device_7 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_8 = json_load(
        os.path.join('testcases', 'testdata', 'device_e.json'))
    device_8['cbsdSerialNumber'] =  'device_8_serial_number'
    device_9 = json_load(
        os.path.join('testcases', 'testdata', 'device_f.json'))
    device_10 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_10['cbsdSerialNumber'] = 'device_10_serial_number'
    device_11 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_11['cbsdSerialNumber'] = 'device_11_serial_number'
    device_12 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_12['cbsdSerialNumber'] = 'device_12_serial_number'
    device_13 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_13['cbsdSerialNumber'] = 'device_13_serial_number'
    device_14 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_14['cbsdSerialNumber'] = 'device_14_serial_number'
    device_15 = json_load(
        os.path.join('testcases', 'testdata', 'device_g.json'))
    device_15['cbsdSerialNumber'] =  'device_15_serial_number'
    device_16 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_16['cbsdSerialNumber'] =  'device_16_serial_number'
    # Devices that contain all necessary Fcc and user data
    devices_with_administrative_data = [device_1, device_2, device_7, device_8,\
                                        device_9, device_15]
    # Inject Fcc Id and User Id for the devices that contain all Fcc and user data data
    for device in devices_with_administrative_data:
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})
    # Inject Fcc Id with not default Fcc max Eirp
    self._sas_admin.InjectFccId({'fccId': 'fccId_approved_eirp',\
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
        'fccId': device_12['fccId'],
        'cbsdSerialNumber': device_12['cbsdSerialNumber'],
        'installationParam': device_12['installationParam'],
    }
    conditionals_13 = {
        'fccId': device_13['fccId'],
        'cbsdSerialNumber': device_13['cbsdSerialNumber'],
        'installationParam': device_13['installationParam'],
    }
    conditionals_14 = {
        'fccId': device_14['fccId'],
        'cbsdSerialNumber': device_14['cbsdSerialNumber'],
        'installationParam': device_14['installationParam'],
    }

    conditionals = {
        'registrationData': [
            conditionals_12, conditionals_13, conditionals_14
        ]
    }
    self._sas_admin.PreloadRegistrationData(conditionals)
    # Modify the configuration of the devices according to the specfications
    # invalid_cbsd serial number with length > 64 octets
    device_2['cbsdSerialNumber'] = 's' * 65
    # invalid_fcc_id with length > 20 octets
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

    device_15['fccId'] =  'fccId_approved_eirp'
    device_15['installationParam']['eirpCapability'] = 26

    device_16['fccId'] =  'fccId_approved_eirp'
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
    self.assertGreater(len(response['registrationResponse'][0]['cbsdId']), 0)
    self.assertLessEqual(len(response['registrationResponse'][0]['cbsdId']), 256)
    self.assertEqual(
          response['registrationResponse'][12]['response']['responseCode'], 0)
    for index in list(range(1, 12)) + list(range(13, 16)):
      self.assertEqual(
          response['registrationResponse'][index]['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINNF_FT_S_REG_8(self):
    """Invalid REG-Conditional parameters in Array Registration Request (responseCode 103)
    The response should be SUCCESS for the first CBSD,
    FAILURE 103 for the second and third CBSDs.
    """

    # Load devices
    device_1 = json_load(os.path.join('testcases', 'testdata', 'device_a.json'))
    device_2 = json_load(os.path.join('testcases', 'testdata', 'device_c.json'))
    device_3 = json_load(os.path.join('testcases', 'testdata', 'device_e.json'))

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
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_c = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_e = json_load(
        os.path.join('testcases', 'testdata', 'device_e.json'))
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
    self._sas.cbsd_sas_version = 'v5.0'

    # Load Devices
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_c = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_e = json_load(
        os.path.join('testcases', 'testdata', 'device_e.json'))
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
    except HTTPError as e:
      # Allow HTTP status 404
      self.assertEqual(e.error_code, 404)

  def generate_REG_11_default_config(self, filename):
    """Generates the WinnForum configuration for REG.11."""
    # Load device info
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_c = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_d = json_load(
        os.path.join('testcases', 'testdata', 'device_d.json'))

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
    conditionals = [conditionals_d]

    # Create the actual config.
    devices = [device_a, device_c, device_b, device_d]
    config = {
        'fccIds': [(d['fccId'], 47) for d in devices],
        'userIds': [d['userId'] for d in devices],
        'registrationRequests': devices,
        'conditionalRegistrationData': conditionals,
        'expectedResponseCodes': [(0,), (200,), (103,), (103,)]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_REG_11_default_config)
  def test_WINNF_FT_S_REG_11(self, config_filename):
    """[Configurable] One-time registration."""

    config = loadConfig(config_filename)
    # Very light checking of the config file.
    self.assertValidConfig(
        config, {
            'fccIds': list,
            'userIds': list,
            'registrationRequests': list,
            'conditionalRegistrationData': list,
            'expectedResponseCodes': list
        })
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
    if config['conditionalRegistrationData']:
      self._sas_admin.PreloadRegistrationData({
          'registrationData': config['conditionalRegistrationData']
      })

    # Register N4 CBSDs.
    request = {'registrationRequest': config['registrationRequests']}
    responses = self._sas.Registration(request)['registrationResponse']

    # Check registration responses.
    self.assertEqual(len(responses), len(config['registrationRequests']))
    has_error = False
    for i in range(len(responses)):
      response = responses[i]
      expected_response_codes = config['expectedResponseCodes'][i]
      logging.debug('Looking at response number %d', i)
      logging.debug('Expecting to see response code in set %s in response: %s',
                    expected_response_codes, response)

      # Check response code.
      response_code = response['response']['responseCode']
      if response_code not in expected_response_codes:
        has_error = True
        logging.error(
            'Error: response %d is expected to have a responseCode in set %s but instead had responseCode %d.',
            i, expected_response_codes, response_code)
        request = config['registrationRequests'][i]
        logging.error('Registration request: %s', config['registrationRequests'][i])
        for data in config['conditionalRegistrationData']:
          if data['fccId'] == request['fccId'] and data[
              'cbsdSerialNumber'] == request['cbsdSerialNumber']:
            logging.error('Corresponding REG-conditional data: %s', data)

      # Check for existence/absence of CBSD ID.
      if response['response']['responseCode'] == 0:  # SUCCESS
        if 'cbsdId' not in response:
          has_error = True
          logging.error('Error: CBSD ID not found in response %d (%s)', i, response)
      else:  # Not SUCCESS
        if 'cbsdId' in response:
          has_error = True
          logging.error('Error: CBSD ID found in response %d (%s)', i, response)

    # Outside the 'for' loop.
    self.assertFalse(
        has_error,
        'Error found in at least one of the responses. See logs for details.')

  def generate_REG_12_default_config(self, filename):
    """Generates the WinnForum configuration for REG.12."""

    # Load device info
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))

    # Device_a is Category A.
    self.assertEqual(device_a['cbsdCategory'], 'A')

    # Device_b is Category B with conditionals pre-loaded.
    self.assertEqual(device_b['cbsdCategory'], 'B')
    conditionals_b = {
        'cbsdCategory': device_b['cbsdCategory'],
        'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'],
        'installationParam': device_b['installationParam']
    }
    conditionals = [conditionals_b]
    del device_b['cbsdCategory']
    del device_b['airInterface']
    del device_b['installationParam']

    # Create the actual config.
    devices = [device_a, device_b]
    blacklist_devices = [device_a]
    reregister_devices = [device_a, device_b]
    config = {
        'fccIds': [(d['fccId'], 47) for d in devices],
        'fccIdsBlacklist': [d['fccId'] for d in blacklist_devices],
        'userIds': [d['userId'] for d in devices],
        'registrationRequests': devices,
        'reregistrationRequests': reregister_devices,
        'conditionalRegistrationData': conditionals,
        'expectedResponseCodes': [(101,), (0,)]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_REG_12_default_config)
  def test_WINNF_FT_S_REG_12(self, config_filename):
    """[Configurable] Re-registration (including intervening blacklist)."""

    config = loadConfig(config_filename)
    # Very light checking of the config file.
    self.assertValidConfig(
        config, {
            'fccIds': list,
            'fccIdsBlacklist': list,
            'userIds': list,
            'registrationRequests': list,
            'reregistrationRequests': list,
            'conditionalRegistrationData': list,
            'expectedResponseCodes': list
        })
    self.assertEqual(
        len(config['reregistrationRequests']),
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
    if config['conditionalRegistrationData']:
      self._sas_admin.PreloadRegistrationData({
          'registrationData': config['conditionalRegistrationData']
      })

    # Register N4 CBSDs.
    request = {'registrationRequest': config['registrationRequests']}
    try:
      responses = self._sas.Registration(request)['registrationResponse']
    except Exception as e:
      logging.error(common_strings.EXPECTED_SUCCESSFUL_REGISTRATION)

    # Check registration responses.
    self.assertEqual(len(responses), len(config['registrationRequests']))
    for i, response in enumerate(responses):
      response = responses[i]
      logging.debug('Looking at response number %d', i)
      self.assertEqual(response['response']['responseCode'], 0)
      self.assertTrue('cbsdId' in response)
    original_responses = responses
    del request, responses

    # Blacklist N5 CBSD
    for fcc_id in config['fccIdsBlacklist']:
      self._sas_admin.BlacklistByFccId({'fccId': fcc_id})

    # Re-register N6 CBSDs
    request = {'registrationRequest': config['reregistrationRequests']}
    responses = self._sas.Registration(request)['registrationResponse']

    # Check registration responses.
    has_error = False
    self.assertEqual(len(responses), len(config['reregistrationRequests']))
    for i, response in enumerate(responses):
      response = responses[i]
      expected_response_codes = config['expectedResponseCodes'][i]
      logging.debug('Looking at response number %d', i)
      logging.debug('Expecting to see response code in set %s in response: %s',
                    expected_response_codes, response)

      # Check response code.
      response_code = response['response']['responseCode']
      if response_code not in expected_response_codes:
        has_error = True
        logging.error(
            'Error: response %d is expected to have a responseCode in set %s but instead had responseCode %d.',
            i, expected_response_codes, response_code)
        request = config['reregistrationRequests'][i]
        logging.error('Re-registration request: %s', request)
        for req, resp in zip(config['registrationRequests'],
                             original_responses):
          if request['fccId'] == req['fccId'] and request[
              'cbsdSerialNumber'] == req['cbsdSerialNumber']:
            logging.error('Original registration request: %s', req)
            logging.error('Original registration response: %s', resp)
        for data in config['conditionalRegistrationData']:
          if data['fccId'] == request['fccId'] and data[
              'cbsdSerialNumber'] == request['cbsdSerialNumber']:
            logging.error('Corresponding REG-conditional data: %s', data)

      # Check for existence/absence of CBSD ID.
      if response['response']['responseCode'] == 0:  # SUCCESS
        if 'cbsdId' not in response:
          has_error = True
          logging.error('Error: CBSD ID not found in response %d (%s)', i, response)
      else:  # Not SUCCESS
        if 'cbsdId' in response:
          has_error = True
          logging.error('Error: CBSD ID found in response %d (%s)', i, response)

    # Outside the 'for' loop.
    self.assertFalse(
        has_error,
        'Error found in at least one of the responses. See logs for details.')

  def generate_REG_13_default_config(self, filename):
    """Generates the WinnForum configuration for REG.13."""

    # Load device info
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))

    # Create the actual config.
    devices = [device_a]
    config = {
        'fccIds': [(d['fccId'], 47) for d in devices],
        'userIds': [d['userId'] for d in devices],
        'registrationRequests': devices,
        # Configure SAS version to a higher than supported version.
        'sasVersion': 'v5.0'
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_REG_13_default_config)
  def test_WINNF_FT_S_REG_13(self, config_filename):
    """[Configurable] Unsupported SAS Protocol version."""

    config = loadConfig(config_filename)
    # Very light checking of the config file.
    self.assertValidConfig(
        config, {
            'fccIds': list,
            'userIds': list,
            'registrationRequests': list,
            'sasVersion': basestring
        })
    self.assertEqual(len(config['fccIds']), len(config['userIds']))
    self.assertEqual(len(config['fccIds']), len(config['registrationRequests']))
    # Use the (higher) SAS version set in the config file.
    self._sas.cbsd_sas_version  = config['sasVersion']

    # Whitelist N1 FCC ID.
    for fcc_id, max_eirp_dbm_per_10_mhz in config['fccIds']:
      self._sas_admin.InjectFccId({
          'fccId': fcc_id,
          'fccMaxEirp': max_eirp_dbm_per_10_mhz
      })

    # Whitelist N1 user ID.
    for user_id in config['userIds']:
      self._sas_admin.InjectUserId({'userId': user_id})

    # Register N1 CBSD.
    request = {'registrationRequest': config['registrationRequests']}
    try:
      responses = self._sas.Registration(request)['registrationResponse']
      # Check registration response.
      self.assertEqual(len(responses), len(config['registrationRequests']))
      for i in range(len(responses)):
        response = responses[i]
        logging.debug('Looking at response number %d', i)
        self.assertEqual(response['response']['responseCode'], 100)
    except HTTPError as e:
      # Allow HTTP status 404
      self.assertEqual(e.error_code, 404)
