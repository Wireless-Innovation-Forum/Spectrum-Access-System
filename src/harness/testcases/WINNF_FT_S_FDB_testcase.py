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
from datetime import timedelta
import json
import logging
import os
import time

import sas
import sas_testcase
from util import winnforum_testcase,configurable_testcase, writeConfig, loadConfig, loadDB, getRandomLatLongInPolygon



class FederalGovernmentDatabaseUpdateTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass


  def generate_FDB_1_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.1"""
    # Load device info
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    # Send grant request
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))

    exclusion_zone_db = json.load(open(os.path.join('testcases', 'testdata', 'exclusion_zone_db.json')))

    # Create the actual config.
    config = {
        'fccIds': [(device_c['fccId'], 47)],
        'userIds': [device_c['userId']],
        'registrationRequests': [device_c],
        'grantRequests': [grant_0],
        'expectedResponseCodes': [0],
        'expectedGrantResponseCodes': [0,400],
        'expectedHBResponseCodes':[500,501],
        'expectedRelinquishResponseCodes':[0],
        'exclusion_zone_db':exclusion_zone_db

    }
    writeConfig(filename, config)


  @configurable_testcase(generate_FDB_1_default_config)
  def test_WINNF_FT_S_FDB_1(self, config_filename):
    """ Exclusion Zone Database Update"""
    
    #Reading the fake database file.
    data = loadDB("fakedatabase/exclusion_zone_db.json")
    #Getting a random point within the polygon 
    point = getRandomLatLongInPolygon(data['record_0'])

    config = loadConfig(config_filename)
    # Very light checking of the config file.
    self.assertEqual(
        len(config['registrationRequests']),
        len(config['expectedResponseCodes']))

    #Updating the latitude and the longitude in config file with the random point
    config['registrationRequests'][0]['installationParam']['latitude']= point[0]
    config['registrationRequests'][0]['installationParam']['longitude']= point[1]    
    writeConfig(config_filename, config)
    

    for fcc_id, max_eirp_dbm_per_10_mhz in config['fccIds']:
      self._sas_admin.InjectFccId({
        'fccId': fcc_id,
        'fccMaxEirp': max_eirp_dbm_per_10_mhz
      })

    for user_id in config['userIds']:
      self._sas_admin.InjectUserId({'userId': user_id})

    request = {'registrationRequest': config['registrationRequests']}
    responses = self._sas.Registration(request)['registrationResponse']
    # Check registration responses.
    cbsd_ids = []
    self.assertEqual(len(responses), len(config['registrationRequests']))
    for i in range(len(responses)):
      response = responses[i]
      expected_response_codes = config['expectedResponseCodes']
      logging.debug('Expecting to see response code in set %s in response: %s',
                      expected_response_codes, response)
      self.assertIn(response['response']['responseCode'],
                      expected_response_codes)
      if response['response']['responseCode'] == 0:  # SUCCESS
        self.assertTrue('cbsdId' in response)
        cbsd_ids.append(response['cbsdId'])
      else:
        self.assertFalse('cbsdId' in response)

    del request, responses
    config['grantRequests'][0]['cbsdId'] = cbsd_ids[0]
    request = {'grantRequest': config['grantRequests']}
    responses = self._sas.Grant(request)['grantResponse']
    # Check Grant responses.
    for i in range(len(responses)):
      response = responses[i]
      expected_response_codes = config['expectedGrantResponseCodes']
      logging.debug('Expecting to see response code in set %s in response: %s',
                      expected_response_codes, response)
      self.assertIn(response['response']['responseCode'],
                      expected_response_codes)
      if response['response']['responseCode'] == 0:  # SUCCESS
          self.assertTrue('cbsdId' in response)
          self.assertTrue('grantId' in response)
          grant_expire_time = datetime.strptime(response['grantExpireTime'],
                                                '%Y-%m-%dT%H:%M:%SZ')
      else:
          self.assertFalse('cbsdId' in response)
          self.assertFalse('grantId' in response)

    # Check grant response
    self.assertEqual(responses[0]['cbsdId'], cbsd_ids[0])
    grant_id = responses[0]['grantId']
    grant_expire_time = datetime.strptime(responses[0]['grantExpireTime'],
                                          '%Y-%m-%dT%H:%M:%SZ')
    del request, responses
    # Load exclusion zone database which includes a zone that contains the CBSD location or is within 50 meters of the CBSD location
    self._sas_admin.InjectDatabase_url(config['exclusion_zone_db'])

    # Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Response code 500(TERMINATED_GRANT)or 501 (SUSPENDED_GRANT) should be sent for Heartbeat Request
    request = {
      'heartbeatRequest': [{
        'cbsdId': cbsd_ids[0], 'grantId': grant_id, 'operationState': 'GRANTED'
      }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    # Check the heartbeat response
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    self.assertEqual(response['grantId'], grant_id)
    self.assertIn(response['response']['responseCode'], config['expectedHBResponseCodes'])
    # Relinquish grant1
    request = {
        'relinquishmentRequest': [{
          'cbsdId': cbsd_ids[0],
          'grantId': grant_id
        }]
      }
    response = self._sas.Relinquishment(request)['relinquishmentResponse'][0]
    # Check the relinquishment response
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    self.assertEqual(response['grantId'], grant_id)
    self.assertIn(response['response']['responseCode'], config['expectedRelinquishResponseCodes'])
    del request, response
    # Request grant with frequency range which partially or fully overlaps with Exclusion zone protected frequency range
    config['grantRequests'][0]['cbsdId'] = cbsd_ids[0]
    request = {'grantRequest': config['grantRequests']}
    config['grantRequests'][0]['operationParam']['operationFrequencyRange']['lowFrequency'] = 3670000000
    config['grantRequests'][0]['operationParam']['operationFrequencyRange']['highFrequency'] = 3680000000
    request = {'grantRequest':  config['grantRequests']}

    # Check grant response should be 400 (INTERFERENCE).
    response = self._sas.Grant(request)['grantResponse'][0]
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    self.assertIn(response['response']['responseCode'], config['expectedGrantResponseCodes'])
    del request, response

    # Load modified exclusion zone database(change frequency of protected zone)
    self._sas_admin.InjectDatabase_url(config['exclusion_zone_db'])

    # Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Request grant with frequency range which partially or fully overlaps with Exclusion zone protected frequency range
    config['grantRequests'][0]['operationParam']['operationFrequencyRange']['lowFrequency'] = 3670000000
    config['grantRequests'][0]['operationParam']['operationFrequencyRange']['highFrequency'] = 3680000000
    request = {'grantRequest': config['grantRequests']}

    # Check grant response should be 400 (INTERFERENCE).
    response = self._sas.Grant(request)['grantResponse'][0]
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    self.assertIn(response['response']['responseCode'],config['expectedGrantResponseCodes'])
    del request, response