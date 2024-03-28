#include "math.h"
#include "ehata.h"

/*
*   Description: Find the isolated ridge correction factor
*   Reference: Section 4.2 of [Okumura]
*   Inputs:
*       d1_hzn__km : horizon distance, in kilometers
*       d2_hzn__km : horizon distance, in kilometers
*       h_edge__meter : intermediate value
*       do_v2_corr: apply correction v3.2. See https://github.com/NTIA/ehata/pull/13
*   Return:
*       [double] : correction factor
*/
double IsolatedRidgeCorrectionFactor(double d1_hzn__km, double d2_hzn__km,
                                     double h_edge__meter)
{
    double d_1__km[3] = { 15.0, 30.0, 60.0 };
    double d_2__km[9] = { 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0 };
    
    // points from Figure 31, Okumura, at corresponding d2 distances
    double curve_data[3][9] = 
            { {  4.0, -13.0, -17.5, -17.5, -15.0, -12.5, -10.0, -8.0, -6.0 },   // C curve : d1 <= 15 km
              { 12.0,  -8.5, -13.0, -12.0, -10.0,  -8.0,  -6.5, -5.0, -4.0 },   // B curve : d1 <= 30 km
              { 20.0,  -4.0,  -6.5,  -6.0,  -4.5,  -3.5,  -2.5, -2.0, -1.0 } }; // A curve : d1 <= 60 km

    // Eq 1, Okumura, alpha = 0.07 * sqrt(h)
    //   Note: 0.07 is approx sqrt (1/ 200), with 200 being the normalization height    
    double alpha = sqrt(h_edge__meter / 200.0);

    int id1 = 0;
    if (d1_hzn__km >= d_1__km[1])
        id1 = 1;

    // select the first d2 curve distance that is <= to actual path d2 distance
    int id2 = 0;
    while (id2 < 7 && d2_hzn__km > d_2__km[id2 + 1])
        id2 = id2 + 1;

    // c1 is value on "lower" curve in Figure 31, Okumura, relative to d1 - either curve B or C
    // c2 is value on "upper" curve in Figure 31, Okumura, relative to d1 - either curve A or B
    double c1 = curve_data[id1][id2] + (curve_data[id1][id2 + 1] - curve_data[id1][id2]) * (d2_hzn__km - d_2__km[id2]) / (d_2__km[id2 + 1] - d_2__km[id2]);
    double c2 = curve_data[id1 + 1][id2] + (curve_data[id1 + 1][id2 + 1] - curve_data[id1 + 1][id2]) * (d2_hzn__km - d_2__km[id2]) / (d_2__km[id2 + 1] - d_2__km[id2]);

    if (!_do_isolated_ridge_v2_corr) {
        return alpha * (c1 + (c2 - c1) * (d1_hzn__km - d_1__km[id1]) / (d_1__km[id1 + 1] - d_1__km[id1]));
    } else {
        // compute isolated ridge correction factor, K_im, from Figure 31, Okumura
        double K_im;
        if (d1_hzn__km <= 15)       // clamp to curve C
            K_im = c1;
        else if (d1_hzn__km >= 60)  // clamp to curve A
            K_im = c2;
        else                        // interpolate between curves
            K_im = (c1 + (c2 - c1) * (d1_hzn__km - d_1__km[id1]) / (d_1__km[id1 + 1] - d_1__km[id1]));

        // clamp K_im asymptote value to 0 dB (to avoid causing a non-physical gain from occuring)
        // allow the gain to occur for portion of the curve with d2 distances close to or equal to 0 km
        if (d2_hzn__km > 2)
            K_im = MIN(K_im, 0);

        // apply conversion factor to account for ridge height, Figure 32, Okumura
        double L_iso__db = alpha * K_im;
        return L_iso__db;      
    }
}
