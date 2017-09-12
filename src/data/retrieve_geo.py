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

"""Retrieve NED and NLCD tiles to be used with reference propagation models.

The tiles are stored in Google Cloud Storage within the `winnforum-sas` bucket.
Tiles are retrieved and unzipped into the top level data/ned/ and data/nlcd/
folders. Only missing or newer tiles are retrieved.
"""

import json
import os
import requests
import zipfile

WF_GEODATA_URI = 'https://www.googleapis.com/storage/v1/b/winnforum-sas/o'


# Extract the wanted zipped data files from the given zipfile into the
# given temporary directory.
def UnzipNeededFiles(zip_filename, dest_dir):
  """Unzip all needed geo files from zip.
  """
  zf = zipfile.ZipFile(zip_filename, 'r')
  for datfile i n zf.infolist():
    if (datfile.filename.endswith('.int') or datfile.filename.endswith('.flt') or
        datfile.filename.endswith('.hdr') or datfile.filename.endswith('.prj')):
      try:
        zf.extract(datfile, dest_dir)
      except:
        raise Exception('Cannot extract ' + datfile.filename +
                        ' from ' + zip_filename)


def RetrieveFileFromUrl(url, out_file):
  """Retrieve a file from a given URL and store it in 'out_file'.
  """
  with open(out_file, 'wb') as fd:
    r = requests.get(url, stream=True)
    for chunk in r.iter_content(chunk_size=128):
      fd.write(chunk)


# Retrieve tile from bucket using GCS JSON API.
def RetrieveTiles(prefix, dest, extension):
  """Retrieve all tiles for given 'prefix' and store in 'dest' folder.
  """
  decoder = json.JSONDecoder()
  session = requests.Session()
  params = {}
  params['prefix'] = prefix
  stop = False
  while not stop:
    data = decoder.decode(
        session.get(WF_GEODATA_URI, params=params).content)
    if data.has_key('nextPageToken'):
      params['pageToken'] = data['nextPageToken']
    else:
      stop = True
    blobs = data['items']
    for blob in blobs:
      blob_name = blob['name']
      zip_tile = os.path.join(dest, os.path.basename(blob_name))
      # Check if tile already exists and check md5 hash
      if (os.path.exists(zip_tile[:-3] + extension) and
          os.path.exists(zip_tile[:-3] + 'md5')):
        with open(zip_tile[:-3] + 'md5', 'r') as fd:
          md5 = fd.readline()
          if md5 == blob['md5Hash']:
            print '  ..Skipping tile: %s (up to date)' % blob_name
            continue

      print '  ..Getting tile: %s' % blob_name
      RetrieveFileFromUrl(blob['mediaLink'], zip_tile)
      UnzipNeededFiles(zip_tile, dest)
      os.remove(zip_tile)
      # Create the MD5 hash file for future update detection
      with open(zip_tile[:-3] + 'md5', 'w') as fd:
        fd.write(blob['md5Hash'])

# Find the output data directories
cur_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.dirname(os.path.dirname(cur_dir))

# Retrieve all tiles
nlcd_dest = os.path.join(os.path.join(data_dir, 'data'), 'nlcd2')
print '# Retrieving NLCD tiles to %s' % nlcd_dest
if not os.path.exists(nlcd_dest):
  os.makedirs(nlcd_dest)
RetrieveTiles('nlcd', nlcd_dest, 'int')

ned_dest = os.path.join(os.path.join(data_dir, 'data'), 'ned2')
print '# Retrieving NED tiles to %s' % ned_dest
if not os.path.exists(ned_dest):
  os.makedirs(ned_dest)
RetrieveTiles('ned', ned_dest, 'flt')
