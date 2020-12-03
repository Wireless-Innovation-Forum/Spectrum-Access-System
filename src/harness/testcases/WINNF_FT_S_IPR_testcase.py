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

from datetime import datetime, timedelta
import logging
import json
import os
import time

from six import string_types as basestring
from six.moves import zip

import sas
import sas_testcase
from database import DatabaseServer
from util import buildDpaActivationMessage, configurable_testcase, writeConfig, \
  loadConfig, getCertificateFingerprint, getFqdnLocalhost, getUnusedPort, \
  getCertFilename, json_load
from test_harness_objects import DomainProxy
from full_activity_dump_helper import getFullActivityDumpSasTestHarness, getFullActivityDumpSasUut
from sas_test_harness import SasTestHarnessServer, generateCbsdRecords
from reference_models.dpa import dpa_mgr
from reference_models.common import data
from common_types import ResponseCodes

LOW_FREQUENCY_LIMIT_HZ = 3550000000
HIGH_FREQUENCY_LIMIT_HZ = 3650000000
ONE_MHZ = 1000000



class FederalIncumbentProtectionTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    self.ShutdownServers()

  def frequencyInBand(self, low_frequency, high_frequency):
    """Returns True iff the given range overlaps with the 3550-3650MHz range."""
    return (LOW_FREQUENCY_LIMIT_HZ <= low_frequency <= HIGH_FREQUENCY_LIMIT_HZ
            or
            LOW_FREQUENCY_LIMIT_HZ <= high_frequency <= HIGH_FREQUENCY_LIMIT_HZ)

  def generate_IPR_1_default_config(self, filename):
    """Generates the WinnForum configuration for IPR_1."""

    # Load Devices.
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_a['installationParam']['latitude'] = 30.71570
    device_a['installationParam']['longitude'] = -88.09350

    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_b['installationParam']['latitude'] = 30.71570
    device_b['installationParam']['longitude'] = -88.09350
    device_c = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
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
    grant_a = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_b = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_c = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))

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
    # The N3 grant requests must all overlap at least partially with 3550-3650.
    for grant_request in config['grantRequestsN3']:
      self.assertLessEqual(
          grant_request['operationParam']['operationFrequencyRange'][
              'lowFrequency'],
          3650e6,
          msg=
          'Invalid config: N3 Grants must at least partially overlap with 3550-3650 MHz.'
      )
    num_peer_sases = len(config['sasTestHarnessConfigs'])
    # SAS UUT loads DPAs.
    logging.info('Step 1: trigger DPA load.')
    self._sas_admin.TriggerLoadDpas()

    # Steps 2 & 3 can be interleaved.
    logging.info('Steps 2 + 3: activate and configure SAS Test Harnesses.')
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
      for fullActivityDumpRecord in test_harness_config['fullActivityDumpRecords']:
          self.InjectTestHarnessFccIds(fullActivityDumpRecord)
      test_harness.writeFadRecords(
          test_harness_config['fullActivityDumpRecords'])
      test_harnesses.append(test_harness)

    # Register N2 CBSDs with the SAS UUT and request Grants.
    logging.info('Step 4: Registering and Granting N2 CBSDs with SAS UUT.')
    n2_domain_proxy = DomainProxy(self)
    n2_domain_proxy.registerCbsdsAndRequestGrants(
        config['registrationRequestsN2'],
        config['grantRequestsN2'],
        conditional_registration_data=config['conditionalRegistrationDataN2'])

    # Trigger CPAS.
    logging.info('Step 5: Triggering CPAS.')
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Register N3 CBSDs with the SAS UUT and request Grants.
    logging.info('Step 6: Registering and Granting N3 CBSDs with SAS UUT.')
    # Note: the frequency range of the N3 grant requests was checked above.
    n3_domain_proxy = DomainProxy(self)
    n3_domain_proxy.registerCbsdsAndRequestGrants(
        config['registrationRequestsN3'],
        config['grantRequestsN3'],
        conditional_registration_data=config['conditionalRegistrationDataN3'])

    # Heartbeat all SAS UUT CBSDS
    logging.info('Step 7: Heartbeating all active Grants.')
    n2_domain_proxy.heartbeatForAllActiveGrants()
    n3_domain_proxy.heartbeatForAllActiveGrants()

    # None of the N3 CBSDS should be authorized.
    logging.info('CHECK: None of the N3 Grants are authorized.')
    cbsds = n3_domain_proxy.getCbsdsWithAtLeastOneAuthorizedGrant()
    if cbsds:
      for cbsd in cbsds:
        logging.info(
            'CBSD (cbsd_id=%s, fcc_id=%s, sn=%s) '
            'is authorized after IPR.1 step 7. SAS UUT FAILS this test. '
            '(If this config is new please verify the CBSD is in a DPA neighborhood.)',
            cbsd.getCbsdId(),
            cbsd.getRegistrationRequest()['fccId'],
            cbsd.getRegistrationRequest()['cbsdSerialNumber'])
    self.assertEqual(
        len(cbsds),
        0,
        msg='At least one N3 CBSD was authorized; see above for details.')

    # Get SAS UUT FAD and Test Harness FADs.
    logging.info('Steps 8 + 9: generate and pull FAD.')
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
    logging.info('Step 10: Triggering CPAS.')
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Heartbeat SAS UUT grants.
    logging.info('Step 12: Heartbeating all active Grants.')
    n2_domain_proxy.heartbeatForAllActiveGrants()
    n3_domain_proxy.heartbeatForAllActiveGrants()
    # Get CbsdGrantInfo list of SAS UUT grants that are in an authorized state.
    grant_info = data.getAuthorizedGrantsFromDomainProxies([n2_domain_proxy, n3_domain_proxy])

    # Initialize DPA objects and calculate movelist for each DPA.
    logging.info('Steps 11 + 13, CHECK: DPA aggregate interference check.')
    dpas = []
    all_dpa_checks_succeeded = True
    for dpa_config in config['dpas']:
      logging.info('Checking DPA %s', dpa_config)
      dpa = dpa_mgr.BuildDpa(dpa_config['dpaId'], dpa_config['points_builder'])
      low_freq_mhz = dpa_config['frequencyRange']['lowFrequency'] // ONE_MHZ
      high_freq_mhz = dpa_config['frequencyRange']['highFrequency'] // ONE_MHZ
      dpa.ResetFreqRange([(low_freq_mhz, high_freq_mhz)])
      dpa.SetGrantsFromFad(sas_uut_fad, test_harness_fads)
      dpa.ComputeMoveLists()
      # Check grants do not exceed each DPAs interference threshold.
      this_dpa_check_succeeded = dpa.CheckInterference(
          sas_uut_active_grants=grant_info,
          margin_db=dpa_config['movelistMargin'],
          channel=(low_freq_mhz, high_freq_mhz),
          do_abs_check_single_uut=(num_peer_sases == 0))
      if not this_dpa_check_succeeded:
        logging.error('Check for DPA %s FAILED.', dpa_config['dpaId'])
        all_dpa_checks_succeeded = False

    self.assertTrue(
        all_dpa_checks_succeeded,
        'At least one DPA check failed; please see logs for details.')

    # Stop test harness servers.
    for test_harness in test_harnesses:
      test_harness.shutdown()
      del test_harness


  def generate_IPR_2_default_config(self, filename):
    """Generates the WinnForum configuration for IPR_2"""

    # Load Devices
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_a['installationParam']['latitude'] = 30.23534
    device_a['installationParam']['longitude'] = -87.93972
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_b['installationParam']['latitude'] = 30.47642
    device_b['installationParam']['longitude'] = -87.08096
    device_c = json_load(
        os.path.join('testcases', 'testdata', 'device_c.json'))
    device_c['installationParam']['latitude'] = 30.31534
    device_c['installationParam']['longitude'] = -86.08972
    device_d = json_load(
        os.path.join('testcases', 'testdata', 'device_d.json'))
    device_d['installationParam']['latitude'] = 30.30642
    device_d['installationParam']['longitude'] = -86.06096
    device_e = json_load(
        os.path.join('testcases', 'testdata', 'device_e.json'))
    device_e['installationParam']['latitude'] = 44.47642
    device_e['installationParam']['longitude'] = -124.08096
    device_h = json_load(
        os.path.join('testcases', 'testdata', 'device_h.json'))
    device_h['installationParam']['latitude'] = 44.46642
    device_h['installationParam']['longitude'] = -124.07096

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
    conditionals_d = {key: device_d[key] for key in conditional_keys}
    device_d = {
        key: device_d[key]
        for key in device_d
        if key not in reg_conditional_keys
    }
    conditionals_h = {key: device_h[key] for key in conditional_keys}
    device_h = {
        key: device_h[key]
        for key in device_h
        if key not in reg_conditional_keys
    }

    # Load grant requests.
    grant_a = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_b = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_c = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_c['operationParam']['operationFrequencyRange']['lowFrequency'] = 3620000000
    grant_c['operationParam']['operationFrequencyRange']['highFrequency'] = 3630000000
    grant_d = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_d['operationParam']['operationFrequencyRange']['lowFrequency'] = 3620000000
    grant_d['operationParam']['operationFrequencyRange']['highFrequency'] = 3630000000
    grant_e = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_e['operationParam']['operationFrequencyRange']['lowFrequency'] = 3610000000
    grant_e['operationParam']['operationFrequencyRange']['highFrequency'] = 3620000000
    grant_h = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_h['operationParam']['operationFrequencyRange']['lowFrequency'] = 3610000000
    grant_h['operationParam']['operationFrequencyRange']['highFrequency'] = 3620000000

    sas_test_harness_config = {
        'sasTestHarnessName': 'SAS-Test-Harness-1',
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'serverCert': getCertFilename('sas.cert'),
        'serverKey': getCertFilename('sas.key'),
        'caCert': getCertFilename('ca.cert'),
        'fullActivityDumpRecords': [
            generateCbsdRecords([device_a, device_c, device_e], [[grant_a], [grant_c], [grant_e]])
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
        'registrationRequests': [device_b, device_d, device_h],
        'grantRequests': [grant_b, grant_d, grant_h],
        'conditionalRegistrationData': [conditionals_b, conditionals_d, conditionals_h],
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
    logging.info('Steps 1 + 2: load DPAs and deactivate.')
    self._sas_admin.TriggerLoadDpas()
    self._sas_admin.TriggerBulkDpaActivation({'activate': False})

    # Steps 3 & 4 can be interleaved.
    logging.info('Steps 3 + 4: activate and configure SAS Test Harnesses.')
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
      for fullActivityDumpRecord in test_harness_config['fullActivityDumpRecords']:
          self.InjectTestHarnessFccIds(fullActivityDumpRecord)
      test_harness.writeFadRecords(
          test_harness_config['fullActivityDumpRecords'])
      test_harnesses.append(test_harness)


    # Register N2 CBSDs and request grants with SAS UUT from ND proxies.
    logging.info('Step 5: Registering and Granting N2 CBSDs with SAS UUT.')
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

    logging.info('Steps 6 + 7: generate and pull FAD.')
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
    logging.info('Step 8: Triggering CPAS.')
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Calculate DPA movelists for each DPA.
    # DPA/channel pairs must be in the order:
    #   (D_i, C_j)
    #   (D_i, C_l)
    #   (D_i+1, C_j)
    #   (D_k, C_l)
    logging.info(
        'Step 9: generate reference DPA move lists for all DPA/channel pairs.')
    all_dpas = []
    for dpa_config in config['dpas']:
      dpa = dpa_mgr.BuildDpa(dpa_config['dpaId'], dpa_config['points_builder'])
      low_freq_mhz = dpa_config['frequencyRange']['lowFrequency'] // ONE_MHZ
      high_freq_mhz = dpa_config['frequencyRange']['highFrequency'] // ONE_MHZ
      dpa.ResetFreqRange([(low_freq_mhz, high_freq_mhz)])
      dpa.SetGrantsFromFad(sas_uut_fad, test_harness_fads)
      dpa.ComputeMoveLists()
      all_dpas.append(dpa)

    # Activate each DPA in sequence and check the move list interference is
    # within the allowed margin. This contains steps 10 to 21.
    current_active_dpas = []
    all_dpa_checks_succeeded = True
    for new_dpa, new_dpa_config in zip(all_dpas, config['dpas']):
      logging.info('Step 10/13/16/19: activate DPA: %s', new_dpa_config)
      self._sas_admin.TriggerDpaActivation(buildDpaActivationMessage(new_dpa_config))
      current_active_dpas.append(new_dpa)

      logging.info('Step 11/14/17/20: wait + heartbeat.')
      time.sleep(240)
      for domain_proxy in domain_proxies:
        domain_proxy.heartbeatForAllActiveGrants()
      grant_info = data.getAuthorizedGrantsFromDomainProxies(domain_proxies)

      logging.info(
          'Step 12/15/18/21 + CHECK: DPA aggregate interference check.')
      # Check each active DPA does not exceed its allowed interference threshold.
      for dpa, dpa_config in zip(current_active_dpas, config['dpas']):
        low_freq_mhz = dpa_config['frequencyRange']['lowFrequency'] // ONE_MHZ
        high_freq_mhz = dpa_config['frequencyRange']['highFrequency'] // ONE_MHZ
        this_dpa_check_succeeded = dpa.CheckInterference(
            sas_uut_active_grants=grant_info,
            margin_db=dpa_config['movelistMargin'],
            channel=(low_freq_mhz, high_freq_mhz),
            do_abs_check_single_uut=(num_peer_sases == 0))
        if not this_dpa_check_succeeded:
          logging.error('Check for DPA %s FAILED.', dpa_config['dpaId'])
          all_dpa_checks_succeeded = False

      if len(current_active_dpas) == len(all_dpas):
        break

      logging.info('Step 13/16/19: pause T seconds.')
      time.sleep(config['pauseTime'])

    self.assertTrue(
        all_dpa_checks_succeeded,
        'At least one DPA check failed; please see logs for details.')

    # Stop test harness servers.
    for test_harness in test_harnesses:
      test_harness.shutdown()
      del test_harness

  def generate_IPR_3_default_config(self, filename):
    """Generates the WinnForum configuration for IPR_3"""

    # Load Device in DPA neighborhood.
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
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
    grant_a = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))

    frequency_range = grant_a['operationParam']['operationFrequencyRange']
    dpa_1 = {
        'dpaId': 'East3',
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
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
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
    grant_b = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
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
      self.assertTrue(
          LOW_FREQUENCY_LIMIT_HZ <=
          config['dpa']['frequencyRange']['lowFrequency'],
          msg=
          'To specify an always-active DPA, omit the "dpa" field from the config.'
      )
      self.assertTrue(config['dpa']['frequencyRange']['lowFrequency'] <
                      config['dpa']['frequencyRange']['highFrequency'])
      self.assertTrue(
          config['dpa']['frequencyRange']['highFrequency'] <= 3650e6)
    self.GrantRequestInActiveDpaNeighborhood(config)

  def GrantRequestInActiveDpaNeighborhood(self, config):
    # SAS UUT loads DPAs and is informed they are all inactive.
    logging.info('Steps 1 + 2: load DPAs and deactivate.')
    self._sas_admin.TriggerLoadDpas()
    self._sas_admin.TriggerBulkDpaActivation({'activate': False})

    # Only inform SAS UUT of DPA activation if one was specified. To test an
    # always-active DPA, omit this field from the config.
    if 'dpa' in config:
      # Inform the SAS UUT that the given DPA is active.
      logging.info('Step 3: activating DPA: %s', config['dpa'])
      self._sas_admin.TriggerDpaActivation(config['dpa'])
    else:
      logging.info(
          'Step 3: skipping: no DPA specified (may be testing an always-active DPA).'
      )

    # Wait till SAS UUT must not authorize grants.
    logging.info('Step 4: wait 240 seconds.')
    time.sleep(240)

    # Register CBSD in the active DPAs neighborhood.
    logging.info('Step 5: registering and granting CBSD to SAS UUT.')
    grant_request = config['grantRequest']
    grant_request['cbsdId'] = self.assertRegistered([config['registrationRequest']], conditional_registration_data=[config['conditionalRegistrationData']])[0]
    # Request grant for the CBSD.
    grant_response = self._sas.Grant({'grantRequest': [grant_request]})['grantResponse'][0]

    # It is only necessary to heartbeat if the initial grant request succeeds.
    if grant_response['response']['responseCode'] == ResponseCodes.SUCCESS.value:
      logging.info('Step 6 + CHECK: heartbeat request.')
      # Heartbeat grant and check the CBSD is not authorized.
      heartbeat_request = {'cbsdId': grant_request['cbsdId'], 'grantId': grant_response['grantId'], 'operationState': 'GRANTED'}
      heartbeat_response = self._sas.Heartbeat({'heartbeatRequest': [heartbeat_request]})['heartbeatResponse'][0]
      self.assertNotEqual(heartbeat_response['response']['responseCode'], ResponseCodes.SUCCESS.value)
    else:
      logging.info('Grant request failed => SAS UUT passes.')

  def generate_IPR_5_default_config(self, filename):
    """Generates the WinnForum configuration for IPR_5"""

    # Load Device in DPA neighborhood.
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
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
    grant_a = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))

    frequency_range = grant_a['operationParam']['operationFrequencyRange']
    dpa_1 = {
        'dpaId': 'East3',
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
    logging.info('Steps 1 + 2: load DPAs and deactivate.')
    self._sas_admin.TriggerLoadDpas()
    self._sas_admin.TriggerBulkDpaActivation({'activate': False})

    # Trigger CPAS.
    logging.info('Step 3: Triggering CPAS.')
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    # Create Domain Proxies and register CBSDs with SAS UUT.
    logging.info('Step 4: Registering and Granting N1 CBSDs with SAS UUT.')
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
    logging.info('Step 5: Heartbeating all active Grants.')
    for domain_proxy in domain_proxies:
      _, heartbeat_responses = domain_proxy.heartbeatForAllActiveGrants()
      t_now = datetime.utcnow()
      for response in heartbeat_responses:
        transmit_expire_time = datetime.strptime(response['transmitExpireTime'], '%Y-%m-%dT%H:%M:%SZ')
        if response['response']['responseCode'] == ResponseCodes.SUCCESS.value:
          self.assertTrue(transmit_expire_time <= t_now + timedelta(seconds=240))

    # Inform the SAS UUT that the given DPA is active.
    logging.info('Step 6: activating DPA: %s', config['dpa'])
    self._sas_admin.TriggerDpaActivation(config['dpa'])
    t_esc = datetime.utcnow()

    # Check heartbeat expiration time is valid
    for iter_number in range(config['iterations']):
      logging.info(
          'Step 7 (5 + CHECK, iteration %d): heartbeat and check response.',
          iter_number)
      for domain_proxy in domain_proxies:
        _, heartbeat_responses = domain_proxy.heartbeatForAllActiveGrants()
        for response in heartbeat_responses:
          transmit_expire_time = datetime.strptime(response['transmitExpireTime'], '%Y-%m-%dT%H:%M:%SZ')
          if response['response'][
              'responseCode'] == ResponseCodes.SUCCESS.value:
            self.assertTrue(
                transmit_expire_time <= t_esc + timedelta(seconds=240),
                msg='Check failed for reponse %s' % response)
      time.sleep(config['pauseTime'])

  def generate_IPR_6_default_config(self, filename):
    """Generates the WinnForum configuration for IPR_6"""

    # Load Devices
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_a['installationParam']['latitude'] = 30.71570
    device_a['installationParam']['longitude'] = -88.09350
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
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
    grant_a = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_b = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))

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
      for fullActivityDumpRecord in test_harness_config['fullActivityDumpRecords']:
          self.InjectTestHarnessFccIds(fullActivityDumpRecord)
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
    all_dpa_checks_succeeded = True
    for dpa, dpa_config in zip(all_dpas, config['dpas']):
      this_dpa_check_succeeded = dpa.CheckInterference(
          sas_uut_active_grants=grant_info,
          margin_db=dpa_config['movelistMargin'],
          do_abs_check_single_uut=(num_peer_sases == 0))
      if not this_dpa_check_succeeded:
        logging.error('Check for DPA %s FAILED.', dpa_config['dpaId'])
        all_dpa_checks_succeeded = False

    self.assertTrue(
        all_dpa_checks_succeeded,
        'At least one DPA check failed; please see logs for details.')

    # Stop test harness servers.
    for test_harness in test_harnesses:
      test_harness.shutdown()
      del test_harness

  def generate_IPR_7_default_config(self, filename):
    """Generates the WinnForum configuration for FDB.2"""

    # DPA database test harness configuration
    dpa_database_config = {
        'hostName': getFqdnLocalhost(),
        'port': getUnusedPort(),
        'fileUrl': '/db_sync',
        'filePath':
            os.path.join('testcases', 'testdata', 'fdb_2',
                         'FDB_2_Portal_DPAs.kml')
    }

    # Load Devices
    device_a = json_load(
        os.path.join('testcases', 'testdata', 'device_a.json'))
    device_a['installationParam']['latitude'] = 43.910
    device_a['installationParam']['longitude'] = -69.700
    device_b = json_load(
        os.path.join('testcases', 'testdata', 'device_b.json'))
    device_b['installationParam']['latitude'] = 43.902
    device_b['installationParam']['longitude'] = -69.850

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
    grant_a = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))
    grant_b = json_load(
        os.path.join('testcases', 'testdata', 'grant_0.json'))

    sas_test_harness_config = {
        'sasTestHarnessName':
            'SAS-Test-Harness-1',
        'hostName':
            getFqdnLocalhost(),
        'port':
            getUnusedPort(),
        'serverCert':
            getCertFilename('sas.cert'),
        'serverKey':
            getCertFilename('sas.key'),
        'caCert':
            getCertFilename('ca.cert'),
        'fullActivityDumpRecords': [
            generateCbsdRecords([device_a], [[grant_a]])
        ]
    }

    domain_proxy = {
        'registrationRequests': [device_b],
        'grantRequests': [grant_b],
        'conditionalRegistrationData': [conditionals_b],
        'cert': getCertFilename('domain_proxy.cert'),
        'key': getCertFilename('domain_proxy.key')
    }

    # Included only as an example; not used below.
    esc_dpa = {
        'dpaId': 'East4',
        # This is the frequency range which will be activated (if applicable)
        # and checked.
        'frequencyRange': {
            'lowFrequency': 3550000000,
            'highFrequency': 3560000000
        },
        'points_builder': 'default (25, 10, 10, 10)',
        'movelistMargin': 10
    }

    frequency_range = grant_a['operationParam']['operationFrequencyRange']
    portal_dpa = {
        'dpaId': 'BATH',
        # This is the frequency range which will be checked. One loaded into the
        # SAS, the DPA is automatically activated.
        'frequencyRange': {
            'lowFrequency': frequency_range['lowFrequency'],
            'highFrequency': frequency_range['highFrequency'],
        },
        'points_builder':
            'default (25, 10, 10, 10)',  # Not actually used since this is a single-point DPA.
        'movelistMargin': 10
    }

    config = {
        'dpaDatabaseConfig': dpa_database_config,
        'sasTestHarnessConfigs': [sas_test_harness_config],
        'domainProxies': [domain_proxy],
        'portalDpa': portal_dpa,
        'runEarlyCpas': False
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_IPR_7_default_config)
  def test_WINNF_FT_S_IPR_7(self, config_filename):
    config = loadConfig(config_filename)
    self.assertValidConfig(config, {
        'sasTestHarnessConfigs': list,
        'domainProxies': list
    }, {
        'dpaDatabaseConfig': dict,
        'escDpa': dict,
        'portalDpa': dict,
        'runEarlyCpas': bool
    })
    if 'dpaDatabaseConfig' in config:
      self.assertValidConfig(
          config['dpaDatabaseConfig'], {
              'hostName': basestring,
              'port': int,
              'fileUrl': basestring,
              'filePath': basestring
          })
    using_esc_dpa = 'escDpa' in config
    using_portal_dpa = 'portalDpa' in config
    self.assertTrue(
        using_esc_dpa ^ using_portal_dpa,
        msg=
        'Invalid config: must use exactly one ESC-monitored DPA OR one portal-controlled DPA.'
    )
    if using_esc_dpa:
      self.assertLessEqual(
          3540e6,
          config['escDpa']['frequencyRange']['lowFrequency'],
          msg=
          'For OOB ESC-monitored DPAs, we only compute the move list and check aggregate interference for 3540-3550 MHz.'
      )
    else:
      self.assertIn('dpaDatabaseConfig', config)

    dpa_config = config['escDpa'] if using_esc_dpa else config['portalDpa']
    self.assertEqual(
        10e6,
        dpa_config['frequencyRange']['highFrequency'] -
        dpa_config['frequencyRange']['lowFrequency'],
        msg='DPAs must be activated and checked in 10 MHz segments.')

    num_peer_sases = len(config['sasTestHarnessConfigs'])

    # SAS UUT loads the appropriate DPAs.
    dpa_database_server = None
    if using_esc_dpa:
      logging.info('Steps 1 + 2: load ESC-monitored DPAs and deactivate.')
      self._sas_admin.TriggerLoadDpas()
      self._sas_admin.TriggerBulkDpaActivation({'activate': False})
    else:
      logging.info(
          'Step 1: create portal-controlled DPA database. Step 2 is skipped.'
      )
      # Create DPA database server
      dpa_database_server = DatabaseServer(
          'DPA Database', config['dpaDatabaseConfig']['hostName'],
          config['dpaDatabaseConfig']['port'])
      # Start DPA database server
      dpa_database_server.start()
      # Set file path
      dpa_database_server.setFileToServe(
          config['dpaDatabaseConfig']['fileUrl'],
          config['dpaDatabaseConfig']['filePath'])
      # Inject the DPA database URL into the SAS UUT
      self._sas_admin.InjectDatabaseUrl({
          'type':
              'SCHEDULED_DPA',
          'url':
              dpa_database_server.getBaseUrl() +
              config['dpaDatabaseConfig']['fileUrl']
      })

    if using_portal_dpa and 'runEarlyCpas' in config and config['runEarlyCpas']:
      logging.info('Step 3: Triggering CPAS.')
      self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()
    else:
      logging.info('Step 3: (skipped).')

    # Steps 4 & 5 can be interleaved.
    logging.info('Steps 4 + 5: activate and configure SAS Test Harnesses.')
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
      for fullActivityDumpRecord in test_harness_config['fullActivityDumpRecords']:
          self.InjectTestHarnessFccIds(fullActivityDumpRecord)
      test_harness.writeFadRecords(
          test_harness_config['fullActivityDumpRecords'])
      test_harnesses.append(test_harness)

    # Register N2 CBSDs and request grants with SAS UUT from ND proxies.
    logging.info('Step 6: Registering and Granting N2 CBSDs with SAS UUT.')
    domain_proxies = []
    for domain_proxy_config in config['domainProxies']:
      domain_proxy = DomainProxy(
          self,
          ssl_cert=domain_proxy_config['cert'],
          ssl_key=domain_proxy_config['key'])
      domain_proxy.registerCbsdsAndRequestGrants(
          domain_proxy_config['registrationRequests'],
          domain_proxy_config['grantRequests'],
          conditional_registration_data=domain_proxy_config[
              'conditionalRegistrationData'])
      domain_proxies.append(domain_proxy)

    logging.info('Steps 7 + 8: generate and pull FAD.')
    sas_uut_fad = None
    test_harness_fads = []
    if num_peer_sases:
      # Trigger, wait and download FAD records from SAS UUT and test harnesses.
      ssl_cert = config['sasTestHarnessConfigs'][0]['serverCert']
      ssl_key = config['sasTestHarnessConfigs'][0]['serverKey']
      sas_uut_fad = getFullActivityDumpSasUut(
          self._sas, self._sas_admin, ssl_cert=ssl_cert, ssl_key=ssl_key)
      for test_harness in test_harnesses:
        test_harness_fads.append(
            getFullActivityDumpSasTestHarness(
                test_harness.getSasTestHarnessInterface()))

    # Trigger CPAS.
    logging.info('Step 9: Triggering CPAS.')
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

    logging.info('Step 10: (done below).')

    # Inform the SAS UUT that the ESC-monitored DPA is activated.
    if using_esc_dpa:
      if dpa_config['frequencyRange']['lowFrequency'] < LOW_FREQUENCY_LIMIT_HZ:
        logging.info(
            'Skipping Step 11: an always-active DPA was specified, so there is '
            'no need to activate.'
        )
      else:
        dpa_activation_request = {
            'dpaId': dpa_config['dpaId'],
            'frequencyRange': dpa_config['frequencyRange']
        }
        logging.info('Step 11: activating DPA: %s', dpa_activation_request)
        self._sas_admin.TriggerDpaActivation(dpa_activation_request)
    else:
      logging.info(
          'Skipping Step 11: using portal-controlled DPA which is active by '
          'default.'
      )

    logging.info('Step 12: wait + heartbeat.')
    time.sleep(240)
    for domain_proxy in domain_proxies:
      domain_proxy.heartbeatForAllActiveGrants()
    grant_info = data.getAuthorizedGrantsFromDomainProxies(domain_proxies)

    logging.info('Step 10, 13, + CHECK: DPA aggregate interference check.')
    logging.info('Checking DPA %s', dpa_config)
    dpa_filename = config['dpaDatabaseConfig'][
        'filePath'] if using_portal_dpa else None
    dpa = dpa_mgr.BuildDpa(
        dpa_config['dpaId'],
        dpa_config['points_builder'],
        portal_dpa_filename=dpa_filename)
    low_freq_mhz = dpa_config['frequencyRange']['lowFrequency'] // ONE_MHZ
    high_freq_mhz = dpa_config['frequencyRange']['highFrequency'] // ONE_MHZ
    dpa.ResetFreqRange([(low_freq_mhz, high_freq_mhz)])
    dpa.SetGrantsFromFad(sas_uut_fad, test_harness_fads)
    dpa.ComputeMoveLists()
    # Check grants do not exceed each DPAs interference threshold.
    self.assertTrue(
        dpa.CheckInterference(
            sas_uut_active_grants=grant_info,
            margin_db=dpa_config['movelistMargin'],
            channel=(low_freq_mhz, high_freq_mhz),
            do_abs_check_single_uut=(num_peer_sases == 0)))

    # Stop test harness servers.
    for test_harness in test_harnesses:
      test_harness.shutdown()
      del test_harness

    if dpa_database_server:
      del dpa_database_server
