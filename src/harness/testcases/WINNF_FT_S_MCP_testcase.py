#    Copyright 2017 SAS Project Authors. All Rights Reserved.
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
import sas_objects
import constraint_testcase
from util import winnforum_testcase, configurable_testcase, writeConfig, \
  loadConfig, generateCpiRsaKeys, generateCpiEcKeys, convertRequestToRequestWithCpiSignature

class MultiConstraintProtectionTestcase(constraint_testcase.ConstraintTestcase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def generate_MCP_1_default_config(self,filename):
    """ Generates the WinnForum configuration for MCP.1. """
    # Load Grant requests
    grant_record_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_record_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_1.json')))
    grant_record_3 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_2.json')))
    grant_record_4 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_3.json')))
    
    #Load CBSD
    device_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_3 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_4 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_d.json')))

    # Load GWPZ Record
    gwpz_record_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'gwpz_record_0.json')))

    # Load FSS record
    fss_record_1 =  json.load(
        open(os.path.join('testcases', 'testdata', 'fss_record_0.json')))
    fss_record_2 =  json.load(
        open(os.path.join('testcases', 'testdata', 'fss_record_1.json')))

    # Load ESC record
    esc_record_1 =  json.load(
        open(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json')))


    # Create the actual config.
    config = {
        'cbsdRecords': [{'registrationRequests':[device_1,device_2],'grantRequests':[grant_record_1,grant_record_2]},
                        {'registrationRequests':[device_3,device_4],'grantRequests':[grant_record_3,grant_record_4]}],
        'IAPRecords': [[
      { 'type': 'FSS','Record': [fss_record_1] },
      { 'type': 'ESC','Record': [esc_record_1] } ],
      [ { 'type': 'GWPZ','Record': [gwpz_record_1]},
      { 'type': 'FSS', 'Record': [fss_record_2]}]],
	'sas_hareness': [{'name': 'SAS-TH-1',
			'url': ['localhost', '9001'],
			'cert_file': 'certs/server_a.cert',
			'key_file': 'certs/server_a.key'},
	                {
			'name': 'SAS-TH-2',
			'url': ['localhost', '9002'],
			'cert_file': 'certs/server_b.cert',
			'key_file': 'certs/server_b.key'
		        }],
        'sas_uut': {'name': 'SAS-UUT',
                        'url': ['localhost', '9000'],
                        'cert_file': 'certs/server.cert',
                        'key_file': 'certs/server.key'}, 
        'K':3, 
        'headroom':{'MgPpa':2,'MgGwpz':2,'MgCochannel':2,'MgBlocking':2,'MgOobe':2,'MgEsc':2},
        'DPAactiveInfo':[],
        'DPAdeactiveInfo':[]
       }
    
    writeConfig(filename, config)


  @configurable_testcase(generate_MCP_1_default_config) 
  def test_WINNF_FT_S_MCP_1(self,config_filename):
    """SAS manages a mix of GAA and PAL Grants in 3550 MHz
       to 3700 MHz to protect configurable IAP-protected entities and DPAs
    """
    config = loadConfig(config_filename)
    pre_iap_headroom = config ['headroom']

    
    #Step 1 : Load DPAs
    self._sas_admin.TriggerLoadDpas()

    #STEP 2 : ESC informs SAS about inactive DPA
    self._sas_admin.TriggerBulkDpaActivation({'activate':False})

    #Step 3 : creates multiple SAS TH, and Load predefined FAD,CBSD 
    self.createSASTH(config)
    self.configureFadForEachSASTH(0)
    
    #fad objects get the fad dumps from the remote SAS configured with 'url'
    fad_object_th = []
    for N in len(config['sas_hareness']):
       cert = os.path.join('certs',config['sas_hareness'][N]['cert_file'])
       key  = os.path.join('certs',config['sas_hareness'][N]['key_file'])
       fad_object_th.append(FullActivityDump(cert,key,config['sas_hareness'][N]['url']))
       fad_records.append(fad_object_th[N])

    #for UUT creating fad object
    cert = os.path.join('certs',config['sas_uut']['cert_file'])
    key  = os.path.join('certs',config['sas_uut']['key_file'])
    fad_uut_object = FullActivityDump(cert,key,config['sas_uut']['url'])
    fad_records.append(fad_uut_object)

    # informing SAS UUT about SAS TH 
    for N in len(config['sas_hareness']):
       self._sas_admin.InjectPeerSas({'certificateHash': config[N]['certificateHash'],
                                     'url': 'https://' + config[N] ['url']+ '/dump'}) 
    

    #Step 4,5 : Inject IAP protected entities into UUT
    for k in  config['K']:	
       for records in config['IAPRecords'][k]:
          if records['type'] == "FSS":
             self._sas_admin.InjectFss(records['Record'])
          if records['type'] == "GWPZ":
             self._sas_admin.InjectWisp(records['Record'])
          if records['type'] == "ESC":
             self._sas_admin.InjectEsc(records['Record'])
          if records['type'] == "PPA":
             self._sas_admin.InjectZoneData(records['Record'])

     
        
       # Step 6 : Trigger FAD generation with SAS test harness
       if len(config['sas_hareness']) > 0 :
          self._sas_admin.TriggerFullActivityDump() # triggers to UUT

          # Step 7 : Pull FAD records from SAS UUT
          fad_uut_object.initiate_full_activity_dump()
          
          for N in len(config['sas_hareness']):
             fad_object_th[N].initiate_full_activity_dump()



       # Step 8 : Trigger CPAS and wait until completion
       self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

       # Step 9 : Call IAP reference model, calculated at step 12
       #collect all the protected Entites
       protectedEntities.append(config['IAPRecords'][k])

       for pe in protectedEntities:
          fad_records_iap = []
          if pe['type'] == 'FSS':
           
             # Find the FSS records with OOBE protection
             fss_with_oobe = self.findFSSInIAPwithOOBE(protectedEntities)
             if fss_with_oobe :
                # Call FSS purge list reference model to fetch cbsd to be purged. output:List of CBSDs
                cbsd_purge_list = FSSPurgeListRefModel(fad_records,fssOobe)
 
                # Remove purged cbsd from fad record
                fad_records_iap = removePurgeCbsd(fad_records,cbsd_purge_list)
             else:
                fad_records_iap = fad_records
          #Call IAP reference model, fad_records contains fad_UUT and fad_SAS_TH
          #To-Do : If there is any change in the API defination, parameters need to be updated
          iap_refmodel_margin_list = IapReferenceModel(config['headroom'], pe,fad_records_iap)
 

       # Step 10 : Register N(2,k)CBSDs with SAS UUT
       # Use DP objects to get CBSD registered
       # creation of Domain Proxy Object
       dp_cert = os.path.join('certs', 'dp_client.cert')
       dp_key = os.path.join('certs', 'dp_client.key')
       reg_records = config['cbsdRecords'][k]['registrationRequests']
       grant_records = config['cbsdRecords'][k]['grantRequests']	
       #dp.initialize triggers the registration and grant for the records passes as parameters
       dp = DomainProxy(dp_cert,dp_key,reg_records,grant_records)

     
       # Step 11 : Send heartbeat request	
       dp.heartbeat_request_for_all_grants()
       
       # Step 12 : Invoke Aggregate Interference Model
	
       cbsd_agg_list = dp.get_all_cbsd_objects_with_atleast_one_grant()

       for pe in protectedEntities:
 
          #invoking Aggregate Interference API,
          agg_interference_list = AggregateInterferenceModel(cbsd_agg_list,pe)
      
          #invoking Aggregate Interference API,with IAP reference model EIRP values
          # This is dummy API, need clarity on the parameters to be passed  
          agg_interference_iap_list = AggregateInterferenceModelWithIAP(cbsd_agg_list,pe)
          
          #check MCP.1
          checkMCP_IAP(pe,agg_interference_list,agg_interference_iap_list,pre_iap_headroom,leftOverAlloc)

       # Step 13 : Configure SAS Harness with FAD,trigger FAD generation
       self.configureFadForEachSASTH(k+1)
       for N in len(config['sas_hareness']):
          fad_object_th[N].initiate_full_activity_dump()


       
       #Step 14: Trigger Full Activty Dump to UUT 
       self._sas_admin.TriggerFullActivityDump() # triggers to UUT

       # Step 15 : Pull FAD records from SAS UUT
       fad_uut_object.initiate_full_activity_dump()
       
       # Step 16 : Trigger CPAS and wait for its completion
       self.self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()
       
       # Step 17 : Call IAP reference model
       # To DO: invoking DPA Move Reference model
       for pe in protectedEntities:
         fad_records_iap = []
         if pe['type'] == 'FSS' :
            # Find the FSS records with OOBE protection
            fss_with_oobe = self.findFSSInIAPwithOOBE(protectedEntities)
            if  fss_with_oobe :
               # Call FSS purge list reference model to fetch cbsd to be purged. output:List of CBSDs
               cbsd_purge_list = FSSPurgeListRefModel(fad_records,fssOobe)
 
               # Remove purged cbsd from fad record
               fad_records_iap = removePurgeCbsd(fad_records,cbsd_purge_list)
            else:
               fad_records_iap = fad_records

         #Call IAP reference model, fad_records contains fad_UUT and fad_SAS_TH
         iap_refmodel_margin_list = IapReferenceModel(config['headroom'], pe,fad_records_iap)
 

 
 
       # Step 18,19,20 and 21 : 
       # Send heartbeat request for the grants, relinquish the grant, grant request and heartbeat for new grant
       dp.HeartBeatRequestForAllGrants_relinquish()

       #Step 22: Calculating the Aggregate interface and IAP reference model invoke.
       cbsd_agg_list = dp.GetAllCbsdObjectsWithAtLeastOneGrant()
       for pe in protectedEntities:
             
          #invoking Aggregate Interference Model API,
          agg_interface_list = AggregateInterferenceModel(cbsd_agg_list,pe)

          #invoking Aggregate Interference API,with IAP reference model EIRP values
          # This is dummy API, need clarity on the parameters to be passed  
          agg_interference_iap_list = AggregateInterferenceModelWithIAP(cbsd_agg_list,pe)
 
          #check MCP.1
          checkMCP_IAP(pe,agg_interface_list,agg_interference_iap_list,pre-IAPHeadroom,leftOverAlloc)

       #Step 23: ESC Test harness enables DPA activations
       #deactivated the DPAdeactiveInfo[k] DPA IDs
       self._sas_admin.TriggerDpaDeactivation(config['DPAdeactiveInfo'][k])

       #activated the DPAactiveInfo[k] DPA IDs
       #step 24: wait for 240 sec if DPA is activated in step 23 else 15 sec
       if config['DPAactiveInfo'][k] :
          TriggerDpaActivation(config['DPAactiveInfo'][k])
          sleep (240)
       else:
          sleep(15)

       # Step 25,26,27 and 28 : 
       # Send heartbeat request for the grants, relinquish the grant, grant request and heartbeat for new grant
       dp.heartbeat_request_for_all_grants_and_update_grants()
       #step 29
       # TODO: Aggregate interference for DPA


       #Step 30:Invoke Aggregate Interference Model
	
       cbsd_agg_list = dp.get_all_cbsd_objects_with_atleast_one_grant()
       
       for pe in protectedEntities :
 
          #invoking Aggregate Interference API,
          agg_interface_list = AggregateInterferenceModel(cbsd_agg_list,pe)

          #check MCP.1 DPA
          #TODO: need to invoke the DPA check
          #check MCP.1 IAP
          checkMCP_IAP(pe,agg_interface_list,agg_interference_iap_list,pre_iap_headroom,left_over_alloc)
   
  def checkMCP_IAP(self,pe,agg_interface_list,iap_refmodel_margin_list,pre_iap_headroom,left_over_alloc):
    """ Performs check step """
    # To Do
    if ((pe['type'] == 'FSS') or (pe['type'] == 'ESC')): # only one lelement with fifferent frequency
       for p in agg_interface_list:
          self.assertLessEqual(agg_interface_list[p] , (iap_refmodel_margin_list[p] +pre_iap_headroom + leftOverAlloc))

    if (pe['type'] == 'PPA') or (pe['type'] == 'GWPZ') :
       points_valid =0
       for p in len(agg_interface_list):
          if (agg_interface_list[p] <= (iap_refmodel_margin_list[p] +pre_iap_headroom + leftOverAlloc)):
             points_valid = points_valid +1
          else:
             continue
       self.assertLessEqual(points_valid , (p*0.95))

  def removePurgeCbsd(fad_records,cbsd_purge_list):
    """ Remove purged cbsd """
