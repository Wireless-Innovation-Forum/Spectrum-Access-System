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

import common_strings
import sas
import sas_testcase
from util import winnforum_testcase, configurable_testcase, writeConfig, \
  loadConfig, addCbsdIdsToRequests, addGrantIdsToRequests, json_load


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
      device = json_load(
        os.path.join('testcases', 'testdata', device_filename))
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
    grant_1 = json_load(os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_1['cbsdId'] = cbsd_ids[0]
    grant_2 = json_load(os.path.join('testcases', 'testdata', 'grant_0.json'))
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
      device = json_load(
          os.path.join('testcases', 'testdata', device_filename))
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
    device = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
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
    device = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
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
    device = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    self._sas_admin.InjectFccId({'fccId': device['fccId']})
    self._sas_admin.InjectUserId({'userId': device['userId']})
    request = {'registrationRequest': [device]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Request for grant
    grant = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
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
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_c = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))

    # Load grant.json
    grant_a = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_c = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_b = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))

    # Heartbeat requests (where testcode will insert cbsdId and grantId)
    heartbeat_a = {'operationState': 'GRANTED'}
    heartbeat_c = {'operationState': 'GRANTED'}
    heartbeat_b = {'operationState': 'GRANTED'}

    # Deregistration requests (where testcode will fill in cbsdId)
    # device_a's CBSD ID will be the same test string.
    deregister_a = {'cbsdId': 'Test-Invalid-cbsd-string'}
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
    conditionals = [conditionals_b]
    del device_b['installationParam']
    del device_b['cbsdCategory']
    del device_b['airInterface']

    # Create the actual config.
    devices = [device_a, device_c, device_b]
    grant_requests = [grant_a, grant_c, grant_b]
    heartbeat_requests = [heartbeat_a, heartbeat_c, heartbeat_b]
    deregistration_requests = [deregister_a, deregister_c, deregister_b]
    config = {
        'registrationRequests': devices,
        'conditionalRegistrationData': conditionals,
        'grantRequests': grant_requests,
        'heartbeatRequests': heartbeat_requests,
        'deregistrationRequests': deregistration_requests,
        # First request has an invalid CBSD ID => INVALID_VALUE
        # Second request is missing CBSD ID => MISSING_PARAM
        # Third request, all valid params => SUCCESS
        'expectedResponseCodes': [(103,), (102,), (0,)]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_DRG_6_default_config)
  def test_WINNF_FT_S_DRG_6(self, config_filename):
    """[Configurable] Array Deregistration."""

    config = loadConfig(config_filename)
    # Very light checking of the config file.
    self.assertValidConfig(
        config, {
            'registrationRequests': list,
            'conditionalRegistrationData': list,
            'grantRequests': list,
            'heartbeatRequests': list,
            'deregistrationRequests': list,
            'expectedResponseCodes': list
        })
    self.assertEqual(
        len(config['registrationRequests']), len(config['grantRequests']))
    self.assertEqual(
        len(config['grantRequests']), len(config['heartbeatRequests']))
    self.assertEqual(
        len(config['heartbeatRequests']), len(config['deregistrationRequests']))
    self.assertEqual(
        len(config['deregistrationRequests']),
        len(config['expectedResponseCodes']))

    # Whitelist FCC IDs.
    for device in config['registrationRequests']:
      self._sas_admin.InjectFccId({
          'fccId': device['fccId'],
          'fccMaxEirp': 47
      })

    # Whitelist user IDs.
    for device in config['registrationRequests']:
      self._sas_admin.InjectUserId({'userId': device['userId']})

    # Step 2 & 3: Register devices and get grants
    try:
      cbsd_ids, grant_ids = self.assertRegisteredAndGranted(
          config['registrationRequests'], config['grantRequests'],
          config['conditionalRegistrationData'])
    except Exception:
      logging.error(common_strings.EXPECTED_SUCCESSFUL_REGISTRATION_AND_GRANT)
      raise

    # Step 4: First Heartbeat Request
    heartbeat_request = config['heartbeatRequests']
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
    deregister_request = config['deregistrationRequests']
    addCbsdIdsToRequests(cbsd_ids, deregister_request)
    request = {'deregistrationRequest': deregister_request}
    responses_1 = self._sas.Deregistration(request)['deregistrationResponse']

    # Check the deregistration response
    self.assertEqual(len(responses_1), len(config['expectedResponseCodes']))
    has_error = False
    registration_request = config['registrationRequests']
    conditional_registration_data = config['conditionalRegistrationData']
    for i, response in enumerate(responses_1):
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
        logging.error('Deregistration request: %s', config['deregistrationRequests'][i])
        logging.error('Deregistration response: %s', response)

      # "If the corresponding request contained a valid cbsdId, the
      # response shall contain the same cbsdId."
      if 'cbsdId' in deregister_request[i]:
        if deregister_request[i]['cbsdId'] in cbsd_ids:
          self.assertEqual(response['cbsdId'], deregister_request[i]['cbsdId'])
        else:
          self.assertFalse('cbsdId' in response)
      # remove still registered CBSDs from the next preload conditional registration
      if response['response']['responseCode'] != 0:
        cbsd_to_be_removed_from_next_reg = registration_request[i]
        indexes_conditional_to_remove = [index for index, c in enumerate(conditional_registration_data) if c['cbsdSerialNumber'] == cbsd_to_be_removed_from_next_reg['cbsdSerialNumber'] and c['fccId'] == cbsd_to_be_removed_from_next_reg['fccId']]
        for index in reversed(indexes_conditional_to_remove):
          del conditional_registration_data[index]

    # Outside the 'for' loop.
    # Test will stop here if there are any errors, else continue.
    self.assertFalse(
        has_error,
        'Error found in at least one of the responses. See logs for details.')

    # Step 6: Send the Deregistration request from Step 5 again
    request = {'deregistrationRequest': deregister_request}
    responses_2 = self._sas.Deregistration(request)['deregistrationResponse']
    # Check the deregistration response
    self.assertEqual(len(responses_2), len(deregister_request))
    self.assertEqual(len(responses_2), len(responses_1))
    # If the corresponding responseCode in the previous Deregistration Response
    # Message was 102, the responseCode shall be 102.
    for i, (response1, response2) in enumerate((zip(responses_1, responses_2))):
      logging.debug('Looking at response number %d, response: %s', i, response2)
      if response1['response']['responseCode'] == 102:
        self.assertEqual(response2['response']['responseCode'], 102)
      else:
        # Otherwise, the responseCode shall be INVALID_VALUE or DEREGISTER.
        self.assertTrue(response2['response']['responseCode'] in [103, 105])
      self.assertFalse('cbsdId' in response2)
    del request, responses_2
    # Step 7: Send registration request from Step 2
    cbsd_ids = self.assertRegistered(registration_request,
                                           conditional_registration_data)

    # Step 8: Heartbeat Request
    heartbeat_requests = config['heartbeatRequests']
    addCbsdIdsToRequests(cbsd_ids, heartbeat_requests)
    request = {'heartbeatRequest': heartbeat_requests}
    responses = self._sas.Heartbeat(request)['heartbeatResponse']
    self.assertEqual(len(responses), len(heartbeat_requests))
    # Check heartbeat response
    for i, response in enumerate(responses):
      logging.debug('Looking at response number %d', i)
      logging.debug('Actual response: %s', response)
      self.assertTrue(response['response']['responseCode'] in [103, 500])
