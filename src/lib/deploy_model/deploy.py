#    Copyright 2020 SAS Project Authors. All Rights Reserved.
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
"""Routines for reading NTIA deployment model.

The data are in data/research/deployment_models.

Typical usage:

  # Read the full nationwide deployment model.
  cbsds = ReadNationWideDeploymentModel()

  # Convert into grants
  grants = entities.ConvertToCbsdGrantInfo(cbsds, min_freq_mhz, max_freq_mhz)

"""
import csv
import collections
import os
import zipfile

DEFAULT_DEPLOY_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                  '..', '..', '..',
                                  'data', 'research', 'deployment_models')

ENV_TYPE = ('rural', 'suburban', 'urban', 'dense_urban')

# A generic Cbsd object.
# Note that it is a superset of entities.Cbsd.
class Cbsd(collections.namedtuple('Cbsd', ['latitude',
                                           'longitude',
                                           'height_agl',
                                           'is_indoor',
                                           'category',
                                           'eirp_dbm_mhz',
                                           'antenna_azimuth',
                                           'antenna_beamwidth',
                                           'antenna_gain',
                                           'environment',
                                           'census_pop'])):
  """
  A generic named tuple representing a CBSD, as a superset of `entities.Cbsd`.
    latitude, longitude: The CBSD location.
    height_agl: Height (Above Groud Level) in meters.
    is_indoor: True if Indoor, False if outdoor.
    category: 'A' or 'B'
    eirp_dbm_mhz: EIRP in dBm/MHz.
    antenna_azimuth: Antenna azimuth (clockwise from north).
    antenna_beamwidth: Antenna horizontal pattern beamwidth.
    antenna_gain: Antenna gain (dBi).
    census_pop: Population in census zone served by CBSD.
    environment: 'rural', 'suburban', 'urban' or 'dense_urban'
  """


def _ReadCsvCbsds(csv_reader, cbsd_type='B', force_omni=False):
  """Returns a list of |Cbsd| from a CSV reader."""
  cbsds = []
  next(csv_reader)
  for row in csv_reader:
    lat_cbsd = float(row[0])
    lon_cbsd = float(row[1])
    height_cbsd = float(row[2])
    environment = ENV_TYPE[max(min(int(row[3])-1, 3), 0)]
    census_pop = int(row[8]) # population of census tract where is CBSD.
    max_eirp = float(row[4])
    if cbsd_type == 'A' or force_omni:
      azis = [0]
      beamwidths = [360]
    else:
      azis = float(row[5]), float(row[6]), float(row[7])
      beamwidths = [65, 65, 65]
    for azi, beamwidth in zip(azis, beamwidths):
      cbsds.append(Cbsd(
          latitude=lat_cbsd,
          longitude=lon_cbsd,
          height_agl=height_cbsd,
          is_indoor=(cbsd_type == 'A'),
          category=cbsd_type,
          eirp_dbm_mhz=max_eirp-10,
          antenna_azimuth=azi,
          antenna_beamwidth=beamwidth,
          antenna_gain=0,
          environment=environment,
          census_pop=census_pop))

  return cbsds


# Read nationwide CBSD deployment model from CatA and CatB csv files
def ReadNationWideDeploymentModel(cat_a_file=None, cat_b_file=None,
                                  force_omni=False):
  """Reads CBSD nation wide deployment model.

  The default deployment model are data/research/deployment_model/NationWide_*.

  Args:
    cat_a_file: A CSV CatA file. If None, use the default file.
    cat_b_file: A CSV catB file. If None, use the default file.
    force_omni: If True, multi-sector sites are collapsed into single omni site.
  Returns:
    A list of |Cbsd|.
  """
  if cat_a_file is None:
    cat_a_file = os.path.join(DEFAULT_DEPLOY_DIR, 'NationWide_CatA.csv.zip')
  if cat_b_file is None:
    cat_b_file = os.path.join(DEFAULT_DEPLOY_DIR, 'NationWide_CatB.csv.zip')

  cbsds = []
  # Read category A CBSD file
  if cat_a_file.endswith('zip'):
    with zipfile.ZipFile(cat_a_file) as zip:
      file_name = [info.filename for info in zip.infolist()
                   if os.path.splitext(info.filename)[1] == '.csv'][0]
      with zip.open(file_name) as cata_fd:
        cata_reader = csv.reader(cata_fd)
        cbsds.extend(_ReadCsvCbsds(cata_reader, 'A', force_omni))
  else:
    with open(cat_a_file, 'r') as cata_fd:
      cata_reader = csv.reader(cata_fd)
      cbsds.extend(_ReadCsvCbsds(cata_reader, 'A', force_omni))

  # Read category B CBSD file
  if cat_b_file.endswith('zip'):
    with zipfile.ZipFile(cat_b_file) as zip:
      file_name = [info.filename for info in zip.infolist()
                   if os.path.splitext(info.filename)[1] == '.csv'][0]
      with zip.open(file_name) as catb_fd:
        catb_reader = csv.reader(catb_fd)
        cbsds.extend(_ReadCsvCbsds(catb_reader, 'B', force_omni))
  else:
    with open(cat_b_file, 'r') as catb_fd:
      catb_reader = csv.reader(catb_fd)
      cbsds.extend(_ReadCsvCbsds(catb_reader, 'B', force_omni))

  return cbsds


'''
with open(cat_b_fd, 'r') as a:
    a_reader = csv.reader(a)

  # Read Category B CBSD file
  with open(cat_b_file, 'r') as b:
    b_reader = csv.reader(b)
    next(b_reader)
    for row in b_reader:
      max_eirp = float(row[4])
      lat_cbsd = float(row[0])
      lon_cbsd = float(row[1])
      height_cbsd = float(row[2])
      grants.append(data.CbsdGrantInfo(
          latitude=lat_cbsd,
          longitude=lon_cbsd,
          height_agl=height_cbsd,
          indoor_deployment=False,
          antenna_azimuth=0,
          antenna_gain=0,
          antenna_beamwidth=360,
          cbsd_category='B',
          max_eirp=max_eirp,
          iap_eirp={max_eirp},
          low_frequency=3550000000,
          high_frequency=3560000000,
          is_managed_grant=True))



'''
