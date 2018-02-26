import numpy as np
from shapely import geometry
 
def ComputePPAProtectionPoints(boundary_points, resolution_arcsec):   
    """Gets all the protected points in a PPA.
     Inputs:
        boundary_points: a list of (lon,lat) tuple defining the boundary of the points.
        resolution_arcsec: the gridding resolution (in arcsec).
     
     Returns:
       all the protection points within the contour
    """   
    ppa_contour_poly = geometry.Polygon([[lon,lat] for lon,lat in boundary_points])
    resolution = resolution_arcsec/3600.0
    lng_min, lat_min, lng_max, lat_max = ppa_contour_poly.bounds
    lat_min = np.floor(lat_min / resolution) * resolution
    lng_min = np.floor(lng_min / resolution) * resolution
    lat_max = np.ceil(lat_max / resolution + 1) * resolution
    lng_max = np.ceil(lng_max / resolution + 1) * resolution    
    mesh_x, mesh_y = np.mgrid[lng_min:lng_max:resolution, lat_min:lat_max:resolution]
    points = np.vstack((mesh_x.ravel(), mesh_y.ravel())).T
    ppa_points = ppa_contour_poly.intersection(geometry.asMultiPoint(points))
    if ppa_points.geom_type == 'MultiPoint':
        return [[pt.x, pt.y] for pt in ppa_points]
    elif ppa_points.geom_type == 'Point':
        return [[ppa_points.x, ppa_points.y]] 
