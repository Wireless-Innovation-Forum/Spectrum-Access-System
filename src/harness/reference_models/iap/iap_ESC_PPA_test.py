#    Copyright 20188888888oject Authors. All Rights Reserved.
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

#================================================================================
# Test IAP calculation for GWPZ, PPA, FSS and ESC Sensor Incumbent types.
# Expected result is 'key value pairs of location,frequency to Power Margin values'].
#================================================================================

import json
import os
import iap



#values from WINNF-TS-0061-V1.1.0 - WG4 SAS Test and Certification Spec-Table 8.4-2 Protected entity reference for IAP Protection
protection_thresholds = {'QPpa': -80, 'QGwpz': -80, 'QCochannel': -129, 'QBlocking': -60, 'QEsc':-109}

#considered the default value for testing purpose
pre_iap_headRooms = {'MgPpa': -2, 'MgGwpz': -2, 'MgCochannel': -2, 'MgBlocking': -2, 'MgEsc': -2}

x = json.load(open(os.path.join('gwpz_record_1_iap.json')))
y = json.load(open(os.path.join('fss_record_1_iap.json')))
protection_entities = [y,x]
f =  json.load(open(os.path.join('sas_uut_fad_2.json')))
sas_uut_fad_object = [f]
m =  json.load(open(os.path.join('sas_th_2_fad.json')))
n = json.load(open(os.path.join('sas_th_1.json')))
sas_th_fad_objects = [m,n]

iap_output = iap.performIAP(protection_thresholds, pre_iap_headRooms, protection_entities,sas_uut_fad_object, sas_th_fad_objects)
