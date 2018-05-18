#include "math.h"
#include "ehata.h"
#include "stdio.h"
#define DEBUG_FRH
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
    //printf("Frh h: %.15f\n",h_m_gnd__meter);
    // deltaH must be at least 10 meters
    if (interValues->deltah__meter < 10.0)
        deltah_use = 10.0;
    else
        deltah_use = interValues->deltah__meter;
        
    K_h = a + log10(deltah_use) * (b + c * log10(deltah_use));
#ifdef DEBUG_FRH
    printf("Frh h: %.15f,%.15f,%.15f,%.15f,%.15f,%.15f\n",h_m_gnd__meter,interValues->pfl10__meter,interValues->pfl50__meter,interValues->pfl90__meter,deltah_use,K_h);
#endif

    if (h_m_gnd__meter >= interValues->pfl10__meter){
        #ifdef DEBUG_FRH
        printf("Frh h1: %.15f\n",K_h);
        #endif
        return K_h;
    }
    else if (h_m_gnd__meter <= interValues->pfl90__meter){
        #ifdef DEBUG_FRH
        printf("Frh h2: %.15f\n",-K_h);
        #endif
        return -K_h;
    }
    else if (h_m_gnd__meter < interValues->pfl10__meter && h_m_gnd__meter >= interValues->pfl50__meter){
        #ifdef DEBUG_FRH
        printf("Frh h3: %.15f\n",K_h * (h_m_gnd__meter - interValues->pfl50__meter) / (interValues->pfl10__meter - interValues->pfl50__meter));
        #endif
        return K_h * (h_m_gnd__meter - interValues->pfl50__meter) / (interValues->pfl10__meter - interValues->pfl50__meter);
    }
    else{
        #ifdef DEBUG_FRH
        printf("Frh h4: %.15f\n", -K_h * (interValues->pfl50__meter - h_m_gnd__meter) / (interValues->pfl50__meter - interValues->pfl90__meter));
        #endif
        //return -K_h * (h_m_gnd__meter - interValues->pfl90__meter) / (interValues->pfl50__meter - interValues->pfl90__meter);
        return -K_h * (interValues->pfl50__meter - h_m_gnd__meter) / (interValues->pfl50__meter - interValues->pfl90__meter);
    }
}
