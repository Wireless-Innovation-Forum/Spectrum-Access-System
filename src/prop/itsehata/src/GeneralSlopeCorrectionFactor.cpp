#include "ehata.h"

/*
*   Description: Find the general slope correction factor
*   Reference: Section 4.3 of [Okumura]
*   Inputs:
*       theta_m__mrad : mobile terrain slope, in millirads
*       d__km : path distance, in kilometers
*   Return:
*       [float] : correction factor
*/
float GeneralSlopeCorrectionFactor(float theta_m__mrad, float d__km)
{
    float emm1 = 0.25;
    float emm2 = 0.8;
    float emp1 = 0.125;
    float emp2 = 0.35;
    float emp3 = 0.6;

    // computing values from the curves on Fig 34 in Okumura
    if (theta_m__mrad <= 0.0)
    {
        if (d__km <= 10.0)
            return theta_m__mrad * emm1;    // the d < 10km line
        else if (d__km >= 30.0)
            return theta_m__mrad * emm2;    // the d > 30km line
        else
            //interpolate between the two lines
            return theta_m__mrad * (emm1 + 0.05 * (emm2 - emm1) * (d__km - 10.0));
    }
    else
    {
        if (d__km <= 10.0)
            return theta_m__mrad * emp1;    // the d < 10km line
        else if (d__km >= 60.0)
            return theta_m__mrad * emp3;    // the d > 60km line
        else if (d__km > 10.0 && d__km <= 30.0)
            // interpolate
            return theta_m__mrad * (emp1 + 0.05 * (d__km - 10.0) * (emp2 - emp1));
        else //if (d__km > 30.0 .and.d__km < 60)
            // interpolate
            return theta_m__mrad * (emp2 + (d__km - 30.0) * (emp3 - emp2) / 30.0);
    }
}