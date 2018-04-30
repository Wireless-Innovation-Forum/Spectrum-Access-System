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
import sas
import sas_testcase
from datetime import date, datetime, time, timedelta
from pytz import timezone
from time import sleep, strftime, gmtime
from util import configurable_testcase, writeConfig, loadConfig, addCbsdIdsToRequests

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
    pass

  def generate_FDB_1_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.1"""

    # Load devices info
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Load grant requests.
    grant_g1_a = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the exclusion zone
    # 'Yuma Proving Ground' frequency range 'F1'.
    grant_g1_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }
    grant_g2_a = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the exclusion zone
    # 'Yuma Proving Ground' frequency range 'F1'.
    grant_g2_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3675000000,
        'highFrequency': 3685000000
    }
    grant_g3_a = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the modified
    # exclusion zone 'Yuma Proving Ground' frequency range 'F2'.
    grant_g3_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3575000000,
        'highFrequency': 3585000000
    }

    grant_g1_b = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the exclusion zone
    # 'Yakima Firing Center' frequency range 'F1'.
    grant_g1_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }
    grant_g2_b = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the exclusion zone
    # 'Yakima Firing Center' frequency range 'F1'.
    grant_g2_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3675000000,
        'highFrequency': 3685000000
    }
    grant_g3_b = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the modified
    # exclusion zone 'Yakima Firing Center' frequency range 'F2'.
    grant_g3_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3575000000,
        'highFrequency': 3585000000
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
        'conditionalRegistrationData': conditionals
        # TODO
        # Need to add data base configurations.
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
    cbsd_ids, grant_ids = self.assertRegisteredAndGranted(config['registrationRequests'],
                                   grant_request_g1,
                                   config['conditionalRegistrationData'])

    # TODO
    # Step 2: Create exclusion zone database which contains the
    # CBSD location 'X' or is within 50 meters of the CBSD location 'X'.

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

    # TODO
    # Step 7: Modify exclusion zone database record frequency range from 'F1' to 'F2'

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
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Load grant requests
    grant_g1_a = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the DPA 'puerto_rico_ver2_dpa_4'.
    grant_g1_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }
    grant_g2_a = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the DPA 'puerto_rico_ver2_dpa_4'.
    grant_g2_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3675000000,
        'highFrequency': 3685000000
    }
    grant_g3_a = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the modified DPA 'puerto_rico_ver2_dpa_4'.
    grant_g3_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3575000000,
        'highFrequency': 3585000000
    }

    grant_g1_b = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the DPA 'alaska_dpa_37'.
    grant_g1_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }
    grant_g2_b = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the DPA 'alaska_dpa_37'.
    grant_g2_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3675000000,
        'highFrequency': 3685000000
    }
    grant_g3_b = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the modified DPA 'alaska_dpa_37'.
    grant_g3_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3575000000,
        'highFrequency': 3585000000
    }

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
        'conditionalRegistrationData': conditionals
        # TODO
        # Need to add data base configurations.
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
    cbsd_ids, grant_ids = self.assertRegisteredAndGranted(config['registrationRequests'],
                                   grant_request_g1,
                                   config['conditionalRegistrationData'])

    # TODO
    # Step 2: Create DPA database which includes at least one inland DPA

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

    # TODO
    # Step 8: Modify DPA database record frequency range from 'F1' to 'F2'

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
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Load grant requests
    grant_g_a = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'KA413' which is 3625-4200 MHz.
    grant_g_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }

    grant_g_b = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'E000306' which is 3625-3700 MHz.
    grant_g_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3660000000,
        'highFrequency': 3670000000
    }

    # Update the location 'X' of CBSD devices to be near FSS sites
    # 'KA413' at Albright,WV
    device_a['installationParam']['latitude'] = 39.57327
    device_a['installationParam']['longitude'] = -79.61903

    # 'E000306' at Andover,ME
    device_b['installationParam']['latitude'] = 44.63367
    device_b['installationParam']['longitude'] = -70.69758

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
        'conditionalRegistrationData': conditionals
        # TODO
        # Need to add data base configurations.
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
    cbsd_ids, grant_ids = self.assertRegisteredAndGranted(config['registrationRequests'],
                                    grant_request_g,
                                    config['conditionalRegistrationData'])

    # TODO
    # Step 2: Create FSS database which includes atleast one FSS site near location 'X'.

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
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

   # Load grant requests
    grant_g1_a = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'KA413' which is 3625-4200 MHz.
    grant_g1_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }
    grant_g2_a = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'KA413' which is 3625-4200 MHz.
    grant_g2_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3675000000,
        'highFrequency': 3685000000
    }

    grant_g1_b = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'E000306' which is 3625-3700 MHz.
    grant_g1_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3660000000,
        'highFrequency': 3670000000
    }
    grant_g2_b = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'E000306' which is 3625-3700 MHz.
    grant_g2_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3685000000,
        'highFrequency': 3695000000
    }

    # Update the location 'X' of CBSD devices to be near FSS sites
    # 'KA413' at Albright,WV
    device_a['installationParam']['latitude'] = 39.57327
    device_a['installationParam']['longitude'] = -79.61903

    # 'E000306' at Andover,ME
    device_b['installationParam']['latitude'] = 44.63367
    device_b['installationParam']['longitude'] = -70.69758

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
            [(0, ), (0,)],
            [(501, ), (501, )]],
        'conditionalRegistrationData': conditionals
        # TODO
        # Need to add data base configurations
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
    cbsd_ids = self.assertRegistered(config['registrationRequests'],
                                     config['conditionalRegistrationData'])

    # TODO
    # Step 2: Create FSS database which includes atleast one FSS site near location 'X'.

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

    # TODO
    # Step 6: Modify the FSS database to include modified version of FSS site S

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
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Load grant requests
    grant_g_a = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'KA413' which is 3625-4200 MHz.
    grant_g_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }

    grant_g_b = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'E000306' which is 3625-3700 MHz.
    grant_g_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3670000000,
        'highFrequency': 3680000000
    }

    # Update the location 'X' of CBSD devices to be near FSS sites
    # 'KA413' at Albright,WV
    device_a['installationParam']['latitude'] = 39.57327
    device_a['installationParam']['longitude'] = -79.61903

    # 'E000306' at Andover,ME
    device_b['installationParam']['latitude'] = 44.63367
    device_b['installationParam']['longitude'] = -70.69758

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
        'conditionalRegistrationData': conditionals
        # TODO
        # Need to add data base configurations
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

    # Very light checking of the config file.
    self.assertEqual(len(config['registrationRequests']),
                     len(config['grantRequests']))

    # Step 1: Registration of CBSDs and requesting for grants.
    # Forming of 'G' grants for all the configured grants
    grant_request_g = config['grantRequests']

    # Register device(s) 'C' and request grant 'G' with SAS UUT.
    cbsd_ids, grant_ids = self.assertRegisteredAndGranted(
                                   config['registrationRequests'],
                                   grant_request_g,
                                   config['conditionalRegistrationData'])

    # TODO
    # Step 2: Create FSS database which includes at least one FSS site near

    # TODO
    # Step 3: Create GWBL database which includes at least one GWBL site near

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
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Load grant requests
    grant_g1_a = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'KA413' which is 3625-4200 MHz.
    grant_g1_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }
    grant_g2_a = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'KA413' which is 3625-4200 MHz.
    grant_g2_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3675000000,
        'highFrequency': 3685000000
    }

    grant_g1_b = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'E000306' which is 3625-3700 MHz.
    grant_g1_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3660000000,
        'highFrequency': 3670000000
    }
    grant_g2_b = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'E000306' which is 3625-3700 MHz.
    grant_g2_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3685000000,
        'highFrequency': 3695000000
    }

    # Update the location 'X' of CBSD devices to be near FSS sites
    # 'KA413' at Albright,WV
    device_a['installationParam']['latitude'] = 39.57327
    device_a['installationParam']['longitude'] = -79.61903

    # 'E000306' at Andover,ME
    device_b['installationParam']['latitude'] = 44.63367
    device_b['installationParam']['longitude'] = -70.69758

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
        'conditionalRegistrationData': conditionals
        # TODO
        # Need to add data base configurations
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_FDB_6_default_config)
  def test_WINNF_FT_S_FDB_6(self, config_filename):
    """GWBL Database Update: GWBL Modification."""

    # Load the configuration file
    config = loadConfig(config_filename)

    # Very light checking of the config file.
    self.assertEqual(len(config['grantRequests']),
                     len(config['expectedResponseCodes']))

    # Step 1: Register device(s) 'C'(at location 'X') with conditional registration data
    cbsd_ids = self.assertRegistered(config['registrationRequest'],
                                     config['conditionalRegistrationData'])

    # TODO
    # Step 2: Create FSS database which includes at least one FSS site near
    # CBSD location 'X'.

    # TODO
    # Step 3: Create GWBL database which includes at least one GWBL site near
    # CBSD location 'X'.

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

  def generate_FDB_7_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.7"""

    # Load devices info
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))

    # Update the FCC ID of CBSDs from FCC ID database.
    device_a['fccId'] = "F_ID_a"
    device_c['fccId'] = "F_ID_c"

    self.assertEqual(device_a['cbsdCategory'], 'A')
    self.assertEqual(device_c['cbsdCategory'], 'A')

    # Create the actual config.
    config = {
        'registrationRequests': [device_a, device_c],
        'expectedResponseCodes': [(103,), (0,)]
        # TODO
        # Need to add data base configurations
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_FDB_7_default_config)
  def test_WINNF_FT_S_FDB_7(self, config_filename):
    """FCC ID Database Update."""

    # Load the configuration file
    config = loadConfig(config_filename)

    # Very light checking of the config file.
    self.assertEqual(len(config['registrationRequests']),
                     len(config['expectedResponseCodes']))

    registration_requests = {
        'registrationRequest': config['registrationRequests']
    }

    # Step 1: Send registration request for CBSD 'C' to SAS UUT.
    registration_responses = self._sas.Registration(registration_requests)['registrationResponse']

    # Check registration response,
    # responseCode should be 103(INVALID_VALUE)
    for resp in registration_responses:
      self.assertEqual(resp['response']['responseCode'], 103)

    del registration_responses

    # TODO
    # Step 2: Create FCC ID database which includes at least one FCC ID 'F_ID'.

    # Step 3: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 4: Send again the same registration request for CBSD 'C'
    # with FCC ID 'F_ID' to SAS UUT.
    registration_responses = self._sas.Registration(registration_requests)['registrationResponse']

    # Check registration response,
    # responseCode should be 0(SUCCESS)
    for resp in registration_responses:
      self.assertEqual(resp['response']['responseCode'], 0)

    del registration_responses

    # TODO
    # Step 5: Modify FCC ID database record with FCC ID 'F_ID'.

    # Step 6: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 7: Send again the same registration request for CBSD 'C'
    # with FCC ID 'F_ID' to SAS UUT.
    registration_responses = self._sas.Registration(registration_requests)['registrationResponse']

    # Check the registration response code is as expected (SUCCESS or INVALID_VALUE).
    for resp_num, resp in enumerate(registration_responses):
      self.assertIn(resp['response']['responseCode'], config['expectedResponseCodes'][resp_num])

    del registration_requests, registration_responses

  def generate_FDB_8_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.8"""

    # Load devices info
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Load grant requests
    grant_g_a = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'KA413' which is 3625-4200 MHz.
    grant_g_a['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }

    grant_g_b = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'E000306' which is 3625-3700 MHz.
    grant_g_b['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3670000000,
        'highFrequency': 3680000000
    }

    # Update the location 'X' of CBSD devices to be near FSS sites
    # 'KA413' at Albright,WV
    device_a['installationParam']['latitude'] = 39.57327
    device_a['installationParam']['longitude'] = -79.61903

    # 'E000306' at Andover,ME
    device_b['installationParam']['latitude'] = 44.63367
    device_b['installationParam']['longitude'] = -70.69758

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
        'conditionalRegistrationData': conditionals
        # TODO
        # Need to add data base configurations
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
    cbsd_ids, grant_ids = self.assertRegisteredAndGranted(
                              config['registrationRequests'],
                              grant_request_g,
                              config['conditionalRegistrationData'])

    # TODO
    # Step 3: Create FSS database which includes atleast one FSS site near location 'X'.

    # TODO
    # Step 4: Inject the FSS database URL into the UUT

    # Step 5: Wait until after the completion of scheduled CPAS
    # Fetching current time in CPAS time zone
    current_time = datetime.now(timezone(CPAS_TIME_ZONE))

    # Checks if CPAS start time is over then wait till next day otherwise
    # wait till scheduled CPAS starts
    scheduled_cpas_start_time = datetime.combine(current_time.date(), time(CPAS_START_TIME))

    # Scheduled CPAS start time is made consistent with the CPAS_TIME_ZONE  
    scheduled_cpas_start_time = scheduled_cpas_start_time.replace(tzinfo=timezone(CPAS_TIME_ZONE))

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
