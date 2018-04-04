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

# =============================================================================
# Test Aggregate Interference calculation for GWPZ, PPA, FSS Co-Channel, 
# FSS Blocking and ESC Sensor incumbent types.
# Expected result is dictionary containing aggregate interference
# value at a protection constraint. 
# =============================================================================
import json
import os
from pykml import parser
from collections import namedtuple
import aggregate_interference
import time
from multiprocessing import Pool
import multiprocessing
from reference_models.interference import interference as interf

# Number of parallel processes 
NUM_OF_PROCESS = 30


if __name__ == '__main__':

  # Data directory
  current_dir = os.getcwd()
  _BASE_DATA_DIR = os.path.join(current_dir, 'test_data')

  # Populate a list of CBSD registration requests
  cbsd_filename = ['cbsd_0.json',
                   'cbsd_1.json', 'cbsd_2.json', 'cbsd_3.json', 
                   'cbsd_4.json', 'cbsd_5.json', 'cbsd_6.json',
                   'cbsd_7.json', 'cbsd_8.json', 'cbsd_9.json',
                   'cbsd_10.json', 'cbsd_11.json', 'cbsd_12.json',
                   'cbsd_13.json', 'cbsd_14.json', 'cbsd_15.json',
                   'cbsd_16.json', 'cbsd_17.json', 'cbsd_18.json',
                   'cbsd_19.json', 'cbsd_20.json', 'cbsd_21.json',
                   'cbsd_22.json', 'cbsd_23.json'
                   ]
  cbsd_list = []
  for cbsd_file in cbsd_filename:
    cbsd_record = json.load(open(os.path.join(_BASE_DATA_DIR, cbsd_file)))
    cbsd_list.append(cbsd_record)
  
  fss_filename = ['fss_0.json', 'fss_1.json']
   
  fss_list = []
  for fss_file in fss_filename:
    # load and inject FSS data with Overlapping Frequency of CBSD
    fss_record = json.load(open(os.path.join(_BASE_DATA_DIR, fss_file)))
    fss_list.append(fss_record)

  esc_filename = ['esc_0.json']
  
  esc_list = []
  for esc_file in esc_filename:
    # load and inject ESC data with Overlapping Frequency of CBSD
    esc_record = json.load(
      open(os.path.join(_BASE_DATA_DIR, esc_file)))
    esc_list.append(esc_record)
  
  gwpz_filename = ['gwpz_0.json', 'gwpz_1.json']

  gwpz_list = []
  
  for gwpz_file in gwpz_filename:
    # load and inject GWPZ data with Overlapping Frequency of CBSD
    gwpz_record = json.load(
      open(os.path.join(_BASE_DATA_DIR, gwpz_file)))
    gwpz_list.append(gwpz_record)
  
  ppa_filename = ['ppa_0.json', 'ppa_1.json', 'ppa_2.json', 'ppa_3.json']

  ppa_list = []
  
  for ppa_file in ppa_filename:
    # load and inject PPA data with Overlapping Frequency of CBSD
    ppa_record = json.load(open(os.path.join(_BASE_DATA_DIR, ppa_file)))
    ppa_list.append(ppa_record)

  # load and inject PAL to get the frequency for PPA calculation
  pal_filename = ['pal_0.json', 'pal_1.json', 'pal_2.json', 'pal_3.json']
  ppa_filename = []
  pal_list = []
  for pal_file in pal_filename:
      pal_record = json.load(open(os.path.join(_BASE_DATA_DIR, pal_file)))
      pal_list.append(pal_record)
  
  # Determine aggregate interference caused by the grants in the neighborhood
  start_time = time.time()

  for fss_record in fss_list:
    # Get the frequency range of the FSS
    fss_freq_range = fss_record['record']['deploymentParam'][0]\
        ['operationParam']['operationFrequencyRange']
    fss_low_freq = fss_freq_range['lowFrequency']
    fss_high_freq = fss_freq_range['highFrequency']

    # Get FSS T&C Flag value
    fss_ttc_flag = fss_record['ttc']
  
    # FSS Passband is between 3600 and 4200
    if (fss_low_freq >= interf.FSS_LOW_FREQ_HZ and 
            fss_low_freq < interf.CBRS_HIGH_FREQ_HZ):
      fss_cochannel_aggr_interference = aggregate_interference.\
        calculateAggregateInterferenceForFssCochannel(fss_record, cbsd_list)
      print('Aggregate Interference (mW) output at FSS co-channel: ' + 
                    str(fss_cochannel_aggr_interference))
      fss_blocking_aggr_interference = aggregate_interference.\
        calculateAggregateInterferenceForFssBlocking(fss_record, cbsd_list)
      print('\nAggregate Interference (mW) output at FSS blocking: \n' + 
                    str(fss_blocking_aggr_interference))
    # FSS Passband is between 3700 and 4200 and TT&C flag is set to TRUE
    elif (fss_low_freq >= interf.FSS_TTC_LOW_FREQ_HZ and 
            fss_high_freq <= interf.FSS_TTC_HIGH_FREQ_HZ and
            fss_ttc_flag is True):
      fss_blocking_aggr_interference = aggregate_interference.\
        calculateAggregateInterferenceForFssBlocking(fss_record, cbsd_list)
      print('\nAggregate Interference (mW) output at FSS blocking: \n' + 
                    str(fss_blocking_aggr_interference))

  for esc_record in esc_list:
    esc_aggr_interference = aggregate_interference.\
      calculateAggregateInterferenceForEsc(esc_record, cbsd_list)
    print('\nAggregate Interference (mW) output at ESC: \n' + 
                    str(esc_aggr_interference))
  for gwpz_record in gwpz_list:
    pool = Pool(processes=min(multiprocessing.cpu_count(), NUM_OF_PROCESS))
    gwpz_aggr_interference = aggregate_interference.\
      calculateAggregateInterferenceForGwpz(gwpz_record, cbsd_list, pool)
    print('\nAggregate Interference (mW) output at GWPZ: \n' + str(gwpz_aggr_interference) )

  for ppa_record in ppa_list:
    pool = Pool(processes=min(multiprocessing.cpu_count(), NUM_OF_PROCESS))
    ppa_aggr_interference = aggregate_interference.\
      calculateAggregateInterferenceForPpa(ppa_record, pal_list, cbsd_list, pool)
    print('\nAggregate Interference (mW) output at PPA: \n' + str(ppa_aggr_interference))

  end_time = time.time()
  print('\nComputation time: \n' + str(end_time - start_time))
