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

import time
import json
import os
import sas
import sas_objects
import constraint_testcase
from util import winnforum_testcase, configurable_testcase, writeConfig, \
  loadConfig, generateCpiRsaKeys, generateCpiEcKeys, convertRequestToRequestWithCpiSignature
from reference_models.aggregate_interference import agg_interf
from reference_models.pre_iap import pre_iap
from reference_models.iap import iap


class MultiConstraintProtectionTestcase(constraint_testcase.ConstraintTestcase):

    def setUp(self):
        self._sas, self._sas_admin = sas.GetTestingSas()
        self._sas_admin.Reset()
  
    def tearDown(self):
        pass
  
    def generate_MCP_1_default_config(self, filename):
        """ Generates the WinnForum configuration for MCP.1. """
        # Load CBSD
        device_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'device_a.json')))
        device_2 = json.load(
          open(os.path.join('testcases', 'testdata', 'device_b.json')))
        device_3 = json.load(
          open(os.path.join('testcases', 'testdata', 'device_c.json')))
        device_4 = json.load(
          open(os.path.join('testcases', 'testdata', 'device_d.json')))
        device_5 = json.load(
          open(os.path.join('testcases', 'testdata', 'device_e.json')))
  
        # Load Grant requests
        grant_request_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_0.json')))
        grant_request_2 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_1.json')))
        grant_request_3 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_2.json')))
        grant_request_4 = json.load(
          open(os.path.join('testcases', 'testdata', 'grant_3.json')))
      
        # Load GWPZ Record
        gwpz_record_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'gwpz_record_0.json')))
  
        # Load FSS record
        fss_record_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'fss_record_0.json')))
  
        # Load ESC record
        esc_record_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json')))
     
        # Load PPA record
        ppa_record_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'ppa_record_0.json'))) 
        # Registration configuration for iteration 1
        cbsd_records_iter_1 = {'registrationRequests': [device_1, device_2],
                              'grantRequests': [grant_request_1, grant_request_2]}
        cbsd_records_iter_2 = {'registrationRequests': [device_3, device_4],
                              'grantRequests': [grant_request_3, grant_request_4]}
        protected_entities_iter_1 = {'PPA': [ppa_record_1], 'ESC': [esc_record_1]}
        protected_entities_iter_2 = {'GWPZ': [gwpz_record_1] , 'FSS': [fss_record_1]}


        # SAS Test Harness FAD records
        sas_th_cbsd_0 = json.load(
          open(os.path.join('testcases', 'testdata', 'cbsd_0.json')))
        sas_th_cbsd_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'cbsd_1.json')))
        sas_th_cbsd_2 = json.load(
          open(os.path.join('testcases', 'testdata', 'cbsd_2.json')))
        sas_th_cbsd_3 = json.load(
          open(os.path.join('testcases', 'testdata', 'cbsd_3.json')))
        sas_th_cbsd_4 = json.load(
          open(os.path.join('testcases', 'testdata', 'cbsd_4.json')))
        sas_th_cbsd_5 = json.load(
          open(os.path.join('testcases', 'testdata', 'cbsd_5.json')))

        sas_th_0_cbsd_iter_0 = [sas_th_cbsd_0]
        sas_th_0_cbsd_iter_1 = [sas_th_cbsd_1]
        sas_th_0_cbsd_iter_2 = [sas_th_cbsd_2]
        sas_th_1_cbsd_iter_0 = [sas_th_cbsd_3]
        sas_th_1_cbsd_iter_1 = [sas_th_cbsd_4]
        sas_th_1_cbsd_iter_2 = [sas_th_cbsd_5]
    
        # Load DPA record
        dpa_0 = json.load(
          open(os.path.join('testcases', 'testdata', 'dpa_0.json')))
        dpa_1 = json.load(
          open(os.path.join('testcases', 'testdata', 'dpa_1.json')))

        sas_harness_0 = {
                    'name': 'SAS-TH-1',
                    'url': 'localhost:9001',
                    'cert_file': 'certs/server_a.cert',
                    'key_file': 'certs/server_a.key',
                    'certificateHash': 'dummy',
                    'cbsdRecord': [sas_th_0_cbsd_iter_0, sas_th_0_cbsd_iter_1, sas_th_0_cbsd_iter_2],
                    'fileServePath': 'sas_harness_2/'
                }
        sas_harness_1 = {
                    'name': 'SAS-TH-2',
                    'url': 'localhost:9002',
                    'cert_file': 'certs/server_b.cert',
                    'key_file': 'certs/server_b.key',
                    'certificateHash': 'dummy',
                    'cbsdRecord': [sas_th_1_cbsd_iter_0, sas_th_1_cbsd_iter_1, sas_th_1_cbsd_iter_2],
                    'fileServePath': 'sas_harness_1/'
                }
        # Create the actual config.
        config = {
            'cbsdRecordsN1': [cbsd_records_iter_1, cbsd_records_iter_2],
            'protectedEntitiesPIAP': [protected_entities_iter_1, protected_entities_iter_2],
            'sasHarness': [sas_harness_0, sas_harness_1],
            'dpConfig': {'cert': 'dp_client.cert', 'key': 'dp_client.key'},
            'K': 2,
            'headroom': {'MgPpa': 2, 'MgGwpz': 2, 'MgCochannel': 2,
                         'MgBlocking': 2, 'MgOobe': 2, 'MgEsc': 2},
            'dpaActiveList': [dpa_0],
            'dpaInactiveList': [dpa_1],
            'protectionThreshold': {'QPpa': -80, 'QGwpz': -80,
                                    'QCochannel': -129, 'QBlocking': -60, 'QEsc': -109},
            'deltaIap': 2
  
           }
        writeConfig(filename, config)

    @configurable_testcase(generate_MCP_1_default_config) 
    def test_WINNF_FT_S_MCP_1(self, config_filename):
        """SAS manages a mix of GAA and PAL Grants in 3550 MHz
           to 3700 MHz to protect configurable IAP-protected entities and DPAs
        """
        config = loadConfig(config_filename)
        protected_entities = []
        list_protected_entities = [] 
        dp_cert_file = config['dpConfig']['cert']
        dp_key_file = config['dpConfig']['key']
        dp_cert = os.path.join('certs', dp_cert_file)
        dp_key = os.path.join('certs', dp_key_file)
        dp = sas_objects.DomainProxy(dp_cert, dp_key, self._sas)

        # Light verification of the input configuration
        self.assertEqual(len(config['cbsdRecordsN1']), config['K'])
        self.assertEqual(len(config['protectedEntitiesPIAP']), config['K'])
        for sasHarness in config['sasHarness']:
            self.assertEqual(len(sasHarness['cbsdRecord']), config['K'] + 1)
        for x in range(config['K']):
            records = config['protectedEntitiesPIAP'][x]
            list_protected_entities.extend(records.keys())
        for key in list_protected_entities:
            self.assertIn(key, ('FSS', 'GWPZ', 'PPA', 'ESC'))

        # Step 1 : Load DPAs
        self._sas_admin.TriggerLoadDpas()
  
        # STEP 2 : ESC informs SAS about inactive DPA
        self._sas_admin.TriggerBulkDpaActivation({'activate': False})
  
        # Step 3 : creates multiple SAS TH, and Load predefined FAD,CBSD
        self.create_sas_th(config)
        self.configure_fad_for_each_sas_th(0)
        
        # fad objects get the fad dumps from the remote SAS configured with 'url'
        fad_th_objects = []
        for N in range(len(config['sasHarness'])):
            cert = os.path.join('certs', config['sasHarness'][N]['cert_file'])
            key = os.path.join('certs', config['sasHarness'][N]['key_file'])
            fad_th_objects.append(sas_objects.FullActivityDump(cert, key, config['sasHarness'][N]['url']))
  
        # for UUT creating fad object
        fad_uut_object = sas_objects.FullActivityDump(cert, key, self._sas._base_url)
  
        # informing SAS UUT about SAS TH 
        for sasHarness in config['sasHarness']:
            self._sas_admin.InjectPeerSas({'certificateHash': sasHarness['certificateHash'],
                                          'url': 'https://' + sasHarness['url'] + '/dump'})
  
        # Step 4,5 : Inject IAP protected entities into UUT
        for k in range(config['K']):
            records = config['protectedEntitiesPIAP'][k]
            if records.has_key('FSS'):
                for fss_record in records['FSS']:
                    self._sas_admin.InjectFss({'record': fss_record})
            if records.has_key('GWPZ'):
                for gwpz_record in records['GWPZ']:
                    self._sas_admin.InjectWisp({'record': gwpz_record})
            if records.has_key('ESC'):
                for esc_record in records['ESC']:
                    self._sas_admin.InjectEscSensorDataRecord({'record': esc_record})
            if records.has_key('PPA'):
                for ppa_record in records['PPA']:
                    self._sas_admin.InjectZoneData({'record': ppa_record})

            # Step 6 : Trigger FAD generation with SAS test harness
            if len(config['sasHarness']) > 0:
                self._sas_admin.TriggerFullActivityDump()
  
                # Step 7 : Pull FAD records from SAS UUT
                fad_uut_object.initiate_full_activity_dump()
              
                for N in range(len(config['sasHarness'])):
                    fad_th_objects[N].initiate_full_activity_dump()

            # Step 8 : Trigger CPAS and wait until completion
            self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()
  
            # Step 9 : Call IAP reference model, calculated at step 12
            # Collect all the protected Entites
            protected_entities.append(config['protectedEntitiesPIAP'][k])
  
            # Call Pre IAP model
            pre_iap.pre_iap(protected_entities, fad_uut_object, fad_th_objects)
             
            # Call IAP reference model
            iap_refmodel_margin_list = iap.performIAP(config['protectionThreshold'], config['headroom'],
                                                      protected_entities, fad_uut_object, fad_th_objects)

            # Step 10 : Register N(2,k)CBSDs with SAS UUT
            # Use DP objects to get CBSD registered
            # creation of Domain Proxy Object
            registration_requests = config['cbsdRecordsN1'][k]['registrationRequests']
            grant_requests = config['cbsdRecordsN1'][k]['grantRequests']
            # dp.initialize triggers the registration and grant for the records passes as parameters
            dp.Initialize(registration_requests, grant_requests)

            # Step 11 : Send heartbeat request
            dp.heartbeat_request_for_all_grants()
           
            # Step 12 : Invoke Aggregate Interference Model
            # Get the list of CBSDs
            cbsd_agg_list = dp.get_all_cbsd_object_with_atleast_one_grant()
  
            # Invoking Aggregate Interference API,
            agg_interference_list_ppa_gwpz, agg_interference_list_esc_fss = self.call_aggregate_interference_model(
                cbsd_agg_list, protected_entities)
  
            # check MCP.1
            self.check_mcp_iap(agg_interference_list_ppa_gwpz,
                               agg_interference_list_esc_fss, iap_refmodel_margin_list, config['deltaIap'])
   
            # Step 13 : Configure SAS Harness with FAD,trigger FAD generation
            self.configure_fad_for_each_sas_th(k+1)
            for N in range(len(config['sasHarness'])):
                fad_th_objects[N].initiate_full_activity_dump()
  
            for N in range(len(config['sasHarness'])):
                fad_th_objects[N].initiate_full_activity_dump()
           
            # Step 14: Trigger Full Activty Dump to UUT
            self._sas_admin.TriggerFullActivityDump()
  
            # Step 15 : Pull FAD records from SAS UUT
            fad_uut_object.initiate_full_activity_dump()
           
            # Step 16 : Trigger CPAS and wait for its completion
            self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()
           
            # Step 17 : Call IAP reference model
            # To DO: invoking DPA Move Reference model
            # Call Pre IAP model
            pre_iap.pre_iap(protected_entities, fad_uut_object, fad_th_objects)
  
            # Call IAP reference model
            iap_refmodel_margin_list = iap.performIAP(config['protectionThreshold'], config['headroom'],
                                                      protected_entities, fad_uut_object, fad_th_objects)
   
            # Step 18,19,20 and 21 :
            # Send heartbeat request for the grants, relinquish the grant, grant request and heartbeat for new grant
            dp.heartbeat_request_for_all_grant_and_update_grants()
  
            # Step 22: Calculating the Aggregate interface and IAP reference model invoke.
            cbsd_agg_list = dp.get_all_cbsd_object_with_atleast_one_grant()
          
            # invoking Aggregate Interference API
            agg_interference_list_ppa_gwpz, agg_interference_list_esc_fss = \
                self.call_aggregate_interference_model(cbsd_agg_list, protected_entities)
  
            # check MCP.1
            self.check_mcp_iap(agg_interference_list_ppa_gwpz,
                               agg_interference_list_esc_fss, iap_refmodel_margin_list, config['deltaIap'])

            # Step 23: ESC Test harness enables DPA activations
            # deactivated the dpaInactiveList[k] DPA IDs
            if len(config['dpaInactiveList']) > k:
                self._sas_admin.TriggerDpaDeactivation(config['dpaInactiveList'][k])
  
            # activated the dpaActiveList[k] DPA IDs
            # step 24: wait for 240 sec if DPA is activated in step 23 else 15 sec
            if len(config['dpaActiveList']) > k:
                self._sas_admin.TriggerDpaActivation(config['dpaActiveList'][k])
                time.sleep(240)
            else:
                time.sleep(15)
  
            # Step 25,26,27 and 28 :
            # Send heartbeat request for the grants, relinquish the grant, grant request and heartbeat for new grant
            dp.heartbeat_request_for_all_grant_and_update_grants()
            # Step 29
            # TODO: Aggregate interference for DPA

            # Step 30:Invoke Aggregate Interference Model
            cbsd_agg_list = dp.get_all_cbsd_object_with_atleast_one_grant()
           
            # invoking Aggregate Interference API,
            agg_interference_list_ppa_gwpz, agg_interference_list_esc_fss = \
                self.call_aggregate_interference_model(cbsd_agg_list, protected_entities)
  
            # check MCP.1
            self.check_mcp_iap(agg_interference_list_ppa_gwpz,
                               agg_interference_list_esc_fss, iap_refmodel_margin_list, config['deltaIap'])
  
            # check MCP.1 DPA
            # TODO: need to invoke the DPA checkheartbeat_request_for_all_grant_and_update_grants

            # check_mcp_iap(pe,agg_interference_list,agg_interference_iap_list,pre_iap_headroom,left_over_alloc)
    def check_mcp_iap(self, agg_interference_list_ppa_gwpz, agg_interference_list_esc_fss,
                      iap_refmodel_margin_list, delta_iap):
        """ Performs check step """
        aggregate_list_length = len(agg_interference_list_ppa_gwpz) + len(agg_interference_list_esc_fss)
        iap_list_length = len(iap_refmodel_margin_list)
        points = 0
        self.assertEqual(aggregate_list_length, iap_list_length)
        for unique_point_with_frequency in iap_refmodel_margin_list.keys():
            if agg_interference_list_esc_fss.has_key(unique_point_with_frequency):
                self.assertLessEqual(agg_interference_list_esc_fss[unique_point_with_frequency],
                                     iap_refmodel_margin_list[unique_point_with_frequency] + delta_iap)
            elif (agg_interference_list_ppa_gwpz.has_key(unique_point_with_frequency)
                  and(agg_interference_list_ppa_gwpz[unique_point_with_frequency])):
                if agg_interference_list_ppa_gwpz[unique_point_with_frequency] \
                        <= iap_refmodel_margin_list[unique_point_with_frequency] + delta_iap:
                    points = points + 1
            else:
                raise AssertionError('Aggregate list and iap list do not have matching points')
        points = int(points * 100) / len(agg_interference_list_ppa_gwpz)
        self.assertGreaterEqual(points, 95)
  
    def call_aggregate_interference_model(self, cbsd_list, protected_entities):
        """ Calls aggregate interference model """
        agg_interference_list_ppa_gwpz = []
        agg_interference_list_esc_fss = []
        for protected_records in protected_entities:
            if protected_records.has_key('FSS'):
                for fss_records in protected_records['FSS']:
                    agg_interference_list_esc_fss.append(agg_interf.compute_aggregate_interference_for_fss
                                                         (fss_records, cbsd_list))
            if protected_records.has_key('ESC'):
                for esc_records in protected_records['ESC']:
                    agg_interference_list_esc_fss.append(agg_interf.compute_aggregate_interference_for_esc
                                                         (esc_records, cbsd_list))
            if protected_records.has_key('PPA'):
                for ppa_records in protected_records['PPA']:
                    agg_interference_list_ppa_gwpz.append(agg_interf.compute_aggregate_interference_for_ppa
                                                          (ppa_records, cbsd_list))
            if protected_records.has_key('GWPZ'):
                for gwpz_records in protected_records['GWPZ']:
                    agg_interference_list_ppa_gwpz.append(agg_interf.compute_aggregate_interference_for_gwpz
                                                          (gwpz_records, cbsd_list))
        return agg_interference_list_ppa_gwpz, agg_interference_list_esc_fss
