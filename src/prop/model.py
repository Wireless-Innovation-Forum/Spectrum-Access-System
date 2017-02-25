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

# This module implements the combination of the eHata and ITM models
# according to the requirements developed in the Winnforum WG1 Propagation
# task group.

import math
import sys
import os
import random
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ehata import ehata
from itm import pytm
from geo import tropoClim
from geo import refractivity
from geo import ned_indexer
from geo import nlcd_indexer
from geo import land_use
from geo import vincenty

# f in MHz; d and h1/h2 all in meters
def FreeSpacePathLoss(f, d, h1, h2):
  r = math.sqrt(d*d + (h1-h2)*(h1-h2))
  return 20*math.log10(r) + 20*math.log10(f) - 27.56

class PropagationLossModel:
  def __init__(self, itu_dir, ned_dir, nlcd_dir):
    self.climIndx = tropoClim.ClimateIndexer(itu_dir)
    self.refractivityIndx = refractivity.RefractivityIndexer(itu_dir)
    self.nedIndx = ned_indexer.NedIndexer(ned_dir)
    self.nlcdIndx = nlcd_indexer.NlcdIndexer(nlcd_dir)

  # Calculate the ITM adjusted propagation loss given the
  # assumptions on the ITM model.
  def ITM_AdjustedPropagationLoss(self, lat1, lng1, h1, lat2, lng2, h2, f, reliability):
    dielectric_constant = 25.0  # good ground
    soil_conductivity = 0.02    # good ground
    polarization = 1
    confidence = 0.5

    # get surface refractivity and radio climate from path midpoint
    dist, bearing, rev_bearing = vincenty.dist_bear_vincenty(lat1, lng1, lat2, lng2)
    lat_c, lng_c, alpha2 = vincenty.to_dist_bear_vincenty(lat1, lng1, dist/2.0, bearing)
    print 'Midpoint = %f, %f' % (lat_c, lng_c)

    radio_climate = self.climIndx.TropoClim(lat_c, lng_c)
    refractivity = self.refractivityIndx.Refractivity(lat_c, lng_c)
    print 'Using climate %d' % radio_climate
    print 'Using refractivity %f' % refractivity
    print 'Using freq %f' % f

    profile = self.nedIndx.Profile(lat1, lng1, lat2, lng2)
    print profile[0], profile[1]
    #print profile
    print 'total distance is ', profile[0]*profile[1]

    loss = pytm.point_to_point(profile, h1, h2,
                               dielectric_constant,
                               soil_conductivity,
                               refractivity,
                               f,
                               radio_climate,
                               polarization,
                               confidence,
                               reliability)
    print 'ITM P2P is ', loss
    return loss


  # Adjusted propagation loss according to the adjustments in R2-SGN-04
  # distance d, heights h1, h2 all in meters
  # frequency f in MHz
  def ExtendedHata_AdjustedPropagationLoss(self, lat1, lng1, h1, lat2, lng2, h2, f, land_cat):
    d, bearing, rev_bearing = vincenty.dist_bear_vincenty(lat1, lng1, lat2, lng2)
    d = d*1000.0
    print 'EHata distance=', d

    if d <= 100.0:
      # return FSPL
      print 'FSPL'
      return FreeSpacePathLoss(f, d, h1, h2)
    if d > 100.0 and d <= 1000.0:
      print 'interp FSPL and ehata'
      # interpolate FSPL and ehata
      fspl_loss = FreeSpacePathLoss(f, 100.0, h1, h2)
      print '  fspl_loss=', fspl_loss
      ehata_loss, abm = ehata.ExtendedHata_MedianBasicPropLoss(f, 1.0, h1, h2, land_cat)
      print '  ehata_loss=', ehata_loss
      print '   ( abm=', abm
      return fspl_loss + (1.0 + math.log10(d/1000.0))*(ehata_loss - fspl_loss)
    if d > 1000.0 and d < 80000.0:
      # return eHata value without adjustment.
      print 'EHata only for d=%f' % d
      profile = self.nedIndx.Profile(lat1, lng1, lat2, lng2)
      return ehata.ExtendedHata_PropagationLoss(f, h1, h2, land_cat, profile)
    if d >= 80000.0:
      print 'EHata for distance %f > 80km' % d
      # Derive profile_80km
      lat_80, lng_80, heading = vincenty.to_dist_bear_vincenty(lat1, lng1, 80.0, bearing)
      print '80km point is %f %f' % (lat_80, lng_80)
      profile_80km = self.nedIndx.Profile(lat1, lng1, lat_80, lng_80)
      # Find J adjustment...
      ehata_loss = ehata.ExtendedHata_PropagationLoss(f, h1, h2, land_cat, profile_80km)
      itm_loss = self.ITM_AdjustedPropagationLoss(lat1, lng1, h1, lat_80, lng_80, h2, f, 0.5)
      J = ehata_loss - itm_loss
      print 'Got ehata=%f itm=%f J=%f' % (ehata_loss, itm_loss, J)
      if J < 0.0:
        J = 0.0

      return self.ITM_AdjustedPropagationLoss(lat1, lng1, h1, lat2, lng2, h2, f, 0.5) + J

  def LandClassification(self, lat, lng):
    code = self.nlcdIndx.NlcdCode(lat, lng)
    return self.nlcdIndx.NlcdLandCategory(code)

  # This is the oracle for propagation loss from point 1 to point 2 at frequency f (Mhz).
  def PropagationLoss(self, f, lat1, lng1, h1, lat2, lng2, h2, land_cat=''):
    if land_cat == '':
      code = self.nlcdIndx.NlcdCode(lat2, lng2)
      if code == 11:
        code = self.nlcdIndx.NlcdCode(lat1, lng1)
      land_cat = land_use.NlcdLandCategory(code)
    print 'Using land_cat =', land_cat
      
    if land_cat == 'RURAL' or h1 >= 200 or h2 >= 200:
      itm_loss = self.ITM_AdjustedPropagationLoss(lat1, lng1, h1, lat2, lng2, h2, f, 0.5)
      if land_cat == 'RURAL':
        itm_loss += random.uniform(0., 15.) # For vegetative loss per TR 15-517, A.2
      print 'Returning itm_loss for rural > 200: ', itm_loss
      return itm_loss
    else:
      itm_loss = self.ITM_AdjustedPropagationLoss(lat1, lng1, h1, lat2, lng2, h2, f, 0.5)
      ehata_loss = self.ExtendedHata_AdjustedPropagationLoss(lat1, lng1, h1, lat2, lng2, h2, f, land_cat)
      if ehata_loss > itm_loss:
        return ehata_loss
      return itm_loss

# Run directly, takes args of "lat1, lng1, h1, lat2, lng2, h2, f" and prints the
# (median) propagation loss in dB.
if __name__ == '__main__':
  dir = os.path.dirname(os.path.realpath(__file__))
  rootDir = os.path.dirname(os.path.dirname(dir))
  ituDir = os.path.join(os.path.join(rootDir, 'data'), 'itu')
  nedDir = os.path.join(os.path.join(rootDir, 'data'), 'ned')
  nlcdDir = os.path.join(os.path.join(rootDir, 'data'), 'nlcd')

  prop = PropagationLossModel(ituDir, nedDir, nlcdDir)
  loss = prop.PropagationLoss(float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]),
                              float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]),
                              float(sys.argv[7]))
  print 'Propagation Loss = ', loss, ' dB'


