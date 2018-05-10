#include "stdio.h" // TODO
#include "math.h"
#include "ehata.h"


void PreprocessTerrainPath(float *pfl, float h_b__meter, float h_m__meter, InterValues *interValues)
{
    FindAverageGroundHeight(pfl, interValues);

    ComputeTerrainStatistics(pfl, interValues);

    MobileTerrainSlope(pfl, interValues);

    AnalyzeSeaPath(pfl, interValues);

    SingleHorizonTest(pfl, h_m__meter, h_b__meter, interValues);
}

/*
*   Description: Find the average ground height at each terminal
*   Inputs:
*       pfl : Terrain profile line with:
*                - pfl[0] = number of terrain points + 1
*                - pfl[1] = step size, in meters
*                - pfl[i] = elevation above mean sea level, in meters
*   Outputs:
*       interValues->h_avg__meter : Average ground height of each terminal 
*               above sea level, in meters
*                - h_avg__meter[0] = terminal at start of pfl
*                - h_avg__meter[1] = terminal at end of pfl
*       interValues->trace_code : Debug trace flag to document code
*               execution path for tracing and testing purposes
*/
void FindAverageGroundHeight(float *pfl, InterValues *interValues)
{
    int np = int(pfl[0]);
    // ******* WinnForum change *******
    // Old code:
    //float xi = pfl[1] * 0.001;      // step size of the profile points, in km
    // New code:
    float xi = pfl[1] / 1000.;      // step size of the profile points, in km
    // ******* End WinnForum change *******
    float d__km = np * xi;

    int i_start, i_end;
    float sum = 0.0;

    if (d__km < 3.0)
    {
        interValues->h_avg__meter[0] = pfl[2];
        interValues->h_avg__meter[1] = pfl[np + 2];

        interValues->trace_code = interValues->trace_code | TRACE__METHOD_00;
    }
    else if (3.0 <= d__km && d__km <= 15.0)
    {
        // ******* WinnForum extension *******
        if (_WinnForum_Extensions) {
          i_start = 2 + int(ceil(3.0 / xi));
          i_end = np + 2;
          //if ( i_start > i_end ) i_start = i_end;
          for (int i = i_start; i <= i_end; i++)
            sum = sum + pfl[i];
          interValues->h_avg__meter[0] = pfl[2] - (pfl[2] - sum / (i_end - i_start + 1))
              * (d__km - 3.0) / 12.0;

          i_start = 2;
          i_end = np + 2 - int(ceil(3.0 / xi));
          sum = 0.0;
          #if ( i_start > i_end ) i_start = i_end;
          for (int i = i_start; i <= i_end; i++)
            sum = sum + pfl[i];
          interValues->h_avg__meter[1] = pfl[np+2] - (pfl[np+2] - sum / (i_end - i_start + 1))
              * (d__km - 3.0) / 12.0;

        } else {
          // Original ITS formula has an issue: it scales everything down
          i_start = 2 + int(3.0 / xi);
          i_end = np + 2;
          for (int i = i_start; i <= i_end; i++)
            sum = sum + pfl[i];
          interValues->h_avg__meter[0] = sum / (i_end - i_start + 1) * (d__km - 3.0) / 12.0;

          i_start = 2;
          i_end = np + 2 - int(3.0 / xi);
          sum = 0.0;
          for (int i = i_start; i <= i_end; i++)
            sum = sum + pfl[i];
          interValues->h_avg__meter[1] = sum / (i_end - i_start + 1) * (d__km - 3.0) / 12.0;
        }
        // ******* End WinnForum extension *******
        interValues->trace_code = interValues->trace_code | TRACE__METHOD_01;
    }
    else // d__km > 15.0
    {
        // ******* WinnForum extension *******
        if (_WinnForum_Extensions) {
          i_start = 2 + int(ceil(3.0 / xi));
        } else {
          i_start = 2 + int(3.0 / xi);
        }
        // ******* End WinnForum extension *******
        i_end = 2 + int(15.0 / xi);
        for (int i = i_start; i <= i_end; i++)
            sum = sum + pfl[i];
        interValues->h_avg__meter[0] = sum / (i_end - i_start + 1);

        i_start = np + 2 - int(15.0 / xi);
        // ******* WinnForum extension *******
        if (_WinnForum_Extensions) {
          i_end = np + 2 - int(ceil(3.0 / xi));
        } else {
          i_end = np + 2 - int(3.0 / xi);
        }
        // ******* End WinnForum extension *******
        sum = 0.0;
        for (int i = i_start; i <= i_end; i++)
            sum = sum + pfl[i];
        interValues->h_avg__meter[1] = sum / (i_end - i_start + 1);

        interValues->trace_code = interValues->trace_code | TRACE__METHOD_02;
    }
}

/*
*   Description: Compute the 10%, 50%, and 90% terrain height quantiles as well as the terrain
*                irregularity parameter, deltaH
*   Inputs:
*       pfl : Terrain profile line with:
*                - pfl[0] = number of terrain points + 1
*                - pfl[1] = step size, in meters
*                - pfl[i] = elevation above mean sea level, in meters
*   Outputs:
*       interValues->pfl10__meter : 10% terrain quantile
*       interValues->pfl50__meter : 50% terrain quantile
*       interValues->pfl90__meter : 90% terrain quantile
*       interValues->deltah__meter : terrain irregularity parameter
*       interValues->trace_code : debug trace flag to document code
*               execution path for tracing and testing purposes
*/
void ComputeTerrainStatistics(float *pfl, InterValues *interValues)
{
    int np = int(pfl[0]);
    // ******* WinnForum change *******
    // Old code:
    //float xi = pfl[1] * 0.001;      // step size of the profile points, in km
    //float d__km = np * xi;          // path distance, in km
    // New code:
    float xi = pfl[1] / 1000.;      // step size of the profile points, in km    
    float d__km = GetDistanceInMeters(pfl) / 1000.;
    // ******* End WinnForum change *******

    int i_start, i_end;

    // "[deltah] may be found ... equal to the difference between 10% and 90% of the terrain
    // undulation height ... within a distance of 10km from the receiving point to the
    // transmitting point." Okumura, Sec 2.4 (1)(b)
    if (d__km < 10.0) // ... then use the whole path
    {
        i_start = 2;
        i_end = np + 2;

        interValues->trace_code = interValues->trace_code | TRACE__METHOD_03;
    }
    else // use 10 km adjacent to the mobile
    {
        i_start = 2;
        i_end = 2 + int(10.0 / xi);

        interValues->trace_code = interValues->trace_code | TRACE__METHOD_04;
    }

    // create a copy of the 10 km path at the mobile, or the whole path (if less than 10 km)
    // ******* WinnForum change *******
    // The following code may crash the application if using a step <= 25m
    // Old code:
    //float pfl_segment[400];
    // New code:
    float *pfl_segment = new float[i_end - i_start + 2];
    // ******* End WinnForum change *******
    
    for (int i = i_start; i <= i_end; i++)
        pfl_segment[i - i_start] = pfl[i];

    int npts = i_end - i_start + 1;
    int i10 = 0.1 * npts - 1;
    int i50 = 0.5 * npts - 1;
    int i90 = 0.9 * npts - 1;
    interValues->pfl10__meter = FindQuantile(npts, pfl_segment, i10);
    interValues->pfl50__meter = FindQuantile(npts, pfl_segment, i50);
    interValues->pfl90__meter = FindQuantile(npts, pfl_segment, i90);
    interValues->deltah__meter = interValues->pfl10__meter - interValues->pfl90__meter;
    
    // "If the path is less than 10 km in distance, then the asymptotic value
    //  for the terrain irrgularity is computed" [TR-15-517]
    if (d__km < 10.0)
    {
        float factor = (1.0 - 0.8*exp(-0.2)) / (1.0 - 0.8*exp(-0.02 * d__km));
        interValues->pfl10__meter = interValues->pfl10__meter * factor;
        interValues->pfl50__meter = interValues->pfl50__meter * factor;
        interValues->pfl90__meter = interValues->pfl90__meter * factor;
        interValues->deltah__meter = interValues->deltah__meter * factor;
    }
    // ******* WinnForum change *******
    delete[] pfl_segment;
    // ******* End winnForum change *******    
}

/*
*   Description: Find the slope of the terrain at the mobile
*   Inputs:
*       pfl : Terrain profile line with:
*                - pfl[0] = number of terrain points + 1
*                - pfl[1] = step size, in meters
*                - pfl[i] = elevation above mean sea level, in meters
*   Outputs:
*       interValues->slope_max : intermediate value
*       interValues->slope_min : intermediate value
*       interValues->theta_m__mrad : mobile terrain slope, in millirads
*       interValues->trace_code : debug trace flag to document code
*               execution path for tracing and testing purposes
*/
void MobileTerrainSlope(float *pfl, InterValues *interValues)
{
    // ******* WinnForum change *******
    // Old code:
    //int np = int(pfl[0]);           // number of points
    //float xi = pfl[1];              // step size of the profile points, in meter
    //float d__meter = np * xi;
    // New code:
    float xi = pfl[1];              // step size of the profile points, in meter
    float d__meter = GetDistanceInMeters(pfl);
    // ******* End WinnForum change *******

    // find the mean slope of the terrain in the vicinity of the mobile station
    interValues->slope_max = -1.0e+31;
    interValues->slope_min = 1.0e+31;
    float slope_five = 0.0;
    float slope;
    
    float x1, x2;
    // ******* WinnForum change *******
    // The following code may crash the application if using a step <= 25m
    // Old code:
    //float pfl_segment[400] = { 0 };
    // New code:
    float *pfl_segment = new float[int(10000/xi) + 4]();
    // ******* End WinnForum change *******

    x1 = 0.0;
    x2 = 5000.0;
    while (d__meter >= x2 && x2 <= 10000.0)
    {
        int npts = x2 / xi;
        pfl_segment[0] = npts;
        pfl_segment[1] = xi;
        for (int i = 0; i < npts + 1; i++) 
            pfl_segment[i + 2] = pfl[i + 2];

        float z1 = 0, z2 = 0;
        LeastSquares(pfl_segment, x1, x2, &z1, &z2);

        // flip the sign to match the Okumura et al.convention
        slope = -1000.0 * (z2 - z1) / (x2 - x1);
        interValues->slope_min = MIN(interValues->slope_min, slope);
        interValues->slope_max = MAX(interValues->slope_max, slope);
        if (x2 == 5000.0)
            slope_five = slope;
        x2 = x2 + 1000.0;
    }

    if (d__meter <= 5000.0 || interValues->slope_max * interValues->slope_min < 0.0)
    {
        interValues->theta_m__mrad = slope_five;

        interValues->trace_code = interValues->trace_code | TRACE__METHOD_05;
    }
    else
    {
        if (interValues->slope_max >= 0.0)
        {
            interValues->theta_m__mrad = interValues->slope_max;

            interValues->trace_code = interValues->trace_code | TRACE__METHOD_06;
        }
        else
        {
            interValues->theta_m__mrad = interValues->slope_min;

            interValues->trace_code = interValues->trace_code | TRACE__METHOD_07;
        }
    }
    // ******* WinnForum change *******
    delete[] pfl_segment;
    // ******* End winnForum change *******    
}

/*
*   Description: Compute the sea details of the path
*   Inputs:
*       pfl : Terrain profile line with:
*                - pfl[0] = number of terrain points + 1
*                - pfl[1] = step size, in meters
*                - pfl[i] = elevation above mean sea level, in meters
*   Outputs:
*       interValues->beta : percentage of the path that is sea
*       interValues->iend_ov_sea : which end of the pfl is sea
*                1  : low end
*                0  : high end
*               -1  : equal amounts on both ends
*/
void AnalyzeSeaPath(float* pfl, InterValues *interValues)
{
    int np = int(pfl[0]);

    // determine the fraction of the path over sea and which end of the path is adjacent to the sea
    int index_midpoint = np / 2;

    int sea_cnt = 0;
    int low_cnt = 0;
    int high_cnt = 0;

    for (int i = 1; i <= np + 1; i++)
    {
        if (pfl[i + 1] == 0.0)
        {
            sea_cnt = sea_cnt + 1;
            if (i <= index_midpoint)
                low_cnt = low_cnt + 1;
            else
                high_cnt = high_cnt + 1;
        }
    }

    interValues->beta = float(sea_cnt) / float(np + 1);

    if (low_cnt > high_cnt)
        interValues->iend_ov_sea = 1;
    else if (high_cnt > low_cnt)
        interValues->iend_ov_sea = 0;
    else
        interValues->iend_ov_sea = -1;
}

/*
*   Description: Compute the average height of the terrain pfl
*   Inputs:
*       pfl : Terrain profile line with:
*                - pfl[0] = number of terrain points + 1
*                - pfl[1] = step size, in meters
*                - pfl[i] = elevation above mean sea level, in meters
*   Return:
*       [float] : average terrain height, in meters
*/
float AverageTerrainHeight(float *pfl)
{
    float h_gnd__meter = 0.0;
    int np = (int)pfl[0];

    for (int i = 1; i <= np + 1; i++)
        h_gnd__meter = h_gnd__meter + pfl[i + 1];
    h_gnd__meter = h_gnd__meter / (np + 1);

    return h_gnd__meter;
}

/*
*   Description: Determine the horizon details
*   Inputs:
*       pfl : Terrain profile line with:
*                - pfl[0] = number of terrain points + 1
*                - pfl[1] = step size, in meters
*                - pfl[i] = elevation above mean sea level, in meters
*       h_m__meter : height of the mobile, in meters
*       h_b__meter : height of the base station, in meters
*   Outputs:
*       interValues->d_hzn__meter : horizon distances, in meters
*                - d_hzn__meter[0] = mobile horizon distance, in meters
*                - d_hzn__meter[1] = base station horizon distance, in meters
*       interValues->single_horizon : horizon flag
*       interValues->hedge_tilda : correction factor
*       interValues->trace_code : debug trace flag to document code
*               execution path for tracing and testing purposes
*/
void SingleHorizonTest(float *pfl, float h_m__meter, float h_b__meter, InterValues *interValues)
{
    int np = int(pfl[0]);           // number of points
    // ******* WinnForum change *******
    // Old code:
    //float xi = pfl[1];              // step size of the profile points, in meter
    //float d__meter = np * xi;
    // New code:
    float d__meter = GetDistanceInMeters(pfl);
    // ******* End WinnForum change *******

    float h_gnd__meter = AverageTerrainHeight(pfl);

    float en0 = 301.0f;
    float ens = 0;
    if (h_gnd__meter == 0)
        ens = en0;
    else
        ens = en0 * exp(-h_gnd__meter / 9460);
    float gma = 157e-9f;
    float gme = gma * (1 - 0.04665 * exp(ens / 179.3));

    FindHorizons(pfl, gme, d__meter, h_m__meter, h_b__meter, interValues->d_hzn__meter);

    //float a = interValues->d_hzn__meter[0];
    //float b = interValues->d_hzn__meter[1];
    float d_diff__meter = d__meter - interValues->d_hzn__meter[0] - interValues->d_hzn__meter[1];
    float q = MAX(d_diff__meter - 0.5*pfl[1], 0) - MAX(-d_diff__meter - 0.5*pfl[1], 0);
    if (q != 0.0)
    {
        interValues->single_horizon = false;
        interValues->trace_code = interValues->trace_code | TRACE__METHOD_08;
    }
    else
    {
        interValues->single_horizon = true;
        int iedge = interValues->d_hzn__meter[0] / pfl[1];

        float za, zb;
        za = h_b__meter + pfl[np + 2];
        zb = h_m__meter + pfl[2];
        interValues->hedge_tilda = pfl[iedge + 2] - (za*interValues->d_hzn__meter[1] + zb*interValues->d_hzn__meter[0]) / d__meter + 0.5*gme*interValues->d_hzn__meter[0] * interValues->d_hzn__meter[1];

        interValues->trace_code = interValues->trace_code | TRACE__METHOD_09;

        if (interValues->hedge_tilda < 0.0)
            interValues->hedge_tilda = 0.0;
    }
}
