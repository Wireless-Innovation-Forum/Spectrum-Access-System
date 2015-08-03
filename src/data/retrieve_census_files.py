#    Copyright 2015 SAS Project Authors. All Rights Reserved.
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

# This script retrieves the tiger/shapefiles from the US Census. It writes
# them into the data/census directory. If the .zip files already exist, the
# script will only download files if they are newer than the local versions.

import ftputil
import os
import re

# Retrieve the desired state-level census tract zip files from the census
# FTP site.
def FindStateTractFilenames(census):
  files = census.listdir('geo/tiger/TIGER2010/TRACT/2010/')
  print 'Found %d files in census ftp dir' % len(files)
  matches = []
  for f in files:
    if re.match('tl_2010_\d\d_tract10.zip$', f):
      matches.append(f)
  print 'Found %d matching state files in census tract ftp dir' % len(matches)
  return matches


# Fetch via FTP all the 2010 census tract state shapefiles. Writes them
# to the current directory.
def RetrieveShapefiles():
  census = ftputil.FTPHost('ftp2.census.gov', 'anonymous', '')
  files = FindStateTractFilenames(census)

  for f in files:
    print 'Downloading %s' % f
    census.download_if_newer('geo/tiger/TIGER2010/TRACT/2010/' + f, f)
  census.close()

# Find the directory of this script.
dir = os.path.dirname(os.path.realpath(__file__))
rootDir = os.path.dirname(os.path.dirname(dir))
dest = os.path.join(os.path.join(rootDir, 'data'), 'census')
print 'Retrieving census shapefiles to dir=%s' % dest
if not os.path.exists(dest):
  os.makedirs(dest)
os.chdir(dest)
RetrieveShapefiles()

