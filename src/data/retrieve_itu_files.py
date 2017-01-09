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

# This script retrieves ITU data files related to climate zone and refractivity.
# The script writes the files into the data/itu directory.

import os
import urllib2
import zipfile

# Retrieve all the NOAA data files into the current directory.
def RetrieveITU():
  print 'Retrieving ITU climate zone file...'
  border = urllib2.urlopen(
      'http://www.itu.int/dms_pubrec/itu-r/rec/p/R-REC-P.617-3-201309-I!!ZIP-E.zip')
  if not border.getcode() == 200:
    raise Exception('Could not find border definition file')

  with open('R-REC-P.617-3-201309-I!!ZIP-E.zip', 'wb') as out:
    while True:
      c = border.read(64*1024)
      if not c:
        break
      out.write(c)
  border.close()
  print 'Retrieved climate zone definition file...'

  print 'Retrieving ITU refractivity file...'
  border = urllib2.urlopen(
      'http://www.itu.int/dms_pubrec/itu-r/rec/p/R-REC-P.452-16-201507-I!!ZIP-E.zip')
  if not border.getcode() == 200:
    raise Exception('Could not find border definition file')

  with open('R-REC-P.452-16-201507-I!!ZIP-E.zip', 'wb') as out:
    while True:
      c = border.read(64*1024)
      if not c:
        break
      out.write(c)
  border.close()
  print 'Retrieved refractivity file...'

def ExtractITU():
  print 'Extracting data files from ITU zip files'

  zf = zipfile.ZipFile('R-REC-P.617-3-201309-I!!ZIP-E.zip', 'r')
  for datfile in zf.infolist():
    if datfile.filename.endswith('.TXT') or datfile.filename.endswith('.txt'):
      try:
        print '   extracting %s' % datfile.filename
        zf.extract(datfile, '.')
      except Exception, err:
        raise Exception('Cannot extract ' + datfile.filename)

  zf = zipfile.ZipFile('R-REC-P.452-16-201507-I!!ZIP-E.zip', 'r')
  for datfile in zf.infolist():
    if datfile.filename.endswith('.TXT') or datfile.filename.endswith('.txt'):
      try:
        print '   extracting %s' % datfile.filename
        zf.extract(datfile, '.')
      except Exception, err:
        raise Exception('Cannot extract ' + datfile.filename)
      if 'TXT' in datfile.filename:
        os.rename(datfile.filename, datfile.filename.lower())


# Find the directory of this script.
dir = os.path.dirname(os.path.realpath(__file__))
rootDir = os.path.dirname(os.path.dirname(dir))
dest = os.path.join(os.path.join(rootDir, 'data'), 'itu')
print 'Retrieving ITU files to dir=%s' % dest
if not os.path.exists(dest):
  os.makedirs(dest)
os.chdir(dest)

RetrieveITU()
ExtractITU()

