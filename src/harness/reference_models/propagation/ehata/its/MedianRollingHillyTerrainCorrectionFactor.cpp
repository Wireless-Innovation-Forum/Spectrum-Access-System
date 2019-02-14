#include "math.h"
#include "ehata.h"

/*
*   Description: Compute the mean rolling hill terrain correction factor
*   Inputs:
*       delta_h__meter : terrain irregularity factor
*   Return:
*       [double] : correction factor
*/
double MedianRollingHillyTerrainCorrectionFactor(double deltah__meter)
{
    double a = -1.5072013;
    double b = 8.458676;
    double c = -6.102538;

    double deltah_use;

    if (deltah__meter < 15.0)
        deltah_use = 15.0;
    else
        deltah_use = deltah__meter;

    return a + log10(deltah_use) * (b + c * log10(deltah_use));
}
