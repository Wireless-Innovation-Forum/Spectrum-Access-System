#include "stdio.h"
#include "cmath"
#include "ehata.h"

// ******* WinnForum extension *******

// Activation of the WinnForum modifications
bool _WinnForum_Extensions = true; // on by default
void SetWinnForumExtensions(bool on)
{
  _WinnForum_Extensions = on;
}

// Definition of the profile distance calculation routine - see ehata.h
double GetDistanceInMeters(double pfl[])
{
  double distance_m = pfl[0] * pfl[1];
  if (fabs(distance_m - round(distance_m)) < 1e-5)
    distance_m = round(distance_m);
  return distance_m;
}

// Debug print routine
void printInterValues(InterValues *interValues)
{
  fprintf(stdout, "IV: %.8f %.8f %.8f # %.8f %.8f # %.8f %.8f %.8f %.8f #\n"
          "    %.8f # %.8f %.8f # %.8f %.8f # %.8f %.8f %d %.8f %d %.8f %.8f\n",
                   interValues->d_bp__km ,
                   interValues->att_1km ,
                   interValues->att_100km ,
                   interValues->h_b_eff__meter ,
                   interValues->h_m_eff__meter ,
                   interValues->pfl10__meter ,
                   interValues->pfl50__meter ,
                   interValues->pfl90__meter ,
                   interValues->deltah__meter ,
                   interValues->d__km ,
                   interValues->d_hzn__meter[0],
                   interValues->d_hzn__meter[1],
                   interValues->h_avg__meter[0],
                   interValues->h_avg__meter[1],
                   interValues->theta_m__mrad ,
                   interValues->beta ,
                   interValues->iend_ov_sea,
                   interValues->hedge_tilda,
                   interValues->single_horizon,
                   interValues->slope_max ,
                   interValues->slope_min);

}
// ******* End WinnForum extension *******


/*
*   Description: The Extended-Hata Urban Propagation Model
*   Inputs:
*       pfl : Terrain profile line with:
*                - pfl[0] = number of terrain points + 1
*                - pfl[1] = step size, in meters
*                - pfl[i] = elevation above mean sea level, in meters
*       f__mhz : frequency, in MHz
*       h_b__meter : height of the base station, in meters
*       h_m__meter : height of the mobile, in meters
*       enviro_code : environmental code
*   Outputs:
*       plb : path loss, in dB
*/
void ExtendedHata(double pfl[], double f__mhz, double h_b__meter, double h_m__meter,
    int enviro_code, double *plb)
{
    InterValues interValues;
    ExtendedHata_DBG(pfl, f__mhz, h_b__meter, h_m__meter, enviro_code, plb, &interValues);
}

/*
*   Description: The Extended-Hata Urban Propagation Model
*   Inputs:
*       pfl : Terrain profile line with:
*                - pfl[0] = number of terrain points + 1
*                - pfl[1] = step size, in meters
*                - pfl[i] = elevation above mean sea level, in meters
*       f__mhz : frequency, in MHz
*       h_b__meter : height of the base station, in meters
*       h_m__meter : height of the mobile, in meters
*       enviro_code : environmental code
*   Outputs:
*       plb : path loss, in dB
*       interValues : data structure containing intermediate calculated values
*/
void ExtendedHata_DBG(double pfl[], double f__mhz, double h_b__meter, double h_m__meter,
    int enviro_code, double *plb, InterValues *interValues)
{
    int np = int(pfl[0]);

    PreprocessTerrainPath(pfl, h_b__meter, h_m__meter, interValues);

    double h_m_gnd__meter, d1_hzn__km, d2_hzn__km;

    h_m_gnd__meter = pfl[2];
    interValues->h_m_eff__meter = h_m__meter + pfl[2] - interValues->h_avg__meter[0];
    interValues->h_b_eff__meter = h_b__meter + pfl[np + 2] - interValues->h_avg__meter[1];
    d1_hzn__km = interValues->d_hzn__meter[1] * 0.001;
    d2_hzn__km = interValues->d_hzn__meter[0] * 0.001;

    // ******* WinnForum extension *******
    // Clamp values
    if (_WinnForum_Extensions) {
        if (interValues->h_b_eff__meter <  20.0) interValues->h_b_eff__meter =  20.0;
        if (interValues->h_b_eff__meter > 200.0) interValues->h_b_eff__meter = 200.0;
        interValues->h_m_eff__meter = h_m__meter;

    } else {
        if (interValues->h_m_eff__meter <   1.0) interValues->h_m_eff__meter =   1.0;
        if (interValues->h_m_eff__meter >  10.0) interValues->h_m_eff__meter =  10.0;
        if (interValues->h_b_eff__meter <  30.0) interValues->h_b_eff__meter =  30.0;
        if (interValues->h_b_eff__meter > 200.0) interValues->h_b_eff__meter = 200.0;
    }
    // ******* End WinnForum extension *******
    // ******* WinnForum change *******
    //interValues->d__km = pfl[0] * pfl[1] / 1000;
    interValues->d__km = GetDistanceInMeters(pfl) / 1000.;

    // ******* End WinnForum change *******

    double plb_median__db;
    MedianBasicPropLoss(f__mhz, interValues->h_b_eff__meter, interValues->h_m_eff__meter, interValues->d__km, enviro_code, &plb_median__db, interValues);

    // apply correction factors based on path
    if (interValues->single_horizon)
    {
        *plb = plb_median__db - IsolatedRidgeCorrectionFactor(d1_hzn__km, d2_hzn__km, interValues->hedge_tilda)
            - MixedPathCorrectionFactor(interValues->d__km, interValues);

        interValues->trace_code = interValues->trace_code | TRACE__METHOD_17;
    }
    else // two horizons
    {
        interValues->trace_code = interValues->trace_code | TRACE__METHOD_18;
        *plb = plb_median__db - MedianRollingHillyTerrainCorrectionFactor(interValues->deltah__meter)
            - FineRollingHillyTerrainCorectionFactor(interValues, h_m_gnd__meter)
            - GeneralSlopeCorrectionFactor(interValues->theta_m__mrad, interValues->d__km)
            - MixedPathCorrectionFactor(interValues->d__km, interValues);
    }
}
