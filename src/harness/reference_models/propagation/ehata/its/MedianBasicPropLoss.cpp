#include "math.h"
#include "ehata.h"

void MedianBasicPropLoss(float f__mhz, float h_b__meter, float h_m__meter, float d__km, int enviro_code, float* plb_med__db, InterValues *interValues)
{
    double perm = 4.0e-7 * PI;
    double eps = 8.854e-12;
    double c = 1.0 / sqrt(eps*perm);

    //	Extend the frequency range to 3, 000 MHz.This is done by computing alpha_1, beta_1, and gamma_1
    //		in Okumura et al.'s median reference attenuation equation in an urban environment.  
    //	Solve the 3 simultanious equations :
    //		- A-4a: 22    dB @ 1500 MHz at 1 km
    //		- A-4b: 23.5  db @ 2000 MHZ at 1 km
    //		- A-4c: 25.85 dB @ 3000 MHz at 1 km
    //	Using algebra to rearrange the equations for alpha_1, beta_1, and gamma_1 yields
    double sr_1km = sqrt(1.0e+6 + pow((200.0 - 3.0), 2));           // reference h_b = 200 m and h_m = 3 m, at 1 km apart
    double htg_hb_ref = 13.82 * log10(200.0);                       // reference h_b = 200
    double htg_hm_ref = 3.2 * pow(log10(11.75 * 3.0), 2) - 4.97;    // reference h_m = 3 m.This is Eq 16 in Hata
    double wn_1500 = 2.0 * PI * 1.5e+9 / c;                         // wavenumber for 1500 MHz

    double gamma_1 = (3.85 / log10(2.0) - 1.5 / log10(4.0 / 3.0)) / log10(1.5);
    double beta_1 = 20 + 1.5 / log10(4.0 / 3.0) - gamma_1 * log10(3.0e+6);
    double alpha_1 = 22 + htg_hb_ref + htg_hm_ref + 20 * log10(2.0 * wn_1500 * sr_1km) - log10(1500.0) * (beta_1 + gamma_1 * log10(1500.0));

    // Repeat the above process but solve for the suburban coefficients using the following values :
    //      - A-4a: 11.5 dB @ 1500 MHz at 1 km
    //      - A-4b: 12.4 db @ 2000 MHZ at 1 km
    //      - A-4c: 14   dB @ 3000 MHz at 1 km
    // Using algebra to rearrange the equations for alpha_1_suburban, beta_1_suburban, and gamma_1_suburban yeilds
    double denom = log10(4.0 / 3.0) * log10(1.5) * log10(2.0);

    double gamma_1_suburban = (2.5 * log10(4.0 / 3.0) - 0.9 * log10(2.0)) / denom;
    double beta_1_suburban = (0.9 * log10(2.0) * log10(4.5e+6) - 2.5 * log10(4.0 / 3.0) * log10(3.0e+6)) / denom;
    double alpha_1_suburban = 11.5 - beta_1_suburban * log10(1.5e+3) - gamma_1_suburban * pow(log10(1.5e+3), 2);

    // Extended the range by fitting to the functional form at 100 km:
    //      alpha_100 + beta_100 * log(f) + gamma_100 * log^2(f)
    // Using the following points:
    //      63.5  dB @ 1500 MHz at 100 km
    //      65.75 dB @ 2000 MHz at 100 km
    //      69.5  dB @ 3000 MHz at 100 km
    // Solving yields:
    double alpha_100 = 120.78129;
    double beta_100 = -52.714929;
    double gamma_100 = 10.919011;

    // coefficients for the power law exponent(wrt distance) (20 <= d <= 100)
    // these come from figure 12 of Okumura et al. (1968) at base effective antenna heights of 24.5 m, 70 m and 200 m.
    // the corresponding values of n / 2 are: 2.5, 3 and 3.22 respectively
    double tau = (0.72 * log10(70.0 / 24.5) - 0.5*log10(200.0 / 24.5)) / log10(70.0 / 24.5) / log10(200.0 / 70.0) / log10(200.0 / 24.5);
    double sigma = 0.72 / log10(200.0 / 24.5) - tau * log10(200.0 * 24.5);
    double rho = 2.5 - log10(24.5) * (sigma + tau * log10(24.5));

    double suburban_factor = alpha_1_suburban + beta_1_suburban * log10(f__mhz) + gamma_1_suburban * pow(log10(f__mhz), 2);
    double rural_factor = 40.94 - 18.33 * log10(f__mhz) + 4.78 * pow(log10(f__mhz), 2);

    //this next step assumes that the height gain corrections are identical
    //above and below the break point

    double wnmh = 2.0e+6*PI*f__mhz / c;

    double term1 = log10(f__mhz) * (beta_1 + gamma_1 * log10(f__mhz));
    interValues->att_1km = alpha_1 + term1 - htg_hb_ref - htg_hm_ref - 20.0*log10(2.0*wnmh*sr_1km);
    interValues->att_100km = alpha_100 + log10(f__mhz)*(beta_100 + gamma_100*log10(f__mhz));

    double term2 = -13.82*log10(h_b__meter);

    //find the "break-point" distance, d_bp, where the attenuation transitions from the Hata distance exponent, n_l,
    //to a larger distance exponent drawn from figure 12 of Okumura et al. (1968), n_h.n.b., d_bp depends on f and hb
    double n_h = 2.0*(rho + log10(h_b__meter)*(sigma + tau*log10(h_b__meter)) - 1.0);
    double n_l = 0.1 * (44.9 - 6.55*log10(h_b__meter)) - 2.0;
    interValues->d_bp__km = pow(10.0, (2.0 * n_h + 0.1 * (interValues->att_1km - interValues->att_100km)) / (n_h - n_l));

    double terma = -3.2 * pow(log10(11.75 * h_m__meter), 2) + 4.97;
    double sr_d = sqrt(1.0e+6 * pow(d__km, 2) + pow(h_b__meter - h_m__meter, 2)); // distance from base station to mobile, along the ray (compute triangle hypoth)

    double plb_urban;

    // d_bp is the break-point distance in the TR, where if the distance is less than the break - point distance,
    //     the original Hata power law exponent and the refitted Hata intercept are used.  Else the model uses
    //     the long distance power law exponent and the 100km basic median attenuation curve fit
    if (d__km <= interValues->d_bp__km)
    {
        plb_urban = alpha_1 + term1 + term2 + terma + (44.9 - 6.55*log10(h_b__meter))*log10(d__km);

        interValues->trace_code = interValues->trace_code | TRACE__METHOD_10;
    }
    else
    {
        plb_urban = interValues->att_100km + htg_hb_ref + term2 + htg_hm_ref + terma - 20*n_h + 10.0*n_h*log10(d__km) + 20.0*log10(2.0*wnmh*sr_d);

        interValues->trace_code = interValues->trace_code | TRACE__METHOD_11;
    }

    if (enviro_code == 23 || enviro_code == 24) 
    {
        *plb_med__db = plb_urban;

        interValues->trace_code = interValues->trace_code | TRACE__METHOD_12;
    } 
    else if (enviro_code == 22) 
    {
        *plb_med__db = plb_urban - suburban_factor;

        interValues->trace_code = interValues->trace_code | TRACE__METHOD_13;
    }
    else 
    {
        *plb_med__db = plb_urban - rural_factor;

        interValues->trace_code = interValues->trace_code | TRACE__METHOD_14;
    }
}
