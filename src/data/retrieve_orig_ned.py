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

"""This script retrieves the NED ArcFloat files from the National Elevation
Map at 1 arc-second (~30m) resolution directly from USGS directory.
It writes them into the data/ned_orig directory.
If the .zip files already exist, the script will only download files if
they are newer than the local versions.

Warning:
NED tiles are often updated in the USGS site.This script is provided for when
the reference NED database shall be updated.

The official set of reference NED files (to be used in SAS) are the ones stored
in the SAS-Data repository, usually reachable with geo/ned soft link.
This set is frozen and will be updated only on specific schedule, so that all
 SAS providers use the same reference geo data.

Usage:
  This script assumes there are 2 directories:

  - orig_ned/: the snapshot directory of downloaded file. If this directory is
  populated, then only newer files will be downloaded and processed (by
  comparison with files present in that directory). Typically one would keep this
  directory alive, and every new run would update only newer files.

  - ned_out/: the output directory of finalized zipped tiles. This is where the
  final zip files are created, holding just the required ArcFloat and header
  files (in a zip archive), using the final naming required by the terrain driver.
  The content of this directory shall be pushed into the SAS-Data/ned/ repository.
"""

import ftputil
import os
import re
import zipfile

curDir = os.path.dirname(os.path.realpath(__file__))

# Download dir for snapshot
downloadDir = os.path.join(curDir, '..', '..', 'data', 'geo', 'orig_ned')

# Output dir for final NED tiles
outDir =  os.path.join(curDir, '..', '..', 'data', 'geo', 'ned_out')

# Retrieve the desired NED zip files from the USGS FTP site.
def FindArcFloatFilenames(usgs):
  files = usgs.listdir('vdelivery/Datasets/Staged/Elevation/1/GridFloat/')
  print('Found %d files in USGS ftp dir' % len(files))
  files.sort()
  files.reverse()
  matches = []
  for f in files:
    filematch = False
    if re.match('USGS_NED_1_[ns]\d{1,3}[ew]\d{1,3}_GridFloat.zip$', f):
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

    # Prune tiles to ones within or near US borders.
    geomatch = True
    if lat < 25 and (lng < -85 and lng > -120):
      geomatch = False
    if lat > 50 and (lng < -50 and lng > -127):
      geomatch = False
    if lat > 61 and (lng < -100 and lng > -139):
      geomatch = False
    if lat < 29 and (lng < -107 and lng > -119):
      geomatch = False
    if geomatch:
      matches.append(f)

    # Prune tiles obsoleted by newer NED data.
    if f.startswith('USGS_NED_1_'):
      obsolete_filename = m.group(1) + m.group(2) + m.group(3) + m.group(4) + '.zip'
      if obsolete_filename in matches:
        matches.remove(obsolete_filename)

  print('Found %d matching elevation tiles in USGS ftp dir' % len(matches))
  return matches


# Extract the Arcfloat and headers and zip them
def ExtractArcFloatToZip(fname, out_dir):
  m = re.search('.*?([ns])(\d{1,3})([ew])(\d{1,3}).*?', fname)
  tile_name = '%s%s%s%s' % (m.group(1), m.group(2), m.group(3), m.group(4))
  if fname.startswith('USGS_NED'):
    basename = 'usgs_ned_1_%s' % (tile_name)
    out_basename = '%s_gridfloat_std' % (basename)
  else:
    basename = 'float%s' % (tile_name)
    out_basename = '%s_1_std' % (basename)
  with zipfile.ZipFile(fname, 'r') as in_zip:
    with  zipfile.ZipFile(os.path.join(out_dir, out_basename + '.zip'),
                          'w') as out_zip:
      for in_name in in_zip.namelist():
        if in_name.lower().startswith(basename) and (
            in_name.endswith('prj') or
            in_name.endswith('hdr') or
            in_name.endswith('flt')):
          data = in_zip.read(in_name)
          out_zip.writestr(out_basename + '.' + in_name[-3:], data)


# Fetch via FTP all the qualifying NED 1-arc-second tiles (only if not newer
# than same file in current directory).
# Writes them to the destination directory in zip archive with proper naming.
def RetrieveElevationTilesAndProcess(out_dir):
  ned = ftputil.FTPHost('rockyftp.cr.usgs.gov', 'anonymous', '')
  files = FindArcFloatFilenames(ned)
  downloaded_files = []
  for f in files:
    print('Checking %s' % f)
    downloaded = ned.download_if_newer(
        'vdelivery/Datasets/Staged/Elevation/1/GridFloat/' + f, f)
    if downloaded:
      # Extract the actual data and save in out dir
      print('..creating final archive for %s' % f)
      ExtractArcFloatToZip(f, out_dir)

  ned.close()


# Find the directory of this script.
print('Retrieving USGS 1-arc-second tiles to dir=%s' % downloadDir)
if not os.path.exists(downloadDir):
  os.makedirs(downloadDir)
if not os.path.exists(outDir):
  os.makedirs(outDir)

os.chdir(downloadDir)

# Retrieve all the newest tiles in destination dir and create the tiles in the
# reference directory
RetrieveElevationTilesAndProcess(outDir)
