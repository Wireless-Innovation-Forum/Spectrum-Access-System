'''
Created on 6 juil. 2017

@author: Red Technologies
Gerard Garnier
'''

def GetCBSDAntennaGain(AZ, antennaAzimut, antennaBeamWidth):
    """
    Returns the CBSD antenna gain (R2-SGN-20).
    Inputs:
        AZ                        azimuth angle (deg : 0 - 359)
        antennaAzimut             (deg : 0 - 359)
        antennaBeamWidth          3-dB antenna beamwidth (deg : 0 - 359)
    Output:
        CBSD antenna gain
    """
    teta = antennaAzimut - AZ
    return -min(12 * pow(teta/antennaBeamWidth,2), 20)
