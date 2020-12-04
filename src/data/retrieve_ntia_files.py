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

# This script retrieves the NTIA data files.
# The script writes the files into the data/ntia directory.

import os
try:
  from urllib.request import urlopen
except ImportError:
  from urllib2 import urlopen

# Retrieve all the NTIA data files into the current directory.
def RetrieveNTIA():
  print('Retrieving ground-based exclusion zone file...')
  ground = urlopen(
      'http://www.ntia.doc.gov/files/ntia/publications/ground_based_exclusion_zones.kml')
  if not ground.getcode() == 200:
    raise Exception('Could not find ground_based_exclusion_zones.kml file')

  with open('ground_based_exclusion_zones.kml', 'wb') as out:
    while True:
      c = ground.read(64*1024)
      if not c:
        break
      out.write(c)
  ground.close()
  print('Retrieved ground-based excluzion zone file...')

  print('Retrieving ship-borne exclusion zone file...')
  ship = urlopen(
      'http://www.ntia.doc.gov/files/ntia/publications/shipborne_radar_envelope_exclusion_zones.kml')
  if not ship.getcode() == 200:
    raise Exception('Could not find shipborne_radar_envelope_exclusion_zones.kml file')

  with open('shipborne_radar_envelope_exclusion_zones.kml', 'wb') as out:
    while True:
      c = ship.read(64*1024)
      if not c:
        break
      out.write(c)
  ship.close()
  print('Retrieved ship-borne excluzion zone file...')


# Find the directory of this script.
dir = os.path.dirname(os.path.realpath(__file__))
rootDir = os.path.dirname(os.path.dirname(dir))
dest = os.path.join(os.path.join(rootDir, 'data'), 'ntia')
print('Retrieving NTIA files to dir=%s' % dest)
if not os.path.exists(dest):
  os.makedirs(dest)
os.chdir(dest)

RetrieveNTIA()
