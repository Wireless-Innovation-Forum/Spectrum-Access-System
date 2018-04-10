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

import logging
import json
import os

import sas
import sas_testcase

from util import configurable_testcase, writeConfig, loadConfig, getCertificateFingerprint
from test_harness_objects import DomainProxy
from full_activity_dump_helper import getFullActivityDumpSasTestHarness, getFullActivityDumpSasUut
from sas_test_harness import SasTestHarnessServer, generateCbsdRecords

LOW_FREQUENCY_LIMIT_HZ = 3550000000
HIGH_FREQUENCY_LIMIT_HZ = 3650000000


class FederalIncumbentProtectionTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def frequencyInBand(self, low_frequency, high_frequency):
    """Returns True iff the given range overlaps with the 3550MHz to 3650MHz range."""
    return (LOW_FREQUENCY_LIMIT_HZ <= low_frequency <= HIGH_FREQUENCY_LIMIT_HZ
            or
            LOW_FREQUENCY_LIMIT_HZ <= high_frequency <= HIGH_FREQUENCY_LIMIT_HZ)

  def generate_IPR_1_default_config(self, filename):
    """Generates the WinnForum configuration for IPR_1"""

    # Load Devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))

    # Pre-load conditionals and remove reg conditional fields from registration
    # request.
    conditional_keys = [
        'cbsdCategory', 'fccId', 'cbsdSerialNumber', 'airInterface',
        'installationParam', 'measCapability'
    ]
    reg_conditional_keys = [
        'cbsdCategory', 'airInterface', 'installationParam', 'measCapability'
    ]
    conditionals_b = {key: device_b[key] for key in conditional_keys}
    conditionals_c = {key: device_c[key] for key in conditional_keys}
    device_b = {
        key: device_b[key]
        for key in device_b
        if key not in reg_conditional_keys
    }
    device_c = {
        key: device_c[key]
        for key in device_c
        if key not in reg_conditional_keys
    }

    # Load grant requests.
    grant_a = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_b = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_c = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))

    sas_test_harness_config = {
        'sasTestHarnessName':
            'SAS-Test-Harness-1',
        'hostName':
            'localhost',
        'port':
            9001,
        'serverCert':
            os.path.join('certs', 'server.cert'),
        'serverKey':
            os.path.join('certs', 'server.key'),
        'caCert':
            os.path.join('certs', 'ca.cert'),
        'fullActivityDumpRecords': [
            generateCbsdRecords([device_a], [[grant_a]])
        ]
    }

    dpa_1 = {
       'dpaId': 'east_dpa_4',
       'frequencyRange': {'lowFrequency': 3550000000, 'highFrequency': 3650000000}
    }

    config = {
        'sasTestHarnessConfigs': [sas_test_harness_config],
        'registrationRequestsN2': [device_b],
        'grantRequestsN2': [grant_b],
        'conditionalRegistrationDataN2': [conditionals_b],
        'registrationRequestsN3': [device_c],
        'grantRequestsN3': [grant_c],
        'conditionalRegistrationDataN3': [conditionals_c],
        'dpas': [dpa_1]
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_IPR_1_default_config)
  def test_WINNF_FT_S_IPR_1(self, config_filename):
    """In the absence of an ESC, SAS protects all ESC-monitored DPAs."""
    config = loadConfig(config_filename)
    self.assertValidConfig(
        config, {
            'sasTestHarnessConfigs': list,
            'registrationRequestsN2': list,
            'grantRequestsN2': list,
            'registrationRequestsN3': list,
            'grantRequestsN3': list,
            'conditionalRegistrationDataN2': list,
            'conditionalRegistrationDataN3': list,
            'dpas', list
        })
    # SAS UUT loads DPAs.
    self._sas_admin.TriggerLoadDpas()

    # Steps 2 & 3 can be interleaved.
    test_harnesses = []
    for test_harness_config in config['sasTestHarnessConfigs']:
      # Create test harness, notify the SAS UUT, and load FAD records.
      test_harness = SasTestHarnessServer(
          test_harness_config['sasTestHarnessName'],
          test_harness_config['hostName'], test_harness_config['port'],
          test_harness_config['serverCert'], test_harness_config['serverKey'],
          test_harness_config['caCert'])
      test_harness.start()
      self._sas_admin.InjectPeerSas({
          'certificateHash':
              getCertificateFingerprint(test_harness_config['serverCert']),
          'url':
              test_harness.getBaseUrl()
      })
      test_harness.writeFadRecords(
          test_harness_config['fullActivityDumpRecords'])
      test_harnesses.append(test_harness)

    # Register N2 CBSDs with the SAS UUT and request Grants.
    n2_domain_proxy = DomainProxy(self)
    n2_domain_proxy.registerCbsdsAndRequestGrants(
        config['registrationRequestsN2'],
        config['grantRequestsN2'],
        conditional_registration_data=config['conditionalRegistrationDataN2'])

    # Trigger CPAS.
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Register N3 CBSDs with the SAS UUT and request Grants.
    n3_domain_proxy = DomainProxy(self)
    n3_domain_proxy.registerCbsdsAndRequestGrants(
        config['registrationRequestsN3'],
        config['grantRequestsN3'],
        conditional_registration_data=config['conditionalRegistrationDataN3'])

    # Heartbeat all SAS UUT CBSDS
    n2_domain_proxy.heartbeatForAllActiveGrants()
    n3_domain_proxy.heartbeatForAllActiveGrants()

    # None of the N3 CBSDS should be authorized.
    for cbsd in n3_domain_proxy.getCbsdsWithAtLeastOneAuthorizedGrant():
      for operationParam in cbsd.getOperationParamsOfAllAuthorizedGrants():
        # By definition the N3 CBSDs are in a DPA neighborhood. Check frequency.
        self.assertFalse(
            self.frequencyInBand(
                operationParam['operationFrequencyRange']['lowFrequency'],
                operationParam['operationFrequencyRange']['highFrequency']),
            msg='CBSD (cbsd_id=%s, fcc_id=%s, sn=%s) '
            'is authorized after IPR.1 step 7. SAS UUT FAILS this test. '
            '(If this config is new please verify the CBSD is in a DPA)' %
            (cbsd.getCbsdId(), cbsd.getRegistrationRequest()['fccId'],
             cbsd.getRegistrationRequest()['cbsdSerialNumber']))

    # Get SAS UUT FAD and Test Harness FADs.
    sas_uut_fad = getFullActivityDumpSasUut(self._sas, self._sas_admin)
    test_harness_fads = []
    for test_harness in test_harnesses:
      test_harness_fads.append(
          getFullActivityDumpSasTestHarness(
              test_harness.getSasTestHarnessInterface()))

    # Trigger CPAS.
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Initialize DPA objects and calculate movelist for each DPA.
    # TODO(taran): Update once DPA movelist reference model changes are reviewed.
    dpas = [Dpa(dpa) for dpa in config['dpas']]
    for dpa in dpas:
      dpa.SetGrantsFromFad(sas_uut_fad, test_harness_fads)
      dpa.CalcMoveLists()
    # Heartbeat SAS UUT grants.
    n2_domain_proxy.heartbeatForAllActiveGrants()
    n3_domain_proxy.heartbeatForAllActiveGrants()
    # Get CbsdGrantInfo list of SAS UUT grants that are in an authorized state.
    grant_info = getGrantsFromDomainProxies([n2_domain_proxy, n3_domain_proxy])

    # Check grants do not exceed each DPAs interference threshold.
    for dpa in dpas:
      self.assertTrue(dpa.CheckInterference(channel=(3550, 3650), sas_uut_active_grants=grant_info, margin_db=10))
