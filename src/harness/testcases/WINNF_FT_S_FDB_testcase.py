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

import json
import logging
import os
import random
import sas
import sas_testcase
from fake_db_server import  FakeDatabaseTestHarness 
from util import configurable_testcase, getOverlappingFrequency, writeConfig, writeDB, loadConfig, getRandomLatLongInPolygon


class FederalGovernmentDatabaseUpdateTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass


  def generate_FDB_1_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.1"""
    # Load device info
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    # Send grant request
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))

    frequency_f2_exz = { 'lowFrequency' : 3680000000,
                        'highFrequency' : 3690000000 
                       }
    fake_fcc_db = { 'name': 'Fake_FCC_DB',
                    'url': 'http://localhost:9090/fakedatabse/exclusionZone',
                    'databaseFile': 'fakedatabase/exclusion_zone_db.json'
                  }

    #Reading the Exclusion zone sample record 
    data = json.load(
      open(os.path.join('testcases', 'testdata', 'exz_record_0.json')))
    #Creating Exclusion zone database
    writeDB(fake_fcc_db['databaseFile'], data)

    #Getting a random point within the polygon 
    device_a['installationParam']['latitude'], device_a['installationParam']['longitude'] = getRandomLatLongInPolygon(data)
    device_a['installationParam']['latitude'] = round(device_a['installationParam']['latitude'],6)
    device_a['installationParam']['longitude'] = round(device_a['installationParam']['longitude'],6)

    #Frequency range of the grant is adjusted to partially or fully overlap the Exclusion zone frequency range. 
    grant_0['operationParam']['operationFrequencyRange']['lowFrequency'] =  data['zone']['features'][0]['properties']['freqrange']['lowFrequency']
    grant_0['operationParam']['operationFrequencyRange']['highFrequency'] = data['zone']['features'][0]['properties']['freqrange']['highFrequency']

    # Create the actual config.
    config = {
        'registrationRequest': [device_a],
        'grantRequest': [grant_0],
        'fake_fcc_db' : fake_fcc_db,
        'Exz_Frequency_F2': frequency_f2_exz
      }
    writeConfig(filename, config)


  @configurable_testcase(generate_FDB_1_default_config)
  def test_WINNF_FT_S_FDB_1(self, config_filename):
    """ Exclusion Zone Database Update"""
    config = loadConfig(config_filename)

    # Create fake database server
    self._fake_database_server = FakeDatabaseTestHarness( \
      config['fake_fcc_db']['url'], config['fake_fcc_db']['databaseFile'] )

    #Start fake database server
    self._fake_database_server.start()

    # Inject FCC ID and User Id of the device into UUT.    
    fcc_id = (config['registrationRequest'][0]['fccId'], 47) 
    user_id = config['registrationRequest'][0]['userId']

    self._sas_admin.InjectFccId({
      'fccId': fcc_id[0],
      'fccMaxEirp': fcc_id[1]
    })
    self._sas_admin.InjectUserId({'userId': user_id})

    cbsd_ids, grant_ids = self.assertRegisteredAndGranted(config['registrationRequest'], config['grantRequest'])
   
    #Loading the FCC database URL into the UUT, the database has a zone containing the CBSD location or is within 50 meters of the CBSD location
    self._sas_admin.InjectDatabaseUrl(config['fake_fcc_db']['url'])

    # Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    #Construct heartbeat message
    request = {
      'heartbeatRequest': [{
        'cbsdId': cbsd_ids[0],
        'grantId': grant_ids[0],
        'operationState': 'GRANTED'
      }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse'][0]
    
    # Check the heartbeat response code is 500(TERMINATED_GRANT) or 501 (SUSPENDED_GRANT) 
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    self.assertEqual(response['grantId'], grant_ids[0])
    self.assertIn(response['response']['responseCode'], [500, 501])

    #Sending the relinquishment request for the Grant if the response code was 501 for heartbeat response
    if response['response']['responseCode'] == 501 :
      # Relinquish grant1
      request = {
          'relinquishmentRequest': [{
            'cbsdId': cbsd_ids[0],
            'grantId': grant_ids[0]
          }]
        }
      response = self._sas.Relinquishment(request)['relinquishmentResponse'][0]
      # Check the relinquishment response
      self.assertEqual(response['cbsdId'], cbsd_ids[0])
      self.assertEqual(response['grantId'], grant_ids[0])
      self.assertIn(response['response']['responseCode'], 0)

    # Request grant with frequency range which partially or fully overlaps with Exclusion zone protected frequency range
    config['grantRequest'][0]['cbsdId'] = cbsd_ids[0]

    #Get an overlapping frequency range for the Exclusion zone Frequency (F1)
    freq_range = getOverlappingFrequency(\
      config['grantRequest'][0]['operationParam']['operationFrequencyRange']['lowFrequency'], \
      config['grantRequest'][0]['operationParam']['operationFrequencyRange']['highFrequency'] ) 
    
    logging.debug('Overlapping Frequency for F1')
    logging.debug("%d %d",freq_range[0],freq_range[1])
    
    config['grantRequest'][0]['operationParam']['operationFrequencyRange']['lowFrequency'] = freq_range[0]
    config['grantRequest'][0]['operationParam']['operationFrequencyRange']['highFrequency'] = freq_range[1]
    request = {'grantRequest': config['grantRequest']}

    # Check grant response should be 400 (INTERFERENCE).
    response = self._sas.Grant(request)['grantResponse'][0]
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    self.assertIn(response['response']['responseCode'], [400])
    del request, response

    # Load modified exclusion zone database(change frequency of protected zone)
    #Reading the fake database file.
    with open(config['fake_fcc_db']['databaseFile'], 'r') as f:  
      data =  json.loads(f.read())
    data['zone']['features'][0]['properties']['freqrange']['lowFrequency'] = config['Exz_Frequency_F2']['lowFrequency']
    data['zone']['features'][0]['properties']['freqrange']['highFrequency'] = config['Exz_Frequency_F2']['highFrequency']
 
    writeDB(config['fake_fcc_db']['databaseFile'], data)    

    # Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Request grant with frequency range which partially or fully overlaps with Exclusion zone protected frequency range
    freq_range = getOverlappingFrequency( \
      data['zone']['features'][0]['properties']['freqrange']['lowFrequency'], \
      data['zone']['features'][0]['properties']['freqrange']['highFrequency'] )

    logging.debug('Overlapping Frequency for F2')
    logging.debug("%d %d",freq_range[0],freq_range[1])    

    config['grantRequest'][0]['operationParam']['operationFrequencyRange']['lowFrequency'] = freq_range[0]
    config['grantRequest'][0]['operationParam']['operationFrequencyRange']['highFrequency'] = freq_range[1]
    request = {'grantRequest': config['grantRequest']}

    # Check grant response should be 400 (INTERFERENCE).
    response = self._sas.Grant(request)['grantResponse'][0]
    self.assertEqual(response['cbsdId'], cbsd_ids[0])
    self.assertIn(response['response']['responseCode'],[400])
    del request, response