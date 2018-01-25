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
#import sas_objects
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
    grantRecord_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grantRecord_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    
    #Load CBSD
    device_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    # Load GWPZ Record
    gwpzRecord_1 = json.load(
        open(os.path.join('testcases', 'testdata', 'gwpz_record_0.json')))
    gwpzRecord_2 = json.load(
        open(os.path.join('testcases', 'testdata', 'gwpz_record_0.json')))
    # Load FSS record
    fssRecord_1 =  json.load(
        open(os.path.join('testcases', 'testdata', 'fss_record_0.json')))
    fssRecord_2 =  json.load(
        open(os.path.join('testcases', 'testdata', 'fss_record_0.json')))
    # Load ESC record
    escRecord_1 =  json.load(
        open(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json')))
    escRecord_2 =  json.load(
        open(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json')))


    # Create the actual config.
    config = {
        'cbsdRecords': [{'registrationRequests':[device_1,device_2],'grantRequests':[grantRecord_1,grantRecord_2]},
                        {'registrationRequests':[device_1,device_2],'grantRequests':[grantRecord_1,grantRecord_2]},
                        {'registrationRequests':[device_1,device_2],'grantRequests':[grantRecord_1,grantRecord_2]}],
        'IAPRecords': [[
      { 'type': 'FSS','Record': [fssRecord_1,fssRecord_2] },
      { 'type': 'ESC','Record': [escRecord_1,escRecord_2] } ],
      [ { 'type': 'GWPZ','Record': [gwpzRecord_1]},
      { 'type': 'ESC', 'Record': [escRecord_1]}]],
	'sas_hareness': [{'name': 'SAS-TH-1',
			'url': ['localhost', '9001'],
			'cert_file': 'certs/server.cert',
			'key_file': 'certs/server.key'},
	                {
			'name': 'SAS-TH-2',
			'url': ['localhost', '9002'],
			'cert_file': 'certs/server.cert',
			'key_file': 'certs/server.key'
		         },
		         {
			'name': 'SAS-TH-3',
			'url': ['localhost','9003'],
			'cert_file': 'certs/server.cert',
			'key_file': 'certs/server.key'
		        }],
        'sas_uut': {'name': 'SAS-UUT',
                        'url': ['localhost', '9001'],
                        'cert_file': 'certs/server.cert',
                        'key_file': 'certs/server.key'},
        'numberOfSasTH':2, 
        'K':3, 
        'headroom':1,
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
    sasTHRecords = os.path.join('testcases','configs','test_WINNF_FT_S_MCP_1')
    pre_IAPHeadroom = config ['headroom']
    #creation of Domain Proxy Object	
    dp =  DomainProxyObject()
    
    #Step 1 : Load DPAs
    self._sas_admin.TriggerLoadDpas()

    #STEP 2 : ESC informs SAS about inactive DPA
    self._sas_admin.TriggerBulkDpaActivation({'activate':False})

    #Step 3 : creates multiple SAS TH, and Load predefined FAD,CBSD 
    self.createSASTH(config)
    self.configureFadForEachSASTH(sasTHRecords)
    
    #fad objects get the fad dumps from the remote SAS configured with 'url'
    for N in config['numberOfSasTH']:
       fadObjectTH.append(FullActivityDumpObject ())
       fadObjectTH[N].initialize(config['sas_hareness'][k]['url'])
       fad_records.append(fadObjectTH[N])

    #for UUT creating fad object
    fadUUTObject = FullActivityDumpObject()	
    fad_record.append(fadUUTObject)

    # informing SAS UUT about SAS TH 
    for N in config['numberOfSasTH']:
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
     
        
       # Step 6 : Trigger FAD generation with SAS test harness
       if config['numberOfSasTH'] > 0 :
          self._sas_admin.TriggerFullActivityDump() # triggers to UUT

          # Step 7 : Pull FAD records from SAS UUT
          
          fadUUTObject.initialize(config['sas_uut']['url'])


       # Step 8 : Trigger CPAS and wait until completion
       self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()

       # Step 9 : Call IAP reference model, calculated at step 12
       #collect all the protected Entites
       protectedEntities.append(config['IAPRecords'][k])




       # Step 10 : Register N(2,k)CBSDs with SAS UUT
       # Use DP objects to get CBSD registered
       dp_cert = os.path.join('certs', 'dp_client.cert')
       dp_key = os.path.join('certs', 'dp_client.key')
       reg_records = config['cbsdRecords'][k]['registrationRequests']
       grant_records = config['cbsdRecords'][k]['grantRequests']	
       #dp.initialize triggers the registration and grant for the records passes as parameters
       dp.Initialize(dp_cert,dp_client,reg_records,grant_records)

     
       # Step 11 : Send heartbeat request	
       dp.HeartBeatRequestForAllGrants()
       
       # Step 12 : Invoke Aggregate Interface Model
	
       cbsdAggList = dp.GetAllCbsdObjectsWithAtLeastOneGrant()

       for pe in protectedEntities:
          fad_records_IAP = [] 
          if (pe['type'] == 'FSS'):
           
             # Find the FSS records with OOBE protection
             fssWithOobe = self.findFSSInIAPwithOOBE(protectedEntities)
             if (fssWithOobe):
                # Call FSS purge list reference model to fetch cbsd to be purged. output:List of CBSDs
                cbsd_purge_list = FSSPurgeListRefModel(fad_record,fssOobe)
 
                # Remove purged cbsd from fad record
                fad_records_IAP = removePurgeCbsd(fad_record,cbsd_purge_list) 
             else:
                fad_records_IAP = fad_record
          #Call IAP reference model, fad_records contains fad_UUT and fad_SAS_TH
          IAPRefModelMarginList = IapReferenceModel(config['headroom'], pe,fad_records_IAP)
 
          #invoking Aggregate Interface API,
          AggInterfaceList = AggregateInterfaceModel(cbsdAggList,pe)
      
          #check MCP.1
          checkMCP_IAP(pe,AggInterfaceList,IAPRefModelMarginList,pre_IAPHeadroom,leftOverAlloc)

       # Step 13 : Configure SAS Harness with FAD,trigger FAD generation
       for N in config['numberOfSasTH']:
          fadObjectTH[N].initialize(config['SasTHUrl'][k])

       
       #Step 14: Trigger Full Activty Dump to UUT 
       self._sas_admin.TriggerFullActivityDump() # triggers to UUT

       # Step 15 : Pull FAD records from SAS UUT
       fadUUTObject.initialize(config['sas_uut']['url'])
       
       # Step 16 : Trigger CPAS and wait for its completion
       self.self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()
       
       # Step 17 : Call IAP reference model
       # To DO: invoking DPA Move REference model
  
 
       # Step 18,19,20 and 21 : 
       # Send heartbeat request for the grants, relinquish the grant, grant request and heartbeat for new grant
       dp.HeartBeatRequestForAllGrants_relinquish()

       #Step 22: Calculating the Aggregate interface and IAP reference model invoke.
       cbsdAggList = dp.GetAllCbsdObjectsWithAtLeastOneGrant()
       for pe in protectedEntities:
          fad_records_IAP = []
          if (pe['type'] == 'FSS'):
             # Find the FSS records with OOBE protection
             fssWithOobe = self.findFSSInIAPwithOOBE(protectedEntities)
             if (fssWithOobe):
                # Call FSS purge list reference model to fetch cbsd to be purged. output:List of CBSDs
                cbsd_purge_list = FSSPurgeListRefModel(fad_record,fssOobe)
 
                # Remove purged cbsd from fad record
                fad_records_IAP = removePurgeCbsd(fad_record,cbsd_purge_list) 
             else:
                fad_records_IAP = fad_record

          #Call IAP reference model, fad_records contains fad_UUT and fad_SAS_TH
          IAPRefModelMarginList = IapReferenceModel(config['headroom'], pe,fad_records_IAP)
          
             
          #invoking Aggregate Interface API,
          AggInterfaceList = AggregateInterfaceModel(cbsdAggList,pe)

          #check MCP.1
          checkMCP_IAP(pe,AggInterfaceList,IAPRefModelMarginList,pre-IAPHeadroom,leftOverAlloc)

       #Step 23: ESC Test harness enables DPA activations
       #deactivated the DPAdeactiveInfo[k] DPA IDs
       self._sas_admin.TriggerDpaDeactivation(config['DPAdeactiveInfo'][k])

       #activated the DPAactiveInfo[k] DPA IDs
       #step 24: wait for 240 sec if DPA is activated in step 23 else 15 sec
       if (config['DPAactiveInfo'][k]):
          TriggerDpaActivation(config['DPAactiveInfo'][k])
          sleep (240)
       else:
          sleep(15)

       # Step 25,26,27 and 28 : 
       # Send heartbeat request for the grants, relinquish the grant, grant request and heartbeat for new grant
       dp.HeartBeatRequestForAllGrants_relinquish()

       #step 29
       # TODO: Aggregate interface for DPA


       #Step 30:Invoke Aggregate Interface Model
	
       cbsdAggList = dp.GetAllCbsdObjectsWithAtLeastOneGrant()
       
       for pe in protectedEntities :
          fad_records_IAP = [] 
          if (pe['type'] == 'FSS'):
           
             # Find the FSS records with OOBE protection
             fssWithOobe = self.findFSSInIAPwithOOBE(protectedEntities)
             if (fssWithOobe):
                # Call FSS purge list reference model to fetch cbsd to be purged. output:List of CBSDs
                cbsd_purge_list = FSSPurgeListRefModel(fad_record,fssOobe)
 
                # Remove purged cbsd from fad record
                fad_records_IAP = removePurgeCbsd(fad_record,cbsd_purge_list) 
             else:
                fad_records_IAP = fad_record
     
          #Call IAP reference model, fad_records contains fad_UUT and fad_SAS_TH
          IAPRefModelMarginList = IapReferenceModel(config['headroom'], pe,fad_record_IAP)
 
 
          #invoking Aggregate Interface API,
          AggInterfaceList = AggregateInterfaceModel(cbsdAggList,pe)

          #check MCP.1 DPA
          #TODO: need to invoke the DPA check
          #check MCP.1 IAP
          checkMCP_IAP(pe,AggInterfaceList,IAPRefModelMarginList,pre-IAPHeadroom,leftOverAlloc)
   
  def checkMCP_IAP(self,pe,AggInterfaceList,IAPRefModelMarginList,pre_IAPHeadroom,leftOverAlloc):
    """ Performs check step """
    # To Do
    if ((pe['type'] == 'FSS') or (pe['type'] == 'ESC')): # only one lelement with fifferent frequency
       for p in AggInterfaceList:
          self.assertLessEqual(AggInterfaceList[p] , (IAPRefModelMarginList[p] +pre_IAPHeadroom + leftOverAlloc))

    if ((pe['type'] == 'PPA') or (pe['type'] == 'GWPZ')):
       points_valid =0
       for p in AggInterfaceList:
          if (AggInterfaceList[p] <= (IAPRefModelMarginList[p] +pre_IAPHeadroom + leftOverAlloc)):
             points_valid = points_valid +1
          else:
             continue
       self.assertLessEqual(points_valid , (p*0.95))

  def removePurgeCbsd(fad_record,cbsd_purge_list):
    """ Remove purged cbsd """
