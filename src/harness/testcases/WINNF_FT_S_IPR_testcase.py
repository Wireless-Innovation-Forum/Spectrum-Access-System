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
import time

import sas
import sas_testcase

from util import buildDpaActivationMessage, configurable_testcase, writeConfig, loadConfig, getCertificateFingerprint
from test_harness_objects import DomainProxy
from full_activity_dump_helper import getFullActivityDumpSasTestHarness, getFullActivityDumpSasUut
from sas_test_harness import SasTestHarnessServer, generateCbsdRecords
from reference_models.dpa import dpa_mgr
from reference_models.common import data

LOW_FREQUENCY_LIMIT_HZ = 3550000000
HIGH_FREQUENCY_LIMIT_HZ = 3650000000
ONE_MHZ = 1000000


class FederalIncumbentProtectionTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def frequencyInBand(self, low_frequency, high_frequency):
    """Returns True iff the given range overlaps with the 3550-3650MHz range."""
    return (LOW_FREQUENCY_LIMIT_HZ <= low_frequency <= HIGH_FREQUENCY_LIMIT_HZ
            or
            LOW_FREQUENCY_LIMIT_HZ <= high_frequency <= HIGH_FREQUENCY_LIMIT_HZ)

  def generate_IPR_1_default_config(self, filename):
    """Generates the WinnForum configuration for IPR_1."""

    # Load Devices.
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a['installationParam']['latitude'] = 30.71570
    device_a['installationParam']['longitude'] = -88.09350

    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_b['installationParam']['latitude'] = 30.71570
    device_b['installationParam']['longitude'] = -88.09350
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_c['installationParam']['latitude'] = 30.71570
    device_c['installationParam']['longitude'] = -88.09350

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
        'frequencyRange': {
            'lowFrequency': 3620000000,
            'highFrequency': 3630000000
        },
        'points_builder': 'default (25, 10, 10, 10)',
        'movelistMargin': 10
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
            'dpas': list
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
      for operation_param in cbsd.getOperationParamsOfAllAuthorizedGrants():
        # By definition the N3 CBSDs are in a DPA neighborhood. Check frequency.
        self.assertFalse(
            self.frequencyInBand(
                operation_param['operationFrequencyRange']['lowFrequency'],
                operation_param['operationFrequencyRange']['highFrequency']),
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
    dpas = []
    for dpa_config in config['dpas']:
      dpa = dpa_mgr.BuildDpa(dpa_config['dpaId'], dpa_config['points_builder'])
      freq_range_low = dpa_config['frequencyRange']['lowFrequency'] / ONE_MHZ
      freq_range_high = dpa_config['frequencyRange']['highFrequency'] / ONE_MHZ
      dpa.ResetFreqRange([(freq_range_low, freq_range_high)])
      dpa.SetGrantsFromFad(sas_uut_fad, test_harness_fads)
      dpa.ComputeMoveLists()
      dpas.append(dpa)
    # Heartbeat SAS UUT grants.
    n2_domain_proxy.heartbeatForAllActiveGrants()
    n3_domain_proxy.heartbeatForAllActiveGrants()
    # Get CbsdGrantInfo list of SAS UUT grants that are in an authorized state.
    grant_info = data.getAuthorizedGrantsFromDomainProxies([n2_domain_proxy, n3_domain_proxy])

    # Check grants do not exceed each DPAs interference threshold.
    for dpa, dpa_config in zip(dpas, config['dpas']):
      self.assertTrue(dpa.CheckInterference(
          sas_uut_active_grants=grant_info,
          margin_db=dpa_config['movelistMargin']))

  def generate_IPR_2_default_config(self, filename):
    """Generates the WinnForum configuration for IPR_2"""

    # Load Devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a['installationParam']['latitude'] = 30.71570
    device_a['installationParam']['longitude'] = -88.09350
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_b['installationParam']['latitude'] = 30.71571
    device_b['installationParam']['longitude'] = -88.09351

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
    device_b = {
        key: device_b[key]
        for key in device_b
        if key not in reg_conditional_keys
    }

    # Load grant requests.
    grant_a = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_b = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))

    sas_test_harness_config = {
        'sasTestHarnessName':
            'SAS-Test-Harness-1',
        'hostName':
            'localhost',
        'port':
            9002,
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
        'frequencyRange': {
            'lowFrequency': 3620000000,
            'highFrequency': 3630000000
        },
        'points_builder': 'default (25, 10, 10, 10)',
        'movelistMargin': 10
    }
    dpa_2 = {
        'dpaId': 'east_dpa_4',
        'frequencyRange': {
            'lowFrequency': 3610000000,
            'highFrequency': 3620000000
        },
        'points_builder': 'default (25, 10, 10, 10)',
        'movelistMargin': 10
    }
    dpa_3 = {
        'dpaId': 'east_dpa_3',
        'frequencyRange': {
            'lowFrequency': 3620000000,
            'highFrequency': 3630000000
        },
        'points_builder': 'default (25, 10, 10, 10)',
        'movelistMargin': 10
    }
    dpa_4 = {
        'dpaId': 'west_dpa_4',
        'frequencyRange': {
            'lowFrequency': 3610000000,
            'highFrequency': 3620000000
        },
        'points_builder': 'default (25, 10, 10, 10)',
        'movelistMargin': 10
    }

    domain_proxy = {
        'registrationRequests': [device_b],
        'grantRequests': [grant_b],
        'conditionalRegistrationData': [conditionals_b],
        'cert': os.path.join('certs', 'domain_proxy.cert'),
        'key': os.path.join('certs', 'domain_proxy.key')
    }

    config = {
        'sasTestHarnessConfigs': [sas_test_harness_config],
        'domainProxies': [domain_proxy],
        'dpas': [dpa_1, dpa_2, dpa_3, dpa_4],
        'pauseTime': 60
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_IPR_2_default_config)
  def test_WINNF_FT_S_IPR_2(self, config_filename):
    """CBSDs Grants after DPA Activation."""
    config = loadConfig(config_filename)
    self.assertValidConfig(
        config, {
            'sasTestHarnessConfigs': list,
            'domainProxies': list,
            'dpas': list,
            'pauseTime': int
        })
    # Light checking that DPAs match the spec constraints.
    self.assertEqual(len(config['dpas']), 4)
    self.assertEqual(config['dpas'][0]['dpaId'], config['dpas'][1]['dpaId'])
    self.assertNotEqual(config['dpas'][0]['dpaId'], config['dpas'][2]['dpaId'])
    self.assertNotEqual(config['dpas'][0]['dpaId'], config['dpas'][3]['dpaId'])
    self.assertNotEqual(config['dpas'][2]['dpaId'], config['dpas'][3]['dpaId'])
    self.assertNotEqual(config['dpas'][0]['frequencyRange'], config['dpas'][1]['frequencyRange'])
    self.assertDictEqual(config['dpas'][0]['frequencyRange'], config['dpas'][2]['frequencyRange'])
    self.assertDictEqual(config['dpas'][1]['frequencyRange'], config['dpas'][3]['frequencyRange'])

    # SAS UUT loads DPAs and is informed they are all inactive.
    self._sas_admin.TriggerLoadDpas()
    self._sas_admin.TriggerBulkDpaActivation({'activate': False})

    # Steps 3 & 4 can be interleaved.
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


    # Register N2 CBSDs and request grants with SAS UUT from ND proxies.
    domain_proxies = []
    for domain_proxy_config in config['domainProxies']:
      domain_proxy = DomainProxy(self,
                                 ssl_cert=domain_proxy_config['cert'],
                                 ssl_key=domain_proxy_config['key'])
      domain_proxy.registerCbsdsAndRequestGrants(
          domain_proxy_config['registrationRequests'],
          domain_proxy_config['grantRequests'],
          conditional_registration_data=domain_proxy_config['conditionalRegistrationData'])
      domain_proxies.append(domain_proxy)

    # Trigger, wait and download FAD records from SAS UUT and test harnesses.
    sas_uut_fad = getFullActivityDumpSasUut(self._sas, self._sas_admin)
    test_harness_fads = []
    for test_harness in test_harnesses:
      test_harness_fads.append(
          getFullActivityDumpSasTestHarness(
              test_harness.getSasTestHarnessInterface()))

    # Trigger CPAS.
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Calculate DPA movelists for each DPA.
    # DPA/channel pairs must be in the order:
    #   (D_i, C_j)
    #   (D_i, C_l)
    #   (D_i+1, C_j)
    #   (D_k, C_l)
    all_dpas = []
    for dpa_config in config['dpas']:
      dpa = dpa_mgr.BuildDpa(dpa_config['dpaId'], dpa_config['points_builder'])
      freq_range_low = dpa_config['frequencyRange']['lowFrequency'] / ONE_MHZ
      freq_range_high = dpa_config['frequencyRange']['highFrequency'] / ONE_MHZ
      dpa.ResetFreqRange([(freq_range_low, freq_range_high)])
      dpa.SetGrantsFromFad(sas_uut_fad, test_harness_fads)
      dpa.ComputeMoveLists()
      all_dpas.append(dpa)

    # Activate each DPA in sequence and check the move list interference is
    # within the allowed margin. This contains steps 10 to 21.
    current_active_dpas = []
    for new_dpa, new_dpa_config in zip(all_dpas, config['dpas']):
      self._sas_admin.TriggerDpaActivation(buildDpaActivationMessage(new_dpa_config))
      current_active_dpas.append(new_dpa)
      time.sleep(240)
      for domain_proxy in domain_proxies:
        domain_proxy.heartbeatForAllActiveGrants()
      grant_info = data.getAuthorizedGrantsFromDomainProxies(domain_proxies)
      # Check each active DPA does not exceed its allowed interference threshold.
      for dpa, dpa_config in zip(current_active_dpas, config['dpas']):
        self.assertTrue(dpa.CheckInterference(
            sas_uut_active_grants=grant_info,
            margin_db=dpa_config['movelistMargin']))
      if len(current_active_dpas) == len(all_dpas):
        break
      time.sleep(config['pauseTime'])

  def generate_IPR_6_default_config(self, filename):
    """Generates the WinnForum configuration for IPR_6"""

    # Load Devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a['installationParam']['latitude'] = 30.71570
    device_a['installationParam']['longitude'] = -88.09350
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_b['installationParam']['latitude'] = 30.71571
    device_b['installationParam']['longitude'] = -88.09351

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
    device_b = {
        key: device_b[key]
        for key in device_b
        if key not in reg_conditional_keys
    }

    # Load grant requests.
    grant_a = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_b = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))

    sas_test_harness_config = {
        'sasTestHarnessName':
            'SAS-Test-Harness-1',
        'hostName':
            'localhost',
        'port':
            9006,
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
        'points_builder': 'default (25, 10, 10, 10)',
        'movelistMargin': 10
    }

    domain_proxy = {
        'registrationRequests': [device_b],
        'grantRequests': [grant_b],
        'conditionalRegistrationData': [conditionals_b],
        'cert': os.path.join('certs', 'domain_proxy.cert'),
        'key': os.path.join('certs', 'domain_proxy.key')
    }

    config = {
        'sasTestHarnessConfigs': [sas_test_harness_config],
        'domainProxies': [domain_proxy],
        'dpas': [dpa_1],
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_IPR_6_default_config)
  def test_WINNF_FT_S_IPR_6(self, config_filename):
    config = loadConfig(config_filename)
    self.assertValidConfig(
        config, {
            'sasTestHarnessConfigs': list,
            'domainProxies': list,
            'dpas': list
        })
    # SAS UUT loads DPAs and is informed they are all inactive.
    self._sas_admin.TriggerLoadDpas()
    self._sas_admin.TriggerBulkDpaActivation({'activate': False})

    # Steps 3 & 4 can be interleaved.
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

    # Register N2 CBSDs and request grants with SAS UUT from ND proxies.
    domain_proxies = []
    for domain_proxy_config in config['domainProxies']:
      domain_proxy = DomainProxy(self,
                                 ssl_cert=domain_proxy_config['cert'],
                                 ssl_key=domain_proxy_config['key'])
      domain_proxy.registerCbsdsAndRequestGrants(
          domain_proxy_config['registrationRequests'],
          domain_proxy_config['grantRequests'],
          conditional_registration_data=domain_proxy_config['conditionalRegistrationData'])
      domain_proxies.append(domain_proxy)

    # Trigger, wait and download FAD records from SAS UUT and test harnesses.
    sas_uut_fad = getFullActivityDumpSasUut(self._sas, self._sas_admin)
    test_harness_fads = []
    for test_harness in test_harnesses:
      test_harness_fads.append(
          getFullActivityDumpSasTestHarness(
              test_harness.getSasTestHarnessInterface()))

    # Trigger CPAS.
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Calculate DPA movelists for each DPA.
    all_dpas = []
    for dpa_config in config['dpas']:
      dpa = dpa_mgr.BuildDpa(dpa_config['dpaId'], dpa_config['points_builder'])
      dpa.SetGrantsFromFad(sas_uut_fad, test_harness_fads)
      dpa.ComputeMoveLists()
      all_dpas.append(dpa)

    # Connectivity between ESCs and SAS UUT is broken.
    self._sas_admin.TriggerEscDisconnect()

    # Wait till all heartbeats must suspend grants that are on DPA movelists.
    time.sleep(240)

    # Heartbeat with all domain proxies.
    for domain_proxy in domain_proxies:
      domain_proxy.heartbeatForAllActiveGrants()
    grant_info = data.getAuthorizedGrantsFromDomainProxies(domain_proxies)
    # Check that for each DPA the SAS UUT has not exceeded the allowed
    # interference threshold.
    for dpa, dpa_config in zip(all_dpas, config['dpas']):
      self.assertTrue(dpa.CheckInterference(
          sas_uut_active_grants=grant_info,
          margin_db=dpa_config['movelistMargin']))
