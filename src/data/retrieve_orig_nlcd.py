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

""" This script retrieves the NLCD original geo data.

This is to be used in combination with `retile_nlcd.py` if ones want to recreate
the NLCD tiles from scratch.
"""
import os
import ssl
import urllib2


# Retrieves a resource via HTTP using urllib2. Writes it to the filename
# in the current working directory. If the filename already exists in the
# current working directory, the method does not retrieve the remote file
# unless the 'force' parameter is set to True.
def RetrieveHTTPFile(resource, force=False, write_file=''):
  if not write_file:
    write_file = resource.split('/')[-1]

  if os.path.exists(write_file) and not force:
    print 'Resource %s already retrieved' % resource
    return

  context = ssl._create_unverified_context()
  f = urllib2.urlopen(resource, context=context)
  if f.getcode() != 200:
    raise Exception('Could not find resource %s' % resource)
  with open(write_file, 'wb') as out:
    while True:
      c = f.read(64*1024)
      if not c:
        break
      out.write(c)
  f.close()


def RetrieveNlcdConus(directory):
  os.chdir(directory)
  print 'Retrieving NLCD for CONUS...'
  RetrieveHTTPFile('http://www.landfire.gov/bulk/downloadfile.php?TYPE=nlcd2011&FNAME=nlcd_2011_landcover_2011_edition_2014_10_10.zip',
                   write_file='nlcd_2011_landcover_2011_edition_2014_10_10.zip')
  print 'Retrieved NLCD for CONUS'


# Find the directory of this script.
cur_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.dirname(os.path.dirname(cur_dir))

dest_dir = os.path.join(os.path.join(root_dir, 'data'), 'nlcd')
print 'Retrieving NLCD files to dir=%s' % dest_dir
if not os.path.exists(dest_dir):
  os.makedirs(dest_dir)

RetrieveNlcdConus(dest_dir)
