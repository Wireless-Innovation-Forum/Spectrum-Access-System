#    Copyright 2016 SAS Project Authors. All Rights Reserved.
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
from  util import winnforum_testcase, makePpaAndPalRecordsConsistent
import sas_testcase
import hashlib
from datetime import datetime, timedelta

class FullActivityDumpMessageTestcase(sas_testcase.SasTestCase):

    def setUp(self):
        self._sas, self._sas_admin = sas.GetTestingSas()
        self._sas_admin.Reset()

    def tearDown(self):
        pass
    
    def generate_FAD_1_default_config(self, filename):
        """Generates the WinnForum configuration for FAD.1"""
        # Load device info
        device_a = json.load(
            open(os.path.join('testcases', 'testdata', 'device_a.json')))
        device_b = json.load(
            open(os.path.join('testcases', 'testdata', 'device_b.json')))
        device_c = json.load(
            open(os.path.join('testcases', 'testdata', 'device_c.json')))
        # Device #2 is Category B
        # pre-loaded.
        self.assertEqual(device_d['cbsdCategory'], 'B')
        conditionals_b = {
            'cbsdCategory': device_b['cbsdCategory'],
            'fccId': device_b['fccId'],
            'cbsdSerialNumber': device_b['cbsdSerialNumber'],
            'airInterface': device_b['airInterface'],
            'installationParam': device_b['installationParam']
        }
        conditionals = {'registrationData': [conditionals_b]}
        devices = [device_a, device_b, device_c]
        # Grants
        grants = []
        for index in range(len(devices)):
            grants[index] = json.load(
             open(os.path.join('testcases', 'testdata', 'grant_0.json')))
        # PPAs and PALs
        ppas = []
        pals = []
        pal_low_frequency = 3550000000.0
        pal_high_frequency = 3560000000.0
        pal_record = json.load(
          open(os.path.join('testcases', 'testdata', 'pal_record_0.json')))
        ppa_record = json.load(
          open(os.path.join('testcases', 'testdata', 'ppa_record_0.json')))
        ppas[0], pals[0] = makePpaAndPalRecordsConsistent(ppa_record,
                                                                [pal_record],
                                                                pal_low_frequency,
                                                                pal_high_frequency,
                                                                device_a['userId'])
        # ESC senosrs
        esc_sensors = []
        esc_sensors[0] = json.load(
              open(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json')))
        config = {
            'registrationRequests': devices,
            'conditionalRegistrationData': conditionals,
            'grants': grants,
            'ppas': ppas,
            'pals': pals,
            'esc_sensors' : esc_sensors
        }
        writeConfig(filename, config)
    
    def assertCbsdRecord(self, registration_request, grant_request, grant_response, recordData):
        for index, device in enumerate(registration_request):
            record_id = 'cbsd/'+ device['fccId']+'/'+ hashlib.sha1(device['cbsdSerialNumber']).hexdigest()
            cbsd_record = [record['registration'] for record in recordData if record['id'] == record_id]
            self.assertEqual(1, len(cbsd_record))
            self.assertEqual(device['cbsdCategory'], cbsd_record[0]['cbsdCategory'])
            self.assertEqual(device['fccId'], cbsd_record[0]['fccId'])
            self.assertEqual(device['airInterface']['radioTechnology'],\
                             cbsd_record[0]['airInterface']['radioTechnology'])
            self.assertEqual(device['installationParam']['latitude'],\
                             cbsd_record[0]['installationParam']['latitude'])
            self.assertEqual(device['installationParam']['longitude'],\
                             cbsd_record[0]['installationParam']['longitude'])
            self.assertEqual(device['installationParam']['height'],\
                             cbsd_record[0]['installationParam']['height'])
            self.assertEqual(device['installationParam']['heightType'], \
                             cbsd_record[0]['installationParam']['heightType'])
            self.assertEqual(device['installationParam']['indoorDeployment'], \
                             cbsd_record[0]['installationParam']['indoorDeployment'])
            self.assertEqual(device['installationParam']['antennaGain'], \
                             cbsd_record[0]['installationParam']['antennaGain'])     
            self.assertEqual(device['installationParam']['antennaAzimuth'], \
                             cbsd_record[0]['installationParam']['antennaAzimuth'])        
            self.assertEqual(device['installationParam']['antennaDowntilt'], \
                             cbsd_record[0]['installationParam']['antennaDowntilt'])       
            self.assertEqual(device['installationParam']['antennaBeamwidth'], \
                             cbsd_record[0]['installationParam']['antennaBeamwidth'])    
                         
            # Get grants by cbsd_id
            grants_of_cbsd = [cbsd['grants'] for cbsd in recordData if cbsd['id'] == record_id]
            self.assertEqual(1, len(grants_of_cbsd))
            self.assertTrue('id' in grants_of_cbsd[0])
            # Verify the Grant Of the Cbsd
            if grants_of_cbsd[0]['requestedOperationParam'] is not None :
                self.assertEqual(grants_of_cbsd[0]['requestedOperationParam']['maxEirp'],\
                             grant_request[index]['operationParam']['maxEirp'])    
                self.assertEqual(grants_of_cbsd[0]['requestedOperationParam']['operationFrequencyRange']\
                                 ['lowFrequency'], grant_request[index]['operationParam']['operationFrequencyRange']['lowFrequency'])
                self.assertEqual( grants_of_cbsd[0]['requestedOperationParam']\
                                 ['operationFrequencyRange']['highFrequency'], grant_request[index]['operationParam']\
                                 ['operationFrequencyRange']['highFrequency']) 
                
            self.assertEqual( grants_of_cbsd[0]['operationParam']['maxEirp'],\
                             grant_request[index]['operationParam']['maxEirp'])    
            self.assertEqual( grants_of_cbsd[0]['operationParam']['operationFrequencyRange']['lowFrequency'],\
                             grant_request[index]['operationParam']['operationFrequencyRange']['lowFrequency'])
            self.assertEqual(grants_of_cbsd[0]['operationParam']['operationFrequencyRange']['highFrequency'],\
                             grant_request[index]['operationParam']['operationFrequencyRange']['highFrequency'])
            self.assertEqual(grants_of_cbsd[0]['channelType'], grant_response[index]['channelType'])
            self.assertEqual( grants_of_cbsd[0]['grantExpireTime'], grant_response[index]['grantExpireTime'])
            self.assertEqual(False, grants_of_cbsd[0]['terminated']) 
    
    # generate default config:        
        # generate default CBSDs and Grants data
        # generate defaul PPAs 
        # generate default Esc
    
    # compare two arrays
    # compare CBSD Record with (CBSD & Grant) requests & responses
    # compare PAL & PPA
    # compare Esc sensor
    
    @configurable_testcase(generate_FAD_1_default_config)
    def test_WINNF_FT_S_FAD_1(self, config_filename):
        """ This test verifies that a SAS UUT can successfully respond to a full
             activity dump request from a SAS Test Harness
			
		SAS UUT approves the request and responds,
		with correct content and format for both dump message and files 
          """
        
        config = loadConfig(config_filename)
        # Very light checking of the config file.
        self.assertEqual(len(config['registrationRequests']),
                         len(config['grants']))
        self.assertEqual(len(config['ppas']),
                         len(config['pals']))
        
        # inject FCC IDs and User IDs     
        for device in config['registrationRequests']:
          self._sas_admin.InjectFccId({
              'fccId': device['fccId'],
              'fccMaxEirp': 47
          })
          self._sas_admin.InjectUserId({'userId': device['userId']})
          
        # Pre-load conditional registration data for N3 CBSDs.
        self._sas_admin.PreloadRegistrationData(
            config['conditionalRegistrationData'])
        
        # Register N1 CBSDs.
        request = {'registrationRequest': config['registrationRequests']}
        responses = self._sas.Registration(request)['registrationResponse']
        # Check registration responses and get cbsd Id
        grants = config['grants']
        self.assertEqual(len(responses), len(config['registrationRequests']))
        for index, response in enumerate(responses):
            self.assertEqual(response['response']['responseCode'], 0)
            grants[index]['cbsdId'] = response['cbsdId']
        # send grants
        del responses
        grant_responses = self._sas.Grant({'grantRequest': grants})['grantResponse']
        # check grant response
        self.assertEqual(len(grant_responses), len(config['grants']))
        for response in grant_responses:
            self.assertEqual(response['response']['responseCode'], 0)       
        # inject N2 PPAs and PALs
        ppa_ids = []
        for index, ppa in enumerate(config['ppas']):
            self._sas_admin.InjectPalDatabaseRecord(config['pals'][index])
            ppa_ids.append(self._sas_admin.InjectZoneData({'record': ppa}))          
        # inject N3 Esc sensor
        for esc_sensor in config['esc_sensors']:
            self._sas_admin.InjectEscSensorDataRecord({'record': esc_sensor})   
        # get dump message
        # check message
        
        # for each file
            # download & add to one of the array (CBSD, PPA, Esc)
        
        # foreach array compare it with the input data
        # check that array contain all input not more with correct format and information
        # STEP 3
        self._sas_admin.TriggerFullActivityDump()
        # STEP 4
        response = self._sas.GetFullActivityDump()
        # STEP 5
        # check dump message format
        self.assertContainsRequiredFields("FullActivityDump.schema.json", response)
        
        cbsd_dump_data = []
        ppa_dump_data = []
        esc_sensor_dump_data = []
        # STEP 5
        self.assertContainsRequiredFields("FullActivityDump.schema.json", response)
        # STEP 6 AND CHECK
        self.assertGreaterEqual(3, len(response['files']))
        self.assertLessEqual(2 + len(cbsd_ids), len(response['files']))
        cbsd_dump_files = [dump_file for dump_file in response['files'] if dump_file['recordType'] ==  'cbsd']
        esc_sensor_dump_file = [dump_file for dump_file in response['files'] if dump_file['recordType'] ==  'esc_sensor']
        zone_dump_file = [dump_file for dump_file in response['files'] if dump_file['recordType'] ==  'zone']        
        # Verify the record type
        # Verify the response files with ActivityDumpFile.schema.json Object schema
        for dump_file in response['files']:
            self.assertContainsRequiredFields("ActivityDumpFile.schema.json",
                                               dump_file[0])
            if dump_file['recordType'] ==  'cbsd':
                cbsd_dump_data.append(self._sas.DownloadFile(dump_file['url'])['recordData'])      
            elif dump_file['recordType'] ==  'esc_sensor':
                esc_sensor_dump_data.append(self._sas.DownloadFile(dump_file['url'])['recordData'])
            elif dump_file['recordType'] ==  'zone':
                ppa_dump_data.append(self._sas.DownloadFile(dump_file['url'])['recordData'])
           
        self.assertEqual(len(config['registrationRequests']), len(cbsd_dump_data))
        self.assertEqual(len(config['ppas']), len(ppa_dump_data))
        self.assertEqual(len(config['esc_sensors']), len(esc_sensor_dump_data))
        
        # Verify the schema of record and  injected ppas exist in the dump files
        for index, ppa in enumerate(config['ppas']):
            ppa_record = [record for record in ppa_dump_data if record['id'].split("/")[-1] == ppa_ids[index]][0]
            
            self.assertContainsRequiredFields("zoneData.schema.json", ppa_record)
            self.assertDictEqual(ppa, ppa_record)
            
        # Verify the schema of record and  injected esc sensors exist in the dump files        
        for esc in config['esc_sensors']:
            esc_record = [record for record in ppa_dump_data if record['id'] == esc['id']][0]
            self.assertContainsRequiredFields("EscSensorRecord.schema.json", esc_record)
            self.assertDictEqual(esc, esc_record)
        # Verify the retrieved files have correct schema
        for cbsd in cbsd_dump_data:
            self.assertContainsRequiredFields("CbsdData.schema.json", record)
    
        # Verify all the previous activities on CBSDs and Grants exist in the dump files
        self.assertCbsdRecord(config['registrationRequests'], grants, grant_responses, cbsd_dump_data)