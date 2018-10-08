#include "math.h"
#include "ehata.h"

/*
*   Description: Least squares fit
*   Inputs:
*       pfl_segment : Terrain profile line with:
*                - pfl_segment[0] = number of terrain points + 1
*                - pfl_segment[1] = step size, in meters
*                - pfl_segment[i] = elevation above mean sea level, in meters
*/
void LeastSquares(double *pfl_segment, double x1, double x2, double *z0, double *zn)
{
    double xn = int(pfl_segment[0]);
    double xi = pfl_segment[1];

    double xa = int(MAX(x1 / xi, 0.0));
    double xb = xn - int(MAX(xn - x2 / xi, 0.0));

    if (xb <= xa)
    {
        xa = MAX(xa - 1.0, 0);
        xb = xn - MAX(xn - xb + 1.0, 0);
    }

    int ja = xa;
    int jb = xb;
    int n = jb - ja;
    xa = xb - xa;
    double x = -0.5 * xa;
    xb = xb + x;
    double a = 0.5 * (pfl_segment[ja + 2] + pfl_segment[jb + 2]);
    double b = 0.5 * (pfl_segment[ja + 2] - pfl_segment[jb + 2]) * x;
    for (int i = 2; i <= n; i++)
    {
        ja = ja + 1;
        x = x + 1.;
        a = a + pfl_segment[ja + 2];
        b = b + pfl_segment[ja + 2] * x;
    }

    a = a / xa;
    b = b * 12. / ((xa * xa + 2.) * xa);
    *z0 = a - b * xb;
    *zn = a + b * (xn - xb);
}
