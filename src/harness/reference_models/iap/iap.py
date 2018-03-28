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
==================================================================================
  Iterative Allocation Process(IAP) Reference Model [R2-SGN-16].
  Based on WINNF-TS-0061, Version V1.0.0-r5.1, 17 January 2018.

  This model provides functions to calculate post IAP allowed interference margin for 
  the protection constraint of FSS, ESC, GWPZ and PPA. 

  The main routines are:

    performIapForEsc
    performIapForGwpz
    performIapForPpa
    performIapForFss
    calculateApIapRef

  The routines return a nested dictionary containing in the format of
  {latitude : {longitude : [interference1, interference2]}. interference is 
  the post IAP aggregate interference value from all the CBSDs managed by the 
  SAS in mW/IAPBW for each of the constraints.
==================================================================================
"""

from reference_models.geo import utils
from reference_models.interference import interference as interf
import numpy as np
import logging
from collections import namedtuple
import multiprocessing
from multiprocessing import Pool
from functools import partial

# Define Post IAP Grant information, i.e., a tuple with named fields of
# 'eirp', 'interference'
PostIAPGrantInfo = namedtuple('PostIAPGrantInfo', ['eirp', 'interference'])

# values from WINNF-TS-0061-V1.1.0 - WG4 SAS Test and Certification Spec-Table 
# 8.4-2 Protected entity reference for IAP Protection 
# The values are in (dBm/RBW)
Q_PPA_DBM_PER_RBW = -80
Q_GWPZ_DBM_PER_RBW = -80
Q_FSS_CO_CHANNEL_DBM_PER_RBW = -129
Q_FSS_BLOCKING_DBM_PER_RBW = -60
Q_ESC_DBM_PER_RBW = -109

# Default 1 dB pre IAP margin for all incumbent types
MG_PPA_DB = 1
MG_GWPZ_DB = 1
MG_FSS_CO_CHANNEL_DB = 1
MG_FSS_BLOCKING_DB = 1
MG_ESC_DB = 1


class PostIapOutputFormat:
  """Implementation of IAP output format
  
  Creates a data structure to store post IAP output in the format of 
  {latitude : {longitude : [ output_first_5MHz_segment, output_first_5MHz_segment ]}}
  """
  def __init__(self):
    self.manager = multiprocessing.Manager()
    self.post_iap_output_info = self.manager.dict()

  def SetPostIapInfo(self, latitude, longitude, grant_info):
    if self.post_iap_output_info.has_key(latitude) is False:
      self.post_iap_output_info[latitude] = {}
   
    # Creating a proxy container for mutable dictionary
    post_iap_output_proxy = self.post_iap_output_info[latitude]

    if post_iap_output_proxy.has_key(longitude) is False:
      post_iap_output_proxy[longitude] = []

    post_iap_output_proxy[longitude].append(grant_info)
    self.post_iap_output_info[latitude] = post_iap_output_proxy 

  def GetPostIapInfo(self):
    return self.post_iap_output_info 

# Post IAP managed grants information maintained in the format of 
# { latitude : {longitude : [ (eirp1, interference1), (eirp2, interference2) ] }}
post_iap_managed_grants = PostIapOutputFormat()

# Aggregate interference Ap considering grants from managing SAS and
# SAS Test Harness in the format of 
# { latitude : {longitude : [ interference1, interference2] }}
aggregate_interference = PostIapOutputFormat()

def iapPointConstraint(protection_point, channels, low_freq, high_freq, 
                       grant_objects, fss_info, esc_antenna_info, region_type, 
                       threshold, protection_ent_type):
  """ Routine to compute aggregate interference(Ap) from authorized grants 
   
  Aggregate interference is calculated over all the 5MHz channels.This routine 
  is applicable for FSS Co-Channel and ESC Sensor protection points.Also for 
  protection points within PPA and GWPZ protection areas. Post IAP grant EIRP
  and interference contribution is calculated over each 5MHz channel

  Args:
    protection_point: List of protection points inside protection area
    channels: List of tuples containing (low_freq, high_freq) of each 5MHz 
              segment of the whole frequency range of protected entity
    low_freq: low frequency of protection constraint (Hz)
    high_freq: high frequency of protection constraint (Hz)
    grant_objects: a list of grant requests, each one being a tuple 
                   containing grant information
    fss_info: contains information on antenna height
              on the tangent and perpendicular components.
    esc_antenna_info: contains information on ESC antenna height, azimuth, 
                      gain and pattern gain
    threshold: protection threshold (mW)
    protection_ent_type: an enum member of class ProtectedEntityType
  Returns:
    Updates post_iap_managed_grants global instance of class type PostIapOutputFormat.
    It is updated in the format of {latitude : {longitude : [ (eirp, interference),.. ]}}
    and aggregate_interference global instance of class type PostIapOutputFormat.
    It is updated in the format of {latitude : { longitude : [interference,..] }}
  """
  
  # Get all the grants inside neighborhood of the protection entity
  grants_inside = interf.findGrantsInsideNeighborhood(
                    grant_objects, protection_point, protection_ent_type)
  
  if len(grants_inside) > 0:

    for channel in channels:
      # Set interference quota for protection_point, channel combination

      # Calculate Roll of Attenuation for ESC Sensor Protection entity
      if protection_ent_type is interf.ProtectedEntityType.ESC:
        if channel[0] >= 3650.e6:
          center_freq = (channel[0] + channel[1]) / 2
          interference_quota = interf.dbToLinear(interf.linearToDb(threshold) - 
                (2.5 + ((center_freq - interf.ESC_CH21_CF_HZ) / interf.MHZ)))
        else:
          interference_quota = threshold

      # Get the FSS blocking passband range
      elif protection_ent_type is interf.ProtectedEntityType.FSS_BLOCKING:
        interference_quota = threshold
        channel = [low_freq, high_freq]

      else:
        interference_quota = threshold

      # Get protection constraint over 5MHz channel range
      channel_constraint = interf.ProtectionConstraint(latitude=protection_point[0],
                             longitude=protection_point[1], low_frequency=channel[0],
                             high_frequency=channel[1], entity_type=protection_ent_type)

      # Identify CBSD grants overlapping with frequency range of the protection entity 
      # in the neighborhood of the protection point and channel
      neighborhood_grants = interf.findOverlappingGrants(
                              grants_inside, channel_constraint)
      num_grants = len(neighborhood_grants)

      if not neighborhood_grants:
        continue

      # calculate the fair share
      fair_share = float(interference_quota) / num_grants

      # Empty list of final IAP EIRP and interference assigned to the grant
      grants_eirp = []

      # Initialize interference list to 0 for all the neighborhood_grants
      interference_list = [0] * num_grants

      aggr_interference = 0

      # Initialize flag to False for all the grants
      grant_initialize_flag = [False] * num_grants

      # Initialize grant EIRP to maxEirp for all the grants 
      grants_eirp = [grant.max_eirp for grant in neighborhood_grants]

      while (num_grants > 0):
        for index, grant in enumerate(neighborhood_grants):
          if grant_initialize_flag[index] is False:
            # Compute interference grant causes to protection point over channel
            interference = interf.computeInterference(grant, grants_eirp[index], 
                             channel_constraint, fss_info, esc_antenna_info, region_type)
            # calculated interference exceeds fair share of
            # interference to which the grants are entitled
            if interference < fair_share:
              interference_list[index] = interference
              # Grant is satisfied
              grant_initialize_flag[index] = True

        for i, grant in enumerate(neighborhood_grants):

          if grant_initialize_flag[i] is True:

            # Remove satisfied CBSD grant from consideration
            interference_quota = interference_quota - interference_list[i]

            if num_grants > 0:
              num_grants = num_grants - 1

            # re-calculate the fair share if number of grants are not zero
            if num_grants != 0:
              fair_share = float (interference_quota) / num_grants

            # Get aggregate interference
            aggr_interference += interference_list[i]

            # Update EIRP and Interference only if managed grant
            if grant.is_managed_grant:
              post_iap_grant = PostIAPGrantInfo(eirp=grants_eirp[i], 
                                 interference=interference_list[i])
              post_iap_managed_grants.SetPostIapInfo(channel_constraint.latitude, 
                channel_constraint.longitude, post_iap_grant)
          else:
            grants_eirp[i] = grants_eirp[i] - 1
      
        aggregate_interference.SetPostIapInfo(channel_constraint.latitude,
            channel_constraint.longitude, aggr_interference)
   
  return 


def performIapForEsc(protected_entity, sas_uut_fad_object, sas_th_fad_objects):
  """ Compute post IAP interference margin for ESC 
  
  IAP algorithm is run over ESC passband 3550-3660MHz for Category A CBSDs and 
  3550-3680MHz for Category B CBSDs

  Args:
    protected_entity: Protected entity of type ESC
    sas_uut_fad_object: FAD object from SAS UUT
    sas_th_fad_object: a list of FAD objects from SAS Test Harness
  """
  iap_threshold_esc = Q_ESC_DBM_PER_RBW + \
                    interf.linearToDb(interf.IAPBW_HZ / interf.MHZ)
  iap_margin_esc = interf.dbToLinear(iap_threshold_esc - MG_ESC_DB)

  grant_objects = interf.getGrantObjectsFromFAD(sas_uut_fad_object, sas_th_fad_objects)

  # Get number of SAS 
  num_sas = len(sas_th_fad_objects) + 1

  # Get the protection point of the ESC
  esc_point = protected_entity['installationParam']
  protection_point = (esc_point['latitude'], esc_point['longitude'])

  # Get azimuth radiation pattern
  ant_pattern = esc_point['azimuthRadiationPattern']

  # Initialize array of size length of ant_pattern list
  ant_pattern_gain = np.arange(len(ant_pattern))
  for i, pattern in enumerate(ant_pattern):
    ant_pattern_gain[i] = pattern['gain']

  # Get ESC antenna information
  esc_antenna_info = interf.EscInformation(antenna_height=esc_point['height'],
                       antenna_azimuth=0,
                       antenna_gain=0,
                       antenna_pattern_gain=ant_pattern_gain)

  # Get ESC passband 3550-3680 MHz protection channels
  protection_channels = interf.getProtectedChannels(interf.ESC_LOW_FREQ_HZ, 
                          interf.ESC_HIGH_FREQ_HZ)

  logging.debug('$$$$ Calling ESC Protection $$$$')
  # ESC algorithm
  iapPointConstraint(protection_point, protection_channels, 
    interf.ESC_LOW_FREQ_HZ, interf.ESC_HIGH_FREQ_HZ, 
    grant_objects, None, esc_antenna_info, None, 
    iap_margin_esc, interf.ProtectedEntityType.ESC)
  
  ap_iap_ref = calculateApIapRef(iap_margin_esc, num_sas)
  return ap_iap_ref 

def performIapForGwpz(protected_entity, sas_uut_fad_object, sas_th_fad_objects):
  """Compute post IAP interference margin for GWPZ incumbent type

  Routine to get protection points within GWPZ protection area and perform 
  IAP algorithm on each protection point 

  Args:
    protected_entity: Protected entity of type GWPZ
    sas_uut_fad_object: FAD object from SAS UUT
    sas_th_fad_object: a list of FAD objects from SAS Test Harness
  """
  iap_threshold_gwpz = Q_GWPZ_DBM_PER_RBW + \
                    interf.linearToDb(interf.IAPBW_HZ / interf.GWPZ_RBW_HZ)
  iap_margin_gwpz = interf.dbToLinear(iap_threshold_gwpz - MG_GWPZ_DB)

  grant_objects = interf.getGrantObjectsFromFAD(sas_uut_fad_object, sas_th_fad_objects)

  # Get number of SAS 
  num_sas = len(sas_th_fad_objects) + 1

  logging.debug('$$$$ Getting GRID points for GWPZ Protection Area $$$$')
  # Get Fine Grid Points for a GWPZ protection area
  protection_points = utils.GridPolygon(protected_entity)

  gwpz_freq_range = protected_entity['deploymentParam']\
                      ['operationParam']['operationFrequencyRange']
  gwpz_low_freq = gwpz_freq_range['lowFrequency']
  gwpz_high_freq = gwpz_freq_range['highFrequency']

  gwpz_region = protected_entity['zone']['features'][0]\
                                 ['properties']['clutter']

  # Get channels over which area incumbent needs partial/full protection
  protection_channels = interf.getProtectedChannels(gwpz_low_freq, gwpz_high_freq)
  
  # Apply IAP for each protection constraint with a pool of parallel processes.
  pool = Pool(processes=min(multiprocessing.cpu_count(), len(protection_points)))

  logging.debug('$$$$ Calling GWPZ Protection $$$$')
  iapPoint = partial(iapPointConstraint, channels=protection_channels, 
                     low_freq=gwpz_low_freq, high_freq=gwpz_high_freq, 
                     grant_objects=grant_objects, fss_info=None, 
                     esc_antenna_info=None, region_type=gwpz_region,
                     threshold=iap_margin_gwpz, 
                     protection_ent_type=interf.ProtectedEntityType.GWPZ_AREA)

  pool.map(iapPoint, protection_points)

  pool.close()
  pool.join()

  ap_iap_ref = calculateApIapRef(iap_threshold_gwpz, num_sas)
  return ap_iap_ref 


def performIapForPpa(protected_entity, sas_uut_fad_object, sas_th_fad_objects, pal_records):
  """Compute post IAP interference margin for PPA incumbent type

  Routine to get protection points within PPA protection area and perform 
  IAP algorithm on each protection point

  Args:
    protected_entity: Protected entity of type PPA
    sas_uut_fad_object: FAD object from SAS UUT
    sas_th_fad_object: a list of FAD objects from SAS Test Harness
    pal_records: PAL records associated with a PPA protection area 
  """
  iap_threshold_ppa = Q_PPA_DBM_PER_RBW + \
                    interf.linearToDb(interf.IAPBW_HZ / interf.PPA_RBW_HZ)
  iap_margin_ppa = interf.dbToLinear(iap_threshold_ppa - MG_PPA_DB)

  grant_objects = interf.getGrantObjectsFromFAD(sas_uut_fad_object, sas_th_fad_objects)
  
  # Get number of SAS 
  num_sas = len(sas_th_fad_objects) + 1

  logging.debug('$$$$ Getting GRID points for PPA Protection Area $$$$')

  # Get Fine Grid Points for a PPA protection area
  protection_points = utils.GridPolygon(protected_entity)

  # Get the region type of the PPA protection area
  ppa_region = protected_entity['ppaInfo']['ppaRegionType']

  # Find the PAL records for the PAL_IDs defined in PPA records
  ppa_pal_ids = protected_entity['ppaInfo']['palId']

  for pal_record in pal_records:
    if pal_record['palId'] == ppa_pal_ids[0]:
      # Get the frequencies from the PAL records
      ppa_freq_range = pal_record['channelAssignment']['primaryAssignment']
      ppa_low_freq = ppa_freq_range['lowFrequency']
      ppa_high_freq = ppa_freq_range['highFrequency']

      # Get channels over which area incumbent needs partial/full protection
      protection_channels = interf.getProtectedChannels(ppa_low_freq, ppa_high_freq)

      # Apply IAP for each protection constraint with a pool of parallel 
      # processes.
      logging.debug('$$$$ Calling PPA Protection $$$$')
     
      pool = Pool(processes=min(multiprocessing.cpu_count(), 
                                   len(protection_points)))
      iapPoint = partial(iapPointConstraint, channels=protection_channels, 
                         low_freq=ppa_low_freq, high_freq=ppa_high_freq, 
                         grant_objects=grant_objects, fss_info=None, 
                         esc_antenna_info=None, region_type=ppa_region,
                         threshold=iap_margin_ppa, 
                         protection_ent_type=interf.ProtectedEntityType.PPA_AREA)

      pool.map(iapPoint, protection_points)

      pool.close()
      pool.join()
      break
  
  ap_iap_ref = calculateApIapRef(iap_threshold_ppa, num_sas)
  return ap_iap_ref 

def performIapForFssCochannel(protected_entity, sas_uut_fad_object, sas_th_fad_objects):
  """Compute post IAP interference margin for FSS Co-channel incumbent type

  FSS protection is provided over co-channel pass band

  Args:
    protected_entity: Protected entity of type PPA
    sas_uut_fad_object: FAD object from SAS UUT
    sas_th_fad_object: a list of FAD objects from SAS Test Harness
  """
  iap_threshold_fss_cochannel = Q_FSS_CO_CHANNEL_DBM_PER_RBW + \
                    interf.linearToDb(interf.IAPBW_HZ / interf.MHZ)
  iap_margin_fss_cochannel = interf.dbToLinear(iap_threshold_fss_cochannel -
                              MG_FSS_CO_CHANNEL_DB)

  grant_objects = interf.getGrantObjectsFromFAD(sas_uut_fad_object, sas_th_fad_objects)

  # Get number of SAS 
  num_sas = len(sas_th_fad_objects) + 1

  # Get the protection point of the FSS
  fss_point = protected_entity['deploymentParam'][0]['installationParam']
  protection_point = (fss_point['latitude'], fss_point['longitude'])

  # Get the frequency range of the FSS
  fss_freq_range = protected_entity['deploymentParam'][0]\
      ['operationParam']['operationFrequencyRange']
  fss_low_freq = fss_freq_range['lowFrequency']

  # Get FSS information
  fss_info = interf.FssProtectionPoint(latitude=fss_point['latitude'], 
               longitude=fss_point['longitude'],
               height_agl=fss_point['height'],
               max_gain_dbi=fss_point['antennaGain'],
               pointing_azimuth=fss_point['antennaAzimuth'],
               pointing_elevation=fss_point['elevation'])

  # Get channels for co-channel CBSDs
  protection_channels = interf.getProtectedChannels(fss_low_freq, interf.CBRS_HIGH_FREQ_HZ)

  # FSS Co-channel algorithm
  logging.debug('$$$$ Calling FSS co-channel Protection $$$$')
  iapPointConstraint(protection_point, protection_channels, fss_low_freq,
    interf.CBRS_HIGH_FREQ_HZ, grant_objects, fss_info, None, 
    None, iap_margin_fss_cochannel, 
    interf.ProtectedEntityType.FSS_CO_CHANNEL)
  
  ap_iap_ref = calculateApIapRef(iap_margin_fss_cochannel, num_sas)
  return ap_iap_ref 

def performIapForFssBlocking(protected_entity, sas_uut_fad_object, sas_th_fad_objects):
  """Compute post IAP interference margin for FSS Blocking incumbent type

  FSS protection is provided over blocking pass band

  Args:
    protected_entity: Protected entity of type PPA
    sas_uut_fad_object: FAD object from SAS UUT
    sas_th_fad_object: a list of FAD objects from SAS Test Harness
  """

  iap_threshold_fss_blocking = Q_FSS_BLOCKING_DBM_PER_RBW 
  iap_margin_fss_blocking = interf.dbToLinear(iap_threshold_fss_blocking -
                              MG_FSS_BLOCKING_DB)

  grant_objects = interf.getGrantObjectsFromFAD(sas_uut_fad_object, sas_th_fad_objects)

  # Get number of SAS 
  num_sas = len(sas_th_fad_objects) + 1

  # Get FSS T&C Flag value
  fss_ttc_flag = protected_entity['deploymentParam'][0]['ttc']

  # Get the protection point of the FSS
  fss_point = protected_entity['deploymentParam'][0]['installationParam']
  protection_point = (fss_point['latitude'], fss_point['longitude'])

  # Get the frequency range of the FSS
  fss_freq_range = protected_entity['deploymentParam'][0]\
      ['operationParam']['operationFrequencyRange']
  fss_low_freq = fss_freq_range['lowFrequency']
  fss_high_freq = fss_freq_range['highFrequency']

  # Get FSS information
  fss_info = interf.FssProtectionPoint(latitude=fss_point['latitude'], 
               longitude=fss_point['longitude'],
               height_agl=fss_point['height'],
               max_gain_dbi=fss_point['antennaGain'],
               pointing_azimuth=fss_point['antennaAzimuth'],
               pointing_elevation=fss_point['elevation'])

  # FSS Passband is between 3700 and 4200 and TT&C flag is set to TRUE
  if (fss_low_freq >= interf.FSS_TTC_LOW_FREQ_HZ and 
           fss_high_freq <= interf.FSS_TTC_HIGH_FREQ_HZ):
    if (fss_ttc_flag is False):
      logging.debug('$$$$ IAP for FSS not applied for FSS Pass band 3700 to 4200' 
        'and TT&C flag set to false $$$$')
  else:
    logging.debug('$$$$ Calling FSS blocking Protection $$$$')
    # 5MHz channelization is not required for Blocking protection
    protection_channels = [interf.CBRS_LOW_FREQ_HZ, fss_low_freq]
    iapPointConstraint(protection_point, protection_channels, 
      interf.CBRS_LOW_FREQ_HZ, fss_low_freq, grant_objects, 
      fss_info, None, None, iap_margin_fss_blocking, 
      interf.ProtectedEntityType.FSS_BLOCKING)

  ap_iap_ref = calculateApIapRef(iap_margin_fss_blocking, num_sas)
  return ap_iap_ref 


def calculateApIapRef(q_p, num_sas):
  """Compute post IAP aggregate interference 

  Routine to calculate aggregate interference from all the CBSDs managed by the
  SAS at protected entity.

  Args:
    q_p: Pre IAP threshold value for protection type(mW)
    num_sas: number of SASs in the peer group 
  Returns:
    ap_iap_ref: post IAP allowed interference in the format of 
                {latitude : {longitude : [interference, interference]}}
  """

  ap_iap_ref = {}
  managed_grants_info = post_iap_managed_grants.GetPostIapInfo()
  a_p_info = aggregate_interference.GetPostIapInfo()

  # Compute AP_IAP_Ref 
  for latitude, a_p_ch in a_p_info.items():
    for longitude, a_p_list in a_p_ch.items():
      a_sas_p = 0

      # Calculate a_sas_p - Aggregate interference calculated using the
      # EIRP obtained by all CBSDs through application of IAP for protected
      # entity p. Only grants managed by SAS UUT are considered
      for lat, point_info in managed_grants_info.items():
        for lon, grant_info in point_info.items():
          if latitude == lat and longitude == lon:
            a_sas_p = a_sas_p + sum(interference[1] for interference in grant_info)

      ap_iap_ref[latitude] = {}
      ap_iap_ref[latitude][longitude] = []
      for a_p in a_p_list:
        ap_iap_ref[latitude][longitude].append(((q_p - a_p) / num_sas) + a_sas_p)
  
  return ap_iap_ref
