#include "ehata.h"

/*
*   Description: Find the correction factor for mixed land-sea path
*   Reference: Section 4.4 of [Okumura]
*   Inputs:
*       d__km : Path distance, in kilometers
*       interValues->beta : percentage of the path that is sea
*       interValues->iend_ov_sea : which end of the pfl is sea
*                1  : low end
*                0  : high end
*               -1  : equal amounts on both ends
*   Outputs:
*       interValues->trace_code : debug trace flag to document code
*               execution path for tracing and testing purposes
*   Return:
*       [double] : correction factor
*/
double MixedPathCorrectionFactor(double d__km, InterValues *interValues)
{
    double slope_30[2];
    double slope_60[2];

    double beta_30[10]    =   { 0.0, 0.15, 0.35, 0.45, 0.6, 0.65, 0.725, 0.775, 0.85,  1.0 };
    double corr_30[2][10] = { { 0.0, 1.0,  3.0,  4.0,  6.0, 7.0,  8.0,   9.0,  10.0,  11.0 },
                             { 0.0, 4.0,  5.5,  7.0,  8.5, 9.0,  9.5,   9.8,  10.25, 11.0 } };

    double beta_60[10]    =   { 0.0, 0.15, 0.3,  0.4,  0.5,  0.6,   0.725,  0.85,  0.9,   1.0 };
    double corr_60[2][10] = { { 0.0, 2.0,  4.0,  5.5,  7.0,  9.0,  11.0,   13.0,  14.0,  15.0 },
                             { 0.0, 4.25, 6.25, 9.2, 10.5, 11.75, 13.0,   14.0,  14.25, 15.0 } };

    if (interValues->beta == 0.0)
    {
        interValues->trace_code = interValues->trace_code | TRACE__METHOD_15;
        return 0.0;         // no sea path, so correction factor is 0 dB
    }

    interValues->trace_code = interValues->trace_code | TRACE__METHOD_16;

    int ist_30 = 0;
    while (interValues->beta > beta_30[ist_30 + 1] && ist_30 < 10)
        ist_30++;

    if (ist_30 == 10)
        ist_30--;

    int ist_60 = 0;
    while (interValues->beta > beta_60[ist_60 + 1] && ist_60 < 10)
        ist_60 = ist_60 + 1;

    if (ist_60 == 10)
        ist_60--;

    for (int i = 0; i < 2; i++)
    {
        slope_30[i] = (corr_30[i][ist_30 + 1] - corr_30[i][ist_30]) / (beta_30[ist_30 + 1] - beta_30[ist_30]);
        slope_60[i] = (corr_60[i][ist_60 + 1] - corr_60[i][ist_60]) / (beta_60[ist_60 + 1] - beta_60[ist_60]);
    }

    if (d__km <= 30.0)
    {
        if (interValues->iend_ov_sea == 0 || interValues->iend_ov_sea == 1)
            return corr_30[interValues->iend_ov_sea][ist_30] + (interValues->beta - beta_30[ist_30])*slope_30[interValues->iend_ov_sea];
        else
            return 0.5*(corr_30[0][ist_30] + corr_30[1][ist_30] + (interValues->beta - beta_30[ist_30])*(slope_30[0] + slope_30[1]));
    }
    else if (d__km >= 60.0)
    {
        if (interValues->iend_ov_sea == 0 || interValues->iend_ov_sea == 1)
            return corr_60[interValues->iend_ov_sea][ist_60] + (interValues->beta - beta_60[ist_60])*slope_60[interValues->iend_ov_sea];
        else
            return 0.5*(corr_60[0][ist_60] + corr_60[1][ist_60] + (interValues->beta - beta_60[ist_60])*(slope_60[0] + slope_60[1]));
    }
    else
    {
        double dist_fact = (d__km - 30.0) / 30.0;
        double qmp_corr_30;
        double qmp_corr_60;

        if (interValues->iend_ov_sea == 0 || interValues->iend_ov_sea == 1)
        {
            qmp_corr_30 = corr_30[interValues->iend_ov_sea][ist_30] + (interValues->beta - beta_30[ist_30])*slope_30[interValues->iend_ov_sea];
            qmp_corr_60 = corr_60[interValues->iend_ov_sea][ist_60] + (interValues->beta - beta_60[ist_60])*slope_60[interValues->iend_ov_sea];
        }
        else
        {
            qmp_corr_30 = 0.5*(corr_30[0][ist_30] + corr_30[1][ist_30] + (interValues->beta - beta_30[ist_30])*(slope_30[0] + slope_30[1]));
            qmp_corr_60 = 0.5*(corr_60[0][ist_60] + corr_60[1][ist_60] + (interValues->beta - beta_60[ist_60])*(slope_60[0] + slope_60[1]));
        }

        return qmp_corr_30 + dist_fact*(qmp_corr_60 - qmp_corr_30);
    }
}
