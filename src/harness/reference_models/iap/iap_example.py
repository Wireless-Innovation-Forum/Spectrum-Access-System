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
# value at a protection constraint. 
# =============================================================================

import json
import os
import iap
import time
import multiprocessing
from multiprocessing import Pool
from reference_models.interference import interference as interf
from full_activity_dump import FullActivityDump

# Number of processes for parallel execution
NUM_OF_PROCESS = 30

cbsd_0 = json.load(open(os.path.join('test_data', 'cbsd_0.json')))
cbsd_1 = json.load(open(os.path.join('test_data', 'cbsd_1.json')))
cbsd_2 = json.load(open(os.path.join('test_data', 'cbsd_2.json')))
cbsd_3 = json.load(open(os.path.join('test_data', 'cbsd_3.json')))
cbsd_4 = json.load(open(os.path.join('test_data', 'cbsd_4.json')))
cbsd_5 = json.load(open(os.path.join('test_data', 'cbsd_5.json')))
cbsd_6 = json.load(open(os.path.join('test_data', 'cbsd_6.json')))
cbsd_7 = json.load(open(os.path.join('test_data', 'cbsd_7.json')))
cbsd_8 = json.load(open(os.path.join('test_data', 'cbsd_8.json')))
cbsd_9 = json.load(open(os.path.join('test_data', 'cbsd_9.json')))
cbsd_10 = json.load(open(os.path.join('test_data', 'cbsd_10.json')))
cbsd_11 = json.load(open(os.path.join('test_data', 'cbsd_11.json')))
cbsd_12 = json.load(open(os.path.join('test_data', 'cbsd_12.json')))
cbsd_13 = json.load(open(os.path.join('test_data', 'cbsd_13.json')))
cbsd_14 = json.load(open(os.path.join('test_data', 'cbsd_14.json')))
cbsd_15 = json.load(open(os.path.join('test_data', 'cbsd_15.json')))
cbsd_16 = json.load(open(os.path.join('test_data', 'cbsd_16.json')))
cbsd_17 = json.load(open(os.path.join('test_data', 'cbsd_17.json')))
cbsd_18 = json.load(open(os.path.join('test_data', 'cbsd_18.json')))
cbsd_19 = json.load(open(os.path.join('test_data', 'cbsd_19.json')))
cbsd_20 = json.load(open(os.path.join('test_data', 'cbsd_20.json')))
cbsd_21 = json.load(open(os.path.join('test_data', 'cbsd_21.json')))
cbsd_22 = json.load(open(os.path.join('test_data', 'cbsd_22.json')))
cbsd_23 = json.load(open(os.path.join('test_data', 'cbsd_23.json')))


fss_0 = json.load(open(os.path.join('test_data', 'fss_0.json')))
fss_1 = json.load(open(os.path.join('test_data', 'fss_1.json')))

ppa_0 = json.load(open(os.path.join('test_data', 'ppa_0.json')))
ppa_1 = json.load(open(os.path.join('test_data', 'ppa_1.json')))
ppa_2 = json.load(open(os.path.join('test_data', 'ppa_2.json')))
ppa_3 = json.load(open(os.path.join('test_data', 'ppa_3.json')))

esc_0 = json.load(open(os.path.join('test_data', 'esc_0.json')))

gwpz_0 = json.load(open(os.path.join('test_data', 'gwpz_0.json')))
gwpz_1 = json.load(open(os.path.join('test_data', 'gwpz_1.json')))

pal_0 = json.load(open(os.path.join('test_data', 'pal_0.json')))
pal_1 = json.load(open(os.path.join('test_data', 'pal_1.json')))
pal_2 = json.load(open(os.path.join('test_data', 'pal_2.json')))
pal_3 = json.load(open(os.path.join('test_data', 'pal_3.json')))

sas_uut = FullActivityDump({
          'cbsd': [cbsd_0, cbsd_1, cbsd_2, cbsd_3, cbsd_4, cbsd_5, cbsd_6,cbsd_7, cbsd_8, cbsd_9, cbsd_10, cbsd_11, cbsd_12, cbsd_13, cbsd_14, cbsd_15, cbsd_16, cbsd_17, cbsd_18, cbsd_19],
          'esc_sensor': [], 
          'zone': []
        })  
sas_th1 = FullActivityDump({
          'cbsd': [cbsd_20], 
          'esc_sensor': [],
          'zone': []
        }) 
sas_th2 = FullActivityDump({
          'cbsd': [cbsd_22, cbsd_23], 
          'esc_sensor': [],
          'zone': [],
        })  
pal_records = [pal_0, pal_1, pal_2, pal_3]
fss_records = [fss_0, fss_1]
esc_records = [esc_0]
gwpz_records = [gwpz_0, gwpz_1]
ppa_records = [ppa_0, ppa_1, ppa_2, ppa_3]

sas_th_fad_objects = [sas_th1, sas_th2]

start_time = time.time()

for fss_record in fss_records:
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
    fss_cochannel_allowed_interference = iap.performIapForFssCochannel(fss_record, sas_uut, sas_th_fad_objects)
    print('$$$$ IAP Reference Model Output for FSS Co-Channel: AP_IAP_Ref (mW/IAPBW)$$$$' +
                                                  str(fss_cochannel_allowed_interference))
    fss_blocking_allowed_interference = iap.performIapForFssBlocking(fss_record, sas_uut, sas_th_fad_objects)
    print('$$$$ IAP Reference Model Output for FSS Blocking: AP_IAP_Ref (mW/IAPBW)$$$$' +
                                                  str(fss_blocking_allowed_interference))
  # FSS Passband is between 3700 and 4200 and TT&C flag is set to TRUE
  elif (fss_low_freq >= interf.FSS_TTC_LOW_FREQ_HZ and 
          fss_high_freq <= interf.FSS_TTC_HIGH_FREQ_HZ and
          fss_ttc_flag is True):
    fss_blocking_allowed_interference = iap.performIapForFssBlocking(fss_record, sas_uut, sas_th_fad_objects)
    print('$$$$ IAP Reference Model Output for FSS Blocking: AP_IAP_Ref (mW/IAPBW)$$$$' +
                                                  str(fss_blocking_allowed_interference))
for esc_record in esc_records:
  esc_allowed_interference = iap.performIapForEsc(esc_record, sas_uut, sas_th_fad_objects)
  print('$$$$ IAP Reference Model Output for ESC: AP_IAP_Ref (mW/IAPBW)$$$$' +
                                                  str(esc_allowed_interference))
for gwpz_record in gwpz_records:
  pool = Pool(processes=min(multiprocessing.cpu_count(), NUM_OF_PROCESS))
  gwpz_allowed_interference = iap.performIapForGwpz(gwpz_record, sas_uut, sas_th_fad_objects)
  print('$$$$ IAP Reference Model Output for GWPZ: AP_IAP_Ref (mW/IAPBW)$$$$' +
                                                  str(gwpz_allowed_interference))
for ppa_record in ppa_records:
  pool = Pool(processes=min(multiprocessing.cpu_count(), NUM_OF_PROCESS))
  ppa_allowed_interference = iap.performIapForPpa(ppa_record, sas_uut, sas_th_fad_objects, pal_records, pool)
  print('$$$$ IAP Reference Model Output for PPA: AP_IAP_Ref (mW/IAPBW)$$$$' +
                                                  str(ppa_allowed_interference))

end_time = time.time()

print('$$$$ Computation time: $$$$' + str(end_time - start_time))



