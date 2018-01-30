#    Copyright 2017 SAS Project Authors. All Rights Reserved.
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

#==================================================================================
# Iterative Allocation Process(IAP_ Reference Model.
# Based on WINNF-TS-0112, Version V1.3.0-r5.0, 29 January 2018.

#==================================================================================

import numpy as np
from operator import attrgetter, iadd
from shapely.geometry import Point as SPoint
from shapely.geometry import Polygon as SPolygon
from shapely.geometry import MultiPolygon as MPolygon
from collections import namedtuple
from multiprocessing import Pool
from functools import partial
from enum import Enum
from util import getFUGPoints, getChannels

# Set constant parameters based on requirements in the WINNF-TS-0112 [R2-SGN-16]
GWPZ_NBRHD_DIST = 40            # neighborhood distance from a CBSD to a given protection point (in km) 
                                # in GWPZ protection area
PPA_NBRHD_DIST = 40             # neighborhood distance from a CBSD to a given protection point (in km)
                                # in PPA protection area

FSS_CO_CHANNEL_NBRHD_DIST = 150  # neighborhood distance from a CBSD to FSS for co-channel protection

FSS_BLOCKING_NBRHD_DIST =40     # neighborhood distace from a CBSD to FSS for blocking protection

#TODO IAP_PP -- Add macro for FSS_CO_CHA, FSS_TT_C and ESC Sensor

INTERFERENCE_QUOTA = 0.000000005 #Protection threshold per IAP BW - in mWatt - -83dbm/IAPBW

#TODO IAP_PP -- Add interference quota macro for FSS_CO_CHA, FSS_TT_C and ESC Sensor


# Frequency used in propagation model (in MHz) [R2-SGN-04]
FREQ_PROP_MODEL = 3625.0

# Frequency range of IAP reference model (Hz)
LOW_FREQ = 3550000000
HIGH_FREQ = 3700000000

# Define an enumeration class named ProtectionEntityType with members
# 'GWPZ_AREA', 'PPA_AREA'
class ProtectionEntityType(Enum):
    GWPZ_AREA = 1
    PPA_AREA = 2
    FSS_CO_CHA = 3
    FSS_BLOCKING = 4
    ESC_POINT = 5
#TODO IAP_PP -- Add macro for FSS_CO_CHA, FSS_TT_C and ESC Sensor


class ProtectionPointType(Enum):

# Define CBSD grant, i.e., a tuple with named fields of 'latitude', 'longitude', 'height',
# 'indoorDeployment', 'antennaAzimuth', 'antennaGain', 'antennaBeamwidth', 'grantIndex',
# 'maxEirp', 'lowFrequency', 'highFrequency'
CBSDGrant = namedtuple('CBSDGrant',
                       ['latitude', 'longitude', 'height', 'indoorDeployment',
                        'antennaAzimuth', 'antennaGain', 'antennaBeamwidth',
                        'grantIndex', 'maxEirp', 'lowFrequency', 'highFrequency'])

# Define protection constraint, i.e., a tuple with named fields of
# 'latitude', 'longitude', 'lowFrequency', 'highFrequency'
ProtectionConstraint = namedtuple('ProtectionConstraint',
                                  ['latitude', 'longitude',
                                   'lowFrequency', 'highFrequency'])

# Define 5 MHz channel range, i.e., a tuple with named fields of
# 'lowFrequency', 'highFrequency'
ChannelRange = namedtuple('ChannelRange',
                          ['lowFrequency', 'highFrequency'])

def findGrantsInsideNeighborhood(cbsdGrantReqs, constraint,
                                 areaZone, protectionEntType):

    """
    Identify the Nc CBSD grants in the neighborhood of protection constraint.
    Inputs:
        cbsdGrantReqs:  a list of grant requests
        constraint:     protection constraint of type ProtectionConstraint
        areaZone:       a polygon object or a list of locations.
                        If it is a list of locations, each one being a tuple
                        with fields 'latitude' and 'longitude'.
                        Default value is 'None'.
    Returns:
        grants_inside:  a list of grants, each one being a namedtuple of type CBSDGrant,
                        of all CBSDs inside the neighborhood of the protection constraint.
    """
    
    if protectionEntType is  ProtectionEntityType.GWPZ_AREA or protectionEntType is ProtectionEntityType.PPA_AREA or protectionPointType is ProtectionPointType.FSS_CO_CHA or protectionPointType is ProtectionPointType.FSS_TT_C: 
       # Make sure area zone is a polygon
       if isinstance(areaZone, SPolygon) or isinstance(areaZone, MPolygon):
            polygon_areaZone = areaZone
       else:
           polygon_areaZone = SPolygon(areaZone)

    # Initialize an empty list
    grants_inside = []

    # Loop over each CBSD grant
    for grantReq in cbsdGrantReqs:

        # Check CBSD location
        lat_cbsd = grantReq.latitude
        lon_cbsd = grantReq.longitude

        # Compute distance from CBSD location to protection constraint location
        lat_c = constraint.latitude
        lon_c = constraint.longitude
        dist_km, bearing, _ = vincenty.GeodesicDistanceBearing(lat_cbsd, lon_cbsd,
                                                               lat_c, lon_c)

        # Check if CBSD is inside the neighborhood of protection constraint
        cbsd_in_nbrhd = False
        
        if protection_ent_type is ProtectionEntityType.GWPZ_AREA:
           if dist_km <= GWPZ_NBRHD_DIST:
              cbsd_in_nbrhd = True
        elif protection_ent_type is ProtectionEntityType.PPA_AREA:
           if dist_km <= PPA_NBRHD_DIST:
              cbsd_in_nbrhd = True
        elif  protectionPointType is ProtectionPointType.FSS_CO_CHA:
           if dist_km <= FSS_CO_CHANNEL_NBRHD_DIST:
              cbsd_in_nbrhd = True         
        elif protectionPointType is ProtectionPointType.FSS_TT_C: 
           if dist_km <= FSS_BLOCKING_NBRHD_DIST:
              cbsd_in_nbrhd = True

        # TODO IAP_PP FSS_CO_CHA, FSS_TT_C and ESC_Sensor 
        else:
            raise ValueError('Unknown area type %s' % protection_ent_type)

        
        # Check frequency range
        low_freq_cbsd = grantReq.lowFrequency
        high_freq_cbsd = grantReq.highFrequency

        low_freq_c = constraint.lowFrequency
        high_freq_c = constraint.highFrequency
        overlapping_bw = min(high_freq_cbsd, high_freq_c) \
                             - max(low_freq_cbsd, low_freq_c)
        freq_check = (overlapping_bw > 0)

        # Return CBSD information if it is inside the neighborhood of protection constraint
        if cbsd_in_nbrhd and freq_check:
            grants_inside.append(grantReq)

    return grants_inside

def computeInterference(cbsd_grant, constraint, h_inc_ant, iap_eirp):

    """
    Calculate interference contribution of each grant in the neighborhood to
    the protection constraint c.
    Inputs:
        cbsd_grant:     a namedtuple of type CBSDGrant
        constraint: 	protection constraint of type ProtectionConstraint
        h_inc_ant:      reference incumbent antenna height (in meters)
    Returns:
        interference: 	interference contribution
    """

    # Get CBSD grant information
    grant_index = cbsd_grant.grantIndex
    lat_cbsd = cbsd_grant.latitude
    lon_cbsd = cbsd_grant.longitude
    h_cbsd = cbsd_grant.height
    indoor_cbsd = cbsd_grant.indoorDeployment
    ant_beamwidth_cbsd = cbsd_grant.antennaBeamwidth
    ant_gain_cbsd = cbsd_grant.antennaGain
    ant_az_cbsd = cbsd_grant.antennaAzimuth
    maxEirpPerMHz_cbsd = iap_eirp
    low_freq_cbsd = cbsd_grant.lowFrequency
    high_freq_cbsd = cbsd_grant.highFrequency

    # Get protection constraint information (protection point and frequency range)
    lat_c = constraint.latitude
    lon_c = constraint.longitude
    low_freq_c = constraint.lowFrequency
    high_freq_c = constraint.highFrequency

    # Compute median and K random realizations of path loss/interference contribution
    # based on ITM model as defined in [R2-SGN-03] (in dB)
    reliabilities = np.random.uniform(0.001, 0.999)  # get K random
                # reliability values from an uniform distribution over [0.001,0.999)
    reliabilities = np.append(reliabilities, [0.5])  # add 0.5 (for median loss) as
                                            # a last value to reliabilities array
    results = wf_itm.CalcItmPropagationLoss(lat_cbsd, lon_cbsd, h_cbsd,
                                            lat_c, lon_c, h_inc_ant,
                                            indoor_cbsd,
                                            reliability=reliabilities,
                                            freq_mhz=FREQ_PROP_MODEL)
    path_loss = np.array(results.db_loss)

    # Compute CBSD antenna gain in the direction of protection point
    ant_gain = antenna.GetStandardAntennaGains(results.incidence_angles.hor_cbsd,
                                               ant_az_cbsd, ant_beamwidth_cbsd,
                                               ant_gain_cbsd)

    #TODO IAP_PP FSS_CO_CHANNEL -- Do this based on protectionEntType
    # Compute -- GFSS->CBSD -- using CBSD reference model 
    #Compute interference as 
    #Grantinterference = (Grant EIRP - CBSD Antenna Gain) + GCBSD→FSS + GFSS→CBSD +
    # PLinv + 10*log10(5) - 0.5 

   #TODO IAP_PP FSS_BLOCKING -- use aggr interference formula as per doc shared from FW

   #TODO IAP_PP ESC_SENSOR 
   # Use formula Grantinterference= (EIRPGranti -CBSD Antenna Gain) + GCBSD→ESC + GESC→CBSD + PLinv + 10*log10(5) -0.5
   # Compute GESC-CBSD computed using ESC reference model (R2-ESC-07) as provided by Admin Test Harness

    # Compute EIRP of CBSD grant inside the frequency range of protection constraint
    # Compute EIRP within co-channel bandwidth
    eirp_cbsd = (maxEirpPerMHz_cbsd - ant_gain_cbsd) + ant_gain \
                    + 10 * np.log10(5000000.0 / 1000000.0)

    # Calculate the interference contributions
    interf = eirp_cbsd - path_loss

    return interf

def iapConstraint(protectionPoints, channels, lowFreq, highFreq, cbsdGrantReqs,
                  areaZone, protectionEntType, hIncAnt,
                  threshold, beamwidth):
    """
    Return the interference margin list for a given protection constraint.
    Inputs:
        protectionPoints:   List of protection points inside protection area
        channels:           Channels over which area incumbent needs protection
        lowFreq:            low frequency of protection constraint (Hz)
        highFreq:           high frequency of protection constraint (Hz)
        cbsdGrantReqs:           a list of grant requests, each one being a dictionary
                            containing grant information
        areaZone:           a polygon object or a list of locations.
                            If it is a list of locations, each one being a tuple
                            with fields 'latitude' and 'longitude'.
        protectionEntType:  an enum member of class ProtectionEntityType
        hIncAnt:            reference incumbent antenna height (m)
        threshold:          protection threshold (dBm/5 MHz)
        beamwidth:          protection antenna beamwidth (degree)
    Returns:                the list of indices of grants on the move list for the
                            given protection constraint
    """
    
    if protectionEntType is FSS_CO_CHA:
        #Set interference quota Q for protectionPoint, channel combination
        Q = INTERFERENCE_QUOTA
        #Get IAP 5MHz channel range
        chRange = ChannelRange(lowFrequency=3550+(5*(channel-1)),highFrequency=lowFrequency+5)
        #Get protection constrain over 5MHz channel range
        chConstrain = ProtectionConstraint(latitude=protectionPoint.latitude,
                                            longitude=protectionPoint.longitude,
                                            lowFrequency=chRange.lowFrequency,
                                            highFrequency=chRange.highFrequency)
        # Identify Nc CBSD grants in the neighborhood of the protection point and channel
        Nc_grants = findGrantsInsideNeighborhood(cbsdGrantReqs, chConstrain, \
                                                 areaZone, protectionEntType)

        N = len(Nc_grants)
        #calculate the fair share
        FS = Q/N
 
        #Empty list of final IAP EIRP assigned to the grant
        grantEirp[]

        grant_initialize_flag = []
        i = 0
        while (i < N):
            grant_initialize_flag.append(0)
            i = i+ 1
        grant_iterator =0
        while (grant_iterator < N):
            if Nc_grants(grant_iterator).status != "Granted"
               for channel in channels:
                  if  Grantinterferencei > FS:
                    grant_initialize_flag(grant_iterator) =1
            grant_iterator = grant_iterator+1
                   
        grant_iterator2 =0
        while (grant_iterator2 < N):
            if Nc_grants(grant_iterator2).status != "Granted"
                grantEirp[i] = Nc_grants(grant_iterator2).maxEirp
                if  grant_initialize_flag(grant_iterator) =0:
                    # Make Grant
                    Q= Q-Grantinterferencei
                    N= N-1
                else
                    grantEirp[i] = grantEirp[i] - 1
                    
            grant_iterator2 = grant_iterator2+1


    elif protectionEntType is FSS_BLOCKING:
        #Set interference quota Q for protectionPoint, channel combination
        Q = INTERFERENCE_QUOTA
        #Get IAP 5MHz channel range
        chRange = ChannelRange(lowFrequency=3550+(5*(channel-1)),highFrequency=lowFrequency+5)
        #Get protection constrain over 5MHz channel range
        chConstrain = ProtectionConstraint(latitude=protectionPoint.latitude,
                                            longitude=protectionPoint.longitude,
                                            lowFrequency=chRange.lowFrequency,
                                            highFrequency=chRange.highFrequency)
        # Identify Nc CBSD grants in the neighborhood of the protection point and channel
        Nc_grants = findGrantsInsideNeighborhood(cbsdGrantReqs, chConstrain, \
                                                 areaZone, protectionEntType)

        N = len(Nc_grants)
        #calculate the fair share
        FS = Q/N

        #Empty list of final IAP EIRP assigned to the grant
        grantEirp[]

        grant_initialize_flag = []
        i = 0
        while (i < N):
            grant_initialize_flag.append(0)
            i = i+ 1
        grant_iterator =0
        while (grant_iterator < N):
            if Nc_grants(grant_iterator).status != "Granted"
               for channel in channels:
                  if  Grantinterferencei > FS:
                    grant_initialize_flag(grant_iterator) =1
            grant_iterator = grant_iterator+1

        grant_iterator2 =0
        while (grant_iterator2 < N):
            if Nc_grants(grant_iterator2).status != "Granted"
                grantEirp[i] = Nc_grants(grant_iterator2).maxEirp
                if  grant_initialize_flag(grant_iterator) =0:
                    # Make Grant
                    Q= Q-Grantinterferencei
                    N= N-1
                else
                    grantEirp[i] = grantEirp[i] - 1

            grant_iterator2 = grant_iterator2+1

    elif protectionEntType is FSS_BLOCKING:


    elif protectionEntType is ESC_POINT:
   
    elif protectionEntType is GWPZ_AREA or protectionEntType is PPA_AREA:
    # Initialize an empty list
    # List of fair share of interference to which grants are entitled for 
    # a particular protectionPoint, channel
    fairshare_p_ch = []
    
    #List of interference quota at a particular protectionpoint, channel
    Q_p_ch = []
    
    #Number of grants to be considered at a particular protectionpoint, channel
    N_p_ch = []
    
    #TODO IAP_PP FSS_CO_CHA, FSS_TT_C and ESC_Sensor -- Modify logic
    #TODO Consider ESC CAT-A and CAT-B 
    # For each point p_i in protectionPoints
    for protectionPoint in protectionPoints
        # For each channel c_j in channels
        for channel in channels:
            #Set interference quota Q for protectionPoint, channel combination
            Q = INTERFERENCE_QUOTA
            #Get IAP 5MHz channel range
            chRange = ChannelRange(lowFrequency=3550+(5*(channel-1)),highFrequency=lowFrequency+5)
            #Get protection constrain over 5MHz channel range
            chConstrain = ProtectionConstraint(latitude=protectionPoint.latitude,
                                                longitude=protectionPoint.longitude,
                                                lowFrequency=chRange.lowFrequency,
                                                highFrequency=chRange.highFrequency) 

            # Identify Nc CBSD grants in the neighborhood of the protection point and channel
            Nc_grants = findGrantsInsideNeighborhood(cbsdGrantReqs, chConstrain, \
                                                     areaZone, protectionEntType)
             
            N = len(Nc_grants) 
            #calculate the fair share
            FS = Q/N

            fairshare_p_ch.append(FS)
            Q_p_ch.append(Q)
            N_p_ch.append(N)
            
    # For each point p_i in protectionPoints
    for protectionPoint in protectionPoints
       
       #Find all the GAA grants inside 40kms of p_i
       # Assign values to the protection constraint
       constraint = ProtectionConstraint(latitude=protectionPoint.latitude,
                                        longitude=protectionPoint.longitude,
                                        lowFrequency=lowFreq,
                                        highFrequency=highFreq) 

       # Identify Na CBSD grants in the neighborhood of the protection constrain
       Na_grants = findGrantsInsideNeighborhood(cbsdGratReqs, constraint,
                                                areaZone, protectionEntType)
       
       num_grants = len(Na_grants)

       if num_grants:  # Number of CBSD grants that fully/partially interfere with protection point p 
                       # over at least one channel in channels
          #Empty list of final IAP EIRP assigned to the grant
          grantEirp[]
          #Empty list of power assigned indicator for the grant
          grant_powerAssigned[]
          for i, grant in enumerate(Na_grants):
              grant_powerAssigned[i] = False
              grantEirp[i] = grant.maxEirp
              while (True):
                 goodOverAllChannels = True
                 # Compute interference contributions of each grant to the protection constraint
                 # over 5MHz IAP channel
                 interf_list = []
                 # For each channel c_j in channels
                 for i, channel in enumerate(channels):
                     #Get IAP 5MHz channel range
                     chRange = ChannelRange(lowFrequency=3550+(5*(channel-1)),highFrequency=lowFrequency+5)
                     #Get protection constrain over 5MHz channel range
                     ch_constrain = ProtectionConstraint(latitude=protectionPoint.latitude,
                                                longitude=protectionPoint.longitude,
                                                lowFrequency=chRange.lowFrequency,
                                                highFrequency=chRange.highFrequency)

                     #Get the fair share for a protection point and channel combination
                     fairshare = fairshare_p_ch[i]
                     
                     #Compute interference grant causes to protection point over channel
                     interf = computeInterference(grant, ch_constraint, h_inc_ant, grantEirp[i])
                     interf_list[i] = interf
              
                     #calculated interference exceeds fair share of interference to which the grants are entitled
                     if interf > fairshare:
                        goodOverAllChannels = False
                        break
                                              
                 if goodOverAllChannels is True:
                    grantPowerassigned[i] = True
                    # For each channel c_j in channels
                    for i, channel in enumerate(channels):
                        #Remove satisfied CBSD grant from consideration
                        Q_p_ch[i] = Q_p_ch[i] - interf_list[i]
                        N_p_ch[i] = N_p_ch[i] - 1
                        #re-calculate fair share
                        fairshare_p_ch[i] = Q_p_chi[i]/N_p_ch[i]
                 else:
                    grantEirp[i] = grantEirp[i] - 1

               if all(i is True for i in grant_powerAssigned):
               break

     return Q_p_ch


def applyIAP(protectionSpecs, cbsdGrants, numProcesses):

    """
    Main routine to apply IAP to all existing and pending grants.
    Inputs:
        protectionSpecs:   a list of protection specifications, a named tuple with
                            fields of 'lowFreq' (in Hz), 'highFreq' (in Hz),
                            'antHeight' (in meter), 'beamwidth' (in degree),
                            'threshold' (in dBm/10MHz),'protectionEntity' (polygon/point),
                            'protectionEntityType'
        cbsdGrantReqs:     a list of grant requests, each one being a dictionary
                            containing CBSD and grant information
        numProcesses:      number of parallel processes to use
    Returns:
        result:             an interference margin array containing unused 
                            interference margin 
    """
     
    if protectionSpecs.protectionEntityType is GWPZ_AREA or \
              protectionSpecs.protectionEntityType or PPA_AREA:
       protection_points = getFUGPoints(protectionSpecs.protectionEntity)
    else
      protection_points = protectionSpecs.protectionEntity


    # Get channels over which area incumbent needs partial/full protection
    protection_channels = getChannels(protectionSpecs.lowFreq, protectionSpecs.highFreq)

    # Apply IAP for each protection constraint with a pool of parallel processes.
    pool = Pool(processes=min(numProcesses, len(protectionPoints)))
    

    iapMarginC = partial(iapConstraint, protectionPoints=protection_points, 
                         channels=protection_channels, 
                         lowFreq=protectionSpecs.lowFreq,
                         highFreq=protectionSpecs.highFreq,
                         cbsdGrantReqs=cbsdGrants,
                         areaZone=protectionSpecs.protectionEntity,
                         protectionEntType=protectionSpecs.protectionEntityType, 
                         hIncAnt=protectionSpecs.antHeight,
                         threshold=protectionSpecs.threshold,
                         beamwidth=protectionSpecs.beamwidth)
    pool.close()
    pool.join()


    return iapMarginC

