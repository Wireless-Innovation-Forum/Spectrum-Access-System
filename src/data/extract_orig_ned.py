#    Copyright 2017 SAS Project Authors. All Rights Reserved.
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

"""This script extracts geo info from the NED original files as retrieved.
Results go alongside source files in the data/ned_orig directory.
"""

import os
import zipfile

# Extract the wanted zipped data files from the given zipfile into the
# given temporary directory.
def UnzipNeededFiles(zip_filename, tmp_dir):
  zf = zipfile.ZipFile(zip_filename, 'r')
  for datfile in zf.infolist():
    if (datfile.filename.endswith('.flt') or
        datfile.filename.endswith('.hdr') or
        datfile.filename.endswith('.prj')):
      try:
        print('   extracting %s' % datfile.filename)
        zf.extract(datfile, tmp_dir)
      except:
        raise Exception('Cannot extract ' + datfile.filename + ' from ' + zip_filename)


def ExtractData(directory):
  for f in os.listdir(directory):
    if f.endswith('.zip'):
      # Check if already extracted
      UnzipNeededFiles(os.path.join(directory, f), directory)

# Find the directory of this script.
cur_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.dirname(os.path.dirname(cur_dir))
ned_dir = os.path.join(root_dir, 'data', 'geo', 'orig_ned')


print('Extracting NED data files from zip files in dir=%s' % ned_dir)
ExtractData(ned_dir)
