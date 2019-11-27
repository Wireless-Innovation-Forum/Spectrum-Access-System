# This software was developed by employees of the National Institute
# of Standards and Technology (NIST), an agency of the Federal
# Government. Pursuant to title 17 United States Code Section 105, works
# of NIST employees are not subject to copyright protection in the United
# States and are considered to be in the public domain. Permission to freely
# use, copy, modify, and distribute this software and its documentation
# without fee is hereby granted, provided that this notice and disclaimer
# of warranty appears in all copies.
#
# THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND,
# EITHER EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED
# TO, ANY WARRANTY THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY
# IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE,
# AND FREEDOM FROM INFRINGEMENT, AND ANY WARRANTY THAT THE DOCUMENTATION
# WILL CONFORM TO THE SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE
# ERROR FREE. IN NO EVENT SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING,
# BUT NOT LIMITED TO, DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES,
# ARISING OUT OF, RESULTING FROM, OR IN ANY WAY CONNECTED WITH THIS
# SOFTWARE, WHETHER OR NOT BASED UPON WARRANTY, CONTRACT, TORT, OR
# OTHERWISE, WHETHER OR NOT INJURY WAS SUSTAINED BY PERSONS OR PROPERTY
# OR OTHERWISE, AND WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR AROSE OUT
# OF THE RESULTS OF, OR USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.
#
# Distributions of NIST software should also include copyright and licensing
# statements of any third-party software that are legally bundled with
# the code in compliance with the conditions of those licenses.

#======================================================
# Utilities for DPA protection testing
#======================================================

import json
import os
from copy import deepcopy
import numpy as np
import simplekml
from collections import namedtuple
from util import loadConfig, writeConfig
from reference_models.geo import vincenty
from reference_models.geo import drive
from reference_models.geo import utils as geo_utils
from reference_models.common import mpool
from reference_models.common import data
from reference_models.ppa import ppa
from shapely.ops import unary_union
from shapely.geometry import LineString
from shapely.prepared import prep
import contour_utils as cutils

# Define protection point as a tuple with named fields of
# 'latitude', 'longitude'
ProtectionPoint = namedtuple('ProtectionPoint', ['latitude', 'longitude'])
  

def csvToRegGrants(data_dir, dpa_name, cbsd_channel, firstN=np.inf, outdoorCatA=False):
  """Return lists of registration and grant requests from deployment csv files.

  Args:
    data_dir: path to template registration and grant request json files and to csv files
    dpa_name: name of DPA
    cbsd_channel: channel start and end frequencies (MHz) of grants (binary tuple)
    firstN: the number of CBSDs to read from the csv files
    outdoorCatA: If True, register category A CBSDs with height <= 6m as outdoor.
  """
  reg_request_list = []
  grant_request_list = []

  # Template registration and grant requests
  reg_request_filename = 'RegistrationRequest_Omni.json'
  reg_requestN = json.load(open(os.path.join(data_dir, reg_request_filename)))
  grant_request_filename = 'GrantRequest_N.json'
  grant_requestN = json.load(open(os.path.join(data_dir, grant_request_filename)))  
  
  # Populate Category A CBSD registration and grant requests
  csv_fname = os.path.join(data_dir, dpa_name + '_cata.csv')
  latA, lonA, htA, EIRPdBm10MHzA = np.loadtxt(csv_fname,delimiter=',',skiprows=1,usecols=(0,1,2,4),unpack=True)
  for i in range(min(firstN,latA.size)):
    reg_request = deepcopy(reg_requestN)
    reg_request['fccId'] = '321cba_' + str(i+1)
    reg_request['cbsdCategory'] = 'A'
    reg_request['installationParam']['latitude'] = latA[i]
    reg_request['installationParam']['longitude'] = lonA[i]
    reg_request['installationParam']['height'] = htA[i]
    if outdoorCatA and htA[i] <= 6:
      reg_request['installationParam']['indoorDeployment'] = False
    else:
      reg_request['installationParam']['indoorDeployment'] = True
    reg_request_list.append(reg_request)
    grant_request = deepcopy(grant_requestN)
    grant_request['cbsdId'] = 'sas1/cbsd' + str(i+1)
    grant_request['operationParam']['maxEirp'] = EIRPdBm10MHzA[i] - 10.0   # convert to dBm/MHz
    grant_request['operationParam']['operationFrequencyRange']['lowFrequency'] = cbsd_channel[0] * int(1e6)
    grant_request['operationParam']['operationFrequencyRange']['highFrequency'] = cbsd_channel[1] * int(1e6)
    grant_request_list.append(grant_request)

  # Populate Category B CBSD registration and grant requests
  csv_fname = os.path.join(data_dir, dpa_name + '_catb.csv')
  latB, lonB, htB, EIRPdBm10MHzB = np.loadtxt(csv_fname,delimiter=',',skiprows=1,usecols=(0,1,2,4),unpack=True)
  for i in range(min(firstN,latB.size)):
    reg_request = deepcopy(reg_requestN)
    reg_request['fccId'] = '321cba_' + str(i+1+latA.size)
    reg_request['cbsdCategory'] = 'B'
    reg_request['installationParam']['latitude'] = latB[i]
    reg_request['installationParam']['longitude'] = lonB[i]
    reg_request['installationParam']['height'] = htB[i]
    reg_request['installationParam']['indoorDeployment'] = False
    reg_request_list.append(reg_request)
    grant_request = deepcopy(grant_requestN)
    grant_request['cbsdId'] = 'sas1/cbsd' + str(i+1+latA.size)
    grant_request['operationParam']['maxEirp'] = EIRPdBm10MHzB[i] - 10.0   # convert to dBm/MHz
    grant_request['operationParam']['operationFrequencyRange']['lowFrequency'] = cbsd_channel[0] * int(1e6)
    grant_request['operationParam']['operationFrequencyRange']['highFrequency'] = cbsd_channel[1] * int(1e6)
    grant_request_list.append(grant_request)

  print 'Size of registration/grant list:', len(grant_request_list)

  return reg_request_list, grant_request_list


def csvToRegGrants2(data_dir, dpa_name, cbsd_channel, firstN=np.inf):
  """Return lists of registration and grant requests from deployment csv file.

  Args:
    data_dir: path to template registration and grant request json files and to csv files
    dpa_name: name of DPA
    cbsd_channel: channel start and end frequencies (MHz) of grants (binary tuple)
    firstN: the number of CBSDs to read from the csv file
  """
  reg_request_list = []
  grant_request_list = []

  # Template registration and grant requests
  reg_request_filename = 'RegistrationRequest_Omni.json'
  reg_requestN = json.load(open(os.path.join(data_dir, reg_request_filename)))
  grant_request_filename = 'GrantRequest_N.json'
  grant_requestN = json.load(open(os.path.join(data_dir, grant_request_filename)))  
  
  # Populate CBSD registration and grant requests
  csv_fname = os.path.join(data_dir, dpa_name + '.csv')
  lat, lon, ht, EIRPdBm10MHz = np.loadtxt(csv_fname,delimiter=',',skiprows=1,usecols=(0,1,2,3),unpack=True)
  indoor = np.loadtxt(csv_fname,dtype=str,delimiter=',',skiprows=1,usecols=(4),unpack=True)
  category = np.loadtxt(csv_fname,dtype=str,delimiter=',',skiprows=1,usecols=(5),unpack=True)
  for i in range(min(firstN,lat.size)):
    reg_request = deepcopy(reg_requestN)
    reg_request['fccId'] = '321cba_' + str(i+1)
    reg_request['cbsdCategory'] = category[i]
    reg_request['installationParam']['latitude'] = lat[i]
    reg_request['installationParam']['longitude'] = lon[i]
    reg_request['installationParam']['height'] = ht[i]
    reg_request['installationParam']['indoorDeployment'] = (indoor[i]=='TRUE')
    reg_request_list.append(reg_request)
    grant_request = deepcopy(grant_requestN)
    grant_request['cbsdId'] = 'sas1/cbsd' + str(i+1)
    grant_request['operationParam']['maxEirp'] = EIRPdBm10MHz[i] - 10.0   # convert to dBm/MHz
    grant_request['operationParam']['operationFrequencyRange']['lowFrequency'] = cbsd_channel[0] * int(1e6)
    grant_request['operationParam']['operationFrequencyRange']['highFrequency'] = cbsd_channel[1] * int(1e6)
    grant_request_list.append(grant_request)

  print 'Size of registration/grant list:', len(grant_request_list)

  return reg_request_list, grant_request_list


def csvToRegGrants3(data_dir, dpa_name, cbsd_channel, catB_beamwidth=360, firstN=np.inf, file_name_suffix=None):
  """Return lists of registration and grant requests from deployment csv file.

  Args:
    data_dir: path to template registration and grant request json files and to csv files
    dpa_name: name of DPA
    cbsd_channel: channel start and end frequencies (MHz) of grants (binary tuple)
    catB_beamwidth: 3 dB beamwidth of CBSD antennas (degrees); used for Cat B CBSDs (default is omni)
    firstN: the number of CBSDs to read from the csv file (optional)
    file_name_suffix: append to the DPA name when forming file name (optional)
  """
  reg_request_list = []
  grant_request_list = []

  # Template registration and grant requests
  reg_request_filename = 'RegistrationRequest_Omni.json'
  reg_requestN = json.load(open(os.path.join(data_dir, reg_request_filename)))
  grant_request_filename = 'GrantRequest_N.json'
  grant_requestN = json.load(open(os.path.join(data_dir, grant_request_filename)))  
  
  # Populate CBSD registration and grant requests
  if file_name_suffix:
    dpa_name = dpa_name + file_name_suffix
  csv_fname = os.path.join(data_dir, dpa_name + '.csv')
  lat, lon, ht, EIRPdBm10MHz = np.loadtxt(csv_fname,delimiter=',',skiprows=1,usecols=(0,1,2,4),unpack=True)
  az1, az2, az3 = np.loadtxt(csv_fname,delimiter=',',skiprows=1,usecols=(5,6,7),unpack=True)
  category = np.loadtxt(csv_fname,dtype=str,delimiter=',',skiprows=1,usecols=(9),unpack=True)
  for i in range(min(firstN,lat.size)):
    reg_request = deepcopy(reg_requestN)
    reg_request['fccId'] = '321cba_' + str(i+1)
    reg_request['cbsdCategory'] = category[i][3]
    reg_request['installationParam']['latitude'] = lat[i]
    reg_request['installationParam']['longitude'] = lon[i]
    reg_request['installationParam']['height'] = ht[i]
    reg_request['installationParam']['indoorDeployment'] = (category[i]=='catA')
    if (category[i] == 'catB') and (catB_beamwidth < 360):
      # Generate three registration and grant requests for each category B CBSD,
      # one for each azimuth
      reg_request['installationParam']['antennaAzimuth'] = az1[i]
      reg_request['installationParam']['antennaBeamwidth'] = catB_beamwidth
      reg_request_list.append(reg_request)
      reg_request2 = deepcopy(reg_request)
      reg_request2['installationParam']['antennaAzimuth'] = az2[i]
      reg_request_list.append(reg_request2)
      reg_request3 = deepcopy(reg_request)
      reg_request3['installationParam']['antennaAzimuth'] = az3[i]
      reg_request_list.append(reg_request3)
    else:
      reg_request_list.append(reg_request)
    grant_request = deepcopy(grant_requestN)
    grant_request['cbsdId'] = 'sas1/cbsd' + str(i+1)
    grant_request['operationParam']['maxEirp'] = EIRPdBm10MHz[i] - 10.0   # convert to dBm/MHz
    grant_request['operationParam']['operationFrequencyRange']['lowFrequency'] = cbsd_channel[0] * int(1e6)
    grant_request['operationParam']['operationFrequencyRange']['highFrequency'] = cbsd_channel[1] * int(1e6)
    grant_request_list.append(grant_request)
    if (category[i] == 'catB') and (catB_beamwidth < 360):
      grant_request_list.append(grant_request)
      grant_request_list.append(grant_request)

  print 'Size of registration/grant list:', len(grant_request_list)

  return reg_request_list, grant_request_list


def regsToKml(reg_list, fname):
  """Create kml file of CBSD locations and category in registration list.

  Args:
    reg_list: list of registration requests
    fname: name of kml file
  """
  kml = simplekml.Kml()
  for reg in reg_list:
    pnt = kml.newpoint(coords=[(reg['installationParam']['longitude'],
                                reg['installationParam']['latitude'])])
    icon_url = 'http://maps.google.com/mapfiles/kml/paddle/blu'
    if reg['cbsdCategory'] == 'B':
      icon_url = icon_url + '-circle.png'
    else:
      icon_url = icon_url + '-blank.png'
    pnt.style.iconstyle.icon.href = icon_url
    pnt.style.iconstyle.scale = 0.7
  kml.save(fname+'.kml')


def moveListToKml(reg_list, move_list, nbor_list, fname):
  """Create kml file of move list amd neighbor list.

  Args:
    reg_list: list of registration requests
    move_list: numpy array of booleans, True is on move list
    nbor_list: numpy array of booleans, True is on neighborhood list
    fname: name of kml file
  """
  kml = simplekml.Kml()
  for k, reg in enumerate(reg_list):
    icon_url = 'http://maps.google.com/mapfiles/kml/paddle/'
    if move_list[k]:
      icon_url = icon_url + 'red'
    elif nbor_list[k]:
      icon_url = icon_url + 'blu'
    else:
      icon_url = icon_url + 'wht'
    if reg['cbsdCategory'] == 'B':
      icon_url = icon_url + '-circle.png'
    else:
      icon_url = icon_url + '-blank.png'
    pnt = kml.newpoint(coords=[(reg['installationParam']['longitude'],
                                reg['installationParam']['latitude'])])
    pnt.style.iconstyle.icon.href = icon_url
    pnt.style.iconstyle.scale = 0.7
  kml.save(fname+'.kml')


def moveListToKml2(move_list, fname):
  """Create kml file of move list.

  Args:
    move_list: list of grants on the move list
    fname: name of kml file
  """
  kml = simplekml.Kml()
  for grant in move_list:
    icon_url = 'http://maps.google.com/mapfiles/kml/paddle/red'
    if grant.cbsd_category == 'B':
      icon_url = icon_url + '-circle.png'
    else:
      icon_url = icon_url + '-blank.png'
    pnt = kml.newpoint(coords=[(grant.longitude, grant.latitude)])
    pnt.style.iconstyle.icon.href = icon_url
    pnt.style.iconstyle.scale = 0.7
  kml.save(fname+'.kml')


def protectionPointsToKml(protection_points, fname, icon_href, scale):
  """Create kml file of protection points.

  Args:
    protection_points: list of protection points
    fname: name of kml file
    icon_href: url to custom icon (optional)
    scale: scale of icon (optional)
  """
  kml = simplekml.Kml()
  i = 1
  for p in protection_points:
    pnt = kml.newpoint(#name="Protection Point " + str(i),
                 coords=[(p.longitude, p.latitude)])
    if icon_href:
      pnt.style.iconstyle.icon.href = icon_href
    if scale:
      pnt.style.iconstyle.scale = scale
    i += 1
  kml.save(fname+'.kml')


def regGrantsToJson(reg_request_list, grant_request_list, fname):
  """Create json file of registration and grant requests.

  Args:
    reg_request_list: list of registration requests
    grant_request_list: list of grant requests
    fname: path and name of json file
  """
  config = {
    'registrationRequests': reg_request_list,
    'grantRequests': grant_request_list
  }
  writeConfig(fname, config)


def regGrantsFromJson(fname):
  """Read registration and grant requests from json file.

  Args:
    fname: path and name of json file
  """
  config = loadConfig(fname)
  reg_request_list = config['registrationRequests']
  grant_request_list = config['grantRequests']
  return reg_request_list, grant_request_list


def neighDistancesFromPointMoveLists(point_move_lists, protection_points):
  """Calculate neighborhood distances from point move lists.

  Args:
    point_move_lists: list of point move lists
    protection_points: list of protection points
  """
  cata_dist = []
  catb_inner = []
  catb_outer = []
  for k, p in enumerate(protection_points):
    cata_distances = [vincenty.GeodesicDistanceBearing(g.latitude, g.longitude,
                                                       p.latitude, p.longitude)[0]
                      for g in point_move_lists[k] if g.cbsd_category=='A']
    if cata_distances:
      cata_dist.append(max(cata_distances))
    catb_low_distances = [vincenty.GeodesicDistanceBearing(g.latitude, g.longitude,
                                                           p.latitude, p.longitude)[0]
                          for g in point_move_lists[k] if g.cbsd_category=='B' and g.height_agl<=18]
    if catb_low_distances:
      catb_inner.append(max(catb_low_distances))
    catb_high_distances = [vincenty.GeodesicDistanceBearing(g.latitude, g.longitude,
                                                            p.latitude, p.longitude)[0]
                           for g in point_move_lists[k] if g.cbsd_category=='B' and g.height_agl>18]
    if catb_high_distances:
      catb_outer.append(max(catb_high_distances))

  return max(cata_dist), max(catb_inner), max(catb_outer)


def maxDistanceFromProtectionPoint(point_move_lists, protection_points, height_cutoff_m):
  """Calculate the maximum distance between a CBSD with a grant on one or more
     point move lists to the nearest of those protection points.  Return this
     maximum distance for Cat A CBSDs, Cat B CBSDs at or below a cutoff height,
     and Cat B CBSDs above the cutoff height.

  Args:
    point_move_lists: list of point move lists
    protection_points: list of protection points
    height_cutoff_m: cutoff height for Cat B CBSDs (m)
  """
  move_list = set().union(*point_move_lists)

  cata_distances = []
  catb_inner_distances = []
  catb_outer_distances = []
  for grant in move_list:
    distances = []
    for k, p in enumerate(protection_points):
      if grant in point_move_lists[k]:
        distances.append(vincenty.GeodesicDistanceBearing(grant.latitude, grant.longitude,
                                                          p.latitude, p.longitude)[0])
    if grant.cbsd_category == 'A':
      cata_distances.append(min(distances))
    elif grant.height_agl <= height_cutoff_m:
      catb_inner_distances.append(min(distances))
    else:
      catb_outer_distances.append(min(distances))

  max_cata_distance = max(cata_distances) if cata_distances else None
  max_catb_inner_distance = max(catb_inner_distances) if catb_inner_distances else None
  max_catb_outer_distance = max(catb_outer_distances) if catb_outer_distances else None

  return max_cata_distance, max_catb_inner_distance, max_catb_outer_distance


def maxDistanceFromProtectionPointClutter(point_move_lists, protection_points):
  """Calculate the maximum distance between a CBSD with a grant on one or more
     point move lists to the nearest of those protection points.  Return this
     maximum distance for CBSDs below and above the ITU-R P.2108 Table 3
     representative clutter heights.

  Args:
    point_move_lists: list of point move lists
    protection_points: list of protection points
  """
  move_list = set().union(*point_move_lists)

  inclutter_distances = []
  aboveclutter_distances = []
  for grant in move_list:
    distances = []
    for k, p in enumerate(protection_points):
      if grant in point_move_lists[k]:
        distances.append(vincenty.GeodesicDistanceBearing(grant.latitude, grant.longitude,
                                                          p.latitude, p.longitude)[0])
    region_code = drive.nlcd_driver.GetLandCoverCodes(grant.latitude, grant.longitude)
    if (grant.height_agl <= 10 or
       (region_code in [23, 41, 42, 43] and grant.height_agl <= 15) or
       (region_code == 24 and grant.height_agl <= 20)):
      inclutter_distances.append(min(distances))
    else:
      aboveclutter_distances.append(min(distances))

  return max(inclutter_distances), max(aboveclutter_distances)


def ppaContour(reg_request_list):
  """Return the PPA contours of the given CBSDs as a list of shapely polygons.

  Args:
    reg_request_list: list of registration requests
  """
  
  mpool.Configure(50)
  pool = mpool.Pool()
  ppa_contours = pool.map(ppa._GetPolygon, reg_request_list)
  pool.close()
  pool.join()
  return ppa_contours


def disjointPpaFilter(reg_list, grant_list, ppa_contours):
  """Create a subset of CBSDs with disjoint (non-overlapping) default PPA contours.
     Return the registration/grant request lists and the PPA contours of
     this subset.

  Args:
    reg_list: list of CBSD registration requests
    grant_list: list of CBSD grant requests
    ppa_contours: list of shapely polygons of CBSD default PPA contours
  """

  if len(reg_list) != len(grant_list):
    print 'Warning: Registration and grant lists are of different lengths.'
  if len(reg_list) != len(ppa_contours):
    print 'Warning: Registration and contour lists are of different lengths.'
##  print 'Number of original CBSDs:', len(reg_list)

  # Construct lists of disjoint registration/grant requests
  reg_disjoint = []
  grant_disjoint = []
  contours_disjoint = []
  for i, contour in enumerate(ppa_contours):
    prepared_contour = prep(contour)
    if not filter(prepared_contour.intersects, contours_disjoint):
      reg_disjoint.append(reg_list[i])
      grant_disjoint.append(grant_list[i])
      contours_disjoint.append(contour)
##    if i in range(1000, len(reg_list), 1000):
##      print 'Completed', i
##
##  print 'Number of disjoint-PPA CBSDs:', len(reg_disjoint)

  return reg_disjoint, grant_disjoint, contours_disjoint


def limitCatBHeight(reg_list, maxHeight):
  """Given a list of registration requests, return a copy of the list
     with Category B CBSDs limited to a given height.

  Args:
    reg_list: list of CBSD registration requests
    maxHeight: the maximum height (m) of the returned list
  """

  new_reg_list = []
  for r in reg_list:
    new_reg_list.append(deepcopy(r))
    if r['cbsdCategory'] == 'B':
      height = r['installationParam']['height']
      new_reg_list[-1]['installationParam']['height'] = min(height, maxHeight)

  return new_reg_list


def calcMoveListMetrics(ml, reg_list, grant_list, contours, area_union):
  """Calculate and print the move list size and coverage area.  Return the
     contours of the CBSDs with grants on the move list.

  Args:
    ml: set of grants on the move list
    reg_list:  list of registration requests
    grant_list:  list of grant requests
    contours: numpy array of shapely polygons representing the default PPA
              contours of the CBSDs in reg_list
    area_union: area (sq km) of the union of the contours
  """
  num_catA = len([r for r in reg_list if r['cbsdCategory'] == 'A'])
  num_catB = len([r for r in reg_list if r['cbsdCategory'] == 'B'])
  num_catA_ml = len([g for g in ml if g.cbsd_category == 'A'])
  num_catB_ml = len([g for g in ml if g.cbsd_category == 'B'])
  grants = data.getGrantsFromRequests(reg_list, grant_list)
  ind = [i for i, g in enumerate(grants) if g in ml]
  area_union_ml = geo_utils.GeometryArea(unary_union(contours[ind]))
  keep_list = set(grants).difference(ml)
  ind = [i for i, g in enumerate(grants) if g in keep_list]
  area_union_kl = geo_utils.GeometryArea(unary_union(contours[ind]))
  print '  Cat A Move List: {0} ({1:.0f}%)'.format(num_catA_ml,
                                                   100.*float(num_catA_ml)/float(num_catA))
  print '  Cat B Move List: {0} ({1:.0f}%)'.format(num_catB_ml,
                                                   100.*float(num_catB_ml)/float(num_catB))
  print '  Total Move List: {0} ({1:.0f}%)'.format(len(ml),
                                                   100.*float(len(ml))/float(len(reg_list)))
  print '  Move List Coverage Area: {0:.0f} sq km ({1:.0f}%)'.format(area_union_ml,
                                                                     100.*area_union_ml/area_union)
  print '  Keep List Coverage Area: {0:.0f} sq km ({1:.0f}%)'.format(area_union_kl,
                                                                     100.*area_union_kl/area_union)

  return contours[ind]


def coverageAnalysis(dpa_name, recalc_ml=False, geo_files=False):
  """Calculate the coverage area of CBSDs and the area on the move
     list for a given DPA deployment.

  Args:
    dpa_name: name of the DPA (string)
    recalc_ml: if True, save registration/grant request configuration files and
               prompt user to calculate move lists
    geo_files: if True, save contour geojson files and move list kml files
  """

  # Calculate metrics for original deployment
  reg_list, grant_list = regGrantsFromJson('test_data/'+dpa_name+'_reg_grant.json')
  num_catA = len([r for r in reg_list if r['cbsdCategory'] == 'A'])
  num_catB = len([r for r in reg_list if r['cbsdCategory'] == 'B'])
  catA_contours = np.load('data/'+dpa_name+'_catA_ppa.npy', allow_pickle=True)
  catB_contours = np.load('data/'+dpa_name+'_catB_ppa.npy', allow_pickle=True)
  contours = np.concatenate((catA_contours, catB_contours))
  area_union = geo_utils.GeometryArea(unary_union(contours))
  print '\nOriginal, no height restriction'
  print '  Cat A:', num_catA
  print '  Cat B:', num_catB
  print '  Total:', len(reg_list)
  print '  Coverage Area: {0:.0f} sq km'.format(area_union)

  if recalc_ml:
    raw_input('\nPress any key when move list with original deployment is available...')
  ml, _, _, _ = np.load('data/'+dpa_name+'_ml_hyb_m0p0.npy', allow_pickle=True)
  ml_contours = calcMoveListMetrics(ml, reg_list, grant_list, contours, area_union)

  if geo_files:
    cutils.writeGeoJson(ml_contours, 'data/'+dpa_name+'_ml_hyb_contours.geojson')
    moveListToKml2(ml, 'data/'+dpa_name+'_ml_hyb')

  # Calculate metrics for original deployment with height restriction
  reg_list_hMaxB18m = limitCatBHeight(reg_list, 18.)
  num_catA = len([r for r in reg_list_hMaxB18m if r['cbsdCategory'] == 'A'])
  num_catB = len([r for r in reg_list_hMaxB18m if r['cbsdCategory'] == 'B'])
  catB18_contours = np.load('data/'+dpa_name+'_hMax18m_catB_ppa.npy', allow_pickle=True)
  contours = np.concatenate((catA_contours, catB18_contours))
  area_union = geo_utils.GeometryArea(unary_union(contours))
  print '\nOriginal, height restriction'
  print '  Coverage Area: {0:.0f} sq km'.format(area_union)

  if recalc_ml:
    regGrantsToJson(reg_list_hMaxB18m, grant_list, 'test_data/'+dpa_name+'_hMaxB18m_reg_grant.json')
    raw_input('\nPress any key when move list with height cutoff is available...')
  ml, _, _, _ = np.load('data/'+dpa_name+'_hMaxB18m_ml_hyb_m0p0.npy', allow_pickle=True)
  ml_contours = calcMoveListMetrics(ml, reg_list_hMaxB18m, grant_list, contours, area_union)
  
  if geo_files:
    cutils.writeGeoJson(catB18_contours, 'data/'+dpa_name+'_hMax18m_catB_ppa.geojson')
    cutils.writeGeoJson(ml_contours, 'data/'+dpa_name+'_hMaxB18m_ml_hyb_contours.geojson')
    moveListToKml2(ml, 'data/'+dpa_name+'_hMaxB18m_ml_hyb')

  # Calculate metrics for non-overlapping deployment
  catBstart = [r['cbsdCategory'] for r in reg_list].index('B')
  regA_list = reg_list[:catBstart]
  grantA_list = grant_list[:catBstart]
  regA_dj, grantA_dj, contourA_dj = disjointPpaFilter(regA_list, grantA_list, catA_contours)
  regB_list = reg_list[catBstart:]
  grantB_list = grant_list[catBstart:]
  regB_dj, grantB_dj, contourB_dj = disjointPpaFilter(regB_list, grantB_list, catB_contours)
  contours = np.array(contourA_dj + contourB_dj)
  area_union = geo_utils.GeometryArea(unary_union(contours))
  print '\nNon-overlapping, no height restriction'
  print '  Cat A:', len(regA_dj)
  print '  Cat B:', len(regB_dj)
  print '  Total:', len(regA_dj) + len(regB_dj)
  print '  Coverage Area: {0:.0f} sq km'.format(area_union)

  if recalc_ml:
    regGrantsToJson(regA_dj+regB_dj, grantA_dj+grantB_dj, 'test_data/'+dpa_name+'_disjointPpa_reg_grant.json')
    raw_input('\nPress any key when move list with disjoint contours is available...')  
  ml, _, _, _ = np.load('data/'+dpa_name+'_disjointPpa_ml_hyb_m0p0.npy', allow_pickle=True)
  ml_contours = calcMoveListMetrics(ml, regA_dj+regB_dj, grantA_dj+grantB_dj, contours, area_union)
  
  if geo_files:
    np.save('data/'+dpa_name+'_disjointPpa.npy', contours)
    cutils.writeGeoJson(contours, 'data/'+dpa_name+'_disjointPpa.geojson')
    cutils.writeGeoJson(ml_contours, 'data/'+dpa_name+'_disjointPpa_ml_hyb_contours.geojson')
    moveListToKml2(ml, 'data/'+dpa_name+'_disjointPpa_ml_hyb')

  # Calculate metrics for non-overlapping deployment with height restriction
  regB_list = reg_list_hMaxB18m[catBstart:]
  regB_dj_hMax18m, grantB_dj_hMax18m, contourB_dj_hMax18m \
    = disjointPpaFilter(regB_list, grantB_list, catB18_contours)
  contours = np.array(contourA_dj + contourB_dj_hMax18m)
  area_union = geo_utils.GeometryArea(unary_union(contours))
  print '\nNon-overlapping, height restriction'
  print '  Cat A:', len(regA_dj)
  print '  Cat B:', len(regB_dj_hMax18m)
  print '  Total:', len(regA_dj) + len(regB_dj_hMax18m)
  print '  Coverage Area: {0:.0f} sq km'.format(area_union)
  
  if recalc_ml:
    regGrantsToJson(regA_dj+regB_dj_hMax18m, grantA_dj+grantB_dj_hMax18m, 'test_data/'+dpa_name+'_hMaxB18m_disjointPpa_reg_grant.json')
    raw_input('\nPress any key when move list with disjoint contours and height cutoff is available...')
  ml, _, _, _ = np.load('data/'+dpa_name+'_hMaxB18m_disjointPpa_ml_hyb_m0p0.npy', allow_pickle=True)
  ml_contours = calcMoveListMetrics(ml, regA_dj+regB_dj_hMax18m, grantA_dj+grantB_dj_hMax18m, contours, area_union)
  
  if geo_files:
    np.save('data/'+dpa_name+'_hMaxB18m_disjointPpa.npy', contours)
    cutils.writeGeoJson(contours, 'data/'+dpa_name+'_hMaxB18m_disjointPpa.geojson')
    cutils.writeGeoJson(ml_contours, 'data/'+dpa_name+'_hMaxB18m_disjointPpa_ml_hyb_contours.geojson')
    moveListToKml2(ml, 'data/'+dpa_name+'_hMaxB18m_disjointPpa_ml_hyb')
