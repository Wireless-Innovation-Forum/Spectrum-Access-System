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
from util import configurable_testcase, writeConfig, writeDB, loadConfig, getRandomLatLongInPolygon


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
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Load grant requests
    grant_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'grant_0.json')))

    # Dictionary containing database information
    fake_db_info = {'name': 'Fake_DB',
                    'url': 'http://localhost:9090/fakedatabase/exclusionZone',
                    'databaseFile': 'fakedatabase/exclusionZone/exclusion_zone_db.json'
                    }
    # Load the exclusion zone record
    exz_record = json.load(
      open(os.path.join('testcases', 'testdata', 'exz_record_0.json')))
    data = {'zone': exz_record
            }
    # Update frequency range('F1') of the exclusion zone.
    data['frequencyRange'] = {}
    data['frequencyRange']['lowFrequency'] = 3625000000
    data['frequencyRange']['highFrequency'] = 3635000000

    # Frequency range overlappig with 'F1'
    overlap_frequency_range_f1 = {'lowFrequency': 3575000000,
                                  'highFrequency': 3635000000
                                  }
    # Modify frequency range of exclusion zone from 'F1' to 'F2'
    frequency_range_f2 = {'lowFrequency': 3680000000,
                          'highFrequency': 3690000000
                          }
    # Frequency range overlapping with 'F2'
    overlap_frequency_range_f2 = {'lowFrequency': 3885000000,
                                  'highFrequency': 3695000000
                                  }


    # Getting a random point within the polygon
    device_a['installationParam']['latitude'],\
            device_a['installationParam']['longitude'] =\
            getRandomLatLongInPolygon(data)
    device_a['installationParam']['latitude'] =\
            round(device_a['installationParam']['latitude'], 6)
    device_a['installationParam']['longitude'] =\
            round(device_a['installationParam']['longitude'], 6)
    device_b['installationParam']['latitude'], \
            device_b['installationParam']['longitude'] =\
            getRandomLatLongInPolygon(data)
    device_b['installationParam']['latitude'] = \
            round(device_b['installationParam']['latitude'], 6)
    device_b['installationParam']['longitude'] = \
            round(device_b['installationParam']['longitude'], 6)

    # Frequency range of the grant is adjusted to partially
    # or fully overlap the Exclusion zone frequency range.
    grant_0['operationParam']['operationFrequencyRange']\
            ['lowFrequency'] = data['frequencyRange']['lowFrequency']
    grant_0['operationParam']['operationFrequencyRange']\
            ['highFrequency'] = data['frequencyRange']['highFrequency']
    grant_1['operationParam']['operationFrequencyRange']\
            ['lowFrequency'] = data['frequencyRange']['lowFrequency']
    grant_1['operationParam']['operationFrequencyRange']\
            ['highFrequency'] = data['frequencyRange']['highFrequency']

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

    conditionals = {'registrationData': conditional_parameters
                    }
    # Create the actual config.
    config = {
        'exzRecord': data,
        'registrationRequestC1': device_a,
        'registrationRequestC2': device_b,
        'grantRequestG1': grant_0,
        'grantRequestG2': grant_1,
        'conditionalRegistrationData': conditionals,
        'fakeDatabaseInfo': fake_db_info,
        'exzOverlapFrequencyRangeF1': overlap_frequency_range_f1,
        'exzOverlapFrequencyRangeF2': overlap_frequency_range_f2,
        'exzFrequencyRangeF2': frequency_range_f2
      }
    writeConfig(filename, config)


  @configurable_testcase(generate_FDB_1_default_config)
  def test_WINNF_FT_S_FDB_1(self, config_filename):
    """ Exclusion Zone Database Update"""
    config = loadConfig(config_filename)

    device_c1 = config['registrationRequestC1']
    device_c2 = config['registrationRequestC2']
    grant_g1 = config['grantRequestG1']
    grant_g2 = config['grantRequestG2']

    registration_requests = [device_c1, device_c2]
    grant_requests = [grant_g1, grant_g2]

    # Create Exclusion zone database
    writeDB(config['fakeDatabaseInfo']['databaseFile'], config['exzRecord'])

    # Create fake database server
    # Parse url to get host name, port number and path \
    # in order to send GET request to fake database server

    # The split() method returns a list of words in the \
    # string based on the separator ('/').
    # The join() method returns a string in which string \
    # elements are joined by a separator ('').
    path = ''.join(('/', config['fakeDatabaseInfo']['url'].split('/', 3)[3]))
    host_name = (config['fakeDatabaseInfo']['url'].split('/')[2]).split(':')[0]
    port = int((config['fakeDatabaseInfo']['url'].split('/')[2]).split(':')[1])

    fake_database_server = FakeDatabaseTestHarness(
      path, host_name, port,
      config['fakeDatabaseInfo']['databaseFile'])
    # Start fake database server
    fake_database_server.start()

    # Step 1: Inject FCC ID and User Id of the devices into UUT.
    for registration_request in registration_requests:
      self._sas_admin.InjectFccId({'fccId': registration_request['fccId']})
      self._sas_admin.InjectUserId({'userId': registration_request['userId']})

    # Pre-load conditional registration data for CBSDs.
    if ('conditionalRegistrationData' in config)\
      and (config['conditionalRegistrationData']):
      self._sas_admin.PreloadRegistrationData(
            config['conditionalRegistrationData'])

    # Register devices and request grants with SAS UUT.
    cbsd_ids, grant_ids = self.assertRegisteredAndGranted(registration_requests,
                                                          grant_requests)
    # Step 2: Loading the Exclusion Zone database URL into the UUT
    # The database has a zone that contains the CBSD location or
    # is within 50 meters of the CBSD location
    self._sas_admin.InjectDatabaseUrl(config['fakeDatabaseInfo']['url'])

    # Step 3: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 4: Sending Heartbeat Request
    # Construct heartbeat message
    request = {
      'heartbeatRequest': [{
        'cbsdId': cbsd_ids[0],
        'grantId': grant_ids[0],
        'operationState': 'GRANTED'
      }, {
        'cbsdId': cbsd_ids[1],
        'grantId': grant_ids[1],
        'operationState': 'GRANTED'
      }]
    }
    response = self._sas.Heartbeat(request)['heartbeatResponse']

    relq_request = {'relinquishmentRequest': []}
    for response_num, resp in enumerate(response):
      # Check the heartbeat response code is 500(TERMINATED_GRANT)
      # or 501 (SUSPENDED_GRANT)
      self.assertEqual(resp['grantId'], grant_ids[response_num])
      self.assertIn(resp['response']['responseCode'], [500, 501])

      # Step 5: Consolidating the relinquishment request for the Grants
      # if the responseCode was 501 for heartbeat response
      if resp['response']['responseCode'] == 501:
        # Update Relinquishment Request content
        content = {
             'cbsdId': cbsd_ids[response_num],
             'grantId': grant_ids[response_num]
        }
        relq_request['relinquishmentRequest'].append(content)

    # Send Consolidated Relinquishment Request for all the grants,
    # if the grant responseCode was 501
    if len(relq_request['relinquishmentRequest']) != 0:
        relq_response =\
          self._sas.Relinquishment(relq_request)['relinquishmentResponse']
        for relq_num, relq in enumerate(relq_response):
            # Check the relinquishment response
            self.assertEqual(relq['grantId'], grant_ids[relq_num])
            self.assertEqual(relq['response']['responseCode'], 0)

        del relq_request, relq_response

    del request, response

    # Step 6: Request grant with frequency range which partially or fully
    # overlaps with Exclusion zone protected frequency range 'F1'
    for grant_num in range(len(grant_requests)):
      grant_requests[grant_num]['cbsdId'] = cbsd_ids[grant_num]

    # Get an overlapping frequency range for the Exclusion zone Frequency
    # range(F1)
    for grant_num in range(len(grant_requests)):
      grant_requests[grant_num]['operationParam']['operationFrequencyRange']\
              ['lowFrequency'] = config['exzOverlapFrequencyRangeF1']['lowFrequency']
      grant_requests[grant_num]['operationParam']['operationFrequencyRange']\
              ['highFrequency'] = config['exzOverlapFrequencyRangeF1']['highFrequency']

    request = {'grantRequest': grant_requests}
    # Check grant response should be 400 (INTERFERENCE).
    response = self._sas.Grant(request)['grantResponse']

    for response_num, resp in enumerate(response):
      self.assertEqual(resp['response']['responseCode'], 400)
    del request, response

    # Step 7: Modify exclusion zone frequency range to 'F2'
    config['exzRecord']['frequencyRange']['lowFrequency'] =\
                 config['exzFrequencyRangeF2']['lowFrequency']
    config['exzRecord']['frequencyRange']['highFrequency'] =\
                 config['exzFrequencyRangeF2']['highFrequency']
    writeDB(config['fakeDatabaseInfo']['databaseFile'], config['exzRecord'])

    # Step 8: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 9: Request grant with frequency range which partially or fully
    # overlaps with Exclusion zone protected frequency range(F2)
    for grant_num in range(len(grant_requests)):
      grant_requests[grant_num]['operationParam']['operationFrequencyRange']\
              ['lowFrequency'] = config['exzOverlapFrequencyRangeF2']['lowFrequency']
      grant_requests[grant_num]['operationParam']['operationFrequencyRange']\
              ['highFrequency'] = config['exzOverlapFrequencyRangeF2']['highFrequency']

    request = {'grantRequest': grant_requests}
    # Check grant response should be 400 (INTERFERENCE).
    response = self._sas.Grant(request)['grantResponse']

    for response_num, resp in enumerate(response):
      self.assertEqual(resp['response']['responseCode'], 400)
    del request, response

    # As Python garbage collector is not very consistent, directory(file)
    # is not getting deleted.
    # Hence, explicitly stopping Database Test Harness and cleaning up.
    fake_database_server.shutdown()
    del fake_database_server
