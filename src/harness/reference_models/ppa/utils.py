import numpy as np
from shapely import geometry

def ComputePPAProtectionPoints(boundarysPoints, ARCSEC):   
    """Gets all the protected points in a PPA.
     Inputs:
        boundary_points: a list of (lon,lat) tuple defining the boundary of the points.
        res_arcsec: the gridding resolution (in arcsec).
    
     Returns:
       all the protection points
    """    
    poly = geometry.Polygon([[lon,lat] for lon,lat in boundarysPoints])
    arcsec = ARCSEC/3600.0
    minlon, minlat, maxlon, maxlat = poly.bounds
    
    iLat = np.floor(minlat)
    iLon = np.floor(minlon)
    nL = np.floor((minlat - iLat)/arcsec)
    nH = np.ceil((maxlat - iLat)/arcsec)
    mL = np.floor((minlon - iLon)/arcsec)
    mH = np.ceil((maxlon - iLon)/arcsec)
        
    latgrid = np.arange(iLat + nL*arcsec, iLat + nH*arcsec, arcsec)
    longrid = np.arange(iLon + mL*arcsec, iLon + mH*arcsec, arcsec)
    
    ppa_points = []
    if len(latgrid) > 0 and len(latgrid)>0:
        for lat in latgrid:
            for lon in longrid:
                ppa_check_point = geometry.Point(lon, lat)
                if ppa_check_point.within(poly):
                        ppa_points.append([lat, lon])

    return ppa_points
