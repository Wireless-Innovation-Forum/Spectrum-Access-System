# Python port of ITS eHata C++ code. WinnForum extensions have been added,
# after R2-SGN-04. This includes the following WinnForum extensions:
#    - Minimum CBSD height/effective height of 20 m
#    - No effective height corrections on mobile/receive side
#    - Added standalne effective height routine
#    - Removed trace/debug code
#    - Refactored AverageTerrainHeight() function
#    - Refactored FindQuantile() function
#
# Andrew Clegg
# April 2017

import numpy as npy
import math

class InterValues:

    # Data structure containing intermediate calculated values
    
    def __init__(self):
        self.d_bp__km = 0.0
        self.att_1km = 0.0
        self.att_100km = 0.0

        self.h_b_eff__meter = 0.0
        self.h_m_eff__meter = 0.0

        #// Terrain Stats
        self.pfl10__meter = 0.0
        self.pfl50__meter = 0.0
        self.pfl90__meter = 0.0
        self.deltah__meter = 0.0

        #// Path Geometry
        self.d__km = 0.0
        self.d_hzn__meter = [0.0, 0.0]
        self.h_avg__meter = [0.0, 0.0]
        self.theta_m__mrad = 0.0
        self.beta = 0.0
        self.iend_ov_sea = 0
        self.hedge_tilda = 0.0
        self.single_horizon = False

        #// Misc
        self.slope_max = 0.0
        self.slope_min = 0.0


def EffectiveHeights(h_b, h_m, pfl):
    """

    *** Note: The mobile side calculation is not correctly implemented and
    is not used in the WF prop model.
    
    """

    np = int(pfl[0])
    xi = pfl[1] * 0.001      #// step size of the profile points, in km
    d__km = np * xi          #// path distance, in km

    summ = 0.0

    if (d__km < 3.0):
        return h_b, h_m
    elif (3.0 <= d__km and d__km <= 15.0):
        i_start = 2 + int(3.0 / xi)
        i_end = np + 2
        for i in range(i_start, i_end+1): # (int i = i_start; i <= i_end; i++)
            summ = summ + pfl[i] ####
        h_b_terrain_avg = pfl[2] - (pfl[2] - summ / (i_end - i_start + 1)) * \
                                      (d__km - 3.0) / 12.0
#        print d__km, pfl[2], summ / (i_end - i_start + 1), h_b_terrain_avg
        i_start = 2
        i_end = np + 2 - int(3.0 / xi)
        summ = 0.0
        for i in range(i_start, i_end+1): # (int i = i_start; i <= i_end; i++)
            summ = summ + pfl[i]
        h_m_terrain_avg = summ / (i_end - i_start + 1) * \
                                      (d__km - 3.0) / 12.0
    else: #// d__km > 15.0
        i_start = 2 + int(3.0 / xi)
        i_end = 2 + int(15.0 / xi)
        for i in range(i_start, i_end+1): #(int i = i_start; i <= i_end; i++)
            summ = summ + pfl[i]
        h_b_terrain_avg = summ / (i_end - i_start + 1)

        i_start = np + 2 - int(15.0 / xi)
        i_end = np + 2 - int(3.0 / xi)
        summ = 0.0
        for i in range(i_start, i_end+1): #(int i = i_start; i <= i_end; i++)
            summ = summ + pfl[i]
        h_m_terrain_avg = summ / (i_end - i_start + 1)
    
    return (h_b + pfl[2]) - h_b_terrain_avg, (h_m + pfl[-1]) - h_m_terrain_avg


def FindHorizons(pfl, gme, d__meter, h_1__meter, h_2__meter, d_hzn__meter):
    """
    Port of ITS FindHorizons.cpp
    """
    
    theta = [0., 0.]

    np = pfl[0]
    xi = pfl[1]
    za = pfl[2] + h_1__meter
    zb = pfl[np + 2] + h_2__meter
    qc = 0.5 * gme
    q = qc * d__meter
    theta[1] = (zb - za) / d__meter
    theta[0] = theta[1] - q
    theta[1] = -theta[1] - q
    d_hzn__meter[0] = d__meter
    d_hzn__meter[1] = d__meter

    if np < 2:
        return

    sa = 0.
    sb = d__meter
    wq = True

    for i in range(2, np+1):
        sa = sa + xi
        sb = sb - xi
        q = pfl[i + 1] - (qc * sa + theta[0])*sa - za
        if q > 0:
            theta[0] = theta[0] + q / sa
            d_hzn__meter[0] = sa
            wq = False
        if not wq:
            q = pfl[i + 1] - (qc*sb + theta[1])*sb - zb
            if q > 0:
                theta[1] = theta[1] + q / sb
                d_hzn__meter[1] = sb
    

def FindQuantile(npts, a, ir):
    """
    Re-write of ITS FindQuantile function. In this version, npts is not needed,
    but is retained as an input for backward compatibility.

    Andrew Clegg
    April 2017
    """

    return npy.sort(npy.asarray(a))[::-1][ir]
    

def FineRollingHillyTerrainCorectionFactor(interValues, h_m_gnd__meter):
    """
    Python port of ITS function.
    
    Description: Find the fine rolling hill terrain correction factor
    Inputs:
        interValues.pfl10__meter : 10% terrain quantile
        interValues.pfl50__meter : 50% terrain quantile
        interValues.pfl90__meter : 90% terrain quantile
        interValues.deltah__meter : terrain irregularity parameter
        h_m_gnd__meter : mobile ground height, in meters
    Return:
        correction factor
    """
    
    a = -11.728795
    b = 15.544272
    c = -1.8154766

    # deltaH must be at least 10 meters
    if (interValues.deltah__meter < 10.0):
        deltah_use = 10.0
    else:
        deltah_use = interValues.deltah__meter
        
    K_h = a + math.log10(deltah_use) * (b + c * math.log10(deltah_use))

    if (h_m_gnd__meter >= interValues.pfl10__meter):
        return K_h
    elif (h_m_gnd__meter <= interValues.pfl90__meter):
        return -K_h
    elif (h_m_gnd__meter < interValues.pfl10__meter and
          h_m_gnd__meter >= interValues.pfl50__meter):
        return K_h * (h_m_gnd__meter - interValues.pfl50__meter) / \
               (interValues.pfl10__meter - interValues.pfl50__meter)
    else:
        return -K_h * (h_m_gnd__meter - interValues.pfl90__meter) / \
               (interValues.pfl50__meter - interValues.pfl90__meter)


def GeneralSlopeCorrectionFactor(theta_m__mrad, d__km):
    """
    Python port of ITS function.

    Description: Find the general slope correction factor
    Reference: Section 4.3 of [Okumura]
    Inputs:
        theta_m__mrad : mobile terrain slope, in millirads
        d__km : path distance, in kilometers
    Return:
        correction factor
    """
    
    emm1 = 0.25
    emm2 = 0.8
    emp1 = 0.125
    emp2 = 0.35
    emp3 = 0.6

    ## computing values from the curves on Fig 34 in Okumura
    if (theta_m__mrad <= 0.0):
        if (d__km <= 10.0):
            return theta_m__mrad * emm1    # the d < 10km line
        elif (d__km >= 30.0):
            return theta_m__mrad * emm2    # the d > 30km line
        else:
            # interpolate between the two lines
            return theta_m__mrad * \
                   (emm1 + 0.05 * (emm2 - emm1) * (d__km - 10.0))
    else:
        if (d__km <= 10.0):
            return theta_m__mrad * emp1    # the d < 10km line
        elif (d__km >= 60.0):
            return theta_m__mrad * emp3    # the d > 60km line
        elif (d__km > 10.0 and d__km <= 30.0):
            # interpolate
            return theta_m__mrad * \
                   (emp1 + 0.05 * (d__km - 10.0) * (emp2 - emp1))
        else: #if (d__km > 30.0 .and.d__km < 60)
            # interpolate
            return theta_m__mrad * \
                   (emp2 + (d__km - 30.0) * (emp3 - emp2) / 30.0)


def IsolatedRidgeCorrectionFactor(d1_hzn__km, d2_hzn__km, h_edge__meter):
    """
    Python port of an ITS function.

    Description: Find the isolated ridge correction factor
    Reference: Section 4.2 of [Okumura]
    Inputs:
        d1_hzn__km : horizon distance, in kilometers
        d2_hzn__km : horizon distance, in kilometers
        h_edge__meter : intermediate value
    Return:
        correction factor
   """

    d_1__km = [15.0, 30.0, 60.0]
    d_2__km = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    
    # points from Figure 31, Okumura
    curve_data = \
        [
             [ 4.0, -13.0, -17.5, -17.5, -15.0, -12.5, -10.0, -8.0, -6.0],
             [12.0,  -8.5, -13.0, -12.0, -10.0,  -8.0,  -6.5, -5.0, -4.0],
             [20.0,  -4.0,  -6.5,  -6.0,  -4.5,  -3.5,  -2.5, -2.0, -1.0]
        ]

    # normalized ridge height factor
    alpha = npy.sqrt(h_edge__meter / 200.0) # Eq 1, Okumura, alpha = 0.07 * sqrt(h)

    id1 = 0
    if (d1_hzn__km >= d_1__km[1]):
        id1 = 1
    id2 = 0;

    while (id2 < 7 and d2_hzn__km > d_2__km[id2 + 1]):
        id2 = id2 + 1

    c1 = curve_data[id1][id2] + (curve_data[id1][id2 + 1] -           \
                                 curve_data[id1][id2]) *              \
                                 (d2_hzn__km - d_2__km[id2]) /        \
                                 (d_2__km[id2 + 1] - d_2__km[id2])
    c2 = curve_data[id1 + 1][id2] + (curve_data[id1 + 1][id2 + 1] -   \
                                     curve_data[id1 + 1][id2]) *      \
                                     (d2_hzn__km - d_2__km[id2]) /    \
                                     (d_2__km[id2 + 1] - d_2__km[id2])

    return alpha * (c1 + (c2 - c1) *
                    (d1_hzn__km - d_1__km[id1]) /
                    (d_1__km[id1 + 1] - d_1__km[id1]))


def LeastSquares(pfl_segment, x1, x2, z0, zn):
    """
    Implements ITS function.

    Description: Least squares fit
    Inputs:
        pfl_segment : Terrain profile line with:
                 - pfl_segment[0] = number of terrain points + 1
                 - pfl_segment[1] = step size, in meters
                 - pfl_segment[i] = elevation above mean sea level, in meters

    AWC note: modifies z0 and zn. Make sure these values as passed to the
    function are mutable.
    """
    
    xn = int(pfl_segment[0])
    xi = pfl_segment[1]

    xa = int(max(x1 / xi, 0.0))
    xb = xn - int(max(xn - x2 / xi, 0.0))

    if (xb <= xa):
        xa = max(xa - 1.0, 0)
        xb = xn - max(xn - xb + 1.0, 0)

    ja = xa
    jb = xb
    n = int(jb - ja)
    xa = xb - xa
    x = -0.5 * xa
    xb = xb + x;
    a = 0.5 * (pfl_segment[ja + 2] + pfl_segment[jb + 2])
    b = 0.5 * (pfl_segment[ja + 2] - pfl_segment[jb + 2]) * x
    
    for i in range(2, n+1): #(int i = 2; i <= n; i++)
        ja = ja + 1
        x = x + 1.
        a = a + pfl_segment[ja + 2]
        b = b + pfl_segment[ja + 2] * x

    a = a / xa
    b = b * 12. / ((xa * xa + 2.) * xa)
    z0[0] = a - b * xb
    zn[0] = a + b * (xn - xb)


def MedianBasicPropLoss(f__mhz, h_b__meter, h_m__meter, d__km, enviro_code,
                        plb_med__db, interValues):
    """
    Port of ITS routine.
    """
    
    perm = 4.0e-7 * math.pi
    eps = 8.854e-12
    c = 1.0 / (eps*perm)**0.5


    ## Extend the frequency range to 3,000 MHz. This is done by computing
    ## alpha_1, beta_1, and gamma_1 in Okumura et al.'s median reference
    ## attenuation equation in an urban environment.
    ##
    ## Solve the 3 simultanious equations :
    ##		- A-4a: 22    dB @ 1500 MHz at 1 km
    ##		- A-4b: 23.5  db @ 2000 MHZ at 1 km
    ##		- A-4c: 25.85 dB @ 3000 MHz at 1 km
    ## Using algebra to rearrange the equations for alpha_1, beta_1,
    ## and gamma_1 yields

    # reference h_b = 200 m and h_m = 3 m, at 1 km apart
    sr_1km = (1.0e+6 + pow((200.0 - 3.0), 2))**0.5

    # reference h_b = 200
    htg_hb_ref = 13.82 * math.log10(200.0)

    # reference h_m = 3 m.This is Eq 16 in Hata
    htg_hm_ref = 3.2 * pow(math.log10(11.75 * 3.0), 2) - 4.97

    #wavenumber for 1500 MHz
    wn_1500 = 2.0 * math.pi * 1.5e+9 / c

    gamma_1 = (3.85 / math.log10(2.0) - 1.5 / math.log10(4.0 / 3.0)) / \
              math.log10(1.5)
    beta_1 = 20. + 1.5 / math.log10(4.0 / 3.0) - gamma_1 * math.log10(3.0e+6)
    
    alpha_1 = 22. + htg_hb_ref + htg_hm_ref + \
              20 * math.log10(2.0 * wn_1500 * sr_1km) - \
              math.log10(1500.0) * (beta_1 + gamma_1 * math.log10(1500.0))

    ## Repeat the above process but solve for the suburban coefficients using
    ## the following values :
    ##      - A-4a: 11.5 dB @ 1500 MHz at 1 km
    ##      - A-4b: 12.4 db @ 2000 MHZ at 1 km
    ##      - A-4c: 14   dB @ 3000 MHz at 1 km
    ## Using algebra to rearrange the equations for alpha_1_suburban,
    ## beta_1_suburban, and gamma_1_suburban yeilds
    denom = math.log10(4.0 / 3.0) * math.log10(1.5) * math.log10(2.0)
    gamma_1_suburban = (2.5 * math.log10(4.0 / 3.0) - 0.9 * math.log10(2.0)) / denom;
    beta_1_suburban = (0.9 * math.log10(2.0) * math.log10(4.5e+6) -
                       2.5 * math.log10(4.0 / 3.0) * math.log10(3.0e+6)) / denom
    alpha_1_suburban = 11.5 - beta_1_suburban * math.log10(1.5e+3) - \
                       gamma_1_suburban * pow(math.log10(1.5e+3), 2)

    ## Extended the range by fitting to the functional form at 100 km:
    ##      alpha_100 + beta_100 * log(f) + gamma_100 * log^2(f)
    ## Using the following points:
    ##      63.5  dB @ 1500 MHz at 100 km
    ##      65.75 dB @ 2000 MHz at 100 km
    ##      69.5  dB @ 3000 MHz at 100 km
    ## Solving yields:
    alpha_100 = 120.78129
    beta_100 = -52.714929
    gamma_100 = 10.919011
	
    ## coefficients for the power law exponent(wrt distance) (20 <= d <= 100)
    ## these come from figure 12 of Okumura et al. (1968) at base effective
    ## antenna heights of 24.5 m, 70 m and 200 m. The corresponding values of
    ## n / 2 are: 2.5, 3 and 3.22 respectively
    tau = (0.72 * math.log10(70.0 / 24.5) - 0.5*math.log10(200.0 / 24.5)) / \
          math.log10(70.0 / 24.5) / math.log10(200.0 / 70.0) / \
          math.log10(200.0 / 24.5)
    sigma = 0.72 / math.log10(200.0 / 24.5) - tau * math.log10(200.0 * 24.5)
    rho = 2.5 - math.log10(24.5) * (sigma + tau * math.log10(24.5))

    suburban_factor = alpha_1_suburban + beta_1_suburban * \
                      math.log10(f__mhz) + gamma_1_suburban * \
                      pow(math.log10(f__mhz), 2)
    rural_factor = 40.94 - 18.33 * math.log10(f__mhz) + 4.78 * \
                   pow(math.log10(f__mhz), 2)
	
    ## this next step assumes that the height gain corrections are identical
    ## above and below the break point

    wnmh = 2.0e+6*math.pi*f__mhz / c;
    term1 = math.log10(f__mhz) * (beta_1 + gamma_1 * math.log10(f__mhz))
    interValues.att_1km = alpha_1 + term1 - htg_hb_ref - htg_hm_ref - \
                          20.0*math.log10(2.0*wnmh*sr_1km)
    interValues.att_100km = alpha_100 + math.log10(f__mhz)* \
                            (beta_100 + gamma_100*math.log10(f__mhz))
    term2 = -13.82*math.log10(h_b__meter)

    ## find the "break-point" distance, d_bp, where the attenuation
    ## transitions from the Hata distance exponent, n_l, to a larger
    ## distance exponent drawn from figure 12 of Okumura et al. (1968),
    ## n_h.n.b., d_bp depends on f and hb
    ## // n_h = 2 * (rho + sigma * math.log10(h_b__meter) + tau * pow(log10(h_m__meter), 2) - 1);
    n_h = 2.0*(rho + math.log10(h_b__meter)*(sigma + tau*math.log10(h_b__meter)) - 1.0)

    ## ***ITS Comment:  NOTE! 44.9 OR 24.9????  And why the -2??
    n_l = 0.1 * (44.9 - 6.55*math.log10(h_b__meter)) - 2.0
    
    interValues.d_bp__km = pow(10.0, (2.0 * n_h + 0.1 * \
                (interValues.att_1km - interValues.att_100km)) / (n_h - n_l))

    terma = -3.2 * pow(math.log10(11.75 * h_m__meter), 2) + 4.97
    ##  // BK: distance from base station to mobile, along the ray
    ## (compute triangle hypoth)
    sr_d = (1.0e+6 * pow(d__km, 2) + pow(h_b__meter - h_m__meter, 2))**0.5

    ## d_bp is the break-point distance in the TR, where if the distance is less than the break - point distance,
    ##     the original Hata power law exponent and the refitted Hata intercept are used.  Else the model uses
    ##     the long distance power law exponent and the 100km basic median attenuation curve fit
    if (d__km <= interValues.d_bp__km):
        plb_urban = alpha_1 + term1 + term2 + terma + \
                    (44.9 - 6.55*math.log10(h_b__meter))*math.log10(d__km)
    else:
        plb_urban = interValues.att_100km + htg_hb_ref + term2 + \
                    htg_hm_ref + terma - 20*n_h + \
                    10.0*n_h*math.log10(d__km) + 20.0*math.log10(2.0*wnmh*sr_d)

    if (enviro_code == 23 or enviro_code == 24): 
        plb_med__db[0] = plb_urban
    elif (enviro_code == 22): 
        plb_med__db[0] = plb_urban - suburban_factor
    else:
        plb_med__db[0] = plb_urban - rural_factor


def MedianRollingHillyTerrainCorrectionFactor(deltah__meter):
    """
    Port of an ITS function.

    Description: Compute the mean rolling hill terrain correction factor
    Inputs:
        delta_h__meter : terrain irregularity factor
    Return:
       correction factor
    """

    a = -1.5072013
    b = 8.458676
    c = -6.102538

    if (deltah__meter < 15.0):
        deltah_use = 15.0
    else:
        deltah_use = deltah__meter

    return a + math.log10(deltah_use) * (b + c * math.log10(deltah_use))


def MixedPathCorrectionFactor(d__km, interValues):
    """
    Port of an ITS function.

    Description: Find the correction factor for mixed land-sea path
    Reference: Section 4.4 of [Okumura]
    Inputs:
        d__km : Path distance, in kilometers
        interValues.beta : percentage of the path that is sea
        interValues.iend_ov_sea : which end of the pfl is sea
                 1  : low end
                 0  : high end
                -1  : equal amounts on both ends
    Return:
        correction factor
    """

    slope_30 = []
    slope_60 = []

    beta_30 = [ 0.0, 0.15, 0.35, 0.45, 0.6, 0.65, 0.725, 0.775, 0.85,  1.0 ]
    corr_30 = [ [ 0.0, 1.0,  3.0,  4.0,  6.0, 7.0,  8.0,   9.0,  10.0,  11.0 ],
                [ 0.0, 4.0,  5.5,  7.0,  8.5, 9.0,  9.5,   9.8,  10.25, 11.0 ] ]

    beta_60 = [ 0.0, 0.15, 0.3,  0.4,  0.5,  0.6,   0.725,  0.85,  0.9,   1.0 ]
    corr_60 = [ [ 0.0, 2.0,  4.0,  5.5,  7.0,  9.0,  11.0,   13.0,  14.0,  15.0 ],
                [ 0.0, 4.25, 6.25, 9.2, 10.5, 11.75, 13.0,   14.0,  14.25, 15.0 ] ]

    if (interValues.beta == 0.0):
        return 0.0         # no sea path, so correction factor is 0 dB


    ist_30 = 0
    while (interValues.beta > beta_30[ist_30 + 1] and ist_30 < 10): ####
        ist_30 += 1

    if (ist_30 == 10):
        ist_30 -= 1

    ist_60 = 0
    while (interValues.beta > beta_60[ist_60 + 1] and ist_60 < 10): ####
        ist_60 = ist_60 + 1

    if (ist_60 == 10):
        ist_60 -= 1

    for i in range(2): 
        slope_30.append((corr_30[i][ist_30 + 1] - corr_30[i][ist_30]) / \
                        (beta_30[ist_30 + 1] - beta_30[ist_30]))
        slope_60.append((corr_60[i][ist_60 + 1] - corr_60[i][ist_60]) / \
                        (beta_60[ist_60 + 1] - beta_60[ist_60]))

    if (d__km <= 30.0):
        if (interValues.iend_ov_sea == 0 or interValues.iend_ov_sea == 1):
            return corr_30[interValues.iend_ov_sea][ist_30] + \
                   (interValues.beta - beta_30[ist_30])* \
                   slope_30[interValues.iend_ov_sea]
        else:
            return 0.5*(corr_30[0][ist_30] + corr_30[1][ist_30] + \
                        (interValues.beta - beta_30[ist_30])* \
                        (slope_30[0] + slope_30[1]))
    elif (d__km >= 60.0):
        if (interValues.iend_ov_sea == 0 or interValues.iend_ov_sea == 1):
            return corr_60[interValues.iend_ov_sea][ist_60] + \
                   (interValues.beta - beta_60[ist_60])* \
                   slope_60[interValues.iend_ov_sea]
        else:
            return 0.5*(corr_60[0][ist_60] + corr_60[1][ist_60] + \
                        (interValues.beta - beta_60[ist_60])*(slope_60[0] + \
                                                              slope_60[1]))
    else:
        dist_fact = (d__km - 30.0) / 30.0
        if (interValues.iend_ov_sea == 0 or interValues.iend_ov_sea == 1):
            qmp_corr_30 = corr_30[interValues.iend_ov_sea][ist_30] + \
                          (interValues.beta - beta_30[ist_30])* \
                          slope_30[interValues.iend_ov_sea]
            qmp_corr_60 = corr_60[interValues.iend_ov_sea][ist_60] + \
                          (interValues.beta - beta_60[ist_60])* \
                          slope_60[interValues.iend_ov_sea]
        else:
            qmp_corr_30 = 0.5*(corr_30[0][ist_30] + corr_30[1][ist_30] + \
                               (interValues.beta - \
                                beta_30[ist_30])*(slope_30[0] + slope_30[1]))
            qmp_corr_60 = 0.5*(corr_60[0][ist_60] + corr_60[1][ist_60] + \
                               (interValues.beta - \
                                beta_60[ist_60])*(slope_60[0] + slope_60[1]))

        return qmp_corr_30 + dist_fact*(qmp_corr_60 - qmp_corr_30)

 
def PreprocessTerrainPath(pfl, h_b__meter, h_m__meter, interValues):
    """
    Port of a wrapper-type ITS routine. Calls routines below.
    """
    
    FindAverageGroundHeight(pfl, interValues)
    ComputeTerrainStatistics(pfl, interValues)
    MobileTerrainSlope(pfl, interValues)
    AnalyzeSeaPath(pfl, interValues)
    SingleHorizonTest(pfl, h_m__meter, h_b__meter, interValues);


def FindAverageGroundHeight(pfl, interValues):
    """
    Port of ITS routine.

    Description: Find the average ground height at each terminal
    Inputs:
        pfl : Terrain profile line with:
                 - pfl[0] = number of terrain points + 1
                 - pfl[1] = step size, in meters
                 - pfl[i] = elevation above mean sea level, in meters
    Outputs:
        interValues->h_avg__meter : Average ground height of each terminal 
                above sea level, in meters
                 - h_avg__meter[0] = terminal at start of pfl
                 - h_avg__meter[1] = terminal at end of pfl
    """
    
    np = int(pfl[0])
    xi = pfl[1] * 0.001      #// step size of the profile points, in km
    d__km = np * xi          #// path distance, in km

    summ = 0.0;

    if (d__km < 3.0):
        interValues.h_avg__meter[0] = pfl[2]
        interValues.h_avg__meter[1] = pfl[np + 2] ####
    elif (3.0 <= d__km and d__km <= 15.0):
        i_start = 2 + int(3.0 / xi)
        i_end = np + 2
        for i in range(i_start, i_end+1): # (int i = i_start; i <= i_end; i++)
            summ = summ + pfl[i] ####
        interValues.h_avg__meter[0] = pfl[2] - (pfl[2] - summ / (i_end - i_start + 1)) * \
                                      (d__km - 3.0) / 12.0
        
        i_start = 2
        i_end = np + 2 - int(3.0 / xi)
        summ = 0.0
        for i in range(i_start, i_end+1): # (int i = i_start; i <= i_end; i++)
            summ = summ + pfl[i]
        interValues.h_avg__meter[1] = summ / (i_end - i_start + 1) #* \
#                                      (d__km - 3.0) / 12.0
    else: #// d__km > 15.0
        i_start = 2 + int(3.0 / xi)
        i_end = 2 + int(15.0 / xi)
        for i in range(i_start, i_end+1): #(int i = i_start; i <= i_end; i++)
            summ = summ + pfl[i]
        interValues.h_avg__meter[0] = summ / (i_end - i_start + 1)

        i_start = np + 2 - int(15.0 / xi)
        i_end = np + 2 - int(3.0 / xi)
        summ = 0.0
        for i in range(i_start, i_end+1): #(int i = i_start; i <= i_end; i++)
            summ = summ + pfl[i]
        interValues.h_avg__meter[1] = summ / (i_end - i_start + 1)


def ComputeTerrainStatistics(pfl, interValues):
    """
    Port of an ITS function.

    Description: Compute the 10%, 50%, and 90% terrain height quantiles as well as the terrain
                 irregularity parameter, deltaH
    Inputs:
        pfl : Terrain profile line with:
                 - pfl[0] = number of terrain points + 1
                 - pfl[1] = step size, in meters
                 - pfl[i] = elevation above mean sea level, in meters
    Outputs:
        interValues->pfl10__meter : 10% terrain quantile
        interValues->pfl50__meter : 50% terrain quantile
        interValues->pfl90__meter : 90% terrain quantile
        interValues->deltah__meter : terrain irregularity parameter
    """

    np = int(pfl[0])
    xi = pfl[1] * 0.001      #// step size of the profile points, in km
    d__km = np * xi          #// path distance, in km


    # "[deltah] may be found ... equal to the difference between 10% and
    # 90% of the terrain undulation height ... within a distance of 10km
    # from the receiving point to the transmitting point."
    # Okumura, Sec 2.4 (1)(b)
    if (d__km < 10.0): #// ... then use the whole path
        i_start = 2
        i_end = np + 2
    else: #// use 10 km adjacent to the mobile
        i_start = 2
        i_end = 2 + int(10.0 / xi)

    #// create a copy of the 10 km path at the mobile, or the whole path (if less than 10 km)
    #float pfl_segment[400];
    pfl_segment = []
    for i in range(i_start, i_end+1): #(int i = i_start; i <= i_end; i++)
        pfl_segment.append(pfl[i]) ####

    npts = i_end - i_start + 1
    i10 = 0.1 * npts - 1
    i50 = 0.5 * npts - 1
    i90 = 0.9 * npts - 1
    interValues.pfl10__meter = FindQuantile(npts, pfl_segment, i10)
    interValues.pfl50__meter = FindQuantile(npts, pfl_segment, i50)
    interValues.pfl90__meter = FindQuantile(npts, pfl_segment, i90)
    interValues.deltah__meter = interValues.pfl10__meter - \
                                interValues.pfl90__meter

    #// "If the path is less than 10 km in distance, then the asymptotic value
    #//  for the terrain irrgularity is computed" [TR-15-517]
    if (d__km < 10.0):
        factor = (1.0 - 0.8*math.exp(-0.2)) / (1.0 - 0.8*math.exp(-0.02 * d__km))
        interValues.pfl10__meter = interValues.pfl10__meter * factor
        interValues.pfl50__meter = interValues.pfl50__meter * factor
        interValues.pfl90__meter = interValues.pfl90__meter * factor
        interValues.deltah__meter = interValues.deltah__meter * factor

def MobileTerrainSlope(pfl, interValues):
    """
    Port of ITS function.

    Description: Find the slope of the terrain at the mobile
    Inputs:
        pfl : Terrain profile line with:
                 - pfl[0] = number of terrain points + 1
                 - pfl[1] = step size, in meters
                 - pfl[i] = elevation above mean sea level, in meters
    Outputs:
        interValues->slope_max : intermediate value
        interValues->slope_min : intermediate value
        interValues->theta_m__mrad : mobile terrain slope, in millirads
    """

    np = int(pfl[0])        #// number of points
    xi = pfl[1]              #// step size of the profile points, in meter
    d__meter = np * xi

    #// find the mean slope of the terrain in the vicinity of the mobile station
    interValues.slope_max = -1.0e+31
    interValues.slope_min = 1.0e+31
    slope_five = 0.0

#    pfl_segment = []

    x1 = 0.0
    x2 = 5000.0
    while (d__meter >= x2 and x2 <= 10000.0):
        pfl_segment = []
        npts = int(x2 / xi)
        pfl_segment.append(npts)
        pfl_segment.append(xi)
        for i in range (npts+1): # (int i = 0; i < npts + 1; i++) 
            pfl_segment.append(pfl[i + 2]) # Doesn't this just copy pfl?

        z1 = [0]
        z2 = [0]
        LeastSquares(pfl_segment, x1, x2, z1, z2)
        z1 = z1[0]
        z2 = z2[0]
        
        #// flip the sign to match the Okumura et al.convention
        slope = -1000.0 * (z2 - z1) / (x2 - x1)
        interValues.slope_min = min(interValues.slope_min, slope)
        interValues.slope_max = max(interValues.slope_max, slope)
        if (x2 == 5000.0):
            slope_five = slope
        x2 = x2 + 1000.0

    if (d__meter <= 5000.0 or
        interValues.slope_max * interValues.slope_min < 0.0):
        interValues.theta_m__mrad = slope_five
    else:
        if (interValues.slope_max >= 0.0):
            interValues.theta_m__mrad = interValues.slope_max
        else:
            interValues.theta_m__mrad = interValues.slope_min

def AnalyzeSeaPath(pfl, interValues):
    """
    Port of ITS Routine

    Description: Compute the sea details of the path
    Inputs:
        pfl : Terrain profile line with:
                 - pfl[0] = number of terrain points + 1
                 - pfl[1] = step size, in meters
                 - pfl[i] = elevation above mean sea level, in meters
    Outputs:
        interValues->beta : percentage of the path that is sea
        interValues->iend_ov_sea : which end of the pfl is sea
                 1  : low end
                 0  : high end
                -1  : equal amounts on both ends
    """

    np = int(pfl[0])

    #// determine the fraction of the path over sea and which end of the path is adjacent to the sea
    index_midpoint = int(np / 2)

    sea_cnt = 0
    low_cnt = 0
    high_cnt = 0

    for i in range(1, np+2): #(int i = 1; i <= np + 1; i++)
        if (pfl[i + 1] == 0.0):
            sea_cnt = sea_cnt + 1
            if (i <= index_midpoint):
                low_cnt = low_cnt + 1
            else:
                high_cnt = high_cnt + 1

    interValues.beta = float(sea_cnt) / float(np + 1)

    if (low_cnt > high_cnt):
        interValues.iend_ov_sea = 1
    elif (high_cnt > low_cnt):
        interValues.iend_ov_sea = 0
    else:
        interValues.iend_ov_sea = -1

def AverageTerrainHeight(pfl):
    """
    Rewrite of ITS routine.
    """
    return npy.mean(pfl[2:])

def SingleHorizonTest(pfl, h_m__meter, h_b__meter, interValues):
    """
    Port of ITS routine.
    
    Description: Determine the horizon details
    Inputs:
        pfl : Terrain profile line with:
                 - pfl[0] = number of terrain points + 1
                 - pfl[1] = step size, in meters
                 - pfl[i] = elevation above mean sea level, in meters
        h_m__meter : height of the mobile, in meters
        h_b__meter : height of the base station, in meters
    Outputs:
        interValues->d_hzn__meter : horizon distances, in meters
                 - d_hzn__meter[0] = mobile horizon distance, in meters
                 - d_hzn__meter[1] = base station horizon distance, in meters
        interValues->single_horizon : horizon flag
        interValues->hedge_tilda : correction factor
    """
    np = int(pfl[0])           #// number of points
    xi = pfl[1]          #// step size of the profile points, in meter
    d__meter = np * xi

    h_gnd__meter = AverageTerrainHeight(pfl)

    en0 = 301.0
    ens = 0
    if (h_gnd__meter == 0):
        ens = en0
    else:
        ens = en0 * math.exp(-h_gnd__meter / 9460)
    gma = 157e-9
    gme = gma * (1 - 0.04665 * math.exp(ens / 179.3))

    FindHorizons(pfl, gme, d__meter, h_m__meter, h_b__meter,
                 interValues.d_hzn__meter)

    a = interValues.d_hzn__meter[0]
    b = interValues.d_hzn__meter[1]
    d_diff__meter = d__meter - interValues.d_hzn__meter[0] - \
                    interValues.d_hzn__meter[1]
    q = max(d_diff__meter - 0.5*pfl[1], 0) - max(-d_diff__meter - 0.5*pfl[1], 0)
    if (q != 0.0):
        interValues.single_horizon = False
    else:
        interValues.single_horizon = True
        iedge = int(interValues.d_hzn__meter[0] / pfl[1])

        za = h_b__meter + pfl[np + 2]
        zb = h_m__meter + pfl[2]
        interValues.hedge_tilda = pfl[iedge + 2] - \
                                  (za*interValues.d_hzn__meter[1] + \
                                   zb*interValues.d_hzn__meter[0]) / d__meter + \
                                   0.5*gme*interValues.d_hzn__meter[0] * \
                                   interValues.d_hzn__meter[1]


        if (interValues.hedge_tilda < 0.0):
            interValues.hedge_tilda = 0.0

def ExtendedHata(pfl, f__mhz, h_b__meter, h_m__meter, enviro_code, plb):
    """
    Port of ITS routine.

    Description: The Extended-Hata Urban Propagation Model
    Inputs:
        pfl : Terrain profile line with:
                 - pfl[0] = number of terrain points + 1
                 - pfl[1] = step size, in meters
                 - pfl[i] = elevation above mean sea level, in meters
        f__mhz : frequency, in MHz
        h_b__meter : height of the base station, in meters
        h_m__meter : height of the mobile, in meters
        enviro_code : environmental code
    Outputs:
        plb : path loss, in dB
    """
    
    interValues = InterValues() 
    ExtendedHata_DBG(pfl, f__mhz, h_b__meter, h_m__meter, enviro_code,
                     plb, interValues);

def ExtendedHata_DBG(pfl, f__mhz, h_b__meter, h_m__meter, enviro_code,
                     plb, interValues):
    """
    Port of ITS routine
    
    Description: The Extended-Hata Urban Propagation Model
    Inputs:
        pfl : Terrain profile line with:
                 - pfl[0] = number of terrain points + 1
                 - pfl[1] = step size, in meters
                 - pfl[i] = elevation above mean sea level, in meters
        f__mhz : frequency, in MHz
        h_b__meter : height of the base station, in meters
        h_m__meter : height of the mobile, in meters
        enviro_code : environmental code
    Outputs:
        plb : path loss, in dB
        interValues : data structure containing intermediate calculated values
    """
    
    np = int(pfl[0])
    PreprocessTerrainPath(pfl, h_b__meter, h_m__meter, interValues);    
    h_m_gnd__meter = pfl[2];
    interValues.h_m_eff__meter = h_m__meter + pfl[2] - \
                                 interValues.h_avg__meter[0]
    interValues.h_b_eff__meter = h_b__meter + pfl[np + 2] - \
                                 interValues.h_avg__meter[1]

    d1_hzn__km = interValues.d_hzn__meter[1] * 0.001
    d2_hzn__km = interValues.d_hzn__meter[0] * 0.001

    #// Clamp values
    ## WinnForum implementation -- minimum h_b__eff = 20., and
    ## no correction for mobile side.
    if (interValues.h_b_eff__meter <  20.0):
        interValues.h_b_eff__meter =  20.0
    if (interValues.h_b_eff__meter > 200.0):
        interValues.h_b_eff__meter = 200.0
    interValues.h_m_eff__meter = h_m__meter

    # Original clamp values from ITS code
##    if (interValues.h_m_eff__meter <   1.0):
##        interValues.h_m_eff__meter =   1.0
##    if (interValues.h_m_eff__meter >  10.0):
##        interValues.h_m_eff__meter =  10.0
##    if (interValues.h_b_eff__meter <  30.0):
##        interValues.h_b_eff__meter =  30.0
##    if (interValues.h_b_eff__meter > 200.0):
##        interValues.h_b_eff__meter = 200.0

    interValues.d__km = pfl[0] * pfl[1] / 1000
    plb_median__db = [0.] # Mutable for passing to routine
    MedianBasicPropLoss(f__mhz, interValues.h_b_eff__meter,
                        interValues.h_m_eff__meter, interValues.d__km,
                        enviro_code, plb_median__db, interValues)

    #// apply correction factors based on path
    if (interValues.single_horizon):
        plb[0] = plb_median__db[0] - \
                 IsolatedRidgeCorrectionFactor(d1_hzn__km, d2_hzn__km,
                                               interValues.hedge_tilda) \
            - MixedPathCorrectionFactor(interValues.d__km, interValues)

    else: #// two horizons
        plb[0] = plb_median__db[0] - \
                 MedianRollingHillyTerrainCorrectionFactor(interValues.deltah__meter) \
            - FineRollingHillyTerrainCorectionFactor(interValues, h_m_gnd__meter) \
            - GeneralSlopeCorrectionFactor(interValues.theta_m__mrad, interValues.d__km) \
            - MixedPathCorrectionFactor(interValues.d__km, interValues)
