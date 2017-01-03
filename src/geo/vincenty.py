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

# Implements Vincenty formula for calculating distance and bearing.
#
# Andrew Clegg
# December 2016

from math import *

def dist_bear_vincenty(lat1, lon1, lat2, lon2, accuracy=1.0E-12):
    """
    Calculates distance and bearings between two points using Vincenty
    formula. The accuracy parameter is used to set the convergence of
    lambda. 1E-12 corresponds to approximately 0.06 mm.

    The formulas and nomenclature are from Vincenty, 1975:
    https://www.ngs.noaa.gov/PUBS_LIB/inverse.pdf

    Input lat/lons are in deg.

    Returns distance (km), initial bearing (deg), and back azimuth (deg).

    Andrew Clegg
    December 2016
    """

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

        lmbda = L + (1. - C)*f*sin_alpha \
                *(sigma + C*sin_sigma \
                  * (cos2sigma_m + C*cos_sigma \
                     * (-1. + 2.*cos2sigma_m**2.0)))

    usq = cossq_alpha*(a**2.0 - b**2.0)/b**2.0
    A = 1 + (usq/16384.)*(4096. + usq*(-768. + usq*(320. - 175.*usq)))
    B = (usq/1024.)*(256. + usq*(-128. + usq*(74. - 47.*usq)))
    dsigma = B*sin(sigma) \
             * (cos2sigma_m + 0.25*B \
               * (cos(sigma)*(-1. + 2.*cos2sigma_m**2.0) \
                  - (1./6.)*B*cos2sigma_m*(-3. + 4.*sin(sigma)**2.0)
                   * (-3. + 4.*cos2sigma_m**2.0)))

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

    return s, alpha1, alpha2

def to_dist_bear_vincenty(lat, lon, dist, bear, accuracy=1.0E-12):
    """
    Computes the latitude and longitude that is a specified distance
    and bearing from a given lat/lon. This version uses Vincenty's formula.

    The formulas and nomenclature are from Vincenty, 1975:
    https://www.ngs.noaa.gov/PUBS_LIB/inverse.pdf

    Input lat/lon in deg, dist in km, bear in deg.

    Returns final lat/lon in deg, and final bearing in deg.

    Andrew Clegg
    December 2016
    """

    a = 6378.1370        # semi-major axis (km), WGS84
    f = 1./298.257223563 # flattening of the ellipsoid, WGS84
    b = (1-f)*a          # semi-minor axis

    phi1 = radians(lat)
    L1   = radians(lon)
    alpha1 = radians(bear)
    s = dist

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
        dsigma = B*sin(sigma) \
                 *(cos(twosigmam) + 0.25*B \
                   *(cos(sigma) \
                     *(-1. + 2.*cos(twosigmam)**2.0) \
                     - (1./6.)*B*cos(twosigmam) \
                     * (-3. + 4. *sin(sigma)**2.0) \
                     * (-3. + 4.*cos(twosigmam)**2.0)))
        sigma = s/(b*A) + dsigma

    num = sin(U1)*cos(sigma) + cos(U1)*sin(sigma)*cos(alpha1)
    den = (1.-f)*(sinalpha**2.0 + (sin(U1)*sin(sigma) - cos(U1)*cos(sigma)*cos(alpha1))**2.0)**0.5

    phi2 = atan2(num, den)

    num = sin(sigma)*sin(alpha1)
    den = cos(U1)*cos(sigma) - sin(U1)*sin(sigma)*cos(alpha1)
    lmbda = atan2(num, den)

    C = (f/16.)*cossq_alpha*(4. + f*(4. - 3.*cossq_alpha))

    L = lmbda - (1. - C)*f*sinalpha \
        * (sigma + C*sin(sigma) \
           *(cos(twosigmam) + C*cos(sigma) \
             * (-1. + 2.*cos(twosigmam)**2.0)))
    L2 = L + L1

    num = sinalpha
    den = -sin(U1)*sin(sigma) + cos(U1)*cos(sigma)*cos(alpha1)
    alpha2 = atan2(num, den)
    alpha2 = (alpha2 + 2.*pi) % (2.*pi)

    return degrees(phi2), degrees(L2), degrees(alpha2)

