'''
Created on 6 juil. 2017

@author: Red Technologies
Gerard Garnier
'''
import vincenty
from ehata_its_wf import *
from cmath import isnan

def GetCBSDAntennaGain(antennaLat, antennaLon, receiverLat, receiverLon, antennaAzimut, antennaBeamWidth):
    """
    Returns the CBSD antenna gain (R2-SGN-20).
    Inputs:
        antennaLat, antennaLon    lat/lon of CBSD (deg)
        receiverLat, receiverLon  lat/lon of Receiver (deg)
        antennaAzimut             (deg : 0 - 359 )
        antennaBeamWidth          3-dB antenna beamwidth (deg : 0 - 359 )
    Output:
        CBSD antenna gain
    """
    d, AZ, backaz = vincenty.dist_bear_vincenty(antennaLat, antennaLon, receiverLat, receiverLon)
    teta = antennaAzimut - AZ
    return -min(12 * pow(teta/antennaBeamWidth,2), 20)

def GetFSSAntennaGain(pfl, h_b__meter, h_m__meter, antennaLat, antennaLon, FSSLat, FSSLon, antennaElevation, alpha, w1, w2):
    """
    Returns the FSS Earth Station Antenna Gain (R2-SGN-21).
    Inputs:
        pfl                       Terrain profile line
        h_b__meter                height of the CBSD, in meters
        h_m__meter                height of the FSS, in meters
        antennaElevation          the FSS earth station antenna elevation (deg : 0 - 359)        
        alpha                     FSS earth station antenna azimuth (deg : 0 - 359)
        w1, w2                    weights 
    Output:
        FSS Earth Station Antenna Gain
    """
    d, azstart, AZ = vincenty.dist_bear_vincenty(antennaLat, antennaLon, FSSLat, FSSLon)

    theta = [0., 0.]
    GetElevationAngle(pfl, h_m__meter, h_b__meter, theta)
    
    theta[0] = npy.degrees(theta[0])
    if(theta[0] < 0) :
        theta[0]+=360
            
    """
    off-axis angle
    """
    ThetaAngle = (180 * (1 / math.cos( (math.cos(theta[0]) * math.cos(antennaElevation)\
                                        * math.cos(alpha - AZ)) + (math.sin(theta[0]) * math.sin(antennaElevation)) )))/ math.pi
        
    Ggso, GgsoT = GetGgsoAndGgsoT(ThetaAngle)
    
    """
    If the FSS earth station registration data includes values for w1 and w2, 
    SAS shall use these values. Otherwise SAS shall assume w1=0 and w2=1.
    """
    if (isnan(w1) | isnan(w2)):
        FSSGain = GgsoT
    else:
        FSSGain = w1*Ggso + w2*GgsoT
    
    return FSSGain

def GetElevationAngle(pfl, h_m__meter, h_b__meter, theta):
    
    """
    Returns elevation angles of the horizons from each terminal.
    Inputs:
        pfl          Terrain profile line
        h_m__meter   height of the mobile, in meters
        h_b__meter   height of the base station, in meters
    Output:
        theta : Elevation angles
                 - theta[0] = mobile horizon distance, in radians
                 - theta[1] = base station horizon distance, in radians
    """
    np = int(pfl[0])           #// number of points
    xi = pfl[1]                #// step size of the profile points, in meter
    d_meter = np * xi

    h_gnd__meter = AverageTerrainHeight(pfl)
    
    en0 = 301.0
    ens = 0
    if (h_gnd__meter == 0):
        ens = en0
    else:
        ens = en0 * math.exp(-h_gnd__meter / 9460)
    gma = 157e-9

    gme = gma * (1 - 0.04665 * math.exp(ens / 179.3))
   
    za = pfl[2] + h_m__meter
    zb = pfl[np + 2] + h_b__meter
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

    
def GetGgsoAndGgsoT(Theta):
    """
    Returns GGSO Patterns.
    Inputs:
        Theta          off-axis angle
    Output:
        GGSO Patterns
    """
    Ggso = 0.0
    GgsoT = 0.0

    if (Theta > 48 and Theta <= 180):
        Ggso = -10;
        GgsoT = -10;
        return Ggso, GgsoT

    if (Theta > 3 and Theta <= 48):
        GgsoT = 32 - 25*math.log10(Theta);
        if (Theta <= 7):
            Ggso = 29 - 25*math.log10(Theta)
        if (Theta > 7 and Theta <= 9.2):
            Ggso = 8;
        if (Theta > 9.2):
            Ggso = 32 - 25*math.log10(Theta)
        return Ggso, GgsoT
    
    if (Theta >= 1.5):
        Ggso = 29 - 25*math.log10(Theta)
    return Ggso, GgsoT
