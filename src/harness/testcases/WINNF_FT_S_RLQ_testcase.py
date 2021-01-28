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

import json
import logging
import os

import common_strings
from request_handler import HTTPError
import sas
import sas_testcase
from util import winnforum_testcase, configurable_testcase, writeConfig, \
  loadConfig, addCbsdIdsToRequests, addGrantIdsToRequests, json_load


class RelinquishmentTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @winnforum_testcase
  def test_WINNF_FT_S_RLQ_1(self):
    """Multiple iterative Grant relinquishments.

    The response should be SUCCESS.
    """

    # Register the device
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    self._sas_admin.InjectFccId({'fccId': device_a['fccId']})
    self._sas_admin.InjectUserId({'userId': device_a['userId']})
    request = {'registrationRequest': [device_a]}
    response = self._sas.Registration(request)['registrationResponse'][0]
    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Request two grants
    grant_0 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_0['cbsdId'] = cbsd_id
    grant_0['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3600000000,
        'highFrequency': 3610000000
    }
    grant_1 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_1['cbsdId'] = cbsd_id
    grant_1['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3610000000,
        'highFrequency': 3620000000
    }
    request = {'grantRequest': [grant_0, grant_1]}
    # Check grant response
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), 2)
    grant_ids = []
    for resp in response:
      self.assertEqual(resp['cbsdId'], cbsd_id)
      self.assertEqual(resp['response']['responseCode'], 0)
      grant_ids.append(resp['grantId'])
    del request, response

    # Relinquish the 1st grant
    request = {
        'relinquishmentRequest': [{
            'cbsdId': cbsd_id,
            'grantId': grant_ids[0]
        }]
    }
    response = self._sas.Relinquishment(request)['relinquishmentResponse'][0]
    # Check the relinquishment response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['grantId'], grant_ids[0])
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response

    # Relinquish the 2nd grant
    request = {
        'relinquishmentRequest': [{
            'cbsdId': cbsd_id,
            'grantId': grant_ids[1]
        }]
    }
    response = self._sas.Relinquishment(request)['relinquishmentResponse'][0]
    # Check the relinquishment response
    self.assertEqual(response['cbsdId'], cbsd_id)
    self.assertEqual(response['grantId'], grant_ids[1])
    self.assertEqual(response['response']['responseCode'], 0)
    del request, response

    # Send a heartbeat request with relinquished grantIds.
    heartbeat_request = []
    for grant_id in grant_ids:
      heartbeat_request.append({
          'cbsdId': cbsd_id,
          'grantId': grant_id,
          'operationState': 'GRANTED'
      })
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    # Check the heartbeat response
    self.assertEqual(len(response), 2)
    for resp in response:
      self.assertEqual(resp['cbsdId'], cbsd_id)
      self.assertTrue(resp['response']['responseCode'] in [103, 500])
      # No need to check transmitExpireTime since this is the first heartbeat.

  @winnforum_testcase
  def test_WINNF_FT_S_RLQ_2(self):
    """Multiple Grant relinquishments: Successful simultaneous Relinquishment
    Request of multiple grants.

    Relinquishment Request array including valid CBSD ID and Grant ID.
    The response should be SUCCESS.
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

    # Request grants
    grant_0 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_0['cbsdId'] = cbsd_id
    grant_0['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3600000000,
        'highFrequency': 3610000000
    }
    grant_1 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_1['cbsdId'] = cbsd_id
    grant_1['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3610000000,
        'highFrequency': 3620000000
    }
    grant_2 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_2['cbsdId'] = cbsd_id
    grant_2['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3620000000,
        'highFrequency': 3630000000
    }
    request = {'grantRequest': [grant_0, grant_1, grant_2]}
    # Check grant response
    grant_ids = []
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), 3)
    for resp_number, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_id)
      self.assertEqual(resp['response']['responseCode'], 0)
      grant_ids.append(resp['grantId'])
    del request, response

    # Relinquish the grants
    request = {'relinquishmentRequest': [
        {'cbsdId': cbsd_id, 'grantId': grant_ids[0]},
        {'cbsdId': cbsd_id, 'grantId': grant_ids[1]},
        {'cbsdId': cbsd_id, 'grantId': grant_ids[2]}]}
    response = self._sas.Relinquishment(request)['relinquishmentResponse']
    # Check the relinquishment response
    self.assertEqual(len(response), 3)
    for resp_number, resp in enumerate(response):
      self.assertEqual(resp['cbsdId'], cbsd_id)
      self.assertEqual(resp['grantId'], grant_ids[resp_number])
      self.assertEqual(resp['response']['responseCode'], 0)
    del request, response

    # Send heartbeat request with relinquished grantIds.
    heartbeat_request = [{
        'cbsdId': cbsd_id,
        'grantId': grant_ids[0],
        'operationState': 'GRANTED'
    }, {
        'cbsdId': cbsd_id,
        'grantId': grant_ids[1],
        'operationState': 'GRANTED'
    }, {
        'cbsdId': cbsd_id,
        'grantId': grant_ids[2],
        'operationState': 'GRANTED'
    }]
    request = {'heartbeatRequest': heartbeat_request}
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    # Check the heartbeat response
    self.assertEqual(len(response), 3)
    for resp in response:
      self.assertEqual(resp['cbsdId'], cbsd_id)
      self.assertTrue(resp['response']['responseCode'] == 103)
      # No need to check transmitExpireTime since this is the first heartbeat.

  @winnforum_testcase
  def test_WINNF_FT_S_RLQ_3(self):
    """CBSD relinquishment request of multiple grants

    CBSD Harness sends Relinquishment Request to SAS including multiple
    grants, some with Grant ID that does not belong to the CBSD, some with
    valid CBSD ID and Grant ID that's previously relinquished.
    The response should be FAIL.
    """

    # Register the device
    device_2 = json_load(os.path.join('testcases', 'testdata', 'device_a.json'))
    device_4 = json_load(os.path.join('testcases', 'testdata', 'device_c.json'))
    self._sas_admin.InjectFccId({'fccId': device_2['fccId']})
    self._sas_admin.InjectUserId({'userId': device_2['userId']})
    self._sas_admin.InjectFccId({'fccId': device_4['fccId']})
    self._sas_admin.InjectUserId({'userId': device_4['userId']})
    request = {'registrationRequest': [device_2, device_4]}
    response = self._sas.Registration(request)['registrationResponse']

    # Check registration response
    self.assertEqual(response[0]['response']['responseCode'], 0)
    self.assertEqual(response[1]['response']['responseCode'], 0)
    cbsd_id_1 = 'A nonexistent cbsd id'
    cbsd_id_2 = response[0]['cbsdId']
    cbsd_id_4 = response[1]['cbsdId']
    del request, response

    # Request grants
    grant_2 = json_load(os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_2['cbsdId'] = cbsd_id_2
    grant_2['operationParam']['operationFrequencyRange'] = {
         'lowFrequency': 3600000000,
         'highFrequency': 3610000000
    }
    grant_3 = json_load(os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_3['cbsdId'] = cbsd_id_2
    grant_3['operationParam']['operationFrequencyRange'] = {
         'lowFrequency': 3610000000,
         'highFrequency': 3620000000
    }
    grant_4 = json_load(os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_4['cbsdId'] = cbsd_id_4
    grant_4['operationParam']['operationFrequencyRange'] = {
         'lowFrequency': 3620000000,
         'highFrequency': 3630000000
    }
    request = {'grantRequest': [grant_2, grant_3, grant_4]}
    response = self._sas.Grant(request)['grantResponse']

    # Check grant response
    self.assertEqual(response[0]['cbsdId'], cbsd_id_2)
    self.assertEqual(response[0]['response']['responseCode'], 0)
    grant_id_2 = response[0]['grantId']
    self.assertEqual(response[1]['cbsdId'], cbsd_id_2)
    self.assertEqual(response[1]['response']['responseCode'], 0)
    grant_id_3 = response[1]['grantId']
    self.assertEqual(response[2]['cbsdId'], cbsd_id_4)
    self.assertEqual(response[2]['response']['responseCode'], 0)
    grant_id_4 = response[2]['grantId']
    grant_id_1 = 'A nonexistent grant id'
    del request, response

    # Relinquish grant for cbsdId2 and grantId3
    request = {'relinquishmentRequest': [{'cbsdId': cbsd_id_2, 'grantId': grant_id_3}]}
    response = self._sas.Relinquishment(request)['relinquishmentResponse'][0]

    # Check the relinquishment response
    self.assertEqual(response['cbsdId'], cbsd_id_2)
    self.assertEqual(response['grantId'], grant_id_3)
    self.assertEqual(response['response']['responseCode'], 0)

    # Relinquish the grants with combinations of cbsd and grant Ids that are incorrect
    request = {'relinquishmentRequest': [
        {'cbsdId': cbsd_id_1, 'grantId': grant_id_2},
        {'cbsdId': cbsd_id_2, 'grantId': grant_id_1},
        {'cbsdId': cbsd_id_1, 'grantId': grant_id_1},
        {'cbsdId': cbsd_id_2, 'grantId': grant_id_4},
        {'cbsdId': cbsd_id_2, 'grantId': grant_id_3}]}
    response = self._sas.Relinquishment(request)['relinquishmentResponse']

    # Check the relinquishment response
    self.assertEqual(len(response), 5)
    self.assertFalse('cbsdId' in response[0])
    self.assertFalse('grantId' in response[0])
    self.assertEqual(response[0]['response']['responseCode'], 103)
    self.assertEqual(response[1]['cbsdId'], cbsd_id_2)
    self.assertFalse('grantId' in response[1])
    self.assertEqual(response[1]['response']['responseCode'], 103)
    self.assertFalse('cbsdId' in response[2])
    self.assertFalse('grantId' in response[2])
    self.assertEqual(response[2]['response']['responseCode'], 103)
    self.assertEqual(response[3]['cbsdId'], cbsd_id_2)
    self.assertFalse('grantId' in response[3])
    self.assertEqual(response[3]['response']['responseCode'], 103)
    self.assertEqual(response[4]['cbsdId'], cbsd_id_2)
    self.assertFalse('grantId' in response[4])
    self.assertEqual(response[4]['response']['responseCode'], 103)

  @winnforum_testcase
  def test_WINNF_FT_S_RLQ_4(self):
    """CBSD relinquishment request of multiple grants

    CBSD Harness sends Relinquishment Request to SAS including multiple
    grants with valid CBSD ID and valid Grant ID, but with protocol
    version not supported by SAS. The response should be FAIL.
    """

    # Register the device
    device = json_load(os.path.join('testcases', 'testdata', 'device_a.json'))
    self._sas_admin.InjectFccId({'fccId': device['fccId']})
    self._sas_admin.InjectUserId({'userId': device['userId']})
    request = {'registrationRequest': [device]}
    response = self._sas.Registration(request)['registrationResponse'][0]

    # Check registration response
    self.assertEqual(response['response']['responseCode'], 0)
    cbsd_id = response['cbsdId']
    del request, response

    # Request grants
    grant_1 = json_load(os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_1['cbsdId'] = cbsd_id
    grant_1['operationParam']['operationFrequencyRange'] = {
         'lowFrequency': 3600000000,
         'highFrequency': 3610000000
    }
    grant_2 = json_load(os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_2['cbsdId'] = cbsd_id
    grant_2['operationParam']['operationFrequencyRange'] = {
         'lowFrequency': 3610000000,
         'highFrequency': 3620000000
    }
    grant_3 = json_load(os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_3['cbsdId'] = cbsd_id
    grant_3['operationParam']['operationFrequencyRange'] = {
         'lowFrequency': 3620000000,
         'highFrequency': 3630000000
    }
    grant_id = []
    request = {'grantRequest': [grant_1, grant_2, grant_3]}
    response = self._sas.Grant(request)['grantResponse']

    # Check grant response
    self.assertEqual(len(response), 3)
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      self.assertEqual(resp['cbsdId'], cbsd_id)
      grant_id.append(resp['grantId'])
    del request, response

    # Use higher than supported version
    self._sas.cbsd_sas_version = 'v5.0'

    # Relinquish the grants
    request = {'relinquishmentRequest': [
        {'cbsdId': cbsd_id, 'grantId': grant_id[0]},
        {'cbsdId': cbsd_id, 'grantId': grant_id[1]},
        {'cbsdId': cbsd_id, 'grantId': grant_id[2]}
    ]}

    try:
      response = self._sas.Relinquishment(request)['relinquishmentResponse']

      # Check relinquishment response
      self.assertEqual(len(response), 3)
      for resp_number, resp in enumerate(response):
        self.assertEqual(resp['cbsdId'], cbsd_id)
        self.assertEqual(resp['grantId'], grant_id[resp_number])
        self.assertEqual(resp['response']['responseCode'], 100)
    except HTTPError as e:
      # Allow HTTP status 404
      self.assertEqual(e.error_code, 404)

  @winnforum_testcase
  def test_WINNF_FT_S_RLQ_5(self):
    """Missing Parameter in Relinquishment Array request.

    Relinquishment Request including multiple grants with missing CBSD/Grant ID.
    The response should be FAIL.
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

    # Request grants
    grant_0 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_0['cbsdId'] = cbsd_id
    grant_0['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3600000000,
        'highFrequency': 3610000000
    }
    grant_1 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_1['cbsdId'] = cbsd_id
    grant_1['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3610000000,
        'highFrequency': 3620000000
    }
    grant_2 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_2['cbsdId'] = cbsd_id
    grant_2['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3620000000,
        'highFrequency': 3630000000
    }
    request = {'grantRequest': [grant_0, grant_1, grant_2]}
    # Check grant response
    grant_id = []
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), 3)
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      self.assertEqual(resp['cbsdId'], cbsd_id)
      grant_id.append(resp['grantId'])
    del request, response

    # Relinquish the grants
    request = {'relinquishmentRequest': [
        {'cbsdId': cbsd_id},
        {},
        {'grantId': grant_id[2]}
    ]}
    response = self._sas.Relinquishment(request)['relinquishmentResponse']
    # Check relinquishment response #1
    self.assertEqual(response[0]['cbsdId'], cbsd_id)
    self.assertFalse('grantId' in response[0])
    self.assertEqual(response[0]['response']['responseCode'], 102)
    # Check relinquishment response #2, 3
    for response_num in [1, 2]:
      self.assertFalse('cbsdId' in response[response_num])
      self.assertFalse('grantId' in response[response_num])
      self.assertEqual(response[response_num]['response']['responseCode'], 102)

  def generate_RLQ_6_default_config(self, filename):
    """Generates the WinnForum configuration for RLQ.6."""

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

    # Relinquishment requests (filled in during test execution):
    # device_a and device_b will use the correct CBSD ID and Grant ID
    relinquish_a = {}
    relinquish_b = {}
    # device_c's CBSD ID will be filled in but Grant ID param will be removed
    # due to the 'REMOVE' keyword.
    relinquish_c = {'grantId': 'REMOVE'}

    # Create the actual config.
    devices = [device_a, device_c, device_b]
    grant_requests = [grant_a, grant_c, grant_b]
    # The CBSD ID from the 0th device (i.e. device_a) in the registration
    # request and the Grant ID from the 0th grant request (corresponding to the
    # 0th CBSD) will be used in this relinquishment request.
    relinquishment_requests1 = [{'cbsdId': 0, 'grantId': 0}]
    relinquishment_requests2 = [relinquish_a, relinquish_c, relinquish_b]
    config = {
        'registrationRequests': devices,
        'conditionalRegistrationData': conditionals,
        'grantRequests': grant_requests,
        'relinquishmentRequestsFirst': relinquishment_requests1,
        'relinquishmentRequestsSecond': relinquishment_requests2,
        'expectedResponseCodesFirst': [(0,)],
        # First request is a "re-relinquishment" => INVALID_VALUE for Grant ID
        # Second request is missing Grant ID => MISSING_PARAM
        # Third request is first relinquishment, all valid params => SUCCESS
        'expectedResponseCodesSecond': [(103,), (102,), (0,)]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_RLQ_6_default_config)
  def test_WINNF_FT_S_RLQ_6(self, config_filename):
    """[Configurable] Multiple Relinquishments."""

    config = loadConfig(config_filename)
    # Very light checking of the config file.
    self.assertValidConfig(
        config, {
            'registrationRequests': list,
            'conditionalRegistrationData': list,
            'grantRequests': list,
            'relinquishmentRequestsFirst': list,
            'relinquishmentRequestsSecond': list,
            'expectedResponseCodesFirst': list,
            'expectedResponseCodesSecond': list
        })
    self.assertEqual(
        len(config['relinquishmentRequestsFirst']),
        len(config['expectedResponseCodesFirst']))
    self.assertEqual(
        len(config['relinquishmentRequestsSecond']),
        len(config['expectedResponseCodesSecond']))

    # Whitelist FCC IDs.
    for device in config['registrationRequests']:
      self._sas_admin.InjectFccId({
          'fccId': device['fccId'],
          'fccMaxEirp': 47
      })

    # Whitelist user IDs.
    for device in config['registrationRequests']:
      self._sas_admin.InjectUserId({'userId': device['userId']})

    # Register devices and get grants
    try:
      cbsd_ids, grant_ids = self.assertRegisteredAndGranted(
          config['registrationRequests'], config['grantRequests'],
          config['conditionalRegistrationData'])
    except Exception:
      logging.error(common_strings.EXPECTED_SUCCESSFUL_REGISTRATION_AND_GRANT)
      raise

    # First relinquishment
    relinquishment_request = config['relinquishmentRequestsFirst']
    addCbsdIdsToRequests(cbsd_ids, relinquishment_request)
    addGrantIdsToRequests(grant_ids, relinquishment_request)
    request = {'relinquishmentRequest': relinquishment_request}

    responses = self._sas.Relinquishment(request)['relinquishmentResponse']
    # Check relinquishment response
    self.assertEqual(len(responses), len(config['expectedResponseCodesFirst']))
    relinquished_grant_ids = []
    has_error = False
    for i, response in enumerate(responses):
      expected_response_codes = config['expectedResponseCodesFirst'][i]
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
        logging.error('Relinquishment request: %s', config['relinquishmentRequestsFirst'][i])
        logging.error('Relinquishment response: %s', response)

      # "If the corresponding request contained a valid cbsdId and grantId, the
      # response shall contain the same grantId."
      if 'cbsdId' and 'grantId' in relinquishment_request[i]:
        if (relinquishment_request[i]['cbsdId'] in cbsd_ids) and (
            relinquishment_request[i]['grantId'] in grant_ids):
          cbsd_index = cbsd_ids.index(relinquishment_request[i]['cbsdId'])
          grant_index = grant_ids.index(relinquishment_request[i]['grantId'])
          # Check if CBSD ID is paired with the corresponding Grant ID.
          if cbsd_index == grant_index:
            self.assertEqual(response['grantId'],
                             relinquishment_request[i]['grantId'])
            relinquished_grant_ids.append(response['grantId'])
    del request, responses

    # Outside the 'for' loop.
    # Test will stop here if there are any errors, else continue.
    self.assertFalse(
        has_error,
        'Error found in at least one of the responses. See logs for details.')

    # Second relinquishment
    relinquishment_request = config['relinquishmentRequestsSecond']
    addCbsdIdsToRequests(cbsd_ids, relinquishment_request)
    addGrantIdsToRequests(grant_ids, relinquishment_request)
    request = {'relinquishmentRequest': relinquishment_request}
    responses = self._sas.Relinquishment(request)['relinquishmentResponse']
    # Check relinquishment response
    self.assertEqual(len(responses), len(config['expectedResponseCodesSecond']))
    for i, response in enumerate(responses):
      expected_response_codes = config['expectedResponseCodesSecond'][i]
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
        logging.error('Relinquishment request: %s', config['relinquishmentRequestsSecond'][i])
        logging.error('Relinquishment response: %s', response)

      if 'cbsdId' and 'grantId' in relinquishment_request[i]:
        if (relinquishment_request[i]['cbsdId'] in cbsd_ids) and (
            relinquishment_request[i]['grantId'] in grant_ids):
          cbsd_index = cbsd_ids.index(relinquishment_request[i]['cbsdId'])
          grant_index = grant_ids.index(relinquishment_request[i]['grantId'])
          if cbsd_index == grant_index:
            if relinquishment_request[i][
                'grantId'] not in relinquished_grant_ids:
              self.assertEqual(response['grantId'],
                               relinquishment_request[i]['grantId'])

    # Outside the 'for' loop.
    self.assertFalse(
        has_error,
        'Error found in at least one of the responses. See logs for details.')
