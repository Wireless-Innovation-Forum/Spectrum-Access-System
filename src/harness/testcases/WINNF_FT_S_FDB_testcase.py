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
import os
import sas
import sas_testcase
from fake_db_server import FakeDatabaseTestHarness
from reference_models.examples import entities
from reference_models.geo import vincenty
from util import configurable_testcase, writeConfig, loadConfig


class FederalGovernmentDatabaseUpdateTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def generate_FDB_1_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.1"""

    # Load device info
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Dictionary containing database information
    fake_db_info = {'hostName': 'localhost',
                    'port': 9090
                    }

    # Load exclusion zone records
    exz_db_record_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'exz_db_record_0.json')))
        
    # Grant G1 Frequency range overlapping with 'F1'
    g1_overlap_frequency_range_f1 = {'lowFrequency': 3650000000,
                                  'highFrequency': 3700000000
                                  }

    # Grant G2 Frequency range overlapping with 'F1'
    g2_overlap_frequency_range_f1 = {'lowFrequency': 3650000000,
                                  'highFrequency': 3660000000
                                  }

    # Modify frequency range of exclusion zone from 'F1' to 'F2'
    frequency_range_f2 = {'lowFrequency': 3680000000,
                          'highFrequency': 3700000000
                          }
    # Grant G3 Frequency range overlapping with 'F2'
    g3_overlap_frequency_range_f2 = {'lowFrequency': 3680000000,
                                  'highFrequency': 3700000000
                                  }

    # Update the location 'X' of CBSD device to be within 50 meters of the 
    # exclusion zone.
    lat_b, long_b, _ = vincenty.GeodesicPoints(
      exz_db_record_0['features'][0]['geometry']['coordinates'][1],
      exz_db_record_0['features'][0]['geometry']['coordinates'][0],
      [0.02], 30)

    device_b['installationParam']['latitude'] = \
            round(lat_b[0], 6)
    device_b['installationParam']['longitude'] = \
            round(long_b[0], 6)

    # Creating conditionals for Cat B devices
    self.assertEqual(device_b['cbsdCategory'], 'B')
    conditional_parameters = {
        'cbsdCategory': device_b['cbsdCategory'],
        'fccId': device_b['fccId'],
        'cbsdSerialNumber': device_b['cbsdSerialNumber'],
        'airInterface': device_b['airInterface'],
        'installationParam': device_b['installationParam'],
        'measCapability': device_b['measCapability']
    }
    del device_b['cbsdCategory']
    del device_b['airInterface']
    del device_b['installationParam']
    del device_b['measCapability']

    conditionals = {
        'registrationData': conditional_parameters
      }
    # Create the actual config.
    config = {
        'exzDbRecord': [exz_db_record_0],
        'registrationRequest': device_b, 
        'conditionalRegistrationData': conditionals,
        'fakeDatabaseInfo': fake_db_info,
        'g1OverlapFrequencyRangeF1': g1_overlap_frequency_range_f1,
        'g2OverlapFrequencyRangeF1': g2_overlap_frequency_range_f1,
        'g3OverlapFrequencyRangeF2': g3_overlap_frequency_range_f2,
        'exzFrequencyRangeF2': frequency_range_f2
      }
    writeConfig(filename, config)

  @configurable_testcase(generate_FDB_1_default_config)
  def test_WINNF_FT_S_FDB_1(self, config_filename):
    """Exclusion Zone Database Update"""
    config = loadConfig(config_filename)

    device_c = config['registrationRequest']

    # Load grant request G1
    grant_g1 = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))

    # Update Grant G1 frequency range to partially/fully overlap 
    # with 'F1'
    grant_g1['operationParam']['operationFrequencyRange'] = config['g1OverlapFrequencyRangeF1']

    # Step 1: Inject FCC ID and User Id of the devices into UUT.
    self._sas_admin.InjectFccId({'fccId': device_c['fccId']})
    self._sas_admin.InjectUserId({'userId': device_c['userId']})

    # Pre-load conditional registration data for CBSD.
    if ('conditionalRegistrationData' in config)\
      and (config['conditionalRegistrationData']):
      self._sas_admin.PreloadRegistrationData(
          config['conditionalRegistrationData'])

    # Register device C and request grant G1 with SAS UUT.
    cbsd_ids, grant_ids = self.assertRegisteredAndGranted([device_c], [grant_g1])

    # Step 2: Loading the Exclusion Zone database URL into the UUT
    # The database has a zone that contains the CBSD location or
    # is within 50 meters of the CBSD location

    # Create fake database server
    fake_database_server = FakeDatabaseTestHarness(
                              config['fakeDatabaseInfo']['hostName'],
                              config['fakeDatabaseInfo']['port'])

    # Start fake database server
    fake_database_server.start()

    # Create Exclusion zone database
    fake_database_server.writeDatabaseFile(config['exzDbRecord'])

    database_url = fake_database_server.getBaseUrl()
    self._sas_admin.InjectDatabaseUrl(database_url)

    # Step 3: Trigger daily activities
    #self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 4: Sending Heartbeat Request
    # Construct heartbeat message
    heartbeat_request = {
      'heartbeatRequest': [{
        'cbsdId': cbsd_ids[0],
        'grantId': grant_ids[0],
        'operationState': 'GRANTED'
      }]
    }
    heartbeat_response = self._sas.Heartbeat(heartbeat_request)['heartbeatResponse'][0]

    # Check the heartbeat response code is 500(TERMINATED_GRANT)
    # or 501 (SUSPENDED_GRANT)
    self.assertEqual(heartbeat_response['grantId'], grant_ids[0])
    #self.assertIn(heartbeat_response['response']['responseCode'], [500, 501])

    # Step 5: Send the relinquishment request for the Grant
    # if the responseCode was 501 for heartbeat response
    if heartbeat_response['response']['responseCode'] == 501:
      # Relinquish the grant
      relq_request = { 
        'relinquishmentRequest': [{
          'cbsdId': cbsd_ids[0],
          'grantId': grant_ids[0]
          }]
        }  

      relq_response = self._sas.Relinquishment(relq_request)['relinquishmentResponse'][0]

      # Check the relinquishment response
      self.assertEqual(relq_response['grantId'], grant_ids[0])
      self.assertEqual(relq_response['response']['responseCode'], 0)

      del relq_request, relq_response

    del heartbeat_request, heartbeat_response

    # Step 6: Request grant G2 with another frequency range which partially or fully
    # overlaps with Exclusion zone protected frequency range 'F1'
    # Load grant request G2
    grant_g2 = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))

    # Update Grant G2 frequency range to partially/fully overlap 
    # with 'F1'
    grant_g2['operationParam']['operationFrequencyRange'] = config['g2OverlapFrequencyRangeF1']
    grant_g2['cbsdId'] = cbsd_ids[0]

    grant_request = {'grantRequest': [grant_g2]}

    # Check grant response should be 400 (INTERFERENCE).
    grant_response = self._sas.Grant(grant_request)['grantResponse'][0]
    #self.assertEqual(grant_response['response']['responseCode'], 400)

    del grant_request, grant_response

    # Step 7: Modify exclusion zone frequency range from 'F1' to 'F2'
    config['exzDbRecord'][0]['features'][0]['properties']['operationParam']\
        ['operationFrequencyRange'] = config['exzFrequencyRangeF2']
    fake_database_server.writeDatabaseFile(config['exzDbRecord'])

    # Step 8: Trigger daily activities
    #self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 9: Request grant G3 with frequency range which partially or fully
    # overlaps with Exclusion zone protected frequency range(F2)
    # Load grant request G3
    grant_g3 = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))

    # Update Grant G3 frequency range to partially/fully overlap 
    # with 'F2'
    grant_g3['operationParam']['operationFrequencyRange'] = config['g3OverlapFrequencyRangeF2']
    grant_g3['cbsdId'] = cbsd_ids[0]

    grant_request = {'grantRequest': [grant_g3]}

    # Check grant response should be 400 (INTERFERENCE).
    grant_response = self._sas.Grant(grant_request)['grantResponse'][0]
    #self.assertEqual(grant_response['response']['responseCode'], 400)

    del grant_request, grant_response

    # As Python garbage collector is not very consistent, directory(file)
    # is not getting deleted.
    # Hence, explicitly stopping Database Test Harness and cleaning up.
    #fake_database_server.shutdown()
    #del fake_database_server
