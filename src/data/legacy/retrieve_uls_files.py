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

# This script retrieves the ULS data files from the FCC ULS database.
# It retrieves the most recent (weekly) full dump of the database, as well
# as the most recent daily update files.
# The script writes the files into the data/uls directory. If the .zip
# files already exist, the script will only download files if they are
# newer than the local versions.

import os
import urllib2

# Retrieve all the ULS data files from the FCC database
def RetrieveULS():
  print 'Retrieving weekly ULS data file...'
  weekly = urllib2.urlopen('http://wireless.fcc.gov/uls/data/complete/l_micro.zip')
  if not weekly.getcode() == 200:
    raise Exception('Could not find l_micro.zip weekly ULS file')

  with open('l_micro.zip', 'wb') as out:
    while True:
      c = weekly.read(64*1024)
      if not c:
        break
      out.write(c)
  weekly.close()
  print 'Retrieved weekly ULS data file...'

  days = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']
  for d in days:
    filename = 'l_mw_' + d + '.zip'
    url = 'http://wireless.fcc.gov/uls/data/daily/' + filename
    print 'Retrieving daily ULS file: %s' % filename
    daily = urllib2.urlopen(url)
    if not daily.getcode() == 200:
      raise Exception('Could not find daily ULS file ' + url)

    with open(filename, 'wb') as out:
      while True:
        c = daily.read(64*1024)
        if not c:
          break
        out.write(c)
    daily.close()
    print 'Retrieved daily ULS file: %s' % filename

  print 'Retrieving schema file...'
  schema = urllib2.urlopen('http://wireless.fcc.gov/uls/ebf/pa_ddef49.txt')
  if not schema.getcode() == 200:
    raise Exception('Could not find ULS schema file')
  with open('pa_ddef49.txt', 'w') as out:
    while True:
      c = schema.read(64*1024)
      if not c:
        break
      out.write(c)
   schema.close()


# Find the directory of this script.
dir = os.path.dirname(os.path.realpath(__file__))
rootDir = os.path.dirname(os.path.dirname(dir))
dest = os.path.join(os.path.join(rootDir, 'data'), 'uls')
print 'Retrieving ULS files to dir=%s' % dest
if not os.path.exists(dest):
  os.makedirs(dest)
os.chdir(dest)

RetrieveULS()

