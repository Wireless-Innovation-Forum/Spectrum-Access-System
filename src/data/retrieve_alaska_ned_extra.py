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
US territories.
It has been found that some tiles are missing for Alaska as shown in:
  https://viewer.nationalmap.gov/basic/?basemap=b1&category=ned,nedsrc&title=3DEP%20View#productGroupSearch

This script retrieves missing tiles from the 2 arcsecond (~60m) database for Alaska,
and resample such tiles to 1 arcsec for consistent processing within test harness.
It is designed to be run *after* the `retrieve_orig_ned.py` script.
"""

import ftputil
import os
import re

curDir = os.path.dirname(os.path.realpath(__file__))
# Destination dir for snapshot
destDir = os.path.join(curDir, '..', '..', 'data', 'geo', 'orig_ned')
# Reference dir for existing 1 arcsec NED data as generated by
# script `retrieve_orig_ned.py`
refDir =  os.path.join(curDir, '..', '..', 'data', 'geo', 'ned')

# Retrieve the desired NED zip files from the USGS FTP site.
def FindArcFloatFilenames(usgs):
  files = usgs.listdir('vdelivery/Datasets/Staged/Elevation/2/GridFloat/')
  print 'Found %d files in USGS ftp dir' % len(files)
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

  print 'Found %d matching elevation tiles in USGS ftp dir' % len(matches)
  return matches

# Check if a filename corresponds to a preexisting tile
def AlreadyExistInDatabase(filename):
  # Detect the tile info
  m = re.search('.*?([ns])(\d{1,3})([ew])(\d{1,3}).*?', f)
  if not m:
    raise Exception('Could not find lat,lng for %s' % f)
  # Check if preexisting tile at 1 arcsec
  preexist = False
  tile_name1 = 'USGS_NED_1_%s%s%s%s_GridFloat.zip' % (
      m.group(1), m.group(2), m.group(3), m.group(4))
  tile_name2 = '%s%s%s%s.zip' % (
      m.group(1), m.group(2), m.group(3), m.group(4))
  if (os.path.isfile(os.path.join(refDir, tile_name1)) or
      os.path.isfile(os.path.join(refDir, tile_name2))):
    return True

  return False


# Fetch via FTP all the qualifying NED 2-arc-second tiles that are missing
# from current reference dir. Writes them to the destination directory
def RetrieveMissingElevationTiles():
  ned = ftputil.FTPHost('rockyftp.cr.usgs.gov', 'anonymous', '')
  files = FindArcFloatFilenames(ned)
  for f in files:
    if AlreadyExistInDatabase(f):
      continue
    print 'Downloading %s' % f
    ned.download_if_newer('vdelivery/Datasets/Staged/Elevation/2/GridFloat/' + f, f)

  ned.close()


# Find the directory of this script.
print 'Retrieving USGS 2-arc-second tiles to dir=%s' % destDir
if not os.path.exists(destDir):
  os.makedirs(destDir)
os.chdir(destDir)
RetrieveMissingElevationTiles()
