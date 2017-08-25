# The Extended Hata (eHata) Urban Propagation Model

(See https://github.com/NTIA/ehata)

## Description

This source repository contains a C language reference version of the eHata
urban propagation model. 

The model was developed by NTIA and used in NTIA Technical Report
[TR-15-517](https://www.its.bldrdoc.gov/publications/2805.aspx),
"3.5 GHz Exclusion Zone Analyses and Methodology," June 2015
[TR-15-517] for the 3.5 GHz exclusion zone analysis.


### Input Parameters

* **float** pfl[] : A terrain profile line.  EHata uses the ITM-method of formatting
terrain information, in that:
  * **float** pfl[0] : Number of points + 1
  * **float** pfl[1] : Resolution, in meters
  * **float** pfl[i] : Elevation above sea level, in meters
* **float** f__mhz : The frequency, in MHz
* **float** h_m__meter : The height of the mobile, in meters.
* **float** h_b__meter : The height of the base station, in meters.
* **int** enviro_code : The NLCD environment code

### Output Parameters
* **float** plb: The path loss, in dB.
* **InterValues** intervalues : [Optional] A data structure containing intermediate 
values from the eHata calculations.

### Function Signatures
* **void** ExtendedHata(**float** pfl[], **float** f__mhz, **float** h_b__meter,
**float** h_m__meter, **int** enviro_code, **float** *plb)
* **void** ExtendedHata_DBG(**float** pfl[], **float** f__mhz, **float** h_b__meter,
**float** h_m__meter, **int** enviro_code, **float** *plb,
**InterValues** *interValues)

### Dependencies

The eHata reference implementation is only dependent on the math.lib library.

### Intermediate Values
When calling the ExtendedHata_DBG() function, the function will populate the
**InterValues** data structure with intermediate values from the eHata
calculations.  Those values are as follows:

* **float** d_bp__km: The breakpoint distance, in km.
* **float** att_1km: Attenuation at 1 km.
* **float** att_100km: Attenuation at 100 km.
* **float** h_b_eff__meter: Effective height of the base station, in meters.
* **float** h_m_eff__meter: Effective height of the mobile, in meters.
* **float** pfl10__meter: 10% terrain quantile, in meters.
* **float** pfl50__meter: 50% terrain quantile, in meters.
* **float** pfl90__meter: 90% terrain quantile, in meters.
* **float** deltah__meter: Terrain irregularity parameter.
* **float** d__km: Total path distance, in km.
* **float** d_hzn__meter[2]: Horizon distances, in meters.
* **float** h_avg__meter[2]: Average heights, in meters.
* **float** theta_m__mrad: Slope of the terrain at the at the mobile, in millirads
* **float** beta: Percentage of path that is sea.
* **int** iend_ov_sea: Flag specifying which end is over the sea.
* **float** hedge_tilda: Horizon correction factor.
* **bool** single_horizon: Flag for specifying number of horizons.
* **float** slope_max: Intermediate value when calculating the mobile terrain slope.
* **float** slope_min: Intermediate value when calculating the mobile terrain slope.
* **int** trace_code: Trace flag showing program flow.

### Notes on Code Style

* In general, variables follow the naming convention in which a single underscore
denotes a subscript (pseudo-LaTeX format), where a double underscore is followed
by the units, i.e. h_m__meter.
* Variables are named to match their corresponding mathematical variables 
in the underlying technical references, i.e., gamma_1.
* Most values are calculated and stored in the **InterValues** data structure
that is passed between function calls.  In general, only the correction factor
functions return their result as a value.

## References

* [Okumura, 1968] Okumura, Y., Ohmori, E., Kawano, T., Fukuda, K.  "Field Strength 
and Its Variability in VHF and UHF Land-Mobile Radio Service", 
_Review of the Electrical Communication Laboratory_, Vol. 16, Num 9-10. 
Sept-Oct 1968. pp. 825-873.
* [Hata, 1980] Hata, M. "Empirical Formula for Propagation Loss in Land Mobile 
Radio Services", _IEEE Transactions on Vehicular Technology_, Vol VT-29, Num 3.  
Aug 1980.  pp 317-325.  DOI: 10.1109/T-VT.1980.23859
* [TR-15-517](https://www.its.bldrdoc.gov/publications/2805.aspx) Drocella, 
E., Richards, J., Sole, R., Najmy, F., Lundy, A., McKenna, P. "3.5 
GHz Exclusion Zone Analyses and Methodology", _NTIA Report 15-517_, June 2015.

## Configuring and Building

This project was developed and built using Microsoft Visual Studio
2015, using the Visual Studio 2015 (v140) C compiler.  By default, the
project file is configured to build with Runtime Library set to 
Multi-threaded (/MT), thus removing the requirement that the target machine
have the matching version of the Microsoft C Redistributable installed.

## Test and Validation

This code repository contains a representative set of test cases to validate
the compiled software against.  The /test/ folder contains:

* test-inputs.csv : A csv file containing inputs, locations, and expected
path loss.  It also contains the name of the corresponding pfl file
* /pfls/ : A directory containing pfls for the test cases

The pfls were generated using the re-sampled terrain data that can be
downloaded from here: [https://www.its.bldrdoc.gov/resources/radio-propagation-software/resampled-terrain-data/re-sampled-terrain-data.aspx](https://www.its.bldrdoc.gov/resources/radio-propagation-software/resampled-terrain-data/re-sampled-terrain-data.aspx)

## Legal
[Please read the LICENSE file]

