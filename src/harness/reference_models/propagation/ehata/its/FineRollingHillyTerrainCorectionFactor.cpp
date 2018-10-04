#include "math.h"
#include "ehata.h"

/*
*   Description: Find the fine rolling hill terrain correction factor
*   Inputs:
*       interValues->pfl10__meter : 10% terrain quantile
*       interValues->pfl50__meter : 50% terrain quantile
*       interValues->pfl90__meter : 90% terrain quantile
*       interValues->deltah__meter : terrain irregularity parameter
*       h_m_gnd__meter : mobile ground height, in meters
*   Return:
*       [float] : correction factor
*/
float FineRollingHillyTerrainCorectionFactor(InterValues *interValues, float h_m_gnd__meter)
{
    float a = -11.728795;
    float b = 15.544272;
    float c = -1.8154766;

    float deltah_use;
    float K_h;

    // deltaH must be at least 10 meters
    if (interValues->deltah__meter < 10.0)
        return 0;
    else
        deltah_use = interValues->deltah__meter;
        
    K_h = a + log10(deltah_use) * (b + c * log10(deltah_use));

    if (h_m_gnd__meter >= interValues->pfl10__meter)
        return K_h;
    else if (h_m_gnd__meter <= interValues->pfl90__meter)
        return -K_h;
    else if (h_m_gnd__meter < interValues->pfl10__meter && h_m_gnd__meter >= interValues->pfl50__meter)
        return K_h * (h_m_gnd__meter - interValues->pfl50__meter) / (interValues->pfl10__meter - interValues->pfl50__meter);
    else
        return -K_h * (interValues->pfl50__meter - h_m_gnd__meter) / (interValues->pfl50__meter - interValues->pfl90__meter);
}
