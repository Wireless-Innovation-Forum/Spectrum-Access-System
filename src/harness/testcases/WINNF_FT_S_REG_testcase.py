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

import jwt
import sas
import sas_testcase
from util import winnforum_testcase, generateCpiRsaKeys, generateCpiEcKeys


class RegistrationTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def _convertRequestToRequestWithCpiSignature(self, private_key, cpi_id,
                                               cpi_name, request,
                                               jwt_algorithm='RS256'):
    """Converts a regular registration request to contain cpiSignatureData
       using the given JWT signature algorithm.

    Args:
      private_key: (string) valid PEM encoded string.
      cpi_id: (string) valid cpiId.
      cpi_name: (string) valid cpiName.
      request: individual CBSD registration request (which is a dictionary).
      jwt_algorithm: (string) algorithm to sign the JWT, defaults to 'RS256'.
    """
    cpi_signed_data = {}
    cpi_signed_data['fccId'] = request['fccId']
    cpi_signed_data['cbsdSerialNumber'] = request['cbsdSerialNumber']
    cpi_signed_data['installationParam'] = request['installationParam']
    del request['installationParam']
    cpi_signed_data['professionalInstallerData'] = {}
    cpi_signed_data['professionalInstallerData']['cpiId'] = cpi_id
    cpi_signed_data['professionalInstallerData']['cpiName'] = cpi_name
    cpi_signed_data['professionalInstallerData'][
        'installCertificationTime'] = datetime.utcnow().strftime(
            '%Y-%m-%dT%H:%M:%SZ')
    compact_jwt_message = jwt.encode(
        cpi_signed_data, private_key, jwt_algorithm)
    jwt_message = compact_jwt_message.split('.')
    request['cpiSignatureData'] = {}
    request['cpiSignatureData']['protectedHeader'] = jwt_message[0]
    request['cpiSignatureData']['encodedCpiSignedData'] = jwt_message[1]
    request['cpiSignatureData']['digitalSignature'] = jwt_message[2]

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
  def test_WINNF_FT_S_REG_6(self):
    """Pending registration in Array request (responseCode 200).

    The response should be:
    - responseCode 0 for CBSD 1.
    - responseCode 200 for CBSDs 2, 3, 4 and 5.
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
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))

    # Load CBSD 2: Cat A, missing 'indoorDeployment' in 'installationParam'.
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    del device_c['installationParam']['indoorDeployment']

    # Load CBSD 3: Cat B, missing 'digitalSignature' in 'cpiSignatureData'.
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    # Convert request to embed cpiSignatureData
    self._convertRequestToRequestWithCpiSignature(cpi_private_key, cpi_id,
                                                  cpi_name, device_b, 'ES256')
    del device_b['cpiSignatureData']['digitalSignature']

    # Load CBSD 4: Cat B, missing 'cpiId' in 'professionalInstallerData'.
    device_d = json.load(
        open(os.path.join('testcases', 'testdata', 'device_d.json')))
    # Convert request to embed cpiSignatureData (without cpiId)
    self._convertRequestToRequestWithCpiSignature(cpi_private_key, '',
                                                  cpi_name, device_d, 'ES256')

    # Load CBSD 5: Cat B
    # Missing 'antennaAzimuth' in 'installationParam', both in Conditionals and
    # in the 'installationParam' signed by CPI.
    device_h = json.load(
        open(os.path.join('testcases', 'testdata', 'device_h.json')))
    del device_h['installationParam']['antennaAzimuth']
    conditionals_h = {
        'cbsdCategory': device_h['cbsdCategory'],
        'fccId': device_h['fccId'],
        'cbsdSerialNumber': device_h['cbsdSerialNumber'],
        'airInterface': device_h['airInterface'],
        'installationParam': device_h['installationParam'],
        'measCapability': device_h['measCapability']
    }
    conditionals = {
        'registrationData': [conditionals_h]
    }
    # Convert CBSD 5's request to embed cpiSignatureData
    self._convertRequestToRequestWithCpiSignature(cpi_private_key, cpi_id,
                                                  cpi_name, device_h, 'ES256')

    # Inject FCC ID and User ID for all devices
    for device in [device_a, device_c, device_b, device_d, device_h]:
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})

    # CBSD 5 conditionals pre-loaded into SAS
    self._sas_admin.PreloadRegistrationData(conditionals)

    # Register devices
    devices = [device_a, device_c, device_b, device_d, device_h]
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    self.assertTrue('cbsdId' in response[0])
    self.assertEqual(response[0]['response']['responseCode'], 0)
    for resp in response[1:]:
      self.assertEqual(resp['response']['responseCode'], 200)

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
