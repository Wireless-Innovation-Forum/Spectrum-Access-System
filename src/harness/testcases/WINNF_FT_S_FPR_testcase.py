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
import logging
from util import winnforum_testcase, writeConfig, loadConfig, configurable_testcase,\
 addCbsdIdsToRequests

class FSSProtectionTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass
    
  def generate_FPR_5_default_config(self, filename):
    """Generates the WinnForum configuration for FPR.5."""

    # Load FSS station operating at range 3600 - 3700 MHz.
    fss_data = json.load(open(os.path.join('testcases', 'testdata', 'fss_record_0.json')))
    fss = fss_data['record']
    fss['deploymentParam'][0]['operationParam']['operationFrequencyRange']\
        ['lowFrequency'] = 3600000000
    fss['deploymentParam'][0]['operationParam']['operationFrequencyRange']\
        ['highFrequency'] = 3700000000

    # Load GWBL operating at range 3650 - 3700 MHz.
    gwbl = json.load(
        open(os.path.join('testcases', 'testdata', 'gwbl_record_0.json')))
    gwbl['record']['deploymentParam'][0]['operationParam']['operationFrequencyRange']\
        ['lowFrequency'] = 3650000000
    gwbl['record']['deploymentParam'][0]['operationParam']['operationFrequencyRange']\
        ['highFrequency'] = 3700000000

    # Load device info
    device_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_3 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))

    # Move devices within 150km of FSS
    device_1['installationParam']['latitude'] = \
        fss['deploymentParam'][0]['installationParam']['latitude'] + 0.05
    device_1['installationParam']['longitude'] = \
        fss['deploymentParam'][0]['installationParam']['longitude'] + 0.05
    device_2['installationParam']['latitude'] = \
        fss['deploymentParam'][0]['installationParam']['latitude'] + 0.12
    device_2['installationParam']['longitude'] = \
        fss['deploymentParam'][0]['installationParam']['longitude'] + 0.05
    device_3['installationParam']['latitude'] = \
        fss['deploymentParam'][0]['installationParam']['latitude'] + 0.15
    device_3['installationParam']['longitude'] = \
        fss['deploymentParam'][0]['installationParam']['longitude'] + 0.05

    # Move GWBL within 150km of FSS
    gwbl['record']['deploymentParam'][0]['installationParam']['latitude'] = \
        fss['deploymentParam'][0]['installationParam']['latitude'] + 0.1
    gwbl['record']['deploymentParam'][0]['installationParam']['longitude'] = \
        fss['deploymentParam'][0]['installationParam']['longitude']

    # Create info for grants
    grant_1 = json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_1['operationParam']['operationFrequencyRange']['lowFrequency'] = 3650000000
    grant_1['operationParam']['operationFrequencyRange']['highFrequency'] = 3660000000
    grant_2 = json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_2['operationParam']['operationFrequencyRange']['lowFrequency'] = 3650000000
    grant_2['operationParam']['operationFrequencyRange']['highFrequency'] = 3660000000
    grant_3 = json.load(open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_3['operationParam']['operationFrequencyRange']['lowFrequency'] = 3650000000
    grant_3['operationParam']['operationFrequencyRange']['highFrequency'] = 3660000000

    # Creating conditionals for Cat B device
    self.assertEqual(device_1['cbsdCategory'], 'B')
    conditionalParameters = {
        'cbsdCategory': device_1['cbsdCategory'],
        'fccId': device_1['fccId'],
        'cbsdSerialNumber': device_1['cbsdSerialNumber'],
        'airInterface': device_1['airInterface'],
        'installationParam': device_1['installationParam'],
        'measCapability': device_1['measCapability']
    }
    del device_1['cbsdCategory']
    del device_1['airInterface']
    del device_1['installationParam']
    del device_1['measCapability']

    # Create the actual config.
    conditionals = [conditionalParameters]
    config = {
      'registrationRequests': [device_1, device_2, device_3],
      'conditionalRegistrationData': conditionals,
      'grantRequests': [grant_1, grant_2, grant_3],
      'gwblRecord': gwbl,
      'fssRecord': fss_data
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_FPR_5_default_config)
  def test_WINNF_FT_S_FPR_5(self, config_filename):
    """[Configurable] Grant Requests from one or more CBSDs Inside an FSS-GWBL Exclusion Zone."""

    config = loadConfig(config_filename)
        
    # Light checking of the config file
    self.assertEqual(len(config['registrationRequests']), len(config['grantRequests']))

    # Load the FSS
    self._sas_admin.InjectFss(config['fssRecord'])

    # Load the GWBL
    self._sas_admin.InjectWisp(config['gwblRecord'])

    # Trigger CPAS activity
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete() 

    # Register N > 0 CBSDs
    cbsd_ids = self.assertRegistered(config['registrationRequests'],config['conditionalRegistrationData'])

    # Add cbsdIds to grants
    grant_request = config['grantRequests']
    addCbsdIdsToRequests(cbsd_ids, grant_request)

    # Send grant request and get response
    request = {'grantRequest': grant_request}
    response = self._sas.Grant(request)['grantResponse']

    # Check grant response
    self.assertEqual(len(response), len(cbsd_ids))
    for response_num in response:
      self.assertEqual(response_num['response']['responseCode'], 400)

