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
from datetime import datetime
from fake_db_server import FakeDatabaseTestHarness
from util import configurable_testcase, writeConfig, loadConfig, writeDB


class WINNFDatabaseUpdateTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def generate_WDB_1_default_config(self, filename):
    """Generates the WinnForum configuration for WDB.1"""
    # Load device info
    device_a = json.load(
      open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
      open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Dictionary containing database information
    fake_db_info = {'name': 'Fake_DB',
                    'url': 'http://localhost:9090/fakedatabase/pal',
                    'databaseFile': 'fakedatabase/pal/pal_db.json'
                    }

    # Load PAL Database record
    pal_record_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
    pal_record_1 = json.load(
      open(os.path.join('testcases', 'testdata', 'pal_record_1.json')))

    device_a['userId'] = pal_record_0['licensee']
    device_b['userId'] = pal_record_1['licensee']

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
    # Create the actual config file
    config = {
      'palRecord0': pal_record_0,
      'palRecord1': pal_record_1,
      'registrationRequestC1': device_a,
      'registrationRequestC2': device_b,
      'conditionalRegistrationData': conditionals,
      'fakeDatabaseInfo': fake_db_info
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_WDB_1_default_config)
  def test_WINNF_FT_S_WDB_1(self, config_filename):
    # Load the config file
    config = loadConfig(config_filename)

    device_c1 = config['registrationRequestC1']
    device_c2 = config['registrationRequestC2']
    pal_record_0 = config['palRecord0']
    pal_record_1 = config['palRecord1']

    registration_requests = [device_c1, device_c2]
    pal_records = [pal_record_0, pal_record_1]

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

    # Step 1: Send registration request
    # Inject FCC ID and User ID of the devices into UUT.
    for registration_request in registration_requests:
      self._sas_admin.InjectFccId({'fccId': registration_request['fccId']})
      self._sas_admin.InjectUserId({'userId': registration_request['userId']})

    # Pre-load conditional registration data for CBSDs.
    if ('conditionalRegistrationData' in config)\
      and (config['conditionalRegistrationData']):
      self._sas_admin.PreloadRegistrationData(
            config['conditionalRegistrationData'])

    # Register devices with SAS UUT.
    cbsd_ids = self.assertRegistered(registration_requests)

    # Step 2.1: Request PPA creation
    pal_ids = []
    for pal_record in pal_records:
      if ('palId'in pal_record) and (pal_record['palId']):
        pal_ids.append({"palId": pal_record['palId']})

    request = {
            "cbsdIds": cbsd_ids,
            "palIds": pal_ids
        }
    response = self._sas_admin.TriggerPpaCreation(request)

    # Validate PPA creation request is rejected
    self.assertEqual(response, None)
    del response

    # Step 2.2: Creating PAL database
    writeDB(config['fakeDatabaseInfo']['databaseFile'], pal_records)

    for index, pal_record in enumerate(pal_records):
      # Inject PAL records into SAS UUT
      self._sas_admin.InjectPalDatabaseRecord(pal_record)

    # Step 3: Admin Test Harness triggers CPAS
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 4: Request PPA creation
    response = self._sas_admin.TriggerPpaCreation(request)
    self.assertNotEqual(response, None)
    del request, response
    
    # As Python garbage collector is not very consistent, directory(file)
    # is not getting deleted.
    # Hence, explicitly stopping Database Test Harness and cleaning up.
    fake_database_server.shutdown()
    del fake_database_server
