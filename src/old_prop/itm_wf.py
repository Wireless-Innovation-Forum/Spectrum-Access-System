from itm import *
from terrain import *
from geo import *
from tropoclim import *
from refractivity import *

def itm_wf(lat1, lon1, h1,
           lat2, lon2, h2,
           f = 3625.,
           rel = 0.5):
    """
    Implements the WinnForum-compliant ITM pt-to-pt propagation loss
    model.

    Inputs:
    lat1, lon1, h1      Lat/lon (deg) and height AGL (m) of point 1
    lat2, lon2, h2      Lat/lon (deg) and height AGL (m) of point 2
    f                   Frequency (MHz). Default is mid-point of band.
    rel                 Reliability (for aggreg interf see R2-SGN-12)
   
    Returns the following values:
    dbloss              Loss in dB (>0)
    errnum              ITM error code (see below)
    strmode             String containing description of dominant prop mode
    dist                Distance between end points (km)
    bearing             Bearing (deg) from lat1/lon1 to lat2/lon2
    d                   Array of distances (km; use as x values to plot terrain)
    t                   Terrain heights (m; use as y values to plot terrain)

    ITM error codes:
    0- No Error.
    1- Warning: Some parameters are nearly out of range.
           Results should be used with caution.
    2- Note: Default parameters have been substituted for impossible ones.
    3- Warning: A combination of parameters is out of range.
            Results are probably invalid.
    Other-  Warning: Some parameters are out of range.
            Results are probably invalid.

    Andrew Clegg
    February 2017
    """
    
    conf = 0.5
    dielec = 25.
    conduct = 0.02
    pol = 1
    refract = -1
    climate = -1
    
#   Get the terrain profile, using Vincenty great circle route, and WF
#   standard (bilinear interp; 1500 pts for all distances over 45 km)
    elev = terrainProfile_vincenty(lat1=lat1, lon1=lon1,
                                   lat2=lat2, lon2=lon2,
                                   target_dx = 30.,
                                   interp='bilinear',
                                   winnf=True)

#   Find the midpoint of the great circle path
    dist, bearing, backaz = dist_bear_vincenty(lat1, lon1, lat2, lon2)
    latmid, lonmid, backaz = to_dist_bear_vincenty(lat1, lon1, dist/2., bearing)
    
#   Lookup the climate value at the path midpoint, if not explicitly provided
    if climate < 0:
        readTropoClim('')
        climate = tropoClim(latmid, lonmid)

#   Look up the refractivity at the path midpoint, if not explicitly provided
    if refract < 0:
        readRefractivity('')
        refract = refractivity(latmid, lonmid)

#   Call ITM prop loss.
    dbloss, strmode, errnum = \
            point_to_point(elev, h1, h2, dielec, conduct,
                           refract, f, climate, pol,
                           conf, rel, 0., '', 0)

#   Create distance/terrain arrays for plotting if desired
    d = (elev[1]/1000.) * np.asarray(range(len(elev)-2))
    t = elev[2:]
    
    return dbloss, errnum, strmode, dist, bearing, d, t
