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
import iap


#values from WINNF-TS-0061-V1.1.0 - WG4 SAS Test and Certification Spec-Table 8.4-2 Protected entity reference for IAP Protection
protectionThreshold = {'QPpa': -80, 'QGwpz': -80, 'QCochannel': -129, 'QBlocking': -60, 'QEsc':-109}

#considered the default value for testing purpose
preIAPHeadRooms = {'MgPpa': -2, 'MgGwpz': -2, 'MgCochannel': -2, 'MgBlocking': -2, 'MgEsc': -2}

#FSS protection point : 
#	Fss-Blocking : within 40 kms
#		- ppa_sas_th_1
#		- cbsd_2_sas_th_2
#		- cbsd_4_sas_th_1
#	Fss-CoChannel : within 150 kms
#		- ppa_sas_th_1
#		- cbsd_1_sas_th_1
#		- cbsd_4_sas_uut
#		- cbad_1_sas_uut
#		- cbsd_3_sas_th_2
#		- GPWZ
#GPWZ protection area :
#	inside area:
#		- cbsd_2_sas_uut
#	outside area : within 40 kms
#		- cbsd_1_sas_uut
#		- cbsd_4_sas_uut
#		- ESC_sas_th_2
#		- cbsd_5_sas_th_2
#
#
protectionEntities = {['fss_record_1_iap.json'],['gwpz_record_1_iap.json']}

#Record type : CBSD
#	cbsd_1_sas_uut : type A 
#       cbsd_2_sas_uut : type B
#       cbsd_3_sas_uut : type A
#       cbsd_4_sas_uut : type A
#       cbsd_5_sas_uut : type B
#
sasUUTFadObject = 'sas_uut_fad.json'

#sas_th_1
#Record type : CBSD
#       cbsd_1_sas_th_1 : type A
#       cbsd_2_sas_th_1 : type B
#       cbsd_3_sas_th_1 : type A
#       cbsd_4_sas_th_1 : type A
#       cbsd_5_sas_th_1 : type A
#Record type : PPA
#	inside the area
#		- cbsd_1_sas_th_1
#		- cbsd_2_sas_th_2	
#	within 40 kms
#		- FSS_0

#sas_th_2
#Record type : CBSD
#       cbsd_1_sas_th_2 : type B
#       cbsd_2_sas_th_2 : type B
#       cbsd_3_sas_th_2 : type B
#       cbsd_4_sas_th_2 : type B
#       cbsd_5_sas_th_2 : type A
#Record type : ESC_Sensor
#	within 40 kms :
#		- cbsd_5_sas_th_2 : type A
#		- GPWZ
#	within 80 kms :
#		- cbsd_2_sas_th_1 : type B
#		- cbsd_2_sas_uut : type B

sasTHFadObjects = {['sas_th_1_fad.json'],['sas_th_2_fad.json']}

iap_output = iap.performIAP(protectionThreshold, preIAPHeadRooms, protectionEntities, sasUUTFadObject, sasTHFadObjects)
