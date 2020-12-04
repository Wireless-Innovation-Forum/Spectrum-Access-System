#    Copyright 2016 SAS Project Authors. All Rights Reserved.
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

"""This script retrieves the missing NED ArcFloat terrain tiles for Alaska.

The `retrieve_orig_ned.py` retrieves all 1 arcsec tiles made available by USGS for
all US territories.
It has been found that some tiles are missing for Alaska as shown in:
  https://viewer.nationalmap.gov/basic/?basemap=b1&category=ned,nedsrc&title=3DEP%20View#productGroupSearch

This script retrieves missing tiles from the 2 arcsecond (~60m) database for Alaska,
and resample such tiles to 1 arcsec for consistent processing within test harness.
It is designed to be run *after* the `retrieve_orig_ned.py` script.

Usage:
  This script assumes there are 3 directories:

  - orig_ned2/: the snapshot directory of downloaded 2'' files. If this directory
  is populated, then only newer files will be downloaded and processed (by
  comparison with files present in that directory). Typically one would keep this
  directory alive, and every new run would update only newer files.

  - ned_out2/: the output directory of finalized zipped tiles. This is where the
  final zip files are created, holding just the required ArcFloat and header
  files (in a zip archive), using the final naming required by the terrain driver.
  The content of this directory shall be pushed into the SAS-Data/ned/ repository.

  - ned/: the reference directory of existing (final) tiles. This is used to
  detect which tiles are missing in the 1'' database, that can be replaced by a
  resampled 2'' tile.
"""

import ftputil
import os
import re
import zipfile
import numpy as np

curDir = os.path.dirname(os.path.realpath(__file__))

# Download dir for snapshot
downloadDir = os.path.join(curDir, '..', '..', 'data', 'geo', 'orig_ned2')

# Output dir for final NED tiles
outDir =  os.path.join(curDir, '..', '..', 'data', 'geo', 'ned_out2')

# Reference dir for existing 1'' NED tiles
refDir =  os.path.join(curDir, '..', '..', 'data', 'geo', 'ned')


# Retrieve the desired NED zip files from the USGS FTP site.
def FindArcFloatFilenames(usgs):
  files = usgs.listdir('vdelivery/Datasets/Staged/Elevation/2/GridFloat/')
  print('Found %d files in USGS ftp dir' % len(files))
  files.sort()
  files.reverse()
  matches = []
  for f in files:
    filematch = False
    if re.match('USGS_NED_2_[ns]\d{1,3}[ew]\d{1,3}_GridFloat.zip$', f):
      filematch = True
    if re.match('[ns]\d{1,3}[ew]\d{1,3}.zip$', f):
      filematch = True

    if not filematch:
      continue

    m = re.search('.*?([ns])(\d{1,3})([ew])(\d{1,3}).*?', f)
    lat = 0
    lng = 0
    if m:
      lat = int(m.group(2))
      lng = int(m.group(4))
      if m.group(1) == 's':
        lat = lat * -1
      if m.group(3) == 'w':
        lng = lng * -1
    else:
      raise Exception('Could not find lat,lng for %s' % f)

    # Prune tiles to ones within or near US borders. Stay coherent with
    # the filtering conditions of retrieve_orig_ned.py
    geomatch = True
    if lat < 51:
      geomatch = False
    if lat > 50 and (lng < -50 and lng > -127):
      geomatch = False
    if lat > 61 and (lng < -100 and lng > -139):
      geomatch = False
    if geomatch:
      matches.append(f)

    # Prune tiles obsoleted by newer NED data.
    if f.startswith('USGS_NED_2_'):
      obsolete_filename = m.group(1) + m.group(2) + m.group(3) + m.group(4) + '.zip'
      if obsolete_filename in matches:
        matches.remove(obsolete_filename)

  print('Found %d matching elevation tiles in USGS ftp dir' % len(matches))
  return matches


# Check if a filename corresponds to a preexisting tile
def AlreadyExistInDatabase(filename, ref_dir):
  # Detect the tile info
  m = re.search('.*?([ns])(\d{1,3})([ew])(\d{1,3}).*?', filename)
  if not m:
    raise Exception('Could not find lat,lng for %s' % f)
  # Check if preexisting tile at 1 arcsec
  preexist = False
  tile_name1 = 'usgs_ned_1_%s%s%s%s_gridfloat_std.zip' % (
      m.group(1), m.group(2), m.group(3), m.group(4))
  tile_name2 = 'float%s%s%s%s_1_std.zip' % (
      m.group(1), m.group(2), m.group(3), m.group(4))
  if (os.path.isfile(os.path.join(ref_dir, tile_name1)) or
      os.path.isfile(os.path.join(ref_dir, tile_name2))):
    return True

  return False


# Extract the Arcfloat and headers, resample and zip them
def ExtractArcFloatToZipAndResample(fname, out_dir, new_download):
  m = re.search('.*?([ns])(\d{1,3})([ew])(\d{1,3}).*?', fname)
  tile_name = '%s%s%s%s' % (m.group(1), m.group(2), m.group(3), m.group(4))
  # Ignore the tile if at -180degree, as these ones need special processing
  # (different padding)
  if m.group(4) == '180':
    print('....ignoring west bound 180deg tile %s' % fname)
    return
  if fname.startswith('USGS_NED'):
    basename = 'usgs_ned_2_%s' % (tile_name)
    out_basename = 'usgs_ned_1_%s_gridfloat_std' % (tile_name)
  else:
    basename = 'float%s' % (tile_name)
    out_basename = '%s_1_std' % (basename)

  out_zip_file = os.path.join(out_dir, out_basename + '.zip')
  # Early stop - ignore if the output zip already exist and not newer download
  exists = os.path.exists(out_zip_file)
  if exists and not new_download:
    print('..alreay exist and latest')
    return
  print('..creating final archive')
  with zipfile.ZipFile(fname, 'r') as in_zip:
    with  zipfile.ZipFile(out_zip_file, 'w') as out_zip:
      for in_name in in_zip.namelist():
        if in_name.lower().startswith(basename) and in_name.endswith('flt'):
          data = in_zip.read(in_name)
          # Convert the data to ndarray
          elev2 = np.frombuffer(data,
                               dtype=np.dtype(np.float32).newbyteorder('<'))
          elev2 = elev2.reshape(1812, 1812)
          # Create the bilinear resampled matrix, keeping the no-values
          elev = np.zeros((3624, 3624), dtype=np.float32)
          elev[1:-2:2, 1:-2:2] = 1/16. * (9 * elev2[:-1,:-1] + 1 * elev2[1:,  1:] +
                                          3 * elev2[:-1, 1:] + 3 * elev2[1:, :-1])
          elev[2:-1:2, 1:-2:2] = 1/16. * (9 * elev2[1:, :-1] + 1 * elev2[:-1, 1:] +
                                          3 * elev2[1:, 1: ] + 3 * elev2[:-1,:-1])
          elev[1:-2:2, 2:-1:2] = 1/16. * (9 * elev2[:-1, 1:] + 1 * elev2[1:, :-1] +
                                          3 * elev2[:-1,:-1] + 3 * elev2[1:, 1: ])
          elev[2:-1:2, 2:-1:2] = 1/16. * (9 * elev2[1:, 1: ] + 1 * elev2[:-1,:-1] +
                                          3 * elev2[1:, :-1] + 3 * elev2[:-1, 1:])
          elev[elev < -200] = -9999
          elev = elev[6:-6, 6:-6]
          # Now store in archive all 3 file data
          data_out = elev.tobytes()
          out_zip.writestr(out_basename + '.flt', data_out,
                           compress_type=zipfile.ZIP_DEFLATED)

          prj_str = """Projection    GEOGRAPHIC
Datum         NAD83
Zunits        METERS
Units         DD
Spheroid      GRS1980
Xshift        0.0000000000
Yshift        0.0000000000
Parameters\n"""
          lat_nw = int(m.group(2)) if (m.group(1) == 'n') else -int(m.group(2))
          lon_nw = int(m.group(4)) if (m.group(3) == 'e') else -int(m.group(4))
          hdr_str = """ncols         3612
nrows         3612
xllcorner     %d.00166666667
yllcorner     %d.99833333333
cellsize      0.0002777777777777778
NODATA_value  -9999
byteorder     LSBFIRST\n""" % (lon_nw, lat_nw-2)
          out_zip.writestr(out_basename + '.prj', prj_str)
          out_zip.writestr(out_basename + '.hdr', hdr_str)



# Fetch via FTP all the qualifying NED 2-arc-second tiles that are missing
# from current reference dir. Writes them to the destination directory.
def RetrieveMissingElevationTilesAndProcess(out_dir, ref_dir):
  ned = ftputil.FTPHost('rockyftp.cr.usgs.gov', 'anonymous', '')
  files = FindArcFloatFilenames(ned)
  for f in files:
    if AlreadyExistInDatabase(f, ref_dir):
      continue
    print('Checking %s' % f)
    downloaded = ned.download_if_newer(
        'vdelivery/Datasets/Staged/Elevation/2/GridFloat/' + f, f)
    # Optionally extract the actual data and save in ref dir
    ExtractArcFloatToZipAndResample(f, out_dir, downloaded)

  ned.close()


# Find the directory of this script.
print('Retrieving USGS 2-arc-second tiles to dir=%s' % downloadDir)
if not os.path.exists(downloadDir):
  os.makedirs(downloadDir)

if not os.path.exists(outDir):
  os.makedirs(outDir)

if not os.path.exists(refDir):
  raise Exception('reference dir %s does not exist' % refDir)

os.chdir(downloadDir)

# Retrieve all the newest tiles into destination dir and create the tiles in the
# reference directory
RetrieveMissingElevationTilesAndProcess(outDir, refDir)
