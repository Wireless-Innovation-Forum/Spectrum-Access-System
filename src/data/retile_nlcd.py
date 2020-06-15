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

"""Script to retile original NLCD in small 1x1 degree tiles in WGS84
unprojected space, at multiple of 1 arcseconds.
"""

import datetime
import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import zipfile

from reference_models.geo import tiles
import nlcd_origin

cur_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(cur_dir, '..', '..', 'data')

# ***** Start Configuration *****
# If needed, modify these directories to fit your local directory structure:
#  - where the NED terrain tiles are stored
TERRAIN_DIR = os.path.join(data_dir, 'geo', 'ned')
USE_TERRAIN_DIR = False

#  - where the original USGS NLCD file is stored.
NLCD_ORIG_DIR = os.path.join(data_dir, 'geo', 'orig_nlcd')

#  - where to put the generated tiles.
OUT_DIR = os.path.join(data_dir, 'geo', 'nlcd_out')

# - reference dir of existing tiles
REF_DIR = os.path.join(data_dir, 'geo', 'nlcd')

# If set to True, will create a jpg file per tile.
create_jpg = True

# ***** End Configuration *****

# If you want to process only part of the original files, simply comment out
# the files
ORIG_NLCD_FILES = [
    # Conus might be replaced by this one if upgrading NLCD at some point:
    # #'NLCD_2011_Land_Cover_L48_20190424.img',
    #'nlcd_2011_landcover_2011_edition_2014_10_10.img'
    #'ak_nlcd_2011_landcover_1_15_15.img',
    'hi_landcover_wimperv_9-30-08_se5.img',
    'pr_landcover_wimperv_10-28-08_se5.img']


def ParseLatLonFromNedFile(fname):
  """Parses the latitude and longitude from a NED DEM tile.

  Currently two different formats exist on the server. They look like the
  following examples:
    floatn34w086_xxx          Filename format used prior to 2015
    usgs_ned_1_n34w086_xxx    Filename format used since 2015

  Inputs:
    fname: filename of a NED DEM tile.

  Returns:
    a tuple of (lat, lon) being the North-West corner of that tile.
  """
  if fname[0].lower() == 'f':
    lat = int(fname[6:8])
    lon = int(fname[9:12])
    if fname[5].lower() == 's':
      lat = -lat
    if fname[8].lower() == 'w':
      lon = -lon
  elif fname[0].lower() == 'u':
    lat = int(fname[12:14])
    lon = int(fname[15:18])
    if fname[11].lower() == 's':
      lat = -lat
    if fname[14].lower() == 'w':
      lon = -lon
  else:
    lat = 0
    lon = 0

  return lat, lon


def ParseLatLonFromNlcdFile(fname):
  """Parses the latitude and longitude from a NLCD tile.

  Inputs:
    fname: filename of a NLCD tile.

  Returns:
    a tuple of (lat, lon) being the North-West corner of that tile.
  """
  lat = int(fname[6:8])
  lon = int(fname[9:12])
  if fname[5].lower() == 's':
    lat = -lat
  if fname[8].lower() == 'w':
    lon = -lon

  return lat, lon


# Main script to retile the NLCD
if __name__ == '__main__':

  if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

  # Log file
  log_file = os.path.join(OUT_DIR, 'nlcd_log.csv')
  if not os.path.isfile(log_file):
    with open(log_file, 'w') as fd:
      fd.write('Lat,Lon,DateTime,NumZero\n')
      fd.close()
  log_fd = open(log_file, 'a')

  # Initialise the terrain tile list
  if USE_TERRAIN_DIR:
    ned_latlon = []
    # Detect the tiles from the NED dir
    terrain_tiles = glob.glob(os.path.join(TERRAIN_DIR, '*.flt'))
    terrain_tiles = [os.path.basename(tile) for tile in terrain_tiles]
    ned_latlon = [ParseLatLonFromNedFile(tile)
                  for tile in terrain_tiles]
    ned_latlon.sort()
  else:
    # Get the tiles from the geo.tiles module
    ned_latlon = list(tiles.NED_TILES)
    ned_latlon.sort()

  # Discover the already processed NLCD tiles
  nlcd_tiles = glob.glob(os.path.join(REF_DIR, '*.zip'))
  nlcd_tiles = [os.path.basename(tile) for tile in nlcd_tiles]
  processed_latlon = [ParseLatLonFromNlcdFile(tile)
                      for tile in nlcd_tiles]

  # Build the coordinates to retrieve at multiple of 1 arcsec
  coord = np.arange(3600) * 1/3600.

  # Loop on original NLCD files
  for orig_file in ORIG_NLCD_FILES:
    print('Processing NLCD file : %s' % orig_file)

    # Initialize the driver - in manual loading mode
    try:
      driver = nlcd_origin.NlcdOriginDriver(
          os.path.join(NLCD_ORIG_DIR, orig_file),
          data_mode=0)
    except Exception:
      print('  ... FILE NOT FOUND')
      continue

    for lat_nw, lon_nw in ned_latlon:

      if (lat_nw, lon_nw) in processed_latlon:
        print('Tile [%d %d] already done. Skipping...' % (lat_nw, lon_nw))
        continue

      # Create the output file name
      encoding = '%c%02d%c%03d' % (
          'sn'[lat_nw >= 0], abs(lat_nw),
          'we'[lon_nw >= 0], abs(lon_nw))

      tile_name = 'nlcd_' + encoding + '_ref.int'

      print('** Processing NLCD tile: %s (Lat%d Lng%d)' % (tile_name, lat_nw, lon_nw))

      # Load the original required tile
      ret = driver.CacheTileInBox(lat_min=lat_nw-1, lat_max=lat_nw,
                                  lon_min=lon_nw, lon_max=lon_nw+1)
      if ret is None:
        print('        ..Skipping - Outside')
        continue

      # Check to see if a corresponding NLCD tile exists for the
      # midpoint of this lat/lon square
      nlcd = np.zeros((3600, 3600)).astype(np.uint8)
      lat = lat_nw - coord
      lon = lon_nw + coord
      cnt_codes_zero = 0
      for k in range(3600):
        if (k+1) % 600 == 0:
          sys.stdout.write('+')
          sys.stdout.flush()
        codes = driver.GetLandCoverCodes(lat[k] * np.ones(3600), lon)
        nlcd[k, :] = codes
        cnt_codes_zero += 3600 - np.count_nonzero(codes)
      print('  Number of zero code = %d' % cnt_codes_zero)

      # Skip saving tile if fully empty
      if cnt_codes_zero >= 3600*3600:
        print('        ..Skipping - All zero')
        continue

      print('        ..Saving & zipping')
      nlcd.tofile(os.path.join(OUT_DIR, tile_name))

      # Create the header files
      hdr_name = tile_name[:-4] + '.hdr'
      with open(os.path.join(OUT_DIR, hdr_name), 'w') as fd:
        fd.write(
            'ncols         3600\n'
            'nrows         3600\n'
            'xllcorner     %.12f\n'
            'yllcorner     %.12f\n'
            'cellsize      0.0002777777777777778\n'
            'NODATA_value  0\n'
            'byteorder     LSBFIRST\n'
            % (lon_nw - 0.5/3600., lat_nw - 1 + 0.5/3600.))
      prj_name = tile_name[:-4] + '.prj'
      with open(os.path.join(OUT_DIR, prj_name), 'w') as fd:
        fd.write(
            'Projection    GEOGRAPHIC\n'
            'Datum         WGS84\n'
            'Zunits        METERS\n'
            'Units         DD\n'
            'Spheroid      GRS1980\n'
            'Xshift        0.0000000000\n'
            'Yshift        0.0000000000\n'
            'Parameters\n')

      # Save as zip
      zip_file = tile_name[:-4] + '.zip'
      with zipfile.ZipFile(os.path.join(OUT_DIR, zip_file), 'w') as z:
        z.write(os.path.join(OUT_DIR, tile_name), tile_name,
                compress_type=zipfile.ZIP_DEFLATED)
        z.write(os.path.join(OUT_DIR, hdr_name), hdr_name,
                compress_type=zipfile.ZIP_DEFLATED)
        z.write(os.path.join(OUT_DIR, prj_name), prj_name,
                compress_type=zipfile.ZIP_DEFLATED)

      # Save infos to log
      log_fd.write(str(lat_nw) + ',' +
                   str(lon_nw) + ',' +
                   str(datetime.datetime.now()) + ',' +
                   str(cnt_codes_zero) + '\n')

      # Optionally create a jpg figure plot
      if create_jpg:
        aspect = 1./np.cos(np.radians(lat_nw-0.5))
        plt.imshow(nlcd, extent=[lon_nw, lon_nw+1, lat_nw-1, lat_nw],
                   aspect=aspect)
        plt.title(tile_name[:-4])
        plt.grid()
        plt.colorbar()
        plt.savefig(os.path.join(OUT_DIR, tile_name[:-4] + '.png'))
        plt.close()
