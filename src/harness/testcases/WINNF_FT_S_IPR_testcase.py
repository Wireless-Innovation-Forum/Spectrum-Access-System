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
import time

from util import buildDpaActivationMessage, configurable_testcase, writeConfig, \
  loadConfig, getCertificateFingerprint, getFqdnLocalhost, getUnusedPort, \
  getCertFilename
from test_harness_objects import DomainProxy
from full_activity_dump_helper import getFullActivityDumpSasTestHarness, getFullActivityDumpSasUut
from sas_test_harness import SasTestHarnessServer, generateCbsdRecords
from reference_models.dpa import dpa_mgr
from reference_models.common import data
from common_types import ResponseCodes
from datetime import datetime, timedelta

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
        'sasTestHarnessName': 'SAS-Test-Harness-1',
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'serverCert': getCertFilename('sas.cert'),
        'serverKey': getCertFilename('sas.key'),
        'caCert': getCertFilename('ca.cert'),
        'fullActivityDumpRecords': [
            generateCbsdRecords([device_a], [[grant_a]])
        ]
    }

    dpa_1 = {
        'dpaId': 'Pascagoula',
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
    num_peer_sases = len(config['sasTestHarnessConfigs'])
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
    sas_uut_fad = None
    test_harness_fads = []
    if num_peer_sases:
        ssl_cert = config['sasTestHarnessConfigs'][0]['serverCert']
        ssl_key = config['sasTestHarnessConfigs'][0]['serverKey']
        sas_uut_fad = getFullActivityDumpSasUut(self._sas, self._sas_admin, ssl_cert=ssl_cert, ssl_key=ssl_key)
        for test_harness in test_harnesses:
          test_harness_fads.append(
              getFullActivityDumpSasTestHarness(
                  test_harness.getSasTestHarnessInterface()))

    # Trigger CPAS.
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Heartbeat SAS UUT grants.
    n2_domain_proxy.heartbeatForAllActiveGrants()
    n3_domain_proxy.heartbeatForAllActiveGrants()
    # Get CbsdGrantInfo list of SAS UUT grants that are in an authorized state.
    grant_info = data.getAuthorizedGrantsFromDomainProxies([n2_domain_proxy, n3_domain_proxy])

    # Initialize DPA objects and calculate movelist for each DPA.
    dpas = []
    for dpa_config in config['dpas']:
      dpa = dpa_mgr.BuildDpa(dpa_config['dpaId'], dpa_config['points_builder'])
      low_freq_mhz = dpa_config['frequencyRange']['lowFrequency'] / ONE_MHZ
      high_freq_mhz = dpa_config['frequencyRange']['highFrequency'] / ONE_MHZ
      dpa.ResetFreqRange([(low_freq_mhz, high_freq_mhz)])
      dpa.SetGrantsFromFad(sas_uut_fad, test_harness_fads)
      dpa.ComputeMoveLists()
      # Check grants do not exceed each DPAs interference threshold.
      self.assertTrue(dpa.CheckInterference(
          sas_uut_active_grants=grant_info,
          margin_db=dpa_config['movelistMargin'],
          channel=(low_freq_mhz, high_freq_mhz),
          do_abs_check_single_uut=(num_peer_sases==0)))


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
        'sasTestHarnessName': 'SAS-Test-Harness-1',
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'serverCert': getCertFilename('sas.cert'),
        'serverKey': getCertFilename('sas.key'),
        'caCert': getCertFilename('ca.cert'),
        'fullActivityDumpRecords': [
            generateCbsdRecords([device_a], [[grant_a]])
        ]
    }

    dpa_1 = {
        'dpaId': 'East3',
        'frequencyRange': {
            'lowFrequency': 3620000000,
            'highFrequency': 3630000000
        },
        'points_builder': 'default (25, 10, 10, 10)',
        'movelistMargin': 10
    }
    dpa_2 = {
        'dpaId': 'East3',
        'frequencyRange': {
            'lowFrequency': 3610000000,
            'highFrequency': 3620000000
        },
        'points_builder': 'default (25, 10, 10, 10)',
        'movelistMargin': 10
    }
    dpa_3 = {
        'dpaId': 'East21',
        'frequencyRange': {
            'lowFrequency': 3620000000,
            'highFrequency': 3630000000
        },
        'points_builder': 'default (25, 10, 10, 10)',
        'movelistMargin': 10
    }
    dpa_4 = {
        'dpaId': 'West4',
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
        'cert': getCertFilename('domain_proxy.cert'),
        'key': getCertFilename('domain_proxy.key')
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

    num_peer_sases = len(config['sasTestHarnessConfigs'])
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

    sas_uut_fad = None
    test_harness_fads = []
    if num_peer_sases:
      # Trigger, wait and download FAD records from SAS UUT and test harnesses.
      ssl_cert = config['sasTestHarnessConfigs'][0]['serverCert']
      ssl_key = config['sasTestHarnessConfigs'][0]['serverKey']
      sas_uut_fad = getFullActivityDumpSasUut(self._sas, self._sas_admin, ssl_cert=ssl_cert, ssl_key=ssl_key)
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
      low_freq_mhz = dpa_config['frequencyRange']['lowFrequency'] / ONE_MHZ
      high_freq_mhz = dpa_config['frequencyRange']['highFrequency'] / ONE_MHZ
      dpa.ResetFreqRange([(low_freq_mhz, high_freq_mhz)])
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
        low_freq_mhz = dpa_config['frequencyRange']['lowFrequency'] / ONE_MHZ
        high_freq_mhz = dpa_config['frequencyRange']['highFrequency'] / ONE_MHZ
        self.assertTrue(dpa.CheckInterference(
            sas_uut_active_grants=grant_info,
            margin_db=dpa_config['movelistMargin'],
            channel=(low_freq_mhz, high_freq_mhz),
            do_abs_check_single_uut=(num_peer_sases==0)))
      if len(current_active_dpas) == len(all_dpas):
        break
      time.sleep(config['pauseTime'])

  def generate_IPR_3_default_config(self, filename):
    """Generates the WinnForum configuration for IPR_3"""

    # Load Device in DPA neighborhood.
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a['installationParam']['latitude'] = 30.71570
    device_a['installationParam']['longitude'] = -88.09350
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

    # Load grant request.
    grant_a = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))

    frequency_range = grant_a['operationParam']['operationFrequencyRange']
    dpa_1 = {
        'dpaId': 'East4',
        'frequencyRange': {
            'lowFrequency': frequency_range['lowFrequency'],
            'highFrequency': frequency_range['highFrequency']
        }
    }

    config = {
        'registrationRequest': device_a,
        'grantRequest': grant_a,
        'conditionalRegistrationData': conditionals_a,
        'dpa': dpa_1
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_IPR_3_default_config)
  def test_WINNF_FT_S_IPR_3(self, config_filename):
    """CBSD Grant Request in the Neighborhood of an Activated Offshore DPA."""
    config = loadConfig(config_filename)
    self.assertValidConfig(
        config, {
            'registrationRequest': dict,
            'grantRequest': dict,
            'conditionalRegistrationData': dict,
            'dpa': dict
        })
    self.assertTrue(config['dpa']['frequencyRange']['lowFrequency'] < config['dpa']['frequencyRange']['highFrequency'])
    self.assertTrue(config['dpa']['frequencyRange']['highFrequency'] <= 3650000000)
    self.GrantRequestInActiveDpaNeighborhood(config)

  def generate_IPR_4_default_config(self, filename):
    """Generates the WinnForum configuration for IPR_4"""

    # Load Device.
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    # Move the CBSD to be nearby the St. Inigoes site.
    device_b['installationParam']['latitude'] = 30.354917
    device_b['installationParam']['longitude'] = -88.532033
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

    # Load grant request.
    grant_b = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    frequency_range = grant_b['operationParam']['operationFrequencyRange']
    dpa_1 = {
        'dpaId': 'Pascagoula',
        'frequencyRange': frequency_range
    }
    config = {
        'registrationRequest': device_b,
        'grantRequest': grant_b,
        'conditionalRegistrationData': conditionals_b,
        'dpa': dpa_1
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_IPR_4_default_config)
  def test_WINNF_FT_S_IPR_4(self, config_filename):
    """CBSD Grant Request in the Neighborhood of an Activated Inland Co-channel DPA."""
    config = loadConfig(config_filename)
    self.assertValidConfig(
        config, {
            'registrationRequest': dict,
            'grantRequest': dict,
            'conditionalRegistrationData': dict,
        },
        optional_fields={'dpa': dict})
    if 'dpa' in config:
        self.assertTrue(config['dpa']['frequencyRange']['lowFrequency'] < config['dpa']['frequencyRange']['highFrequency'])
        self.assertTrue(config['dpa']['frequencyRange']['highFrequency'] <= 3650000000)
    self.GrantRequestInActiveDpaNeighborhood(config)

  def GrantRequestInActiveDpaNeighborhood(self, config):
    # SAS UUT loads DPAs and is informed they are all inactive.
    self._sas_admin.TriggerLoadDpas()
    self._sas_admin.TriggerBulkDpaActivation({'activate': False})

    # Only inform SAS UUT of DPA activation in IPR.3, in IPR.4 all the
    # relevant DPAs are always active.
    if 'dpa' in config:
      # Inform the SAS UUT that the given DPA is active.
      self._sas_admin.TriggerDpaActivation(config['dpa'])
    # Wait till SAS UUT must not authorize grants.
    time.sleep(240)
    # Register CBSD in the active DPAs neighborhood.
    grant_request = config['grantRequest']
    grant_request['cbsdId'] = self.assertRegistered([config['registrationRequest']], conditional_registration_data=[config['conditionalRegistrationData']])[0]
    # Request grant for the CBSD.
    grant_response = self._sas.Grant({'grantRequest': [grant_request]})['grantResponse'][0]
    # It is only necessary to heartbeat if the initial grant request succeeds.
    if grant_response['response']['responseCode'] == ResponseCodes.SUCCESS.value:
      # Heartbeat grant and check the CBSD is not authorized.
      heartbeat_request = {'cbsdId': grant_request['cbsdId'], 'grantId': grant_response['grantId'], 'operationState': 'GRANTED'}
      heartbeat_response = self._sas.Heartbeat({'heartbeatRequest': [heartbeat_request]})['heartbeatResponse'][0]
      self.assertNotEqual(heartbeat_response['response']['responseCode'], ResponseCodes.SUCCESS.value)

  def generate_IPR_5_default_config(self, filename):
    """Generates the WinnForum configuration for IPR_5"""

     # Load Device in DPA neighborhood.
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_a['installationParam']['latitude'] = 30.71570
    device_a['installationParam']['longitude'] = -88.09350
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

    # Load grant request.
    grant_a = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))

    frequency_range = grant_a['operationParam']['operationFrequencyRange']
    dpa_1 = {
        'dpaId': 'East4',
        'frequencyRange': {
            'lowFrequency': frequency_range['lowFrequency'],
            'highFrequency': frequency_range['highFrequency']
        }
    }

    domain_proxy = {
        'registrationRequests': [device_a],
        'grantRequests': [grant_a],
        'conditionalRegistrationData': [conditionals_a],
        'sslCert': getCertFilename('domain_proxy.cert'),
        'sslKey': getCertFilename('domain_proxy.key')
    }

    config = {
        'domainProxies': [domain_proxy],
        'dpa': dpa_1,
        'pauseTime': 10,
        'iterations': 10
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_IPR_5_default_config)
  def test_WINNF_FT_S_IPR_5(self, config_filename):
    """CBSD Grant Requests in the Neighborhood of Inactive DPAs followed by DPA Activation ."""
    config = loadConfig(config_filename)
    self.assertValidConfig(
        config, {
            'domainProxies': list,
            'dpa': dict,
            'pauseTime': int,
            'iterations': int
        })
    self.assertTrue(config['dpa']['frequencyRange']['lowFrequency'] < config['dpa']['frequencyRange']['highFrequency'])
    self.assertTrue(config['dpa']['frequencyRange']['highFrequency'] <= 3650000000)

    # SAS UUT loads DPAs and is informed all fully monitored DPAs are inactive.
    self._sas_admin.TriggerLoadDpas()
    self._sas_admin.TriggerBulkDpaActivation({'activate': False})
    # Trigger CPAS.
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Create Domain Proxies and register CBSDs with SAS UUT.
    domain_proxies = []
    for domain_proxy_config in config['domainProxies']:
      domain_proxy = DomainProxy(
          self,
          ssl_cert=domain_proxy_config['sslCert'],
          ssl_key=domain_proxy_config['sslKey'])
      domain_proxy.registerCbsdsAndRequestGrants(
          domain_proxy_config['registrationRequests'],
          domain_proxy_config['grantRequests'],
          conditional_registration_data=domain_proxy_config['conditionalRegistrationData'])
      domain_proxies.append(domain_proxy)

    # Heartbeat each grant and check the timestamp is within the allowed range.
    for domain_proxy in domain_proxies:
      _, heartbeat_responses = domain_proxy.heartbeatForAllActiveGrants()
      t_now = datetime.utcnow()
      for response in heartbeat_responses:
        transmit_expire_time = datetime.strptime(response['transmitExpireTime'], '%Y-%m-%dT%H:%M:%SZ')
        if response['response']['responseCode'] == ResponseCodes.SUCCESS.value:
          self.assertTrue(transmit_expire_time <= t_now + timedelta(seconds=240))

    # Inform the SAS UUT that the given DPA is active.
    self._sas_admin.TriggerDpaActivation(config['dpa'])
    t_esc = datetime.utcnow()

    # Check heartbeat expiration time is valid
    for _ in range(config['iterations']):
      for domain_proxy in domain_proxies:
        _, heartbeat_responses = domain_proxy.heartbeatForAllActiveGrants()
        for response in heartbeat_responses:
          transmit_expire_time = datetime.strptime(response['transmitExpireTime'], '%Y-%m-%dT%H:%M:%SZ')
          if response['response']['responseCode'] == ResponseCodes.SUCCESS.value:
            self.assertTrue(transmit_expire_time <= t_esc + timedelta(seconds=240))
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
        'sasTestHarnessName': 'SAS-Test-Harness-1',
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'serverCert': getCertFilename('sas.cert'),
        'serverKey': getCertFilename('sas.key'),
        'caCert': getCertFilename('ca.cert'),
        'fullActivityDumpRecords': [
            generateCbsdRecords([device_a], [[grant_a]])
        ]
    }

    dpa_1 = {
        'dpaId': 'East4',
        'points_builder': 'default (25, 10, 10, 10)',
        'movelistMargin': 10
    }

    domain_proxy = {
        'registrationRequests': [device_b],
        'grantRequests': [grant_b],
        'conditionalRegistrationData': [conditionals_b],
        'cert': getCertFilename('domain_proxy.cert'),
        'key': getCertFilename('domain_proxy.key')
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
    num_peer_sases = len(config['sasTestHarnessConfigs'])
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

    sas_uut_fad = None
    test_harness_fads = []
    if num_peer_sases:
      # Trigger, wait and download FAD records from SAS UUT and test harnesses.
      ssl_cert = config['sasTestHarnessConfigs'][0]['serverCert']
      ssl_key = config['sasTestHarnessConfigs'][0]['serverKey']
      sas_uut_fad = getFullActivityDumpSasUut(self._sas, self._sas_admin, ssl_cert=ssl_cert, ssl_key=ssl_key)
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
          margin_db=dpa_config['movelistMargin'],
          do_abs_check_single_uut=(num_peer_sases==0)))
