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
"""Implementation of FPR test cases."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import os
import sas
import sas_testcase
from sas_test_harness import generateCbsdRecords
from util import winnforum_testcase, writeConfig, loadConfig, configurable_testcase,\
 addCbsdIdsToRequests, getFqdnLocalhost, getUnusedPort, getCertFilename, json_load
from testcases.WINNF_FT_S_MCP_testcase import McpXprCommonTestcase


class FSSProtectionTestcase(McpXprCommonTestcase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    self.ShutdownServers()

  def generate_FPR_1_default_config(self, filename):
    """ Generates the WinnForum configuration for FPR.1. """

    # Load FSS record
    fss_record_1 = json_load(
      os.path.join('testcases', 'testdata', 'fss_record_0.json'))
    fss_record_1['ttc'] = False

    # Load devices for SAS UUT for multiple iterations through multiple domain proxy's
    device_1 = json_load(
      os.path.join('testcases', 'testdata', 'device_a.json'))
        # Moving device_1 to a location within 40 KMs of FSS zone (9.596km)
    device_1['installationParam']['latitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['latitude'] + 0.08
    device_1['installationParam']['longitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['longitude'] + 0.08

    device_2 = json_load(
      os.path.join('testcases', 'testdata', 'device_b.json'))
        # Moving device_2 to a location within 150 KMs of FSS zone (115.243km)
    device_2['installationParam']['latitude'] = \
       fss_record_1['record']['deploymentParam'][0]['installationParam']['latitude'] + 1
    device_2['installationParam']['longitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['longitude'] + 1

    device_3 = json_load(
      os.path.join('testcases', 'testdata', 'device_c.json'))
        # Moving device_3 to a location outside 40 KMs of FSS zone(60.861km)
    device_3['installationParam']['latitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['latitude'] + 0.5
    device_3['installationParam']['longitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['longitude'] + 0.5

    device_4 = json_load(
      os.path.join('testcases', 'testdata', 'device_d.json'))
        # Moving device_4 to a location outside 150 KMs of FSS zone (182.158km)
    device_4['installationParam']['latitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['latitude']  +  1.2

    device_4['installationParam']['longitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['longitude'] + 1.2
    device_5 = json_load(
      os.path.join('testcases', 'testdata', 'device_e.json'))
        # Moving device_5 to a location within 40 KMs of FSS zone (5.425km)
    device_5['installationParam']['latitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['latitude'] + 0.02
    device_5['installationParam']['longitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['longitude'] + 0.02

    device_6 = json_load(
      os.path.join('testcases', 'testdata', 'device_f.json'))
        # Moving device_6 to a location outside 40 KMs of FSS zone (44.504km)
    device_6['installationParam']['latitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['latitude'] +0.3
    device_6['installationParam']['longitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['longitude'] + 0.3

    # Load Grant requests
    grant_request_1 = json_load(
      os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_1['operationParam']['operationFrequencyRange']['lowFrequency']  = 3575000000
    grant_request_1['operationParam']['operationFrequencyRange']['highFrequency'] = 3585000000
    grant_request_2 = json_load(
      os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_2['operationParam']['operationFrequencyRange']['lowFrequency']  = 3580000000
    grant_request_2['operationParam']['operationFrequencyRange']['highFrequency'] = 3590000000
    grant_request_3 = json_load(
      os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_3['operationParam']['operationFrequencyRange']['lowFrequency']  = 3610000000
    grant_request_3['operationParam']['operationFrequencyRange']['highFrequency'] = 3620000000
    grant_request_4 = json_load(
      os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_4['operationParam']['operationFrequencyRange']['lowFrequency']  = 3645000000
    grant_request_4['operationParam']['operationFrequencyRange']['highFrequency'] = 3655000000
    grant_request_5 = json_load(
      os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_5['operationParam']['operationFrequencyRange']['lowFrequency']  = 3675000000
    grant_request_5['operationParam']['operationFrequencyRange']['highFrequency'] = 3685000000
    grant_request_6 = json_load(
      os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_6['operationParam']['operationFrequencyRange']['lowFrequency']  = 3690000000
    grant_request_6['operationParam']['operationFrequencyRange']['highFrequency'] = 3700000000

    # device_2 and device_4 are of Category B
    # Load Conditional Data
    self.assertEqual(device_2['cbsdCategory'], 'B')
    conditionals_device_2 = {
        'cbsdCategory': device_2['cbsdCategory'],
        'fccId': device_2['fccId'],
        'cbsdSerialNumber': device_2['cbsdSerialNumber'],
        'airInterface': device_2['airInterface'],
        'installationParam': device_2['installationParam'],
        'measCapability': device_2['measCapability']
    }
    self.assertEqual(device_4['cbsdCategory'], 'B')
    conditionals_device_4 = {
        'cbsdCategory': device_4['cbsdCategory'],
        'fccId': device_4['fccId'],
        'cbsdSerialNumber': device_4['cbsdSerialNumber'],
        'airInterface': device_4['airInterface'],
        'installationParam': device_4['installationParam'],
        'measCapability': device_4['measCapability']
    }

    # Remove conditionals from registration
    del device_2['cbsdCategory']
    del device_2['airInterface']
    del device_2['installationParam']
    del device_2['measCapability']
    del device_4['cbsdCategory']
    del device_4['airInterface']
    del device_4['installationParam']
    del device_4['measCapability']

    # Registration and grant records for multiple iterations
    cbsd_records_iteration_0_domain_proxy_0 = {
        'registrationRequests': [device_1, device_3,device_4],
        'grantRequests': [grant_request_1, grant_request_3,grant_request_4],
        'conditionalRegistrationData': [conditionals_device_4]
    }
    cbsd_records_iteration_0_domain_proxy_1 = {
        'registrationRequests': [device_5,device_2],
        'grantRequests': [grant_request_5,grant_request_2],
        'conditionalRegistrationData': [conditionals_device_2]
    }

    # Protected entities records for multiple iterations
    protected_entities_iteration_0 = {
         'fssRecords': [fss_record_1]
    }

    # SAS Test Harnesses configurations,
    # Following configurations are for two SAS test harnesses for two iterations
    sas_test_harness_device_1 = json_load(
      os.path.join('testcases', 'testdata', 'device_a.json'))
    sas_test_harness_device_1['fccId'] = "test_fcc_id_g"
    sas_test_harness_device_1['userId'] = "test_user_id_g"
    sas_test_harness_device_1['installationParam']['latitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['latitude'] - 1.2
    sas_test_harness_device_1['installationParam']['longitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['longitude'] -1.2

    sas_test_harness_device_2 = json_load(
      os.path.join('testcases', 'testdata', 'device_b.json'))
    sas_test_harness_device_2['fccId'] = "test_fcc_id_h"
    sas_test_harness_device_2['userId'] = "test_user_id_h"
    sas_test_harness_device_2['installationParam']['latitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['latitude'] - 1.5
    sas_test_harness_device_2['installationParam']['longitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['longitude'] - 1.5

    # Generate Cbsd FAD Records for SAS Test Harness 0, iteration 0
    cbsd_fad_records_iteration_0_sas_test_harness_0 = generateCbsdRecords([sas_test_harness_device_1],[[grant_request_1]])
    # Generate Cbsd FAD Records for SAS Test Harness 1, iteration 0
    cbsd_fad_records_iteration_0_sas_test_harness_1 = generateCbsdRecords([sas_test_harness_device_2],[[grant_request_2]])

    # Generate SAS Test Harnesses dump records for multiple iterations
    dump_records_iteration_0_sas_test_harness_0 = {
        'cbsdRecords': cbsd_fad_records_iteration_0_sas_test_harness_0
    }

    dump_records_iteration_0_sas_test_harness_1 = {
        'cbsdRecords': cbsd_fad_records_iteration_0_sas_test_harness_1
    }

    # SAS Test Harnesses configuration
    sas_test_harness_0_config = {
        'sasTestHarnessName': 'SAS-TH-1',
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'serverCert': getCertFilename('sas.cert'),
        'serverKey': getCertFilename('sas.key'),
        'caCert': getCertFilename('ca.cert')
    }
    sas_test_harness_1_config = {
        'sasTestHarnessName': 'SAS-TH-2',
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort() ,
        'serverCert': getCertFilename('sas_1.cert'),
        'serverKey': getCertFilename('sas_1.key'),
        'caCert': getCertFilename('ca.cert')
    }

    # Create the actual config.
    iteration0_config = {
        'cbsdRequestsWithDomainProxies': [cbsd_records_iteration_0_domain_proxy_0, cbsd_records_iteration_0_domain_proxy_1],
        'cbsdRecords': [{
            'registrationRequest': device_6,
            'grantRequest': grant_request_6,
            'clientCert': getCertFilename('device_f.cert'),
            'clientKey': getCertFilename('device_f.key')
        }],
        'protectedEntities': protected_entities_iteration_0,
        'dpaActivationList': [],
        'dpaDeactivationList': [],
        'sasTestHarnessData': [dump_records_iteration_0_sas_test_harness_0, dump_records_iteration_0_sas_test_harness_1]
    }

    config = {
        'initialCbsdRequestsWithDomainProxies': self.getEmptyCbsdRequestsWithDomainProxies(2),
        'initialCbsdRecords': [],
        'iterationData': [iteration0_config],
        'sasTestHarnessConfigs': [sas_test_harness_0_config, sas_test_harness_1_config],
        'domainProxyConfigs': [{'cert': getCertFilename('domain_proxy.cert'),
                                'key': getCertFilename('domain_proxy.key')},
                               {'cert': getCertFilename('domain_proxy_1.cert'),
                                'key': getCertFilename('domain_proxy_1.key')}]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_FPR_1_default_config)
  def test_WINNF_FT_S_FPR_1(self, config_filename):
    """Multiple CBSDs from Multiple SASs Inside and Outside the Neighborhood of an FSS Station for FSS Scenario 1 with TT&C Flag = OFF"""
    config = loadConfig(config_filename)
    # Invoke MCP test steps 1 through 22.
    self.executeMcpTestSteps(config, 'xPR2')


  def generate_FPR_2_default_config(self, filename):
    """Generates the WinnForum configuration for FPR.2."""

    # Load FSS station operating at range below 3700 to 4200 MHz, TT&C flag ON.
    fss_data = json_load(
        os.path.join('testcases', 'testdata', 'fss_record_0.json'))
    fss_record = fss_data['record']
    fss_record['deploymentParam'][0]['operationParam'][
        'operationFrequencyRange']['lowFrequency'] = 3625000000
    fss_record['deploymentParam'][0]['operationParam'][
        'operationFrequencyRange']['highFrequency'] = 4200000000
    fss_data['ttc'] = True

    # Load devices and grant info for Scenario 1.
    # Loading device_1 (Cat A) to a location within 40 km of FSS,
    # frequency range outside of FSS band.
    device_1 = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_1['installationParam']['latitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['latitude'] + 0.20
    device_1['installationParam']['longitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['longitude']
    grant_request_1 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_1['operationParam'][
        'operationFrequencyRange']['lowFrequency'] = 3560000000
    grant_request_1['operationParam'][
        'operationFrequencyRange']['highFrequency'] = 3570000000

    # Loading device_2 (Cat B) to a location within 40 km of FSS,
    # frequency range outside of FSS band, overlapping device 1 band.
    device_2 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_2['installationParam']['latitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['latitude']
    device_2['installationParam']['longitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['longitude'] + 0.20
    grant_request_2 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_2['operationParam'][
        'operationFrequencyRange']['lowFrequency'] = 3565000000
    grant_request_2['operationParam'][
        'operationFrequencyRange']['highFrequency'] = 3575000000

    # Loading device_3 (Cat A) to a location within 40 km of FSS,
    # frequency range outside of FSS band.
    device_3 = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_3['installationParam']['latitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['latitude'] + 0.05
    device_3['installationParam']['longitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['longitude'] + 0.05
    grant_request_3 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_3['operationParam'][
        'operationFrequencyRange']['lowFrequency'] = 3590000000
    grant_request_3['operationParam'][
        'operationFrequencyRange']['highFrequency'] = 3600000000

    # Loading device_4 (Cat B) to a location within 40 km of FSS,
    # frequency range overlapping FSS band.
    device_4 = json_load(
        os.path.join('testcases', 'testdata', 'device_d.json'))
    device_4['installationParam']['latitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['latitude'] - 0.05
    device_4['installationParam']['longitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['longitude'] - 0.05
    grant_request_4 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_4['operationParam'][
        'operationFrequencyRange']['lowFrequency'] = 3620000000
    grant_request_4['operationParam'][
        'operationFrequencyRange']['highFrequency'] = 3630000000

    # Loading device_5 (Cat A) to a location within 40 km of FSS,
    # frequency range inside of FSS band.
    device_5 = json_load(
        os.path.join('testcases', 'testdata', 'device_e.json'))
    device_5['installationParam']['latitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['latitude'] + 0.05
    device_5['installationParam']['longitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['longitude'] - 0.05
    grant_request_5 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_5['operationParam'][
        'operationFrequencyRange']['lowFrequency'] = 3650000000
    grant_request_5['operationParam'][
        'operationFrequencyRange']['highFrequency'] = 3660000000

    # Loading device_6 (Cat A) to a location between 40 to 150 km of FSS,
    # frequency range inside of FSS band.
    device_6 = json_load(
        os.path.join('testcases', 'testdata', 'device_f.json'))
    device_6['installationParam']['latitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['latitude'] + 1.00
    device_6['installationParam']['longitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['longitude']
    grant_request_6 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_6['operationParam'][
        'operationFrequencyRange']['lowFrequency'] = 3690000000
    grant_request_6['operationParam'][
        'operationFrequencyRange']['highFrequency'] = 3700000000

    # Loading device_7 (Cat A) to a location outside 150 km of FSS,
    # frequency range inside of FSS band.
    device_7 = json_load(
        os.path.join('testcases', 'testdata', 'device_g.json'))
    device_7['installationParam']['latitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['latitude'] + 1.50
    device_7['installationParam']['longitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['longitude'] + 0.50
    grant_request_7 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_7['operationParam'][
        'operationFrequencyRange']['lowFrequency'] = 3670000000
    grant_request_7['operationParam'][
        'operationFrequencyRange']['highFrequency'] = 3680000000

    # Load Conditional Data for Cat B devices (devices 2 and 4).
    self.assertEqual(device_2['cbsdCategory'], 'B')
    conditionals_device_2 = {
        'cbsdCategory': device_2['cbsdCategory'],
        'fccId': device_2['fccId'],
        'cbsdSerialNumber': device_2['cbsdSerialNumber'],
        'airInterface': device_2['airInterface'],
        'installationParam': device_2['installationParam'],
        'measCapability': device_2['measCapability']
    }

    self.assertEqual(device_4['cbsdCategory'], 'B')
    conditionals_device_4 = {
        'cbsdCategory': device_4['cbsdCategory'],
        'fccId': device_4['fccId'],
        'cbsdSerialNumber': device_4['cbsdSerialNumber'],
        'airInterface': device_4['airInterface'],
        'installationParam': device_4['installationParam'],
        'measCapability': device_4['measCapability']
    }

    # Remove conditionals from registration
    del device_2['cbsdCategory']
    del device_2['airInterface']
    del device_2['installationParam']
    del device_2['measCapability']
    del device_4['cbsdCategory']
    del device_4['airInterface']
    del device_4['installationParam']
    del device_4['measCapability']

    # DP Registration and grant records
    cbsd_records_domain_proxy_0 = {
        'registrationRequests': [device_1, device_2, device_6],
        'grantRequests': [grant_request_1, grant_request_2, grant_request_6],
        'conditionalRegistrationData': [conditionals_device_2]
    }
    cbsd_records_domain_proxy_1 = {
        'registrationRequests': [device_3, device_4, device_7],
        'grantRequests': [grant_request_3, grant_request_4, grant_request_7],
        'conditionalRegistrationData': [conditionals_device_4]
    }

    # Protected entity record
    protected_entities = {
        'fssRecords': [fss_data]
    }

    # SAS Test Harnesses configurations,
    # Following configurations are for two SAS test harnesses
    sas_test_harness_device_1 = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    sas_test_harness_device_1['fccId'] = 'test_fcc_id_1'
    sas_test_harness_device_1['userId'] = 'test_user_id_1'

    sas_test_harness_device_2 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    sas_test_harness_device_2['fccId'] = 'test_fcc_id_2'
    sas_test_harness_device_2['userId'] = 'test_user_id_2'

    sas_test_harness_device_3 = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    sas_test_harness_device_3['fccId'] = 'test_fcc_id_3'
    sas_test_harness_device_3['userId'] = 'test_user_id_3'

    # Generate Cbsd FAD Records for SAS Test Harness 0
    cbsd_fad_records_sas_test_harness_0 = generateCbsdRecords(
        [sas_test_harness_device_1], [[grant_request_1]])

    # Generate Cbsd FAD Records for SAS Test Harness 1
    cbsd_fad_records_sas_test_harness_1 = generateCbsdRecords(
        [sas_test_harness_device_2, sas_test_harness_device_3],
        [[grant_request_4], [grant_request_6]])

    # Generate SAS Test Harnesses dump records
    dump_records_sas_test_harness_0 = {
        'cbsdRecords': cbsd_fad_records_sas_test_harness_0
    }
    dump_records_sas_test_harness_1 = {
        'cbsdRecords': cbsd_fad_records_sas_test_harness_1
    }

    # SAS Test Harnesses configuration
    sas_test_harness_0_config = {
        'sasTestHarnessName': 'SAS-TH-1',
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'serverCert': getCertFilename('sas.cert'),
        'serverKey': getCertFilename('sas.key'),
        'caCert': getCertFilename('ca.cert')
    }
    sas_test_harness_1_config = {
        'sasTestHarnessName': 'SAS-TH-2',
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'serverCert': getCertFilename('sas_1.cert'),
        'serverKey': getCertFilename('sas_1.key'),
        'caCert': getCertFilename('ca.cert')
    }

    iteration_config = {
        'cbsdRequestsWithDomainProxies': [cbsd_records_domain_proxy_0,
                                          cbsd_records_domain_proxy_1],
        'cbsdRecords': [{
            'registrationRequest': device_5,
            'grantRequest': grant_request_5,
            'clientCert': getCertFilename('device_e.cert'),
            'clientKey': getCertFilename('device_e.key')
        }],
        'protectedEntities': protected_entities,
        'dpaActivationList': [],
        'dpaDeactivationList': [],
        'sasTestHarnessData': [dump_records_sas_test_harness_0,
                               dump_records_sas_test_harness_1]
    }

    # Create the actual config.
    config = {
        'initialCbsdRequestsWithDomainProxies': self.getEmptyCbsdRequestsWithDomainProxies(2),
        'initialCbsdRecords': [],
        'iterationData': [iteration_config],
        'sasTestHarnessConfigs': [sas_test_harness_0_config,
                                  sas_test_harness_1_config],
        'domainProxyConfigs': [
            {'cert': getCertFilename('domain_proxy.cert'),
             'key': getCertFilename('domain_proxy.key')},
            {'cert': getCertFilename('domain_proxy_1.cert'),
             'key': getCertFilename('domain_proxy_1.key')}
        ]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_FPR_2_default_config)
  def test_WINNF_FT_S_FPR_2(self, config_filename):
    """Multiple CBSDs from Multiple SASs Inside and Outside the Neighborhood
    of an FSS Station for Scenario 1 with TT&C Flag = ON.
    """
    config = loadConfig(config_filename)
    # Invoke MCP test steps 1 through 22.
    self.executeMcpTestSteps(config, 'xPR2')

  def generate_FPR_3_default_config(self, filename):
    """ Generates the WinnForum configuration for FPR.3. """
      # Load FSS record
    fss_record_1 = json_load(
      os.path.join('testcases', 'testdata', 'fss_record_0.json'))
    fss_record_1['ttc'] = False
    fss_record_1['record']['deploymentParam'][0]['operationParam']['operationFrequencyRange']['lowFrequency']  = 3700000000

    # Load devices for SAS UUT for multiple iterations through multiple domain proxy's
    device_1 = json_load(
      os.path.join('testcases', 'testdata', 'device_a.json'))
        # Moving device_1 to a location within 40 KMs of FSS zone (9.596km)
    device_1['installationParam']['latitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['latitude'] - 0.02
    device_1['installationParam']['longitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['longitude'] +0.02

    device_2 = json_load(
      os.path.join('testcases', 'testdata', 'device_b.json'))
        # Moving device_2 to a location within 150 KMs of FSS zone (115.243km)
    device_2['installationParam']['latitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['latitude'] + 1
    device_2['installationParam']['longitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['longitude'] +1

    device_3 = json_load(
      os.path.join('testcases', 'testdata', 'device_c.json'))
        # Moving device_3 to a location outside 40 KMs of FSS zone(60.861km)
    device_3['installationParam']['latitude'] = fss_record_1['record']['deploymentParam'][0]['installationParam']['latitude'] + 0.5
    device_3['installationParam']['longitude'] = fss_record_1['record']['deploymentParam'][0]['installationParam']['longitude'] + 0.5

    device_4 = json_load(
      os.path.join('testcases', 'testdata', 'device_d.json'))
        # Moving device_4 to a location outside 150 KMs of FSS zone (182.158km)
    device_4['installationParam']['latitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['latitude'] + 1.2
    device_4['installationParam']['longitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['longitude'] + 1.2


    # Load Grant requests
    grant_request_1 = json_load(
      os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_1['operationParam']['operationFrequencyRange']['lowFrequency']  = 3575000000
    grant_request_1['operationParam']['operationFrequencyRange']['highFrequency'] = 3585000000
    grant_request_2 = json_load(
      os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_2['operationParam']['operationFrequencyRange']['lowFrequency']  = 3580000000
    grant_request_2['operationParam']['operationFrequencyRange']['highFrequency'] = 3590000000
    grant_request_3 = json_load(
      os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_3['operationParam']['operationFrequencyRange']['lowFrequency']  = 3610000000
    grant_request_3['operationParam']['operationFrequencyRange']['highFrequency'] = 3620000000
    grant_request_4 = json_load(
      os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_4['operationParam']['operationFrequencyRange']['lowFrequency']  = 3645000000
    grant_request_4['operationParam']['operationFrequencyRange']['highFrequency'] = 3655000000

    # device_2 and device_4 are of Category B
    # Load Conditional Data
    self.assertEqual(device_2['cbsdCategory'], 'B')
    conditionals_device_2 = {
        'cbsdCategory': device_2['cbsdCategory'],
        'fccId': device_2['fccId'],
        'cbsdSerialNumber': device_2['cbsdSerialNumber'],
        'airInterface': device_2['airInterface'],
        'installationParam': device_2['installationParam'],
        'measCapability': device_2['measCapability']
    }
    self.assertEqual(device_4['cbsdCategory'], 'B')
    conditionals_device_4 = {
        'cbsdCategory': device_4['cbsdCategory'],
        'fccId': device_4['fccId'],
        'cbsdSerialNumber': device_4['cbsdSerialNumber'],
        'airInterface': device_4['airInterface'],
        'installationParam': device_4['installationParam'],
        'measCapability': device_4['measCapability']
    }

    conditionals = [conditionals_device_2, conditionals_device_4]
    # Remove conditionals from registration
    del device_2['cbsdCategory']
    del device_2['airInterface']
    del device_2['installationParam']
    del device_2['measCapability']
    del device_4['cbsdCategory']
    del device_4['airInterface']
    del device_4['installationParam']
    del device_4['measCapability']

    # Registration and grant records for multiple iterations
    cbsd_records_iteration_0_domain_proxy_0 = {
        'registrationRequests': [device_1, device_2],
        'grantRequests': [grant_request_1, grant_request_2],
        'conditionalRegistrationData': [conditionals_device_2]
    }
    cbsd_records_iteration_0_domain_proxy_1 = {
        'registrationRequests': [device_4],
        'grantRequests': [grant_request_4],
        'conditionalRegistrationData': [conditionals_device_4]
    }

    # Protected entities records for multiple iterations
    protected_entities_iteration_0 = {
         'fssRecords': [fss_record_1]
    }

    # SAS Test Harnesses configurations,
    # Following configurations are for two SAS test harnesses for two iterations
    sas_test_harness_device_1 = json_load(
      os.path.join('testcases', 'testdata', 'device_a.json'))
    sas_test_harness_device_1['fccId'] = "test_fcc_id_e"
    sas_test_harness_device_1['userId'] = "test_user_id_e"
    sas_test_harness_device_1['installationParam']['latitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['latitude'] - 1.2
    sas_test_harness_device_1['installationParam']['longitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['longitude'] -1.2

    sas_test_harness_device_2 = json_load(
      os.path.join('testcases', 'testdata', 'device_b.json'))
    sas_test_harness_device_2['fccId'] = "test_fcc_id_f"
    sas_test_harness_device_2['userId'] = "test_user_id_f"
    sas_test_harness_device_2['installationParam']['latitude'] =  \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['latitude'] - 1.5
    sas_test_harness_device_2['installationParam']['longitude'] = \
        fss_record_1['record']['deploymentParam'][0]['installationParam']['longitude']  -1.5

    # Generate Cbsd FAD Records for SAS Test Harness 0, iteration 0
    cbsd_fad_records_iteration_0_sas_test_harness_0 = generateCbsdRecords([sas_test_harness_device_1],[[grant_request_1]])
    # Generate Cbsd FAD Records for SAS Test Harness 1, iteration 0
    cbsd_fad_records_iteration_0_sas_test_harness_1 = generateCbsdRecords([sas_test_harness_device_2],[[grant_request_2]])

    # Generate SAS Test Harnesses dump records for multiple iterations
    dump_records_iteration_0_sas_test_harness_0 = {
        'cbsdRecords': cbsd_fad_records_iteration_0_sas_test_harness_0
    }

    dump_records_iteration_0_sas_test_harness_1 = {
        'cbsdRecords': cbsd_fad_records_iteration_0_sas_test_harness_1
    }

    # SAS Test Harnesses configuration
    sas_test_harness_0_config = {
        'sasTestHarnessName': 'SAS-TH-1',
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'serverCert': getCertFilename('sas.cert'),
        'serverKey': getCertFilename('sas.key'),
        'caCert': getCertFilename('ca.cert')
    }
    sas_test_harness_1_config = {
        'sasTestHarnessName': 'SAS-TH-2',
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'serverCert': getCertFilename('sas_1.cert'),
        'serverKey': getCertFilename('sas_1.key'),
        'caCert': getCertFilename('ca.cert')
    }

    # Create the actual config.
    iteration0_config = {
        'cbsdRequestsWithDomainProxies': [cbsd_records_iteration_0_domain_proxy_0, cbsd_records_iteration_0_domain_proxy_1],
        'cbsdRecords': [{
            'registrationRequest': device_3,
            'grantRequest': grant_request_3,
            'clientCert': getCertFilename('device_c.cert'),
            'clientKey': getCertFilename('device_c.key')
        }],
        'protectedEntities': protected_entities_iteration_0,
        'dpaActivationList': [],
        'dpaDeactivationList': [],
        'sasTestHarnessData': [dump_records_iteration_0_sas_test_harness_0, dump_records_iteration_0_sas_test_harness_1]
    }

    config = {
        'initialCbsdRequestsWithDomainProxies': self.getEmptyCbsdRequestsWithDomainProxies(2),
        'initialCbsdRecords': [],
        'iterationData': [iteration0_config],
        'sasTestHarnessConfigs': [sas_test_harness_0_config, sas_test_harness_1_config],
        'domainProxyConfigs': [{'cert': getCertFilename('domain_proxy.cert'),
                                'key': getCertFilename('domain_proxy.key')},
                               {'cert': getCertFilename('domain_proxy_1.cert'),
                                'key': getCertFilename('domain_proxy_1.key')}]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_FPR_3_default_config)
  def test_WINNF_FT_S_FPR_3(self, config_filename):
    """Multiple CBSDs from Multiple SASs Inside and Outside the Neighborhood of an FSS Station for FSS Scenario 2 with TT&C Flag = OFF"""
    config = loadConfig(config_filename)
    # Invoke MCP test steps 1 through 22.
    self.executeMcpTestSteps(config, 'xPR2')

  def generate_FPR_4_default_config(self, filename):
    """Generates the WinnForum configuration for FPR.4."""

    # Load FSS station operating at range 3700 to 4200 MHz, TT&C flag ON.
    fss_data = json_load(
        os.path.join('testcases', 'testdata', 'fss_record_0.json'))
    fss_record = fss_data['record']
    fss_record['deploymentParam'][0]['operationParam'][
        'operationFrequencyRange']['lowFrequency'] = 3700000000
    fss_record['deploymentParam'][0]['operationParam'][
        'operationFrequencyRange']['highFrequency'] = 4200000000
    fss_data['ttc'] = True

    # Load devices and grant info for Scenario 1.
    # Loading device_1 (Cat A) to a location within 40 km of FSS,
    # frequency range outside of FSS band.
    device_1 = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_1['installationParam']['latitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['latitude'] + 0.20
    device_1['installationParam']['longitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['longitude']
    grant_request_1 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_1['operationParam'][
        'operationFrequencyRange']['lowFrequency'] = 3560000000
    grant_request_1['operationParam'][
        'operationFrequencyRange']['highFrequency'] = 3570000000

    # Loading device_2 (Cat B) to a location within 40 km of FSS,
    # frequency range outside of FSS band, overlapping device 1 band.
    device_2 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_2['installationParam']['latitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['latitude']
    device_2['installationParam']['longitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['longitude'] + 0.20
    grant_request_2 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_2['operationParam'][
        'operationFrequencyRange']['lowFrequency'] = 3565000000
    grant_request_2['operationParam'][
        'operationFrequencyRange']['highFrequency'] = 3575000000

    # Loading device_3 (Cat A) to a location within 40 km of FSS,
    # frequency range outside of FSS band.
    device_3 = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_3['installationParam']['latitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['latitude'] + 0.05
    device_3['installationParam']['longitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['longitude'] + 0.05
    grant_request_3 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_3['operationParam'][
        'operationFrequencyRange']['lowFrequency'] = 3590000000
    grant_request_3['operationParam'][
        'operationFrequencyRange']['highFrequency'] = 3600000000

    # Loading device_4 (Cat B) to a location within 40 km of FSS,
    # frequency range overlapping FSS band.
    device_4 = json_load(
        os.path.join('testcases', 'testdata', 'device_d.json'))
    device_4['installationParam']['latitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['latitude'] - 0.05
    device_4['installationParam']['longitude'] = fss_record[
        'deploymentParam'][0]['installationParam']['longitude'] - 0.05
    grant_request_4 = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_4['operationParam'][
        'operationFrequencyRange']['lowFrequency'] = 3620000000
    grant_request_4['operationParam'][
        'operationFrequencyRange']['highFrequency'] = 3630000000

    # Load Conditional Data for Cat B devices (devices 2 and 4).
    self.assertEqual(device_2['cbsdCategory'], 'B')
    conditionals_device_2 = {
        'cbsdCategory': device_2['cbsdCategory'],
        'fccId': device_2['fccId'],
        'cbsdSerialNumber': device_2['cbsdSerialNumber'],
        'airInterface': device_2['airInterface'],
        'installationParam': device_2['installationParam'],
        'measCapability': device_2['measCapability']
    }

    self.assertEqual(device_4['cbsdCategory'], 'B')
    conditionals_device_4 = {
        'cbsdCategory': device_4['cbsdCategory'],
        'fccId': device_4['fccId'],
        'cbsdSerialNumber': device_4['cbsdSerialNumber'],
        'airInterface': device_4['airInterface'],
        'installationParam': device_4['installationParam'],
        'measCapability': device_4['measCapability']
    }

    # Remove conditionals from registration
    del device_2['cbsdCategory']
    del device_2['airInterface']
    del device_2['installationParam']
    del device_2['measCapability']
    del device_4['cbsdCategory']
    del device_4['airInterface']
    del device_4['installationParam']
    del device_4['measCapability']

    # DP Registration and grant records
    cbsd_records_domain_proxy_0 = {
        'registrationRequests': [device_1, device_2],
        'grantRequests': [grant_request_1, grant_request_2],
        'conditionalRegistrationData': [conditionals_device_2]
    }
    cbsd_records_domain_proxy_1 = {
        'registrationRequests': [device_3],
        'grantRequests': [grant_request_3],
        'conditionalRegistrationData': []
    }

    # Protected entity record
    protected_entities = {
        'fssRecords': [fss_data]
    }

    # SAS Test Harnesses configurations,
    # Following configurations are for two SAS test harnesses
    sas_test_harness_device_1 = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    sas_test_harness_device_1['fccId'] = 'test_fcc_id_1'
    sas_test_harness_device_1['userId'] = 'test_user_id_1'

    sas_test_harness_device_2 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    sas_test_harness_device_2['fccId'] = 'test_fcc_id_2'
    sas_test_harness_device_2['userId'] = 'test_user_id_2'

    sas_test_harness_device_3 = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    sas_test_harness_device_3['fccId'] = 'test_fcc_id_3'
    sas_test_harness_device_3['userId'] = 'test_user_id_3'

    # Generate Cbsd FAD Records for SAS Test Harness 0
    cbsd_fad_records_sas_test_harness_0 = generateCbsdRecords(
        [sas_test_harness_device_1], [[grant_request_1]])

    # Generate Cbsd FAD Records for SAS Test Harness 1
    cbsd_fad_records_sas_test_harness_1 = generateCbsdRecords(
        [sas_test_harness_device_2, sas_test_harness_device_3],
        [[grant_request_2], [grant_request_3]])

    # Generate SAS Test Harnesses dump records
    dump_records_sas_test_harness_0 = {
        'cbsdRecords': cbsd_fad_records_sas_test_harness_0
    }
    dump_records_sas_test_harness_1 = {
        'cbsdRecords': cbsd_fad_records_sas_test_harness_1
    }

    # SAS Test Harnesses configuration
    sas_test_harness_0_config = {
        'sasTestHarnessName': 'SAS-TH-1',
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'serverCert': getCertFilename('sas.cert'),
        'serverKey': getCertFilename('sas.key'),
        'caCert': getCertFilename('ca.cert')
    }
    sas_test_harness_1_config = {
        'sasTestHarnessName': 'SAS-TH-2',
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'serverCert': getCertFilename('sas_1.cert'),
        'serverKey': getCertFilename('sas_1.key'),
        'caCert': getCertFilename('ca.cert')
    }

    iteration_config = {
        'cbsdRequestsWithDomainProxies': [cbsd_records_domain_proxy_0,
                                          cbsd_records_domain_proxy_1],
        'cbsdRecords': [{
            'registrationRequest': device_4,
            'grantRequest': grant_request_4,
            'conditionalRegistrationData': conditionals_device_4,
            'clientCert': getCertFilename('device_d.cert'),
            'clientKey': getCertFilename('device_d.key')
        }],
        'protectedEntities': protected_entities,
        'dpaActivationList': [],
        'dpaDeactivationList': [],
        'sasTestHarnessData': [dump_records_sas_test_harness_0,
                               dump_records_sas_test_harness_1]
    }

    # Create the actual config.
    config = {
        'initialCbsdRequestsWithDomainProxies': self.getEmptyCbsdRequestsWithDomainProxies(2),
        'initialCbsdRecords': [],
        'iterationData': [iteration_config],
        'sasTestHarnessConfigs': [sas_test_harness_0_config,
                                  sas_test_harness_1_config],
        'domainProxyConfigs': [
            {'cert': getCertFilename('domain_proxy.cert'),
             'key': getCertFilename('domain_proxy.key')},
            {'cert': getCertFilename('domain_proxy_1.cert'),
             'key': getCertFilename('domain_proxy_1.key')}
        ]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_FPR_4_default_config)
  def test_WINNF_FT_S_FPR_4(self, config_filename):
    """Multiple CBSDs from Multiple SASs Inside and Outside the Neighborhood
    of an FSS Station for Scenario 2 with TT&C Flag = ON.
    """
    config = loadConfig(config_filename)
    # Invoke MCP test steps 1 through 22.
    self.executeMcpTestSteps(config, 'xPR2')

  def generate_FPR_5_default_config(self, filename):
    """Generates the WinnForum configuration for FPR.5."""

    # Load FSS station operating at range 3600 - 3700 MHz.
    fss_data = json_load(os.path.join('testcases', 'testdata', 'fss_record_0.json'))
    fss = fss_data['record']
    fss['deploymentParam'][0]['operationParam']['operationFrequencyRange']\
        ['lowFrequency'] = 3600000000
    fss['deploymentParam'][0]['operationParam']['operationFrequencyRange']\
        ['highFrequency'] = 3700000000

    # Load GWBL operating at range 3650 - 3700 MHz.
    gwbl = json_load(
        os.path.join('testcases', 'testdata', 'gwbl_record_0.json'))
    gwbl['record']['deploymentParam'][0]['operationParam']['operationFrequencyRange']\
        ['lowFrequency'] = 3650000000
    gwbl['record']['deploymentParam'][0]['operationParam']['operationFrequencyRange']\
        ['highFrequency'] = 3700000000

    # Load device info
    device_1 = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_2 = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_3 = json_load(
        os.path.join('testcases', 'testdata', 'device_e.json'))

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
    grant_1 = json_load(os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_1['operationParam']['operationFrequencyRange']['lowFrequency'] = 3650000000
    grant_1['operationParam']['operationFrequencyRange']['highFrequency'] = 3660000000
    grant_2 = json_load(os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_2['operationParam']['operationFrequencyRange']['lowFrequency'] = 3650000000
    grant_2['operationParam']['operationFrequencyRange']['highFrequency'] = 3660000000
    grant_3 = json_load(os.path.join('testcases', 'testdata', 'grant_0.json'))
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
