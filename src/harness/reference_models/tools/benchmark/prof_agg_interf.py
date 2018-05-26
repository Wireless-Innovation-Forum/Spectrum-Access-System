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

"""Runs the aggregate interference code under profiler.

This script creates several profile output:
  profile-<idx>.out
where idx:
  0 is the main process
  1-N: for each workers

Note: script derived from the aggregate_interference_example.py
"""

import json
import os
import time
import cProfile

from reference_models.common import data
from reference_models.common import mpool
from reference_models.interference import interference as interf
from reference_models.interference import aggregate_interference
from reference_models.tools import profpool

# Number of parallel processes
NUM_PROCESS = 4

def CvtToList(data):
  """Convert interf to a sorted list suitable for comparison."""
  out_dict = {}
  for k0, v0 in data.items():
    for k1, v1 in v0.items():
      out_dict[(k0, k1)] = v1

  out_list = list(out_dict.items())
  out_list.sort()
  return out_list

if __name__ == '__main__':

  #=======================================
  # Decrease resolution of GWPZ/PPA for reducing time
  aggregate_interference.GWPZ_GRID_RES_ARCSEC = 10
  aggregate_interference.PPA_GRID_RES_ARCSEC = 10

  #=======================================
  # Configure the multiprocess pool with profiler enabled
  pool = profpool.PoolWithProfiler(NUM_PROCESS)
  mpool.Configure(pool=pool)
  prof0 = cProfile.Profile()

  #=======================================
  # Data directory
  _BASE_DATA_DIR = os.path.join(os.path.dirname(__file__),
                                '../../interference/test_data')

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

  # Populate FSS
  fss_filename = ['fss_0.json', 'fss_1.json']
  fss_list = []
  for fss_file in fss_filename:
    fss_record = json.load(open(os.path.join(_BASE_DATA_DIR, fss_file)))
    fss_list.append(fss_record)

  # Populate ESC
  esc_filename = ['esc_0.json']
  esc_list = []
  for esc_file in esc_filename:
    esc_record = json.load(
      open(os.path.join(_BASE_DATA_DIR, esc_file)))
    esc_list.append(esc_record)

  # Populate GWPZ
  gwpz_filename = ['gwpz_0.json', 'gwpz_1.json']
  gwpz_list = []
  for gwpz_file in gwpz_filename:
    gwpz_record = json.load(
        open(os.path.join(_BASE_DATA_DIR, gwpz_file)))
    gwpz_list.append(gwpz_record)

  # Populate PPA/PAL
  ppa_filename = ['ppa_0.json', 'ppa_1.json', 'ppa_2.json', 'ppa_3.json']
  ppa_list = []
  for ppa_file in ppa_filename:
    # load and inject PPA data with Overlapping Frequency of CBSD
    ppa_record = json.load(open(os.path.join(_BASE_DATA_DIR, ppa_file)))
    ppa_list.append(ppa_record)

  pal_filename = ['pal_0.json', 'pal_1.json', 'pal_2.json', 'pal_3.json']
  ppa_filename = []
  pal_list = []
  for pal_file in pal_filename:
    pal_record = json.load(open(os.path.join(_BASE_DATA_DIR, pal_file)))
    pal_list.append(pal_record)

  #=======================================
  # Determine aggregate interference caused by the grants in the neighborhood
  start_time = time.time()
  prof0.enable()

  #--- FSS ---
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
        calculateAggregateInterferenceForFssCochannel(
            fss_record, data.getAllGrantInfoFromCbsdDataDump(cbsd_list))
      print('Aggregate Interference (mW) output at FSS co-channel: %s\n'
            % (CvtToList(fss_cochannel_aggr_interference)))
      fss_blocking_aggr_interference = aggregate_interference.\
        calculateAggregateInterferenceForFssBlocking(
            fss_record, data.getAllGrantInfoFromCbsdDataDump(cbsd_list))
      print('\nAggregate Interference (mW) output at FSS blocking: %s\n'
            % (CvtToList(fss_blocking_aggr_interference)))

    # FSS Passband is between 3700 and 4200 and TT&C flag is set to TRUE
    elif (fss_low_freq >= interf.FSS_TTC_LOW_FREQ_HZ and
          fss_high_freq <= interf.FSS_TTC_HIGH_FREQ_HZ and
          fss_ttc_flag is True):
      fss_blocking_aggr_interference = aggregate_interference.\
        calculateAggregateInterferenceForFssBlocking(
            fss_record, data.getAllGrantInfoFromCbsdDataDump(cbsd_list))
      print('\nAggregate Interference (mW) output at FSS blocking: %s\n'
            % (CvtToList(fss_blocking_aggr_interference)))

  #--- ESC ---
  for esc_record in esc_list:
    esc_aggr_interference = aggregate_interference.\
      calculateAggregateInterferenceForEsc(
          esc_record, data.getAllGrantInfoFromCbsdDataDump(cbsd_list))
    print('\nAggregate Interference (mW) output at ESC: %s\n'
          % (CvtToList(esc_aggr_interference)))

  #--- GWPZ ---
  for gwpz_record in gwpz_list:
    gwpz_aggr_interference = aggregate_interference.\
      calculateAggregateInterferenceForGwpz(
          gwpz_record, data.getAllGrantInfoFromCbsdDataDump(cbsd_list))
    print('\nAggregate Interference (mW) output at GWPZ: \n' +
          str(CvtToList(gwpz_aggr_interference))[0:400])

  #--- PPA ---
  for ppa_record in ppa_list:
    ppa_aggr_interference = aggregate_interference.\
      calculateAggregateInterferenceForPpa(
          ppa_record, pal_list,
          data.getAllGrantInfoFromCbsdDataDump(cbsd_list, ppa_record=ppa_record))
    print('\nAggregate Interference (mW) output at PPA: \n' +
          str(CvtToList(gwpz_aggr_interference))[0:400])

  prof0.disable()
  end_time = time.time()
  #=======================================
  print('\nComputation time: %.4f\n' % (end_time - start_time))
  print('Saving profile')
  prof0.dump_stats('profile-0m.out')
  pool.dump_stats()

  #=======================================
  # Print on screen basic data
  import pstats
  print('******* Profiling on main process *******')
  p0 = pstats.Stats('profile-0m.out')
  p0.sort_stats('cumulative')
  p0.print_stats(20)
  print('******* Profiling on worker1 *******')
  p1 = pstats.Stats('profile-1.out')
  p1.sort_stats('cumulative')
  p1.print_stats(20)
