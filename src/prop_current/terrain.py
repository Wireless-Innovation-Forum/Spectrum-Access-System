# Routines to extract terrain elevation from USGS 3DEP data.
#
# This version is hard-coded for the 1" 3DEP data. Assumes the data have
# been stored in 1x1 deg float32 ("GridFloat") format files, stored with the
# file names NXXWYYY.dat, where XX and YYY are the lat and lon of the northwest
# corner of the tiles. (If lat is S or lon is E, then N->S, W->E). Also assumes
# the standard 6-pixel overlap between tiles.
#
# INSTRUCTIONS
# - Set the TERRAIN_DIR variable to the local directory where the .dat files
#   are stored (.dat files are the same as the .flt files from the USGS distro)
#
# To retrieve an elevation:
#   getTerrainElevation3DEP1(lat, lon) retrieves elevation in meters

# Set this path to the modules directory
MODULES_PATH = 'E:\\Google Drive\\Google\\Programming\\python\\modules'

import sys
sys.path.insert(0, MODULES_PATH)

import matplotlib.pyplot as plt
import numpy as np
import math
import geo # An AWC module
import physics # An AWC module

# Set this to the directory where the terrain data files are located
TERRAIN_DIR = 'E:\\Google Drive\\BigFiles\\Google\\Databases\\Terrain\\3dep-1\\'

# These global variables are used to allow a terrain grid to be kept in memory
# until it is no longer needed.
CURRENT_GRID_FILE = ''
TDATA = np.zeros((3612,3612))

#######################
# FOR TESTING AND DEBUG
# Writes the intermediate terrain info to a csv file
DEBUG = False
import random
if DEBUG == True:
    fname = 'terrain%03d.csv' % random.uniform(0,999) 
    F_TEST = open(fname, 'w')
    F_TEST.write('point,lat,lon,interp,float_x,float_y,' \
             + 'xm or ix,xp or iy,"ym or TDATA[iy,ix]",yp,area_xm_ym,"TDATA[yp,xp]",area_xm_yp,' \
             + '"TDATA[ym,xp]",area_xp_yp,"TDATA[ym,xm]",area_xp_ym,' \
             + '"TDATA[yp,xm]",bilin_fit\n')
#######################


def gridFile(lat, lon):
    """
    Returns file name of the terrain grid tile that contains the specified
    lat/lon.
    
    Andrew Clegg
    October 2016
    """

#   The file name is the northwest corner of the tile
    ilat = math.ceil(lat)
    ilon = math.floor(lon)

    if ilat >= 0:
        gridfile = 'N%02d' % ilat
    else:
        gridfile = 'S%02d' % abs(ilat)

    if ilon >= 0:
        gridfile += 'E%03d' % ilon
    else:
        gridfile += 'W%03d' % abs(ilon)
    
    return gridfile + '.dat'


def readGridFile3DEP1(gridfile):
    """
    Reads a USGS 3DEP 1" terrain grid file into the global array TDATA.

    Note that gridfile should be the grid file base name, without the
    directory prepended. The directory is handled as a global variable
    declared above.

    If the file doesn't exist or can't be read, TDATA[:,:] = 0 and
    the return code is -1.
    
    Andrew Clegg
    October 2016
    """

    global TDATA
    global CURRENT_GRID_FILE

    xdim = ydim = 3612
    
    try:
        TDATA = np.fromfile(TERRAIN_DIR + gridfile, dtype=np.float32).reshape(ydim,xdim)
        CURRENT_GRID_FILE= gridfile
        return 0
    except:
        TDATA = np.zeros((3612,3612))
        CURRENT_GRID_FILE = gridfile
        return -1


def getTerrainElevation3DEP1(lat, lon, interp='none'):
    """
    Retrieves an elevation corresponding to the given lat/lon. The terrain
    data are 1" USGS 3DEP.
    
    Andrew Clegg
    October 2016
    """

    global CURRENT_GRID_FILE
    global TDATA
    global F_TEST #DEBUG
    global IPOINT #DEBUG
    
#   Resolution of terrain grid file in arc seconds
    res = 1.0

#   Number of overlapping pixels between neighboring terrain files
    xoverlap = yoverlap = 6

#   Check if this requires reading a new grid file. If so, read it. If the
#   file doesn't exist, display a warning and return 0 elevation.
    gridfile = gridFile(lat, lon)
    if gridfile <> CURRENT_GRID_FILE:
        if readGridFile3DEP1(gridfile) < 0:
            print 'No terrain file. Setting elevations to 0. ', gridfile
            return 0.0

    # Find the coordinates of this lat/lon in the tile file,
    # in floating point units. The -0.5 factor at the end compensates for
    # the half-pixel offset of the center from the edge.
    float_x = float(xoverlap) + 3600.*(lon - math.floor(lon))/res - 0.5
    float_y = float(yoverlap) + 3600.*(math.ceil(lat) - lat)/res - 0.5

    if interp.lower().strip() == 'bilinear':

        # Bilinear interpolation

        # Calculate the integer coordinates of the tile points that
        # are just below and just above the floating point coordinates
        xm = math.floor(float_x)
        xp = xm + 1
        ym = math.floor(float_y)
        yp = ym + 1

#       Calculate the areas used for weighting
        area_xm_ym = abs((float_x-xm)*(float_y-ym))
        area_xm_yp = abs((float_x-xm)*(float_y-yp))
        area_xp_yp = abs((float_x-xp)*(float_y-yp))
        area_xp_ym = abs((float_x-xp)*(float_y-ym))

#       Find and warn of bad data
        if TDATA[yp, xp] < -9000:
            TDATA[yp, xp] = 0.
            print 'Bad terrain data'
        if TDATA[ym, xp] < -9000:
            TDATA[ym, xp] = 0.
            print 'Bad terrain data'
        if TDATA[ym, xm] < -9000:
            TDATA[ym, xm] = 0.
            print 'Bad terrain data'
        if TDATA[yp, xm] < -9000:
            TDATA[yp, xm] = 0.
            print 'Bad terrain data'
            
#       Weight each of the four grid points by the opposite area
        value =  area_xm_ym * TDATA[yp, xp] \
               + area_xm_yp * TDATA[ym, xp] \
               + area_xp_yp * TDATA[ym, xm] \
               + area_xp_ym * TDATA[yp, xm]
            
        if DEBUG == True:
            IPOINT += 1
            F_TEST.write(        str(IPOINT)
                         + ',' + str(lat)
                         + ',' + str(lon)
                         + ',' + interp
                         + ',' + str(float_x)
                         + ',' + str(float_y)
                         + ',' + str(xm)
                         + ',' + str(xp)
                         + ',' + str(ym)
                         + ',' + str(yp)
                         + ',' + str(area_xm_ym)
                         + ',' + str(TDATA[yp, xp])
                         + ',' + str(area_xm_yp)
                         + ',' + str(TDATA[ym, xp])
                         + ',' + str(area_xp_yp)
                         + ',' + str(TDATA[ym, xm])
                         + ',' + str(area_xp_ym)
                         + ',' + str(TDATA[yp, xm])
                         + ',' + str(value)
                         + '\n')
                                 
        return value
    
    else:

        # Return the elevation of the nearest point
        # The +0.5 factor compensates for the half-pixel offset
        # previously added to compensate for the half-width of the pixel.
        ix = int(float_x + 0.5)
        iy = int(float_y + 0.5)

        if DEBUG == True:
            IPOINT += 1
            F_TEST.write(        str(IPOINT)
                         + ',' + str(lat)
                         + ',' + str(lon)
                         + ',' + interp
                         + ',' + str(float_x)
                         + ',' + str(float_y)
                         + ',' + str(ix)
                         + ',' + str(iy)
                         + ',' + str(TDATA[iy,ix])
                         + '\n')
        if TDATA[iy, ix] < -9000:
            print 'Bad terrain point'
            return 0
        else:
            return TDATA[iy, ix]


def terrainProfile(lat1, lon1, lat2, lon2, target_dx = -1, interp = 'bilinear',
                   winnf=False, res = 1.):
    """
    Returns the terrain profile along the great circle path between the two
    lat/lon pairs. If npts > 2, the profile consists of npts equally-spaced points
    starting at lat1/lon1 and ending at lat2/lon2. If npts < 3, then the
    routine uses the closest spacing greater than target_dx in size such that an
    integer number of points is returned. If neither input is valid, target_dx
    is set to sqrt(2) * dy, where dy is the N/S spatial resolution of the dataset.

    Inputs:
        lat1, lon1      lat/lon of starting point (deg)
        lat2, lon2      lat/lon of end point (deg)
        npts            Number of desired points in profile
        target_dx       Target resolution between points (m) (>= 1 m)
        res             Dataset resolution (arc seconds)
        winnf           If True, uses WinnForum requirement for paths over 45 km

    Output:
        elev[npts+2]    Elevation array in ITS format
                        elev[0] = number of terrain points - 1 (i.e., npts-1)
                        elev[1] = distance between sample points (m)
                        elev[2]...elev[npts+1] = Terrain elevation (m)

    Andrew Clegg
    November 2016
    """

    d = geo.dist(lat1, lon1, lat2, lon2, 'm') # Distance between end points (m)

    if target_dx < 1:
        target_dx = 1000. * physics.Re * math.radians(res/3600.)

    if d > 45000. and winnf:
        npts = 1500
    else:
        npts = int(d/target_dx) + 1
        
    dx = d/float(npts-1)
    
    lat = lat1
    lon = lon1

    elev = [npts-1, dx, getTerrainElevation3DEP1(lat, lon, interp)]
    
    for i in range(1, npts-1):
        b = geo.bearing(lat, lon, lat2, lon2)
        lat, lon = geo.to_dist_bearing(lat, lon, dx, b, 'm')
        elev.append(getTerrainElevation3DEP1(lat, lon, interp))

    elev.append(getTerrainElevation3DEP1(lat2, lon2, interp))

    return elev

def terrainProfile_vincenty(lat1, lon1, lat2, lon2, target_dx = -1,
                            interp = 'none', winnf=False, res = 1.):
    """
    Returns the terrain profile along the vincenty path between the two
    lat/lon pairs. If npts > 2, the profile consists of npts equally-spaced points
    starting at lat1/lon1 and ending at lat2/lon2. If npts < 3, then the
    routine uses the closest spacing greater than target_dx in size such that an
    integer number of points is returned. If neither input is valid, target_dx
    is set to sqrt(2) * dy, where dy is the N/S spatial resolution of the dataset.

    Inputs:
        lat1, lon1      lat/lon of starting point (deg)
        lat2, lon2      lat/lon of end point (deg)
        npts            Number of desired points in profile
        target_dx       Target resolution between points (m) (>= 1 m)
        res             Dataset resolution (arc seconds)
        winnf           If True, uses WinnForum requirement for paths over 45 km

    Output:
        elev[npts+2]    Elevation array in ITS format
                        elev[0] = number of terrain points - 1 (i.e., npts-1)
                        elev[1] = distance between sample points (m)
                        elev[2]...elev[npts+1] = Terrain elevation (m)

    Andrew Clegg
    November 2016
    """

    d, azstart, backaz = \
       geo.dist_bear_vincenty(lat1, lon1, lat2, lon2) # Distance between end points (m)
    d *= 1000. # convert to m
    
    if target_dx < 1:
        target_dx = 1000. * physics.Re * math.radians(res/3600.)

    if d > 45000. and winnf:
        npts = 1500
    else:
        npts = int(d/target_dx) + 1
        
    dx = d/float(npts-1)
    
    lat = lat1
    lon = lon1

    elev = [npts-1, dx, getTerrainElevation3DEP1(lat, lon, interp)]
    
    for i in range(1, npts-1):
        d, b, backaz = geo.dist_bear_vincenty(lat, lon, lat2, lon2)
        lat, lon, az = geo.to_dist_bear_vincenty(lat, lon, dx/1000., b)
        elev.append(getTerrainElevation3DEP1(lat, lon, interp))

    elev.append(getTerrainElevation3DEP1(lat2, lon2, interp))

    return elev
