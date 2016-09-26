// Copyright 2016 SAS Project Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

double ITMDLLVersion();

// 'pol' values
#define POL_HORIZONTAL 0
#define POL_VERTICAL 1

// 'TSiteCriteria' and 'RSiteCritera' values
#define SITE_CRITERIA_RANDOM 0
#define SITE_CRITERIA_CAREFUL 1
#define SITE_CRITERIA_VERY_CAREFUL 2

// 'radio_climate' values
#define RADIO_CLIMATE_EQUATORIAL 1
#define RADIO_CLIMATE_CONTINTAL_SUBTROPICAL 2
#define RADIO_CLIMATE_MARITIME_TROPICAL 3
#define RADIO_CLIMATE_DESERT 4
#define RADIO_CLIMATE_CONTINENTAL_TEMPERATE 5
#define RADIO_CLIMATE_MARITIME_TEMPERATE_OVER_LAND 6
#define RADIO_CLIMATE_MARITIME_TEMPERATE_OVER_SEA 7

// 'ModVar' values
#define MODVAR_SINGLE 0
#define MODVAR_INDIVIDUAL 1
#define MODVAR_MOBILE 2
#define MODVAR_BROADCAST 3

// 'errnum' return settings
// Note that if another non-zero error code is returned, parameters are out of
// range and results are probably invalid.
#define ERR_NO_ERROR 0
#define ERR_WARNING_NEARLY_OUT_OF_RANGE 1
#define ERR_NOTE_IMPOSSIBLE_PARAMS 2
#define ERR_WARNING_COMBINATION_OUT_OF_RANGE 3

// 'propmode' return settings
#define PROPMODE_UNDEFINED = -1
#define PROPMODE_LINE_OF_SIGHT = 0
#define PROPMODE_SINGLE_HORIZON_DIFFRACTION 5
#define PROPMODE_SINGLE_HORIZON_TROPOSCATTER 6
#define PROPMODE_DOUBLE_HORIZON_DIFFRACTION 9
#define PROPMODE_DOUBLE_HORIZON_TROPOSCATTER 10

// 'strmode' return settings
#define STRMODE_LINE_OF_SIGHT "Line-Of-Sight Mode"
#define STRMODE_SINGLE_HORIZON_DIFFRACTION "Single Horizon, Diffraction Dominant"
#define STRMODE_SINGLE_HORIZON_TROPOSCATTER "Single Horizon, Troposcatter Dominant"
#define STRMODE_DOUBLE_HORIZON_DIFFRACTION "Double Horizon, Diffraction Dominant"
#define STRMODE_DOUBLE_HORIZON_TROPOSCATTER "Double Horizon, Troposcatter Dominant"

// Parameter documentation:
// elev : an array of terrain elevation values in meters. The format is that the
//        first array value is the total size of the elevations passed minus 1, the
//        second is the distance between the values in meters, and then come the
//        actual elevation values. So passing four values separated by 100m
//        would look like: [ 3, 100, 1, 2, 3, 4]
// tht_m : transmitter height in meters
// rht_m : receiver height in meters
// eps_dielect : the dielectric constant (relative permittivity) of the ground.
//               Typical values are 15 for ground, 81 for water.
// sgm_conductivity : conductivity of the soil/ground.
//                    Typical values are 0.005 for gruond, 0.01 for fresh water,
//                    5 for sea water.
// eno_ns_surfref : refractivity of the atmosphere.
//                  Should be between 250 and 400. (Reasonable default value is 314.)
// frq_mhz : the emission frequency in megahertz
// radio_climate : the radio climate. one of the RADIO_CLIMATE_* values above
// pol : emission polarization. one of the POL_* values above
// conf : Confidence. A value between 0.01 and 0.99.
//        This value indicates a fraction of situations that the actual loss will
//        not exceed the model loss in similar situations.
// rel : Reliability. A value between 0.01 and 0.99
//       This value indicates a fraction of the time that the actual loss will not exceed
//       the model loss for a particular radio system.

// ModVar : ???. One of the MODVAR_* values above
// deltaH : interdecile range of elevations in the path
// dist_km : path length distance in kilometers
// TSiteCriteria : site criteria for transmitter. One of the SITE_CRITERIA_* values above.
// RSiteCriteria : site criteria for receiver. One of teh SITE_CRITERIA_* values above.

// Return parameter documentation:
// dbloss : the estimated loss in dB
// strmode : the dominant loss mode. One of the STRMODE_* values above.
// errnum : error indicator. One of the ERR_* values above.
// propmode : dominant loss mode indicator. One of the PROPMODE_* values above.
// deltaH : the interdecile range of elevations in the path



void point_to_point(double elev[], double tht_m, double rht_m,
                    double eps_dielect, double sgm_conductivity, double eno_ns_surfref,
                    double frq_mhz, int radio_climate, int pol,
                    double conf, double rel,
                    double &dbloss, char *strmode, int &errnum);

void point_to_pointMDH(double elev[], double tht_m, double rht_m,
                       double eps_dielect, double sgm_conductivity, double eno_ns_surfref,
                       double frq_mhz, int radio_climate, int pol,
                       double timepct, double locpct, double confpct,
                       double &dbloss, int &propmode, double &deltaH, int &errnum);

void point_to_pointDH(double elev[], double tht_m, double rht_m,
                      double eps_dielect, double sgm_conductivity, double eno_ns_surfref,
                      double frq_mhz, int radio_climate, int pol,
                      double conf, double rel,
                      double &dbloss, double &deltaH, int &errnum);

double ITMAreadBLoss(long ModVar, double deltaH, double tht_m, double rht_m,
                     double dist_km, int TSiteCriteria, int RSiteCriteria,
                     double eps_dielect, double sgm_conductivity, double eno_ns_surfref,
                     double frq_mhz, int radio_climate, int pol,
                     double pctTime, double pctLoc, double pctConf);

