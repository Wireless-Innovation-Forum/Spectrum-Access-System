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
import logging
import math
import os
import sas
import sas_testcase
from reference_models.propagation import wf_itm
from reference_models.propagation import wf_hybrid
from reference_models.antenna import antenna
from reference_models.ppa import ppa
nlcd_driver = ppa.nlcd_driver
from util import winnforum_testcase, configurable_testcase, writeConfig, loadConfig
from reference_models.geo import utils as GeoUtils

def computePropagationAntennaModel(request):
    reliability_level = request['reliabilityLevel']
    if reliability_level not in [-1, 0.05, 0.95]:
        raise ValueError('reliability_level not in [-1, 0.05, 0.95]')

    tx = request['cbsd']
    if ('fss' in request) and ('ppa' in request):
        raise ValueError('fss and ppa in request')
    elif 'ppa' in request:
        rx ={}
        rx['height'] = 1.5
        isfss = False
        coordinates = []
        ppa = request['ppa']

        arcsec = 1
        ppa_points = GeoUtils.GridPolygon(ppa['geometry'], arcsec)
        if len(ppa_points) == 1:
            rx['longitude']= ppa_points[0][0]
            rx['latitude'] = ppa_points[0][1]
        elif len(ppa_points) == 0:
            raise ValueError('ppa boundary contains no protection point')
        else:
            raise ValueError('ppa boundary contains more than a single protection point')
        
        region_val = nlcd_driver.RegionNlcdVote([[rx['latitude'], rx['longitude']]])

    elif 'fss' in request:
        isfss = True
        rx = request['fss']
    else:
        raise ValueError('Neither fss nor ppa in request')
    
    # ITM pathloss (if receiver type is FSS) or the hybrid model pathloss (if receiver type is PPA) and corresponding antenna gains.
    # The test specification notes that the SAS UUT shall use default values for w1 and w2 in the ITM model.
    result = {}
    if isfss:
        path_loss = wf_itm.CalcItmPropagationLoss(tx['latitude'], tx['longitude'], tx['height'], 
                                                   rx['latitude'], rx['longitude'], rx['height'],
                                                   cbsd_indoor= tx['indoorDeployment'],
                                                   reliability=reliability_level, freq_mhz=3625.)
        result['pathlossDb'] = path_loss.db_loss
        gain_tx_rx = antenna.GetStandardAntennaGains(path_loss.incidence_angles.hor_cbsd, ant_azimuth=tx['antennaAzimuth'], 
                                                     ant_beamwidth=tx['antennaBeamwidth'], ant_gain=tx['antennaGain'])
        result['txAntennaGainDbi'] = gain_tx_rx 
        if 'rxAntennaGainRequired' in rx:
            hor_dirs = path_loss.incidence_angles.hor_rx
            ver_dirs = path_loss.incidence_angles.ver_rx
            gain_rx_tx = antenna.GetFssAntennaGains(hor_dirs, ver_dirs, rx['antennaAzimuth'], 
                                                    rx['antennaElevation'], rx['antennaGain'])
            result['rxAntennaGainDbi'] = gain_rx_tx           
    else:
        
        path_loss = wf_hybrid.CalcHybridPropagationLoss(tx['latitude'], tx['longitude'], tx['height'], 
                                                        rx['latitude'], rx['longitude'], rx['height'],
                                                        cbsd_indoor= tx['indoorDeployment'],                                                        
                                                        reliability=-1, freq_mhz=3625., region=region_val)
        result['pathlossDb'] = path_loss.db_loss
        gain_tx_rx = antenna.GetStandardAntennaGains(path_loss.incidence_angles.hor_cbsd, ant_azimuth=tx['antennaAzimuth'], 
                                                     ant_beamwidth=tx['antennaBeamwidth'], ant_gain=tx['antennaGain'])
        result['txAntennaGainDbi'] = gain_tx_rx 
        
    
    return result
   
def cbsddata(device):
    installationParam = device['installationParam']
    if 'antennaAzimuth' not in installationParam:
        installationParam['antennaAzimuth'] = None
    if 'antennaBeamwidth' not in installationParam:
        installationParam['antennaBeamwidth'] = None
    if 'antennaGain' not in installationParam:
        installationParam['antennaGain'] = 0
                
    cbsd = {'latitude': installationParam['latitude'],
             'longitude': installationParam['longitude'],
              'height': installationParam['height'],
              'heightType': installationParam['heightType'],
              'indoorDeployment': installationParam['indoorDeployment'],
              'antennaAzimuth': installationParam['antennaAzimuth'],
              'antennaGain': installationParam['antennaGain'],
              'antennaBeamwidth': installationParam['antennaBeamwidth']}
    return cbsd

def fssdata(fss_record, rx_antenna_gain_required=None):
    deploymentParam = fss_record['deploymentParam'][0]
    installationParam = deploymentParam['installationParam']
    if 'antennaAzimuth' not in installationParam:
        installationParam['antennaAzimuth'] = None
        
    fss = {'latitude': installationParam['latitude'],
             'longitude': installationParam['longitude'],
              'height': installationParam['height'],
              'antennaAzimuth': installationParam['antennaAzimuth'],
              'antennaGain': installationParam['antennaGain'],
              'antennaElevation': -installationParam['antennaDowntilt']}
    if rx_antenna_gain_required is not None:
        fss['rxAntennaGainRequired'] = rx_antenna_gain_required
    else:
        fss['rxAntennaGainRequired'] = False
    return fss


class PropAndAntennaModelTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
      pass

  def generate_FT_S_PAT_default_config(self, filename):
    """Generates the WinnForum configuration for PAT.1."""
    
    # Load Devices
    device_a = json.load(
    open(os.path.join('testcases', 'testdata', 'device_a.json')))

    # load FSS
    fss_record_0 = json.load(
      open(os.path.join('testcases', 'testdata', 'fss_record_0.json')))
    fss_record_0['rxAntennaGainRequired'] = True
    reliability_level = -1
    config = []
    config.append({'reliabilityLevel': reliability_level, 'cbsd': cbsddata(device_a),'fss': fssdata(fss_record_0, True)})

    # Load PPA
    ppa_record = json.load(
        open(os.path.join('testcases', 'testdata', 'ppa_record_3.json')))
     
    reliability_level = -1
    config.append({'reliabilityLevel': reliability_level, 'cbsd': cbsddata(device_a),'ppa': ppa_record['zone']['features'][0]})

    writeConfig(filename, config)
      
  @configurable_testcase(generate_FT_S_PAT_default_config)
  def test_WINNF_FT_S_PAT_1(self, config_filename):
    """Query with CBSD and FSS/PPA
   
    If (rxAntennaGainRequired = True)
    The response should have the pathlossDb, txAntennaGainDbi and rxAntennaGainDbi 
 
    If (rxAntennaGainRequired = False or omitted)
    The response should have the pathlossDb, txAntennaGainDbi
    """
    
    config = loadConfig(config_filename)
    num_tests = len(config)
    test_pass_threshold = 0.999 #percentage of passed test expected
    num_passed_tests = 0
    num_tests = len(config)
    max_fail_num = int ((1-test_pass_threshold) * num_tests)
    num_failed_tests = 0
    num_invalid_tests = 0

    for test_num, request in enumerate(config):
       try:
           ref_response = computePropagationAntennaModel(request)
       except ValueError as e:
           logging.debug('Test # %d, Exception: %s', test_num, e)
           logging.debug('Configuration: %s', request)
           num_invalid_tests += 1
           num_tests -= 1
           max_fail_num = math.floor((1-test_pass_threshold) * num_tests)
           continue
       
       # don't send a response to sas if invalid
       sas_response = self._sas_admin.QueryPropagationAndAntennaModel(request)


       # Check response
       this_test = False
       if 'pathlossDb' in sas_response and 'txAntennaGainDbi' in sas_response:
           this_test = (sas_response['pathlossDb'] < ref_response['pathlossDb'] + 1) and (sas_response['txAntennaGainDbi'] < (ref_response['txAntennaGainDbi'] + .2))

           if 'fss' in request and request['fss']['rxAntennaGainRequired']:
               if 'rxAntennaGainDbi' in sas_response:
                   this_test = this_test and (sas_response['rxAntennaGainDbi'] < (ref_response['rxAntennaGainDbi'] + .2))
               else:
                   this_test = False
       if this_test:
           num_passed_tests += 1
       else:
           num_failed_tests += 1
       if num_failed_tests > max_fail_num: #test fails if number of failed tests greater than allowed
           break
       
    self.assertTrue(num_passed_tests >= num_tests * test_pass_threshold)
    
