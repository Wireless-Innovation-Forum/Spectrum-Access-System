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
    calling of 4 sub reference modules in to ensure the 
    checks to be done before sending to the IAP calculation 
"""

import sas_pre_iap_fss
import sas_objects
import radar_dpa_purge_list
import ppa_gwpz_purge_list

def pre_iap(protected_entities, uut_fad_object, test_harness_fad_objects, headroom):
    """
     Args:
      protected Entities: List of protected entities
      uut_fad_object: Fad Object for SAS UUT
      test_harness_fad_objects: List of FAD objects for SAS Test Harness
    
     Returns:
      Removes duplicate grants among SAS UUT and SAS Test harness
    """
    #Call Inter SAS duplicate grant purge list reference model
    inter_sas_duplicate_grant.InterSasDuplicateGrantReferenceModel(uut_fad_object, test_harness_fad_objects)
    
    # TODO
    # call Inland Radar / DPA purge list reference model

    # TODO
    # Call PPA, and GWPZ, and FSS+GWBL purge list reference model

    #call FSS purge list reference model
    for protected_record in protected_entities:
        if protected_record.has_key('FSS'):
            for fss_records in protected_record['FSS']:
                sas_pre_iap_fss.fssPurgeModel(fad_uut_object, fad_th_object, fss_records, headroom['MgOobe'])


def InterSasDuplicateGrantReferenceModel(self, uut_fad_object, test_harness_fad_objects):
     """
     Checks if a CBSD is registered with more than one SAS and removes the grants of the
     CBSD if they overlap. If all grants are removed from a CBSD then the CBSD is removed
     from the FAD Object.

     Args:
           uut_fad_object: UUT Objects
           test_harness_fad_objects: array of Test Harness Objects
    
     Returns:
           Purging duplicate grants among SAS UUT and SAS Test harness
     """

     #Creating list of cbsds from UUT FAD and Test Harness FADs
     cbsd_list = []
     for cbsds in uut_fad_object.getCbsds():
        cbsd_list.append(cbsds)
     for fad in test_harness_fad_objects:
        for cbsds in fad.getCbsds():
            cbsd_list.append(cbsds)

     #Iterate through each CBSD and check if the FCC ID and SerialNumber matches another
     #CBSD. If yes then check whether their grants overlap and mark the overlapping grants as duplicate.
     for source_index,src_cbsd in enumerate(cbsd_list):
        for destination_index,dst_cbsd in enumerate(cbsd_list):
           #Ensure that the source and destination CBSDs to compare are different objects 
           if source_index != destination_index :

              #Check if fccId and cbsdSerialNumber are same 
              if ((src_cbsd['registrationRequest']['fccId'] ==
                                          dst_cbsd['registrationRequest']['fccId'] ) and
                 (src_cbsd['registrationRequest']['cbsdSerialNumber'] ==
                                 dst_cbsd['registrationRequest']['cbsdSerialNumber']) ):
                 len_dst_grants = len(dst_cbsd['grantRequests'])
                 len_src_grants = len(src_cbsd['grantRequests'])

                 #Check matching grants in source and destination
                 for grant_src in range(0,len_src_grants):
                    for grant_dst in range(0, len_dst_grants):

                       #Check for overlapping grants
                       if (src_cbsd['grantRequests'][grant_src]['operationParam'][
                           'operationFrequencyRange']['lowFrequency']) >= (
                               dst_cbsd['grantRequests'][grant_dst]['operationParam'][
                                   'operationFrequencyRange']['lowFrequency']):
                          if (src_cbsd['grantRequests'][grant_src]['operationParam'][
                               'operationFrequencyRange']['lowFrequency']) < (
                                   dst_cbsd['grantRequests'][grant_dst]['operationParam'][
                                       'operationFrequencyRange']['highFrequency']):
                             #Marking the grant as duplicate
                             dst_cbsd['grantRequests'][grant_dst]["Duplicate_flag"] = "TRUE" 
                       else:
                          #Check for overlapping grants
                          if (src_cbsd['grantRequests'][grant_src]['operationParam'][
                               'operationFrequencyRange']['highFrequency']) <= (
                                   dst_cbsd['grantRequests'][grant_dst]['operationParam'][
                                       'operationFrequencyRange']['highFrequency']):
                             #Marking the grant as duplicate
                             dst_cbsd['grantRequests'][grant_dst]["Duplicate_flag"] = "TRUE"

     #Check and remove duplicates grants
     for cbsd in cbsd_list:
         for elements in cbsd['grantRequests']:
             if "Duplicate_flag" in elements:
                  cbsd['grantRequests'].remove(elements)

     #Check and removing cbsds with no grants
     uut = uut_fad_object.getCbsds()
     self.removeEmptyCbsd(uut)
     for fad in test_harness_fad_objects:
        test_harness = fad.getCbsds()
        self.removeEmptyCbsd(test_harness)

def removeEmptyCbsd(self,cbsd):
     """
     Checks if a CBSD has no grants and remove the CBSD if true.
     Args:
           CBSD element: CBSD element parameters 
    
     Returns:
           Removes cbsds with no grants
     """
     empty_cbsd_grants = []
     for index in range(len(cbsd)):
         if len(cbsd[index]['grantRequests']) == 0:
               empty_cbsd_grants.append(cbsd[index])   
     for elements in empty_cbsd_grants:
         cbsd.remove(elements)

