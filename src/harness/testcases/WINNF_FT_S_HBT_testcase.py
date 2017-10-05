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
from datetime import datetime, timedelta
import hashlib

class HeartbeatTestcase(sas_testcase.SasTestCase):
  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  def getHeartBeatRequest(self,cbsd_ids, grant_ids, status):     
    heartbeat_request = []
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
        heartbeat_request.append({
            'cbsdId': cbsd_id,
            'grantId': grant_id,
            'operationState': status
        })
    return {'heartbeatRequest': heartbeat_request}

  def sendAndAssertSuccessfulHeartBeat(self, cbsd_ids, grant_ids, status):    
    request =  self.getHeartBeatRequest(cbsd_ids, grant_ids, status)
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    # check Heartbeat response 
    self.assertEqual(len(response), 3)
    for response_num, resp in enumerate(response):
        self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
        self.assertEqual(resp['grantId'], grant_ids[response_num])
        self.assertEqual(resp['response']['responseCode'], 0)
        grant_expire_time_1 = datetime.strptime(resp['grantExpireTime'],'%Y-%m-%dT%H:%M:%SZ')
        transmit_expire_time_1 = datetime.strptime(resp['transmitExpireTime'],'%Y-%m-%dT%H:%M:%SZ')
        self.assertLessEqual((transmit_expire_time_1 - datetime.utcnow()).total_seconds(), 240)
        self.assertLessEqual(transmit_expire_time_1, grant_expire_time_1)
    del request
    return response
   
  @winnforum_testcase
  def test_WINNF_FT_S_HBT_9(self):
    """
    Purpose : Array request, of three cbsds,SAS terminates the Grant for the one
     with incumbent present (in Granted or Authorized state)
     in response to its Heartbeat Request immediately after CBSD 
     moves into Granted State or following a previous Heartbeat Response

    Result:SAS responds with a basic Heartbeat Response in the form of one 3-element Array as follows:
     - SAS response includes the cbsdId, and grantId that match the request from each CBSD in the array.
     - The responseCode in Response Object shall be 0 for the first two CBSDs concluding a successful operation.
      transmitExpireTime is set to a valid UTC time in the future for the first two CBSDs. It shall be not later than 240 seconds in the future and not later than the grantExpireTime.
     - The responseCode in Response Object for the third CBSD set to 500, concluding a failed operation due to termination of the Grant. Other potential errors in the previous Heartbeat Request are ignored.
      transmitExpireTime set to a value equal or less than the transmitExpireTime in the previous successful Heartbeat response. If this is the first Heartbeat response, any value for transmitExpireTime is acceptable, for the third CBSD

    TS verrsion : BASED_ON_V0.0.0-r5.0 (15 September 2017)

    Test version : 0.1
    """
    # STEP 1
    # register three devices 
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_d = json.load(
        open(os.path.join('testcases', 'testdata', 'device_d.json')))
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    devices = [device_d, device_e, device_c]
    for device in devices:
        # inject FCC IDs
        self._sas_admin.InjectFccId({'fccId': device['fccId']})
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)['registrationResponse']
    cbsd_ids = []
    for resp in response:
        cbsd_ids.append(resp['cbsdId'])
    cbsd_ids.sort(key=lambda cbsdId: cbsdId)
    del request, response    
    # create and send grant requests
    grant_c = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_c['cbsdId'] = cbsd_ids[0]
    grant_d = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_d['cbsdId'] = cbsd_ids[1]
    grant_d['operationParam']['operationFrequencyRange']['lowFrequency'] = 3560
    grant_d['operationParam']['operationFrequencyRange']['highFrequency'] = 3570
    grant_e = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_e['cbsdId'] = cbsd_ids[2]
    grant_e['operationParam']['operationFrequencyRange']['lowFrequency'] = 3560
    grant_e['operationParam']['operationFrequencyRange']['highFrequency'] = 3570
    request = {'grantRequest': [grant_c, grant_d, grant_e]}
    # send grant request and get response
    response = self._sas.Grant(request)['grantResponse']
    self.assertEqual(len(response), 3)       
    grant_ids = (response[0]['grantId'], response[1]['grantId'], response[2]['grantId'])
    del request, response
    # First Heartbeat
    response = self.sendAndAssertSuccessfulHeartBeat(cbsd_ids, grant_ids, "GRANTED")
    del response
    # STEP 2
    # load and inject FSS data
    fss_c = json.load(
        open(os.path.join('testcases', 'testdata', 'fss_record_c.json')))
    # Inject Incumbent Activity with Overlapping Frequency of CBSD
    fss_c['deploymentParam']['operationParam']['operationFrequencyRange']['lowFrequency'] = \
                             grant_c['operationParam']['operationFrequencyRange']['lowFrequency']
    fss_c['deploymentParam']['operationParam']['operationFrequencyRange']['highFrequency'] = \
                             grant_c['operationParam']['operationFrequencyRange']['highFrequency']
    
    self._sas_admin.InjectFss({'record': fss_c})   
    # load and inject GWPZ data
    gwpz_c = json.load(
        open(os.path.join('testcases', 'testdata', 'gwpz_record_c.json')))
    # Inject Incumbent Activity with Overlapping Frequency of CBSD
    gwpz_c['deploymentParam']['operationParam']['operationFrequencyRange']['lowFrequency'] = \
                             grant_c['operationParam']['operationFrequencyRange']['lowFrequency']
    gwpz_c['deploymentParam']['operationParam']['operationFrequencyRange']['highFrequency'] = \
                             grant_c['operationParam']['operationFrequencyRange']['highFrequency']
    
    self._sas_admin.InjectWisp({'record': gwpz_c})      
    # Send Heartbeat before trigger the IAP to extent grants' expiration time
    heartbeat_response_1 = self.sendAndAssertSuccessfulHeartBeat(cbsd_ids, grant_ids, 'AUTHORIZED')
     
    # STEP 3
    # Trigger daily activities and wait for it to get it complete
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()
    # Send Heartbeat after triggering the IAP
    request =  self.getHeartBeatRequest(cbsd_ids, grant_ids, 'AUTHORIZED')
    response = self._sas.Heartbeat(request)['heartbeatResponse']
    # CHECK
    for response_num, resp in enumerate(response):
        self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
        self.assertEqual(resp['grantId'], grant_ids[response_num])
        grant_expire_time_2 = datetime.strptime(resp['grantExpireTime'],'%Y-%m-%dT%H:%M:%SZ')
        transmit_expire_time_2 = datetime.strptime(resp['transmitExpireTime'],'%Y-%m-%dT%H:%M:%SZ')
        self.assertLessEqual((transmit_expire_time_2 - datetime.utcnow()).total_seconds(), 240)
        self.assertLessEqual(transmit_expire_time_2, grant_expire_time_2)
        if cbsd_ids[response_num] == cbsd_ids[2]:
            self.assertEqual(resp['response']['responseCode'], 500)
            transmit_expire_time_1 = datetime.strptime(heartbeat_response_1[response_num]\
                                                       ['transmitExpireTime'],'%Y-%m-%dT%H:%M:%SZ')
            self.assertLessEqual(transmit_expire_time_2, transmit_expire_time_1)
        else:
            self.assertEqual(resp['response']['responseCode'], 0)
