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

# This script retrieves the NED ArcFloat files from the National Elevation
# Map at 1 arc-second (~30m) resolution. It writes them into the data/ned
# directory. If the .zip files already exist, the script will only
# download files if they are newer than the local versions.

import ftputil
import os
import re
import urllib2

# Retrieve the desired NED zip files from the USGS FTP site.
def FindArcFloatFilenames(usgs):
  files = usgs.listdir('vdelivery/Datasets/Staged/Elevation/1/GridFloat/')
  print 'Found %d files in USGS ftp dir' % len(files)
  matches = []
  for f in files:
    if re.match('USGS_NED_1_[ns]\d{1,3}[ew]\d{1,3}_GridFloat.zip$', f):
      matches.append(f)
    if re.match('[ns]\d{1,3}[ew]\d{1,3}.zip$', f):
      matches.append(f)
  print 'Found %d matching elevation tiles in USGS ftp dir' % len(matches)
  return matches


# Fetch via FTP all the qualifying NED 1-arc-second tiles. Writes them
# to the current directory.
def RetrieveElevationTiles():
  ned = ftputil.FTPHost('rockyftp.cr.usgs.gov', 'anonymous', '')
  files = FindArcFloatFilenames(ned)

  for f in files:
    print 'Downloading %s' % f
    ned.download_if_newer('vdelivery/Datasets/Staged/Elevation/1/GridFloat/' + f, f)
  ned.close()

def RetrieveNLCD_CONUS():
  print 'Retrieving NLCD for CONUS...'
  nlcd = urllib2.urlopen(
    'http://www.landfire.gov/bulk/downloadfile.php?TYPE=nlcd2011&FNAME=nlcd_2011_landcover_2011_edition_2014_10_10.zip')
  if not nlcd.getcode() == 200:
    raise Exception('Could not find NLCD CONUS file')
  with open('nlcd_2011_landcover_2011_edition_2014_10_10.zip', 'wb') as out:
    while True:
      c = nlcd.read(64*1024)
      if not c:
        break
      out.write(c)
  nlcd.close()
  print 'Retrieved NLCD for CONUS'

def RetrieveNLCD_AK():
  print 'Retrieving NLCD for CONUS...'
  nlcd = urllib2.urlopen(
    'http://www.landfire.gov/bulk/downloadfile.php?TYPE=nlcd2011&FNAME=ak_nlcd_2011_landcover_1_15_15.zip')
  if not nlcd.getcode() == 200:
    raise Exception('Could not find NLCD CONUS file')
  with open('ak_nlcd_2011_landcover_1_15_15.zip', 'wb') as out:
    while True:
      c = nlcd.read(64*1024)
      if not c:
        break
      out.write(c)
  nlcd.close()
  print 'Retrieved NLCD for CONUS'


# Find the directory of this script.
dir = os.path.dirname(os.path.realpath(__file__))
rootDir = os.path.dirname(os.path.dirname(dir))
dest = os.path.join(os.path.join(rootDir, 'data'), 'ned')
print 'Retrieving USGS 1-arc-second tiles to dir=%s' % dest
if not os.path.exists(dest):
  os.makedirs(dest)
os.chdir(dest)
RetrieveElevationTiles()

os.chdir(rootDir)
dest = os.path.join(os.path.join(rootDir, 'data'), 'nlcd')
print 'Retrieving NLCD files to dir=%s' % dest
if not os.path.exists(dest):
  os.makedirs(dest)
os.chdir(dest)
RetrieveNLCD_CONUS()
RetrieveNLCD_AK()

