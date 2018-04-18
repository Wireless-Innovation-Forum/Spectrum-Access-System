#ifndef PROPAGATION_EHATA_ITS_EHATA_H
#define PROPAGATION_EHATA_ITS_EHATA_H

#ifdef _WIN32
// Export the DLL functions as "C" and not C++
#define DLLEXPORT extern "C" __declspec(dllexport)
#else
#define DLLEXPORT
#endif

#define MAX(x, y) (((x) > (y)) ? (x) : (y))
#define MIN(x, y) (((x) < (y)) ? (x) : (y))

// ******* WinnForum extension *******
// Change all inputs and intermediate value from float to double
// The reason for that are:
// - to make the interface more in line with the ITM model
// - to suppress all mismatch between different implementations:
//   By using float, every implementation will lead to slightly different
//   results depending on the compiler and manual code optimisation done.
//
//   Because the propagation model is strongly non linear, this typically
//   leads to variation which can exceed a fraction of a dB or more.
//   By using double, this issue is strongly alleviated (with the appropriate
//   compiler flag to force exactness of double calculation, for example the
//   -fno-unsafe-math-optimizations in gcc or the /fp:precise (default) in
//   Microsoft compiler).
//
// Note: Hacky but works perfect if ehata.h last #include in the C++ files.
#define float double

// Activate the Winnforum extensions
extern bool _WinnForum_Extensions; // default is ON
void SetWinnForumExtensions(bool on);

// Function to get the distance in meters from a profile:
//  the `pfl` profile store the number of points and the step between
//  points. The total profile distance is given by N*step, but can lead to a
//  very small loss of precision because of floating point issues. This can
//  create mismatch depending on compilers, given that the eHata model has
//  specific logic based on threshold on specific integer values (10km, etc..).
//  One solution is to reset the distance used in calculation to proper integer
//  values when detected as very close to an integer value.
//  This function does exactly that.
float GetDistanceInMeters(float pfl[]);

// ******* End WinnForum extension *******

struct InterValues
{
    float d_bp__km;
    float att_1km;
    float att_100km;

    float h_b_eff__meter;
    float h_m_eff__meter;

    // Terrain Stats
    float pfl10__meter;
    float pfl50__meter;
    float pfl90__meter;
    float deltah__meter;

    // Path Geometry
    float d__km;
    float d_hzn__meter[2];
    float h_avg__meter[2];
    float theta_m__mrad;
    float beta;
    int iend_ov_sea;
    float hedge_tilda;
    bool single_horizon;

    // Misc
    float slope_max;
    float slope_min;

    int trace_code;
};

#define PI 3.14159265358979323846

// public
DLLEXPORT void ExtendedHata(float pfl[], float f__mhz, float h_b__meter, float h_m__meter, int environment, float *plb);
DLLEXPORT void ExtendedHata_DBG(float pfl[], float f__mhz, float h_b__meter, float h_m__meter, int environment, float *plb, InterValues *interValues);

// private
void FindAverageGroundHeight(float *pfl, InterValues *interValues);
void MobileTerrainSlope(float *pfl, InterValues *interValues);
void LeastSquares(float *pfl_segment, float x1, float x2, float *z0, float *zn);
void AnalyzeSeaPath(float* pfl, InterValues *interValues);
void FindHorizons(float *pfl, float gme, float d__meter, float h_1__meter, float h_2__meter, float *d_hzn__meter);
void SingleHorizonTest(float *pfl, float h_m__meter, float h_b__meter, InterValues *interValues);
void ComputeTerrainStatistics(float *pfl, InterValues *interValues);
float FindQuantile(const int &nn, float *apfl, const int &ir);
void PreprocessTerrainPath(float *pfl, float h_b__meter, float h_m__meter, InterValues *interValues);
float AverageTerrainHeight(float *pfl);
float GeneralSlopeCorrectionFactor(float theta_m__mrad, float d__km);
float FineRollingHillyTerrainCorectionFactor(InterValues *interValues, float h_m_gnd__meter);
float MixedPathCorrectionFactor(float d__km, InterValues *interValues);
float MedianRollingHillyTerrainCorrectionFactor(float deltah);
void MedianBasicPropLoss(float f__mhz, float h_b__meter, float h_m__meter, float d__km, int environment, float* plb_med__db, InterValues *interValues);
float IsolatedRidgeCorrectionFactor(float d1_hzn__km, float d2_hzn__km, float h_edge__meter);

// Trace Constants
#define TRACE__METHOD_00    0x00000001;
#define TRACE__METHOD_01    0x00000002;
#define TRACE__METHOD_02    0x00000004;
#define TRACE__METHOD_03    0x00000008;
#define TRACE__METHOD_04    0x00000010;
#define TRACE__METHOD_05    0x00000020;
#define TRACE__METHOD_06    0x00000040;
#define TRACE__METHOD_07    0x00000080;
#define TRACE__METHOD_08    0x00000100;
#define TRACE__METHOD_09    0x00000200;
#define TRACE__METHOD_10    0x00000400;
#define TRACE__METHOD_11    0x00000800;
#define TRACE__METHOD_12    0x00001000;
#define TRACE__METHOD_13    0x00002000;
#define TRACE__METHOD_14    0x00004000;
#define TRACE__METHOD_15    0x00008000;
#define TRACE__METHOD_16    0x00010000;
#define TRACE__METHOD_17    0x00020000;
#define TRACE__METHOD_18    0x00040000;
#define TRACE__METHOD_19    0x00080000;


#endif // PROPAGATION_EHATA_ITS_EHATA_H
