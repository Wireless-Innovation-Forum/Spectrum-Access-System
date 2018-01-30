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
  loadConfig, addCbsdIdsToRequests, addGrantIdsToRequests


class DeregistrationTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @winnforum_testcase
  def test_WINNF_FT_S_DRG_1(self):
    """Valid and correct CBSD ID: two deregistrationRequest objects
    CBSD sends deregistration request to SAS with two deregistrationRequest
    objects that contain correct and valid CBSD ID, the response should be
    SUCCESS.
    """

    # Register the devices
    registration_request = []
    for device_filename in ('device_a.json', 'device_c.json'):
      device = json.load(
        open(os.path.join('testcases', 'testdata', device_filename)))
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})
      registration_request.append(device)
    request = {'registrationRequest': registration_request}
    response = self._sas.Registration(request)['registrationResponse']

    # Check registration response
    cbsd_ids = []
    self.assertEqual(len(response), 2)
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Deregister the device
    request = {'deregistrationRequest': [{'cbsdId': cbsd_ids[0]}, {'cbsdId': cbsd_ids[1]}]}
    response = self._sas.Deregistration(request)['deregistrationResponse']

    # Check the deregistration response
    self.assertEqual(len(response), 2)
    for x in range(0, 2):
      self.assertEqual(response[x]['cbsdId'], cbsd_ids[x])
      self.assertEqual(response[x]['response']['responseCode'], 0)
    del request, response

    # Prepare grant requests for two cbsdIds
    grant_1 = json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1['cbsdId'] = cbsd_ids[0]
    grant_2 = json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_2['cbsdId'] = cbsd_ids[1]

    # Send the grant requests
    request = {'grantRequest': [grant_1, grant_2]}
    response = self._sas.Grant(request)['grantResponse']

    # Check the grant responses
    # valid cbsdIds, responseCode should be 103 for both cbsdIds
    self.assertEqual(len(response), 2)
    for x, resp in enumerate(response):
      self.assertEqual(resp['response']['responseCode'], 103)
    del request, response

  @winnforum_testcase
  def test_WINNF_FT_S_DRG_2(self):
    """Missing CBSD ID: two objects in the DeregistrationRequest.
    CBSD sends Deregistration Request with two objects to the SAS, first
    object has the correct CBSD ID, the second does not have CBSD ID. The
    response for the first object should be SUCCESS. The response for the
    second object should be FAIL.
    """

    # Register two devices
    registration_request = []
    for device_filename in ('device_a.json', 'device_c.json'):
      device = json.load(
        open(os.path.join('testcases', 'testdata', device_filename)))
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})
      registration_request.append(device)
    request = {'registrationRequest': registration_request}
    response = self._sas.Registration(request)['registrationResponse']

    # Check registration response
    cbsd_ids = []
    self.assertEqual(len(response), 2)
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # Deregister
    # Send a deregister request with two elements
    # 1st element with 1st cbsdId, the 2nd element with no cbsdId
    request = {'deregistrationRequest': [{'cbsdId': cbsd_ids[0]}, {}]}
    response = self._sas.Deregistration(request)['deregistrationResponse']

    # Check the deregistration response
    self.assertEqual(len(response), 2)
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[0])
    self.assertEqual(response[0]['response']['responseCode'], 0)
    self.assertFalse('cbsdId' in response[1])
    self.assertEqual(response[1]['response']['responseCode'], 102)

  def test_WINNF_FT_S_DRG_3(self):
    """CBSD ID initially exists, CBSD deregisters first by sending
    Deregistration request. Then sends another Deregistration request
    to check that SAS indeed erased the CBSD information from its
    database.
    The response for the first Deregistration request should be SUCCESS.
    The response for the second Deregistration request should be FAIL.
    """

    # Register the device
    device = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device['fccId']})
    self._sas_admin.InjectUserId({'userId': device['userId']})
    request = {'registrationRequest': [device]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Deregister the device
    request = {'deregistrationRequest': [
        {'cbsdId': cbsd_id}]}
    response = self._sas.Deregistration(request)['deregistrationResponse'][0]
    # Check the deregistration response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['response']['responseCode'], 0)

    # Deregister the device again
    request = {'deregistrationRequest': [
        {'cbsdId': cbsd_id}]}
    response = self._sas.Deregistration(request)['deregistrationResponse'][0]
    # Check the deregistration response
    self.assertEqual(response['response']['responseCode'], 103)
    self.assertFalse('cbsdId' in response)

  @winnforum_testcase
  def test_WINNF_FT_S_DRG_4(self):
    """CBSD ID value invalid: two request objects.
    CBSD sends deregistration request to SAS with two objects in which
    the first object has the correct CBSD ID and the second object
    has an nonexistent CBSD ID. The response for the first
    object should be SUCCESS. The response for the second object
    should be FAIL.
    """

    # Register the device
    device = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device['fccId']})
    self._sas_admin.InjectUserId({'userId': device['userId']})
    request = {'registrationRequest': [device]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Deregister the devices
    request = {'deregistrationRequest': [
        {'cbsdId': cbsd_id},
        {'cbsdId': 'A nonexistent cbsd id'}]}
    response = self._sas.Deregistration(request)['deregistrationResponse']
    # Check the deregistration response
    self.assertEqual(response[0]['cbsdId'], cbsd_id)
    self.assertEqual(response[0]['response']['responseCode'], 0)
    self.assertEqual(response[1]['response']['responseCode'], 103)
    self.assertFalse('cbsdId' in response[1])

  @winnforum_testcase
  def test_WINNF_FT_S_DRG_5(self):
    """CBSD ID initially exists with a grant, CBSD deregisters,
    then re-registers and attempts to use the old grant ID. This
    is to verify SAS deletes grants on deregistration.
    """

    # Register the device
    device = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    self._sas_admin.InjectFccId({'fccId': device['fccId']})
    self._sas_admin.InjectUserId({'userId': device['userId']})
    request = {'registrationRequest': [device]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Request for grant
    grant = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant['cbsdId'] = cbsd_id
    request = {'grantRequest': [grant]}
    # Check grant response
    response = self._sas.Grant(request)['grantResponse'][0]
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['response']['responseCode'], 0)
    grant_id = response['grantId']
    del request, response

    # Send heartbeat so the device will be in Authorized state
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_id,
            'grantId': grant_id,
            'operationState': 'GRANTED'
        }]
    }

    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    # Check the heartbeat response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['grantId'], grant_id)
    self.assertEqual(response['response']['responseCode'], 0)
    self.assertLess(datetime.utcnow(),
                    datetime.strptime(response['transmitExpireTime'],
                                      '%Y-%m-%dT%H:%M:%SZ'))
    del request, response

    # Deregister the device
    request = {'deregistrationRequest': [{'cbsdId': cbsd_id}]}
    response = self._sas.Deregistration(request)['deregistrationResponse'][0]
    # Check the deregistration response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response, cbsd_id

    # Re-register the device
    request = {'registrationRequest': [device]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Send heartbeat
    request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_id,
            'grantId': grant_id,
            'operationState': 'AUTHORIZED'
        }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]

    # Check the heartbeat response
    self.assertEqual(response['response']['responseCode'], 103)
    del request, response

  def generate_DRG_6_default_config(self, filename):
    """Generates the WinnForum configuration for DRG.6."""

    # Load device info
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Load grant.json
    grant_a = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_c = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_b = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))

    # Heartbeat requests (where testcode will insert cbsdId and grantId)
    heartbeat_a = {'operationState': 'GRANTED'}
    heartbeat_c = {'operationState': 'GRANTED'}
    heartbeat_b = {'operationState': 'GRANTED'}

    # Deregistration requests (where testcode will fill in cbsdId)
    deregister_a = {}
    # device_c's CBSD ID will be removed due to the 'REMOVE' keyword.
    deregister_c = {'cbsdId': 'REMOVE'}
    deregister_b = {}

    # Device_a and device_c are Category A.
    self.assertEqual(device_a['cbsdCategory'], 'A')
    self.assertEqual(device_c['cbsdCategory'], 'A')

    # Device_b is Category B with conditionals pre-loaded.
    self.assertEqual(device_b['cbsdCategory'], 'B')
    conditionals_b = {
        'cbsdCategory': device_b['cbsdCategory'],
        'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'],
        'installationParam': device_b['installationParam']
    }
    conditionals = {'registrationData': [conditionals_b]}
    del device_b['installationParam']

    # Create the actual config.
    devices = [device_a, device_c, device_b]
    grant_requests = [grant_a, grant_c, grant_b]
    heartbeat_requests = [heartbeat_a, heartbeat_c, heartbeat_b]
    deregistration_requests = [deregister_a, deregister_c, deregister_b]
    config = {
        'registrationRequest': devices,
        'conditionalRegistrationData': conditionals,
        'grantRequest': grant_requests,
        'heartbeatRequest': heartbeat_requests,
        'deregistrationRequest': deregistration_requests,
        # First request, all valid params => SUCCESS
        # Second request is missing CBSD ID => MISSING_PARAM
        # Third request, all valid params => SUCCESS
        'expectedResponseCodes': [(0,), (102,), (0,)]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_DRG_6_default_config)
  def test_WINNF_FT_S_DRG_6(self, config_filename):
    """[Configurable] Array Deregistration."""

    config = loadConfig(config_filename)
    # Very light checking of the config file.
    self.assertTrue(
        len(config['registrationRequest']) == len(config['grantRequest']) ==
        len(config['heartbeatRequest']) == len(config['deregistrationRequest']))
    self.assertEqual(
        len(config['deregistrationRequest']),
        len(config['expectedResponseCodes']))

    # Whitelist FCC IDs.
    for device in config['registrationRequest']:
      self._sas_admin.InjectFccId({
          'fccId': device['fccId'],
          'fccMaxEirp': 47
      })

    # Whitelist user IDs.
    for device in config['registrationRequest']:
      self._sas_admin.InjectUserId({'userId': device['userId']})

    # Step 2 & 3: Register devices and get grants
    cbsd_ids, grant_ids = self.assertRegisteredAndGranted(
        config['registrationRequest'], config['grantRequest'],
        config['conditionalRegistrationData'])

    # Step 4: First Heartbeat Request
    heartbeat_request = config['heartbeatRequest']
    addCbsdIdsToRequests(cbsd_ids, heartbeat_request)
    addGrantIdsToRequests(grant_ids, heartbeat_request)
    request = {'heartbeatRequest': heartbeat_request}
    responses = self._sas.Heartbeat(request)['heartbeatResponse']
    self.assertEqual(len(responses), len(heartbeat_request))
    # Check heartbeat response
    for i, response in enumerate(responses):
      self.assertEqual(response['response']['responseCode'], 0)
    del request, responses

    # Step 5: First deregistration request
    degregister_request = config['deregistrationRequest']
    addCbsdIdsToRequests(cbsd_ids, degregister_request)
    request = {'deregistrationRequest': degregister_request}
    responses = self._sas.Deregistration(request)['deregistrationResponse']
    # Check the deregistration response
    self.assertEqual(len(responses), len(config['expectedResponseCodes']))
    for i, response in enumerate(responses):
      expected_response_codes = config['expectedResponseCodes'][i]
      logging.debug('Looking at response number %d', i)
      logging.debug('Expecting to see response code in set %s in response: %s',
                    expected_response_codes, response)
      self.assertIn(response['response']['responseCode'],
                    expected_response_codes)
      if response['response']['responseCode'] == 0:
        self.assertTrue('cbsdId' in response)
        self.assertEqual(response['cbsdId'],
                         degregister_request[i]['cbsdId'])
      else:
        self.assertFalse('cbsdId' in response)

    # Step 6: Send the Deregistration request from Step 5 again
    request = {'deregistrationRequest': degregister_request}
    responses = self._sas.Deregistration(request)['deregistrationResponse']
    # Check the deregistration response
    self.assertEqual(len(responses), len(degregister_request))
    for i, response in enumerate(responses):
      # Expecting responseCode 103 and INVALID_VALUE for CBSD ID.
      logging.debug('Looking at response number %d, response: %s', i, response)
      self.assertEqual(response['response']['responseCode'], 103)
      self.assertFalse('cbsdId' in response)
    del request, responses

    # Step 7: Send registration request from Step 2
    cbsd_ids = self.assertRegistered(config['registrationRequest'],
                                     config['conditionalRegistrationData'])

    # Step 8: Heartbeat Request
    heartbeat_requests = config['heartbeatRequest']
    addCbsdIdsToRequests(cbsd_ids, heartbeat_requests)
    request = {'heartbeatRequest': heartbeat_requests}
    responses = self._sas.Heartbeat(request)['heartbeatResponse']
    self.assertEqual(len(responses), len(heartbeat_request))
    # Check heartbeat response
    for i, response in enumerate(responses):
      logging.debug('Looking at response number %d', i)
      logging.debug('Actual response: %s', response)
      self.assertTrue(response['response']['responseCode'] in [103, 500])
