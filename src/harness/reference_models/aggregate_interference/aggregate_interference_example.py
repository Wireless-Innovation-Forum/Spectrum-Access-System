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
# Test Aggregate Interference calculation for GWPZ, PPA, FSS and ESC Sensor 
# incumbent types.
# Expected result is dictionary containing aggregate interference
# value at a protection constaint. 
# =============================================================================
import json
import os
from pykml import parser
from collections import namedtuple
import aggregate_interference
import time
import logging


if __name__ == '__main__':

  # Data directory
  current_dir = os.getcwd()
  _BASE_DATA_DIR = os.path.join(current_dir, 'test_data')

  # Populate a list of CBSD registration requests
  cbsd_filename = ['cbsd_0.json',
                   'cbsd_1.json', 'cbsd_2.json', 'cbsd_3.json', 
                   'cbsd_4.json', 'cbsd_5.json', 'cbsd_6.json']
  cbsd_list = []
  for cbsd_file in cbsd_filename:
      cbsd_record = json.load(open(os.path.join(_BASE_DATA_DIR, cbsd_file)))
      cbsd_list.append(cbsd_record)

  # load and inject FSS data with Overlapping Frequency of CBSD
  fss = json.load(open(os.path.join(_BASE_DATA_DIR, ('fss_record_0.json'))))

  # load and inject ESC data with Overlapping Frequency of CBSD
  esc = json.load(
      open(os.path.join(_BASE_DATA_DIR, ('esc_sensor_record_0.json'))))

  # load and inject GWPZ data with Overlapping Frequency of CBSD
  gwpz = json.load(
      open(os.path.join(_BASE_DATA_DIR, ('gwpz_record_2.json'))))
  # load and inject PPA data with Overlapping Frequency of CBSD
  ppa = json.load(open(os.path.join(_BASE_DATA_DIR, ('ppa_record_2.json'))))

  # load and inject PAL to get the frequency for PPA calculation
  pal_filename = ['pal_0.json', 'pal_1.json', 'pal_2.json', 'pal_3.json']
  pal_list = []
  for pal_file in pal_filename:
      pal_record = json.load(open(os.path.join(_BASE_DATA_DIR, pal_file)))
      pal_list.append(pal_record)
  
  # Determine which CBSD grants are on the move list
  start_time = time.time()
  fss_aggr_interference = aggregate_interference.\
      calculateAggregateInterferenceForFss(fss, cbsd_list)
  esc_aggr_interference = aggregate_interference.\
      calculateAggregateInterferenceForEsc(esc, cbsd_list)
  gwpz_aggr_interference = aggregate_interference.\
      calculateAggregateInterferenceForGwpz(gwpz, cbsd_list)
  ppa_aggr_interference = aggregate_interference.\
      calculateAggregateInterferenceForPpa(ppa, pal_list, cbsd_list)

  end_time = time.time()
  logging.info('\nAggregate Interference (dBm) output at FSS: \n' + 
                    str(fss_aggr_interference))
  logging.info('\nAggregate Interference (dBm) output at ESC: \n' + 
                    str(esc_aggr_interference))
  logging.info('\nAggregate Interference (dBm) output at GWPZ: \n' + 
                    str(gwpz_aggr_interference))
  logging.info('\nAggregate Interference (dBm) output at PPA: \n' + 
                    str(ppa_aggr_interference))
  logging.info('\nComputation time: \n' + str(end_time - start_time))
