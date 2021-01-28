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

import json
import os

import sas
import sas_testcase
from sas_test_harness import SasTestHarnessServer, generateCbsdRecords, \
    generatePpaRecords
from util import addCbsdIdsToRequests, winnforum_testcase, configurable_testcase, writeConfig, \
  loadConfig, getRandomLatLongInPolygon, makePpaAndPalRecordsConsistent, \
  getFqdnLocalhost, getUnusedPort, getCertFilename, json_load
from testcases.WINNF_FT_S_MCP_testcase import McpXprCommonTestcase


class GwpzProtectionTestcase(McpXprCommonTestcase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    self.ShutdownServers()

  def generate_GPR_1_default_config(self, filename):
    """ Generates the WinnForum configuration for GPR.1. """

    # Load GWPZ Record
    gwpz_record_1 = json_load(
      os.path.join('testcases', 'testdata', 'gwpz_record_0.json'))

    # Load devices info
    device_1 = json_load(
      os.path.join('testcases', 'testdata', 'device_a.json'))
    # Moving device_1 to a location within 40 KMs of GWPZ zone
    device_1['installationParam']['latitude'] = 39.10448
    device_1['installationParam']['longitude'] = -99.7792

    device_2 = json_load(
      os.path.join('testcases', 'testdata', 'device_b.json'))
    # Moving device_2 to a location outside 40 KMs of GWPZ zone
    device_2['installationParam']['latitude'] = 37.83075
    device_2['installationParam']['longitude'] = -107.65025

    device_3 = json_load(
      os.path.join('testcases', 'testdata', 'device_c.json'))
    # Moving device_3 to a location inside GWPZ zone
    device_3['installationParam']['latitude'], \
    device_3['installationParam']['longitude'] = getRandomLatLongInPolygon(gwpz_record_1)

    device_4 = json_load(
      os.path.join('testcases', 'testdata', 'device_d.json'))
    # Moving device_4 to a location outside 40 KMs of GWPZ zone
    device_4['installationParam']['latitude'] = 38.0934
    device_4['installationParam']['longitude'] = -106.91676

    # Load Grant requests
    grant_request_1 = json_load(
      os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_2 = json_load(
      os.path.join('testcases', 'testdata', 'grant_1.json'))
    grant_request_3 = json_load(
      os.path.join('testcases', 'testdata', 'grant_2.json'))
    grant_request_4 = json_load(
      os.path.join('testcases', 'testdata', 'grant_0.json'))

    # device_b and device_d are Category B
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

    # Registration and grant records
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
        'gwpzRecords': [gwpz_record_1]
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
        'sasTestHarnessData': []
    }

    # Create the actual config.
    config = {
        'initialCbsdRequestsWithDomainProxies': self.getEmptyCbsdRequestsWithDomainProxies(2),
        'initialCbsdRecords': [],
        'iterationData': [iteration_config],
        'sasTestHarnessConfigs': [],
        'domainProxyConfigs': [{
            'cert': getCertFilename('domain_proxy.cert'),
            'key': getCertFilename('domain_proxy.key')
        }, {
            'cert': getCertFilename('domain_proxy_1.cert'),
            'key': getCertFilename('domain_proxy_1.key')
        }]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_GPR_1_default_config)
  def test_WINNF_FT_S_GPR_1(self, config_filename):
    """Single SAS GWPZ Protection
    """
    config = loadConfig(config_filename)
    # Invoke MCP test steps 1 through 22.
    self.executeMcpTestSteps(config, 'xPR1')

  def generate_GPR_2_default_config(self, filename):
    """ Generates the WinnForum configuration for GPR.2. """

    # Load GWPZ Record
    gwpz_record_1 = json_load(
      os.path.join('testcases', 'testdata', 'gwpz_record_0.json'))

    # Load devices info
    device_1 = json_load(
      os.path.join('testcases', 'testdata', 'device_a.json'))
    # Moving device_1 to a location within 40 KMs of GWPZ zone
    device_1['installationParam']['latitude'] = 39.10448
    device_1['installationParam']['longitude'] = -99.7792

    device_2 = json_load(
      os.path.join('testcases', 'testdata', 'device_b.json'))
    # Moving device_2 to a location outside 40 KMs of GWPZ zone
    device_2['installationParam']['latitude'] = 37.83075
    device_2['installationParam']['longitude'] = -107.65025

    device_3 = json_load(
      os.path.join('testcases', 'testdata', 'device_c.json'))
    # Moving device_3 to a location inside GWPZ zone
    device_3['installationParam']['latitude'], \
    device_3['installationParam']['longitude'] = getRandomLatLongInPolygon(gwpz_record_1)

    device_4 = json_load(
      os.path.join('testcases', 'testdata', 'device_d.json'))
    # Moving device_4 to a location outside 40 KMs of GWPZ zone
    device_4['installationParam']['latitude'] = 38.0934
    device_4['installationParam']['longitude'] = -106.91676

    # Load Grant requests
    grant_request_1 = json_load(
      os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_1['operationParam']['operationFrequencyRange']['lowFrequency'] = 3650000000
    grant_request_1['operationParam']['operationFrequencyRange']['highFrequency'] = 3655000000

    grant_request_2 = json_load(
      os.path.join('testcases', 'testdata', 'grant_1.json'))
    grant_request_2['operationParam']['operationFrequencyRange']['lowFrequency'] = 3660000000
    grant_request_2['operationParam']['operationFrequencyRange']['highFrequency'] = 3665000000

    grant_request_3 = json_load(
      os.path.join('testcases', 'testdata', 'grant_2.json'))
    grant_request_3['operationParam']['operationFrequencyRange']['lowFrequency'] = 3670000000
    grant_request_3['operationParam']['operationFrequencyRange']['highFrequency'] = 3680000000

    grant_request_4 = json_load(
      os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_4['operationParam']['operationFrequencyRange']['lowFrequency'] = 3690000000
    grant_request_4['operationParam']['operationFrequencyRange']['highFrequency'] = 3700000000

    # device_b and device_d are Category B
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

    # Registration and grant records
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
        'gwpzRecords': [gwpz_record_1]
    }

    # SAS Test Harnesses configurations,
    # Following configurations are for two SAS test harnesses
    sas_test_harness_device_1 = json_load(
      os.path.join('testcases', 'testdata', 'device_a.json'))
    sas_test_harness_device_1['fccId'] = "test_fcc_id_e"
    sas_test_harness_device_1['userId'] = "test_user_id_e"

    sas_test_harness_device_2 = json_load(
      os.path.join('testcases', 'testdata', 'device_b.json'))
    sas_test_harness_device_2['fccId'] = "test_fcc_id_f"
    sas_test_harness_device_2['userId'] = "test_user_id_f"

    sas_test_harness_device_3 = json_load(
      os.path.join('testcases', 'testdata', 'device_c.json'))
    sas_test_harness_device_3['fccId'] = "test_fcc_id_g"
    sas_test_harness_device_3['userId'] = "test_user_id_g"

    # Generate Cbsd FAD Records for SAS Test Harness 0
    cbsd_fad_records_sas_test_harness_0 = generateCbsdRecords(
                                          [sas_test_harness_device_1],
                                          [[grant_request_1]]
    )

    # Generate Cbsd FAD Records for SAS Test Harness 1
    cbsd_fad_records_sas_test_harness_1 = generateCbsdRecords(
                                          [sas_test_harness_device_2, sas_test_harness_device_3],
                                          [[grant_request_2], [grant_request_3]]
    )

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
        'domainProxyConfigs': [{
             'cert': getCertFilename('domain_proxy.cert'),
             'key': getCertFilename('domain_proxy.key')
        }, {
             'cert': getCertFilename('domain_proxy_1.cert'),
             'key': getCertFilename('domain_proxy_1.key')}]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_GPR_2_default_config)
  def test_WINNF_FT_S_GPR_2(self, config_filename):
    """Multiple SAS GWPZ Protection
    """
    config = loadConfig(config_filename)
    # Invoke MCP test steps 1 through 22.
    self.executeMcpTestSteps(config, 'xPR2')

  def generate_GPR_3_default_config(self, filename):
    """ Generates the WinnForum configuration for GPR.3 """

    # Load GWPZ Record
    gwpz_record_1 = json_load(
      os.path.join('testcases', 'testdata', 'gwpz_record_0.json'))

    # Load devices info
    device_1 = json_load(
      os.path.join('testcases', 'testdata', 'device_a.json'))
    # Moving device_1 to a location inside GWPZ zone
    device_1['installationParam']['latitude'], \
    device_1['installationParam']['longitude'] = getRandomLatLongInPolygon(gwpz_record_1)

    device_2 = json_load(
      os.path.join('testcases', 'testdata', 'device_b.json'))
    # Moving device_2 to a location inside GWPZ zone
    device_2['installationParam']['latitude'], \
    device_2['installationParam']['longitude'] = getRandomLatLongInPolygon(gwpz_record_1)

    # Load Grant requests
    grant_request_1 = json_load(
      os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_request_1['operationParam']['operationFrequencyRange']['lowFrequency'] = 3650000000
    grant_request_1['operationParam']['operationFrequencyRange']['highFrequency'] = 3655000000

    grant_request_2 = json_load(
      os.path.join('testcases', 'testdata', 'grant_1.json'))
    grant_request_2['operationParam']['operationFrequencyRange']['lowFrequency'] = 3660000000
    grant_request_2['operationParam']['operationFrequencyRange']['highFrequency'] = 3665000000

    # device_b is Category B
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

    conditionals = [conditionals_device_2]

    # Remove conditionals from registration
    del device_2['cbsdCategory']
    del device_2['airInterface']
    del device_2['installationParam']
    del device_2['measCapability']

    devices = [device_1, device_2]
    grants = [grant_request_1, grant_request_2]

    # Create the actual config.
    config = {
        'registrationRequests': devices,
        'grantRequests': grants,
        'conditionalRegistrationData': conditionals,
        'gwpzRecord': gwpz_record_1
      }
    writeConfig(filename, config)

  @configurable_testcase(generate_GPR_3_default_config)
  def test_WINNF_FT_S_GPR_3(self, config_filename):
    """GWPZ Exclusion Zone
      One or more CBSDs, located inside a GWPZ, request Grants and are rejected
    """
    config = loadConfig(config_filename)

    # Step1: Admin Test Harness injects a GWPZ into the SAS UUT
    self._sas_admin.InjectWisp(config['gwpzRecord'])

    # Step2: Admin Test Harness triggers CPAS and waits until completion of CPAS
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Step3: DP Test Harness registers N > 0 CBSDs
    cbsd_ids = self.assertRegistered(config['registrationRequests'], config['conditionalRegistrationData'])

    # Step4: DP Test Harness requests one Grant per registered CBSD
    grant_request = config['grantRequests']
    addCbsdIdsToRequests(cbsd_ids, grant_request)

    request = {'grantRequest': grant_request}
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), len(grant_request))

    for response_num, response in enumerate(response):
      self.assertEqual(response['cbsdId'], request['grantRequest'][response_num]['cbsdId'])
      self.assertEqual(response['response']['responseCode'], 400)
