#include "ehata.h"
#include "math.h"

/*
*   Description: Compute the mean rolling hill terrain correction factor
*   Inputs:
*       delta_h__meter : terrain irregularity factor
*   Return:
*       [float] : correction factor
*/
float MedianRollingHillyTerrainCorrectionFactor(float deltah__meter)
{
    float a = -1.5072013;
    float b = 8.458676;
    float c = -6.102538;

    float deltah_use;

    if (deltah__meter < 15.0)
        deltah_use = 15.0;
    else
        deltah_use = deltah__meter;

    return a + log10(deltah_use) * (b + c * log10(deltah_use));
}