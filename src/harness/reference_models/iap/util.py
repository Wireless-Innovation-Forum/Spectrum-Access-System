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
"""Helper functions for IAP and Aggregate Interference."""

from collections import namedtuple
from enum import Enum
import sys
import numpy as np
from shapely.geometry import Point as SPoint
from shapely.geometry import Polygon as SPolygon
from shapely.geometry import MultiPolygon as MPolygon
import random
from shapely.geometry import shape, Point, LineString
sys.path.append('../..')
from reference_models.antenna import antenna
from reference_models.antenna import fss_pointing
from reference_models.geo import vincenty
from reference_models.examples import entities,example_fss_interference
from reference_models.propagation import wf_itm 
from reference_models.propagation import wf_hybrid 



# Set constant parameters based on requirements in the WINNF-TS-0112 [R2-SGN-16]
GWPZ_NBRHD_DIST = 40  # neighborhood distance from a CBSD to a given protection point (in km)
# in GWPZ protection area
PPA_NBRHD_DIST = 40  # neighborhood distance from a CBSD to a given protection point (in km)
# in PPA protection area

FSS_CO_CHANNEL_NBRHD_DIST = 150  # neighborhood distance from a CBSD to FSS for co-channel protection

FSS_BLOCKING_NBRHD_DIST = 40  # neighborhood distace from a CBSD to FSS for blocking protection

ESC_NBRHD_DIST_A = 40  # neighborhood distance from a ESC to category A CBSD

ESC_NBRHD_DIST_B = 80  # neighborhood distance from a ESC to category B CBSD

NUM_OF_PROCESSES = 6

# Frequency used in propagation model (in MHz) [R2-SGN-04]
FREQ_PROP_MODEL = 3625.0

# CBRS Band Frequency Range (Hz)
CBRS_LOW_FREQ = 3550000000.0
CBRS_HIGH_FREQ = 3700000000.0

# FSS Passband low frequency range  (Hz)
FSS_LOW_FREQ = 3600000000.0

# PPA Frequency Range (Hz)
PPA_LOW_FREQ = 3550000000.0
PPA_HIGH_FREQ = 3680000000.0

# ESC IAP for Out-of-Band Categoroy A CBSDs in Frequency Range (Hz)
ESC_CAT_A_LOW_FREQ = 3550000000.0
ESC_CAT_A_HIGH_FREQ = 3660000000.0

# ESC IAP for Out-of-Band Categoroy B CBSDs in Frequency Range (Hz)
ESC_CAT_B_LOW_FREQ = 3550000000.0
ESC_CAT_B_HIGH_FREQ = 3680000000.0

# ESC Channel 21 Center Frequency
ESC_CH21_CF = 3652500000.0

# One Mega Herts
ONE_MHZ = 1000000.0

# Channel bandwidth over which SASs execute the IAP process
IAPBW = 5000000.0

# GWPZ Area Protection reference bandwidth for the IAP process
GWPZ_RBW = 10000000.0

# PPA Area Protection reference bandwidth for the IAP process
PPA_RBW = 10000000.0

# GWPZ and PPA height (m)
GWPZ_PPA_HEIGHT = 1.5

# Number of SASs - NSAS
NUM_SAS = 3

# Global grant counter
grant_counter = 0

#In-band insertion loss
IN_BAND_INSERTION_LOSS = 0.5

# Define an enumeration class named ProtectionEntityType with members
# 'GWPZ_AREA', 'PPA_AREA'
class ProtectionEntityType(Enum):
    GWPZ_AREA = 1
    PPA_AREA = 2
    FSS_CO_CHA = 3
    FSS_BLOCKING = 4
    ESC_CAT_A = 5
    ESC_CAT_B = 6


# Define CBSD grant, i.e., a tuple with named fields of 'latitude', 'longitude', 'height',
# 'indoorDeployment', 'antennaAzimuth', 'antennaGain', 'antennaBeamwidth', 'cbsdCategory', 
# 'grantIndex', 'maxEirp', 'maxEirp', 'lowFrequency', 'highFrequency', 'isManagedGrant'
CBSDGrant = namedtuple('CBSDGrant',
                       ['latitude', 'longitude', 'height', 'indoorDeployment',
                        'antennaAzimuth', 'antennaGain', 'antennaBeamwidth',
                        'cbsdCategory', 'grantIndex', 'maxEirp', 'lowFrequency', 
                        'highFrequency','isManagedGrant'])

# Define protection constraint, i.e., a tuple with named fields of
# 'latitude', 'longitude', 'lowFrequency', 'highFrequency'
ProtectionConstraint = namedtuple('ProtectionConstraint',
                                  ['latitude', 'longitude',
                                   'lowFrequency', 'highFrequency', 'entityType'])



def getFUGPoints(area):
    """This function returns FUG points list
    Args:
      area: (dictionary) A dictionary containing PPA/GWPZ Record.
    Returns:
      An array of tuple (lat, lng).
    """
    fug_points = []
    area_polygon = shape(area[0]['zone']['features'][0]['geometry'])
    min_lng, min_lat, max_lng, max_lat = area_polygon.bounds
    upper_boundary_lng = np.ceil(max_lng)
    lower_boundary_lng = np.floor(min_lng)
    upper_boundary_lat = np.ceil(max_lat)
    lower_boundary_lat = np.floor(min_lat)
    while(upper_boundary_lat >= lower_boundary_lat):
        while(upper_boundary_lng >= lower_boundary_lng):
            pointLat = round(upper_boundary_lat, 6)
            pointLng = round(upper_boundary_lng, 6)
            if Point([pointLng, pointLat]).within(area_polygon):
                fug_points.append((pointLat, pointLng))
            upper_boundary_lng = upper_boundary_lng - 2.0 / 3600
        upper_boundary_lat =  upper_boundary_lat - 2.0 / 3600
        upper_boundary_lng = np.ceil(max_lng)
    return fug_points


def getChannels(low_freq, high_freq):
    """This function returns protected channels list
      Args:
      low_freq: Low frequency of the protected entity.
      high_freq: High frequency of the protected entity
    Returns:
      An array of protected channnel frequency range tuple (lowFreq,highFreq).
    """

    protection_channels = []
    start_frequency = 3550
    channel = 0
    while channel < 30:
        if ((start_frequency+channel*5 < low_freq/1000000 and start_frequency + (channel+1)*5 > low_freq/1000000)
                or (start_frequency+channel*5 >= low_freq/1000000 and start_frequency + (channel+1)*5 <= high_freq/1000000)
                or (start_frequency+channel*5 < high_freq/1000000 and start_frequency + (channel+1)*5 > high_freq/1000000)):
            ch_low_freq = (start_frequency * 1000000) + (channel * 5000000)
            ch_high_freq = ch_low_freq + 5000000
            # Frequency range of the channel, which partially overlaps with
            # protection entity frequency range
            channel_range = min(5000000.0, high_freq - ch_low_freq)
            
            if channel_range is 5000000.0: 
               protection_channels.append((ch_low_freq, ch_high_freq))
            else:
              protection_channels.append((ch_low_freq, ch_low_freq + channel_range))
            
        channel = channel + 1
    return protection_channels

def findGrantsInsideNeighborhood(cbsdGrantReqs, constraint):
    """
    Identify the Nc CBSD grants in the neighborhood of protection constraint.
    Inputs:
        cbsdGrantReqs:     a list of grant requests
        constraint:        protection constraint of type ProtectionConstraint
    Returns:
        grants_inside:  a list of grants, each one being a namedtuple of type CBSDGrant,
                        of all CBSDs inside the neighborhood of the protection constraint.
    """
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
        dist_km, bearing, _ = vincenty.GeodesicDistanceBearing(
            lat_cbsd, lon_cbsd,
            lat_c, lon_c)

        # Check if CBSD is inside the neighborhood of protection constraint
        cbsd_in_nbrhd = False

        if constraint.entityType is ProtectionEntityType.GWPZ_AREA:
            if dist_km <= GWPZ_NBRHD_DIST:
                cbsd_in_nbrhd = True
        elif constraint.entityType is ProtectionEntityType.PPA_AREA:
            if dist_km <= PPA_NBRHD_DIST:
                cbsd_in_nbrhd = True
        elif constraint.entityType is ProtectionEntityType.FSS_CO_CHA:
            if dist_km <= FSS_CO_CHANNEL_NBRHD_DIST:
                cbsd_in_nbrhd = True
        elif constraint.entityType is ProtectionEntityType.FSS_BLOCKING:
            if dist_km <= FSS_BLOCKING_NBRHD_DIST:
                cbsd_in_nbrhd = True
        elif constraint.entityType is ProtectionEntityType.ESC_CAT_A:
            if grantReq.cbsdCategory == 'A':
                if dist_km <= ESC_NBRHD_DIST_A:
                    cbsd_in_nbrhd = True
        elif constraint.entityType is ProtectionEntityType.ESC_CAT_B:
            if grantReq.cbsdCategory == 'B':
                if dist_km <= ESC_NBRHD_DIST_B:
                    cbsd_in_nbrhd = True
        else:
            raise ValueError(
                'Unknown protection entity type %s' % constraint.entityType)

        if cbsd_in_nbrhd:
            # Check frequency range
            low_freq_cbsd = grantReq.lowFrequency
            high_freq_cbsd = grantReq.highFrequency

            low_freq_c = constraint.lowFrequency
            high_freq_c = constraint.highFrequency
            overlapping_bw = min(high_freq_cbsd, high_freq_c) \
                - max(low_freq_cbsd, low_freq_c)
            freq_check = (overlapping_bw > 0)

            # Return CBSD information if it is inside the neighborhood of
            # protection constraint
            if freq_check:
                grants_inside.append(grantReq)

    return grants_inside
def getGrantFromCBSDDump(cbsd_dump,is_managing_sas):
    """
    Routine to extract CBSDGrant tuple from CBSD dump from FAD object
    Inputs:
        cbsd_dump:         cbsd dump extracted from FAD record 
        is_managing_sas:   flag indicating cbsd dump is from managing SAS or peer SAS
                           True - Managing SAS, False - Peer SAS
    Returns:
        grant_objects:     List of CBSD grant objects 
    """
    
    cbsd_objects = len(cbsd_dump)
    grant_objects = []
    
    # Loop over each CBSD grant
    for i in range(cbsd_objects):
        cbsd_record = cbsd_dump[i].get('recordData')
        registration = cbsd_record[0].get('registration')
        grants = cbsd_record[0].get('grants')

        # Check CBSD location
        lon_cbsd = registration.get('installationParam', {}).get('longitude')
        height_cbsd = registration.get('installationParam', {}).get('height')
        height_type_cbsd = registration.get('installationParam', {}).get('heightType')
        if height_type_cbsd == 'AMSL':
            altitude_cbsd = terrainDriver.GetTerrainElevation(lat_cbsd, lon_cbsd)
            height_cbsd = height_cbsd - altitude_cbsd

        # Sanity check on CBSD antenna height
        if height_cbsd < 1 or height_cbsd > 1000:
            raise ValueError('CBSD height is less than 1 m or greater than 1000 m.')
        
        global grant_counter 
        for grant in grants:
           grant_counter += 1
           # Return CBSD information
           cbsd_grant = CBSDGrant(
                # Get information from the registration
                latitude=registration.get('installationParam', {}).get('latitude'),
                longitude=registration.get('installationParam', {}).get('longitude'),
                height=height_cbsd,
                indoorDeployment=registration.get('installationParam',{}).get('indoorDeployment'),
                antennaAzimuth=registration.get('installationParam',{}).get('antennaAzimuth'),
                antennaGain=registration.get('installationParam',{}).get('antennaGain'),
                antennaBeamwidth=registration.get('installationParam',{}).get('antennaBeamwidth'),
                cbsdCategory=registration.get('cbsdCategory'),
                grantIndex=grant_counter,
                # Get information from the grant
                maxEirp=grant.get('operationParam',{}).get('maxEirp'),
                lowFrequency=grant.get('operationParam', {}). \
                       get('operationFrequencyRange', {}).get('lowFrequency'),
                highFrequency=grant.get('operationParam', {}). \
                       get('operationFrequencyRange', {}).get('highFrequency'),
                isManagedGrant=is_managing_sas)
           grant_objects.append(cbsd_grant)
    return grant_objects


def getGrantsFromCbsdObjects(cbsd_list):
    """
    Fetch grant details from CBSD objects.
    Inputs:
        cbsd_list:     a list of CBSD objects
    Returns:
        grants_list:  a list of grants, each one being a namedtuple of type CBSDGrant,
                        of all CBSDs.
    """
    grant_index = 0
    grant_request_list = []
    for cbsd in cbsd_list:
        grant_list = cbsd['grantRequests']
        height_cbsd = cbsd['registrationRequest'][
            'installationParam']['height']
        height_type_cbsd = cbsd['registrationRequest'][
            'installationParam']['heightType']
        if height_type_cbsd == 'AMSL':
            altitude_cbsd = terrainDriver.GetTerrainElevation(cbsd['registrationRequest'][
                                                              'installationParam']['latitude'], cbsd['registrationRequest']['installationParam']['longitude'])
            height_cbsd = height_cbsd - altitude_cbsd
        for i in range(len(grant_list)):
            cbsd_grant = CBSDGrant(
                latitude=cbsd['registrationRequest'][
                    'installationParam']['latitude'],
                longitude=cbsd['registrationRequest'][
                    'installationParam']['longitude'],
                height=height_cbsd,
                indoorDeployment=cbsd['registrationRequest'][
                    'installationParam']['indoorDeployment'],
                antennaAzimuth=cbsd['registrationRequest'][
                    'installationParam']['antennaAzimuth'],
                antennaGain=cbsd['registrationRequest'][
                    'installationParam']['antennaGain'],
                antennaBeamwidth=cbsd['registrationRequest'][
                    'installationParam']['antennaBeamwidth'],
                cbsdCategory=cbsd['registrationRequest']['cbsdCategory'],
                grantIndex=grant_index + 1,
                maxEirp=grant_list[i]['operationParam']['maxEirp'],
                lowFrequency=grant_list[i]['operationParam'][
                    'operationFrequencyRange']['lowFrequency'],
                highFrequency=grant_list[i]['operationParam'][
                    'operationFrequencyRange']['highFrequency'],
                isManagedGrant=None 
            )
            grant_request_list.append(cbsd_grant)
    return grant_request_list



