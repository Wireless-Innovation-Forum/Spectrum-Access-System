#include "ehata.h"

float FindQuantile(const int &nn, float *a, const int &ir)
{
    float q, r;
    int m, n, i, j, j1, i0, k;
    bool done = false;
    bool goto10 = true;

    m = 0;
    n = nn;
    k = MIN(MAX(0, ir), n);
    while (!done)
    {
        if (goto10)
        {
            q = a[k];
            i0 = m;
            j1 = n;
        }
        i = i0;

        while (i <= n && a[i] >= q)
            i++;
        if (i>n)
            i = n;
        j = j1;

        while (j >= m && a[j] <= q)
            j--;
        if (j<m)
            j = m;
        if (i<j)
        {
            r = a[i]; a[i] = a[j]; a[j] = r;
            i0 = i + 1;
            j1 = j - 1;
            goto10 = false;
        }
        else if (i<k)
        {
            a[k] = a[i];
            a[i] = q;
            m = i + 1;
            goto10 = true;
        }
        else if (j>k)
        {
            a[k] = a[j];
            a[j] = q;
            n = j - 1;
            goto10 = true;
        }
        else
            done = true;
    }
    return q;
}
