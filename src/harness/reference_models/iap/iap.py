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

# ==================================================================================
# Iterative Allocation Process(IAP) Reference Model.
# Based on WINNF-TS-0112, Version V1.3.0-r5.0, 29 January 2018.

# ==================================================================================

import numpy as np
from operator import attrgetter, iadd
from collections import namedtuple
from multiprocessing import Pool
from enum import Enum
import sys
sys.path.append('../..')
from reference_models.iap import util
from reference_models.iap import compute
from reference_models.antenna import fss_pointing
from reference_models.examples import entities,example_fss_interference

# Define Post IAP Grant information, i.e., a tuple with named fields of
# 'eirp', 'interference'
PostIAPGrantInfo = namedtuple('PostIAPGrantInfo',
                          ['eirp', 'interference'])

# Global Post IAP managed grants container
post_iap_managed_grants = {}

# Global common leftover container (mW/RBW)
common_leftover = {}

# Global IAP Allowed Margin container (mW/RBW)
iap_allowed_margin = {}
 
# Global IAP protection threshold per IAPBW container (dBm/IAPBW)
threshold_per_iapbw = {} 

# Global headroom per reference bandwidth allocation container (mw/RBW) 
headroom_per_reference_bandwidth = {}

def iapAreaConstraint(protectionPoints, channels, lowFreq, highFreq, cbsdGrantReqs, threshold, protection_ent_type):
    """
    Return the interference margin list for a given protection constraint.
    Inputs:
        protectionPoints:     List of protection points inside protection area
        channels:             Channels over which area incumbent needs protection
        lowFreq:              low frequency of protection constraint (Hz)
        highFreq:             high frequency of protection constraint (Hz)
        cbsdGrantReqs:        a list of grant requests, each one being a dictionary
                              containing grant information
        threshold:            protection threshold (dBm/5 MHz)
        protection_ent_type:    Type of the protection entity
    Returns:                  the list of indices of grants on the move list for the
                              given protection constraint
    """
    # Initialize an empty list
    # List of fair share of interference to which grants are entitled for
    # a particular protectionPoint, channel
    fairshare_p_ch = []

    # List of interference quota at a particular protectionpoint, channel
    Q_p_ch = []

    # Number of grants to be considered at a particular protectionpoint, channel
    N_p_ch = []

    # For each point p_i in protectionPoints
    for protectionPoint in protectionPoints:
        # For each channel c_j in channels
        for channel in channels:
            # Set interference quota Q for protectionPoint, channel combination
            Q = threshold

            # Get protection constraint over 5MHz channel range
            ch_constraint = util.ProtectionConstraint(latitude=protectionPoint[0],
                                               longitude=protectionPoint[1],
                                               lowFrequency=channel[0],
                                               highFrequency=channel[1],
                                               entityType=protection_ent_type)

            # Identify Nc CBSD grants in the neighborhood of the protection point and channel
            Nc_grants = util.findGrantsInsideNeighborhood(cbsdGrantReqs, ch_constraint)

            N = len(Nc_grants)
            # calculate the fair share
            FS = Q / N

            fairshare_p_ch.append(FS)
            Q_p_ch.append(Q)
            N_p_ch.append(N)

    # For each point p_i in protectionPoints
    for protectionPoint in protectionPoints:

        # Find all the GAA grants inside 40kms of p_i
        # Assign values to the protection constraint
        constraint = util.ProtectionConstraint(latitude=protectionPoint[0],
                                          longitude=protectionPoint[1],
                                          lowFrequency=lowFreq,
                                          highFrequency=highFreq,
                                          entityType=protection_ent_type)

        # Identify Na CBSD grants in the neighborhood of the protection constraint
        Na_grants = util.findGrantsInsideNeighborhood(cbsdGrantReqs, constraint)

        num_grants = len(Na_grants)

        if num_grants:  # Number of CBSD grants that fully/partially interfere with protection point p
            # over at least one channel in channels
            # Empty list of final IAP EIRP assigned to the grant
            grantEirp = []
            # Empty list of power assigned indicator for the grant
            grant_powerAssigned = []
            
            for j, grant in enumerate(Na_grants):
                grant_powerAssigned.append(False)
                grantEirp.append(grant.maxEirp)

                while (True):
                    goodOverAllChannels = True
                    # Compute interference contributions of each grant to the protection constraint
                    # over 5MHz IAP channel
                    interference_list = []
                    # For each channel c_j in channels
                    for i, channel in enumerate(channels):
                        # Get protection constraint over 5MHz channel range
                        ch_constraint = util.ProtectionConstraint(latitude=protectionPoint[0],
                                                            longitude=protectionPoint[1],
                                                            lowFrequency=channel[0],
                                                            highFrequency=channel[1],
                                                            entityType=protection_ent_type)

                        # Get the fair share for a protection point and channel combination
                        fairshare = fairshare_p_ch[i]

                        # Compute interference grant causes to protection point over channel
                        interference = compute.computeInterference(grant, ch_constraint, 
                                                     GWPZ_PPA_HEIGHT, grantEirp[j])
                        interference = 10**(interference/10)
                        interference_list.append(interference)

                        # calculated interference exceeds fair share of interference to which the grants are entitled
                        if interference > fairshare:
                            goodOverAllChannels = False
                            break

                    if goodOverAllChannels is True:
                        grant_powerAssigned[j] = True
                        # For each channel c_j in channels
                        for i, channel in enumerate(channels):
                            # Remove satisfied CBSD grant from consideration
                            Q_p_ch[i] = Q_p_ch[i] - interference_list[i]
                            N_p_ch[i] = N_p_ch[i] - 1
                            if N_p_ch[i] == 0:
                                continue
                            else:
                                # re-calculate fair share
                                fairshare_p_ch[i] = Q_p_ch[i] / N_p_ch[i]

                            # Get protection constraint over 5MHz channel range
                            ch_constraint = util.ProtectionConstraint(latitude=protectionPoint[0],
                                                            longitude=protectionPoint[1],
                                                            lowFrequency=channel[0],
                                                            highFrequency=channel[1],
                                                            entityType=protection_ent_type)

                            common_leftover[ch_constraint] =  Q_p_ch[i]
                            # Update EIRP and Interference only if managed grant
                            if grant.isManagedGrant:
                               if grant.grantIndex not in post_iap_managed_grants:
                                  post_iap_managed_grants[grant.grantIndex] = {}
                               # Nested dictionary - contains dictionary of protection
                               # constraint over which grant extends
                               post_iap_grant = PostIAPGrantInfo(eirp=grantEirp[i],
                                                    interference=interference_list[i])
                               post_iap_managed_grants[grant.grantIndex][ch_constraint] = \
								post_iap_grant
                        else:
                            grantEirp[j] = grantEirp[j] - 1

                    if all(j is True for j in grant_powerAssigned):
                        break

        return

def iapPointConstraint(protectionPoint, channels, lowFreq, highFreq, cbsdGrantReqs,
                       hIncAnt, azIncAnt, gainIncAnt, fssEntities, threshold, protection_ent_type):
    """
    Return the interference margin list for a given protection constraint.
    Inputs:
     protectionPoints:   List of protection points inside protection area
     channels:           Channels over which reference incumbent needs protection
     lowFreq:            low frequency of protection constraint (Hz)
     highFreq:           high frequency of protection constraint (Hz)
     cbsdGrantReqs:           a list of grant requests, each one being a dictionary
                         containing grant information
     hIncAnt:            reference incumbent antenna height (m)
     threshold:          protection threshold (dBm/5 MHz)
     protection_ent_type:  an enum member of class ProtectionEntityType
    Returns:              Updates common_leftover and post_iap_managed_grants
                          global container with leftover margin, power and interference
    """
    
    # For each channel c_j in channels
    for channel in channels:
        # Set interference quota Q for protectionPoint, channel combination

        if protection_ent_type is util.ProtectionEntityType.ESC_CAT_A or\
            protection_ent_type is util.ProtectionEntityType.ESC_CAT_B:

            if channel[0] >= 3650000000.0:
                center_freq = (channel[0] + channel[1]) / 2
                Q = threshold - (2.5 + ((center_freq - util.ESC_CH21_CF) / util.ONE_MHZ))
                iap_allowed_margin['iapQEsc'+`channel`] = Q
            else:
                Q = threshold
        else:
            # FSS Co-channel threshold
            Q = threshold
        
        # Get protection constraint over 5MHz channel range
        ch_constraint = util.ProtectionConstraint(latitude=protectionPoint[0],\
                                           longitude=protectionPoint[1],\
                                           lowFrequency=channel[0],\
                                           highFrequency=channel[1],\
                                           entityType=protection_ent_type)
        
        # Identify Nc CBSD grants in the neighborhood of the protection point and channel
        Nc_grants = util.findGrantsInsideNeighborhood(cbsdGrantReqs, ch_constraint)
        N = len(Nc_grants)
        
        if N is 0:
           continue 
        # calculate the fair share
        FS = Q / N
         
        # Empty list of final IAP EIRP and interference assigned to the grant
        grantEirp = []
        interference_list = []
        
        # Initialize flag to 0 for all the grants
        grant_initialize_flag = []
        grant_initialize_flag[:N] = [0] * N

        # Initialize grant EIRP to maxEirp for all the grants
        for i, grant in enumerate(Nc_grants):
           grantEirp.append(grant.maxEirp)

        while (N):
            for i, grant in enumerate(Nc_grants):

                 if grant_initialize_flag[i] == 0:
                    # Compute interference grant causes to protection point over channel
                    if protection_ent_type is util.ProtectionEntityType.FSS_CO_CHA:
                       interference = compute.computeInterferenceFSS(grant, 
                             ch_constraint, hIncAnt, fssEntities, grantEirp[i])
                    else:
                       interference = compute.computeInterferenceESC(grant, ch_constraint, hIncAnt,
                                                              azIncAnt, grantEirp[i],gainIncAnt)
                    interference = 10**(interference/10)
                       
                    # calculated interference exceeds fair share of 
                    # interference to which the grants are entitled
                    if interference < FS:
                       interference_list.append(interference) 
                    else:
                       # interference exceeds fair share interference
                       # need to reduce EIRP of the grant
                       grant_initialize_flag[i] = 1
           

            for i, grant in enumerate(Nc_grants):
                 if grant_initialize_flag[i] == 0:
                   # Remove satisfied CBSD grant from consideration
                   Q = Q - interference_list[i]
                   N = N - 1
                   # re-calculate the fair share if number of grants are not zero
                   if N != 0:
                      FS = Q / N
                   # Update EIRP and Interference only if managed grant
                   if grant.isManagedGrant:
                      if grant.grantIndex not in post_iap_managed_grants:
                         post_iap_managed_grants[grant.grantIndex] = {}

                      # Nested dictionary - contains dictionary of protection
                      # constraint over which grant extends
                      post_iap_grant = PostIAPGrantInfo(eirp=grantEirp[i],
                                             interference=interference_list[i])
                      post_iap_managed_grants[grant.grantIndex][ch_constraint] =\
                                                         post_iap_grant
                 else:
                   grantEirp[i] = grantEirp[i] - 1
            common_leftover[ch_constraint] =  Q
    print '$$$$ FSS Co-Channel COMMON LEFTOVER$$$$$$$$\n'
    print common_leftover
    print 'Post IAP Managed Grant'
    print post_iap_managed_grants


def iapFSSBlockingConstraint(protectionPoint, lowFreq, highFreq, cbsdGrantReqs,
                                     hIncAnt, fssEntities, threshold, protection_ent_type):
    """
    Return the interference margin list for a given protection constraint.
    Inputs:
        protectionPoints:   List of protection points inside protection area
        channels:           Channels over which reference incumbent needs protection
        lowFreq:            low frequency of protection constraint (Hz)
        highFreq:           high frequency of protection constraint (Hz)
        cbsdGrantReqs:           a list of grant requests, each one being a dictionary
                            containing grant information
        hIncAnt:            reference incumbent antenna height (m)
        threshold:          protection threshold (dBm/5 MHz)
        protection_ent_type:  an enum member of class ProtectionEntityType
    Returns:                the list of indices of grants on the move list for the
                            given protection constraint
    """

    Q = threshold
        
    # Get protection constraint over 5MHz channel range
    constraint = util.ProtectionConstraint(latitude=protectionPoint[0],\
                                      longitude=protectionPoint[1],\
                                      lowFrequency=lowFreq,\
                                      highFrequency=highFreq,\
                                      entityType=protection_ent_type)
        
    # Identify Nc CBSD grants in the neighborhood of the protection point
    Nc_grants = util.findGrantsInsideNeighborhood(cbsdGrantReqs, constraint)
    N = len(Nc_grants)
        
    if N is 0:
       quit()
    # calculate the fair share
    FS = Q / N
         
    # Empty list of final IAP EIRP and interference assigned to the grant
    grantEirp = []
    interference_list = []
        
    # Initialize flag to 0 for all the grants
    grant_initialize_flag = []
    grant_initialize_flag[:N] = [0] * N

    # Initialize grant EIRP to maxEirp for all the grants
    for i, grant in enumerate(Nc_grants):
        grantEirp.append(grant.maxEirp)

    while (N):
        for i, grant in enumerate(Nc_grants):

           if grant_initialize_flag[i] == 0:
              # Compute interference grant causes to protection point over blocking 
              # frequency range
              interference = compute.computeInterferenceFSSBlocking(grant, 
                             constraint, hIncAnt, fssEntities, grantEirp[i])
              interference = 10**(interference/10)
                       
              # calculated interference exceeds fair share of 
              # interference to which the grants are entitled
              if interference < FS:
                 interference_list.append(interference) 
              else:
                 # interference exceeds fair share interference
                 # need to reduce EIRP of the grant
                 grant_initialize_flag[i] == 1
           

        for i, grant in enumerate(Nc_grants):
            if grant_initialize_flag[i] == 0:
               # Remove satisfied CBSD grant from consideration
               Q = Q - interference_list[i]
               N = N - 1
               # re-calculate the fair share if number of grants are not zero
               if N != 0:
                  FS = Q / N
               # Update EIRP and Interference only if managed grant
               if grant.isManagedGrant:
                  if grant.grantIndex not in post_iap_managed_grants:
                     post_iap_managed_grants[grant.grantIndex] = {}
                  # Nested dictionary - contains dictionary of protection
                  # constraint over which grant extends
                  post_iap_grant = PostIAPGrantInfo(eirp=grantEirp[i],
                                        interference=interference_list[i])
                  post_iap_managed_grants[grant.grantIndex][constraint] =\
                                                         post_iap_grant
            else:
               grantEirp[i] = grantEirp[i] - 1
        common_leftover[constraint] =  Q
    print '$$$$ COMMON LEFTOVER FSS Blocking $$$$$$$$\n'
    print common_leftover
    print 'Post IAP Managed Grant FSS Blocking '
    print post_iap_managed_grants


def performIAPforESC(protection_entity, grant_objects, iapQEsc):
    """
     Return the interference margin list for a given protection constraint.
     Inputs:
         protection_entity:  List of protection points inside protection area
         grant_objects:      a list of grant requests, each one being a dictionary
                             containing grant information
         iapQEsc:            Pre IAP threshold value for ESC incumbent type
     Returns:                the list of indices of grants on the move list for the
                             given protection constraint 
     """
     
    # Get the protection point of the ESC
    esc_point = protection_entity[0]['installationParam']
    protection_point = (esc_point['latitude'], esc_point['longitude'])

    # Get ESC Antenna Height
    antenna_height = esc_point['height']

    # Get ESC Antenna Azimuth
    antenna_azimuth = esc_point['antennaAzimuth']
    
    # Get ESC Antenna Gain
    ant_gain_esc = esc_point['antennaGain']

    pool = Pool(processes=min(util.NUM_OF_PROCESSES, len(protection_point)))

    # ESC Category A CBSDs between 3550 - 3660 MHz within 40 km
    protection_channels = util.getChannels(ESC_CAT_A_LOW_FREQ, ESC_CAT_A_HIGH_FREQ)

    # ESC algorithm
    iapPointConstraint(protectionPoint=protection_point,
            channels=protection_channels,
            lowFreq=ESC_CAT_A_LOW_FREQ,
            highFreq=ESC_CAT_A_HIGH_FREQ,
            cbsdGrantReqs=grant_objects,
            hIncAnt=antenna_height,
            azIncAnt=antenna_azimuth,
            gainIncAnt=ant_gain_esc,
            fssEntities=None,
            threshold=iapQEsc,
            protection_ent_type=util.ProtectionEntityType.ESC_CAT_A)

    # ESC Category B CBSDs between 3550 - 3680 MHz within 80 km
    protection_channels = util.getChannels(ESC_CAT_B_LOW_FREQ, ESC_CAT_B_HIGH_FREQ)

    iapPointConstraint(protectionPoint=protection_point,
            channels=protection_channels,
            lowFreq=ESC_CAT_B_LOW_FREQ,
            highFreq=ESC_CAT_B_HIGH_FREQ,
            cbsdGrantReqs=grant_objects,
            hIncAnt=antenna_height,
            azIncAnt=antenna_azimuth,
            gainIncAnt=ant_gain_esc,
            fssEntities=None,
            threshold=iapQEsc,
            protection_ent_type=util.ProtectionEntityType.ESC_CAT_B)

    pool.close()
    pool.join()

    return

def performIAPforGWPZ(protection_entity, grant_objects, iapQGwpz):
    """
    Return the interference margin list for a given protection constraint.
    Inputs:
        protection_entity:  List of protection points inside protection area
        grant_objects:      a list of grant requests, each one being a dictionary
                            containing grant information
        iapQGwpz:           Pre IAP threshold value for GWPZ incumbent type
    Returns:                the list of indices of grants on the move list for the
                            given protection constraint 
    """

    # Get Fine Grid Points for a GWPZ protoection area
    protection_points = util.getFUGPoints(protection_entity)

    gwpz_freqRange = protection_entity[0]['record']['deploymentParam'][0]['operationParam']['operationFrequencyRange']
    gwpz_lowFreq = gwpz_freqRange['lowFrequency']
    gwpz_highFreq = gwpz_freqRange['highFrequency']

    # Get channels over which area incumbent needs partial/full protection
    protection_channels = util.getChannels(gwpz_lowFreq, gwpz_highFreq)

    # Apply IAP for each protection constraint with a pool of parallel processes.
    pool = Pool(processes=min(util.NUM_OF_PROCESSES, len(protection_points)))

    iapAreaConstraint(protectionPoints=protection_points,
            channels=protection_channels,
            lowFreq=gwpz_lowFreq,
            highFreq=gwpz_highFreq,
            cbsdGrantReqs=grant_objects,
            threshold=iapQGwpz,
            protection_ent_type=util.ProtectionEntityType.GWPZ_AREA)

    pool.close()
    pool.join()

    return

def performIAPforPPA(protection_entity, grant_objects, iapQPpa):
    """
    Return the interference margin list for a given protection constraint.
    Inputs:
        protection_entity:  List of protection points inside protection area
        grant_objects:      a list of grant requests, each one being a dictionary
                            containing grant information
        iapQPpa:            Pre IAP threshold value for PPA incumbent type 
    Returns:                the list of indices of grants on the move list for the
                            given protection constraint 
    """

    # Get Fine Grid Points for a PPA protoection area
    protection_points = util.getFUGPoints(protection_entity)


    #TODO - How do we get PPA frequency range - PAL and device record 
    # doesn't contain frequency range info
    # Currently default frequency is considered from 3550-3680 MHz
    # Get channels over which area incumbent needs partial/full protection
    protection_channels = util.getChannels(PPA_LOW_FREQ, PPA_HIGH_FREQ)

    # Apply IAP for each protection constraint with a pool of parallel processes.
    pool = Pool(processes=min(util.NUM_OF_PROCESSES, len(protection_points)))

    iapAreaConstraint(protectionPoints=protection_points,
            channels=protection_channels,
            lowFreq=PPA_LOW_FREQ,
            highFreq=PPA_HIGH_FREQ,
            cbsdGrantReqs=grant_objects,
            threshold=iapQPpa,
            protection_ent_type=util.ProtectionEntityType.PPA_AREA)

    pool.close()
    pool.join()

    return

def performIAPforFSS(protection_entity, grant_objects, iapQCochannel, iapQBlocking):
    """
    Return the interference margin list for a given protection constraint.
    Inputs:
        protection_entity:  List of protection points inside protection area
        grant_objects:      a list of grant requests, each one being a dictionary
                            containing grant information
        iapQCochannel:      Pre IAP threshold value for FSS co-channel incumbent type
        iapQBlocking:       Pre IAP threshold value for FSS Blocking incumbent type
    Returns:                the list of indices of grants on the move list for the
                            given protection constraint 
    """

    # Get FSS T&C Flag value
    fss_ttc_flag = protection_entity[0]['deploymentParam'][0]['ttc_flag']

    # Get the protection point of the FSS
    fss_point = protection_entity[0]['deploymentParam'][0]['installationParam']
    protection_point = (fss_point['latitude'], fss_point['longitude'])

    # Get FSS Antenna Height
    antenna_height = fss_point['height']
   
    # Get FSS Antenna Gain
    antenna_gain = fss_point['antennaGain']

    # Get the frequency range of the FSS
    fss_freqRange = protection_entity[0]['deploymentParam'][0]['operationParam']['operationFrequencyRange']
    fss_lowFreq = fss_freqRange['lowFrequency']
    fss_highFreq = fss_freqRange['highFrequency']

    # TODO -- How to pass satellite info ? 
    # Protect the following FSS near Kansas City defined here:
    #    http://licensing.fcc.gov/myibfs/displayLicense.do?filingKey=-205179
    fss_info = entities.FssLicenseInfo(latitude=protection_point[0],
                                       longitude=protection_point[1],
                                       height_agl=antenna_height,
                                       max_gain_dbi=antenna_gain,
                                       satellite_arc_east_limit=-60,
                                       satellite_arc_west_limit=-143,
                                       elevation_east_limit=32.8,
                                       elevation_west_limit=22.9,
                                       azimuth_east_limit=132.6,
                                       azimuth_west_limit=241.2)

    # Get all the FSS "protection points".
    fss_entities = example_fss_interference.GetAllFssFromLicenseInfo(fss_info)

    pool = Pool(processes=min(util.NUM_OF_PROCESSES, len(protection_point)))

    # FSS Passband is between 3600 and 4200
    if (fss_lowFreq >= util.FSS_LOW_FREQ and fss_lowFreq < util.CBRS_HIGH_FREQ):
        # Get channels for co-channel CBSDs
        protection_channels = util.getChannels(fss_lowFreq, util.CBRS_HIGH_FREQ)

        # FSS Co-channel algorithm
         
        print 'Calling FSS Protection' 
        iapPointConstraint(protectionPoint=protection_point,\
			channels=protection_channels,\
			lowFreq=fss_lowFreq,\
			highFreq=util.CBRS_HIGH_FREQ,\
			cbsdGrantReqs=grant_objects,\
			hIncAnt=antenna_height,\
			azIncAnt=None,\
                        gainIncAnt=None,\
			fssEntities=fss_entities,\
			threshold=iapQCochannel,\
			protection_ent_type=util.ProtectionEntityType.FSS_CO_CHA)

        print 'Calling FSS Inband blocking Protection' 
        # 5MHz channelization is not required for Blocking protection
        # FSS in-band blocking algorithm
        iapFSSBlockingConstraint(protectionPoint=protection_point,
                lowFreq=util.CBRS_LOW_FREQ,
                highFreq=fss_lowFreq,
                cbsdGrantReqs=grant_objects,
                hIncAnt=antenna_height,
                fssEntities=fss_entities,
                threshold=iapQBlocking,
                protection_ent_type=util.ProtectionEntityType.FSS_BLOCKING)


    # FSS Passband is between 3700 and 4200 and TT&C flag is set to TRUE
    elif (fss_lowFreq >= 3700 and fss_highFreq <= 4200) and (fss_ttc_flag == True):
        # 5MHz channelization is not required for Blocking protection
        # FSS TT&C Blocking Algorithm
        print 'Calling FSS TT&C  blocking Protection' 
        iapFSSBlockingConstraint(protectionPoint=protection_point,
                lowFreq=util.CBRS_LOW_FREQ,
                highFreq=fss_lowFreq,
                cbsdGrantReqs=grant_objects,
                hIncAnt=antenna_height,
                fssEntities=fss_entities,
                threshold=iapQBlocking,
                protection_ent_type=util.ProtectionEntityType.FSS_BLOCKING)

    elif (fss_lowFreq >= 3700 and fss_highFreq <= 4200) and (fss_ttc_flag == False):
        print 'IAP for FSS not applied for FSS Pass band 3700 to 4200 and TT&C flag set to false'

    pool.close()
    pool.join()

    return

def calculateIAPQ(protection_thresholds, pre_iap_headRooms):
    """
   Routine to calculate interference margin for each 5MHz channel
   Inputs:
       protection_threhsold: protection threshold of the protected entity
       headrooms:            headroom for the protected entity 
       protection_ent_type:  protected entity type
   Returns:
       allowed_margin:       allowed interference margin of the protected entity 
   """

    for key, Q in protection_thresholds.iteritems():
        if key is 'QPpa':
             threshold_per_iapbw['iapThPpa'] = Q + 10 \
                    * np.log10(util.IAPBW/util.PPA_RBW)
             iap_allowed_margin['iapQPpa'] = 10**(( \
                   threshold_per_iapbw['iapThPpa'] - \
                   pre_iap_headRooms.get('MgPpa'))/10)
        elif key is 'QGwpz':
             threshold_per_iapbw['iapThGwpz'] = Q + 10 \
                   * np.log10(util.IAPBW/util.GWPZ_RBW)
             iap_allowed_margin['iapQGwpz'] = 10**((\
                    threshold_per_iapbw['iapThGwpz'] -  \
                    pre_iap_headRooms.get('MgGwpz'))/10)
        elif key is 'QCochannel':
             threshold_per_iapbw['iapThCochannel'] = Q + 10 \
                 * np.log10(util.IAPBW/util.ONE_MHZ)
             iap_allowed_margin['iapQCochannel'] = 10**(( \
                   threshold_per_iapbw['iapThCochannel'] - \
                   pre_iap_headRooms.get('MgCochannel'))/10)
        elif key is 'QBlocking':
             threshold_per_iapbw['iapThBlocking'] = Q
             iap_allowed_margin['iapQBlocking'] = \
                 10**((threshold_per_iapbw['iapThBlocking']\
                    - pre_iap_headRooms.get('MgBlocking'))/10)
        elif key is 'QEsc':
             threshold_per_iapbw['iapThEsc'] = Q + 10 \
                 * np.log10(util.IAPBW/util.ONE_MHZ)
             iap_allowed_margin['iapQEsc'] = 10**(( \
                   threshold_per_iapbw['iapThEsc'] - \
                  pre_iap_headRooms.get('MgEsc'))/10) 

    print iap_allowed_margin
    print threshold_per_iapbw 

def getHeadroomPerReferenceBandwidth():
    """
   Routine to get allocation of the headroom per reference bandwidth in (mW/RBW)
   Inputs:
       protection_threhsold: protection threshold of the protected entity (dBm/RBW)
       pre_iap_headRooms:    Pre-IAP Headrooms Mg (dB)
   Returns:
      Updates global container headroom_per_reference_bandwidth for all the 
      incumbent types 
   """

    for key, Q in threshold_per_iapbw.iteritems():
        if key is 'iapThPpa':
            headroom_per_reference_bandwidth['hmPpa'] = (10**(\
                 Q/10) - iap_allowed_margin['iapQPpa'])/util.NUM_SAS
        elif key is 'iapThGwpz':
             headroom_per_reference_bandwidth['hmGwpz'] = (10**( \
                 Q/10) - iap_allowed_margin['iapQGwpz'])/util.NUM_SAS
        elif key is 'iapThCochannel':
             headroom_per_reference_bandwidth['hmCochannel'] = (10**(\
                 Q/10) - iap_allowed_margin['iapQCochannel'])/util.NUM_SAS
        elif key is 'iapThBlocking':
             headroom_per_reference_bandwidth['hmBlocking'] = (10**(\
                 Q/10) - iap_allowed_margin['iapQBlocking'])/util.NUM_SAS
        elif key is 'iapThEsc':
             headroom_per_reference_bandwidth['hmEsc'] = (10**( \
                 Q/10) - iap_allowed_margin['iapQEsc'])/util.NUM_SAS

    print headroom_per_reference_bandwidth 

def calculate_AP_IAP_Ref():
    """
    Routine to calculate calculate interference from all the CBSDs managed 
    by the SAS at protected entity
    Inputs:
        post_iap_managed_grants: Global container to store EIRP and Interference 
                                 of a grant over all the protection point, channel
        common_leftover:         Global container too store common_leftover interference 
                                 margin for all the protection point, channel
    Returns:
        AP_IAP_Ref:              a dictionary containing AP_IAP_Ref for
                                 protection point, channel
    """
    
    AP_IAP_Ref = {}

    for p_ch_key, Q_p_ch in common_leftover.iteritems():
        A_SAS_P = 0
        # Calculate A_SAS_P - Aggregate interference calculated using the 
        # EIRP obtained by all CBSDs through application of IAP for protected
        # entity p. Only grants managed by SAS UUT are considered  
        for grant_id, grant_info in post_iap_managed_grants.iteritems():
            for grant_protection_constraint, grant_params in grant_info.iteritems():
                if p_ch_key == grant_protection_constraint:
                   #Aggregate interference if grant in inside protection constraint
                   A_SAS_P =  A_SAS_P +  grant_params.interference
        # Calculate AP_IAP_Ref for a particular protection point, channel
        if p_ch_key.entityType == util.ProtectionEntityType.ESC_CAT_A or \
           p_ch_key.entityType == util.ProtectionEntityType.ESC_CAT_B:
              HM_p = headroom_per_reference_bandwidth['hmEsc']
        elif p_ch_key.entityType == util.ProtectionEntityType.GWPZ_AREA: 
              HM_p = headroom_per_reference_bandwidth['hmGwpz']
        elif p_ch_key.entityType == util.ProtectionEntityType.PPA_AREA: 
              HM_p = headroom_per_reference_bandwidth['hmPpa']
        elif p_ch_key.entityType == util.ProtectionEntityType.FSS_CO_CHA: 
              HM_p = headroom_per_reference_bandwidth['hmCochannel']
        elif p_ch_key.entityType == util.ProtectionEntityType.FSS_BLOCKING: 
              HM_p = headroom_per_reference_bandwidth['hmBlocking']
        AP_IAP_Ref[p_ch_key] =  HM_p + Q_p_ch/ util.NUM_SAS + A_SAS_P



def performIAP(protection_thresholds, pre_iap_headRooms, protection_entities,
                   sas_uut_fad_object, sas_th_fad_objects):
    """
    Main routine to apply IAP to all existing and pending grants.
    Inputs:
        protection_thresholds : a list of protection thresholds per IAPBW(dbm/IAPBW)
                               for protection entities
        pre_iap_headRooms :      a list of per IAP headroom for protection entities
        protection_entities:    a list of protection entities, a list of FSS and GWPZ records
        fadObjects:            a list of FAD objects from SAS UUT and SAS Test Harness
    Returns:
        result:                a list of post IAP margin for all the protected entities p
    """

    # Calculate protection threshold per IAPBW
    calculateIAPQ(protection_thresholds, pre_iap_headRooms)

    # Calculate headroom per reference bandwidth
    getHeadroomPerReferenceBandwidth()

    # List of CBSD grant tuples extract from FAD record 
    grant_objects = []
    tot_fad_th = len(sas_th_fad_objects)

    # Extract CBSD dump from SAS UUT FAD object
    #cbsd_dump = self.sas_uut_fad_object.get_cbsds() 
    sas_uut_fad_object =sas_uut_fad_object[0]
    cbsd_dump_uut = sas_uut_fad_object[0]   #testing purpose
    # Extract CBSD Grant objects from CBSD dump from Managing SAS  
    grant_objects = util.getGrantFromCBSDDump(cbsd_dump_uut,True)

    # Extract CBSD dump from SAS Test Harness FAD objects
    for i in range (0,tot_fad_th):
        sas_th_fad_object = sas_th_fad_objects[i]
        #cbsd_dump_sasTH = self.sas_th_fad_object.get_cbsds()
        cbsd_dump_sasTH = sas_th_fad_object[0]
        # Extract CBSD Grant objects from CBSD dump from Managing SAS  
        grant_objects_sasTH = util.getGrantFromCBSDDump(cbsd_dump_sasTH,False)
        grant_objects = grant_objects + grant_objects_sasTH
    
    # Extract PPA protection entity information from SAS UUT FAD object
    #ppa_protection_entities = self.sas_uut_fad_object.get_ppas()
    ppa_protection_entities = sas_uut_fad_object[1]  #testing purpose
    
    # Extract PPA protection entity information from SAS TH FAD objects
    for i in range (0,tot_fad_th):
        sas_th_fad_object = sas_th_fad_objects[i]
        #ppa_entities_sasTH = self.sas_th_fad_objects.get_ppas()
        ppa_entities_sasTH = sas_th_fad_object[1]
        ppa_protection_entities.append(ppa_entities_sasTH)

    # Extract ESC protection entity information from SAS UUT FAD object
    #esc_protection_entities = self.sas_uut_fad_object.get_esc_sensors()
    esc_protection_entities = sas_uut_fad_object[2]  #testing purpose

    # Extract ESC protection entity information from SAS TH FAD objects
    for i in range (0,tot_fad_th):
        sas_th_fad_object = sas_th_fad_objects[i]
        #esc_entities_sasTH = self.sas_th_fad_objects.get_esc_sensors()
        esc_entities_sasTH = sas_th_fad_object[2]
        esc_protection_entities.append(esc_entities_sasTH)

    for protection_entity in protection_entities:
        if 'type' in protection_entity [0]:
            if protection_entity[0]['type'] == 'FSS':
               performIAPforFSS(protection_entity, grant_objects, \
	   			iap_allowed_margin['iapQCochannel'], \
				iap_allowed_margin['iapQBlocking'])
        elif protection_entity[0]['record']['type'] == 'PART_90':
             performIAPforGWPZ(protection_entity, grant_objects, \
                             iap_allowed_margin['iapQGwpz'])

    for ppa_entity in ppa_protection_entities:
        performIAPforPPA(ppa_entity, grant_objects, \
                         iap_allowed_margin['iapQPpa'])

    for esc_entity in esc_protection_entities:
       if len( esc_entity) != 0 :
           performIAPforESC(esc_entity, grant_objects, \
                        iap_allowed_margin['iapQEsc'])
    
     # List of Aggregate interference from all the CBSDs managed by 
     # the SAS at the protected entity 
    AP_IAP_Ref = {}

    AP_IAP_Ref = calculate_AP_IAP_Ref()

    return AP_IAP_Ref
