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

"""Vincenty methods for calculating geodesic distance, bearing and locations
along the great circle in the earth ellipsoid.

Typical usage:
  # Get distance and bearing between 2 points on the earth
  dist_km, bearing, rev_bearing = GeodesicDistanceBearing(lat1, lon1, lat2, lon2)

  # Get location of a all points at given bearing, at one or multiple distances
  lat2, lon2 = GeodesicPoints(lat1, lon1, dist_km, bearing)

  # Get N equidistant points along the geodesic between 2 locations
  points = GeodesicSampling(lat, lon1, lat2, lon2, N)
"""

from math import pi, radians, degrees, atan, atan2, tan, cos, sin
import numpy as np


def GeodesicDistanceBearing(lat1, lon1, lat2, lon2, accuracy=1.0E-12):
  """Calculates distance and bearings between two points.

  This uses Vincenty formula with an accuracy parameter used
  to set the convergence of lambda. The default 1E-12 corresponds
  to approximately 0.06 mm.

  The formulas and nomenclature are from Vincenty, 1975:
    https://www.ngs.noaa.gov/PUBS_LIB/inverse.pdf
  See also:
    https://en.wikipedia.org/wiki/Vincenty's_formulae

  Inputs:
    lat1, lon1: the initial point coodinates (in degrees)
    lat2, lon2: the final point coodinates (in degrees)
    accuracy: accuracy for the vincenty convergence (optional)

  Returns:
    a tuple of distance (km), initial bearing (deg), and back bearing (deg).
  """
  if lat1 == lat2 and lon1 == lon2:
    return 0., 0., 0.

  a = 6378.1370        # semi-major axis (km), WGS84
  f = 1./298.257223563 # flattening of the ellipsoid, WGS84
  b = (1-f)*a          # semi-minor axis

  phi1 = radians(lat1)
  L1   = radians(lon1)
  phi2 = radians(lat2)
  L2   = radians(lon2)

  U1 = atan((1-f)*tan(phi1))
  U2 = atan((1-f)*tan(phi2))
  L = L2 - L1

  lmbda = L
  lastlmbda = 9.E40

  while abs(lmbda - lastlmbda) > accuracy:

    lastlmbda = lmbda

    sin_sigma = ((cos(U2)*sin(lmbda))**2.0 +
                 (cos(U1)*sin(U2) - sin(U1)*cos(U2)*cos(lmbda))**2.0)**0.5
    cos_sigma = sin(U1)*sin(U2) + cos(U1)*cos(U2)*cos(lmbda)
    sigma = atan2(sin_sigma, cos_sigma)

    sin_alpha = (cos(U1)*cos(U2)*sin(lmbda))/sin(sigma)
    cossq_alpha = 1 - sin_alpha**2.0

    cos2sigma_m = cos(sigma) - (2.*sin(U1)*sin(U2)/cossq_alpha)

    C = (f/16.)*cossq_alpha*(4. + f*(4. - 3.*cossq_alpha))

    lmbda = (L + (1. - C)*f*sin_alpha
             *(sigma + C*sin_sigma
               * (cos2sigma_m + C*cos_sigma
                  * (-1. + 2.*cos2sigma_m**2.0))))

  usq = cossq_alpha*(a**2.0 - b**2.0)/b**2.0
  A = 1 + (usq/16384.)*(4096. + usq*(-768. + usq*(320. - 175.*usq)))
  B = (usq/1024.)*(256. + usq*(-128. + usq*(74. - 47.*usq)))
  dsigma = (B*sin(sigma)
            * (cos2sigma_m + 0.25*B
               * (cos(sigma)*(-1. + 2.*cos2sigma_m**2.0)
                  - (1./6.)*B*cos2sigma_m*(-3. + 4.*sin(sigma)**2.0)
                  * (-3. + 4.*cos2sigma_m**2.0))))

  s = b*A*(sigma-dsigma)

  alpha1 = atan2(cos(U2)*sin(lmbda),
                 (cos(U1)*sin(U2) - sin(U1)*cos(U2)*cos(lmbda)))
  alpha2 = atan2(cos(U1)*sin(lmbda),
                 (-sin(U1)*cos(U2) + cos(U1)*sin(U2)*cos(lmbda)))

  if alpha2 < pi:
    alpha2 = alpha2 + pi
  else:
    alpha2 = alpha2 - pi

  alpha1 = (alpha1 + 2.*pi) % (2.*pi)
  alpha2 = (alpha2 + 2.*pi) % (2.*pi)

  alpha1 = degrees(alpha1)
  alpha2 = degrees(alpha2)
  print("Distance,Azimuth: %.15f,%.15f" %(s,alpha1))
  return s, alpha1, alpha2


def GeodesicPoint(lat, lon, dist_km, bearing, accuracy=1.0E-12):
  """Computes the coordinates from a point towards a bearing at given distance.

  This uses Vincenty formula with an accuracy parameter used
  to set the convergence of lambda. The default 1E-12 corresponds
  to approximately 0.06 mm.

  The formulas and nomenclature are from Vincenty, 1975:
    https://www.ngs.noaa.gov/PUBS_LIB/inverse.pdf
  See also:
    https://en.wikipedia.org/wiki/Vincenty's_formulae

  Inputs:
    lat,lon: the initial point coordinates (in degrees),
    dist_km: the distance of the target point (in km)
    bearing: the bearing angle (in degrees)
    accuracy: accuracy for the vincenty convergence (optional)

  Returns:
    a tuple of the final point latitude, longitude and final reverse bearing, all in degrees.
  """

  a = 6378.1370        # semi-major axis (km), WGS84
  f = 1./298.257223563 # flattening of the ellipsoid, WGS84
  b = (1-f)*a          # semi-minor axis

  phi1 = radians(lat)
  L1   = radians(lon)
  alpha1 = radians(bearing)
  s = dist_km

  U1 = atan((1-f)*tan(phi1))

  sigma1 = atan2(tan(U1), cos(alpha1))

  sinalpha = cos(U1)*sin(alpha1)
  cossq_alpha = (1. - sinalpha**2.0)
  usq = cossq_alpha*(a**2.0-b**2.0)/b**2.0

  A = 1 + usq/16384. * (4096. + usq*(-768 + usq*(320.-175.*usq)))
  B = usq/1024.*(256. + usq*(-128. + usq*(74.-47.*usq)))

  sigma = s/(b*A)
  lastsigma = 1.E40

  while abs(sigma - lastsigma) > accuracy:

    lastsigma = sigma

    twosigmam = 2.*sigma1 + sigma
    dsigma = (B*sin(sigma)
              *(cos(twosigmam) + 0.25*B
                *(cos(sigma)
                  *(-1. + 2.*cos(twosigmam)**2.0)
                  - (1./6.)*B*cos(twosigmam)
                  * (-3. + 4. *sin(sigma)**2.0)
                  * (-3. + 4.*cos(twosigmam)**2.0))))
    sigma = s/(b*A) + dsigma

  num = sin(U1)*cos(sigma) + cos(U1)*sin(sigma)*cos(alpha1)
  den = (1.-f)*(sinalpha**2.0 + (sin(U1)*sin(sigma)
                                 - cos(U1)*cos(sigma)*cos(alpha1))**2.0)**0.5

  phi2 = atan2(num, den)

  num = sin(sigma)*sin(alpha1)
  den = cos(U1)*cos(sigma) - sin(U1)*sin(sigma)*cos(alpha1)
  lmbda = atan2(num, den)

  C = (f/16.)*cossq_alpha*(4. + f*(4. - 3.*cossq_alpha))

  L = (lmbda - (1. - C)*f*sinalpha
       * (sigma + C*sin(sigma)
          *(cos(twosigmam) + C*cos(sigma)
            * (-1. + 2.*cos(twosigmam)**2.0))))
  L2 = L + L1

  num = sinalpha
  den = -sin(U1)*sin(sigma) + cos(U1)*cos(sigma)*cos(alpha1)
  alpha2 = atan2(num, den)
  alpha2 = (alpha2 + 3.*pi) % (2.*pi)

  return degrees(phi2), degrees(L2), degrees(alpha2)


def GeodesicPoints(lat, lon, distances_km, bearing, accuracy=1.0E-12):
  """Computes the coordinates from a point towards a bearing for several distances.

  This uses Vincenty formula with an accuracy parameter used
  to set the convergence of lambda. The default 1E-12 corresponds
  to approximately 0.06 mm.

  The formulas and nomenclature are from Vincenty, 1975:
    https://www.ngs.noaa.gov/PUBS_LIB/inverse.pdf
  See also:
    https://en.wikipedia.org/wiki/Vincenty's_formulae

  This routine version is similar to `GeodesicPoint` but takes a sequence of
  distances, and perform an efficient vectorized operation internally.

  Inputs:
    lat,lon: the initial point coordinates (in degrees),
    distances_km: a sequence of distance of the target points (in km). Can be
      for example a ndarray or a list.
    bearing: the bearing angle (in degrees)
    accuracy: accuracy for the vincenty convergence (optional)

  Returns:
    a tuple of the points latitude, longitude and reverse bearing, all in degrees.
    If input distances_km is a ndarray, 3 ndarray are returned,
    otherwise 3 lists are returned.
  """

  if np.isscalar(distances_km):
    return GeodesicPoint(lat, lon, distances_km, bearing, accuracy)

  a = 6378.1370        # semi-major axis (km), WGS84
  f = 1./298.257223563 # flattening of the ellipsoid, WGS84
  b = (1-f)*a          # semi-minor axis

  phi1 = radians(lat)
  L1   = radians(lon)
  alpha1 = radians(bearing)
  s = np.asarray(distances_km)

  U1 = atan((1-f)*tan(phi1))

  sigma1 = atan2(tan(U1), cos(alpha1))

  sinalpha = cos(U1)*sin(alpha1)
  cossq_alpha = (1. - sinalpha**2.0)
  usq = cossq_alpha*(a**2.0-b**2.0)/b**2.0

  A = 1 + usq/16384. * (4096. + usq*(-768 + usq*(320.-175.*usq)))
  B = usq/1024.*(256. + usq*(-128. + usq*(74.-47.*usq)))

  sigma = s/(b*A)
  lastsigma = np.zeros(len(s))
  twosigmam = np.zeros(len(s))
  dsigma = np.zeros(len(s))
  idxs = np.arange(len(s))
  while True:
    # Using iteration on partial subset for perfect equivalence
    # with scalar version
    lastsigma[idxs] = sigma[idxs]

    twosigmam[idxs] = 2.*sigma1 + sigma[idxs]
    cos_twosigmam = np.cos(twosigmam[idxs])
    sin_sigma = np.sin(sigma[idxs])
    cos_sigma = np.cos(sigma[idxs])
    dsigma[idxs] = (B * sin_sigma
                    *(cos_twosigmam + 0.25*B
                      *(cos_sigma
                        *(-1. + 2. * cos_twosigmam**2)
                        - (1./6.) * B * cos_twosigmam
                        * (-3. + 4. * sin_sigma**2)
                        * (-3. + 4. * cos_twosigmam**2))))
    sigma[idxs] = s[idxs]/(b*A) + dsigma[idxs]
    idxs = np.where(np.abs(sigma - lastsigma) > accuracy)[0]
    if not len(idxs):
      break
  cos_sigma = np.cos(sigma)
  sin_sigma = np.sin(sigma)
  cos_twosigmam = np.cos(twosigmam)

  num = sin(U1) * cos_sigma + cos(U1) * sin_sigma * cos(alpha1)
  den = ((1.-f) * (sinalpha**2 +
                   (sin(U1) * sin_sigma - cos(U1) * cos_sigma * cos(alpha1))**2)**0.5)

  phi2 = np.arctan2(num, den)

  num = sin_sigma * sin(alpha1)
  den = cos(U1) * cos_sigma - sin(U1) * sin_sigma * cos(alpha1)
  lmbda = np.arctan2(num, den)

  C = (f/16.) * cossq_alpha * (4. + f * (4. - 3.*cossq_alpha))

  L = (lmbda - (1. - C) * f * sinalpha
       * (sigma + C * sin_sigma
          * (cos_twosigmam + C * cos_sigma
             * (-1. + 2. * cos_twosigmam**2))))
  L2 = L + L1

  num = sinalpha
  den = -sin(U1) * sin_sigma + cos(U1) * cos_sigma * cos(alpha1)
  alpha2 = np.arctan2(num, den)
  alpha2 = (alpha2 + 3.*pi) % (2.*pi)

  if isinstance(distances_km, np.ndarray):
    return np.degrees(phi2), np.degrees(L2), np.degrees(alpha2)
  else:
    return list(np.degrees(phi2)), list(np.degrees(L2)), list(np.degrees(alpha2))


def GeodesicSampling(lat1, lon1, lat2, lon2, num_points):
  """Returns a geodesic between 2 points defined as equally spaced points.

  Inputs:
    lat1, lon1 : the initial point coordinates.
    lat2, lon2 : the final point coordinates.
    num_points : number of points to use (must be >=2)

  Returns:
    A tuple (lats, longs) of ndarray vector defining points along the
    geodesic. The two input locations are first and last points.
  """
  dist, bearing, _ = GeodesicDistanceBearing(lat1, lon1, lat2, lon2)
  step_km = dist / (float(num_points-1))
  print("GreatCircle_km: %.15f" %step_km)
  distances = step_km * np.arange(0, num_points)
  lats, lons, _ = GeodesicPoints(lat1, lon1, distances, bearing)
  lats[0], lons[0] = lat1, lon1
  lats[-1], lons[-1] = lat2, lon2
  return lats, lons
