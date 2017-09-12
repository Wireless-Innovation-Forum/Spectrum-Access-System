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

# This module implements the extended Hata model described by NTIA in
# Technical Report 15-517: 3.5 GHz Exclusion Zone Analyses and Methodology
# in Appendix A.3 (p.28-35).

# The model describes several terrain types: dense urban (large city), urban (small city),
# suburban, and rural. These correspond to National Land Cover Database terrain
# classifications.

# This code is a Python adaptation of implementation code developed by NIST and released
# in September 2016 at https://github.com/usnistgov/eHATA. Notice in that release:

#   This software was developed by employees of the National Institute of Standards and
#   Technology (NIST), an agency of the Federal Government. Pursuant to title 17 United
#   States Code Section 105, works of NIST employees are not subject to copyright
#   protection in the United States and are considered to be in the public domain.
#   Permission to freely use, copy, modify, and distribute this software and its documentation
#   without fee is hereby granted, provided that this notice and disclaimer of warranty
#   appears in all copies.

#   THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND, EITHER EXPRESSED,
#   IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED TO, ANY WARRANTY THAT THE SOFTWARE
#   WILL CONFORM TO SPECIFICATIONS, ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS
#   FOR A PARTICULAR PURPOSE, AND FREEDOM FROM INFRINGEMENT, AND ANY WARRANTY THAT THE
#   DOCUMENTATION WILL CONFORM TO THE SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL
#   BE ERROR FREE. IN NO EVENT SHALL NASA BE LIABLE FOR ANY DAMAGES, INCLUDING, BUT NOT
#   LIMITED TO, DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES, ARISING OUT OF,
#   RESULTING FROM, OR IN ANY WAY CONNECTED WITH THIS SOFTWARE, WHETHER OR NOT BASED
#   UPON WARRANTY, CONTRACT, TORT, OR OTHERWISE, WHETHER OR NOT INJURY WAS SUSTAINED BY
#   PERSONS OR PROPERTY OR OTHERWISE, AND WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR
#   AROSE OUT OF THE RESULTS OF, OR USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.

#   Distributions of NIST software should also include copyright and licensing statements
#   of any third-party software that are legally bundled with the code in compliance with
#   the conditions of those licenses.


import math
import numpy
import scipy.stats

# Return the Extended-Hata Propagation Loss in dB given a
#  f - frequency (in MHz)
#  hb - base station (tx) height in meters
#  hm - mobile station (rx) height in meters
#  region - 'URBAN', 'SUBURBAN', 'DENSE_URBAN', 'RURAL' code for environment
#  profile - ITM-style encoded profile data. First element is an integer
#            corresponding to the number of points in the profile minus one.
#            The second is the separation between points in meters.
#            3->end is the elevation profile data in meters AMSL.
def ExtendedHata_PropagationLoss(f, hb, hm, region, profile):
  # print f, hb, hm, region
  region = region.upper().strip()
  if region != 'URBAN' and region != 'SUBURBAN' and region != 'DENSEURBAN':
    print 'Invalid region'
    # throw an exception
    return NaN

  # Also need to do bounds checking on hm/hb/f and validation on profile...
  hb_eff, hm_eff = EffectiveHeights(hb, hm, profile)

  numPoints = profile[0]+1
  resolution = float(profile[1]/1000.0);
  distance = float(profile[0] * resolution)

  basic_loss_db, above_median_loss_db = ExtendedHata_MedianBasicPropLoss(f, distance, hb_eff, hm_eff, region)
  #print 'Basic loss = %f (%f)' % (basic_loss_db, above_median_loss_db)

  Kir = IsolatedRidgeCorrection(profile)
  #print 'Kir = %f' % Kir

  # TODO: get better sea indicator than elevation==0
  Kmp = MixedPathCorrection(profile, [float(i) == 0.0 for i in profile])
  #print 'Kmp = %f' % Kmp

  # If isolated ridge applies, then don't do rolling hill and general slope corrections
  if Kir == 0.0:
    Krh, Kh, Khf = RollingHillyCorrection(profile)
    #print 'Krh=%f' % Krh

    Kgs = GeneralSlopeCorrection(profile)
    #print 'Kgs=%f' % Kgs

    return basic_loss_db + Krh - Kgs - Kmp

  else:
    return basic_loss_db + Kir - Kmp

# Return the Extended-Hata propagation loss given a particular set of
# reliability values.
def ExtendedHata_PropagationLossStat(f, hb, hm, region, profile, reliability):
  loss_db = ExtendedHata_PropagationLoss(f, hb, hm, region, profile)

  # Assume stdev for RURAL or SUBURBAN is the stdev_urban + 2. See p.35
  region = region.upper().strip()
  if region == 'URBAN' or region == 'DENSEURBAN':
    stdev = EHataStdDevUrban(f)
  else:
    stdev = EHataStdDevSuburban(f)

  n = scipy.stats.norm(loc=0.0, scale=stdev)
  rel = n.ppf(reliability)
  for i in range(0, len(rel)):
    rel[i] = rel[i] + loss_db

  return rel


# Compute median basic transmission loss for a given region
def ExtendedHata_MedianBasicPropLoss(f, d, hb, hm, region):

  # TODO: add bounds checking for frequency
  #if f < 1500:
  #  f = 1500
  #if f > 3000:
  #  f = 3000

  # TODO: add bounds checking for distance
  #if (d<1)
  #  d = 1      
  #if (d>100)
  #  d = 100  

  # TODO: add bounds checking for hb
  #if hb < 30:
  #  hb = 30
  #if hb > 200
  #  hb = 200

  # TODO: add bounds checking for hm
  #if hm < 1:
  #  hm = 1
  #if hm > 10:
  #  hm = 10

  # Obtain the base station effective height dependence of the lower
  # distance range power law component of the median attenuation relative to
  # free space (Page 30 of [1])
  nl = 0.1*(24.9 - 6.55*math.log10(hb))

  # Obtain the base station effective height dependence of the higher
  # distance range power law component of the median attenuation relative to
  # free space (Page 30 of [1])
  nh = 2*(-1.75 + 3.27*math.log10(hb) - 0.67*(math.log10(hb))**2)

  # Compute basic median attenuation relative to free space at the reference
  # base and mobile stations effective heights
  # @ reference distance of 1 km (Eqn. (A-6) of [1] with d = 1)
  Abmf1 = 30.52 - 16.81*math.log10(f) + 4.45*(math.log10(f))**2
  abmf1 = 10**(Abmf1/10.)  # Note A(f,d) = 10*log10(a(f,d))

  # @ reference distance of 100 km (alpha_100=120.78, beta_100=-52.71, 
  # gamma_100=10.92 on Page 30 of [1])
  Abmf100 = 120.78 - 52.71*math.log10(f) + 10.92*(math.log10(f))**2
  abmf100 = 10**(Abmf100/10.)

  # Compute "break-point" distance (in km) (Eqn. (A-9b) of [1])
  dbp = (10**(2.*nh) * abmf1 / abmf100)**(1./(nh-nl)) 

  # Compute direct LOS distance (in meters) between base station and mobile 
  # station (Eqn. (A-12) of [1])
  R = ((d*1e3)**2 + (hb-hm)**2)**0.5

  # Compute free space loss 
  Lfs = 20.*math.log10(f) + 20.*math.log10(R) - 27.56

  # Compute power law exponent (Eqn (A-13) of [1]) (Note: the conditions have 
  # been relaxed to account for distances < 1 km or > 100 km)
  if (d <= dbp):
      n = nl
  elif (d > dbp):
      n = nh

  # Compute basic median attenuation relative to free space at break point
  # distance (Eqn. (A-11) of [1])
  Abmfdbp = 30.52 - 16.81*math.log10(f) + 4.45*(math.log10(f))**2 + (24.9 - 6.55*math.log10(hb)) * math.log10(dbp)   
             
  # Compute correction factor for hm (Eqn. (A-2a) of [1])
  ahm = 3.2*(math.log10(11.75*hm))**2 - 4.97 
  a3 = 3.2*(math.log10(11.75*3.))**2 - 4.97

  # Compute median basic transmission loss (Eqn. (A-10) of [1])
  MedianLossEH = Abmfdbp + 10.*n*math.log10(d/dbp) +13.82*math.log10(200/hb) + a3 - ahm + Lfs

  # Get basic median attenuation relative to free space for validation
  # purpose
  MedianAbmEH = MedianLossEH - Lfs

  # Adjust the loss for suburban region by subtracting suburban correction 
  # factor
  if region.upper().strip() == 'SUBURBAN':   # adjust for suburban area 
    MedianLossEH = MedianLossEH - (54.19 - 33.30*math.log10(f) + 6.25*(math.log10(f))**2)
                                    # (Eqn. (A-14) of [1])
    MedianAbmEH = MedianLossEH - Lfs

  return MedianLossEH, MedianAbmEH



# Interpolate the rolling hill values of the CDF of terrain in order to
# determine the percentile values.
# (Also value for other sorted-value interpolation when needed.)
def hill_interp(profile, norm_index):
  # The CDF interval the norm_index is in is the i'th one, which comes after the [i-1]
  # element of the sorted profile.
  index = norm_index * (len(profile) - 1)
  lo = int(math.floor(index))
  hi = int(math.ceil(index))
  if hi > len(profile)-1:
    hi = lo
  #print norm_index, index, lo, hi, len(profile), profile[lo], profile[hi]
  return profile[lo] + (profile[hi] - profile[lo]) * (index-lo)


#PIECELIN  Piecewise linear interpolation.
#  v = piecelin(x, y, u) finds the piecewise linear L(x)
#  with L(x(j)) = y(j) and returns L(u(k)).
def piecelin(x, y, u):
    for i in range(len(x)-1):
        if u > x[i] and u < x[i+1]:
            return y[i] + (u-x[i]) * (y[i+1] - y[i])/(x[i+1] - x[i]) 
        elif u == x[i]:
            return y[i]
        elif u == x[i+1]:
            return y[i+1]


# Note: there are six site-specific corrections to this base loss estimate, corresponding
# to accounting for:
#  * effective height of terminals,
#  * rolling hilly terrain at the receiver
#  * fine rolling hilly terrain correction
#  * general slope of terrain at the receiver
#  * isolated ridge (applied if the path is single-horizon)
#  * mixed land-sea path corrections
# Note: the report does not give sufficient information to implement the last three
# corrections. They reference figures in Okumura 1968 (ref A-1) but do not provide
# implementation values derived from those figures.

# The elev parameter is the same as that given to the ITM algorithm: an array of elevations
# where the first element is the number of elevations minus one and the second is
# the distance in meters between elevation points. Elevations given in meters.
# See discussion at the top of p.33
# Returns the total correction, the median, and the fine corrections.
def RollingHillyCorrection(elev):
  numPoints = elev[0]+1
  distance = elev[0] * elev[1]
  resolution = float(elev[1]/1000.0);
  profile = elev[2:numPoints+2]

  # neighborhood of the terminal (10km)
  radiusKm = 10

  prof = []
  reversed_prof = profile[::-1]
  for i in range(0, int(math.ceil(radiusKm/resolution))):
    if i*resolution <= radiusKm and i < len(reversed_prof):
      prof.append(reversed_prof[i])

  prof = sorted(prof)
  #print prof
  lowest = hill_interp(prof, .1)
  highest = hill_interp(prof, .9)
  median = hill_interp(prof, .5)
  #print lowest, median, highest
  irregularity = highest - lowest

  if distance < 10000.0:
    irregularity = irregularity*(1.0-0.8*math.exp(-.2))/(1.0-0.8*(math.exp(-.02*distance)))

  if irregularity < 10.0:
    return 0.0, 0.0, 0.0
  if irregularity > 500.0:  # cap undulation at 500m
    irregularity = 500.0


  # Median undulation correction. See eq. A-16
  Kh = 1.507213 - 8.458676*math.log10(irregularity) + 6.102538*math.pow(math.log10(irregularity), 2)


  # Fine undulation correction. See eq. A-17
  Khf = -11.72879 + 15.544272*math.log10(irregularity) - 1.8154766*math.pow(math.log10(irregularity), 2)

  elevation_rx = elev[-1]
  if elevation_rx <= lowest:
    Khf = -Khf
  elif lowest < elevation_rx and elevation_rx < median:
    Khf = (1 - (elevation_rx - lowest)/(median-lowest)) * -Khf
  elif median <= elevation_rx and elevation_rx < highest:
    Khf = (elevation_rx - median)/(highest - median) * Khf
  #otherwise, elevation_rx >= highest, and Khf does not change

  return Kh - Khf, Kh, Khf


# Compute the standard deviation (expected variation in actual measurements) for
# the urban case. We expect the suburban variation to be about this value plus 2.
# See p.34-35
def EHataStdDevUrban(f):
  stdev_u = 4.0976291 - 1.2255656*math.log10(f) + 0.68350345*math.pow(math.log10(f), 2)

  return stdev_u

def EHataStdDevSuburban(f):
  return EHataStdDevUrban(f) + 2.0


# Return the effective heights of the source and destination. The profile
# is a ITM-compatible array containing the number of points in the first
# element, the distance between them in the second, followed by an
# array of profile[0]-1 elevation points.
# Returns the source effective height and dest effective height in meters.
def EffectiveHeights(source_height_m, dest_height_m, profile):
  dMinKm = 3
  dMaxKm = 15

  numPoints = profile[0]+1
  resolution = float(profile[1]/1000.0);
  elevations = profile[2:]
  distance = float(profile[0] * resolution)

  if distance < dMinKm:
    return source_height_m, dest_height_m

  elif distance >= dMinKm and distance <= dMaxKm:
    # Find the mean of the terrain height
    meanElev = (math.fsum(elevations) / len(elevations)) * (distance / dMaxKm)

    source_effective_height_m = source_height_m + elevations[0] - meanElev
    dest_effective_height_m = dest_height_m + elevations[-1] - meanElev

    if source_effective_height_m < 0:
      source_effective_height_m = meanElev

    if dest_effective_height_m < 0:
      dest_effective_height_m = meanElev

    return source_effective_height_m, dest_effective_height_m

  else:
   eff_heights = []
   for i in range(0, int(math.ceil(dMaxKm/resolution))):
     if i*resolution >= dMinKm and i*resolution <= dMaxKm:
       eff_heights.append(elevations[i])

   meanElevTx = math.fsum(eff_heights) / len(eff_heights)
   source_effective_height_m = source_height_m + elevations[0] - meanElevTx
   if source_effective_height_m < 0:
     source_effective_height_m = meanElevTx

   eff_heights = []
   reversed_elev = elevations[::-1]
   for i in range(0, int(math.ceil(dMaxKm/resolution))):
     if i*resolution >= dMinKm and i*resolution <= dMaxKm:
       eff_heights.append(reversed_elev[i])

   eff_heights = eff_heights[::-1]

   meanElevRx = math.fsum(eff_heights) / len(eff_heights);
   dest_effective_height_m = dest_height_m + elevations[-1] - meanElevRx
   if dest_effective_height_m < 0:
     dest_effective_height_m = meanElevRx

  return source_effective_height_m, dest_effective_height_m


# The mixed-path correction adapts the model to cases where the propagation path passes
# over both land and sea. The sea_path should correspond in array index to the profile
# array, and have 1 where the path is over-sea.
def MixedPathCorrection(profile, sea_path):
  numPoints = profile[0]+1
  resolution = float(profile[1]/1000.0);
  elevations = profile[2:]
  distance = float(profile[0] * resolution)
  
  sea_path = sea_path[2:]
  sea_distance = sum(sea_path) * resolution

  beta = sea_distance/distance

  near_sea_threshold = 1.0   # value in km

  # print len(elevations), len(sea_path)

  tx_near_sea = False
  rx_near_sea = False
  for i in range(0, int(math.ceil(near_sea_threshold/resolution))):
    if i*resolution <= near_sea_threshold and sea_path[i] > 0:
      tx_near_sea = True
    if i*resolution <= near_sea_threshold and sea_path[len(sea_path)-1 - i] > 0:
      rx_near_sea = True

  # print tx_near_sea, rx_near_sea
  # print distance, beta

  Kmp_dGreater60km_A = [0.0, 3.0, 5.3, 7.5, 9.2, 10.5, 11.8, 12.7, 13.5, 14.2, 14.8];
  Kmp_dGreater60km_B = [0.0, 1.5, 2.5, 4.0, 5.5, 7.0,  9.0,  10.8, 12.5, 14.2, 14.8];

  Kmp_dLessThan30km_A = [0.0, 2.0, 3.8, 5.0, 6.3, 7.5, 8.5, 9.3, 10.0,  10.5, 11];
  Kmp_dLessThan30km_B = [0.0, 0.5, 1.5, 2.5, 3.5, 4.8, 6.0, 7.8, 9.5,   10.5, 11];

  if distance > 60.0:
    if not tx_near_sea and rx_near_sea:
      Kmp = hill_interp(Kmp_dGreater60km_A, beta)
    elif tx_near_sea and not rx_near_sea:
      Kmp = hill_interp(Kmp_dGreater60km_B, beta)
    else:
      Kmp = (hill_interp(Kmp_dGreater60km_A, beta) +
             hill_interp(Kmp_dGreater60km_B, beta))/2.0

  elif distance < 30.0:
    if not tx_near_sea and rx_near_sea:
      Kmp = hill_interp(Kmp_dLessThan30km_A, beta)
    elif tx_near_sea and not rx_near_sea:
      Kmp = hill_interp(Kmp_dLessThan30km_B, beta)
    else:
      Kmp = (hill_interp(Kmp_dLessThan30km_A, beta) +
             hill_interp(Kmp_dLessThan30km_B, beta))/2.0

  else:
    if not tx_near_sea and rx_near_sea:
      Kmp60 = hill_interp(Kmp_dGreater60km_A, beta)
      Kmp30 = hill_interp(Kmp_dLessThan30km_A, beta)
    elif tx_near_sea and not rx_near_sea:
      Kmp60 = hill_interp(Kmp_dGreater60km_B, beta)
      Kmp30 = hill_interp(Kmp_dLessThan30km_B, beta)
    else:
      Kmp60 = (hill_interp(Kmp_dGreater60km_A, beta) +
               hill_interp(Kmp_dGreater60km_B, beta))/2.0
      Kmp30 = (hill_interp(Kmp_dLessThan30km_A, beta) +
               hill_interp(Kmp_dLessThan30km_B, beta))/2.0

    #interpolate between the Kmp60 and Kmp30 values based on distance
    Kmp = Kmp30 + (distance - 30.0)/(60.0-30.0)*(Kmp60-Kmp30)

  return Kmp

def NarrowPeaks(elevations, peaks, start, end, resolution, min_distance):
  mx = min(elevations) - 1.0
  mxi = -1
  for i in range(start+1, end):
    if peaks[i] == 1 and elevations[i] > mx:
      mx = elevations[i]
      mxi = i

  if mxi == -1:
    for i in range(start, end):
      peaks[i] = 0
    return

  minzi = int(max(start, mxi - math.floor(min_distance/resolution)))
  maxzi = int(min(end, mxi + math.floor(min_distance/resolution)))
  for i in range(minzi, maxzi+1):
    if i != mxi:
      peaks[i] = 0

  if minzi > 0:
    NarrowPeaks(elevations, peaks, start, minzi-1, resolution, min_distance)

  if maxzi < len(elevations)-1:
    NarrowPeaks(elevations, peaks, maxzi+1, end, resolution, min_distance)

def FindPeaks(elevations, min_peak_value):
  peaks = [0] * len(elevations)

  # mark all potential peaks
  # TODO: move to a function...
  for i in range(0, len(elevations)-1):
    if elevations[i] >= min_peak_value:
      if i == 0 and elevations[i] > elevations[i+1]:
        peaks[i] = 1
      elif i == len(elevations)-1 and elevations[i] > elevations[i-1]:
        peaks[i] = 1
      elif elevations[i] > elevations[i-1] and elevations[i] > elevations[i+1]:
        peaks[i] = 1

  in_plateau = False
  for i in range(1, len(elevations)-1):
    if elevations[i] == elevations[i-1] and not in_plateau:
      in_plateau = True
      first_plateau = i-1
    elif elevations[i] != elevations[i-1] and in_plateau:
      last_plateau = i-1
      in_plateau = False
      mid_plateau = int(math.floor((first_plateau + last_plateau)/2.0))
      if elevations[mid_plateau] < min_peak_value:
        continue
      if (first_plateau > 0 and elevations[first_plateau-1] > elevations[first_plateau]) or (
          last_plateau < len(elevations)-1 and elevations[last_plateau] < elevations[last_plateau+1]):
        peaks[mid_plateau] = 0
      else:
        peaks[mid_plateau] = 1
    elif elevations[i] == elevations[i-1] and in_plateau:
      in_plateau = True
    else:
      in_plateau = False

  return peaks


# Develops a correction factor for a single isolated ridge in a propagation path.
def IsolatedRidgeCorrection(profile):
  numPoints = profile[0]+1
  resolution = float(profile[1]/1000.0);
  elevations = profile[2:]
  distance = float(profile[0] * resolution)

  meanElev = math.fsum(elevations) / len(elevations)

  minPeakHeight_m = 100.0  # 100m min peak height
  minPeakSeparation_km = 6.0

  # 'peaks' is an array marking with 1 values where the peaks are.
  peaks = FindPeaks(elevations, meanElev + minPeakHeight_m)

  # Find the tallest peak. Then use minPeakDistance=6km and find the next
  # peak outside of that range. Repeat to get a vector of the found peaks.
  NarrowPeaks(elevations, peaks, 0, len(elevations)-1, resolution, minPeakSeparation_km)

  if sum(peaks) == 0 or sum(peaks) > 1:
    return 0

  peak = max(elevations)
  mxi = elevations.index(peak)
  peak_distance = resolution * mxi

  Kir_A =  [20.0,  6.0, -4.0,  -6.5,  -7.0,  -6.5,  -6.0,  -5.0,  -4.5,  -4.0,  -3.5,  -3.0,  -2.5,  -2.0, -1.5, -1.0, -0.5]
  Kir_B =  [12.0,  0.0, -8.5,  -12.0, -13.0, -12.5, -12.0, -10.5, -10.0, -9.0,  -8.0,  -7.0,  -6.5,  -5.5, -4.5, -4.0, -3.5]
  Kir_C =  [4.0,  -4.0, -13.0, -16.0, -17.5, -18.0, -17.5, -16.0, -15.0, -14.0, -12.5, -11.0, -10.0, -9.0, -8.0, -7.0, -6.0]

  if distance - peak_distance > 8.0:
    if peak_distance >= 60.0:
      Kir = Kir_A[-1]
    elif peak_distance > 30.0 and peak_distance < 60.0:
      Kir60 = Kir_A[-1]
      Kir30 = Kir_B[-1]
      Kir = Kir30 + (peak_distance-30.0)/(60.0-30.0) * (Kir60-Kir30)
    elif peak_distance > 15.0 and peak_distance <= 30.0:
      Kir30 = Kir_B[-1]
      Kir15 = Kir_C[-1]
      Kir = Kir15 + (peak_distance-15.0)/(30.0-15.0) * (Kir30-Kir15)
    else:
      Kir = Kir_C[-1]

  else:
    rx_dist = distance - peak_distance
    if peak_distance >= 60.0:
      Kir = hill_interp(Kir_A, rx_dist/8.0)
    elif peak_distance > 30.0 and peak_distance < 60.0:
      Kir60 = hill_interp(Kir_A, rx_dist/8.0)
      Kir30 = hill_interp(Kir_B, rx_dist/8.0)
      Kir = Kir30 + (peak_distance-30.0)/(60.0-30.0) * (Kir60-Kir30)
    elif peak_distance > 15.0 and peak_distance <= 30.0:
      Kir30 = hill_interp(Kir_B, rx_dist/8.0)
      Kir15 = hill_interp(Kir_C, rx_dist/8.0)
      Kir = Kir15 + (peak_distance-15.0)/(30.0-15.0) * (Kir30-Kir15)
    else:
      Kir = hill_interp(Kir_C, rx_dist/8.0)

  if Kir < -20 or Kir > 20:
    print 'ERROR! Kir = %f for profile' % Kir
    return 0

  h_m = peak - meanElev
  alpha = 0.07*math.sqrt(h_m)   # if you set alpha for h_m=200 to 1, the constant is 0.07071
  Kir = Kir * alpha
  return Kir


def GeneralSlopeCorrection(elev):
  # Distance range on the mobile station's end of the path
  dMinKm = 5
  dMaxKm = 10

  # Extract data from elevation profile 
  numPoints = elev[0] + 1                # number of points between Tx & Rx
  resolution = float(elev[1]/1000.0);
  elevations = elev[2:numPoints+2]
  distance = float(elev[0] * resolution)

  # If all elevations = 0 or distance < dMinKm, set correction factor = 0
  allzeros = True
  for i in range(len(elevations)):
    if elevations[i] <> 0:
      allzeros = False

  if (allzeros or (distance < dMinKm)):
    return 0

  # Distance from each point to the Rx-er (km)
  d_point_Rx_km = numpy.multiply(range(numPoints-1, -1, -1), resolution)
    
  # Compute the average angle of general terrain slope
  intervalVec_km = range(int(dMinKm), int(min(dMaxKm, math.floor(distance)))+1)
  angle = numpy.zeros((len(intervalVec_km)))

  for ii in range(len(intervalVec_km)):
    
    # Get elevation within a certain distance of the mobile station
    elevTemp_m = []
    for j in range(len(elevations)):
      if d_point_Rx_km[j] <= intervalVec_km[ii]:
        elevTemp_m.append(elevations[j])

    p = numpy.polyfit(range(len(elevTemp_m)), elevTemp_m, 1);
    slope = p[0]
    angle[ii] = math.atan(slope/(resolution * 1000.0))


  # Subtract the computed angle from average angle of the overall path distance
  pOverall = numpy.polyfit(range(numPoints), elevations, 1)
  slopeOverall = pOverall[0]
  angleOverall = math.atan(slopeOverall/(resolution * 1000.0))
  angle = angle - angleOverall

  # Select which slope will be used, based on the criteria of [1] Pages 33-34
  all_gt_zero = True
  all_lt_zero = True
  for i in angle:
    if i < 0:
      all_gt_zero = False
    if i > 0:
      all_lt_zero = False
            
  if all_gt_zero:
    primary_angle = numpy.max(angle)
  elif all_lt_zero:
    primary_angle = numpy.min(angle)
  else: # mix slopes have mixture of signs, use the slope at dMinKm = 5
    primary_angle = angle[0]

  # Convert angle (radians) to angle (milliradians)
  angle_mr = primary_angle * 1000.0

  # Set min and max for angle_mr ([2] Figure 34)
  if angle_mr < -20.0:
    angle_mr = -20.0
  elif angle_mr > 20.0:
    angle_mr = 20.0
    
  # Determine the correction factor using curves obtained from Figure 34 of [2]
  thetaVec_Neg = range(-20, 1, 5)   
  kgs_Neg_LT10km = [-5.0, -3.5, -2.0, -1.0, 0.0]
  kgs_Neg_GT30km = [-18.0, -12.5, -8.0, -3.5, 0.0]
  thetaVec_Pos = range(0, 21, 5)
  kgs_Pos_LT10km = [0.0, 1.0, 2.0, 2.5, 3.0]
  kgs_Pos_ET30km = [0.0, 2.5, 4.5, 6.0, 7.0]
  kgs_Pos_GT60km = [0.0, 4.0, 7.0, 10.0, 12]

  # Check average angle of slope
  if (angle_mr == 0.0):          # angle_mr is zero
    Kgs = 0.0
    
  elif (angle_mr < 0.0):         # angle_mr is negative
    
    if (distance < 10.0):    # Resolve for distance < 10 km
        Kgs = piecelin(thetaVec_Neg, kgs_Neg_LT10km, angle_mr)

    elif (distance >= 10.0 and distance <= 30.0):   # Resolve for distance [10, 30] km
      # Linear interpolation b/w kgs_Neg_LT10km and kgs_Neg_GT30km curves
      kgs_10 = piecelin(thetaVec_Neg, kgs_Neg_LT10km, angle_mr)
      kgs_30 = piecelin(thetaVec_Neg, kgs_Neg_GT30km, angle_mr)
      Kgs = piecelin([10.0, 30.0], [kgs_10, kgs_30], distance)
        
    elif (distance > 30.0):  # Resolve for distance > 30 km
      Kgs = piecelin(thetaVec_Neg, kgs_Neg_GT30km, angle_mr)
        
  else:                        # angle_mr is positive
    if (distance < 10.0):    # Resolve for distance < 10 km
      Kgs = piecelin(thetaVec_Pos, kgs_Pos_LT10km, angle_mr)
        
    elif (distance >= 10.0 and distance < 30.0):    # Resolve for distance [10, 30) km
      # Linear interpolation b/w kgs_Pos_LT10km and kgs_Pos_ET30km curves
      kgs_10 = piecelin(thetaVec_Pos, kgs_Pos_LT10km, angle_mr)
      kgs_30 = piecelin(thetaVec_Pos, kgs_Pos_ET30km, angle_mr)
      Kgs = piecelin([10.0, 30.0], [kgs_10, kgs_30], distance)
        
    elif (distance == 30.0): # Resolve for distance = 30 km
      Kgs = piecelin(thetaVec_Pos, kgs_Pos_ET30km, angle_mr)
        
    elif (distance > 30.0 and distance <= 60.0):    # Resolve for distance (30, 60] km
      # Linear interpolation b/w kgs_Pos_ET30km and kgs_Pos_GT60km curves
      kgs_30 = piecelin(thetaVec_Pos, kgs_Pos_ET30km, angle_mr)
      kgs_60 = piecelin(thetaVec_Pos, kgs_Pos_GT60km, angle_mr)
      Kgs = piecelin([30.0, 60.0], [kgs_30, kgs_60], distance)
        
    elif (distance > 60.0):  # Resolve for distance > 60 km
      Kgs = piecelin(thetaVec_Pos, kgs_Pos_GT60km, angle_mr)
    
  # Display an error msg if correction factor is outside [-20, 20] (dB) range
  if (Kgs < - 20.0 or Kgs > 20.0):
    print(['Error: GeneralSlopeCorr.m: Correction ' +
           'factor is outside of [-20, 20] dB range'])
    return 0.0

  return Kgs

