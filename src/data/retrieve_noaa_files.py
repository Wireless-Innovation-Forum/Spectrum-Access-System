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

# This script retrieves the NOAA data files.
# The script writes the files into the data/noaa directory.

import os
import urllib2

# Retrieve all the NOAA data files into the current directory.
def RetrieveNOAA():
  print 'Retrieving border definition file...'
  border = urllib2.urlopen(
      'http://maritimeboundaries.noaa.gov/downloads/USMaritimeLimitsAndBoundariesKML.kmz')
  if not border.getcode() == 200:
    raise Exception('Could not find border definition file')

  with open('USMaritimeLimitsAndBoundariesKML.kmz', 'wb') as out:
    while True:
      c = border.read(64*1024)
      if not c:
        break
      out.write(c)
  border.close()
  print 'Retrieved border definition file...'


# Find the directory of this script.
dir = os.path.dirname(os.path.realpath(__file__))
rootDir = os.path.dirname(os.path.dirname(dir))
dest = os.path.join(os.path.join(rootDir, 'data'), 'noaa')
print 'Retrieving NOAA files to dir=%s' % dest
if not os.path.exists(dest):
  os.makedirs(dest)
os.chdir(dest)

RetrieveNOAA()

