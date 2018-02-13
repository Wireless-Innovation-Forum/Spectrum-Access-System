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

"""
    This is the Pre-IAP reference model which implements
    calling of 4 sub reference modles in to ensure the 
    checks to be done before sending to the IAP calculation 
"""

import sas_pre_iap_fss
import sas_objects
import radar_dpa_purge_list
import ppa_gwpz_purge_list

def pre_iap(protected_entities, uut_fad_object, test_harness_fad_objects):
    """
     Args:
           request: A dictionary with multiple key-value pairs where the keys are
           Protected Entities: List of protected entities
           UUT FAD Object: FAD UUT Object
           Test Harness FAD Objects: array of Test Harness Objects
    
     Returns:
           Removes duplicate grants among SAS UUT and SAS Test harness
    """
    #Call Inter SAS duplicate grant purge list reference model
     inter_sas_duplicate_grant.InterSasDuplicateGrantReferenceModel(uut_fad_object, test_harness_fad_objects)

#    #call Inland Radar / DPA purge list reference model
#    radar_dpa_purge_list.RadarDPAPurgeListReferenceModel(uut_fad_object, test_harness_fad_objects,protected_entities)


#    #Call PPA, and GWPZ, and FSS+GWBL purge list reference model
#    ppa_gwpz_purge_list.PpaGpwzPurgeListReferenceModel(uut_fad_object, test_harness_fad_objects,protected_entities)

    #call FSS purge list reference model
    for protected_record in protected_entities:
        if protected_record.has_key('FSS'):
            for fss_records in protected_record['FSS']:
                sas_pre_iap_fss.fssPurgeModel(fad_uut_object, fad_th_object, fss_records, margin_oobe)

def InterSasDuplicateGrantReferenceModel(self, uut_fad_object, test_harness_fad_objects):
     """
     Args:
           request: A dictionary with multiple key-value pairs where the keys are
           UUT FAD Object: FAD UUT Object
           Test Harness FAD Objects: array of Test Harness Objects
    
     Returns:
           Purging duplicate grants among SAS UUT and SAS Test harness
     """
     #Creating list of cbsds
     cbsd_list = []
     for cbsds in uut_fad_object.getCbsds():
        cbsd_list.append(cbsds)
     for fad in test_harness_fad_objects:
        for cbsds in fad.getCbsds():
            cbsd_list.append(cbsds)

     #Check for every source cbsd
     for source_index,src_cbsd in enumerate(cbsd_list):
        delete_counter = 0
        duplicate_grant_index = []
        #Check for every destination cbsd
        for destination_index,dst_cbsd in enumerate(cbsd_list):
           if source_index != destination_index :
                #Check if fccId and cbsdSerialNumber are same 
                if ((src_cbsd['registrationRequest']['fccId'] ==
                                                 dst_cbsd['registrationRequest']['fccId'] ) and
                        (src_cbsd['registrationRequest']['cbsdSerialNumber'] ==
                                        dst_cbsd['registrationRequest']['cbsdSerialNumber']) ):
                        len_dst_grants = len(dst_cbsd['grantRequests'])
                        len_src_grants = len(src_cbsd['grantRequests'])
                        index = 0

                        #Check matching grants in source and destination
                        for grant_src in range(0,len_src_grants):
                            for grant_dst in range(0, len_dst_grants):
                                if (grant_dst == len_dst_grants ):
                                   break
                                if (index > 0):
                                   grant_dst = grant_dst -1

                                #Check overlapping grants
                                if (src_cbsd['grantRequests'][grant_src]['operationParam'][
                                    'operationFrequencyRange']['lowFrequency']) >= (
                                        dst_cbsd['grantRequests'][grant_dst]['operationParam'][
                                            'operationFrequencyRange']['lowFrequency']):
                                    if (src_cbsd['grantRequests'][grant_src]['operationParam'][
                                        'operationFrequencyRange']['lowFrequency']) < (
                                            dst_cbsd['grantRequests'][grant_dst]['operationParam'][
                                                'operationFrequencyRange']['highFrequency']):
                                        index = index+1
                                        delete_counter = delete_counter+1
                                        duplicate_grant_index.append(grant_src)

                                        #Delete destination grants
                                        del dst_cbsd['grantRequests'][grant_dst] 
                                        len_dst_grants = len_dst_grants -1 
                                else:
                                    #Check overlapping grants
                                    (src_cbsd['grantRequests'][grant_src]['operationParam'][
                                        'operationFrequencyRange']['highFrequency']) <= (
                                        dst_cbsd['grantRequests'][grant_dst]['operationParam'][
                                            'operationFrequencyRange']['highFrequency'])
                                    if (src_cbsd['grantRequests'][grant_src]['operationParam'][
                                        'operationFrequencyRange']['highFrequency']) > (
                                            dst_cbsd['grantRequests'][grant_dst]['operationParam'][
                                                'operationFrequencyRange']['highFrequency']):
                                        index = index+1
                                        delete_counter = delete_counter+1
                                        duplicate_grant_index.append(grant_src)

                                        #Delete destination grants
                                        del dst_cbsd['grantRequests'][grant_dst]
                                        len_dst_grants = len_dst_grants -1
        #Deleting source grants
        if (delete_counter > 0):
           duplicate_list = []
           for value in duplicate_grant_index:
              duplicate_list.append(src_cbsd['grantRequests'][value])
           for element in duplicate_list:
              src_cbsd['grantRequests'].remove(element)

>>>>>>> 7a4f7effd778d16ce2ce87583bfe380c2420bb42
