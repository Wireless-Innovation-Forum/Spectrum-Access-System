#    Copyright 2018 SAS Project Authors. All Rights Reserved.
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
import signal
import time
import unittest
import sas
from google3.third_party.winnforum_sas.src.harness import util


class SasTestCase(unittest.TestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def assertContainsRequiredFields(self, schema_filename, response):
    """Assertion of required fields in response, validating it with Schema.

    Args:
      schema_filename: A string containing the filename of the schema to be used
        to validate. (The schema file should exist in /schema directory.)
      response: A dictionary containing the response to validate for required
        fields using the schema.
    """
    util.assertContainsRequiredFields(schema_filename, response)

  def assertValidResponseFormatForApprovedGrant(self, grant_response):
    """Validates an approved grant response.

    Checks presence and basic validity of each required field.
    Checks basic validity of optional fields if they exist.
    Args:
      grant_response: A dictionary with a single grant response object from an
        array originally returned by a SAS server as specified in TS

    Returns:
      Nothing. It asserts if something about the response is broken/not per
      specs. Assumes it is dealing with an approved request.
    """
    # Check required string fields
    for field_name in ('cbsdId', 'grantId', 'grantExpireTime', 'channelType'):
      self.assertTrue(field_name in grant_response)
      self.assertGreater(len(grant_response[field_name]), 0)

    self.assertTrue('heartbeatInterval' in grant_response)

    if 'measReportConfig' in grant_response:
      self.assertGreater(len(grant_response['measReportConfig']), 0)

    # operationParam should not be set if grant is approved
    self.assertFalse('operationParam' in grant_response)
    self.assertTrue(grant_response['channelType'] in ('PAL', 'GAA'))

  def assertRegistered(self, registration_request,
                       conditional_registration_data=None, cert=None, key=None):
    """Register a list of devices.

    Quickly register N devices, assert registration SUCCESS, get CBSD IDs.
    Includes injection of FCC IDs and conditional registration data.

    Args:
      registration_request: A list of individual CBSD registration requests
        (each of which is itself a dictionary).
      conditional_registration_data: A list of individual CBSD registration
        data that need to be preloaded into SAS (each of which is a dictionary).
        The dictionary is a RegistrationRequest object, the fccId and
        cbsdSerialNumber fields are required, other fields are optional.
      cert: Path to SSL cert file, if None, will use default cert file.
      key: Path to SSL key file, if None, will use default key file.

    Returns:
      A list of cbsd_ids.
    """

    for device in registration_request:
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})
    if conditional_registration_data:
      self._sas_admin.PreloadRegistrationData({
          'registrationData': conditional_registration_data
      })

    # Pass the correct client cert and key in Registration request
    ssl_cert = cert if cert is not None else self._sas._tls_config.client_cert
    ssl_key = key if key is not None else self._sas._tls_config.client_key

    request = {'registrationRequest': registration_request}
    response = self._sas.Registration(
        request, ssl_cert=ssl_cert, ssl_key=ssl_key)['registrationResponse']

    # Check the registration response; collect CBSD IDs
    cbsd_ids = []
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      self.assertTrue('cbsdId' in resp)
      cbsd_ids.append(resp['cbsdId'])

    # Return list of cbsd_ids
    return cbsd_ids

  def assertRegisteredAndGranted(self, registration_request, grant_request,
                                 conditional_registration_data=None, cert=None,
                                 key=None):
    """Register and get grants for a list of devices.

    Quickly register and grant N devices; assert SUCCESS for each step and
    return corresponding CBSD and grant IDs.
    Args:
      registration_request: A list of individual CBSD registration requests
        (each of which is itself a dictionary).
      grant_request: A dictionary with a single key-value pair where the key is
        "grantRequest" and the value is a list of individual CBSD
        grant requests (each of which is itself a dictionary).
      conditional_registration_data: A list of individual CBSD registration
        data that need to be preloaded into SAS (each of which is a dictionary).
        The dictionary is a RegistrationRequest object, the fccId and
        cbsdSerialNumber fields are required, other fields are optional.
      cert: Path to SSL cert file, if None, will use default cert file.
      key: Path to SSL key file, if None, will use default key file.

    Returns:
      A tuple containing list of cbsdIds and grantIds.
    """
    self.assertEqual(len(registration_request), len(grant_request))
    cbsd_ids = self.assertRegistered(registration_request,
                                     conditional_registration_data)

    for cbsd_id, grant_req in zip(cbsd_ids, grant_request):
      grant_req['cbsdId'] = cbsd_id

    # Pass the correct client cert and key in Grant request
    ssl_cert = cert if cert is not None else self._sas._tls_config.client_cert
    ssl_key = key if key is not None else self._sas._tls_config.client_key

    grant_ids = []
    request = {'grantRequest': grant_request}
    grant_response = self._sas.Grant(
        request, ssl_cert=ssl_cert, ssl_key=ssl_key)['grantResponse']

    # Check the grant response
    for cbsd_id, grant_resp in zip(cbsd_ids, grant_response):
      self.assertEqual(grant_resp['cbsdId'], cbsd_id)
      self.assertTrue(grant_resp['grantId'])
      self.assertEqual(grant_resp['response']['responseCode'], 0)
      grant_ids.append(grant_resp['grantId'])

    # Return cbsd_ids and grant_ids
    return cbsd_ids, grant_ids

  def assertHeartbeatsSuccessful(self, cbsd_ids, grant_ids, operation_states):
    """Makes a heartbeat request for a list of devices with its grants and
    operation states.

    Sends heartbeat requests and assert the response for valid CBSD ID,
     Grant ID, and Transmit expire time.
    Args:
      cbsd_ids: A list containing CBSD IDs.
      grant_ids: A list containing Grant IDs associated with each device in
        cbsd_ids list.
      operation_states: A list containing operation states (AUTHORIZED or
        GRANTED) for each devices in the cbsd_ids list.
    Returns:
      A list of transmit expire time in the format YYYY-MM-DDThh:mm:ssZ.
    """
    transmit_expire_times = []
    self.assertEqual(len(cbsd_ids), len(grant_ids))
    self.assertEqual(len(cbsd_ids), len(operation_states))
    heartbeat_requests = []
    for cbsd_id, grant_id, operation_state in zip(cbsd_ids, grant_ids,
                                                  operation_states):
      heartbeat_requests.append({
          'cbsdId': cbsd_id,
          'grantId': grant_id,
          'operationState': operation_state
      })

    # Pass the correct client cert and key in HeartBeat request
    ssl_cert = self._sas._tls_config.client_cert
    ssl_key = self._sas._tls_config.client_key

    heartbeat_response = self._sas.Heartbeat(
        {
            'heartbeatRequest': heartbeat_requests
        },
        ssl_cert=ssl_cert,
        ssl_key=ssl_key)['heartbeatResponse']

    for index, response in enumerate(heartbeat_response):
      # Check the heartbeat response
      self.assertEqual(response['cbsdId'], cbsd_ids[index])
      self.assertEqual(response['grantId'], grant_ids[index])
      transmit_expire_time = datetime.strptime(response['transmitExpireTime'],
                                               '%Y-%m-%dT%H:%M:%SZ')
      self.assertLess(datetime.utcnow(), transmit_expire_time)
      self.assertLessEqual(
          (transmit_expire_time - datetime.utcnow()).total_seconds(), 240)
      self.assertEqual(response['response']['responseCode'], 0)
      transmit_expire_times.append(response['transmitExpireTime'])
    return transmit_expire_times

  def TriggerDailyActivitiesImmediatelyAndWaitUntilComplete(self):
    """
    Triggers daily activities immediately and checks for the status of activity
    every 10 seconds until it is completed.
    If the status is not changed within 2 hours it will throw an exception.
    """
    self._sas_admin.TriggerDailyActivitiesImmediately()
    signal.signal(signal.SIGALRM,
                  lambda signum, frame:
                  (_ for _ in ()).throw(
                      Exception('Daily Activity Check Timeout')))

    # Timeout after 2 hours if it's not completed
    signal.alarm(7200)
    # Check the Status of Daily Activities every 10 seconds
    while not self._sas_admin.GetDailyActivitiesStatus()['completed']:
      time.sleep(10)
    signal.alarm(0)

  def assertChannelsContainFrequencyRange(self, channels, frequency_range):
    channels.sort(
        key=
        lambda ch: (ch['frequencyRange']['lowFrequency'],
                    ch['frequencyRange']['highFrequency']),
        reverse=False)
    for index, channel in enumerate(channels):
      if index == 0:
        self.assertEqual(channel['frequencyRange']['lowFrequency'],
                         frequency_range['lowFrequency'])
      else:
        self.assertLessEqual(
            channel['frequencyRange']['lowFrequency'],
            channels[index - 1]['frequencyRange']['highFrequency'])

    channels.sort(
        key=lambda ch: (ch['frequencyRange']['highFrequency']), reverse=True)
    self.assertEqual(channels[0]['frequencyRange']['highFrequency'],
                     frequency_range['highFrequency'])

  def assertChannelIncludedInFrequencyRanges(self, channel, frequency_ranges):
    """Checks if the channel lies within the list of frequency ranges.

    Args:
      channel: A dictionary containing frequencyRange,
        which is a dictionary containing lowFrequency and highFrequency.
      frequency_ranges: A list of dictionaries containing
        lowFrequency and highFrequency.
    """
    is_frequency_included_in_range = False
    for frequency in frequency_ranges:
      if (channel['frequencyRange']['lowFrequency'] >= frequency['lowFrequency']
          and channel['frequencyRange']['highFrequency'] <=
          frequency['highFrequency']):
        is_frequency_included_in_range = True
        break
    self.assertTrue(is_frequency_included_in_range,
                    'Channel is not included in list of frequency ranges')

  def TriggerFullActivityDumpAndWaitUntilComplete(self, server_cert, server_key):
    request_time = datetime.utcnow().replace(microsecond=0)
    self._sas_admin.TriggerFullActivityDump()
    signal.signal(signal.SIGALRM,
                  lambda signum, frame:
                  (_ for _ in ()).throw(
                      Exception('Full Activity Dump Check Timeout')))
    # Timeout after 2 hours if it's not completed
    signal.alarm(7200)
    # Check generation date of full activity dump
    while True:
      dump_message = self._sas.GetFullActivityDump(server_cert, server_key)
      dump_time = datetime.strptime(dump_message['generationDateTime'],
                                    '%Y-%m-%dT%H:%M:%SZ')
      if request_time <= dump_time:
        break
      time.sleep(10)
    signal.alarm(0)
    return dump_message
