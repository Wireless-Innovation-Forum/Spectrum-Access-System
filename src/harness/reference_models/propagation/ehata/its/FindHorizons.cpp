#include "ehata.h"

void FindHorizons(float *pfl, float gme, float d__meter, float h_1__meter,
    float h_2__meter, float *d_hzn__meter)
{
    float theta[2];

    bool wq;

    int np = pfl[0];
    float xi = pfl[1];
    float za = pfl[2] + h_1__meter;
    float zb = pfl[np + 2] + h_2__meter;
    float qc = 0.5 * gme;
    float q = qc * d__meter;
    theta[1] = (zb - za) / d__meter;
    theta[0] = theta[1] - q;
    theta[1] = -theta[1] - q;
    d_hzn__meter[0] = d__meter;
    d_hzn__meter[1] = d__meter;

    if (np < 2)
        return;

    float sa = 0;
    float sb = d__meter;
    wq = true;
    for (int i = 2; i <= np; i++)
    {
        sa = sa + xi;
        sb = sb - xi;
        q = pfl[i + 1] - (qc * sa + theta[0])*sa - za;
        if (q > 0)
        {
            theta[0] = theta[0] + q / sa;
            d_hzn__meter[0] = sa;
            wq = false;
        }
        if (!wq)
        {
            q = pfl[i + 1] - (qc*sb + theta[1])*sb - zb;
            if (q > 0)
            {
                theta[1] = theta[1] + q / sb;
                d_hzn__meter[1] = sb;
            }
        }
    }
}