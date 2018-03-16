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
# Test IAP calculation for GWPZ, PPA, FSS and ESC Sensor incumbent types.
# Expected result is dictionary containing post IAP aggregate interference
# value at a protection constaint. 
# =============================================================================

import sas_objects
import json
import os
import iap
import time
import logging

cbsd_0 = json.load(open(os.path.join('test_data', 'cbsd_0.json')))
cbsd_1 = json.load(open(os.path.join('test_data', 'cbsd_1.json')))
cbsd_2 = json.load(open(os.path.join('test_data', 'cbsd_2.json')))
cbsd_3 = json.load(open(os.path.join('test_data', 'cbsd_3.json')))
cbsd_4 = json.load(open(os.path.join('test_data', 'cbsd_4.json')))
cbsd_5 = json.load(open(os.path.join('test_data', 'cbsd_5.json')))
cbsd_6 = json.load(open(os.path.join('test_data', 'cbsd_6.json')))

fss_0 = json.load(open(os.path.join('test_data', 'fss_0.json')))
fss_1 = json.load(open(os.path.join('test_data', 'fss_1.json')))

ppa_0 = json.load(open(os.path.join('test_data', 'ppa_0.json')))
ppa_1 = json.load(open(os.path.join('test_data', 'ppa_1.json')))
ppa_2 = json.load(open(os.path.join('test_data', 'ppa_2.json')))

esc_0 = json.load(open(os.path.join('test_data', 'esc_0.json')))

gpwz_0 = json.load(open(os.path.join('test_data', 'gwpz_0.json')))
gpwz_1 = json.load(open(os.path.join('test_data', 'gwpz_1.json')))
gpwz_2 = json.load(open(os.path.join('test_data', 'gwpz_2.json')))

pal_0 = json.load(open(os.path.join('test_data', 'pal_0.json')))
pal_1 = json.load(open(os.path.join('test_data', 'pal_1.json')))
pal_2 = json.load(open(os.path.join('test_data', 'pal_2.json')))
pal_3 = json.load(open(os.path.join('test_data', 'pal_3.json')))

sas_uut = sas_objects.FullActivityDump("", "", "", "")
sas_th_1 = sas_objects.FullActivityDump("", "", "", "")
sas_th_2 = sas_objects.FullActivityDump("", "", "", "")
sas_uut.cbsd_records = [cbsd_0, cbsd_1, cbsd_2]
sas_th_1.cbsd_records = [cbsd_3, cbsd_6]
sas_th_2.cbsd_records = [cbsd_4, cbsd_5]
pal_records = [pal_0, pal_1, pal_2, pal_3]

sas_th_fad_objects = [sas_th_1, sas_th_2]
protected_entities = [gpwz_0, gpwz_1, gpwz_2, fss_0, fss_1, ppa_0, ppa_1, ppa_2, esc_0]

start_time = time.time()

iap_output = iap.performIap(protected_entities, sas_uut, sas_th_fad_objects, pal_records)

end_time = time.time()

logging.info('$$$$ IAP Reference Model Output: AP_IAP_Ref (mW/RBW)$$$$' +
                                                  str(iap_output))
logging.info('$$$$ Computation time: $$$$' + str(end_time - start_time))



