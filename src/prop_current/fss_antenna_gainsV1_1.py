'''
Created on 6 juil. 2017

@author: Red Technologies
Gerard Garnier
'''
import vincenty
import numpy as npy
import math

def GetFSSAntennaGain(pfl, cbsdLat, cbsdLng, cbsdHeight, fssLat, fssLng, fssHeight, fssPointingElevation, fssPointingAzimuth, w1=None, w2=None):
    """
    Returns the FSS Earth Station Antenna Gain (R2-SGN-21).
    Inputs:
        pfl                       Terrain profile line
        cbsdLat, cbsdLng          lat/lon of cbsd (deg)
        cbsdHeight                height of the CBSD, in meters
        fssLat, fssLng            lat/lon of fss (deg) 
        fssHeight                 height of the FSS, in meters
        fssPointingElevation      the FSS earth station antenna elevation (deg : 0 - 359)        
        fssPointingAzimuth        FSS earth station antenna azimuth (deg : 0 - 359)
        w1, w2                    weights 
    Output:
        FSS Earth Station Antenna Gain
    """
    d, azstart, AZ = vincenty.dist_bear_vincenty(cbsdLat, cbsdLng, fssLat, fssLng)

    theta = [0., 0.]
    GetElevationAngle(pfl, fssHeight, cbsdHeight, theta)
    
            
    # off-axis angle
    ThetaAngle = (180 * (1 / math.cos( (math.cos(theta[0]) * math.cos(math.radians(fssPointingElevation))\
                                        * math.cos(math.radians(fssPointingAzimuth - AZ))) + (math.sin(theta[0]) * math.sin(math.radians(fssPointingElevation))) )))/ math.pi
        
    Ggso, GgsoP = GetGgsoAndGgsoP(ThetaAngle)
    
    # If the FSS earth station registration data includes values for w1 and w2, 
    # SAS shall use these values. Otherwise SAS shall assume w1=0 and w2=1.
    if w1 is None or w2 is None:
        FSSGain = GgsoP
    else:
        FSSGain = w1*Ggso + w2*GgsoP
    
    return FSSGain

def GetElevationAngle(pfl, fssHeight, cbsdHeight, theta):
    
    """
    Returns elevation angles of the horizons from each terminal.
    extract and rewrite of the ITM horizon calculation routine hzns()
    Inputs:
        pfl          Terrain profile line
        fssHeight   height of the mobile, in meters
        cbsdHeight   height of the base station, in meters
    Output:
        theta : Elevation angles
                 - theta[0] = mobile horizon distance, in radians
                 - theta[1] = base station horizon distance, in radians
    """
    np = int(pfl[0])           #// number of points
    xi = pfl[1]                #// step size of the profile points, in meter
    d_meter = np * xi

    h_gnd__meter = npy.mean(pfl[2:])
    
    # Effective earth curvature per meter, based on refractivity ens 
    # at average altitude based on refractivity en0 at sea level
    en0 = 301.0
    ens = 0
    if h_gnd__meter == 0:
        ens = en0
    else:
        ens = en0 * math.exp(-h_gnd__meter / 9460)
    gma = 157e-9

    gme = gma * (1 - 0.04665 * math.exp(ens / 179.3))
   
    za = pfl[2] + fssHeight
    zb = pfl[np + 2] + cbsdHeight
    qc = 0.5 * gme
    q = qc * d_meter
    theta[1] = (zb - za) / d_meter
    theta[0] = theta[1] - q
    theta[1] = -theta[1] - q
  
    if np < 2:
        return

    sa = 0.
    sb = d_meter
    wq = True
    
    for i in range(2, np+1):
        sa = sa + xi
        sb = sb - xi
        q = pfl[i + 1] - (qc * sa + theta[0])*sa - za
        if q > 0:
            theta[0] = theta[0] + q / sa
            wq = False
        if not wq:
            q = pfl[i + 1] - (qc*sb + theta[1])*sb - zb
            if q > 0:
                theta[1] = theta[1] + q / sb

    
def GetGgsoAndGgsoP(Theta):
    """
    Returns GGSO Patterns.
    Inputs:
        Theta          off-axis angle
    Output:
        GGSO gains :
            Ggso     : in tangent plane 
            GgsoP    : in perpendicular plane
    """
    Ggso = 0.0
    GgsoP = 0.0

    Theta = abs(Theta)
    if Theta > 48:
        Ggso = -10;
        GgsoP = -10;
        return Ggso, GgsoP

    if Theta > 3:
        GgsoP = 32 - 25*math.log10(Theta)

    if Theta <= 1.5:
        return Ggso, GgsoP
    if Theta <= 7:
        Ggso =  29 - 25*math.log10(Theta)
    elif Theta <= 9.2:
        Ggso = 8
    else:
        Ggso = 32 - 25*math.log10(Theta)
 
    return Ggso, GgsoP
