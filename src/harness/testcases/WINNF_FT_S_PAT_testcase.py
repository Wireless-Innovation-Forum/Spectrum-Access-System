#    Copyright 2024 SAS Project Authors. All Rights Reserved.
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

import logging
import math
import os
from datetime import datetime

import sas
import sas_testcase
from reference_models.propagation import wf_itm
from reference_models.propagation import wf_hybrid
from reference_models.propagation import p2108
from reference_models.antenna import antenna
from reference_models.geo import drive
from util import configurable_testcase, writeConfig, loadConfig, json_load
from reference_models.geo import utils as geoutils

# If enabled, the test harness will stop as soon as the failure threshold is reached.
# If disabled, the test harness will execute all subtests and only PASS/FAIL at the end.
EARLY_EXIT_ENABLED = False


def computePropagationDpa(request):
    """Calculates path loss in dB between a CBSD and DPA point.

    Inputs:
        request: A DPA point PAT request, a dict of:
            modelType: Propagation model type, must be '3'
            reliabilityLevel: Reliability, must be 0.5
            cbsd: CBSD, a dict of:
                latitude: Latitude (degrees)
                longitude: Longitude (degrees)
                height: Height (m)
                heightType: Height type of 'AGL' or 'AMSL'
                indoorDeployment: CBSD indoor status
            dpaPoint: A DPA point, a dict of:
                latitude: Latitude (degrees)
                longitude: Longitude (degrees)
                height: Height (m)
                heightType: Height type of 'AGL' or 'AMSL'

    Returns:
        A dict of:
            pathlossDb: Path loss in dB
    """

    # Must have modelType '3' indicating ITM for DPA Points augmented by Clutter loss and network loading factors
    model_type = request['modelType']
    if model_type != '3':
        raise ValueError('modelType is not 3')

    reliability_level = request['reliabilityLevel']
    if reliability_level != 0.5:
        raise ValueError('reliabilityLevel is not 0.5')

    result = {}

    tx = request['cbsd']
    if 'dpaPoint' not in request:
        raise ValueError('dpaPoint not in request')
    else:
        rx = request['dpaPoint'].copy()

    # convert rx height to AGL
    if rx['heightType'] == 'AMSL':
        altitude_rx = drive.terrain_driver.GetTerrainElevation(rx['latitude'], rx['longitude'])
        rx['height'] = rx['height'] - altitude_rx

    path_loss = wf_itm.CalcItmPropagationLoss(
        tx['latitude'], tx['longitude'], tx['height'],
        rx['latitude'], rx['longitude'], rx['height'],
        cbsd_indoor=tx['indoorDeployment'],
        reliability=reliability_level,
        freq_mhz=3625.,
        is_height_cbsd_amsl=(tx['heightType'] == 'AMSL'))

    clutter_loss = p2108.calc_P2108(
        tx['latitude'], tx['longitude'], tx['height'],
        rx['latitude'], rx['longitude'],
        is_height_cbsd_amsl=(tx['heightType'] == 'AMSL'))

    result['pathlossDb'] = path_loss.db_loss + clutter_loss + p2108.ACTIVITY_LOSS_FACTOR

    return result


def computePropagationAntennaModel(request):
    # dpa
    if 'dpaPoint' in request:
      return computePropagationDpa(request)

    # fss/ppa
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
        ppa_points = geoutils.GridPolygon(ppa['geometry'], arcsec)
        if len(ppa_points) == 1:
            rx['longitude']= ppa_points[0][0]
            rx['latitude'] = ppa_points[0][1]
        elif len(ppa_points) == 0:
            raise ValueError('ppa boundary contains no protection point')
        else:
            raise ValueError('ppa boundary contains more than a single protection point')

        region_val = drive.nlcd_driver.RegionNlcdVote([[rx['latitude'], rx['longitude']]])

    elif 'fss' in request:
        isfss = True
        rx = request['fss']
    else:
        raise ValueError('Neither fss nor ppa in request')

    # ITM pathloss (if receiver type is FSS) or the hybrid model pathloss (if receiver type is PPA) and corresponding antenna gains.
    # The test specification notes that the SAS UUT shall use default values for w1 and w2 in the ITM model.
    result = {}
    if isfss:
        path_loss = wf_itm.CalcItmPropagationLoss(
            tx['latitude'], tx['longitude'], tx['height'],
            rx['latitude'], rx['longitude'], rx['height'],
            cbsd_indoor= tx['indoorDeployment'],
            reliability=reliability_level,
            freq_mhz=3625.,
            is_height_cbsd_amsl=(tx['heightType'] == 'AMSL'))

        result['pathlossDb'] = path_loss.db_loss
        gain_tx_rx = antenna.GetStandardAntennaGains(
            path_loss.incidence_angles.hor_cbsd, ant_azimuth=tx['antennaAzimuth'],
            ant_beamwidth=tx['antennaBeamwidth'], ant_gain=tx['antennaGain'])
        result['txAntennaGainDbi'] = gain_tx_rx
        if 'rxAntennaGainRequired' in rx:
            hor_dirs = path_loss.incidence_angles.hor_rx
            ver_dirs = path_loss.incidence_angles.ver_rx
            gain_rx_tx = antenna.GetFssAntennaGains(
                hor_dirs, ver_dirs, rx['antennaAzimuth'],
                rx['antennaElevation'], rx['antennaGain'])
            result['rxAntennaGainDbi'] = gain_rx_tx
    else:

        path_loss = wf_hybrid.CalcHybridPropagationLoss(
            tx['latitude'], tx['longitude'], tx['height'],
            rx['latitude'], rx['longitude'], rx['height'],
            cbsd_indoor= tx['indoorDeployment'],
            reliability=-1, freq_mhz=3625., region=region_val,
            is_height_cbsd_amsl=(tx['heightType'] == 'AMSL'))
        result['pathlossDb'] = path_loss.db_loss
        gain_tx_rx = antenna.GetStandardAntennaGains(
            path_loss.incidence_angles.hor_cbsd, ant_azimuth=tx['antennaAzimuth'],
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


# The logging path
def getPatLogDir():
  pat_log_dir = os.path.join(os.path.dirname(__file__), 'output')
  if not os.path.exists(pat_log_dir):
      os.makedirs(pat_log_dir)
  return pat_log_dir


def logPat2Results(config_filename, results):
    """Saves PAT.2 config and results to ouptut file
    Inputs:
        config_filename: config file used to run PAT.2
        results: dict containing config file contents and the ref and sut results
            reliabilityLevel: Reliability, must be 0.5
            cbsd: CBSD, a dict of:
                latitude: Latitude (degrees)
                longitude: Longitude (degrees)
                height: Height (m)
                heightType: Height type of 'AGL' or 'AMSL'
                indoorDeployment: CBSD indoor status
            dpaPoint: A DPA point, a dict of:
                latitude: Latitude (degrees)
                longitude: Longitude (degrees)
                height: Height (m)
                heightType: Height type of 'AGL' or 'AMSL'
            refResult: interference (dB)
            sutResult: interference (dB)

    Returns:
        void, writes results to testcases/output file
    """

    base, tail = os.path.split(config_filename)
    timestamp = datetime.now().strftime('%Y-%m-%d %H_%M_%S')
    filename = os.path.join(getPatLogDir(), '%s_PAT.2_config=%s.csv' % (timestamp, tail))
    logging.info('Saving stats for PAT.2 config %s, to file: %s', config_filename, filename)
    with open(filename, 'w') as f:
        # CSV header.
        f.write(
            'Reliability Level,DPA Latitude,DPA Longitude,DPA Height,DPA Height Type,'
            'CBSD Latitude,CBSD Longitude,CBSD Height,CBSD Height Type,CBSD Indoor Deployment,'
            'CBSD Antenna Azimuth,CBSD Antenna Gain,CBSD Antenna Beamwidth,Ref Result (dB),SUT Result (dB)\n'
        )

        # Write results in same order as CSV header
        for result in results:
            vals = [result['reliabilityLevel']]
            for key in ['latitude', 'longitude', 'height', 'heightType']:
                vals.append(result['dpaPoint'][key])
            for key in ['latitude', 'longitude', 'height', 'heightType', 'indoorDeployment', 'antennaAzimuth',
                        'antennaGain', 'antennaBeamwidth']:
                vals.append(result['cbsd'][key])
            vals.append(result['refResult'])
            vals.append(result['sutResult'])
            line = ','.join('%3.6f' % val if not isinstance(val, str) else '%s' % val for val in vals)
            f.write(line + '\n')


class PropAndAntennaModelTestcase(sas_testcase.SasTestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
      pass

  def generate_FT_S_PAT_default_config(self, filename):
    """Generates the WinnForum configuration for PAT.1."""

    # Load Devices
    device_a = json_load(
    os.path.join('testcases', 'testdata', 'device_a.json'))

    # load FSS
    fss_data = json_load(
      os.path.join('testcases', 'testdata', 'fss_record_0.json'))
    fss_record_0 = fss_data['record']
    fss_record_0['rxAntennaGainRequired'] = True
    reliability_level = -1
    config = []
    config.append({'reliabilityLevel': reliability_level,
                   'modelType': '1',
                   'cbsd': cbsddata(device_a),
                   'fss': fssdata(fss_record_0, True)})

    # Load PPA
    ppa_record = json_load(
        os.path.join('testcases', 'testdata', 'ppa_record_3.json'))

    reliability_level = -1
    config.append({'reliabilityLevel': reliability_level,
                   'modelType': '2',
                   'cbsd': cbsddata(device_a),
                   'ppa': ppa_record['zone']['features'][0]})

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
    test_pass_threshold = 0.999 #percentage of passed test expected
    num_passed_tests = 0
    num_tests = len(config)
    max_fail_num = int ((1-test_pass_threshold) * num_tests)
    num_failed_tests = 0
    num_invalid_tests = 0
    already_failed = False

    for test_num, request in enumerate(config):
      logging.info('Running test number %d: %s', test_num, str(request))
      try:
        ref_response = computePropagationAntennaModel(request)
        logging.info('Reference response: %s', str(ref_response))
      except ValueError as e:
        logging.debug('Test # %d, Exception: %s', test_num, e)
        logging.debug('Invalid configuration: %s', request)
        num_invalid_tests += 1
        num_tests -= 1
        max_fail_num = math.floor((1-test_pass_threshold) * num_tests)
        # Do not send the request to the SAS if the reference prop model flagged it as an invalid config.
        continue

      # Send the request to the SAS.
      sas_response = self._sas_admin.QueryPropagationAndAntennaModel(request)
      logging.info('SAS response: %s', str(sas_response))

      # Check response.
      this_test_passed = False
      if 'pathlossDb' in sas_response and 'txAntennaGainDbi' in sas_response:
        this_test_passed = ((sas_response['pathlossDb'] < ref_response['pathlossDb'] + 1) and
                            (sas_response['txAntennaGainDbi'] >= (ref_response['txAntennaGainDbi'] - .2)))

        if 'fss' in request and request['fss']['rxAntennaGainRequired']:
          if 'rxAntennaGainDbi' in sas_response:
            this_test_passed = (this_test_passed and
                                (sas_response['rxAntennaGainDbi'] >= (ref_response['rxAntennaGainDbi'] - .2)))
          else:
            this_test_passed = False

      logging.info('This test passed? %s', str(this_test_passed))

      if this_test_passed:
        num_passed_tests += 1
      else:
        num_failed_tests += 1
      if num_failed_tests > max_fail_num: #test fails if number of failed tests greater than allowed
        if not already_failed:  # This value is False the first time we cross the threshold.
          logging.error('Just failed the maximum number of tests (%d).', num_failed_tests)
          already_failed = True
        if EARLY_EXIT_ENABLED:
          self.fail("Just failed the maximum number of tests (%d), quitting early." % num_failed_tests)

    # Outside the 'for' loop.
    logging.info('Passed %d out of %d tests. Need %2.6f percent pass rate.',
                 num_passed_tests, num_tests, test_pass_threshold * 100)
    self.assertTrue(num_passed_tests >= num_tests * test_pass_threshold)

  def generate_FT_S_PAT_2_default_config(self, filename):
    """Generates the WinnForum configuration for PAT.2."""

    pat2_data = json_load(
        os.path.join("testcases", "testdata", "pat2_test_data.json"))
    dpa_points = pat2_data["dpa_points"]
    cbsds = pat2_data["cbsds"]
    assert len(cbsds) == len(dpa_points)
    config = []
    for i in range(len(cbsds)):
      config.append({
            "reliabilityLevel": 0.5,
            "modelType": "3",
            "dpaPoint": dpa_points[i],
            "cbsd": cbsds[i]
        })
    writeConfig(filename, config)

  @configurable_testcase(generate_FT_S_PAT_2_default_config)
  def test_WINNF_FT_S_PAT_2(self, config_filename):
    """Query with CBSD and DPA

    The response should have the pathlossDb
    """
    config = loadConfig(config_filename)
    num_tests = len(config)
    test_pass_threshold = 0.999  # percentage of passed test expected
    num_passed_tests = 0
    max_fail_num = int((1 - test_pass_threshold) * num_tests)
    num_failed_tests = 0
    num_invalid_tests = 0
    already_failed = False

    results = []
    for test_num, request in enumerate(config):
      result = request.copy()
      logging.info('Running test number %d: %s', test_num, str(request))
      try:
        ref_response = computePropagationDpa(request)
        logging.info('Reference response: %s', str(ref_response))
        result['refResult'] = ref_response['pathlossDb']
      except ValueError as e:
        logging.debug('Test # %d, Exception: %s', test_num, e)
        logging.debug('Invalid configuration: %s', request)
        num_invalid_tests += 1
        num_tests -= 1
        max_fail_num = math.floor((1 - test_pass_threshold) * num_tests)
        result['refResult'] = None
        result['sutResult'] = None
        # Do not send the request to the SAS if the reference prop model flagged it as an invalid config.
        continue

      # Send the request to the SAS.
      sas_response = self._sas_admin.QueryPropagationAndAntennaModel(request)
      logging.info('SAS response: %s', str(sas_response))

      # Check response.
      this_test_passed = False
      if 'pathlossDb' in sas_response:
        result['sutResult'] = sas_response['pathlossDb']
        this_test_passed = sas_response['pathlossDb'] < ref_response['pathlossDb'] + 1
      else:
        result['sutResult'] = None

      logging.info('This test passed? %s', str(this_test_passed))
      results.append(result)

      if this_test_passed:
        num_passed_tests += 1
      else:
        num_failed_tests += 1
      if num_failed_tests > max_fail_num:  # test fails if number of failed tests greater than allowed
        if not already_failed:  # This value is False the first time we cross the threshold.
          logging.error('Just failed the maximum number of tests (%d).', num_failed_tests)
          already_failed = True
        if EARLY_EXIT_ENABLED:
          logPat2Results(config_filename, results)
          self.fail("Just failed the maximum number of tests (%d), quitting early." % num_failed_tests)

    logPat2Results(config_filename, results)

    # Outside the 'for' loop.
    logging.info('Passed %d out of %d tests. Need %2.6f percent pass rate.',
                 num_passed_tests, num_tests, test_pass_threshold * 100)
    self.assertTrue(num_passed_tests >= num_tests * test_pass_threshold)
