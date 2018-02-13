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

from datetime import datetime
import json
import logging
import os
import sas
import sas_testcase

from util import winnforum_testcase, getRandomLatLongInPolygon, makePpaAndPalRecordsConsistent, QueryPropagationAntennaModel

def cbsddata(device):
    installationParam = device['installationParam']
    if 'antennaAzimuth' not in installationParam:
        installationParam['antennaAzimuth'] = None
        
    cbsd = {'latitude': installationParam['latitude'],
             'longitude': installationParam['longitude'],
              'height': installationParam['height'],
              'heightType': installationParam['heightType'],
              'indoorDeployment': installationParam['indoorDeployment'],
              'antennaAzimuth': installationParam['antennaAzimuth'],
              'antennaGain': installationParam['antennaGain'],
              'antennaBeamwidth': installationParam['antennaBeamwidth'],
              'cbsdCategory': device['cbsdCategory']}
    return cbsd

def fssdata(fss_record, rxAntennaGainRequired=None):
    deploymentParam = fss_record['deploymentParam'][0]
    installationParam = deploymentParam['installationParam']
    if 'antennaAzimuth' not in installationParam:
        installationParam['antennaAzimuth'] = ''
        
    fss = {'latitude': installationParam['latitude'],
             'longitude': installationParam['longitude'],
              'height': installationParam['height'],
              'antennaAzimuth': installationParam['antennaAzimuth'],
              'antennaGain': installationParam['antennaGain'],
              'antennaDowntilt': installationParam['antennaDowntilt']}
    if rxAntennaGainRequired is not None:
        fss['rxAntennaGainRequired'] = rxAntennaGainRequired
    return fss


class PropAndAntennaModelTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    #self._sas_admin.Reset()

  def tearDown(self):
      pass

  def generate_FT_S_PAT_default_config(self, testcasedir):

# Load Devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
   
    # load FSS
    fss_record_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'fss_record_0.json')))
    fss_record_0['rxAntennaGainRequired'] = True
    reliabilityLevel = -1
    with open(os.path.join(testcasedir, 'default_fss.json'), "w") as outfile:
        json.dump( {'reliabilityLevel': reliabilityLevel, 'cbsd': cbsddata(device_a),'fss': fssdata(fss_record_0, True)}, outfile, indent=4, separators=(',', ': '))
       
    # Load PPA
    ppa_record = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_3.json')))
     
    reliabilityLevel = -1
    with open(os.path.join(testcasedir, 'default_ppa.json'), "w") as outfile:
        json.dump({'reliabilityLevel': reliabilityLevel, 'cbsd': cbsddata(device_a),'ppa': ppa_record['zone']['features'][0]}, outfile, indent=4, separators=(',', ': '))
      
  @winnforum_testcase
  def test_WINNF_FT_S_PAT_1(self):
    """Query with CBSD and FSS/PPA
   
    If (rxAntennaGainRequired = True)
    The response should have the pathlossDb, txAntennaGainDbi and rxAntennaGainDbi 
 
    If (rxAntennaGainRequired = False or omitted)
    The response should have the pathlossDb, txAntennaGainDbi
    """
 
    from os import listdir
    from os.path import isfile, join
    testcasedir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'testdata', 'pat_testcases')
    print os.path.exists(testcasedir)
    if os.path.exists(testcasedir):
        testfiles = [f for f in listdir(testcasedir) if isfile(join(testcasedir, f))]
        testfiles = [f for f in testfiles if f.endswith('.json')]
        if not testfiles:
            testcasedir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'testdata', 'config', 'test_WINNF_FT_S_PAT_1')
            self.generate_FT_S_PAT_default_config(testcasedir)
            testfiles = ['default_ppa.json', 'default_fss.json']
    else:
        testcasedir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'testdata', 'config', 'test_WINNF_FT_S_PAT_1')
        if not os.path.exists(testcasedir):
            os.makedirs(testcasedir)
        
        testfiles = [f for f in listdir(testcasedir) if isfile(join(testcasedir, f))]
        testfiles = [f for f in testfiles if f.endswith('.json')]
        if not testfiles:
            self.generate_FT_S_PAT_default_config(testcasedir)
            testfiles = ['default_ppa.json', 'default_fss.json']
        
    for testfile in testfiles:
        if testfile.endswith('.json'):
                    with open(os.path.join(testcasedir, testfile), 'r') as myfile:
                        testjson=myfile.read().replace('\n', '')
                        refResponse = QueryPropagationAntennaModel(testjson)

                        try:
                            sasResponse = self._sas_admin.QueryPropagationAndAntennaModel(testjson)
                            # Check response
                            if 'pathlossDb' in refResponse:
                                self.assertTrue(sasResponse['pathlossDb'] < refResponse['pathlossDb'] + 1)
                                self.assertTrue(sasResponse['txAntennaGainDbi'] < (refResponse['txAntennaGainDbi'] + .2))
                            if 'rxAntennaGainDbi' in refResponse:
                                self.assertTrue(sasResponse['rxAntennaGainDbi'] < (refResponse['rxAntennaGainDbi'] + .2))
                        except AssertionError as e:
                            # Allow HTTP status 404
                            self.assertEqual(e.args[0], 404)
