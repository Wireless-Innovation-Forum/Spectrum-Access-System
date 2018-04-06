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
from util import configurable_testcase, writeConfig, loadConfig


class FederalGovernmentDatabaseUpdateTestcase(sas_testcase.SasTestCase):
  """SAS federal government database update test cases"""

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

    # Load grant request.
    grant_g1 = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the exclusion zone 'Yuma Proving Ground'
    #  frequency range 'F1' which is .
    grant_g1['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }
    grant_g2 = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the exclusion zone
    # 'Yuma Proving Ground' frequency range 'F1' which is.
    grant_g2['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3675000000,
        'highFrequency': 3685000000
    }
    grant_g3 = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the modified
    # exclusion zone 'Yuma Proving Ground' frequency range 'F2' which is.
    grant_g3['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3575000000,
        'highFrequency': 3585000000
    }

    # Update the location 'X' of CBSD contained witin the exclusion zone
    # 'Yuma Proving Ground'.
    device_b['installationParam']['latitude'] = 32.94414
    device_b['installationParam']['longitude'] = -113.85681

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
        'registrationRequest': [device_b],
        'grantRequests': [grant_g1, grant_g2, grant_g3],
        'conditionalRegistrationData': conditionals
      }
    writeConfig(filename, config)

  @configurable_testcase(generate_FDB_1_default_config)
  def test_WINNF_FT_S_FDB_1(self, config_filename):
    """Exclusion Zone Database Update"""

    # Load the configuration file
    config = loadConfig(config_filename)

    # Step 1: Register device C and request grant 'G1' with SAS UUT.
    grant_request_g1 = [config['grantRequests'][0]]
    cbsd_ids, grant_ids = self.assertRegisteredAndGranted(config['registrationRequest'],
                                   grant_request_g1,
                                   config['conditionalRegistrationData'])
    # TODO
    # Step 2: Create exclusion zone database which contains the
    # CBSD location 'X' or is within 50 meters of the CBSD location 'X'.

    # Step 3: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 4: Sending Heartbeat Request
    # Construct heartbeat message
    heartbeat_request = {
      'heartbeatRequest': [{
        'cbsdId': cbsd_ids[0],
        'grantId': grant_ids[0],
        'operationState': 'GRANTED'
      }]
    }
    heartbeat_response = self._sas.Heartbeat(heartbeat_request)['heartbeatResponse']

    # Check the heartbeat response code is 500(TERMINATED_GRANT)
    # or 501 (SUSPENDED_GRANT)
    self.assertEqual(heartbeat_response[0]['grantId'], grant_ids[0])
    self.assertIn(heartbeat_response[0]['response']['responseCode'], [500, 501])

    # Step 5: Sending relinquishment request for the Grant
    # if the responseCode was 501 for heartbeat response
    relq_request = {'relinquishmentRequest': []}
    if heartbeat_response[0]['response']['responseCode'] == 501:
      # Update Relinquishment Request content
      content = {
           'cbsdId': cbsd_ids[0],
           'grantId': grant_ids[0]
      }
      relq_request['relinquishmentRequest'].append(content)

      relq_response = self._sas.Relinquishment(relq_request)['relinquishmentResponse']
      self.assertEqual(relq_response[0]['grantId'], grant_ids[0])
      self.assertEqual(relq_response[0]['response']['responseCode'], 0)
      del relq_request, relq_response

    del heartbeat_request, heartbeat_response

    # Step 6: Request grant 'G2' with another frequency range which partially or fully
    # overlaps with Exclusion zone protected frequency range 'F1'.
    config['grantRequests'][1]['cbsdId'] = cbsd_ids[0]

    # Send grant request 'G2'
    grant_request_g2 = {'grantRequest': [config['grantRequests'][1]]}
    grant_response_g2 = self._sas.Grant(grant_request_g2)['grantResponse']
    self.assertEqual(len(grant_response_g2), len(grant_request_g2))

    # Check grant response,
    # responseCode should be 400 (INTERFERENCE).
    self.assertEqual(grant_response_g2[0]['response']['responseCode'], 400)

    del grant_request_g2, grant_response_g2
    # TODO
    # Step 7: Modify exclusion zone database record frequency range from 'F1' to 'F2'

    # Step 8: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 9: Request grant 'G3' with frequency range which partially or fully
    # overlaps with Exclusion zone protected frequency range 'F2'.
    config['grantRequests'][2]['cbsdId'] = cbsd_ids[0]

    # Send grant request 'G3'
    grant_request_g3 = {'grantRequest': [config['grantRequests'][2]]}
    grant_response_g3 = self._sas.Grant(grant_request_g3)['grantResponse']
    self.assertEqual(len(grant_response_g3), len(grant_request_g3))

    # Check grant response,
    # responseCode should be 400 (INTERFERENCE).
    self.assertEqual(grant_response_g3[0]['response']['responseCode'], 400)

    del grant_request_g3, grant_response_g3

  def generate_FDB_2_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.2"""

    # Load device info
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    # Load grant request
    grant_g1 = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the DPA 'puerto_rico_ver2_dpa_4' which is .
    grant_g1['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }
    grant_g2 = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the DPA 'puerto_rico_ver2_dpa_4' which is.
    grant_g2['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3675000000,
        'highFrequency': 3685000000
    }

    grant_g3 = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the modified DPA 'puerto_rico_ver2_dpa_4' which is.
    grant_g3['operationParam']['operationFrequencyRange'] = {
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
        'registrationRequest': [device_b],
        'grantRequests': [grant_g1, grant_g2, grant_g3],
        'conditionalRegistrationData': conditionals
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_FDB_2_default_config)
  def test_WINNF_FT_S_FDB_2(self, config_filename):
    """DPA Database Update for DPAs which cannot be monitored by an ESC."""

    # Load the configuration file
    config = loadConfig(config_filename)

    # Step 1: Register device and request grant 'G1' with SAS UUT.
    grant_request_g1 = [config['grantRequests'][0]]
    cbsd_ids, grant_ids = self.assertRegisteredAndGranted(config['registrationRequest'],
                                   grant_request_g1,
                                   config['conditionalRegistrationData'])
    # TODO...
    # Step 2: Create DPA database which includes at least one inland DPA

    # Step 3: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 4: Sending Heartbeat Request
    # Construct heartbeat message
    heartbeat_request = {
      'heartbeatRequest': [{
        'cbsdId': cbsd_ids[0],
        'grantId': grant_ids[0],
        'operationState': 'GRANTED'
      }]
    }
    heartbeat_response = self._sas.Heartbeat(heartbeat_request)['heartbeatResponse']
    # Check the heartbeat response code is 500(TERMINATED_GRANT)
    # or 501 (SUSPENDED_GRANT)
    self.assertEqual(heartbeat_response[0]['grantId'], grant_ids[0])
    self.assertIn(heartbeat_response[0]['response']['responseCode'], [500, 501])

    # Step 5: Sending relinquishment request for the Grant
    # if the responseCode was 501 for heartbeat response
    relq_request = {'relinquishmentRequest': []}
    if heartbeat_response[0]['response']['responseCode'] == 501:
      # Update Relinquishment Request content
      content = {
           'cbsdId': cbsd_ids[0],
           'grantId': grant_ids[0]
      }
      relq_request['relinquishmentRequest'].append(content)

      relq_response = self._sas.Relinquishment(relq_request)['relinquishmentResponse']
      self.assertEqual(relq_response[0]['grantId'], grant_ids[0])
      self.assertEqual(relq_response[0]['response']['responseCode'], 0)
      del relq_request, relq_response

    del heartbeat_request, heartbeat_response

    # Step 6: Request grant 'G2' with frequency range which partially or fully
    # overlaps with DPA protected frequency range 'F1'
    config['grantRequests'][1]['cbsdId'] = cbsd_ids[0]

    # Send grant request 'G2'
    grant_request_g2 = {'grantRequest': [config['grantRequests'][1]]}
    grant_response_g2 = self._sas.Grant(grant_request_g2)['grantResponse']
    self.assertEqual(len(grant_response_g2), len(grant_request_g2))

    # Check grant response,
    # responseCode should be either 400 (INTERFERENCE) or 0 (SUCCESS).
    self.assertIn(grant_response_g2[0]['response']['responseCode'], [0, 400])

    # Consolidating the heartbeat request for the Grant 'G2'
    # if the responseCode was 0 in grant response
    heartbeat_request = {'heartbeatRequest': []}
    if self.assertEqual(grant_response_g2[0]['response']['responseCode'], 0):
      self.assertTrue('grantId' in grant_response_g2[0])
      # Construct heartbeat message.
      # Update heartbeat request content
      content = {
          'cbsdId': cbsd_ids[0],
          'grantId': grant_response_g2[0]['grantId'],
          'operationState': 'GRANTED'
      }
      heartbeat_request['heartbeatRequest'].append(content)
      heartbeat_response = self._sas.Heartbeat(heartbeat_request)['heartbeatResponse']

      self.assertEqual(len(heartbeat_response), len(heartbeat_request['heartbeatRequest']))

      # Step 7: Send Relinquishment Request
      relq_request = {'relinquishmentRequest': []}

      # Check the heartbeat response code is 501 (SUSPENDED_GRANT)
      self.assertTrue('grantId' in heartbeat_response[0])
      self.assertEqual(heartbeat_response[0]['response']['responseCode'], 501)

      # Consolidating the relinquishment request for the Grants
      # Update relinquishment request content
      content = {
          'cbsdId': cbsd_ids[0],
          'grantId': heartbeat_response[0]['grantId']
      }
      relq_request['relinquishmentRequest'].append(content)

      # Send Relinquishment Request for grant 'G2',
      relq_response = self._sas.Relinquishment(relq_request)['relinquishmentResponse']
      # Check the relinquishment response
      self.assertEqual(len(relq_response), len(relq_request['relinquishmentRequest']))
      self.assertTrue('grantId' in relq_response[0])
      self.assertEqual(relq_response[0]['response']['responseCode'], 0)

      del relq_request, relq_response
      del heartbeat_request, heartbeat_response

    del grant_request_g2, grant_response_g2

    # TODO
    # Step 8: Modify DPA database record frequency range from 'F1' to 'F2'

    # Step 9: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 10: Request grant 'G3' with frequency range which partially or fully
    # overlaps with DPA protected frequency range 'F2'.
    config['grantRequests'][2]['cbsdId'] = cbsd_ids[0]

    # Send grant request 'G3'
    grant_request_g3 = {'grantRequest': [config['grantRequests'][2]]}
    grant_response_g3 = self._sas.Grant(grant_request_g3)['grantResponse']
    self.assertEqual(len(grant_response_g3), len(grant_request_g3))

    # Check grant response,
    # responseCode should be either 400 (INTERFERENCE) or 0 (SUCCESS).
    self.assertIn(grant_response_g3[0]['response']['responseCode'], [0, 400])

    # Consolidating the heartbeat request for the Grant 'G3'
    # if the responseCode was 0 in grant response
    heartbeat_request = {'heartbeatRequest': []}
    if self.assertEqual(grant_response_g3[0]['response']['responseCode'], 0):
      self.assertTrue('grantId' in grant_response_g3[0])
      # Construct heartbeat message.
      # Update heartbeat request content
      content = {
          'cbsdId': cbsd_ids[0],
          'grantId': grant_response_g3[0]['grantId'],
          'operationState': 'GRANTED'
      }
      heartbeat_request['heartbeatRequest'].append(content)
      heartbeat_response = self._sas.Heartbeat(heartbeat_request)['heartbeatResponse']

      self.assertEqual(len(heartbeat_response), len(heartbeat_request['heartbeatRequest']))

      # Check the heartbeat response code is 501 (SUSPENDED_GRANT)
      self.assertTrue('grantId' in heartbeat_response[0])
      self.assertEqual(heartbeat_response[0]['response']['responseCode'], 501)

      del heartbeat_request, heartbeat_response
    del grant_request_g3, grant_response_g3

  def generate_FDB_3_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.3"""

    # Load device info
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Update the location of CBSD to be near FSS site 'KA413' at Albright,WV
    device_b['installationParam']['latitude'] = 39.57327
    device_b['installationParam']['longitude'] = -79.61903

    # Load grant request info
    grant_g = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'KA413' which is 3625-4200 MHz.
    grant_g['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
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
        'registrationRequest': [device_b],
        'grantRequest': [grant_g],
        'conditionalRegistrationData': conditionals
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

    # Step 1: Register device (at location 'X') and request grant 'G' with SAS UUT.
    cbsd_ids, grant_ids = self.assertRegisteredAndGranted(config['registrationRequest'],
                                    config['grantRequest'],
                                    config['conditionalRegistrationData'])

    # TODO
    # Step 2: Create FSS database which includes atleast one FSS site near location 'X'.

    # Step 3: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 4: Sending Heartbeat Request
    # Construct heartbeat message
    heartbeat_request = {
        'heartbeatRequest': [{
        'cbsdId': cbsd_ids[0],
        'grantId': grant_ids[0],
        'operationState': 'GRANTED'
        }]
    }
    heartbeat_response = self._sas.Heartbeat(heartbeat_request)['heartbeatResponse']

    # Check the heartbeat response code is 500(TERMINATED_GRANT)
    self.assertEqual(heartbeat_response[0]['response']['responseCode'], 500)

    del heartbeat_request, heartbeat_response

  def generate_FDB_4_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.4"""

    # Load device info
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Update the location of CBSD to be near FSS site 'KA413' at Albright,WV
    device_b['installationParam']['latitude'] = 39.57327
    device_b['installationParam']['longitude'] = -79.61903

    # Load grant requests 'G1' and 'G2'
    grant_g1 = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'KA413' which is 3625-4200 MHz.
    grant_g1['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }
    grant_g2 = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'KA413' which is 3625-4200 MHz.
    grant_g2['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3675000000,
        'highFrequency': 3685000000
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
        'registrationRequest': device_b,
        'grantRequests': [grant_g1, grant_g2],
        'conditionalRegistrationData': conditionals
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

    device_c = config['registrationRequest']

    # Step 1: Register device(s) (at location 'X') with conditional registration data
    cbsd_ids = self.assertRegistered([device_c],
                                     config['conditionalRegistrationData'])

    # TODO
    # Step 2: Create FSS database which includes atleast one FSS site near location 'X'.

    # Step 3: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 4: Sending Grant Request 'G1'
    grant_request_g1 = {
        'grantRequest': [config['grantRequests'][0]]
    }
    grant_request_g1['grantRequest'][0]['cbsdId'] = cbsd_ids[0]
    grant_response_g1 = self._sas.Grant(grant_request_g1)['grantResponse']

    # Check grant 'G1' response (responseCode should be SUCCESS(0))
    grant_ids = []
    self.assertEqual(grant_response_g1[0]['response']['responseCode'], 0)
    self.assertTrue('cbsdId' in grant_response_g1[0])
    self.assertTrue('grantId' in grant_response_g1[0])
    grant_ids.append(grant_response_g1[0]['grantId'])

    del grant_request_g1, grant_response_g1

    # Step 5.1: Sending Heartbeat Request
    # Construct heartbeat message
    heartbeat_request = {
      'heartbeatRequest': [{
        'cbsdId': cbsd_ids[0],
        'grantId': grant_ids[0],
        'operationState': 'GRANTED'
      }]
    }
    heartbeat_response = self._sas.Heartbeat(heartbeat_request)['heartbeatResponse']
    # Check the heartbeat response code is either 0(SUCCESS) or
    # 501(SUSPENDED_GRANT)
    self.assertIn(heartbeat_response[0]['response']['responseCode'], [0, 501])

    # Sending relinquishment request for the grant 'G1'.
    relq_request = {'relinquishmentRequest': []}
    content = {
        'cbsdId': cbsd_ids[0],
        'grantId': grant_ids[0]
    }
    relq_request['relinquishmentRequest'].append(content)

    relq_response = self._sas.Relinquishment(relq_request)['relinquishmentResponse']
    # Check relinquishment response
    self.assertEqual(relq_response[0]['grantId'], grant_ids[0])
    self.assertEqual(relq_response[0]['response']['responseCode'], 0)

    del relq_request, relq_response
    del heartbeat_request, heartbeat_response

    # TODO
    # Step 6: Modify the FSS database to include modified version of FSS site S

    # Step 7: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 8: Sending grant request 'G2'
    grant_request_g2 = {
        'grantRequest': [config['grantRequests'][1]]
    }
    grant_request_g2['grantRequest'][0]['cbsdId'] = cbsd_ids[0]
    grant_response_g2 = self._sas.Grant(grant_request_g2)['grantResponse']

    # Check grant 'G2' response (responseCode should be SUCCESS(0))
    grant_ids = []
    self.assertEqual(grant_response_g2[0]['response']['responseCode'], 0)
    self.assertTrue('cbsdId' in grant_response_g2[0])
    self.assertTrue('grantId' in grant_response_g2[0])
    grant_ids.append(grant_response_g2[0]['grantId'])

    del grant_request_g2,grant_response_g2

    # Step 9: Sending Heartbeat Request
    # Construct heartbeat message
    heartbeat_request = {
      'heartbeatRequest': [{
        'cbsdId': cbsd_ids[0],
        'grantId': grant_ids[0],
        'operationState': 'GRANTED'
      }]
    }
    heartbeat_response = self._sas.Heartbeat(heartbeat_request)['heartbeatResponse']

    # Check the heartbeat response code is either 0(SUCCESS) or
    # 501(SUSPENDED_GRANT)
    self.assertIn(heartbeat_response[0]['response']['responseCode'], [0, 501])

    del heartbeat_request, heartbeat_response

  def generate_FDB_5_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.5"""

    # Load device info.
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Load grant request 'G'.
    grant_g = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'KA413' which is 3625-4200 MHz.
    grant_g['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }

    # Update the location 'X' of CBSD near FSS site 'KA413' at Albright,WV
    device_b['installationParam']['latitude'] = 39.57327
    device_b['installationParam']['longitude'] = -79.61903

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
        'registrationRequest': [device_b],
        'grantRequest': [grant_g],
        'conditionalRegistrationData': conditionals
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

    # Step 1: Register device 'C'(at location 'X') and request grant 'G' with SAS UUT.
    cbsd_ids, grant_ids = self.assertRegisteredAndGranted(
                                   config['registrationRequest'],
                                   config['grantRequest'],
                                   config['conditionalRegistrationData'])

    # TODO
    # Step 2: Create FSS database which includes at least one FSS site near

    # TODO
    # Step 3: Create GWBL database which includes at least one GWBL site near

    # Step 4: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 5: Sending Heartbeat Request
    # Construct heartbeat message
    heartbeat_request = {
        'heartbeatRequest': [{
            'cbsdId': cbsd_ids[0],
            'grantId': grant_ids[0],
            'operationState': 'GRANTED'
        }]
    }
    heartbeat_response = self._sas.Heartbeat(heartbeat_request)['heartbeatResponse']

    # Check the heartbeat response code is 500(TERMINATED_GRANT)
    self.assertEqual(heartbeat_response[0]['response']['responseCode'], 500)

    del heartbeat_request, heartbeat_response
 
  def generate_FDB_6_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.6"""

    # Load device info.
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Load grant requests 'G1' and 'G2'.
    grant_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'KA413' which is 3625-4200 MHz.
    grant_1['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }
    grant_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'KA413' which is 3625-4200 MHz.
    grant_2['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
    }
   
    # Update the location 'X' of CBSD near FSS site 'KA413' at Albright,WV
    device_b['installationParam']['latitude'] = 39.57327
    device_b['installationParam']['longitude'] = -79.61903

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
        'registrationRequest': [device_b],
        'grantRequests': [grant_1, grant_2],
        'expectedResponseCodes': [(400,), (0,)],
        'conditionalRegistrationData': conditionals
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

    # Step 1: Register device 'C'(at location 'X') with SAS UUT.
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

    # Step 5: Request grant 'G1'
    config['grantRequests'][0]['cbsdId'] = cbsd_ids[0]

    grant_request_g1 = {'grantRequest': [config['grantRequests'][0]]}
    grant_response_g1 = self._sas.Grant(grant_request_g1)['grantResponse']

    # Check the heartbeat response code is as expected (SUCCESS or INTERFERENCE)
    self.assertIn(grant_response_g1[0]['response']['responseCode'],
                      config['expectedResponseCodes'][0])

    # Step 6: Construct relinquishment request for grant 'G1'.
    relq_request = {
        'relinquishmentRequest': [{
            'cbsdId': cbsd_ids[0],
            'grantId': grant_response_g1[0]['grantId']
        }]
    }

    # Send relinquishment request for grant 'G1'.
    relq_response = self._sas.Relinquishment(relq_request)['relinquishmentResponse']
    self.assertEqual(relq_response[0]['response']['responseCode'], 0)

    del relq_request, relq_response

    # TOD0
    # Step 7: Modify the GWBL database to include a modified version of the GWBL 'W'.
    # 'W' is moved further than 150 kms from FSS site.

    # Step 8: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 9: Request grant 'G2'.
    config['grantRequests'][1]['cbsdId'] = cbsd_ids[0]

    grant_request_g2 = {'grantRequest': [config['grantRequests'][1]]}
    grant_response_g2 = self._sas.Grant(grant_request_g2)['grantResponse']

    # Check the grant response code is as expected (SUCCESS or INTERFERENCE).
    self.assertIn(grant_response_g2[0]['response']['responseCode'],
                      config['expectedResponseCodes'][1])

  def generate_FDB_7_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.7"""

    # Load device info
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Update the FCC ID of CBSD 'C' with the FCC ID 'F_ID' from FCC ID database.
    device_b['fccId'] = "F_ID"

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
        'registrationRequest': [device_b],
        'expectedResponseCodes': [(103,), (0,)],
        'conditionalRegistrationData': conditionals
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_FDB_7_default_config)
  def test_WINNF_FT_S_FDB_7(self, config_filename):
    """DPA Database Update for DPAs which cannot be monitored by an ESC."""

    # Load the configuration file
    config = loadConfig(config_filename)

    registration_request = {
        'registrationRequest': config['registrationRequest']
    }

    # Step 1: Inject FCC ID and User Id of the devices into UUT.
    self._sas_admin.InjectFccId({'fccId': registration_request['registrationRequest'][0]['fccId']})
    self._sas_admin.InjectUserId({'userId': registration_request['registrationRequest'][0]['userId']})

    # Pre-load conditional registration data for CBSD.
    if ('conditionalRegistrationData' in config)\
      and (config['conditionalRegistrationData']):
      self._sas_admin.PreloadRegistrationData(
          config['conditionalRegistrationData'])

    # Send registration request for CBSD 'C' with FCC ID 'F_ID' to SAS UUT.
    registration_response = self._sas.Registration(registration_request)['registrationResponse']

    # Check registration response,
    # responseCode should be 103(INVALID_VALUE)
    self.assertEqual(registration_response[0]['response']['responseCode'], 103)

    # TODO
    # Step 2: Create FCC ID database which includes at least one FCC ID 'F_ID'.

    # Step 3: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 4: Send again the same registration request for CBSD 'C'
    # with FCC ID 'F_ID' to SAS UUT.
    registration_response = self._sas.Registration(registration_request)['registrationResponse']

    # Check registration response,
    # responseCode should be 0(SUCCESS)
    self.assertEqual(registration_response[0]['response']['responseCode'], 0)

    # TODO
    # Step 5: Modify FCC ID database record with FCC ID 'F_ID'.

    # Step 6: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 7: Send again the same registration request for CBSD 'C'
    # with FCC ID 'F_ID' to SAS UUT.
    registration_response = self._sas.Registration(registration_request)['registrationResponse']

    # Check the registration response code is as expected (SUCCESS or INVALID_VALUE).
    self.assertIn(registration_response[0]['response']['responseCode'],
                      config['expectedResponseCodes'][1])

  def generate_FDB_8_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.8"""

    # Load device info
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))

    # Update the location of CBSD to be near FSS site 'KA413' at Albright,WV
    device_b['installationParam']['latitude'] = 39.57327
    device_b['installationParam']['longitude'] = -79.61903

    # Load grant request info
    grant_g = json.load(
                open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    # Set the grant frequency to overlap with the FSS 'KA413' which is 3625-4200 MHz.
    grant_g['operationParam']['operationFrequencyRange'] = {
        'lowFrequency': 3650000000,
        'highFrequency': 3660000000
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
        'registrationRequest': [device_b],
        'grantRequest': [grant_g],
        'conditionalRegistrationData': conditionals
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_FDB_8_default_config)
  def test_WINNF_FT_S_FDB_8(self, config_filename):
    """FSS Database Update: Scheduled Database Update."""

    # Load the configuration file
    config = loadConfig(config_filename)

    # Step 1: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 2: Register device (at location 'X') and request grant 'G' with SAS UUT.
    cbsd_ids, grant_ids = self.assertRegisteredAndGranted(config['registrationRequest'],
                                   config['grantRequest'],
                                   config['conditionalRegistrationData'])

    # TODO
    # Step 3: Create FSS database which includes atleast one FSS site near location 'X'.

    # TODO
    # Step 4: Inject the FSS database URL into the UUT

    # Step 5: Trigger daily activities
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step 6: Sending Heartbeat Request
    # Construct heartbeat message
    heartbeat_request = {
      'heartbeatRequest': [{
        'cbsdId': cbsd_ids[0],
        'grantId': grant_ids[0],
        'operationState': 'GRANTED'
      }]
    }
    heartbeat_response = self._sas.Heartbeat(heartbeat_request)['heartbeatResponse']

    # Check the heartbeat response code is 500(TERMINATED_GRANT)
    self.assertEqual(heartbeat_response[0]['grantId'], grant_ids[0])
    self.assertEqual(heartbeat_response[0]['response']['responseCode'], 500)

    del heartbeat_request, heartbeat_response
