#include "math.h"
#include "ehata.h"

/*
*   Description: Find the isolated ridge correction factor
*   Reference: Section 4.2 of [Okumura]
*   Inputs:
*       d1_hzn__km : horizon distance, in kilometers
*       d2_hzn__km : horizon distance, in kilometers
*       h_edge__meter : intermediate value
*   Return:
*       [float] : correction factor
*/
float IsolatedRidgeCorrectionFactor(float d1_hzn__km, float d2_hzn__km, float h_edge__meter)
{
    float d_1__km[3] = { 15.0, 30.0, 60.0 };
    float d_2__km[9] = { 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0 };
    
    // points from Figure 31, Okumura
    float curve_data[3][9] = 
            { {  4.0, -13.0, -17.5, -17.5, -15.0, -12.5, -10.0, -8.0, -6.0 },   // C curve : d1 <= 15 km
              { 12.0,  -8.5, -13.0, -12.0, -10.0,  -8.0,  -6.5, -5.0, -4.0 },   // B curve : d1 <= 30 km
              { 20.0,  -4.0,  -6.5,  -6.0,  -4.5,  -3.5,  -2.5, -2.0, -1.0 } }; // A curve : d1 <= 60 km

    // normalized ridge height factor
    float alpha = sqrt(h_edge__meter / 200.0); // Eq 1, Okumura, alpha = 0.07 * sqrt(h)

    int id1 = 0;
    if (d1_hzn__km >= d_1__km[1])
        id1 = 1;
    int id2 = 0;

    while (id2 < 7 && d2_hzn__km > d_2__km[id2 + 1])
        id2 = id2 + 1;

    float c1 = curve_data[id1][id2] + (curve_data[id1][id2 + 1] - curve_data[id1][id2]) * (d2_hzn__km - d_2__km[id2]) / (d_2__km[id2 + 1] - d_2__km[id2]);
    float c2 = curve_data[id1 + 1][id2] + (curve_data[id1 + 1][id2 + 1] - curve_data[id1 + 1][id2]) * (d2_hzn__km - d_2__km[id2]) / (d_2__km[id2 + 1] - d_2__km[id2]);

    return alpha * (c1 + (c2 - c1) * (d1_hzn__km - d_1__km[id1]) / (d_1__km[id1 + 1] - d_1__km[id1]));
}
