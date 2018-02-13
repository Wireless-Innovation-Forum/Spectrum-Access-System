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

import json
import os
from pykml import parser
from collections import namedtuple
import aggregate_interference
import time


if __name__ == '__main__':

    # Data directory
    current_dir = os.getcwd()
    _BASE_DATA_DIR = os.path.join(current_dir, 'test_data')

    # Populate a list of CBSD registration requests
    cbsd_filename = ['cbsd_0.json',
                     'cbsd_1.json']
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
        open(os.path.join(_BASE_DATA_DIR, ('gwpz_record_0.json'))))
    # load and inject PPA data with Overlapping Frequency of CBSD
    ppa = json.load(open(os.path.join(_BASE_DATA_DIR, ('ppa_record_0.json'))))

    # Determine which CBSD grants are on the move list
    start_time = time.time()
    res = aggregate_interference.calculateAggregateInterferenceForFSS(fss,cbsd_list)
    #res = aggregate_interference.calculateAggregateInterferenceForESC(esc,cbsd_list)
    #res = aggregate_interference.calculateAggregateInterferenceForGWPZ(gwpz,cbsd_list)
    #res = aggregate_interference.calculateAggregateInterferenceForPPA(ppa, cbsd_list)

    end_time = time.time()
    print 'Aggregate Interference output: ' + str(res)
    print 'Computation time: ' + str(end_time - start_time)
