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

import common_strings
import json
import logging
import os
from datetime import date, datetime, time, timedelta
from pytz import timezone
from time import sleep, strftime, gmtime

from six.moves import zip

import sas
import sas_testcase
from database import DatabaseServer
from util import configurable_testcase, writeConfig, loadConfig, \
  addCbsdIdsToRequests, getFqdnLocalhost, getUnusedPort,getCertFilename, json_load

# Time zone in which CPAS is scheduled
CPAS_TIME_ZONE = 'US/Pacific'

# CPAS_START_TIME indicates the schedule start time(24 hours format)
CPAS_START_TIME = 2

# CPAS_END_TIME corresponds to the time(24 hours format) "T3 + 300 seconds"
# as defined in the WinnForum CPAS policy doc.
CPAS_END_TIME = 4


class FederalGovernmentDatabaseUpdateTestcase(sas_testcase.SasTestCase):
  """SAS federal government database update test cases"""

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    self.ShutdownServers()

  def generate_FDB_1_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.1"""

    # Load devices info
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))

    # Exclusion zone database test harness configuration
    exclusion_zone_database_config = {
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'fileUrl': '/db_sync',
        'filePath': os.path.join('testcases', 'testdata', 'fdb_1', 'FDB_1_ground_based_exclusion_zones.kml'),
        'modifiedFilePath': os.path.join('testcases', 'testdata', 'fdb_1', 'modified_FDB_1_ground_based_exclusion_zones.kml')
    }

    # Load grant requests.
    grant_g1_a = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the exclusion zone
    # 'Yuma Proving Ground' frequency range 'F1'.
    grant_g1_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3640000000,
        'highFrequency': 3650000000
    }
    grant_g2_a = grant_g1_a
    grant_g3_a = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the exclusion zone
    # 'Yuma Proving Ground' frequency range 'F1'.
    grant_g3_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3550000000,
        'highFrequency': 3560000000
    }
    grant_g1_b = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the exclusion zone
    # 'Yakima Firing Center' frequency range 'F1'.
    grant_g1_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3550000000,
        'highFrequency': 3560000000
    }
    grant_g2_b = grant_g1_b
    grant_g3_b = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the exclusion zone
    # 'Yakima Firing Center' frequency range 'F1'.
    grant_g3_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3640000000,
        'highFrequency': 3650000000
    }

    # Update the location 'X' of CBSD devices contained witin the exclusion zones
    # 'Yuma Proving Ground'
    device_a['installationParam']['latitude'] = 33.01805
    device_a['installationParam']['longitude'] = -114.25253
    # 'Yakima Firing Center'
    device_b['installationParam']['latitude'] = 46.67553
    device_b['installationParam']['longitude'] = -120.43033

    # Creating conditionals for Cat B devices
    self.assertEqual(device_b['cbsdCategory'], 'B')
    conditionals_b = {
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

    conditionals = [conditionals_b]

    # Create the actual config.
    config = {
        'registrationRequests': [device_a, device_b],
        'grantRequests': [
            [grant_g1_a, grant_g1_b],
            [grant_g2_a, grant_g2_b],
            [grant_g3_a, grant_g3_b]],
        'conditionalRegistrationData': conditionals,
        'exclusionZoneDatabaseConfig': exclusion_zone_database_config
      }
    writeConfig(filename, config)

  @configurable_testcase(generate_FDB_1_default_config)
  def test_WINNF_FT_S_FDB_1(self, config_filename):
    """Exclusion Zone Database Update"""

    # Load the configuration file
    config = loadConfig(config_filename)

    # Very light checking of the config file.
    self.assertEqual(len(config['grantRequests']), 3)
    for grant_bundle in config['grantRequests']:
      self.assertEqual(len(grant_bundle), len(config['registrationRequests']))

    # Step 1: Registration of CBSDs and requesting for grants.
    # Forming of 'G1' grants for all the configured grants
    grant_request_g1 = config['grantRequests'][0]

    # Register device(s) 'C' and request grant 'G1' with SAS UUT.
    try:
      cbsd_ids, grant_ids = self.assertRegisteredAndGranted(
          config['registrationRequests'], grant_request_g1,
          config['conditionalRegistrationData'])
    except Exception:
      logging.error(common_strings.EXPECTED_SUCCESSFUL_REGISTRATION_AND_GRANT)
      raise

    # Step 2: Create exclusion zone database which contains the
    # CBSD location 'X' or is within 50 meters of the CBSD location 'X'.
    # Create exclusion zone database server
    exclusion_zone_database_server = DatabaseServer("Exclusion Zone Database",
                                          config['exclusionZoneDatabaseConfig']['hostName'],
                                          config['exclusionZoneDatabaseConfig']['port'])

    # Start exclusion zone database server
    exclusion_zone_database_server.start()

    # Set file path
    exclusion_zone_database_server.setFileToServe(config['exclusionZoneDatabaseConfig']['fileUrl'],
                                        config['exclusionZoneDatabaseConfig']['filePath'])

    # Inject the exclusion zone database URL into the SAS UUT
    self._sas_admin.InjectDatabaseUrl({'type': 'EXCLUSION_ZONE', 'url': exclusion_zone_database_server.getBaseUrl()+
                                       config['exclusionZoneDatabaseConfig']['fileUrl']})

    # Step 3: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 4: Sending Heartbeat Request
    # Construct heartbeat message
    heartbeat_requests = {'heartbeatRequest': []}
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
      heartbeat_requests['heartbeatRequest'].append({
        'cbsdId': cbsd_id,
        'grantId': grant_id,
        'operationState': 'GRANTED'
      })
    heartbeat_responses = self._sas.Heartbeat(heartbeat_requests)['heartbeatResponse']

    relq_requests = {'relinquishmentRequest': []}
    for resp in heartbeat_responses:
      # Check the heartbeat response code is 500(TERMINATED_GRANT)
      # or 501 (SUSPENDED_GRANT)
      self.assertIn(resp['response']['responseCode'], [500, 501])

      # Step 5: Consolidating the relinquishment request for the Grants
      # if the responseCode was 501 for heartbeat response
      if resp['response']['responseCode'] == 501:
        # Update Relinquishment Request content
        relq_requests['relinquishmentRequest'].append({
             'cbsdId': resp['cbsdId'],
             'grantId': resp['grantId']
        })

    # Send Consolidated Relinquishment Request for all the grants,
    # if the grant responseCode was 501
    if len(relq_requests['relinquishmentRequest']) != 0:
        relq_responses = self._sas.Relinquishment(relq_requests)['relinquishmentResponse']
        self.assertEqual(len(relq_responses), len(relq_requests['relinquishmentRequest']))
        for relq_resp in relq_responses:
          # Check the relinquishment response
          self.assertEqual(relq_resp['response']['responseCode'], 0)

        del relq_requests, relq_responses

    del heartbeat_requests, heartbeat_responses

    # Step 6: Request grant 'G2' with another frequency range which partially or fully
    # overlaps with Exclusion zone protected frequency range 'F1'.
    # Forming of 'G2' grants for all the configured grants
    addCbsdIdsToRequests(cbsd_ids, config['grantRequests'][1])
    grant_request_g2 = {'grantRequest': config['grantRequests'][1]}

    # Send grant request 'G2'
    grant_response_g2 = self._sas.Grant(grant_request_g2)['grantResponse']
    self.assertEqual(len(grant_response_g2), len(grant_request_g2['grantRequest']))

    # Check grant response,
    # responseCode should be 400 (INTERFERENCE).
    for resp in grant_response_g2:
      self.assertEqual(resp['response']['responseCode'], 400)

    del grant_request_g2, grant_response_g2

    # Step 7: Modify exclusion zone database record frequency range from 'F1' to 'F2'
    # Set the path of modified file
    exclusion_zone_database_server.setFileToServe(config['exclusionZoneDatabaseConfig']['fileUrl'],
                                        config['exclusionZoneDatabaseConfig']['modifiedFilePath'])

    # Step 8: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 9: Request grant 'G3' with frequency range which partially or fully
    # overlaps with Exclusion zone protected frequency range 'F2'.
    # Forming of 'G3' grants for all the configured grants
    addCbsdIdsToRequests(cbsd_ids, config['grantRequests'][2])
    grant_request_g3 = {'grantRequest': config['grantRequests'][2]}

    # Send grant request 'G3'
    grant_response_g3 = self._sas.Grant(grant_request_g3)['grantResponse']
    self.assertEqual(len(grant_response_g3), len(grant_request_g3['grantRequest']))

    # Check grant response,
    # responseCode should be 400 (INTERFERENCE).
    for resp in grant_response_g3:
      self.assertEqual(resp['response']['responseCode'], 400)

    del grant_request_g3, grant_response_g3

  def generate_FDB_2_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.2"""

    # Load devices info
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))

    # DPA database test harness configuration
    dpa_database_config = {
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'fileUrl': '/db_sync',
        'filePath': os.path.join('testcases', 'testdata', 'fdb_2', 'FDB_2_Portal_DPAs.kml'),
        'modifiedFilePath': os.path.join('testcases', 'testdata', 'fdb_2', 'modified_FDB_2_Portal_DPAs.kml')
    }

    # Load grant requests
    grant_g1_a = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the DPA 'BATH' which is 3500-3650 MHz.
    grant_g1_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3640000000,
        'highFrequency': 3650000000
    }
    grant_g2_a = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the DPA 'BATH' which is 3500-3650 MHz.
    grant_g2_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3615000000,
        'highFrequency': 3625000000
    }
    grant_g3_a = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the modified DPA 'BATH' which is 3500-3700 MHz.
    grant_g3_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3575000000,
        'highFrequency': 3585000000
    }

    grant_g1_b = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the DPA 'China Lake' which is 3500-3650 MHz.
    grant_g1_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3630000000,
        'highFrequency': 3640000000
    }
    grant_g2_b = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the DPA 'China Lake' which is 3500-3650 MHz.
    grant_g2_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3645000000,
        'highFrequency': 3655000000
    }
    grant_g3_b = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the modified DPA 'China Lake' which is 3500-3700 MHz.
    grant_g3_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3575000000,
        'highFrequency': 3585000000
    }

    # Update the location 'X' of CBSD devices to be near DPAs
    # 'BATH'
    device_a['installationParam']['latitude'] = 43.906455
    device_a['installationParam']['longitude'] = -69.813888
    # 'China Lake'
    device_b['installationParam']['latitude'] = 37.11318
    device_b['installationParam']['longitude'] = -116.84714

    # Creating conditionals for Cat B devices
    self.assertEqual(device_b['cbsdCategory'], 'B')
    conditionals_b = {
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

    conditionals = [conditionals_b]

    # Create the actual config.
    config = {
        'registrationRequests': [device_a, device_b],
        'grantRequests': [
            [grant_g1_a, grant_g1_b],
            [grant_g2_a, grant_g2_b],
            [grant_g3_a, grant_g3_b]],
        'conditionalRegistrationData': conditionals,
        'dpaDatabaseConfig': dpa_database_config
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_FDB_2_default_config)
  def test_WINNF_FT_S_FDB_2(self, config_filename):
    """DPA Database Update for DPAs which cannot be monitored by an ESC."""

    # Load the configuration file
    config = loadConfig(config_filename)

    # Very light checking of the config file.
    self.assertEqual(len(config['grantRequests']), 3)
    for grant_bundle in config['grantRequests']:
      self.assertEqual(len(grant_bundle), len(config['registrationRequests']))

    # Step 1: Registration of CBSDs and requesting for grants.
    # Forming of 'G1' grants for all the configured grants
    grant_request_g1 = config['grantRequests'][0]

    # Register device(s) 'C' and request grant 'G1' with SAS UUT.
    try:
      cbsd_ids, grant_ids = self.assertRegisteredAndGranted(
          config['registrationRequests'], grant_request_g1,
          config['conditionalRegistrationData'])
    except Exception:
      logging.error(common_strings.EXPECTED_SUCCESSFUL_REGISTRATION_AND_GRANT)
      raise

    # Step 2: Create DPA database which includes at least one inland DPA
    # Create DPA database server
    dpa_database_server = DatabaseServer("DPA Database",
                                          config['dpaDatabaseConfig']['hostName'],
                                          config['dpaDatabaseConfig']['port'])

    # Start DPA database server
    dpa_database_server.start()

    # Set file path
    dpa_database_server.setFileToServe(config['dpaDatabaseConfig']['fileUrl'],
                                        config['dpaDatabaseConfig']['filePath'])

    # Inject the DPA database URL into the SAS UUT
    self._sas_admin.InjectDatabaseUrl({'type': 'SCHEDULED_DPA', 'url': dpa_database_server.getBaseUrl()+
                                       config['dpaDatabaseConfig']['fileUrl']})

    # Step 3: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 4: Sending Heartbeat Request
    # Construct heartbeat message
    heartbeat_requests = {'heartbeatRequest': []}
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
      heartbeat_requests['heartbeatRequest'].append({
        'cbsdId': cbsd_id,
        'grantId': grant_id,
        'operationState': 'GRANTED'
      })
    heartbeat_responses = self._sas.Heartbeat(heartbeat_requests)['heartbeatResponse']

    relq_requests = {'relinquishmentRequest': []}
    for resp in heartbeat_responses:
      # Check the heartbeat response code is 500(TERMINATED_GRANT)
      # or 501 (SUSPENDED_GRANT)
      self.assertIn(resp['response']['responseCode'], [500, 501])

      # Step 5: Consolidating the relinquishment request for the Grants
      # if the responseCode was 501 for heartbeat response
      if resp['response']['responseCode'] == 501:
        # Update Relinquishment Request content
        relq_requests['relinquishmentRequest'].append({
             'cbsdId': resp['cbsdId'],
             'grantId': resp['grantId']
        })

    # Send Consolidated Relinquishment Request for all the grants,
    # if the grant responseCode was 501
    if len(relq_requests['relinquishmentRequest']) != 0:
      relq_responses = self._sas.Relinquishment(relq_requests)['relinquishmentResponse']
      self.assertEqual(len(relq_responses), len(relq_requests['relinquishmentRequest']))

      # Check the relinquishment response
      for relq_resp in relq_responses:
        self.assertEqual(relq_resp['response']['responseCode'], 0)

      del relq_requests, relq_responses

    del heartbeat_requests, heartbeat_responses

    # Step 6: Request grant 'G2' with frequency range which partially or fully
    # overlaps with DPA protected frequency range 'F1'.
    # Forming of 'G2' grants for all the configured grants
    addCbsdIdsToRequests(cbsd_ids, config['grantRequests'][1])
    grant_request_g2 = {'grantRequest': config['grantRequests'][1]}

    # Send grant request 'G2'
    grant_response_g2 = self._sas.Grant(grant_request_g2)['grantResponse']
    self.assertEqual(len(grant_response_g2), len(grant_request_g2['grantRequest']))

    # Check grant response,
    # responseCode should be either 400 (INTERFERENCE) or 0 (SUCCESS).
    heartbeat_requests = {'heartbeatRequest': []}
    for resp in grant_response_g2:
      self.assertIn(resp['response']['responseCode'], [0, 400])

      # Consolidating the heartbeat request for the Grant 'G2'
      # if the responseCode was 0 in grant response
      if resp['response']['responseCode'] == 0:
        # Update heartbeat request content
        heartbeat_requests['heartbeatRequest'].append({
            'cbsdId': resp['cbsdId'],
            'grantId': resp['grantId'],
            'operationState': 'GRANTED'
        })

    # Send Heartbeat Request for grant 'G2'
    if len(heartbeat_requests['heartbeatRequest']) != 0:
      heartbeat_responses = self._sas.Heartbeat(heartbeat_requests)['heartbeatResponse']
      self.assertEqual(len(heartbeat_responses), len(heartbeat_requests['heartbeatRequest']))

      # Step 7: Send Relinquishment Request for grant 'G2'
      relq_requests = {'relinquishmentRequest': []}

      # Check the heartbeat response code is 501 (SUSPENDED_GRANT)
      for resp in heartbeat_responses:
        self.assertEqual(resp['response']['responseCode'], 501)
        # Consolidating the relinquishment request for the Grants
        relq_requests['relinquishmentRequest'].append({
          'cbsdId': resp['cbsdId'],
          'grantId': resp['grantId']
        })

      relq_responses = self._sas.Relinquishment(relq_requests)['relinquishmentResponse']

      # Check the relinquishment response
      self.assertEqual(len(relq_responses), len(relq_requests['relinquishmentRequest']))
      for relq_resp in relq_responses:
        self.assertEqual(relq_resp['response']['responseCode'], 0)

      del relq_requests, relq_responses
      del heartbeat_requests, heartbeat_responses

    del grant_request_g2, grant_response_g2

    # Step 8: Modify DPA database record frequency range from 'F1' to 'F2'
    # Set the path of modified file
    dpa_database_server.setFileToServe(config['dpaDatabaseConfig']['fileUrl'],
                                        config['dpaDatabaseConfig']['modifiedFilePath'])

    # Step 9: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 10: Request grant 'G3' with frequency range which partially or fully
    # overlaps with DPA protected frequency range 'F2'.
    # Forming of 'G3' grants for all the configured grants
    addCbsdIdsToRequests(cbsd_ids, config['grantRequests'][2])
    grant_request_g3 = {'grantRequest': config['grantRequests'][2]}

    # Send grant request 'G3'
    grant_response_g3 = self._sas.Grant(grant_request_g3)['grantResponse']
    self.assertEqual(len(grant_response_g3), len(grant_request_g3['grantRequest']))

    # Check grant response,
    # responseCode should be either 400 (INTERFERENCE) or 0 (SUCCESS).
    heartbeat_requests = {'heartbeatRequest': []}
    for resp in grant_response_g3:
      self.assertIn(resp['response']['responseCode'], [0, 400])

      # Consolidating the heartbeat request for the Grant 'G3'
      # if the responseCode was 0 in grant response
      if resp['response']['responseCode'] == 0:
        # Update heartbeat request content
        heartbeat_requests['heartbeatRequest'].append({
            'cbsdId': resp['cbsdId'],
            'grantId': resp['grantId'],
            'operationState': 'GRANTED'
        })

    # Send Heartbeat Request for grant 'G3'
    if len(heartbeat_requests['heartbeatRequest']) != 0:
      heartbeat_responses = self._sas.Heartbeat(heartbeat_requests)['heartbeatResponse']
      self.assertEqual(len(heartbeat_responses), len(heartbeat_requests['heartbeatRequest']))

      # Check the heartbeat response code is 501 (SUSPENDED_GRANT)
      for resp in heartbeat_responses:
        self.assertEqual(resp['response']['responseCode'], 501)

      del heartbeat_requests, heartbeat_responses

    del grant_request_g3, grant_response_g3

  def generate_FDB_3_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.3"""

    # Load devices info
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))

    # Load grant requests
    grant_g_b = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_g_a = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the Respective FSSes.
    grant_g_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }
    grant_g_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }

    device_b['installationParam']['latitude'] = 39.2291
    device_b['installationParam']['longitude'] = -100.1
    device_b['installationParam']['antennaBeamwidth'] = 0
    device_a['installationParam']['latitude'] = 39.7355
    device_a['installationParam']['longitude'] = -107.9575
    device_a['installationParam']['antennaBeamwidth'] = 0

    # Pre-load conditionals and remove reg conditional fields from registration
    # request.
    conditional_keys = [
        'cbsdCategory', 'fccId', 'cbsdSerialNumber', 'airInterface',
        'installationParam', 'measCapability'
    ]
    reg_conditional_keys = [
        'cbsdCategory', 'airInterface', 'installationParam', 'measCapability'
    ]
    conditionals_a = {key: device_a[key] for key in conditional_keys}
    device_a = {
        key: device_a[key]
        for key in device_a
        if key not in reg_conditional_keys
    }
    conditionals_b = {key: device_b[key] for key in conditional_keys}
    device_b = {
        key: device_b[key]
        for key in device_b
        if key not in reg_conditional_keys
    }

    fss_database_config = {
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'fileUrl': '/rest/fss/v1/allsitedata',
        'filePath': os.path.join('testcases', 'testdata', 'fdb_3', 'FDB_3_default_allsitedata')
    }

    # Create the actual config.
    config = {
        'registrationRequests': [device_a, device_b],
        'grantRequests': [grant_g_a, grant_g_b],
        'conditionalRegistrationData': [conditionals_a, conditionals_b],
        'fssDatabaseConfig': fss_database_config
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_FDB_3_default_config)
  def test_WINNF_FT_S_FDB_3(self, config_filename):
    """FSS Database Update: Adding an FSS Site.

    Checks SAS UUT responds with Heartbeat Response 500 (TERMINATED_GRANT) for
    CBSD location X near FSS site
    """

    # Load the configuration file
    config = loadConfig(config_filename)

    # Very light checking of the config file.
    self.assertEqual(len(config['registrationRequests']),
                     len(config['grantRequests']))

    # Step 1: Registration of CBSDs and requesting for grants.
    # Forming of 'G' grants for all the configured grants
    grant_request_g = config['grantRequests']

    # Register device(s) 'C' and request grant 'G' with SAS UUT.
    try:
      cbsd_ids, grant_ids = self.assertRegisteredAndGranted(
          config['registrationRequests'], grant_request_g,
          config['conditionalRegistrationData'])
    except Exception:
      logging.error(common_strings.EXPECTED_SUCCESSFUL_REGISTRATION_AND_GRANT)
      raise

    # Step 2: Create FSS database which includes atleast one FSS site near location 'X'.
    fss_database = DatabaseServer(
        'FSS Database',
        config['fssDatabaseConfig']['hostName'],
        config['fssDatabaseConfig']['port'],
        authorization=True)

    fss_database.start()

    fss_database.setFileToServe(
        config['fssDatabaseConfig']['fileUrl'],
        config['fssDatabaseConfig']['filePath'])

    # Inject the FSS database URL into the SAS UUT
    self._sas_admin.InjectDatabaseUrl({'type': 'FSS', 'url': fss_database.getBaseUrl() + config['fssDatabaseConfig']['fileUrl']})

    # Step 3: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 4: Sending Heartbeat Request
    # Construct heartbeat message
    heartbeat_requests = {'heartbeatRequest': []}
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
      heartbeat_requests['heartbeatRequest'].append({
        'cbsdId': cbsd_id,
        'grantId': grant_id,
        'operationState': 'GRANTED'
      })
    heartbeat_responses = self._sas.Heartbeat(heartbeat_requests)['heartbeatResponse']

    # Check the heartbeat response code is 500(TERMINATED_GRANT)
    for resp in heartbeat_responses:
      self.assertEqual(resp['response']['responseCode'], 500)

    del heartbeat_requests, heartbeat_responses

  def generate_FDB_4_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.4"""

    # Load devices info
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))

    # FSS database test harness configuration
    fss_database_config = {
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'fileUrl': '/db_sync',
        'filePath': os.path.join('testcases', 'testdata', 'fdb_4', 'FDB_4_default_allsitedata.json'),
        'modifiedFilePath': os.path.join('testcases', 'testdata', 'fdb_4', 'modified_FDB_4_default_allsitedata.json')
    }

    # Load grant requests
    grant_g1_a = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the FSS frequency range which is 3650-4200 MHz.
    grant_g1_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }
    grant_g2_a = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the FSS frequency range which is 3650-4200 MHz.
    grant_g2_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3675000000,
        'highFrequency': 3685000000
    }

    grant_g1_b = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the FSS frequency range which is 3650-4200 MHz.
    grant_g1_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3660000000,
        'highFrequency': 3670000000
    }
    grant_g2_b = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the FSS frequency range which is 3650-4200 MHz.
    grant_g2_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3685000000,
        'highFrequency': 3695000000
    }

    # Update the location 'X' of CBSD devices to be near FSS sites
    # with FSS Number 'FSS0001010'
    device_a['installationParam']['latitude'] = 39.7355
    device_a['installationParam']['longitude'] = -107.9575
    device_a['installationParam']['antennaBeamwidth'] = 0
    # with FSS Number 'FSS0002010'
    device_b['installationParam']['latitude'] = 35.51043
    device_b['installationParam']['longitude'] = -100.27183

    # Creating conditionals for Cat B devices
    self.assertEqual(device_b['cbsdCategory'], 'B')
    conditionals_b = {
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

    conditionals = [conditionals_b]

    # Create the actual config.
    config = {
        'registrationRequests': [device_a, device_b],
        'grantRequests': [
            [grant_g1_a, grant_g1_b],
            [grant_g2_a, grant_g2_b]],
        'expectedResponseCodes': [
            [(0, ), (0,501)],
            [(501, ), (501, )]],
        'conditionalRegistrationData': conditionals,
        'fssDatabaseConfig': fss_database_config
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_FDB_4_default_config)
  def test_WINNF_FT_S_FDB_4(self, config_filename):
    """FSS Database Update: FSS Site Modification.

    Check SAS UUT responds with HeartbeatResponse either SUCCESS or
    SUSPENDED_GRANT for CBSD C's location X near FSS site before and
    after FSS database record modification.
    """

    # Load the configuration file
    config = loadConfig(config_filename)

    # Very light checking of the config file.
    self.assertEqual(len(config['grantRequests']), 2)
    for grant_bundle in config['grantRequests']:
      self.assertEqual(len(grant_bundle), len(config['registrationRequests']))

    # Step 1: Register device(s) 'C' (at location 'X') with conditional registration data
    try:
      cbsd_ids = self.assertRegistered(config['registrationRequests'],
                                      config['conditionalRegistrationData'])
    except Exception:
      logging.error(common_strings.EXPECTED_SUCCESSFUL_REGISTRATION)
      raise

    # Step 2: Create FSS database which includes atleast one FSS site near location 'X'.
    # Create FSS database server
    fss_database_server = DatabaseServer(
      'FSS Database',
      config['fssDatabaseConfig']['hostName'],
      config['fssDatabaseConfig']['port'],
      authorization=True)

    # Start FSS database server
    fss_database_server.start()

    # Set file path
    fss_database_server.setFileToServe(config['fssDatabaseConfig']['fileUrl'],
                                        config['fssDatabaseConfig']['filePath'])

    # Inject the FSS database URL into the SAS UUT
    self._sas_admin.InjectDatabaseUrl({'type': 'FSS', 'url': fss_database_server.getBaseUrl()+
                                       config['fssDatabaseConfig']['fileUrl']})

    # Step 3: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 4: Send Grant Request 'G1'
    # Forming of 'G1' grants for all the configured grants
    addCbsdIdsToRequests(cbsd_ids, config['grantRequests'][0])
    grant_request_g1 = {'grantRequest': config['grantRequests'][0]}

    # Send grant request 'G1'
    grant_response_g1 = self._sas.Grant(grant_request_g1)['grantResponse']

    # Check grant 'G1' response (responseCode should be SUCCESS(0))
    grant_ids = []
    for resp in grant_response_g1:
      self.assertEqual(resp['response']['responseCode'], 0)
      grant_ids.append(resp['grantId'])

    del grant_request_g1, grant_response_g1

    # Step 5.1: Sending Heartbeat Request
    # Construct heartbeat message
    heartbeat_requests = {'heartbeatRequest': []}
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
      heartbeat_requests['heartbeatRequest'].append({
        'cbsdId': cbsd_id,
        'grantId': grant_id,
        'operationState': 'GRANTED'
      })
    heartbeat_responses = self._sas.Heartbeat(heartbeat_requests)['heartbeatResponse']

    # Check responseCode of Heartbeat Response for grant 'G1' matches the
    # responseCode in the configuration file (SUCCESS '0' or SUSPENDED_GRANT '501')
    for resp_num, resp in enumerate(heartbeat_responses):
      self.assertIn(resp['response']['responseCode'], config['expectedResponseCodes'][0][resp_num])

    # Sending relinquishment request for the grant 'G1'.
    relq_requests = {'relinquishmentRequest': []}
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
      relq_requests['relinquishmentRequest'].append({
        'cbsdId': cbsd_id,
        'grantId': grant_id
      })
    relq_responses = self._sas.Relinquishment(relq_requests)['relinquishmentResponse']
    self.assertEqual(len(relq_responses), len(relq_requests['relinquishmentRequest']))

    # Check relinquishment response
    for relq_resp in relq_responses:
      self.assertEqual(relq_resp['response']['responseCode'], 0)

    del relq_requests, relq_responses
    del heartbeat_requests, heartbeat_responses

    # Step 6: Modify the FSS database to include modified version of FSS site S
    # Set the path of modified file
    fss_database_server.setFileToServe(config['fssDatabaseConfig']['fileUrl'],
                                        config['fssDatabaseConfig']['modifiedFilePath'])

    # Step 7: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 8: Send Grant Request 'G2'.
    # Forming of 'G2' grants for all the configured grants
    addCbsdIdsToRequests(cbsd_ids, config['grantRequests'][1])
    grant_request_g2 = {'grantRequest': config['grantRequests'][1]}

    grant_response_g2 = self._sas.Grant(grant_request_g2)['grantResponse']

    # Check grant 'G2' response (responseCode should be SUCCESS(0))
    grant_ids = []
    for resp in grant_response_g2:
      self.assertEqual(resp['response']['responseCode'], 0)
      grant_ids.append(resp['grantId'])

    del grant_request_g2, grant_response_g2

    # Step 9: Sending Heartbeat Request
    # Construct heartbeat message
    heartbeat_requests = {'heartbeatRequest': []}
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
      heartbeat_requests['heartbeatRequest'].append({
        'cbsdId': cbsd_id,
        'grantId': grant_id,
        'operationState': 'GRANTED'
      })
    heartbeat_responses = self._sas.Heartbeat(heartbeat_requests)['heartbeatResponse']

    # Check responseCode of Heartbeat Response for grant 'G2' matches the
    # responseCode in the configuration file (SUCCESS '0' or SUSPENDED_GRANT '501')
    for resp_num, resp in enumerate(heartbeat_responses):
      self.assertIn(resp['response']['responseCode'], config['expectedResponseCodes'][1][resp_num])

    del heartbeat_requests, heartbeat_responses

  def generate_FDB_5_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.5"""

    # Load devices info
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))

    # FSS database test harness configuration
    # The database File FDB_5_default_allsitedata.json has FSS sites information.
    fss_database_config = {
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'fileUrl': '/db_sync',
        'filePath': os.path.join('testcases', 'testdata', 'fdb_5', 'FDB_5_default_allsitedata.json')
    }

    # GWBL database test harness configuration.
    # The GWBL database file l_micro.zip has following GWBLs within 150 KMs from FSS sites
    # WAKEENEY,KS with Unique System Identifier as 959499
    # NEW YORK, NY with Unique System Identifier as 954597
    gwbl_database_config = {
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'fileUrl': '/db_sync',
        'filePath': os.path.join('testcases', 'testdata', 'fdb_5', 'l_micro.zip')
    }

    # Load grant requests
    grant_g_a = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the FSS frequency range which is 3650-4200 MHz.
    grant_g_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }

    grant_g_b = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with FSS frequency range which is 3650-4200 MHz.
    grant_g_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3670000000,
        'highFrequency': 3680000000
    }

    # Update the location 'X' of CBSD devices to be near the FSS sites
    # with FSS Number 'FSS0001010'
    device_a['installationParam']['latitude'] = 39.353414
    device_a['installationParam']['longitude'] = -100.195313
    # with FSS Number 'FSS0002010'
    device_b['installationParam']['latitude'] = 35.51043
    device_b['installationParam']['longitude'] = -100.27183

    # Creating conditionals for Cat B devices
    self.assertEqual(device_b['cbsdCategory'], 'B')
    conditionals_b = {
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

    conditionals = [conditionals_b]

    # Create the actual config.
    config = {
        'registrationRequests': [device_a, device_b],
        'grantRequests': [grant_g_a, grant_g_b],
        'conditionalRegistrationData': conditionals,
        'fssDatabaseConfig': fss_database_config,
        'gwblDatabaseConfig': gwbl_database_config
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_FDB_5_default_config)
  def test_WINNF_FT_S_FDB_5(self, config_filename):
    """GWBL Database Update: Adding a GWBL.

    Checks SAS UUT responds with Heartbeat Response 500 (TERMINATED_GRANT) for
    CBSD location X near FSS site
    """

    # Load the configuration file
    config = loadConfig(config_filename)

    self.check_default_test_not_expired()

    # Very light checking of the config file.
    self.assertEqual(len(config['registrationRequests']),
                     len(config['grantRequests']))

    # Step 1: Registration of CBSDs and requesting for grants.
    # Forming of 'G' grants for all the configured grants
    grant_request_g = config['grantRequests']

    # Register device(s) 'C' and request grant 'G' with SAS UUT.
    try:
      cbsd_ids, grant_ids = self.assertRegisteredAndGranted(
          config['registrationRequests'], grant_request_g,
          config['conditionalRegistrationData'])
    except Exception:
      logging.error(common_strings.EXPECTED_SUCCESSFUL_REGISTRATION_AND_GRANT)
      raise

    # Step 2: Create FSS database which includes at least one FSS site near location 'X'.
    # Create FSS database server
    fss_database_server = DatabaseServer(
      'FSS Database',
      config['fssDatabaseConfig']['hostName'],
      config['fssDatabaseConfig']['port'],
      authorization=True)

    # Start FSS database server
    fss_database_server.start()

    # Set file path
    fss_database_server.setFileToServe(config['fssDatabaseConfig']['fileUrl'],
                                        config['fssDatabaseConfig']['filePath'])

    # Inject the FSS database URL into the SAS UUT
    self._sas_admin.InjectDatabaseUrl({'type': 'FSS', 'url': fss_database_server.getBaseUrl()+
                                       config['fssDatabaseConfig']['fileUrl']})

    # Step 3: Create GWBL database which includes at least one GWBL site near location 'X'.
    # Create GWBL database server
    gwbl_database_server = DatabaseServer("GWBL Database",
                                          config['gwblDatabaseConfig']['hostName'],
                                          config['gwblDatabaseConfig']['port'])

    # Start GWBL database server
    gwbl_database_server.start()

    # Set file path
    gwbl_database_server.setFileToServe(config['gwblDatabaseConfig']['fileUrl'],
                                        config['gwblDatabaseConfig']['filePath'])

    # Inject the GWBL database URL into the SAS UUT
    self._sas_admin.InjectDatabaseUrl({'type': 'GWBL', 'url': gwbl_database_server.getBaseUrl()+
                                       config['gwblDatabaseConfig']['fileUrl']})

    # Step 4: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 5: Sending Heartbeat Request
    # Construct heartbeat message
    heartbeat_requests = {'heartbeatRequest': []}
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
      heartbeat_requests['heartbeatRequest'].append({
        'cbsdId': cbsd_id,
        'grantId': grant_id,
        'operationState': 'GRANTED'
      })
    heartbeat_responses = self._sas.Heartbeat(heartbeat_requests)['heartbeatResponse']

    # Check the heartbeat response code is 500(TERMINATED_GRANT)
    for resp in heartbeat_responses:
      self.assertEqual(resp['response']['responseCode'], 500)

    del heartbeat_requests, heartbeat_responses

  def generate_FDB_6_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.6"""

    # Load devices info
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))

    # FSS database test harness configuration.
    # The database File FDB_6_default_allsitedata.json has FSS sites information.
    fss_database_config = {
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'fileUrl': '/db_sync',
        'filePath': os.path.join('testcases', 'testdata', 'fdb_6', 'FDB_6_default_allsitedata.json')
    }

    # GWBL database test harness configuration.
    # The GWBL database file l_micro.zip has following GWBLs near CBSD locations 'X' and are
    # within 150 KMs from FSS sites
    # WAKEENEY,KS with Unique System Identifier as 959499
    # NEW YORK, NY with Unique System Identifier as 954597
    # The GWBL database file modified_l_micro.zip has updated locations for the above
    # mentioned GWBLs (GWBLs are moved further than 150 km from the FSS sites).
    gwbl_database_config = {
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'fileUrl': '/db_sync',
        'filePath': os.path.join('testcases', 'testdata', 'fdb_6', 'l_micro.zip'),
        'modifiedFilePath': os.path.join('testcases', 'testdata', 'fdb_6', 'modified_l_micro.zip')
    }

    # Load grant requests
    grant_g1_a = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the FSS frequency range which is 3650-4200 MHz.
    grant_g1_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }
    grant_g2_a = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the FSS frequency range which is 3650-4200 MHz.
    grant_g2_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3675000000,
        'highFrequency': 3685000000
    }

    grant_g1_b = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the FSS frequency range which is 3650-4200 MHz.
    grant_g1_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3660000000,
        'highFrequency': 3670000000
    }
    grant_g2_b = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the FSS frequency range which is 3650-4200 MHz.
    grant_g2_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3685000000,
        'highFrequency': 3695000000
    }

    # Update the location 'X' of CBSD devices to be near the FSS sites
    # with FSS Number 'FSS0001010'
    device_a['installationParam']['latitude'] = 39.353414
    device_a['installationParam']['longitude'] = -100.195313
    # with FSS Number 'FSS0002010'
    device_b['installationParam']['latitude'] = 35.51043
    device_b['installationParam']['longitude'] = -100.27183

    # Creating conditionals for Cat B devices
    self.assertEqual(device_b['cbsdCategory'], 'B')
    conditionals_b = {
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

    conditionals = [conditionals_b]

    # Create the actual config.
    config = {
        'registrationRequest': [device_a, device_b],
        'grantRequests': [
            [grant_g1_a, grant_g1_b],
            [grant_g2_a, grant_g2_b]],
        'expectedResponseCodes': [
            [(400,), (400,)],
            [(0,), (0,)]],
        'conditionalRegistrationData': conditionals,
        'fssDatabaseConfig': fss_database_config,
        'gwblDatabaseConfig': gwbl_database_config
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_FDB_6_default_config)
  def test_WINNF_FT_S_FDB_6(self, config_filename):
    """GWBL Database Update: GWBL Modification."""

    # Load the configuration file
    config = loadConfig(config_filename)

    self.check_default_test_not_expired()

    # Very light checking of the config file.
    self.assertEqual(len(config['grantRequests']),
                     len(config['expectedResponseCodes']))

    # Step 1: Register device(s) 'C'(at location 'X') with conditional registration data
    try:
      cbsd_ids = self.assertRegistered(config['registrationRequest'],
                                       config['conditionalRegistrationData'])
    except Exception:
      logging.error(common_strings.EXPECTED_SUCCESSFUL_REGISTRATION)
      raise

    # Step 2: Create FSS database which includes at least one FSS site near
    # CBSD location 'X'.
    # Create FSS database server.
    fss_database_server = DatabaseServer(
      'FSS Database',
      config['fssDatabaseConfig']['hostName'],
      config['fssDatabaseConfig']['port'],
      authorization=True)

    # Start FSS database server
    fss_database_server.start()

    # Set file path
    fss_database_server.setFileToServe(config['fssDatabaseConfig']['fileUrl'],
                                        config['fssDatabaseConfig']['filePath'])

    # Inject the FSS database URL into the SAS UUT
    self._sas_admin.InjectDatabaseUrl({'type': 'FSS', 'url': fss_database_server.getBaseUrl()+
                                       config['fssDatabaseConfig']['fileUrl']})

    # Step 3: Create GWBL database which includes at least one GWBL site near
    # CBSD location 'X'.
    # Create GWBL database server.
    gwbl_database_server = DatabaseServer("GWBL Database",
                                          config['gwblDatabaseConfig']['hostName'],
                                          config['gwblDatabaseConfig']['port'])

    # Start GWBL database server
    gwbl_database_server.start()

    # Set file path
    gwbl_database_server.setFileToServe(config['gwblDatabaseConfig']['fileUrl'],
                                        config['gwblDatabaseConfig']['filePath'])

    # Inject the GWBL database URL into the SAS UUT
    self._sas_admin.InjectDatabaseUrl({'type': 'GWBL', 'url': gwbl_database_server.getBaseUrl()+
                                       config['gwblDatabaseConfig']['fileUrl']})

    # Step 4: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 5: Send Grant Request 'G1'.
    # Forming of 'G1' grants for all the configured grants
    addCbsdIdsToRequests(cbsd_ids, config['grantRequests'][0])
    grant_request_g1 = {'grantRequest': config['grantRequests'][0]}

    grant_response_g1 = self._sas.Grant(grant_request_g1)['grantResponse']

    # Check the grant response code is as expected (SUCCESS or INTERFERENCE).
    # Used a 2-D matrix of response codes to check against the grant responses received
    grant_ids_g1 = []
    cbsd_ids_g1 = []
    for resp_num, resp in enumerate(grant_response_g1):
      self.assertIn(resp['response']['responseCode'], config['expectedResponseCodes'][0][resp_num])
      if 'grantId' in resp:
        grant_ids_g1.append(resp['grantId'])
        cbsd_ids_g1.append(resp['cbsdId'])

    # If SAS UUT Responded with SUCCESS for Grant then Proceed with Relinquishment or else skip it
    if grant_ids_g1:
      # Step 6: Send relinquishment request for grant 'G1'
      relq_requests = {'relinquishmentRequest': []}
      for cbsd_id, grant_id in zip(cbsd_ids_g1, grant_ids_g1):
        # Update Relinquishment Request content
        relq_requests['relinquishmentRequest'].append({
          'cbsdId': cbsd_id,
          'grantId': grant_id
        })
      relq_responses = self._sas.Relinquishment(relq_requests)['relinquishmentResponse']
      self.assertEqual(len(relq_responses), len(relq_requests['relinquishmentRequest']))

      # Check relinquishment response
      for relq_resp in relq_responses:
        self.assertEqual(relq_resp['response']['responseCode'], 0)

      del relq_requests, relq_responses

    del grant_request_g1, grant_response_g1

    # TOD0
    # Step 7: Modify the GWBL database to include a modified version of the GWBL 'W'.
    # 'W' is moved further than 150 kms from FSS site.
    # Set the path of modified file
    gwbl_database_server.setFileToServe(config['gwblDatabaseConfig']['fileUrl'],
                                        config['gwblDatabaseConfig']['modifiedFilePath'])

    # Step 8: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 9: Send Grant Request 'G2'
    # Forming of 'G2' grants for all the configured grants
    addCbsdIdsToRequests(cbsd_ids, config['grantRequests'][1])
    grant_request_g2 = {'grantRequest': config['grantRequests'][1]}

    grant_response_g2 = self._sas.Grant(grant_request_g2)['grantResponse']

    # Check the grant response code is as expected (SUCCESS or INTERFERENCE).
    for resp_num, resp in enumerate(grant_response_g2):
      self.assertIn(resp['response']['responseCode'], config['expectedResponseCodes'][1][resp_num])

    del grant_request_g2, grant_response_g2

  def generate_FDB_8_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.8"""

    # Load devices info
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))

    # Load grant requests
    grant_g_b = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_g_a = json_load(
                os.path.join('testcases', 'testdata', 'grant_0.json'))
    # Set the grant frequency to overlap with the Respective FSSes.
    grant_g_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }
    grant_g_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }

    device_b['installationParam']['latitude'] = 39.2291
    device_b['installationParam']['longitude'] = -100.1
    device_b['installationParam']['antennaBeamwidth'] = 0
    device_a['installationParam']['latitude'] = 39.7355
    device_a['installationParam']['longitude'] = -107.9575
    device_a['installationParam']['antennaBeamwidth'] = 0

    # Pre-load conditionals and remove reg conditional fields from registration
    # request.
    conditional_keys = [
        'cbsdCategory', 'fccId', 'cbsdSerialNumber', 'airInterface',
        'installationParam', 'measCapability'
    ]
    reg_conditional_keys = [
        'cbsdCategory', 'airInterface', 'installationParam', 'measCapability'
    ]
    conditionals_a = {key: device_a[key] for key in conditional_keys}
    device_a = {
        key: device_a[key]
        for key in device_a
        if key not in reg_conditional_keys
    }
    conditionals_b = {key: device_b[key] for key in conditional_keys}
    device_b = {
        key: device_b[key]
        for key in device_b
        if key not in reg_conditional_keys
    }

    fss_database_config = {
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'fileUrl': '/rest/fss/v1/allsitedata',
        'filePath': os.path.join('testcases', 'testdata', 'fdb_8', 'FDB_8_default_allsitedata.json')
    }

    # Create the actual config.
    config = {
        'registrationRequests': [device_a, device_b],
        'grantRequests': [grant_g_a, grant_g_b],
        'conditionalRegistrationData': [conditionals_a, conditionals_b],
        'fssDatabaseConfig': fss_database_config
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_FDB_8_default_config)
  def test_WINNF_FT_S_FDB_8(self, config_filename):
    """FSS Database Update: Scheduled Database Update."""

    # Load the configuration file
    config = loadConfig(config_filename)

    # Very light checking of the config file.
    self.assertEqual(len(config['registrationRequests']),
                     len(config['grantRequests']))

    # Step 1: Trigger for enabling "schedule daily activities"
    self._sas_admin.TriggerEnableScheduledDailyActivities()

    # Step 2: Registration of CBSDs and requesting for grants.
    # Forming of 'G' grants for all the configured grants
    grant_request_g = config['grantRequests']

    # Register device(s) 'C' and request grant 'G' with SAS UUT.
    try:
      cbsd_ids, grant_ids = self.assertRegisteredAndGranted(
          config['registrationRequests'], grant_request_g,
          config['conditionalRegistrationData'])
    except Exception:
      logging.error(common_strings.EXPECTED_SUCCESSFUL_REGISTRATION_AND_GRANT)
      raise

    # Step 3: Create FSS database which includes atleast one FSS site near location 'X'.
    # Create FSS database server
    fss_database_server = DatabaseServer(
      'FSS Database',
      config['fssDatabaseConfig']['hostName'],
      config['fssDatabaseConfig']['port'],
      authorization=True)

    # Start FSS database server
    fss_database_server.start()

    # Set file path
    fss_database_server.setFileToServe(config['fssDatabaseConfig']['fileUrl'],
                                        config['fssDatabaseConfig']['filePath'])

    # Step 4: Inject the FSS database URL into the UUT
    self._sas_admin.InjectDatabaseUrl({'type': 'FSS', 'url': fss_database_server.getBaseUrl()+
                                       config['fssDatabaseConfig']['fileUrl']})

    # Step 5: Wait until after the completion of scheduled CPAS
    # Fetching current time in CPAS time zone
    current_time = datetime.now(timezone(CPAS_TIME_ZONE))

    # Calculate the scheduled CPAS start time.
    scheduled_cpas_start_time =  timezone(CPAS_TIME_ZONE).localize(datetime.combine(current_time.date(), time(CPAS_START_TIME)))

    # Checks if CPAS start time is over then wait till next day otherwise
    # wait till scheduled CPAS starts
    if scheduled_cpas_start_time < current_time:
      scheduled_cpas_start_time += timedelta(days=1)

    # Wait time in seconds
    wait_time_in_secs = (scheduled_cpas_start_time - current_time).seconds

    # Checks if scheduled CPAS starts today and ends on the next day
    if CPAS_START_TIME < CPAS_END_TIME:
      scheduled_cpas_end_time = scheduled_cpas_start_time +\
                                timedelta(hours=CPAS_END_TIME - CPAS_START_TIME)
    else:
      scheduled_cpas_end_time = scheduled_cpas_start_time +\
                                timedelta(days=1, hours=CPAS_END_TIME - CPAS_START_TIME)

    # Run time in seconds
    run_time_in_secs = (scheduled_cpas_end_time - scheduled_cpas_start_time).seconds

    # Wait until CPAS is scheduled to start
    logging.debug('Wait time for scheduled CPAS is (HH:MM:SS) %s',
                  strftime("%H:%M:%S", gmtime(wait_time_in_secs)))
    sleep(wait_time_in_secs)

    # Wait until CPAS completes
    logging.debug('Run time for scheduled CPAS is (HH:MM:SS) %s',
                  strftime("%H:%M:%S", gmtime(run_time_in_secs)))
    sleep(run_time_in_secs)

    # Step 6: Sending Heartbeat Request
    # Construct heartbeat message
    heartbeat_requests = {'heartbeatRequest': []}
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
      heartbeat_requests['heartbeatRequest'].append({
        'cbsdId': cbsd_id,
        'grantId': grant_id,
        'operationState': 'GRANTED'
      })
    heartbeat_responses = self._sas.Heartbeat(heartbeat_requests)['heartbeatResponse']

    # Check the heartbeat response code is 500(TERMINATED_GRANT)
    for resp in heartbeat_responses:
      self.assertEqual(resp['response']['responseCode'], 500)

  def check_default_test_not_expired(self):
    """Check the expiration date in the default configs has not been reached."""
    if datetime.now() > datetime.strptime('2028-09-23', '%Y-%m-%d') - timedelta(days=1):
      logging.error('Test is being run near or past the expiration date of the '
                    'default database. This test may fail. Is this testcase '
                    'still required?')
