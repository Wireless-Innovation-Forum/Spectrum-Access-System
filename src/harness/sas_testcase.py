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
"""Implementation of SasTestcaseInterface"""

import json
from jsonschema import validate, Draft4Validator, RefResolver
from datetime import datetime
import os
import logging
import unittest
import sas_interface
import sas
import signal
import time

import util

class SasTestCase(sas_interface.SasTestcaseInterface, unittest.TestCase):
  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def assertContainsRequiredFields(self, schema_filename, response):
    util.assertContainsRequiredFields(schema_filename, response)

  def assertValidResponseFormatForApprovedGrant(self, grant_response):
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
                       conditional_registration_data=None):
    for device in registration_request:
      self._sas_admin.InjectFccId({'fccId': device['fccId']})
      self._sas_admin.InjectUserId({'userId': device['userId']})
    if conditional_registration_data:
      self._sas_admin.PreloadRegistrationData(conditional_registration_data)

    # Pass the correct client cert and key in Registration request
    ssl_cert = self._sas._tls_config.client_cert
    ssl_key = self._sas._tls_config.client_key

    request = {'registrationRequest': registration_request}
    response = self._sas.Registration(request,ssl_cert=ssl_cert,ssl_key=ssl_key)['registrationResponse']

    # Check the registration response; collect CBSD IDs
    cbsd_ids = []
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      self.assertTrue('cbsdId' in resp)
      cbsd_ids.append(resp['cbsdId'])

    # Return list of cbsd_ids
    return cbsd_ids

  def assertRegisteredAndGranted(self, registration_request, grant_request,
                                 conditional_registration_data=None):
    self.assertEqual(len(registration_request), len(grant_request))
    cbsd_ids = self.assertRegistered(registration_request,
                                     conditional_registration_data)

    for cbsd_id, grant_req in zip(cbsd_ids, grant_request):
      grant_req['cbsdId'] = cbsd_id


    # Pass the correct client cert and key in Grant request
    ssl_cert = self._sas._tls_config.client_cert
    ssl_key = self._sas._tls_config.client_key

    grant_ids = []
    request = {'grantRequest': grant_request}
    grant_response = self._sas.Grant(request,ssl_cert=ssl_cert,ssl_key=ssl_key)['grantResponse']

    # Check the grant response
    for cbsd_id, grant_resp in zip(cbsd_ids, grant_response):
      self.assertEqual(grant_resp['cbsdId'], cbsd_id)
      self.assertTrue(grant_resp['grantId'])
      self.assertEqual(grant_resp['response']['responseCode'], 0)
      grant_ids.append(grant_resp['grantId'])

    # Return cbsd_ids and grant_ids
    return cbsd_ids, grant_ids

  def assertHeartbeatsSuccessful(self, cbsd_ids, grant_ids, operation_states):
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

    heartbeat_response = self._sas.Heartbeat({
      'heartbeatRequest': heartbeat_requests},ssl_cert=ssl_cert, ssl_key=ssl_key)['heartbeatResponse']

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
    self._sas_admin.TriggerDailyActivitiesImmediately()
    signal.signal(signal.SIGALRM,
                  lambda signum, frame:
                  (_ for _ in ()).throw(Exception('Daily Activity Check Timeout')))

    # Timeout after 2 hours if it's not completed
    signal.alarm(7200)
    # Check the Status of Daily Activities every 10 seconds
    while not self._sas_admin.GetDailyActivitiesStatus()['completed']:
      time.sleep(10)
    signal.alarm(0)
    
  def assertChannelsContainFrequencyRange(self, channels, frequency_range):
    channels.sort(key=lambda ch: (ch['frequencyRange']['lowFrequency'], ch['frequencyRange']['highFrequency']), reverse = False)
    for index, channel in  enumerate(channels):
        if index == 0:
           self.assertEqual(channel['frequencyRange']['lowFrequency'],\
             frequency_range['lowFrequency'])
        else:
            self.assertLessEqual(channel['frequencyRange']['lowFrequency'],
                                 channels[index - 1]\
                                 ['frequencyRange']['highFrequency'])
            
    channels.sort(key=lambda ch: (ch['frequencyRange']['highFrequency']), reverse = True)
    self.assertEqual(channels[0]['frequencyRange']['highFrequency'],\
             frequency_range['highFrequency'])

  def assertChannelIncludedInFrequencyRanges(self, channel, frequency_ranges):
    """Check if the channel lies within the list of frequency ranges.

    Args:
      channel: A dictionary containing frequencyRange,
               which is a dictionary containing lowFrequency and highFrequency
      frequency_ranges: A list of dictionaries containing
                        lowFrequency and highFrequency
    """
    isFrequencyIncludedInRange = False
    for frequency in frequency_ranges:
      if (channel['frequencyRange']['lowFrequency'] >= frequency['lowFrequency'] and
          channel['frequencyRange']['highFrequency'] <= frequency['highFrequency']):
        isFrequencyIncludedInRange = True
        break
    self.assertTrue(isFrequencyIncludedInRange, "Channel is not included in list of frequency ranges")

  def TriggerFullActivityDumpAndWaitUntilComplete(self, server_cert, server_key):
    request_time = datetime.utcnow().replace(microsecond=0)
    self._sas_admin.TriggerFullActivityDump()
    signal.signal(signal.SIGALRM,
                  lambda signum, frame:
                  (_ for _ in ()).throw(Exception('Full Activity Dump Check Timeout')))
    # Timeout after 2 hours if it's not completed
    signal.alarm(7200)
    # Check generation date of full activity dump 
    while True:
       dump_message = self._sas.GetFullActivityDump( server_cert, server_key)
       dump_time = datetime.strptime(dump_message['generationDateTime'],
                                               '%Y-%m-%dT%H:%M:%SZ')
       if request_time <= dump_time:
          break
       time.sleep(10)
    signal.alarm(0)
    return dump_message
