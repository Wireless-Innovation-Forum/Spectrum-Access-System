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
    performIapForFssCochannel
    performIapForFssBlocking
    calculatePostIapAggregateInterference

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

# values from WINNF-TS-0061-V1.1.0 - WG4 SAS Test and Certification Spec-Table 
# 8.4-2 Protected entity reference for IAP Protection 
# The values are in (dBm/RBW)
THRESH_PPA_DBM_PER_RBW = -80
THRESH_GWPZ_DBM_PER_RBW = -80
THRESH_FSS_CO_CHANNEL_DBM_PER_RBW = -129
THRESH_FSS_BLOCKING_DBM_PER_RBW = -60
THRESH_ESC_DBM_PER_RBW = -109

# Default 1 dB pre IAP margin for all incumbent types
MARGIN_PPA_DB = 1
MARGIN_GWPZ_DB = 1
MARGIN_FSS_CO_CHANNEL_DB = 1
MARGIN_FSS_BLOCKING_DB = 1
MARGIN_ESC_DB = 1

# One Mega Hertz
MHZ = 1.e6

# Channel bandwidth over which SASs execute the IAP process
IAPBW_HZ = 5.e6

# GWPZ Area Protection reference bandwidth for the IAP process
GWPZ_RBW_HZ = 10.e6

# PPA Area Protection reference bandwidth for the IAP process
PPA_RBW_HZ = 10.e6

# FSS Point Protection reference bandwidth for the IAP process
FSS_RBW_HZ = 1*MHZ

# ESC Point Protection reference bandwidth for the IAP process
ESC_RBW_HZ = 1*MHZ


def iapPointConstraint(protection_point, channels, low_freq, high_freq, 
                       grant_objects, fss_info, esc_antenna_info, region_type, 
                       threshold, protection_ent_type, asas_interference, 
                       aggregate_interference): 
  """ Routine to compute aggregate interference(Ap and ASASp) from authorized grants 
   
  Aggregate interference is calculated over all the 5MHz channels.This routine 
  is applicable for FSS Co-Channel and ESC Sensor protection points.Also for 
  protection points within PPA and GWPZ protection areas. Post IAP grant EIRP
  and interference contribution is calculated over each 5MHz channel

  Args:
    protection_point: A protection point as a tuple (longitude, latitude).
    channels: List of tuples containing (low_freq, high_freq) of each 5MHz 
              segment of the whole frequency range of protected entity
    low_freq: low frequency of protection constraint (Hz)
    high_freq: high frequency of protection constraint (Hz)
    grant_objects: a list of grant requests, each one being a tuple 
                   containing grant information
    fss_info: contains fss point and antenna information
    esc_antenna_info: contains information on ESC antenna height, azimuth, 
                      gain and pattern gain
    threshold: protection threshold (mW)
    protection_ent_type: an enum member of class ProtectedEntityType 
    asas_interference: object of class type AggregateInterferenceOutputFormat 
    aggregate_interference: object of class type AggregateInterferenceOutputFormat 
  Returns:
    Updates asas_interference instance of class type AggregateInterferenceOutputFormat.
    It is updated in the format of {latitude : {longitude : [ asas_p(mW/IAPBW),.. ]}}
    and aggregate_interference instance of class type AggregateInterferenceOutputFormat.
    It is updated in the format of {latitude : { longitude : [a_p(mW/IAPBW),..] }}
  """
  
  # Get all the grants inside neighborhood of the protection entity
  grants_inside = interf.findGrantsInsideNeighborhood(
                    grant_objects, protection_point, protection_ent_type)
   
  if len(grants_inside) > 0:
    # Get protection constraint of protected entity
    protection_constraint = interf.ProtectionConstraint(latitude=protection_point[1],
                               longitude=protection_point[0], low_frequency=low_freq,
                               high_frequency=high_freq, entity_type=protection_ent_type)

    # Get all the grants fully/partially overlap with protection point,p
    neighborhood_grants = interf.findOverlappingGrants(
                            grants_inside, protection_constraint)

    num_unsatisfied_grants = len(neighborhood_grants)
    
    # Get number of grants, IAP protection threshold and fairshare per channel 
    if num_unsatisfied_grants > 0:
      # algorithm to calculate interference within IAPBW using EIRP obtained for all 
      # the grants through application of IAP

      # Initialize list of aggregate interference from all the grants 
      # ( including grants from managing and peer SAS )
      aggr_interf = [0] * len(channels)
      # Initialize list of aggregate interference from all the grants 
      # ( including only grants from managing SAS )
      asas_interf = [0] * len(channels)

      num_unsatisfied_grants_channel = []
      iap_threshold_channel = []
      fairshare_channel = []

      for index, channel in enumerate(channels):
        # Get protection constraint over 5MHz channel range
        channel_constraint = interf.ProtectionConstraint(latitude=protection_point[1],
                               longitude=protection_point[0], low_frequency=channel[0],
                               high_frequency=channel[1], entity_type=protection_ent_type)

        # Identify CBSD grants overlapping with frequency range of the protection entity 
        # in the neighborhood of the protection point and channel
        channel_neighborhood_grants = interf.findOverlappingGrants(
                                        neighborhood_grants, channel_constraint)

        num_unsatisfied_grants_channel.append(len(channel_neighborhood_grants))
        
        # Set interference quota for protection_point, channel combination
        # Calculate Roll of Attenuation for ESC Sensor Protection entity
        if protection_ent_type is interf.ProtectedEntityType.ESC:
          if channel[0] >= 3650.e6:
            center_freq = (channel[0] + channel[1]) / 2
            iap_threshold_channel.append(interf.dbToLinear(interf.linearToDb(threshold) - 
              (2.5 + ((center_freq - interf.ESC_CH21_CF_HZ) / MHZ))))
          else:
            iap_threshold_channel.append(threshold)
        else:
          iap_threshold_channel.append(threshold)

        # calculate the fair share per channel based on unsatisfied grants
        if num_unsatisfied_grants_channel[index] > 0:
          fairshare_channel.append(float(iap_threshold_channel[index]) / 
            num_unsatisfied_grants_channel[index] )
        else:
          fairshare_channel.append(0)

      # List of grants initialized with max EIRP
      grants_eirp = [grant.max_eirp for grant in neighborhood_grants]
      
      # Initialize list of grants_satisfied to False
      grants_satisfied = [False] * num_unsatisfied_grants
      
      while num_unsatisfied_grants > 0:

        for g_idx, grant in enumerate(neighborhood_grants):

          if grants_satisfied[g_idx] is False:
            grant_good_over_all_channels = True

            # Set to True if grant frequency range overlaps with a channel, 
            # otherwise, set to False
            grants_overlap_flag = [False] * len(channels)

            # Initialize interference per channel list 
            interference_list = [0] * len(channels) 

            for idx, channel in enumerate(channels):
              # check if grant interferes with protection point, channel
              grant_overlap_check = interf.grantFrequencyOverlapCheck(grant, 
                                           channel[0], channel[1], protection_ent_type)
          
              # Update True or False for a particular channel index
              grants_overlap_flag[idx] = grant_overlap_check 
              # if grant overlaps with protection point over channel 
              if grant_overlap_check:
                # Compute interference grant causes to protection point over channel
                interference = interf.dbToLinear(interf.computeInterference(grant, 
                                 grants_eirp[g_idx], channel_constraint, fss_info, 
                                 esc_antenna_info, region_type))
                # if calculated interference is more than fair share of
                # interference to which the grants are entitled then 
                # grant is considered unsatisfied
                if interference > fairshare_channel[idx]:
                  grant_good_over_all_channels = False
                  break
                else:
                  interference_list[idx] = interference
       
          if grant_good_over_all_channels is True:
            grants_satisfied[g_idx] = True
            if num_unsatisfied_grants > 0:
              num_unsatisfied_grants = num_unsatisfied_grants - 1
            for ch_idx, g_ch_flag in enumerate(grants_overlap_flag):
              # Grant interferes with protection point over channel 
              if g_ch_flag:
                iap_threshold_channel[ch_idx] = iap_threshold_channel[ch_idx] - \
                                                  interference_list[ch_idx]
                num_unsatisfied_grants_channel[ch_idx] = num_unsatisfied_grants_channel[ch_idx] - 1
                # Re-calculate fairshare for a channel
                if num_unsatisfied_grants_channel[ch_idx] > 0:
                  fairshare_channel[ch_idx] = float (iap_threshold_channel[ch_idx]) /  \
                                         num_unsatisfied_grants_channel[ch_idx]
              if grant.is_managed_grant is True:
                asas_interf[ch_idx] += interference_list[ch_idx]
              
              aggr_interf[ch_idx] += interference_list[ch_idx]
          else:
            grants_eirp[g_idx] = grants_eirp[g_idx] - 1
     
    # Update aggregate interference and asas_interference from all the grants 
    # at a protection point, channel
    for j, interf_val in enumerate(aggr_interf):
      asas_interference.UpdateAggregateInterferenceInfo(protection_point[1],
        protection_point[0], asas_interf[j])
      aggregate_interference.UpdateAggregateInterferenceInfo(protection_point[1],
        protection_point[0], interf_val)


def performIapForEsc(protected_entity, sas_uut_fad_object, sas_th_fad_objects):
  """ Compute post IAP interference margin for ESC 
  
  IAP algorithm is run over ESC passband 3550-3660MHz for Category A CBSDs and 
  3550-3680MHz for Category B CBSDs

  Args:
    protected_entity: Protected entity of type ESC
    sas_uut_fad_object: FAD object from SAS UUT
    sas_th_fad_object: a list of FAD objects from SAS Test Harness
   Returns:
    ap_iap_ref: post IAP allowed interference in the format of 
    {latitude : {longitude : [interference(mW/IAPBW), interference(mW/IAPBW)]}}
  """
  esc_thresh_q = THRESH_ESC_DBM_PER_RBW + \
                   + 10*np.log10(IAPBW_HZ / ESC_RBW_HZ)
  # Actual protection threshold used for IAP - calculated by applying
  # a pre-defined Pre-IAP headroom (Mg) at each protection threshold(Q)
  esc_iap_threshold = interf.dbToLinear(esc_thresh_q - MARGIN_ESC_DB)

  grant_objects = interf.getGrantObjectsFromFAD(sas_uut_fad_object, sas_th_fad_objects)

  # Get number of SAS 
  num_sas = len(sas_th_fad_objects) + 1

  # Get the protection point of the ESC
  esc_point = protected_entity['installationParam']
  protection_point = (esc_point['longitude'], esc_point['latitude'])

  # Get azimuth radiation pattern
  ant_pattern = esc_point['azimuthRadiationPattern']
  ant_pattern = sorted([(pat['angle'], pat['gain']) for pat in ant_pattern])
  angles, gains = zip(*ant_pattern)
  if angles != tuple(range(360)):
      raise ValueError('ESC pattern inconsistent')
  ant_gain_pattern = np.array(gains)

  # Get ESC antenna information
  esc_antenna_info = interf.EscInformation(antenna_height=esc_point['height'],
                       antenna_azimuth=esc_point['antennaAzimuth'],
                       antenna_gain_pattern=ant_gain_pattern)

  # Get ESC passband 3550-3680 MHz protection channels
  protection_channels = interf.getProtectedChannels(interf.ESC_LOW_FREQ_HZ, 
                          interf.ESC_HIGH_FREQ_HZ)

  logging.debug('$$$$ Calling ESC Protection $$$$')
  # ESC algorithm
  asas_interference = interf.getInterferenceObject()
  aggregate_interference = interf.getInterferenceObject()
  iapPointConstraint(protection_point, protection_channels, 
    interf.ESC_LOW_FREQ_HZ, interf.ESC_HIGH_FREQ_HZ, 
    grant_objects, None, esc_antenna_info, None, 
    esc_iap_threshold, interf.ProtectedEntityType.ESC,
    asas_interference, aggregate_interference)
  
  ap_iap_ref = calculatePostIapAggregateInterference(esc_iap_threshold, num_sas,
                 asas_interference, aggregate_interference) 
  return ap_iap_ref 

def performIapForGwpz(protected_entity, sas_uut_fad_object, sas_th_fad_objects, pool=None):
  """Compute post IAP interference margin for GWPZ incumbent type

  Routine to get protection points within GWPZ protection area and perform 
  IAP algorithm on each protection point 

  Args:
    protected_entity: Protected entity of type GWPZ
    sas_uut_fad_object: FAD object from SAS UUT
    sas_th_fad_object: a list of FAD objects from SAS Test Harness
    pool: object of type Pool to distribute execution of a iapPointConstraint
    function across multiple input values, distributing the input data across
    processes
   Returns:
    ap_iap_ref: post IAP allowed interference in the format of 
    {latitude : {longitude : [interference(mW/IAPBW), interference(mW/IAPBW)]}}
  """
  gwpz_thresh_q = THRESH_GWPZ_DBM_PER_RBW + \
                    10*np.log10(IAPBW_HZ / GWPZ_RBW_HZ)
  # Actual protection threshold used for IAP - calculated by applying
  # a pre-defined Pre-IAP headroom (Mg) at each protection threshold(Q)
  gwpz_iap_threshold = interf.dbToLinear(gwpz_thresh_q - MARGIN_GWPZ_DB)

  grant_objects = interf.getGrantObjectsFromFAD(sas_uut_fad_object, sas_th_fad_objects)

  # Get number of SAS 
  num_sas = len(sas_th_fad_objects) + 1

  logging.debug('$$$$ Getting GRID points for GWPZ Protection Area $$$$')
  # Get Fine Grid Points for a GWPZ protection area
  protection_points = utils.GridPolygon(protected_entity['zone']['features'][0]['geometry'], 2)

  gwpz_freq_range = protected_entity['deploymentParam']\
                      ['operationParam']['operationFrequencyRange']
  gwpz_low_freq = gwpz_freq_range['lowFrequency']
  gwpz_high_freq = gwpz_freq_range['highFrequency']

  gwpz_region = protected_entity['zone']['features'][0]\
                                 ['properties']['clutter']

  # Get channels over which area incumbent needs partial/full protection
  protection_channels = interf.getProtectedChannels(gwpz_low_freq, gwpz_high_freq)
  
  if not pool:
    # Apply IAP for each protection constraint with a pool of parallel processes.
    pool = Pool(processes=min(multiprocessing.cpu_count(), len(protection_points)))

  asas_interference = interf.getInterferenceObject()
  aggregate_interference = interf.getInterferenceObject()
  logging.debug('$$$$ Calling GWPZ Protection $$$$')
  iapPoint = partial(iapPointConstraint, channels=protection_channels, 
                     low_freq=gwpz_low_freq, high_freq=gwpz_high_freq, 
                     grant_objects=grant_objects, fss_info=None, 
                     esc_antenna_info=None, region_type=gwpz_region,
                     threshold=gwpz_iap_threshold, 
                     protection_ent_type=interf.ProtectedEntityType.GWPZ_AREA,
                     asas_interference=asas_interference, 
                     aggregate_interference=aggregate_interference) 

  pool.map(iapPoint, protection_points)

  ap_iap_ref = calculatePostIapAggregateInterference(gwpz_iap_threshold, num_sas,
                 asas_interference, aggregate_interference) 
  return ap_iap_ref 


def performIapForPpa(protected_entity, sas_uut_fad_object, sas_th_fad_objects, 
      pal_records, pool=None):
  """Compute post IAP interference margin for PPA incumbent type

  Routine to get protection points within PPA protection area and perform 
  IAP algorithm on each protection point

  Args:
    protected_entity: Protected entity of type PPA
    sas_uut_fad_object: FAD object from SAS UUT
    sas_th_fad_object: a list of FAD objects from SAS Test Harness
    pal_records: PAL records associated with a PPA protection area
    pool: object of type Pool to distribute execution of a iapPointConstraint
    function across multiple input values, distributing the input data across
    processes
   Returns:
    ap_iap_ref: post IAP allowed interference in the format of 
    {latitude : {longitude : [interference(mW/IAPBW), interference(mW/IAPBW)]}}
  """
  ppa_thresh_q = THRESH_PPA_DBM_PER_RBW + \
                   + 10*np.log10(IAPBW_HZ / PPA_RBW_HZ)
  # Actual protection threshold used for IAP - calculated by applying
  # a pre-defined Pre-IAP headroom (Mg) at each protection threshold(Q)
  ppa_iap_threshold = interf.dbToLinear(ppa_thresh_q - MARGIN_PPA_DB)

  grant_objects = interf.getGrantObjectsFromFAD(sas_uut_fad_object, 
                    sas_th_fad_objects, protected_entity)

  # Get number of SAS 
  num_sas = len(sas_th_fad_objects) + 1

  logging.debug('$$$$ Getting GRID points for PPA Protection Area $$$$')

  # Get Fine Grid Points for a PPA protection area
  protection_points = utils.GridPolygon(protected_entity['zone']['features'][0]['geometry'], 2)

  # Get the region type of the PPA protection area
  ppa_region = protected_entity['ppaInfo']['ppaRegionType']

  # Find the PAL records for the PAL_IDs defined in PPA records
  ppa_pal_ids = protected_entity['ppaInfo']['palId']
 
  matching_pal_records = [pr for pr in pal_records if pr['palId'] == ppa_pal_ids[0]]
  if not matching_pal_records:
    raise ValueError('No matching PAL record, please check input')

  pal_record = matching_pal_records[0]

  # Get the frequencies from the PAL records
  ppa_freq_range = pal_record['channelAssignment']['primaryAssignment']
  ppa_low_freq = ppa_freq_range['lowFrequency']
  ppa_high_freq = ppa_freq_range['highFrequency']

  # Get channels over which area incumbent needs partial/full protection
  protection_channels = interf.getProtectedChannels(ppa_low_freq, ppa_high_freq)
  
  # Apply IAP for each protection constraint with a pool of parallel 
  # processes.
  logging.debug('$$$$ Calling PPA Protection $$$$')
   
  if not pool:
    pool = Pool(processes=min(multiprocessing.cpu_count(), 
                               len(protection_points)))
  asas_interference = interf.getInterferenceObject()
  aggregate_interference = interf.getInterferenceObject()
  iapPoint = partial(iapPointConstraint, channels=protection_channels, 
                     low_freq=ppa_low_freq, high_freq=ppa_high_freq, 
                     grant_objects=grant_objects, fss_info=None, 
                     esc_antenna_info=None, region_type=ppa_region,
                     threshold=ppa_iap_threshold, 
                     protection_ent_type=interf.ProtectedEntityType.PPA_AREA,
                     asas_interference=asas_interference, 
                     aggregate_interference=aggregate_interference) 

  pool.map(iapPoint, protection_points)

  ap_iap_ref = calculatePostIapAggregateInterference(ppa_iap_threshold, num_sas,
                 asas_interference, aggregate_interference) 
  return ap_iap_ref 

def performIapForFssCochannel(protected_entity, sas_uut_fad_object, sas_th_fad_objects):
  """Compute post IAP interference margin for FSS Co-channel incumbent type

  FSS protection is provided over co-channel pass band

  Args:
    protected_entity: Protected entity of type FSS co-channel
    sas_uut_fad_object: FAD object from SAS UUT
    sas_th_fad_object: a list of FAD objects from SAS Test Harness
   Returns:
    ap_iap_ref: post IAP allowed interference in the format of 
    {latitude : {longitude : [interference(mW/IAPBW), interference(mW/IAPBW)]}}
  """
  fss_cochannel_thresh_q = THRESH_FSS_CO_CHANNEL_DBM_PER_RBW\
                          + 10*np.log10(IAPBW_HZ / FSS_RBW_HZ)
  # Actual protection threshold used for IAP - calculated by applying
  # a pre-defined Pre-IAP headroom (Mg) at each protection threshold(Q)
  fss_cochannel_iap_threshold = interf.dbToLinear(fss_cochannel_thresh_q -
                              MARGIN_FSS_CO_CHANNEL_DB)

  grant_objects = interf.getGrantObjectsFromFAD(sas_uut_fad_object, sas_th_fad_objects)

  # Get number of SAS 
  num_sas = len(sas_th_fad_objects) + 1

  # Get the protection point of the FSS
  fss_point = protected_entity['record']['deploymentParam'][0]['installationParam']
  protection_point = (fss_point['longitude'], fss_point['latitude'])

  # Get the frequency range of the FSS
  fss_freq_range = protected_entity['record']['deploymentParam'][0]\
      ['operationParam']['operationFrequencyRange']
  fss_low_freq = fss_freq_range['lowFrequency']
  fss_high_freq = fss_freq_range['highFrequency']

  # Get FSS information
  fss_info = interf.FssInformation(height_agl=fss_point['height'],
               max_gain_dbi=fss_point['antennaGain'],
               pointing_azimuth=fss_point['antennaAzimuth'],
               pointing_elevation=fss_point['antennaDowntilt'])

  # Get channels for co-channel CBSDs
  if fss_high_freq < interf.CBRS_HIGH_FREQ_HZ:
    protection_channels = interf.getProtectedChannels(fss_low_freq, fss_high_freq)
  else:
    protection_channels = interf.getProtectedChannels(fss_low_freq, interf.CBRS_HIGH_FREQ_HZ)
  
  asas_interference = interf.getInterferenceObject()
  aggregate_interference = interf.getInterferenceObject()
  # FSS Co-channel algorithm
  logging.debug('$$$$ Calling FSS co-channel Protection $$$$')
  iapPointConstraint(protection_point, protection_channels, fss_low_freq,
    interf.CBRS_HIGH_FREQ_HZ, grant_objects, fss_info, None, 
    None, fss_cochannel_iap_threshold, 
    interf.ProtectedEntityType.FSS_CO_CHANNEL,
    asas_interference, aggregate_interference) 
  
  ap_iap_ref = calculatePostIapAggregateInterference(fss_cochannel_iap_threshold, num_sas,
                 asas_interference, aggregate_interference) 
  return ap_iap_ref 

def performIapForFssBlocking(protected_entity, sas_uut_fad_object, sas_th_fad_objects):
  """Compute post IAP interference margin for FSS Blocking incumbent type

  FSS protection is provided over blocking pass band

  Args:
    protected_entity: Protected entity of type PPA
    sas_uut_fad_object: FAD object from SAS UUT
    sas_th_fad_object: a list of FAD objects from SAS Test Harness
   Returns:
    ap_iap_ref: post IAP allowed interference in the format of 
    {latitude : {longitude : [interference(mW/IAPBW), interference(mW/IAPBW)]}}
  """
  # Actual protection threshold used for IAP - calculated by applying
  # a pre-defined Pre-IAP headroom (Mg) at each protection threshold(Q)
  fss_blocking_iap_threshold = interf.dbToLinear(THRESH_FSS_BLOCKING_DBM_PER_RBW -
                              MARGIN_FSS_BLOCKING_DB)

  grant_objects = interf.getGrantObjectsFromFAD(sas_uut_fad_object, sas_th_fad_objects)

  # Get number of SAS 
  num_sas = len(sas_th_fad_objects) + 1

  # Get FSS T&C Flag value
  fss_ttc_flag = protected_entity['ttc']

  # Get the protection point of the FSS
  fss_point = protected_entity['record']['deploymentParam'][0]['installationParam']
  protection_point = (fss_point['longitude'], fss_point['latitude'])

  # Get the frequency range of the FSS
  fss_freq_range = protected_entity['record']['deploymentParam'][0]\
      ['operationParam']['operationFrequencyRange']
  fss_low_freq = fss_freq_range['lowFrequency']
  fss_high_freq = fss_freq_range['highFrequency']

  # Get FSS information
  fss_info = interf.FssInformation(height_agl=fss_point['height'],
               max_gain_dbi=fss_point['antennaGain'],
               pointing_azimuth=fss_point['antennaAzimuth'],
               pointing_elevation=fss_point['antennaDowntilt'])

  # FSS Passband is between 3700 and 4200 and TT&C flag is set to FALSE
  if (fss_low_freq >= interf.FSS_TTC_LOW_FREQ_HZ and 
        fss_high_freq <= interf.FSS_TTC_HIGH_FREQ_HZ and
        fss_ttc_flag is False):
    raise Exception("IAP for FSS not applied for FSS Pass band 3700 to 4200 "  
        "and TT&C flag set to false, please check the inputs.")
  else:
    logging.debug('$$$$ Calling FSS blocking Protection $$$$')
    # 5MHz channelization is not required for Blocking protection
    protection_channels = [(interf.CBRS_LOW_FREQ_HZ, fss_low_freq)]
    asas_interference = interf.getInterferenceObject()
    aggregate_interference = interf.getInterferenceObject()
    iapPointConstraint(protection_point, protection_channels, 
      interf.CBRS_LOW_FREQ_HZ, fss_low_freq, grant_objects, 
      fss_info, None, None, fss_blocking_iap_threshold, 
      interf.ProtectedEntityType.FSS_BLOCKING,
      asas_interference, aggregate_interference) 

  ap_iap_ref = calculatePostIapAggregateInterference(fss_blocking_iap_threshold, num_sas, 
                 asas_interference, aggregate_interference) 
  return ap_iap_ref 


def calculatePostIapAggregateInterference(q_p, num_sas, asas_interference, 
      aggregate_interference):
  """Compute post IAP allowed aggregate interference  

  Routine to calculate aggregate interference from all the CBSDs managed by the
  SAS at protected entity.

  Args:
    q_p: Pre IAP threshold value for protection type(mW)
    num_sas: number of SASs in the peer group
    asas_interference: dictionary in the format of 
    {latitude : {longitude : [asas_p(mW/IAPBW), asas_p(mW/IAPBW)]}}, where
    asas_p is aggregate interference calculated within IAPBW by managing SAS using 
    the EIRP obtained from IAP results for that point p for CBSDs managed by the 
    managing SAS. Only grants overlapping IAPBW are used in the calculation
    aggregate_interference: dictionary in the format of 
    {latitude : {longitude : [a_p(mW/IAPBW), a_p(mW/IAPBW)]}}, where
    a_p is aggregate interference calculated within IAPBW by managing SAS using 
    the EIRP obtained by all CBSDs (including the CBSDs managed by other SASs) 
    through application of IAP for protected entity p. Only grants overlapping
    IAPBW are used in the calculation
   Returns:
    ap_iap_ref: post IAP allowed interference in the format of 
    {latitude : {longitude : [interference(mW/IAPBW), interference(mW/IAPBW)]}}
  """
  ap_iap_ref = {}
  # Extract dictionary from DictProxy object using _getvalue object method
  asas_info = asas_interference.GetAggregateInterferenceInfo()._getvalue()
  a_p_info = aggregate_interference.GetAggregateInterferenceInfo()._getvalue()
  
  # Compute AP_IAP_Ref 
  for latitude, a_p_ch in a_p_info.items():
    for longitude, a_p_list in a_p_ch.items():
      ap_iap_ref[latitude] = {}
      ap_iap_ref[latitude][longitude] = []
      for index, a_p in enumerate(a_p_list):
          ap_iap_ref[latitude][longitude].append(((q_p - a_p) / num_sas) + 
                              asas_info[latitude][longitude][index])
  
  return ap_iap_ref
