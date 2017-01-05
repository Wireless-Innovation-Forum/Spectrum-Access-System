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

# This script extracts geo info from the NED and NLCD files as retrieved.
# Results go alongside source files in the data/ned and data/nlcd directories.

import os
import zipfile

# Extract the wanted zipped data files from the given zipfile into the
# given temporary directory.
def UnzipNeededNLCDFiles(zip_filename, tmpDir):
  zf = zipfile.ZipFile(zip_filename, 'r')
  for datfile in zf.infolist():
    if datfile.filename.endswith('.rrd') or datfile.filename.endswith('.img') or datfile.filename.endswith('.ige'):
      try:
        print '   extracting %s' % datfile.filename
        zf.extract(datfile, tmpDir)
      except Exception, err:
        raise Exception('Cannot extract ' + datfile.filename + ' from ' + zip_filename)

def UnzipNeededNEDFiles(zip_filename, tmpDir):
  zf = zipfile.ZipFile(zip_filename, 'r')
  for datfile in zf.infolist():
    if datfile.filename.endswith('.flt') or datfile.filename.endswith('.hdr') or datfile.filename.endswith('.prj'):
      if '/' not in datfile.filename and 'meta' not in datfile.filename:
        try:
          print '   extracting %s' % datfile.filename
          zf.extract(datfile, tmpDir)
        except Exception, err:
          raise Exception('Cannot extract ' + datfile.filename + ' from ' + zip_filename)

def ExtractNLCDData(directory):
  for f in os.listdir(directory):
    if f.endswith('.zip'):
      UnzipNeededNLCDFiles(os.path.join(directory, f), directory)

def ExtractNEDData(directory):
  for f in os.listdir(directory):
    if f.endswith('.zip'):
      UnzipNeededNEDFiles(os.path.join(directory, f), directory)

# Find the directory of this script.
dir = os.path.dirname(os.path.realpath(__file__))
rootDir = os.path.dirname(os.path.dirname(dir))
nlcdDir = os.path.join(os.path.join(rootDir, 'data'), 'nlcd')
nedDir = os.path.join(os.path.join(rootDir, 'data'), 'ned')

print 'Extracting NLCD data files from zip files in dir=%s' % nlcdDir
ExtractNLCDData(nlcdDir)

print 'Extracting NED data files from zip files in dir=%s' % nedDir
ExtractNEDData(nedDir)

