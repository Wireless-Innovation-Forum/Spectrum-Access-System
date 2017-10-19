# Wrapper to implement R2-SGN-04 "Frankenmodel"

# Includes unresolved dependencies that will need to be resolved.

import sys

from terrain import *
from itm_wf import *
from ehata_its_wf import *
from nlcd_indexer import *
import os
import numpy as np
import geo
import terrain

global interValues
interValues = InterValues()

def get_NLCD_region(lat, lon):
    """
    Returns the NLCD region type for the specified location. This implementation
    simply returns the region at lat/lon.

    ***TODO: WinnForum implementation involves calculating the region based on
    the preponderance of region types in the service area.

    ***TODO: This code takes a long time to execute because it initializes some
    stuff. Probably need to integrate the NlcdIndexer class into this code and
    do the initialization once upon startup otherwise it will take a very long
    time to calculate many prop losses.

    Andrew Clegg
    February 2017
    """

    nlcdDir = "E:\\Google Drive\\BigFiles\\Google\\Databases\\NLCD"

#   The following line is needed because for some reason Windows GDAL environment
#   variables won't stick:
    os.putenv('GDAL_DATA', 'C:\Program Files (x86)\GDAL\gdal-data')

    indx = NlcdIndexer(nlcdDir)
    code = indx.NlcdCode(lat, lon)

    if code == 22:
        return 'SUBURBAN'
    elif code == 23 or code == 24:
        return 'URBAN'

    return 'RURAL' # If not urban or suburban

    
def hybrid_prop(lat_cbsd, lon_cbsd, h_cbsd,
                lat2, lon2, h2=1.5, f=3625.,
                region='', mode='FSS', rel=0.5, conf=0.5):
    """
    Implements the hybrid ITM/eHata prop model as specified by WinnForum
    (https://goo.gl/IDkEAJ), particularly R2-SGN-03, R2-SGN-04 through
    R2-SGN-10, and NTIA TR 15-517 Appendix A (https://goo.gl/s28vgJ).

    **NOTE: point 1 must correspond to CBSD location
    
    If region is not specified, it is looked up via the NLCD digital map.

    If mode is FSS or ESC, ITM (only) is used, per R2-SGN-03. Otherwise,
    ITM and/or eHata are used per R2-SGN-04.

    The reliability parameter (rel) can be changed if the code is being used to
    manually implement the statistical aggregate interference method described
    in R2-SGN-12.
    
    Andrew Clegg
    February 2017
    """

    global interValues

    h_cbsd_eff = -999
    
    region = region.strip().upper()
    mode = mode.strip().upper()
    
#   Calculate the predicted ITM loss
    dbloss_itm, errnum, strmode_itm, dist, bearing, d, elev = \
           itm_wf(lat_cbsd, lon_cbsd, h_cbsd, lat2, lon2, h2, f, rel, conf)     

#   Per R2-SGN-03, if mode = FSS or ESC, only ITM is used
    if mode == 'FSS' or mode == 'ESC': 
        return dbloss_itm, dbloss_itm, errnum, strmode_itm, 'FSS or ESC. Using ITM.', h_cbsd_eff

#   Calculate the effective heights of the tx and rx:
    h_cbsd_eff, h2_eff = EffectiveHeights(max(h_cbsd,20.), h2, elev)

#   Use ITM P2P if CBSD effective height greater than 200 m
    if h_cbsd_eff >= 200:
        return dbloss_itm, dbloss_itm, errnum, strmode_itm, 'Effective height > 200 m. Using ITM.', h_cbsd_eff

#   Only call the NLCD indexer if region is not specified. The indexer is slow.
#   TODO: Implement code to determine preponderance of NLCD value within
#   coverage area.
    if region not in ['URBAN', 'SUBURBAN', 'RURAL']:
        region = get_NLCD_region(lat_cbsd, lon_cbsd)

#   If rural, use ITM
    if region == 'RURAL':
        return dbloss_itm, dbloss_itm, errnum, strmode_itm, 'Rural. Using ITM.', h_cbsd_eff

#   If region is not rural

    plb_med_db = [0.]
    
#   Set the environment code number.
    if region == 'URBAN':
        enviro_code = 23
    elif region == 'SUBURBAN':
        enviro_code = 22
    
    if dist <= 0.1: # Use FSL
        r = ((1000. * dist)**2 + (h_cbsd-h2)**2)**0.5
        dbloss = 20.*log10(r) + 20.*log10(f) - 27.56
        return dbloss, dbloss_itm, 0, '', 'd <= 100 m and not rural. Using FSL.', h_cbsd_eff

    elif dist > 0.1 and dist < 1.:
        fsl100m = 12.44 + 20.*log10(f)
        MedianBasicPropLoss(f, max(h_cbsd,20.), h2, dist, enviro_code,
                        plb_med_db, interValues)
        ehata1km = plb_med_db[0]
        dbloss = fsl100m + (1. + log10(dist)) * (ehata1km - fsl100m)
        return dbloss, dbloss_itm, 0, '', 'Distance between 100 m - 1 km. Interpolating.', h_cbsd_eff

    elif dist >= 1. and dist <= 80.:
        plb = [0.]
        ExtendedHata(elev, f, max(h_cbsd,20.), h2, enviro_code, plb)
        ehata_loss = plb[0] 
        if abs(rel-0.5) < 0.001 and abs(conf-0.5) < 0.001:
            dbloss_itm_med = dbloss_itm
        else:
            dbloss_itm_med, errnum_med, strmode_itm_med, dist_med, bearing_med, d_med, elev_med = \
              itm_wf(lat_cbsd, lon_cbsd, h_cbsd, lat2, lon2, h2, f, 0.5, 0.5)
        if dbloss_itm_med >= ehata_loss:
            return dbloss_itm, dbloss_itm, errnum, strmode_itm, 'TR 15-517 mode. Using ITM because ITM_MED is >= eHata', h_cbsd_eff
        else:
            return ehata_loss, dbloss_itm, 0, '', 'TR 15-517 mode. Using eHata which is > ITM_MED.', h_cbsd_eff

    elif dist > 80.:
        # Calculate the ITM median and eHata median losses at a
        # distance of 80 km

        # Find the 80 km points
        lat80, lon80, alpha2 = geo.to_dist_bear_vincenty(lat_cbsd, lon_cbsd,
                                                 80., bearing)
        elev80 = terrain.terrainProfile_vincenty(lat_cbsd, lon_cbsd, lat80, lon80)
        
        # Calculate eHata loss and the ITM median loss at 80 km
        plb = [0.]
        ExtendedHata(elev80, f, max(h_cbsd,20.), h2, enviro_code, plb)        
        ehata80 = plb[0]
        dbloss_itm_med80, errnum_med, strmode_itm_med, dist_med, bearing_med, d_med, elev_med = \
              itm_wf(lat_cbsd, lon_cbsd, h_cbsd, lat80, lon80, h2, f, 0.5, 0.5)

        J = max(ehata80 - dbloss_itm_med80, 0)
        dbloss = dbloss_itm + J

        modeString = 'D > 80 km. Applying J = %.2f dB to ITM.' % J 
        
        return dbloss, dbloss_itm, errnum, strmode_itm, modeString, h_cbsd_eff

