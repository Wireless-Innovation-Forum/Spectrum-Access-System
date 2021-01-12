#include "math.h"
#include "ehata.h"
#include "stdio.h"

/*
*   Description: Find the isolated ridge correction factor
*   Reference: Section 4.2 of [Okumura]
*   Inputs:
*       d1_hzn__km : horizon distance, in kilometers
*       d2_hzn__km : horizon distance, in kilometers
*       h_edge__meter : intermediate value
*   Return:
*       [double] : correction factor
*/
double IsolatedRidgeCorrectionFactor(double d1_hzn__km, double d2_hzn__km, double h_edge__meter)
{
    double d_1__km[3] = { 15.0, 30.0, 60.0 };
    double d_2__km[9] = { 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0 };
    
    // points from Figure 31, Okumura
    double curve_data[3][9] = 
            { {  4.0, -13.0, -17.5, -17.5, -15.0, -12.5, -10.0, -8.0, -6.0 },   // C curve : d1 <= 15 km
              { 12.0,  -8.5, -13.0, -12.0, -10.0,  -8.0,  -6.5, -5.0, -4.0 },   // B curve : d1 <= 30 km
              { 20.0,  -4.0,  -6.5,  -6.0,  -4.5,  -3.5,  -2.5, -2.0, -1.0 } }; // A curve : d1 <= 60 km

    // normalized ridge height factor
    double alpha = sqrt(h_edge__meter / 200.0); // Eq 1, Okumura, alpha = 0.07 * sqrt(h)

    int id1 = 0;
    if (d1_hzn__km >= d_1__km[1])
        id1 = 1;
    int id2 = 0;

    while (id2 < 7 && d2_hzn__km > d_2__km[id2 + 1])
        id2 = id2 + 1;

    //fprintf(stdout, "Isolated ridge:\n");
    //fprintf(stdout, " id1=%d,  id2=%d, alpha=%.2f\n", id1, id2, alpha);
    
    double c1 = curve_data[id1][id2] + (curve_data[id1][id2 + 1] - curve_data[id1][id2]) * (d2_hzn__km - d_2__km[id2]) / (d_2__km[id2 + 1] - d_2__km[id2]);
    double c2 = curve_data[id1 + 1][id2] + (curve_data[id1 + 1][id2 + 1] - curve_data[id1 + 1][id2]) * (d2_hzn__km - d_2__km[id2]) / (d_2__km[id2 + 1] - d_2__km[id2]);
    //fprintf(stdout, " c1=%.2f,  c2=%.2f  c2-c1=%.3f\n", c1, c2, c2-c1);
    //fprintf(stdout, " d1_hzn=%.2f  d2_hzn=%.2f\n", d1_hzn__km, d2_hzn__km);    
    //fprintf(stdout, " d1_hzn-d_1=%.2f,  d_1_delta=%.2f\n", d1_hzn__km - d_1__km[id1], d_1__km[id1 + 1] - d_1__km[id1]);
    //fprintf(stdout, " d2_hzn-d_2=%.2f,  d_2_delta=%.2f\n", d2_hzn__km - d_2__km[id2], d_2__km[id2 + 1] - d_2__km[id2]);    
    //fprintf(stdout, " curve_data[id1]: %.2f   %.2f\n", curve_data[id1][id2], curve_data[id1][id2+1]);
    //fprintf(stdout, " curve_data[id1+1]: %.2f   %.2f\n", curve_data[id1+1][id2], curve_data[id1+1][id2+1]);
    //fprintf(stdout, " Final: %.2f  (c1 interp = %.2f)\n",
    //        alpha * (c1 + (c2 - c1) * (d1_hzn__km - d_1__km[id1]) / (d_1__km[id1 + 1] - d_1__km[id1])),
    //        (c1 + (c2 - c1) * (d1_hzn__km - d_1__km[id1]) / (d_1__km[id1 + 1] - d_1__km[id1])));
    return alpha * (c1 + (c2 - c1) * (d1_hzn__km - d_1__km[id1]) / (d_1__km[id1 + 1] - d_1__km[id1]));
}

double IsolatedRidgeCorrectionFactorCorr(double d1_hzn__km, double d2_hzn__km, double h_edge__meter)
{
    double d_1__km[3] = { 15.0, 30.0, 60.0 };
    double d_2__km[9] = { 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0 };
    
    // points from Figure 31, Okumura
    double curve_data[3][9] = 
            { {  4.0, -13.0, -17.5, -17.5, -15.0, -12.5, -10.0, -8.0, -6.0 },   // C curve : d1 <= 15 km
              { 12.0,  -8.5, -13.0, -12.0, -10.0,  -8.0,  -6.5, -5.0, -4.0 },   // B curve : d1 <= 30 km
              { 20.0,  -4.0,  -6.5,  -6.0,  -4.5,  -3.5,  -2.5, -2.0, -1.0 } }; // A curve : d1 <= 60 km

    // normalized ridge height factor
    double alpha = sqrt(h_edge__meter / 200.0); // Eq 1, Okumura, alpha = 0.07 * sqrt(h)

    int id1 = 0;
    if (d1_hzn__km >= d_1__km[1])
        id1 = 1;
    int id2 = 0;

    while (id2 < 7 && d2_hzn__km > d_2__km[id2 + 1])
        id2 = id2 + 1;

    //fprintf(stdout, "Isolated ridge:\n");
    //fprintf(stdout, " id1=%d,  id2=%d, alpha=%.2f\n", id1, id2, alpha);
    
    double c1 = curve_data[id1][id2] + (curve_data[id1][id2 + 1] - curve_data[id1][id2]) * (d2_hzn__km - d_2__km[id2]) / (d_2__km[id2 + 1] - d_2__km[id2]);
    double c2 = curve_data[id1 + 1][id2] + (curve_data[id1 + 1][id2 + 1] - curve_data[id1 + 1][id2]) * (d2_hzn__km - d_2__km[id2]) / (d_2__km[id2 + 1] - d_2__km[id2]);
    //fprintf(stdout, " c1=%.2f,  c2=%.2f  c2-c1=%.3f\n", c1, c2, c2-c1);
    //fprintf(stdout, " d1_hzn=%.2f  d2_hzn=%.2f\n", d1_hzn__km, d2_hzn__km);    
    //fprintf(stdout, " d1_hzn-d_1=%.2f,  d_1_delta=%.2f\n", d1_hzn__km - d_1__km[id1], d_1__km[id1 + 1] - d_1__km[id1]);
    //fprintf(stdout, " d2_hzn-d_2=%.2f,  d_2_delta=%.2f\n", d2_hzn__km - d_2__km[id2], d_2__km[id2 + 1] - d_2__km[id2]);    
    //fprintf(stdout, " curve_data[id1]: %.2f   %.2f\n", curve_data[id1][id2], curve_data[id1][id2+1]);
    //fprintf(stdout, " curve_data[id1+1]: %.2f   %.2f\n", curve_data[id1+1][id2], curve_data[id1+1][id2+1]);
    //fprintf(stdout, " Final: %.2f  (c1 interp = %.2f)\n",
    //        alpha * (c1 + (c2 - c1) * (d1_hzn__km - d_1__km[id1]) / (d_1__km[id1 + 1] - d_1__km[id1])),
    //        (c1 + (c2 - c1) * (d1_hzn__km - d_1__km[id1]) / (d_1__km[id1 + 1] - d_1__km[id1])));
    double L_iso__db = alpha * (c1 + (c2 - c1) * MAX(0, (d1_hzn__km - d_1__km[id1])) / (d_1__km[id1 + 1] - d_1__km[id1]));
    return MIN(L_iso__db, 0);
}
