#    Copyright 2016-2018 SAS Project Authors. All Rights Reserved.
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
"""
PPA Reference Model Sample File 

Note: The county in the testdata is not the actual county, 
it is only intended to be used for testing purpose.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import os

import util2
from reference_models.geo import drive
from reference_models.ppa import ppa


def json_load(fname):
  with open(fname) as fd:
    return json.load(fd)


# Configuration
user_id = 'pal_user_id_0'
pal_record_filenames = ['pal_record_0.json']
device_filenames = ['device_a.json']
pal_low_frequency = 3550000000
pal_high_frequency = 3650000000
TEST_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

# Change the Default County Driver Directory to parent directory of test_data
drive.ConfigureCountyDriver(TEST_DIR)

# Load Devices and PAL Records
devices = [json_load(os.path.join(TEST_DIR, device_filename))
           for device_filename in device_filenames]
pal_records = [json_load(os.path.join(TEST_DIR, pal_record_filename))
               for pal_record_filename in pal_record_filenames]

# Modify PAL Record to comply with WINNF-TS-0245
pal_records = util2.makePalRecordsConsistent(pal_records, pal_low_frequency,
                                                  pal_high_frequency, user_id)

ppa = ppa.PpaCreationModel(devices, pal_records)
print(ppa)
