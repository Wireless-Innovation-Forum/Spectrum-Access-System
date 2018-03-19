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
  Aggregate Interference Calculations Reference Model[R2-SGN-12].
  Based on WINNF-TS-0112, Version V1.4.1, 16 January 2018.

  This model provides the functions to calculate the aggregate interference for
  the protection constrains of FSS, ESC, GWPZ and PPA.

  The main routines are:

    calculateAggregateInterferenceForFss
    calculateAggregateInterferenceForEsc
    calculateAggregateInterferenceForGwpz
    calculateAggregateInterferenceForPpa

  The routines returns a dictionary containing key as protection constraints 
  (lat, long, low_freq, high_freq, entity_type) and value as the aggregate 
  interference value in dBm for each of the constraints.
==================================================================================
"""

import numpy as np 
import logging
from reference_models.interference import interference as interf
from reference_models.geo import utils

def convertAndSumInterference(cbsd_interference_list):
  """ Converts interference in dBm to mW to calculate aggregate interference """
  
  interferences_in_mw = [interf.dbToLinear(cbsd_interference) 
      for cbsd_interference in cbsd_interference_list]

  aggregate_interference_in_mw = np.sum(interferences_in_mw)

  return interf.linearToDb(aggregate_interference_in_mw)

def aggregateInterferenceForPoint(protection_point, channels, low_freq, high_freq, 
      grant_objects, fss_info, esc_antenna_info, protection_ent_type, 
      region_type="SUBURBAN"):
  """Algorithm to compute aggregate interference for protection point
  
  This method is invoked to calculate aggregate interference for FSS(Co-channel 
  passband) and ESC protection points.It is also invoked for protection points 
  within PPA and GWPZ protection areas.

  Args:
   protection_point: Protection point inside protection area
   channels: Channels over which reference incumbent needs protection
   low_freq: Low frequency of protection constraint (Hz)
   high_freq: High frequency of protection constraint (Hz)
   grant_objects: A list of grant requests, each one being a namedtuple
                  containing grant information
   fss_info: Contains information on antenna height and weights on the tangent
             and perpendicular components.
   esc_antenna_info: Contains information on ESC antenna height, azimuth,
                     gain and pattern gain 
   protection_ent_type: An enum member of class ProtectedEntityType
   region_type: Region type of the protection point
   Returns:
      Aggregate interference for a protection constraint(dBm)
  """

  aggregate_interference = {}

  for channel in channels:
    # Get protection constraint over 5MHz channel range
    protection_constraint = interf.ProtectionConstraint(latitude=protection_point[0],
                              longitude=protection_point[1], low_frequency=channel[0],
                              high_frequency=channel[1], entity_type=protection_ent_type)

    # Identify CBSD grants in the neighborhood of the protection point
    # and channel
    neighborhood_grants = interf.findOverlappingGrantsInsideNeighborhood(
                            grant_objects, protection_constraint)

    if len(neighborhood_grants) is 0:
      continue

    cbsd_interference_list = []
    # Compute interference grant causes to protection point over channel 
    for i, grant in enumerate(neighborhood_grants):

      # Compute interference at FSS incumbent type
      if protection_ent_type is interf.ProtectedEntityType.FSS_CO_CHANNEL or\
        protection_ent_type is interf.ProtectedEntityType.FSS_BLOCKING:
         cbsd_interference = interf.computeInterferenceFss(grant, 
                               protection_constraint, fss_info, grant.max_eirp)
         cbsd_interference_list.append(cbsd_interference)

      # Compute interference at ESC incumbent type
      elif protection_ent_type is interf.ProtectedEntityType.ESC_CAT_A or\
         protection_ent_type is interf.ProtectedEntityType.ESC_CAT_B:
        cbsd_interference = interf.computeInterferenceEsc(grant, 
                              protection_constraint, esc_antenna_info, 
                              grant.max_eirp)
        cbsd_interference_list.append(cbsd_interference)

      else:
        # Compute interference at GWPZ or PPA incumbent types
        cbsd_interference = interf.computeInterferencePpaGwpzPoint(grant, 
                              protection_constraint, interf.GWPZ_PPA_HEIGHT, 
                              grant.max_eirp, region_type)
        cbsd_interference_list.append(cbsd_interference)
    
    # Update aggregate interference for a protection constraint
    aggregate_interference[protection_constraint] =\
              convertAndSumInterference(cbsd_interference_list)

  return aggregate_interference

def aggrFSSBlockingConstraint(protection_point, low_freq, high_freq, 
                              grant_objects, fss_info, protection_ent_type):
  """ Calculates aggregate interference from CBSDs in the neighborhood of 
  FSS Blocking pass band
  """ 

  # Assign values to the protection constraint
  constraint = interf.ProtectionConstraint(latitude=protection_point[0],
                 longitude=protection_point[1], low_frequency=low_freq,
                 high_frequency=high_freq, entity_type=protection_ent_type)

  # Identify CBSD grants in the neighborhood of the protection constraint
  neighborhood_grants = interf.findOverlappingGrantsInsideNeighborhood(grant_objects, constraint)

  cbsd_interference_list = []
  aggregate_interference = {}

  # Get interference caused by each grant
  for grant in neighborhood_grants:
    cbsd_interference = interf.computeInterferenceFssBlocking(grant, constraint,
                          fss_info, grant.max_eirp)
    cbsd_interference_list.append(cbsd_interference)

  aggregate_interference[constraint] = convertAndSumInterference(cbsd_interference_list)
  return aggregate_interference


def calculateAggregateInterferenceForFss(fss_record, cbsd_list):
  """Calculates aggregate interference for FSS.
  
  Calculates aggregate interference for each protection constraint in the FSS
  based on the interferences caused by CBSD's grants in the neighborhood of
  the FSS protection entity.

  Args:
    fss_record: FSS protection entity
    cbsd_list: list of CBSD objects containing RegistrationRequests and GrantRequests
  Returns:
    Aggregate interference to FSS in the dictionary format,where the key is a tuple. 
    {(latitude, longitude, low_frequency, high_frequency,entity_type):
    aggregate_interference(dBm)}
  """
  grant_list = interf.getAllGrantInformationFromCbsdDataDump(cbsd_list)
  # Get FSS T&C Flag value
  fss_weight1 = fss_record['deploymentParam'][0]['weight1']
  fss_weight2 = fss_record['deploymentParam'][0]['weight2']

  fss_ttc_flag = fss_record['deploymentParam'][0]['ttc']
  # Get the protection point of the FSS
  fss_point = fss_record['deploymentParam'][0]['installationParam']
  protection_point = (fss_point['latitude'], fss_point['longitude'])

  # Get the frequency range of the FSS
  fss_freq_range = fss_record['deploymentParam'][0]['operationParam']['operationFrequencyRange']
  fss_low_freq = fss_freq_range['lowFrequency']
  fss_high_freq = fss_freq_range['highFrequency']

  # Get FSS information
  fss_info = interf.FssProtectionPoint(latitude=fss_point['latitude'], 
               longitude=fss_point['longitude'],
               height_agl=fss_point['height'],
               max_gain_dbi=fss_point['antennaGain'],
               pointing_azimuth=fss_point['antennaAzimuth'],
               pointing_elevation=fss_point['antennaElevationAngle'],
               weight_1=fss_weight1, weight_2=fss_weight2)

  aggregate_interference = {}
  # FSS Passband is between 3600 and 4200
  if(fss_low_freq >= interf.FSS_LOW_FREQ_HZ and 
         fss_low_freq < interf.CBRS_HIGH_FREQ_HZ):

    # Get channels for co-channel CBSDs
    protection_channels = interf.getProtectedChannels(fss_low_freq, interf.CBRS_HIGH_FREQ_HZ)
    aggregate_interference = aggregateInterferenceForPoint(protection_point, 
                               protection_channels, fss_low_freq, 
                               interf.CBRS_HIGH_FREQ_HZ, grant_list, fss_info, 
                               None, interf.ProtectedEntityType.FSS_CO_CHANNEL)

    # 5MHz channelization is not required for Blocking protection
    # FSS in-band blocking algorithm
    aggregate_interference = aggrFSSBlockingConstraint(
      protection_point, interf.CBRS_LOW_FREQ_HZ, fss_low_freq, 
      grant_list, fss_info, interf.ProtectedEntityType.FSS_BLOCKING)

  # FSS Passband is between 3700 and 4200 and TT&C flag is set to TRUE
  elif(fss_low_freq >= 3700 and fss_high_freq <= 4200) and\
                                (fss_ttc_flag is True):
    # 5MHz channelization is not required for Blocking protection
    # FSS TT&C Blocking Algorithm
    aggregate_interference = aggrFSSBlockingConstraint(
      protection_point, interf.CBRS_LOW_FREQ_HZ, fss_low_freq, 
      grant_list, fss_info, interf.ProtectedEntityType.FSS_BLOCKING)

  elif(fss_low_freq >= 3700 and fss_high_freq <= 4200) and\
                             (fss_ttc_flag is False):
    logging.debug('Aggregate interference not calculated for FSS Pass band'
    '3700 to 4200 and TT&C flag set to false')
  return aggregate_interference


def calculateAggregateInterferenceForEsc(esc_record, cbsd_list):
  """Calculates aggregate interference for ESC.
  
  Calculates aggregate interference for each protection constraint in the ESC
  based on the interferences caused by CBSD's grants in the neighborhood of
  the ESC protection entity.
  
  Args:
    esc_record: ESC protection entity
    cbsd_list: list of CBSD objects containing RegistrationRequests and GrantRequests
  Returns:
    Aggregate interference to ESC in the dictionary format,where the key is a tuple. 
    {(latitude, longitude, low_frequency, high_frequency,entity_type):
    aggregate_interference(dBm)}
  """

  grant_list = interf.getAllGrantInformationFromCbsdDataDump(cbsd_list)

  # Get the protection point of the ESC
  esc_point = esc_record['installationParam']
  protection_point = (esc_point['latitude'], esc_point['longitude'])

  # Get azimuth radiation pattern
  ant_pattern = esc_point['azimuthRadiationPattern']

  # Initialize array of size length of ant_pattern list
  ant_pattern_gain = np.arange(len(ant_pattern))
  for i, pattern in enumerate(ant_pattern):
    ant_pattern_gain[i] = pattern['gain']

  # Get ESC antenna information
  esc_antenna_info = interf.EscInformation(antenna_height=esc_point['height'],
                       antenna_azimuth=esc_point['antennaAzimuth'],
                       antenna_gain=esc_point['antennaGain'],
                       antenna_pattern_gain=ant_pattern_gain)

  # ESC Category A CBSDs between 3550 - 3660 MHz within 40 km
  protection_channels = interf.getProtectedChannels(interf.ESC_CAT_A_LOW_FREQ_HZ, 
                          interf.ESC_CAT_A_HIGH_FREQ_HZ)
  aggregate_interference = aggregateInterferenceForPoint(protection_point, 
                             protection_channels, interf.ESC_CAT_A_LOW_FREQ_HZ, 
                             interf.ESC_CAT_A_HIGH_FREQ_HZ, grant_list, None, 
                             esc_antenna_info, interf.ProtectedEntityType.ESC_CAT_A)
  # ESC Category B CBSDs between 3550 - 3680 MHz within 80 km
  protection_channels = interf.getProtectedChannels(interf.ESC_CAT_B_LOW_FREQ_HZ, 
                          interf.ESC_CAT_B_HIGH_FREQ_HZ)
  aggregate_interference = aggregateInterferenceForPoint(protection_point, 
                             protection_channels, interf.ESC_CAT_B_LOW_FREQ_HZ, 
                             interf.ESC_CAT_B_HIGH_FREQ_HZ, grant_list, None, 
                             esc_antenna_info, interf.ProtectedEntityType.ESC_CAT_B)

  return aggregate_interference


def calculateAggregateInterferenceForGwpz(gwpz_record, cbsd_list):
  """Calculates aggregate interference for GWPZ.
  
  Calculates aggregate interference for each protection constraint in the GWPZ
  based on the interferences caused by CBSD's grants in the neighborhood of
  the GWPZ protection entity.

  Args:
    gwpz_record: GWPZ protection entity
    cbsd_list: list of CBSD objects containing RegistrationRequests and GrantRequests
  Returns:
    Aggregate interference to GWPZ in the dictionary format,where the key is a tuple. 
    {(latitude, longitude, low_frequency, high_frequency,entity_type):
    aggregate_interference(dBm)}
  """

  grant_list = interf.getAllGrantInformationFromCbsdDataDump(cbsd_list)
  gwpz_region = gwpz_record['zone']['features'][0]['properties']['gwpzRegionType']

  # Get Fine Grid Points for a GWPZ protection area
  protection_points = utils.GridPolygon(gwpz_record)
  gwpz_freq_range = gwpz_record['deploymentParam']['operationParam']['operationFrequencyRange']
  gwpz_low_freq = gwpz_freq_range['lowFrequency']
  gwpz_high_freq = gwpz_freq_range['highFrequency']

  # Get channels over which area incumbent needs partial/full protection
  protection_channels = interf.getProtectedChannels(gwpz_low_freq, gwpz_high_freq)
  for protection_point in protection_points:
    aggregate_interference = aggregateInterferenceForPoint(protection_point, 
                               protection_channels, gwpz_low_freq, 
                               gwpz_high_freq, grant_list, None, None, 
                               interf.ProtectedEntityType.GWPZ_AREA, 
                               gwpz_region)
  return aggregate_interference


def calculateAggregateInterferenceForPpa(ppa_record, pal_list, cbsd_list):
  """Calculates aggregate interference for PPA.
  
  Calculates aggregate interference for each protection constraint in the PPA
  based on the interferences caused by CBSD's grants in the neighborhood of
  the PPA protection entity.

  Args:
    ppa_record: PPA protection entity
    pal_list: list of PAL records
    cbsd_list: list of CBSD objects containing RegistrationRequests and GrantRequests
  Returns:
    Aggregate interference to PPA in the dictionary format,where the key is a tuple. 
    {(latitude, longitude, low_frequency, high_frequency,entity_type):
    aggregate_interference(dBm)}
  """
  grant_list = interf.getAllGrantInformationFromCbsdDataDump(cbsd_list)

  # Get Fine Grid Points for a PPA protection area
  protection_points = utils.GridPolygon(ppa_record)

  # Get the region type of the PPA protection area
  ppa_region = ppa_record['ppaInfo']['ppaRegionType']

  # Find the PAL records for the PAL_IDs defined in PPA records
  ppa_pal_ids = ppa_record['ppaInfo']['palId']
  
  for pal_record in pal_list:
    # Frequency range of all the PAL records within a PPA is same 
    # Considering frequency range from first PAL record for 
    # aggregate interference calculation
    if pal_record['palId'] == ppa_pal_ids[0]:
      # Get the frequencies from the PAL records
      ppa_freq_range = pal_record['channelAssignment']['primaryAssignment']
      ppa_low_freq = ppa_freq_range['lowFrequency']
      ppa_high_freq = ppa_freq_range['highFrequency']

      # Get channels over which area incumbent needs partial/full protection
      protection_channels = interf.getProtectedChannels(ppa_low_freq, ppa_high_freq)

      for protection_point in protection_points:
        aggregate_interference = aggregateInterferenceForPoint(protection_point, 
                                   protection_channels, ppa_low_freq, 
                                   ppa_high_freq, grant_list, None, None, 
                                   interf.ProtectedEntityType.PPA_AREA, 
                                   ppa_region)
      break
  return aggregate_interference
