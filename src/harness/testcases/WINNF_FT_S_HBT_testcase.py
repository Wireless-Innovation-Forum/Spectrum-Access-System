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
import time


class HeartbeatTestcase(sas_testcase.SasTestCase):
  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @winnforum_testcase
  def test_WINNF_FT_S_HBT_9(self):
    """ Array request, of three cbsds,SAS terminates the Grant for the one
    that impacts incumbent activity.

    successful heartbeat for the grants of two cbsds that don't impact
     the incumbent and failed with responseCode 500 for the third one.
    """
    # STEP 1
    # register three devices
    # load  CBSD data
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json'))) 
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    request = {'registrationRequest': [device_a, device_c, device_e]}
    response = self._sas.Registration(request)['registrationResponse']
    cbsd_ids = []
    for resp in response:
      self.assertEqual(resp['response']['responseCode'], 0)
      cbsd_ids.append(resp['cbsdId'])
    del request, response

    # load and set Grants data
    grant_a = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_a['cbsdId'] = cbsd_ids[0]
    grant_c = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_c['cbsdId'] = cbsd_ids[1]
    grant_e = json.load(
        open(os.path.join('testcases', 'testdata', 'grant_0.json')))
    grant_e['cbsdId'] = cbsd_ids[2]
    grant_e['operationParam']['operationFrequencyRange']\
                             ['lowFrequency'] = 3650000000
    grant_e['operationParam']['operationFrequencyRange']\
                             ['highFrequency'] = 3700000000
    request = {'grantRequest': [grant_a, grant_c, grant_e]}
    # send grant request
    response = self._sas.Grant(request)['grantResponse']
    grant_ids = []
    grant_expire_times = []
    for response_num, resp in enumerate(response):
      grant_ids.append(resp['grantId'])
      grant_expire_times.append(
          datetime.strptime(resp['grantExpireTime'], '%Y-%m-%dT%H:%M:%SZ'))
    del request, response
    # First Heartbeat
    request = []
    for cbsd_id, grant_id in zip(cbsd_ids, grant_ids):
        request.append({
            'cbsdId': cbsd_id,
            'grantId': grant_id,
            'operationState': 'GRANTED'
        })
    
    response = self._sas.Heartbeat({'heartbeatRequest': request})['heartbeatResponse']
    
    del request, response
    # STEP 2
    # load and inject FSS data with Overlapping Frequency of CBSD
    fss_e = json.load(
        open(os.path.join('testcases', 'testdata', 'fss_record.json')))
    self._sas_admin.InjectFss({'record': fss_e})   
    # load and inject GWPZ data with Overlapping Frequency of CBSD 
    gwpz_e = json.load(
        open(os.path.join('testcases', 'testdata', 'gwpz_record.json')))  
    self._sas_admin.InjectWisp(gwpz_e)      
    # STEP 3
    # Trigger daily activities and wait for it to get it complete
    self.TriggerDailyActivitiesImmediatelyAndWaitUntilComplete()
    # Send Heartbeat after triggering the IAP
    request = []
    for cbsd_id, grant_id in\
     zip(cbsd_ids, grant_ids):
        request.append({
            'cbsdId': cbsd_id,
            'grantId': grant_id,
            'operationState': 'GRANTED'
        })
    response = self._sas.Heartbeat({'heartbeatRequest': request})['heartbeatResponse']
    del request
    # CHECK
    # Check first two CBSDs with a successful HB response
    for response_num, resp in enumerate(response[:2]):
        self.assertEqual(resp['cbsdId'], cbsd_ids[response_num])
        self.assertEqual(resp['grantId'], grant_ids[response_num])
        self.assertEqual(resp['response']['responseCode'], 0)
        transmit_expire_time = datetime.strptime(resp['transmitExpireTime'],\
                                                 '%Y-%m-%dT%H:%M:%SZ')
        self.assertLessEqual((transmit_expire_time - \
                              datetime.utcnow()).total_seconds(), 240)
        self.assertLessEqual(transmit_expire_time, grant_expire_times[response_num])
    # Check the third  CBSD with unsuccessful HB response of code 500
    self.assertEqual(response[2]['cbsdId'], cbsd_ids[2])
    self.assertEqual(response[2]['grantId'], grant_ids[2])
    self.assertEqual(response[2]['response']['responseCode'], 500)
    self.assertLessEqual(datetime.strptime(
        response[2]['transmitExpireTime'],'%Y-%m-%dT%H:%M:%SZ'), datetime.utcnow())