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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime, timedelta
import logging
import threading
import time
import unittest
import six
from six.moves import zip

import sas
import util
from request_handler import HTTPError


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
    if not registration_request:
      return []
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

    self.assertEqual(len(response), len(registration_request))
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
    - Fails immediately if the status check returns HTTP 500 (or) if it gives
    *any other error code* 20 times in a row.
    - If the status is not changed within 24 hours it will throw an exception.
    """
    self._sas_admin.TriggerDailyActivitiesImmediately()
    # Timeout after 24 hours if it's not completed
    timeout = datetime.now() + timedelta(hours=24)
    # Check the Status of Daily Activities every 10 seconds
    error_counter = 0
    is_completed = False
    while not is_completed:
      try:
        is_completed = self._sas_admin.GetDailyActivitiesStatus()['completed']
        error_counter = 0
      except HTTPError as e:
        # Fail immediately if HTTP 500
        if e.error_code == 500:
          self.fail(
              'Got HTTP %d, indicating a fatal error during CPAS execution in'
              'SAS UUT. Failing immediately.'
              % e.error_code)
        else:
          logging.info('Got HTTP: %d ', e.error_code)
          error_counter += 1
          if error_counter == 20:
            self.fail('Encountered errors 20 times. Failing immediately.')
      # If any other error (including HTTP errors other than 500) 20 times in a
      # row, fail.
      except Exception as ex:
        logging.info('Exception: %s ', str(ex))
        error_counter += 1
        if error_counter == 20:
          self.fail('Encountered errors 20 times. Failing immediately.')
      self.assertLess(datetime.now(), timeout, 'Timeout during CPAS execution.')
      time.sleep(10)

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

  def assertChannelsOverlapFrequencyRange(self, channels, frequency_range,
                                          constrain_low=False, constrain_high=False):
    """Checks if the frequency range of all channels overlap
       the given frequency range.

    Args:
      channels: A list of dictionaries containing frequencyRange,
        which is a dictionary containing lowFrequency and highFrequency.
      frequency_range: A dictionary containing lowFrequency and highFrequency.
      constrain_low: A Boolean flag indicating if the lower frequency edge of the
        channel with the lowest frequency segment need to be constrained to be 
        equal to the lower frequency edge of the frequency range.
      constrain_high: A Boolean flag indicating if the upper frequency edge of the
        channel with the highest frequency segment need to be constrained to be 
        equal to the upper frequency edge of the frequency range.
    """
    channels.sort(
        key=
        lambda ch: (ch['frequencyRange']['lowFrequency'],
                    ch['frequencyRange']['highFrequency']),
        reverse=False)
    for index, channel in enumerate(channels):
      self.assertGreater(channel['frequencyRange']['highFrequency'],
                         frequency_range['lowFrequency'])
      if index == 0:
        if constrain_low:
          self.assertEqual(channel['frequencyRange']['lowFrequency'],
                           frequency_range['lowFrequency'])
        else:
          self.assertLessEqual(channel['frequencyRange']['lowFrequency'],
                               frequency_range['lowFrequency'])
      else:
        self.assertLessEqual(
            channel['frequencyRange']['lowFrequency'],
            channels[index - 1]['frequencyRange']['highFrequency'])

    for index, channel in enumerate(channels):
      self.assertLess(channel['frequencyRange']['lowFrequency'],
                      frequency_range['highFrequency'])
    channels.sort(
        key=lambda ch: (ch['frequencyRange']['highFrequency']), reverse=True)
    if constrain_high:
      self.assertEqual(channels[0]['frequencyRange']['highFrequency'],
                       frequency_range['highFrequency'])
    else:
      self.assertGreaterEqual(channels[0]['frequencyRange']['highFrequency'],
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

  def assertValidConfig(self, config, required_fields, optional_fields={}):
    """Does basic checking of a testing config.

    Checks that the given config contains the required fields of the correct
    type and present optional fields are the correct type.

    Args:
      config: The test configuration as a dictionary.
      required_fields: Dictionary of the required fields where the key is the
        field name and the value is the expected data type.
      optional_fields: Optional. Dictionary of the optional fields where the
        key is the field name and the value is the expected data type.

    Raises:
      AssertError: When the given config does not include the required and
      optional fields or the config contains unexpected keys.
    """
    def TypeName(a_type):
      """Returns the type name, even if multiple type (as tuple of types)."""
      try:
        return a_type.__name__
      except AttributeError:
        return a_type[0].__name__

    for key, field_type in six.iteritems(required_fields):
      self.assertTrue(key in config,
                      'Required config field \'%s\' is not present.' % key)
      self.assertTrue(
          isinstance(config[key], field_type),
          'Required config field \'%s\' is of type(%s) when it should be type(%s).'
          % (key, type(config[key]).__name__, TypeName(field_type)))
    for key, field_type in six.iteritems(optional_fields):
      if key in config:
        self.assertTrue(
            isinstance(config[key], field_type),
            'Optional config field \'%s\' is of type(%s) when it should be type(%s).'
            % (key, type(config[key]).__name__, TypeName(field_type)))
    # Check the config only contains the checked fields
    for key in config:
      self.assertTrue(
          key in required_fields or key in optional_fields,
          'Config field \'%s\' is neither required nor optional.' % key)

  def TriggerFullActivityDumpAndWaitUntilComplete(self, server_cert, server_key):
    request_time = datetime.utcnow().replace(microsecond=0)
    self._sas_admin.TriggerFullActivityDump()
    # Timeout after 2 hours if it's not completed
    timeout = datetime.now() + timedelta(hours=2)
    # Check generation date of full activity dump
    while True:
      try:
        dump_message = self._sas.GetFullActivityDump( server_cert, server_key)
        dump_time = datetime.strptime(dump_message['generationDateTime'],
                                               '%Y-%m-%dT%H:%M:%SZ')
        if request_time <= dump_time:
          break
      except AssertionError:
        pass
      self.assertLess(datetime.now(), timeout, 'Timeout during Full Activity Dump.')
      time.sleep(10)
    return dump_message

  def triggerPpaCreationAndWaitUntilComplete(self, ppa_creation_request):
    """Triggers PPA Creation Admin API and returns PPA ID if the creation status is completed.

    Triggers PPA creation to the SAS UUT. Checks the status of the PPA creation
    by invoking the PPA creation status API. If the status is complete then the
    PPA ID is returned. The status is checked every 10 seconds until it is completed.
    - Fails if it gives an error code 20 times in a row.
    - If the status is not changed within 2 hours it will throw an exception.

    Args:
      ppa_creation_request: A dictionary with a multiple key-value pair containing the
        "cbsdIds", "palIds" and optional "providedContour"(a GeoJSON object).

    Returns:
      A Return value is string format of the PPA ID.

    """
    ppa_id = self._sas_admin.TriggerPpaCreation(ppa_creation_request)

    # Verify ppa_id should not be None.
    self.assertIsNotNone(ppa_id, msg="PPA ID received from SAS UUT as result of "
                                     "PPA Creation is None")

    logging.info('TriggerPpaCreation is in progress')

    # Triggers most recent PPA Creation Status immediately and checks for the
    # status of activity every 10 seconds until it is completed. If the status
    # is not changed within 2 hours it will throw an exception.
    # Timeout after 2 hours if it's not completed.
    timeout = datetime.now() + timedelta(hours=2)

    # Check the Status of most recent ppa creation every 10 seconds.
    error_counter = 0
    is_completed = False
    while not is_completed:
      try:
        is_completed = self._sas_admin.GetPpaCreationStatus()['completed']
        error_counter = 0
      # If any error 20 times in a row, fail.
      except Exception as ex:
        logging.info('Exception: %s ', str(ex))
        error_counter += 1
        if error_counter == 20:
          self.fail('Encountered errors 20 times. Failing immediately.')
      self.assertLess(datetime.now(), timeout, 'Timeout during PPA creation.')
      time.sleep(10)

    # Additional check to ensure whether PPA creation status has error.
    self.assertFalse(self._sas_admin.GetPpaCreationStatus()['withError'],
                     msg='There was an error while creating PPA')

    return ppa_id

  def assertPpaCreationFailure(self, ppa_creation_request):
    """Trigger PPA Creation Admin API and asserts the failure response.

    Triggers PPA creation to the SAS UUT and handles exception received if the
    PPA creation returns error or times out.Checks the status of the PPA creation
    by invoking the PPA creation status API.If the status is complete then looks for
    withError set to True to declare ppa creation is failed. The status is checked
    every 10 secs for up to 2 hours.
    - Fails if it gives an error code 20 times in a row.
    - If the status is not changed within 2 hours it will throw an exception.

    Args:
      ppa_creation_request: A dictionary with a multiple key-value pair containing the
        "cbsdIds", "palIds" and optional "providedContour"(a GeoJSON object).

    Raises:
      Exception for the following cases:
         a. withError flag set to False even though most recent ppa creation
         status is completed.
         b. SAS UUT does not respond for longer time and timeout.
         c. SAS UUT responds with success response rather than failure response.

    """
    try:
      response = self._sas_admin.TriggerPpaCreation(ppa_creation_request)
    except HTTPError:
      # We are done if PPA creation failure is detected during TriggerPpaCreation.
      return

    logging.info('TriggerPpaCreation is in progress')

    timeout = datetime.now() + timedelta(hours=2)

    # Check the Status of most recent ppa creation every 10 seconds.
    error_counter = 0
    is_completed = False
    while not is_completed:
      try:
        is_completed = self._sas_admin.GetPpaCreationStatus()['completed']
        error_counter = 0
      # If any error 20 times in a row, fail.
      except Exception as ex:
        logging.info('Exception: %s ', str(ex))
        error_counter += 1
        if error_counter == 20:
          self.fail('Encountered errors 20 times. Failing immediately.')
      self.assertLess(datetime.now(), timeout, 'Timeout during PPA creation.')
      time.sleep(10)

    # Expect the withError flag in status response should be toggled on to True
    # to indicate PPA creation failure.
    self.assertTrue(self._sas_admin.GetPpaCreationStatus()['withError'],
                    msg='Expected:There is an error in create PPA. But '
                        'PPA creation status indicates no error')


  def ShutdownServers(self):
    logging.info('Stopping all running servers, if any')
    for thread in threading.enumerate():
      if 'shutdown' in dir(thread):
        logging.info('Stopping %s' % thread.name)
        thread.shutdown()

  def InjectTestHarnessFccIds(self, cbsd_records):
    logging.info('Injecting FCC IDs for CBSDs in the SAS test harness into the SAS UUT.')
    for cbsd_record in cbsd_records:
      self._sas_admin.InjectFccId({'fccId': cbsd_record['registration']['fccId']})
