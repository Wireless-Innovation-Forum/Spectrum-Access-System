import json
import os

import util
from reference_models.ppa import ppa


"""
PPA Reference Model Sample File 

Note: The Census Tract in the testdata is not the actual Census Tract, 
it is only intended to be used for testing purpose.
"""

# Configuration
user_id = 'pal_user_id_0'
pal_record_filenames = ['pal_record_0.json']
device_filenames = ['device_a.json']
pal_low_frequency = 3550000000
pal_high_frequency = 3650000000

# Change the Default Driver Directory to test_data
ppa.ConfigureCensusTractDriver(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data'))

# Load Devices and Pal Records
devices = [json.load(open(os.path.join('test_data', device_filename)))
           for device_filename in device_filenames]
pal_records = [json.load(open(os.path.join('test_data', pal_record_filename)))
               for pal_record_filename in pal_record_filenames]

# Modify Pal Record to comply with WINNF-TS-0245
pal_records = util.makePpaAndPalRecordsConsistent(pal_records, pal_low_frequency,
                                                  pal_high_frequency, user_id)
ppa = ppa.PpaCreationModel(devices, pal_records)
print ppa
