# A Python port of the C++ port of the NTIA ITS ITM FORTRAN code.
#
# Original FORTRAN code documentation is at:
# http://www.its.bldrdoc.gov/media/50674/itm.pdf
#
# Section numbers referenced here correspond to the FORTRAN code document.
#
# Andrew Clegg
# October 2016
# Last update: Nov 5, 2016

import math

# Static function variables in C++ implemented via global variables in Python
global wd1, xd1, afo, qk, aht, xht                        # Function adiff
global ad, rr, etq, h0s                                   # Function ascat
global wls                                                # Function alos
global wlos, wscat, dmin, xae                             # Function lrprop
global kdv                                                # Function avar
global dexa, de, vmd, vs0, sgl, sgtm, sgtp, sgtd, tgtd    # Function avar
global gm, gp, cv1, cv2, yv1, yv2, yv3, csm1, csm2, ysm1  # Function avar
global ysm2, ysm3, csp1, csp2, ysp1, ysp2, ysp3, csd1, zd # Function avar
global cfm1, cfm2, cfm3, cfp1, cfp2, cfp3                 # Function avar
global ws, w1                                             # Function avar

# Initialize the static function variables
wd1 = xd1 = afo = qk = aht = xht = 0.
ad = rr = etq = h0s = 0.
wls = 0.
wlos = wscat = False
dmin = xae = 0.
kdv = 0
dexa = de = vmd = vs0 = sgl = sgtm = sgtp = sgtd = tgtd = 0.0
gm = gp = cv1 = cv2 = yv1 = yv2 = yv3 = csm1 = csm2 = ysm1 = 0.0
ysm2 = ysm3 = csp1 = csp2 = ysp1 = ysp2 = ysp3 = csd1 = zd = 0.0
cfm1 = cfm2 = cfm3 = cfp1 = cfp2 = cfp3 = 0.0
ws = w1 = False


class PropType:

    # <Primary parameters 2> (Section 2)

    def __init__(self):
        self.aref = 0.0         # Reference attenuation
        self.dist = 0.0         # Distance
        self.hg = [0.0, 0.0]    # Antenna structural heights, m
        self.wn = 0.0           # Wave number (inverse length), 1/m
        self.dh = 0.0           # Terrain irregularity parameter, m
        self.ens = 0.0          # Surface refractivity, N-units
        self.gme = 0.0          # Earth's effective curvature (inverse length), 1/m
        self.zgndreal = 0.0     # Surface transfer impedance (real part)
        self.zgndimag = 0.0     # Surface transfer impedance (imag part)
        self.he = [0.0, 0.0]    # Antenna effective heights, m
        self.dl = [0.0, 0.0]    # Horizon distances, m
        self.the = [0.0, 0.0]   # Horizon elevation angles
        self.kwx = 0            # Error indicator
        self.mdp = 0            # Controlling mode


class PropvType:

    # <Variability parameters 27> (Section 27)

    def __init__(self):
        self.sgc = 0.0          # Std dev of situation variability (confidence)
        self.lvar = 0           # Control switch
        self.mdvar = 0          # Mode of variability
        self.klim = 0           # Climate indicator


class PropaType:

    # <Secondary parameters 3> (Section 3)
    
    def __init__(self):
        self.dlsa = 0.0         # Line-of-sight distance
        self.dx = 0.0           # Scatter distance
        self.ael = 0.0          # Line-of-sight coefficient
        self.ak1 = 0.0          # Line-of-sight coefficient
        self.ak2 = 0.0          # Line-of-sight coefficient
        self.aed = 0.0          # Diffraction coefficient
        self.emd = 0.0          # Diffraction coefficient
        self.aes = 0.0          # Scatter coefficient
        self.ems = 0.0          # Scatter coefficient
        self.dls = [0.0, 0.0]   # Smooth earth horizon distance
        self.dla = 0.0          # Total horizon distance
        self.tha = 0.0          # Total bending angle


# Integer and double functions 'mymin' replaced by Python's min() function
# Integer and double functions 'mymax' replaced by Python's max() function


def fortran_dim(x, y):
    """
    This performs the FORTRAN DIM function.
    result is x-y if x is greater than y otherwise result is 0.0
    """

    if (x > y):
        return x-y
    else:
        return 0.0


def aknfe(v2):
    """
    The attenuation due to a single knife edge--the Fresnel integral (in dB)
    as a function of v**2. The approximation is that given in [Alg 6.1].

    (Section 13)
    """
    
    if(v2 < 5.76):
        return 6.02 + 9.11*(v2)**0.5 - 1.27*v2
    else:
        return 12.953 + 4.343*math.log(v2)


def fht(x, pk):
    """
    The height-gain over a smooth spherical earth--to be used in the "three-radii"
    method. The approximation is that given in [Alg 6.4].

    (Section 14)
    """
    
    if (x < 200.0):
        w = -math.log(pk)
        if (pk < 1.e-5) or (x * w**3.0 > 5495.0):
            fhtv = -117.0
            if (x > 1.0):
                fhtv = 17.372*math.log(x) + fhtv
        else:
            fhtv = 2.5e-5*x*x/pk - 8.686*w - 15.0
    else:
        fhtv = 0.05751*x - 4.343*math.log(x)
        if(x < 2000.0):
            w = 0.0134*x*math.exp(-0.005*x)
            fhtv = (1.0 - w) * fhtv + w*(17.372*math.log(x) - 117.0)

    return fhtv


def h0f(r, et):
    """
    This is the H01 function for scatter fields as defined in [Alg Section 6].

    (Section 25)
    """

    a = [25.0, 80.0, 177.0, 395.0, 705.0]
    b = [24.0, 45.0,  68.0,  80.0, 105.0]

    it = int(et)

    if it <= 0:
        it = 1
        q = 0.0
    elif it >= 5:
        it = 5
        q = 0.0
    else:
        q = et - it

    x = (1.0/r)**2.0
    h0fv = 4.343*math.log((a[it-1]*x + b[it-1])*x + 1.0)
    
    if q <> 0.0:
        h0fv = (1.0 - q)*h0fv + q*4.343*math.log((a[it]*x + b[it])*x + 1.0)

    return h0fv


def ahd(td):
    """
    This is the F(theta*d) function for scatter fields.

    (Section 26)
    """

    a = [   133.4,    104.6,     71.8]
    b = [0.332e-3, 0.212e-3, 0.157e-3]
    c = [  -4.343,   -1.086,    2.171]

    if td <= 10.e3:
        i=0
    elif td <= 70.e3:
        i=1
    else:
        i=2

    return a[i] + b[i]*td + c[i]*math.log(td)


def adiff(d, prop, propa):
    """
    The function adiff finds the "diffraction attenuation" at the distance d. It
    uses a convex combination of smooth earth diffraction and double knife-
    edge diffraction. A call with d = 0 sets up initial constants.

    (Section 10)
    """

#   To implement C++ static function variables.
#   Function must first be called with d = 0 to initialize these variables.
    global wd1, xd1, afo, qk, aht, xht
    
    prop_zgnd = prop.zgndreal + prop.zgndimag * 1j

    if d == 0:

        q  = prop.hg[0]*prop.hg[1]
        qk = prop.he[0]*prop.he[1] - q
	
        if prop.mdp < 0.0:
            q  += 10.0

        wd1 = (1.0 + qk/q)**0.5
        xd1 = propa.dla + propa.tha/prop.gme
        q   = (1.0 - 0.8*math.exp(-propa.dlsa/50e3))*prop.dh
        q  *= 0.78*math.exp(- (q/16.)**0.25)
        afo = min(15.0, \
                  2.171*math.log(1.0 + 4.77e-4*prop.hg[0]*prop.hg[1]*prop.wn*q))
        qk  = 1.0/abs(prop_zgnd)
        aht = 20.0
        xht = 0.0

        for j in range(2):
            a = (0.5*prop.dl[j]**2.0)/prop.he[j]
            wa = (a*prop.wn)**(1./3.)
            pk = qk/wa
            q = (1.607 - pk)*151.0*wa*prop.dl[j]/a
            xht += q
            aht += fht(q,pk)
        adiffv = 0.0

    else:

        th = propa.tha + d*prop.gme
        ds = d - propa.dla
        q = 0.0795775*prop.wn*ds*(th**2.0)
        adiffv =   aknfe(q*prop.dl[0]/(ds+prop.dl[0])) \
                 + aknfe(q*prop.dl[1]/(ds+prop.dl[1]))
        a = ds/th
        wa = (a*prop.wn)**(1./3.)
        pk = qk/wa
        q = (1.607 - pk)*151.0*wa*th+xht
        ar = 0.05751*q - 4.343*math.log(q) - aht
        q = (wd1 + xd1/d) \
            *min(((1.0 - 0.8*math.exp(-d/50e3))*prop.dh*prop.wn),6283.2)
        wd = 25.1/(25.1 + q**0.5)
        adiffv = ar*wd+(1.0 - wd)*adiffv + afo
    
    return adiffv


def ascat(d, prop, propa):
    """
    The function ascat finds the "scatter attenuation" at the distance d. It uses
    an approximation to the methods of NBS Tech Note 101 with checks for inadmissable
    situations. For proper operation, the larger distance (d = d_6) must be the
    first called. A call with d = 0 sets up initial constants.

    (Section 22)
    """
    
#   To implement C++ static function variables.
#   Function must first be called with d = 0 to initialize.
    global ad, rr, etq, h0s

    prop_zgnd = prop.zgndreal + prop.zgndimag*1j

    if d == 0.0:
        
        ad = prop.dl[0] - prop.dl[1]
        rr = prop.he[1]/prop.he[0]

        if ad < 0.0:
            ad = -ad
            rr = 1.0/rr

        etq = (5.67e-6*prop.ens - 2.32e-3)*prop.ens + 0.031
        h0s = -15.0
        ascatv = 0.0

    else:

        if h0s > 15.0:
            h0 = h0s
        else:
            th = prop.the[0] + prop.the[1] + d*prop.gme
            r2 = 2.0*prop.wn*th
            r1 = r2*prop.he[0]
            r2 *= prop.he[1]

            if r1 < 0.2 and r2 < 0.2:
                # Early return
                return 1001.0

            ss = (d - ad)/(d + ad)
            q = rr/ss
            ss = max(0.1, ss)
            q = min(max(0.1, q), 10.0)
            z0 = (d - ad)*(d + ad)*th*0.25/d
            et=(etq*math.exp(-pow(min(1.7,z0/8.0e3),6.0))+1.0)*z0/1.7556e3
            ett = max(et, 1.0)
            h0 = (h0f(r1, ett) + h0f(r2, ett))*0.5
            h0 += min(h0, (1.38 - math.log(ett))*math.log(ss)*math.log(q)*0.49)
            h0 = fortran_dim(h0, 0.0)

            if et < 1.0:
                h0 =   et*h0+(1.0-et)*4.343* \
                     math.log(pow((1.0+1.4142/r1)*(1.0+1.4142/r2),2.0)*(r1+r2)/(r1+r2+2.8284))

            if h0 > 15.0 and h0s >= 0.0:
                h0 = h0s

        h0s = h0
        th = propa.tha+d*prop.gme
        ascatv =  ahd(th*d)+4.343*math.log(47.7*prop.wn*pow(th,4.0)) - 0.1 \
                * (prop.ens-301.0)*math.exp(-th*d/40e3) + h0

    return ascatv


def qerfi(q):
    """
    The invese of qerf -- the solution for x to q = Q(x). The approximation is due
    to C. Hastings, Jr. ("Approximations for digital computers," Princeton Univ.
    Press, 1955) and the maximum error should be 4.5e-4.

    (Section 51)
    """

    c0  = 2.515516698
    c1  = 0.802853
    c2  = 0.010328
    d1  = 1.432788
    d2  = 0.189269
    d3  = 0.001308

    x = 0.5 - q
    t = max(0.5 - abs(x), 0.000001)
    t = (-2.0 * math.log(t))**0.5
    v = t - ((c2 * t + c1) * t + c0) / (((d3 * t + d2) * t + d1) * t + 1.0)
    if (x < 0.0):
        v = -v

    return v


def qlrps(fmhz, zsys, en0, ipol, eps, sgm, prop):
    """
    This routine converts the frequency fmhz, the surface refractivity reduced to
    sea level en0, and general system elevation zsys, and the polarization and ground
    constants eps, sgm, to wave number un, surface refractivity ens, effective earth
    curvature gme, and surface impedance zgnd. It may be used with either the area
    prediction or the point-to-point mode.

    (Section 41)
    """
    
    gma = 157e-9
    prop.wn = fmhz/47.7
    prop.ens = en0

    if zsys <> 0.0:
        prop.ens *= math.exp(-zsys/9460.0)

    prop.gme = gma*(1.0 - 0.04665*math.exp(prop.ens/179.3))

    prop_zgnd = prop.zgndreal + prop.zgndimag*1j
    zq = eps + 376.62*sgm/prop.wn *1j
    prop_zgnd = (zq-1.0)**0.5

    if  ipol <> 0.0:
        prop_zgnd = prop_zgnd/zq

    prop.zgndreal = prop_zgnd.real
    prop.zgndimag = prop_zgnd.imag


def abq_alos(r):
    return r.real*r.real + r.imag*r.imag


def alos(d, prop, propa):
    """
    The function alos finds the "line-of-sight" attenuation at the distance d. It
    uses a convex combination of plane earth fields and diffracted fields. A call
    with d = 0 sets up initial constants.

    (Section 17)
    """

#   To implement C++ static function variables.
#   Function must first be called with d = 0 to initialize.
    global wls

    prop_zgnd = prop.zgndreal + prop.zgndimag*1j

    if d == 0.0:
        wls = 0.021/(0.021+prop.wn*prop.dh/max(10e3,propa.dlsa))
        alosv = 0.0
    else:
        q = (1.0-0.8*math.exp(-d/50.e3))*prop.dh
        s = 0.78*q*math.exp(-pow(q/16.0,0.25))
        q = prop.he[0] + prop.he[1]
        sps = q/(d*d + q*q)**0.5
        r = (sps - prop_zgnd)/(sps + prop_zgnd)*math.exp(-min(10.0,prop.wn*s*sps))
        q = abq_alos(r)

        if q < 0.25 or q < sps:
            r = r*(sps/q)**0.5

        alosv = propa.emd*d + propa.aed
        q = prop.wn*prop.he[0]*prop.he[1]*2.0/d

        if q > 1.57:
            q = 3.14-2.4649/q

        alosv = (-4.343*math.log(abq_alos((math.cos(q) - math.sin(q)*1j) + r)) - alosv) * wls \
                + alosv

    return alosv


def qlra(kst, klimx, mdvarx, prop, propv):
    """
    This is used to prepare the model in the area prediction mode. Normally,
    one first calls qlrps and then qlra. Before calling the latter, one should
    have defined in the <Primary Parameters 2> the antenna heights hg, the
    terrain irregularity dh, and (probably through qlrps) the variables wn,
    ens, gme, and zgnd. The input kst will define siting criteria for the
    terminals, klimx the climate, and mdvarx the mode of variability. If
    klimx <= 0 or mdvarx < 0 the associated parameters remain unchanged.

    (Section 42)
    """

    prop_zgnd = prop.zgndreal + prop.zgndimag * 1j

    for j in range(2):

        if kst[j] <= 0:
            prop.he[j] = prop.hg[j]

        else:
            q = 4.0

            if kst[j] <> 1:
                q = 9.0

            if prop.hg[j] < 5.0:
                q *= sin(0.3141593*prop.hg[j])

            prop.he[j] = prop.hg[j] + (1.0 + q) \
                         *math.exp(-min(20.0,2.0*prop.hg[j]/max(1e-3,prop.dh)))

        q = (2.0*prop.he[j]/prop.gme)**0.5
        prop.dl[j] = q*math.exp(-0.07*(prop.dh/max(prop.he[j],5.0))**0.5)
        prop.the[j] = (0.65*prop.dh*(q/prop.dl[j]-1.0)-2.0*prop.he[j])/q

    prop.mdp = 1
    propv.lvar = max(propv.lvar, 3)

    if mdvarx >= 0:
        propv.mdvar = mdvarx
        propv.lvar = max(propv.lvar, 4)

    if klimx > 0:
        propv.klim = klimx
        propv.lvar = 5

    return 0


def lrprop(d, prop, propa):  # // PaulM_lrprop
    """
    The Longley Rice propagation program. This is the basic program it
    returns the reference attenuation aref.

    (Section 4)

    AWC Notes
    """

    global wlos, wscat
    global dmin, xae

    prop_zgnd = prop.zgndreal + prop.zgndimag * 1j

    if prop.mdp <> 0:

        for j in range(2):
            propa.dls[j] = (2.0*prop.he[j]/prop.gme)**0.5
        propa.dlsa = propa.dls[0] + propa.dls[1]
        propa.dla = prop.dl[0] + prop.dl[1]
        propa.tha = max(prop.the[0]+prop.the[1], -propa.dla*prop.gme)
        wlos = False
        wscat = False

        if prop.wn < 0.838 or prop.wn > 210.0:
            prop.kwx = max(prop.kwx, 1)

        for j in range(2):
            if prop.hg[j] < 1.0 or prop.hg[j] > 1000.0:
                prop.kwx = max(prop.kwx, 1)

        for j in range(2):
            if (abs(prop.the[j]) > 200e-3
               or prop.dl[j] < 0.1*propa.dls[j]
               or prop.dl[j] > 3.0*propa.dls[j]):
                prop.kwx = max(prop.kwx, 3)

        if (prop.ens < 250.0   or prop.ens > 400.0
           or prop.gme < 75e-9 or prop.gme > 250e-9
           or prop_zgnd.real <= abs(prop_zgnd.imag)
           or prop.wn < 0.419 or prop.wn > 420.0):
            prop.kwx=4

        for j in range(2):
            if prop.hg[j] < 0.5 or prop.hg[j] > 3000.0:
                prop.kwx=4

        dmin = abs(prop.he[0] - prop.he[1])/200e-3

        q = adiff(0.0, prop, propa)

        xae = pow(prop.wn*pow(prop.gme, 2), -(1.0/3.0))
        d3 = max(propa.dlsa, 1.3787*xae + propa.dla)
        d4 = d3 + 2.7574*xae
        a3 = adiff(d3, prop, propa)
        a4 = adiff(d4, prop, propa)
        propa.emd = (a4 - a3)/(d4 - d3)
        propa.aed = a3 - propa.emd*d3

    if prop.mdp >= 0:
        prop.mdp = 0
        prop.dist = d

    if prop.dist > 0.0:
        if prop.dist > 1000e3:
            prop.kwx = max(prop.kwx,1)
        if prop.dist < dmin:
            prop.kwx = max(prop.kwx,3)
        if prop.dist < 1e3 or prop.dist > 2000e3:
            prop.kwx = 4

   
    if prop.dist < propa.dlsa:

        if not wlos:
            q = alos(0.0, prop, propa)
            d2 = propa.dlsa
            a2 = propa.aed + d2*propa.emd
            d0 = 1.908*prop.wn*prop.he[0]*prop.he[1]

            if propa.aed >= 0.0:
                d0 = min(d0, 0.5*propa.dla)
                d1 = d0 + 0.25*(propa.dla-d0)
            else:
                d1 = max(-propa.aed/propa.emd, 0.25*propa.dla)

            a1 = alos(d1, prop, propa)
            wq = False

            if d0 < d1:
                a0 = alos(d0, prop, propa)
                q = math.log(d2/d0)
                propa.ak2 = max(0.0, ((d2 - d0)*(a1 - a0)-(d1 - d0)*(a2 - a0)) \
                                  / ((d2-d0)*math.log(d1/d0)-(d1-d0)*q))
                wq = (propa.aed >= 0.0 or propa.ak2 > 0.0)

                if wq:
                    propa.ak1 = (a2 - a0 - propa.ak2*q)/(d2 - d0)

                    if propa.ak1 < 0.0:
                        propa.ak1 = 0.0
                        propa.ak2 = fortran_dim(a2, a0)/q

                        if propa.ak2 == 0.0:
                            propa.ak1=propa.emd

            if not wq:
                propa.ak1 = fortran_dim(a2, a1)/(d2 - d1)
                propa.ak2 = 0.0

                if propa.ak1 == 0.0:
                    propa.ak1=propa.emd

            propa.ael = a2 - propa.ak1*d2 - propa.ak2*math.log(d2)
            wlos = True

        if prop.dist > 0.0:
            prop.aref = propa.ael + propa.ak1*prop.dist \
                    + propa.ak2*math.log(prop.dist)

    if prop.dist <= 0.0 or prop.dist >= propa.dlsa:
        if not wscat:
            q = ascat(0.0, prop, propa)
            d5 = propa.dla + 200e3
            d6 = d5+200e3
            a6 = ascat(d6, prop, propa)
            a5 = ascat(d5, prop, propa)

            if a5 < 1000.0:
                propa.ems = (a6 - a5)/200e3
                propa.dx = max(propa.dlsa, max(propa.dla+0.3*xae \
                    *math.log(47.7*prop.wn), (a5-propa.aed-propa.ems*d5) \
                    /(propa.emd-propa.ems)))
                propa.aes=(propa.emd-propa.ems)*propa.dx+propa.aed
            else:
                propa.ems = propa.emd
                propa.aes = propa.aed
                propa.dx = 10.e6

            wscat = True

        if prop.dist > propa.dx:
            prop.aref = propa.aes + propa.ems*prop.dist
        else:
            prop.aref = propa.aed + propa.emd*prop.dist

    prop.aref = max(prop.aref, 0.0)

    return 0


def curve(c1, c2, x1, x2, x3, de):
    """
    (Section 30)
    """

    return (c1 + c2/(1.0 + pow((de - x2)/x3, 2.0)))*pow(de/x1, 2.0) \
           / (1.0 + pow(de/x1, 2.0))


def avar(zzt, zzl, zzc, prop, propv):
    """
    When in the area prediction mode, one needs a threefold quantile of
    attenuation which corresponds to the fraction q_T of time, the fraction
    q_L of locations, and the fraction q_S of "situations." In the point to
    point mode, one needs only q_T and q_S. For efficiency, avar is written as
    a function of the "standard normal deviates" z_T, z_L, and z_S corresponding
    to the requested fractions. Thus, for example, q_T = Q(z_T) where Q(z) is
    the "complementary standard normal distribution." For the point to point
    mode one sets z_L = 0 which corresponds to the median q_L = 0.50.

    The subprogram is written trying to reduce duplicate calculations. This is
    done through the switch lvar. On first entering, set lvar = 5. Then all
    parameters will be initialized, and lvar will be changed to 0. If the
    program is to be used to find several quantiles with different values of
    z_T, z_L, or z_S, then lvar whould be 0, as it is. If the distance is
    changed, set lvar = 1 and parameters that depend on the distance will be
    recomputed. If antenna heights are changed, set lvar = 2 if the frequency,
    lvar = 3 if the mode variability mdvar, set lvar = 4 and finally, if the
    climate is changed, set lvar = 5. The higher the value of lvar, the more
    parameters will be recomputed.

    (Section 28)
    """

    global kdv
    global dexa, de, vmd, vs0, sgl, sgtm, sgtp, sgtd, tgtd
    global gm, gp, cv1, cv2, yv1, yv2, yv3, csm1, csm2, ysm1
    global ysm2, ysm3, csp1, csp2, ysp1, ysp2, ysp3, csd1, zd
    global cfm1, cfm2, cfm3, cfp1, cfp2, cfp3
    global ws, w1

    bv1 = [-9.67,-0.62,1.26,-9.21,-0.62,-0.39,3.15]
    bv2 = [12.7,9.19,15.5,9.05,9.19,2.86,857.9]
    xv1 = [144.9e3,228.9e3,262.6e3,84.1e3,228.9e3,141.7e3,2222.e3]
    xv2 = [190.3e3,205.2e3,185.2e3,101.1e3,205.2e3,315.9e3,164.8e3]
    xv3 = [133.8e3,143.6e3,99.8e3,98.6e3,143.6e3,167.4e3,116.3e3]
    bsm1 = [2.13,2.66,6.11,1.98,2.68,6.86,8.51]
    bsm2 = [159.5,7.67,6.65,13.11,7.16,10.38,169.8]
    xsm1 = [762.2e3,100.4e3,138.2e3,139.1e3,93.7e3,187.8e3,609.8e3]
    xsm2 = [123.6e3,172.5e3,242.2e3,132.7e3,186.8e3,169.6e3,119.9e3]
    xsm3 = [94.5e3,136.4e3,178.6e3,193.5e3,133.5e3,108.9e3,106.6e3]
    bsp1 = [2.11,6.87,10.08,3.68,4.75,8.58,8.43]
    bsp2 = [102.3,15.53,9.60,159.3,8.12,13.97,8.19]
    xsp1 = [636.9e3,138.7e3,165.3e3,464.4e3,93.2e3,216.0e3,136.2e3]
    xsp2 = [134.8e3,143.7e3,225.7e3,93.1e3,135.9e3,152.0e3,188.5e3]
    xsp3 = [95.6e3,98.6e3,129.7e3,94.2e3,113.4e3,122.7e3,122.9e3]
    bsd1 = [1.224,0.801,1.380,1.000,1.224,1.518,1.518]
    bzd1 = [1.282,2.161,1.282,20.,1.282,1.282,1.282]
    bfm1 = [1.0,1.0,1.0,1.0,0.92,1.0,1.0]
    bfm2 = [0.0,0.0,0.0,0.0,0.25,0.0,0.0]
    bfm3 = [0.0,0.0,0.0,0.0,1.77,0.0,0.0]
    bfp1 = [1.0,0.93,1.0,0.93,0.93,1.0,1.0]
    bfp2 = [0.0,0.31,0.0,0.19,0.31,0.0,0.0]
    bfp3 = [0.0,2.00,0.0,1.79,2.00,0.0,0.0]
    rt = 7.8
    rl = 24.0
    temp_klim = propv.klim - 1

    if propv.lvar > 0:

        if propv.lvar not in [1, 2, 3, 4]:
            
            if propv.klim <= 0 or propv.klim > 7:
                propv.klim = 5
                temp_klim = 4
                prop.kwx = max(prop.kwx,2)
            cv1 = bv1[temp_klim]
            cv2 = bv2[temp_klim]
            yv1 = xv1[temp_klim]
            yv2 = xv2[temp_klim]
            yv3 = xv3[temp_klim]
            csm1 = bsm1[temp_klim]
            csm2 = bsm2[temp_klim]
            ysm1 = xsm1[temp_klim]
            ysm2 = xsm2[temp_klim]
            ysm3 = xsm3[temp_klim]
            csp1 = bsp1[temp_klim]
            csp2 = bsp2[temp_klim]
            ysp1 = xsp1[temp_klim]
            ysp2 = xsp2[temp_klim]
            ysp3 = xsp3[temp_klim]
            csd1 = bsd1[temp_klim]
            zd = bzd1[temp_klim]
            cfm1 = bfm1[temp_klim]
            cfm2 = bfm2[temp_klim]
            cfm3 = bfm3[temp_klim]
            cfp1 = bfp1[temp_klim]
            cfp2 = bfp2[temp_klim]
            cfp3 = bfp3[temp_klim]
        
        if propv.lvar == 4 or propv.lvar not in [1, 2, 3, 4]:
            kdv = propv.mdvar
            ws = (kdv >= 20)

            if ws:
                kdv -= 20
            w1 = (kdv >= 10)

            if w1:
                kdv -= 10

            if kdv < 0 or kdv > 3:
                kdv = 0
                prop.kwx = max(prop.kwx,2)

        if propv.lvar in [3, 4] or propv.lvar not in [1, 2, 3, 4]:
            q = math.log(0.133*prop.wn)
            gm = cfm1 + cfm2/(pow(cfm3*q, 2.0) + 1.0)
            gp = cfp1 + cfp2/(pow(cfp3*q, 2.0) + 1.0)

        if propv.lvar in [2, 3, 4] or propv.lvar not in [1, 2, 3, 4]:
            dexa = (18.e6*prop.he[0])**0.5 + (18.e6*prop.he[1])**0.5 \
                   + pow((575.7e12/prop.wn), (1./3.))
            
        if propv.lvar in [1, 2, 3, 4] or propv.lvar not in [1, 2, 3, 4]:
            if prop.dist < dexa:
                de = 130.e3*prop.dist/dexa
            else:
                de = 130.e3+prop.dist-dexa

        vmd = curve(cv1, cv2, yv1, yv2, yv3, de)
        sgtm = curve(csm1,csm2,ysm1,ysm2,ysm3,de) * gm
        sgtp = curve(csp1,csp2,ysp1,ysp2,ysp3,de) * gp
        sgtd = sgtp*csd1
        tgtd = (sgtp - sgtd)*zd

        if w1:
            sgl = 0.0
        else:
            q = (1.0 - 0.8*math.exp(-prop.dist/50.e3))*prop.dh*prop.wn
            sgl = 10.0*q/(q + 13.0)
        if ws:
            vs0 = 0.0
        else:
            vs0 = pow(5.0 + 3.0*math.exp(-de/100.e3), 2.0)
        propv.lvar=0
        
    zt = zzt
    zl = zzl
    zc = zzc

    if kdv == 0:
        zt = zc
        zl = zc
    elif kdv == 1:
        zl = zc
    elif kdv == 2:
        zl = zt

    if abs(zt) > 3.1 or abs(zl) > 3.1 or abs(zc) > 3.1:
        prop.kwx = max(prop.kwx, 1)

    if zt < 0.0:
        sgt = sgtm
    elif zt <= zd:
        sgt = sgtp
    else:
        sgt = sgtd + tgtd/zt
        
    vs = vs0 + pow(sgt*zt,2.0)/(rt + zc*zc) + pow(sgl*zl, 2.0)/(rl + zc*zc)

    if kdv == 0:
        yr = 0.0
        propv.sgc = (sgt*sgt + sgl*sgl + vs)**0.5
    elif kdv == 1:
        yr = sgt*zt
        propv.sgc = (sgl*sgl + vs)**0.5
    elif kdv == 2:
        yr = zt * (sgt*sgt + sgl*sgl)**0.5
        propv.sgc = vs**0.5
    else:
        yr = sgt*zt + sgl*zl
        propv.sgc = vs**0.5

    avarv = prop.aref - vmd - yr - propv.sgc*zc
    if avarv < 0.0:
        avarv = avarv*(29.0 - avarv)/(29.0 - 10.0*avarv)

    return avarv


def hzns(pfl, prop):
    """
    Here we use the terrain profile pfl to find the two horizons. Output consists
    of the horizon distances dl and the horizon take-off angles the. If the path is
    line-of-sight, the routine sets both horizon distances equal to dist.

    (Section 47)
    """

    np = int(pfl[0])
    xi = pfl[1]
    za = pfl[2] + prop.hg[0]
    zb = pfl[np+2] + prop.hg[1]
    qc = 0.5*prop.gme
    q = qc*prop.dist
    prop.the[1] = (zb-za)/prop.dist
    prop.the[0] = prop.the[1] - q
    prop.the[1] = -prop.the[1] - q
    prop.dl[0] = prop.dist
    prop.dl[1] = prop.dist

    if np >= 2:
        sa = 0.0
        sb = prop.dist
        wq = True
        for i in range(1, np):
            sa += xi
            sb -= xi
            q = pfl[i+2] - (qc*sa + prop.the[0])*sa - za
            if q > 0.0:
                prop.the[0] += q/sa
                prop.dl[0] = sa
                wq = False
            if not wq:
                q = pfl[i+2] - (qc*sb + prop.the[1])*sb - zb
                if q > 0.0:
                    prop.the[1] += q/sb
                    prop.dl[1] = sb


def z1sq1 (z, x1, x2, z0, zn):
    """
    A linear least squares fit between x1, x2 to the function described by the
    array z. This array must have a special format: z(1) = en, the number of
    equally large intervals, z(2) = epsilon, the interval length, and z(j+3),
    j = 0, ..., n, function values. The output consists of values of the required
    line, z0 at 0, zn at xt = n*epsilon.

    (Section 53)

    [Note: Changed to a function that returns z0 and zn, since Python functions
    cannot return modified parameters that are immutable objects. Because of this
    change, the code has been changed elsewhere, wherever z1sq1 is called. -- AWC]
    """

    xn = z[0]
    xa = int(fortran_dim(x1/z[1], 0.0))
    xb = xn - int(fortran_dim(xn, x2/z[1]))

    if xb <= xa:
        xa = fortran_dim(xa, 1.0)
        xb = xn - fortran_dim(xn, xb+1.0)

    ja = int(xa)
    jb = int(xb)
    n = jb - ja
    xa = xb - xa
    x = -0.5*xa
    xb += x
    a = 0.5*(z[ja+2] + z[jb+2])
    b = 0.5*(z[ja+2] - z[jb+2])*x

    for i in range(2, n+1):
        ja = ja + 1
        x += 1.0
        a += z[ja + 2]
        b += z[ja + 2]*x

    a /= xa
    b = b*12.0/((xa*xa + 2.0)*xa)
    z0 = a - b*xb
    zn = a + b*(xn-xb)

    return z0, zn


def qtile(nn, a, ir):
    """
    This routine provides a quantile. It reorders the array a so that a(j),
    j = 1...i_r are all greater than or equal to all a(i), i = i_r ... nn. In
    particular, a(i_r) will have the same value it would have if a were completely
    sorted in descending order. The returned value is qtile = a(i_r).

    (Section 52)
    """

    m = 0
    n = nn
    j1 = n
    i0 = m
    done = False
    goto10 = True

    m = 0
    n = nn
    k = min(max(0, ir), n)
    q = a[k]

    while not done:
        
        if goto10:
            q = a[k]
            i0 = m
            j1 = n

        i = i0
        while i <= n and a[i] >= q:
            i += 1

        if i > n:
            i = n

        j = j1
        while j >= m and a[j] <= q:
            j -= 1

        if j < m:
            j = m

        if i < j:
            r = a[i]
            a[i] = a[j]
            a[j] = r
            i0 = i+1
            j1 = j-1
            goto10 = False
        elif i < k:
            a[k] = a[i]
            a[i] = q
            m = i+1
            goto10 = True
        elif j > k:
            a[k] = a[j]
            a[j] = q
            n = j-1
            goto10 = True
        else:
            done = True

    return q


def qerf(z):
    """
    The standard normal complementary probability -- the function Q(x) =
    1/sqrt(2pi) int_x^inf e^(-t^2/2)dt.  The approximation is
    due to C. Hastings, Jr. ("Approximations for digital computers," Princeton
    University Press, 1955) and the maximum error should be 7.5E-8.

    (Section 50)
    """

    b1 = 0.319381530
    b2 = -0.356563782
    b3 = 1.781477937
    b4 = -1.821255987
    b5 = 1.330274429
    rp = 4.317008
    rrt2pi = 0.398942280

    x = z
    t = abs(x)

    if t >= 10.0:
        qerfv = 0.0
    else:
        t = rp/(t + rp)
        qerfv = math.exp(-0.5*x*x)*rrt2pi*((((b5*t + b4)*t + b3)*t + b2)*t + b1)*t

    if x < 0.0:
        qerfv = 1.0 - qerfv

    return qerfv


def d1thx(pfl, x1, x2):
    """
    Using the terrain profile pfl we find deltah, the interdecile range of
    elevations between the two points x1 and x2.

    (Section 48)
    """

    np = int(pfl[0])
    xa = x1/pfl[1]
    xb = x2/pfl[1]
    d1thxv = 0.0

    if xb - xa < 2.0:  # exit out
        return d1thxv

    ka = int(0.1*(xb - xa + 8.0))
    ka = min(max(4, ka), 25)

    n = 10*ka - 5
    kb = n-ka + 1
    sn = n-1

    s = []
    s.append(sn)
    s.append(1.0)
    xb = (xb - xa)/sn
    k = int(xa + 1.0)
    xa -= float(k)

    for j in range(n):
        while xa > 0.0 and k < np:
            xa -= 1.0
            k += 1
        s.append(pfl[k+2] + (pfl[k+2] - pfl[k+1])*xa)
        xa = xa + xb

    xa, xb = z1sq1(s,0.0,sn,xa,xb) # Revised call to z1sq1
    xb = (xb - xa)/sn
    for j in range(n):
        s[j+2] -= xa
        xa = xa + xb

    spartial = s[2:]
    
    d1thxv = qtile(n-1, spartial, ka-1) - qtile(n-1, spartial, kb-1)
    d1thxv /= 1.0 - 0.8*math.exp(-(x2 - x1)/50.0e3)

    return d1thxv

def qlrpfl(pfl, klimx, mdvarx, prop, propa, propv):
    """
    This subroutine may be used to prepare for the point-to-point mode. Since the
    path is fixed, it has only one value of aref and therefore at the end of the
    routine there is a call to lrprop. To complete the process one needs to call avar
    for whatever quantiles are desired.

    (Section 43)
    """

    xl = []

    prop.dist = pfl[0] * pfl[1]
    np = int(pfl[0])
    hzns(pfl, prop)

    for j in range(2):
        xl.append(min(15.0*prop.hg[j], 0.1*prop.dl[j]))

    xl[1] = prop.dist - xl[1]
    prop.dh = d1thx(pfl, xl[0], xl[1])
    
    if prop.dl[0] + prop.dl[1] > 1.5*prop.dist:

        za = 0 # Must initialize before calling z1sq1
        zb = 0 # Must initialize before calling z1sq1
        za, zb = z1sq1(pfl, xl[0], xl[1], za, zb) # Revised call to z1sq1
        prop.he[0] = prop.hg[0] + fortran_dim(pfl[2], za)
        prop.he[1] = prop.hg[1] + fortran_dim(pfl[np+2], zb)

        for j in range(2):
            prop.dl[j] = (2.0*prop.he[j]/prop.gme)**0.5 \
                         * math.exp(-0.07*(prop.dh/max(prop.he[j],5.0))**0.5)
        q = prop.dl[0] + prop.dl[1]

        if q <= prop.dist:
            q = pow(prop.dist/q, 2.0)

            for j in range(2):
                prop.he[j] *= q 
                prop.dl[j] = (2.0*prop.he[j]/prop.gme)**0.5 \
                             * math.exp(-0.07*(prop.dh/max(prop.he[j],5.0))**0.5)

        for j in range(2):
            q = (2.0*prop.he[j]/prop.gme)**0.5
            prop.the[j] = (0.65*prop.dh*(q/prop.dl[j]-1.0)-2.0 \
                           * prop.he[j])/q

    else:
        za = 0 # Must initialize before using in function call
        q = 0  # Must initialize before using in function call
        za, q = z1sq1(pfl, xl[0], 0.9*prop.dl[0], za, q) # Revised call to z1sq1

        zb = 0 # Must initialize before using in function call        
        q, zb = z1sq1(pfl, prop.dist-0.9*prop.dl[1], xl[1], q, zb) # Revised call

        prop.he[0] = prop.hg[0] + fortran_dim(pfl[2], za)
        prop.he[1] = prop.hg[1] + fortran_dim(pfl[np+2], zb)

    prop.mdp = -1
    propv.lvar = max(propv.lvar, 3)

    if mdvarx >= 0:
        propv.mdvar = mdvarx
        propv.lvar = max(propv.lvar, 4)

    if klimx > 0:
        propv.klim = klimx
        propv.lvar = 5

    lrprop(0.0, prop, propa)

    return 0

def deg2rad(d):
    """
    Legacy function to convert degrees to radians.
    """
    
    return math.radians(d)


#//********************************************************
#//* Point-To-Point Mode Calculations                     *
#//********************************************************

def point_to_point(elev, tht_m, rht_m, eps_dielect, sgm_conductivity,
                   eno_ns_surfref, frq_mhz, radio_climate, pol, conf, rel,
		   dbloss, strmode, errnum):
    
## pol: 0-Horizontal, 1-Vertical
## radio_climate: 1-Equatorial, 2-Continental Subtropical, 3-Maritime Tropical,
##                4-Desert, 5-Continental Temperate, 6-Maritime Temperate, Over Land,
##                7-Maritime Temperate, Over Sea
## conf, rel: .01 to .99
## elev[]: [num points - 1], [delta dist(meters)], [height(meters) point 1], ..., [height(meters) point n]
## errnum: 0- No Error.
##         1- Warning: Some parameters are nearly out of range.
##                     Results should be used with caution.
##         2- Note: Default parameters have been substituted for impossible ones.
##         3- Warning: A combination of parameters is out of range.
##                     Results are probably invalid.
##         Other-  Warning: Some parameters are out of range.
##                          Results are probably invalid.

    prop = PropType()
    propv = PropvType()
    propa = PropaType()
    zsys = 0

    prop.hg[0] = tht_m
    prop.hg[1] = rht_m
    propv.klim = radio_climate
    prop.kwx = 0
    propv.lvar = 5
    prop.mdp = -1
    zc = qerfi(conf)
    zr = qerfi(rel)
    np = int(elev[0])

    eno = eno_ns_surfref
    enso = 0.0
    q = enso

    if q <= 0.0:
        ja = int(3.0 + 0.1 * elev[0])
        jb = np - ja + 6
        for i in range(ja-1, jb):
            zsys += elev[i]
        zsys /= (jb - ja + 1)
        q = eno

    propv.mdvar = 13  # WinnForum mod. ORIGINAL CODE HAS mdvar = 12 ***
    qlrps(frq_mhz, zsys, q, pol, eps_dielect, sgm_conductivity,prop)
    qlrpfl(elev, propv.klim, propv.mdvar, prop, propa, propv)
    fs = 32.45 + 20.0 * math.log10(frq_mhz) + 20.0 * math.log10(prop.dist / 1000.0)
    q = prop.dist - propa.dla

    if int(q) < 0.0:
        strmode = "Line-Of-Sight Mode"
    else:
        if int(q) == 0.0:
            strmode = "Single Horizon"
        elif int(q) > 0.0:
            strmode = "Double Horizon"
        if prop.dist <= propa.dlsa or prop.dist <= propa.dx:
            strmode += ", Diffraction Dominant"
        elif prop.dist > propa.dx:
            strmode += ", Troposcatter Dominant"

    dbloss = avar(zr, 0.0, zc, prop, propv) + fs
    errnum = prop.kwx
    
    return dbloss, strmode, errnum


def point_to_pointMDH(elev, tht_m, rht_m, eps_dielect, sgm_conductivity,
                      eno_ns_surfref, frq_mhz, radio_climate, pol, timepct,
                      locpct, confpct, dbloss, propmode, deltaH, errnum):

## pol: 0-Horizontal, 1-Vertical
## radio_climate: 1-Equatorial, 2-Continental Subtropical, 3-Maritime Tropical,
##                4-Desert, 5-Continental Temperate, 6-Maritime Temperate, Over Land,
##                7-Maritime Temperate, Over Sea
## timepct, locpct, confpct: .01 to .99
## elev[]: [num points - 1], [delta dist(meters)], [height(meters) point 1], ..., [height(meters) point n]
## propmode:  Value   Mode
##             -1     mode is undefined
##              0     Line of Sight
##              5     Single Horizon, Diffraction
##              6     Single Horizon, Troposcatter
##              9     Double Horizon, Diffraction
##             10     Double Horizon, Troposcatter
## errnum: 0- No Error.
##         1- Warning: Some parameters are nearly out of range.
##                     Results should be used with caution.
##         2- Note: Default parameters have been substituted for impossible ones.
##         3- Warning: A combination of parameters is out of range.
##                     Results are probably invalid.
##         Other-  Warning: Some parameters are out of range.
##                          Results are probably invalid.

    prop = PropType()
    propv = PropvType()
    propa = PropaType()
    zsys = 0

    propmode = -1  # mode is undefined
    prop.hg[0] = tht_m
    prop.hg[1] = rht_m
    propv.klim = radio_climate
    prop.kwx = 0
    propv.lvar = 5
    prop.mdp = -1
    ztime = qerfi(timepct)
    zloc = qerfi(locpct)
    zconf = qerfi(confpct)

    np = int(elev[0])
    eno = eno_ns_surfref
    enso = 0.0
    q = enso

    if q <= 0.0:
        ja = int(3.0 + 0.1 * elev[0])
        jb = np - ja + 6
        for i in range(ja-1, jb):
            zsys += elev[i]
        zsys /= (jb - ja + 1)
        q = eno

    propv.mdvar = 12
    qlrps(frq_mhz, zsys, q, pol, eps_dielect, sgm_conductivity, prop)
    qlrpfl(elev, propv.klim, propv.mdvar, prop,propa, propv)
    fs = 32.45 + 20.0 * math.log10(frq_mhz) + 20.0 * math.log10(prop.dist / 1000.0)
    deltaH = prop.dh
    q = prop.dist - propa.dla

    if int(q) < 0.0:
        propmode = 0  # Line-Of-Sight Mode
    else:
        if int(q) == 0.0:
            propmode = 4  # Single Horizon
        elif int(q) > 0.0:
            propmode = 8  # Double Horizon
        if prop.dist <= propa.dlsa or prop.dist <= propa.dx:
            propmode += 1 # Diffraction Dominant
        elif prop.dist > propa.dx:
            propmode += 2 # Troposcatter Dominant

    dbloss = avar(ztime, zloc, zconf, prop, propv) + fs  # avar(time,location,confidence)
    errnum = prop.kwx
    
    return dbloss, propmode, deltaH, errnum


def point_to_pointDH (elev, tht_m, rht_m, eps_dielect, sgm_conductivity,
                      eno_ns_surfref, frq_mhz, radio_climate, pol, conf, rel,
                      dbloss, deltaH, errnum):

## pol: 0-Horizontal, 1-Vertical
## radio_climate: 1-Equatorial, 2-Continental Subtropical, 3-Maritime Tropical,
##                4-Desert, 5-Continental Temperate, 6-Maritime Temperate, Over Land,
##                7-Maritime Temperate, Over Sea
## conf, rel: .01 to .99
## elev[]: [num points - 1], [delta dist(meters)], [height(meters) point 1], ..., [height(meters) point n]
## errnum: 0- No Error.
##         1- Warning: Some parameters are nearly out of range.
##                     Results should be used with caution.
##         2- Note: Default parameters have been substituted for impossible ones.
##         3- Warning: A combination of parameters is out of range.
##                     Results are probably invalid.
##         Other-  Warning: Some parameters are out of range.
##                          Results are probably invalid.


    prop = PropType()
    propv = PropvType()
    propa = PropaType()
    zsys = 0

    prop.hg[0] = tht_m
    prop.hg[1] = rht_m
    propv.klim = radio_climate
    prop.kwx = 0
    propv.lvar = 5
    prop.mdp = -1
    zc = qerfi(conf)
    zr = qerfi(rel)
    np = int(elev[0])

    eno = eno_ns_surfref
    enso = 0.0
    q = enso

    if q <= 0.0:
        ja = int(3.0 + 0.1 * elev[0])
        jb = np - ja + 6
        for i in range(ja-1, jb): # (i=ja-1;i<jb;++i)
            zsys += elev[i]
        zsys /= (jb - ja + 1)
        q = eno

    propv.mdvar = 12
    qlrps(frq_mhz, zsys, q, pol, eps_dielect, sgm_conductivity, prop)
    qlrpfl(elev, propv.klim, propv.mdvar, prop,propa, propv)
    fs = 32.45 + 20.0 * math.log10(frq_mhz) + 20.0 * math.log10(prop.dist / 1000.0)
    deltaH = prop.dh
    q = prop.dist - propa.dla

    if int(q) < 0.0:
        strmode = "Line-Of-Sight Mode"
    else:
        if int(q) == 0.0:
            strmode = "Single Horizon"
        elif int(q) > 0.0:
            strmode = "Double Horizon"
        if prop.dist <= propa.dlsa or prop.dist <= propa.dx:
            strmode += ", Diffraction Dominant"
        elif prop.dist > propa.dx:
            strmode += ", Troposcatter Dominant"

    dbloss = avar(zr, 0.0, zc, prop, propv) + fs  # avar(time,location,confidence)
    errnum = prop.kwx

    return dbloss, deltaH, errnum, strmode # Original routine never returns strmode


##//********************************************************
##//* Area Mode Calculations                               *
##//********************************************************

def area(ModVar, deltaH, tht_m, rht_m, dist_km, TSiteCriteria, RSiteCriteria,
         eps_dielect, sgm_conductivity, eno_ns_surfref, frq_mhz, radio_climate,
         pol, pctTime, pctLoc, pctConf, dbloss, strmode, errnum):

## pol: 0-Horizontal, 1-Vertical
## TSiteCriteria, RSiteCriteria:
##		   0 - random, 1 - careful, 2 - very careful
## radio_climate: 1-Equatorial, 2-Continental Subtropical, 3-Maritime Tropical,
##                4-Desert, 5-Continental Temperate, 6-Maritime Temperate, Over Land,
##                7-Maritime Temperate, Over Sea
## ModVar: 0 - Single: pctConf is "Time/Situation/Location", pctTime, pctLoc not used
##         1 - Individual: pctTime is "Situation/Location", pctConf is "Confidence", pctLoc not used
##         2 - Mobile: pctTime is "Time/Locations (Reliability)", pctConf is "Confidence", pctLoc not used
##         3 - Broadcast: pctTime is "Time", pctLoc is "Location", pctConf is "Confidence"
## pctTime, pctLoc, pctConf: .01 to .99
## errnum: 0- No Error.
##         1- Warning: Some parameters are nearly out of range.
##                     Results should be used with caution.
##         2- Note: Default parameters have been substituted for impossible ones.
##         3- Warning: A combination of parameters is out of range.
##                     Results are probably invalid.
##         Other-  Warning: Some parameters are out of range.
##                          Results are probably invalid.
## NOTE: strmode is not used at this time.

    prop = PropType()
    propv = PropvType()
    propa = PropaType()

    kst = [int(TSiteCriteria), int(RSiteCriteria)]

    zt = qerfi(pctTime)
    zl = qerfi(pctLoc)
    zc = qerfi(pctConf)

    eps = eps_dielect
    sgm = sgm_conductivity
    eno = eno_ns_surfref

    prop.dh = deltaH
    prop.hg[0] = tht_m
    prop.hg[1] = rht_m
    propv.klim = int(radio_climate)
    prop.ens = eno
    prop.kwx = 0

    ivar = int(ModVar)
    ipol = int(pol)

    qlrps(frq_mhz, 0.0, eno, ipol, eps, sgm, prop)
    qlra(kst, propv.klim, ivar, prop, propv)
    
    if propv.lvar < 1:
        propv.lvar = 1
    
    lrprop(dist_km * 1000.0, prop, propa)

    fs = 32.45 + 20.0 * math.log10(frq_mhz) + 20.0 * math.log10(prop.dist / 1000.0)
    
    xlb = fs + avar(zt, zl, zc, prop, propv)
    dbloss = xlb

    if prop.kwx == 0:
        errnum = 0
    else:
        errnum = prop.kwx
        
    return dbloss, errnum


def ITMAreadBLoss(ModVar, deltaH, tht_m, rht_m, dist_km, TSiteCriteria,
                  RSiteCriteria, eps_dielect, sgm_conductivity, eno_ns_surfref,
                  frq_mhz, radio_climate, pol, pctTime, pctLoc, pctConf):

#   Initialize dbloss, errnum, and strmode before using in function call
    dbloss = 0.
    errnum = 0
    strmode = ''
    
    dbloss, errnum = \
    area(ModVar, deltaH, tht_m, rht_m, dist_km, TSiteCriteria, RSiteCriteria,
         eps_dielect, sgm_conductivity, eno_ns_surfref, frq_mhz, radio_climate,
         pol, pctTime, pctLoc, pctConf, dbloss, strmode, errnum)

    return dbloss, errnum


def ITMDLLVersion():

    return 7.0



# Test code:
p2pTest = False
p2pMDHtest = False
p2pDHtest = False
areaTest = False

def setElevation():
    """
    Returns an elevation profile for testing point-to-point prop mode.

    Andrew Clegg
    November 2016
    """

# This is the GLOBE terrain profile from MSAM, from 39N 77W to 39N 77.5W
##    return [95, 454.7352316, 89., 92., 89., 92., 100., 104., 106., 108., 106.,
##            100., 88., 80., 75., 78., 80., 80., 86., 91., 98., 105., 110., 107.,
##            103., 97., 91., 89., 92., 87., 81., 79., 77., 75., 80., 85., 89., 98.,
##            105., 107., 107., 106., 102., 105., 112., 108., 99., 84., 61., 51.,
##            74., 86., 93., 97., 100., 102., 109., 114., 116., 117., 117., 112.,
##            113., 117., 122., 129., 138., 131., 119., 103., 93., 87., 83., 86., 97.,
##            99., 103., 111., 108., 101., 97., 95., 95., 94., 90., 85., 81., 78.,
##            78., 78., 78., 79., 83., 89., 89., 91., 96., 101.]

# This is the Crystal Palace to Mursley, England path from the ITM test code
    return [156, 499, 96,   84,   65,   46,   46,   46,   61,   41,   33,   27,   23,
        19,   15,   15,   15, 15,   15,   15,   15,   15,   15,   15,   15,   15,
        17,   19,   21,   23,   25,   27, 29,   35,   46,   41,   35,   30,   33,
        35,   37,   40,   35,   30,   51,   62,   76, 46,   46,   46,   46,   46,
        46,   50,   56,   67,  106,   83,   95,  112,  137,  137, 76,  103,  122,
        122,   83,   71,   61,   64,   67,   71,   74,   77,   79,   86,   91, 83,
        76,   68,   63,   76,  107,  107,  107,  119,  127,  133,  135,  137,  142,
        148, 152, 152,  107,  137,  104,   91,   99,  120,  152,  152,  137,  168,
        168,  122,  137, 137, 170,  183,  183,  187,  194,  201,  192,  152,  152,
        166,  177,  198,  156,  127, 116, 107,  104,  101,   98,   95,  103,   91,
        97,  102,  107,  107,  107,  103,   98, 94,   91,  105,  122,  122,  122,
        122,  122,  137,  137,  137,  137,  137,  137,  137, 137, 140,  144,  147,
        150,  152,  159]

if p2pTest:
#================================
# Example of running in p2p mode
#================================
    elev = setElevation()
    
    ModVar = 3 # Broadcast
    deltaH = 91.
    tht_m = 10.0 # Tx height
    rht_m = 10. # Rx height
    TSiteCriteria = 0 # Random
    RSiteCriteria = 0 # Random
    eps_dielect = 15
    sgm_conductivity = 0.005
    eno_ns_surfref = 301
    frq_mhz = 3500.0
    radio_climate = 5 # Continental Temperate
    pol = 0 # Vertical
    rel = 0.5
    conf = 0.5

# Must initialize these variables since they are passed to the function
    dbloss = 0
    strmode = ''
    errnum = 0

    a_rel = [0.01, 0.1, 0.5, 0.9, 0.99]
    a_conf = [0.5, 0.9, 0.1]

    for rel in a_rel:
        for conf in a_conf:
            dbloss, strmode, errnum = \
                point_to_point(elev, tht_m, rht_m, eps_dielect, sgm_conductivity,
                eno_ns_surfref, frq_mhz, radio_climate, pol, conf, rel,
                dbloss, strmode, errnum)
            print rel, conf, dbloss, strmode, errnum

if p2pMDHtest:

    elev = setElevation()
    ModVar = 3 # Broadcast
    deltaH = 0.
    tht_m = 10. # Tx height
    rht_m = 10. # Rx height
    TSiteCriteria = 0 # Random
    RSiteCriteria = 0 # Random
    eps_dielect = 15
    sgm_conductivity = 0.005
    eno_ns_surfref = 301
    frq_mhz = 3500.
    radio_climate = 5 # Continental Temperate
    pol = 1 # Vertical
    timepct = 0.5
    locpct = 0.5
    confpct = 0.5

#   Initialize before using in function call
    dbloss = propmode = deltaH = errnum = 0
    
    dbloss, propmode, deltaH, errnum = \
            point_to_pointMDH(elev, tht_m, rht_m, eps_dielect, sgm_conductivity,
                      eno_ns_surfref, frq_mhz, radio_climate, pol, timepct,
                      locpct, confpct, dbloss, propmode, deltaH, errnum)

    print dbloss, propmode, deltaH, errnum


if p2pDHtest:

    elev = setElevation()
    ModVar = 3 # Broadcast
    deltaH = 0.
    tht_m = 10. # Tx height
    rht_m = 10. # Rx height
    TSiteCriteria = 0 # Random
    RSiteCriteria = 0 # Random
    eps_dielect = 15
    sgm_conductivity = 0.005
    eno_ns_surfref = 301
    frq_mhz = 3500.
    radio_climate = 5 # Continental Temperate
    pol = 1 # Vertical
    conf = 0.5
    rel = 0.5

#   Initialize before using in function call
    dbloss = deltaH = errnum = 0
    strmode = ''
    
    dbloss, deltaH, errnum, strmode = \
            point_to_pointDH (elev, tht_m, rht_m, eps_dielect, sgm_conductivity,
                      eno_ns_surfref, frq_mhz, radio_climate, pol, conf, rel,
                      dbloss, deltaH, errnum)

    print dbloss, deltaH, errnum, strmode

    
if areaTest:
#================================
# Example of running in area mode
#================================
    ModVar = 3 # Broadcast
    deltaH = 0.
    tht_m = 10. # Tx height
    rht_m = 10. # Rx height
    TSiteCriteria = 0 # Random
    RSiteCriteria = 0 # Random
    eps_dielect = 15
    sgm_conductivity = 0.005
    eno_ns_surfref = 301
    frq_mhz = 3500.
    radio_climate = 5 # Continental Temperate
    pol = 1 # Vertical
    pctTime = 0.5
    pctLoc = 0.5
    pctConf = 0.5

    for dist_km in range(10, 101):
      temp = ITMAreadBLoss(ModVar, deltaH, tht_m, rht_m, dist_km, TSiteCriteria,
                        RSiteCriteria, eps_dielect, sgm_conductivity, eno_ns_surfref,
                        frq_mhz, radio_climate, pol, pctTime, pctLoc, pctConf)

      print dist_km, temp[0]  
#==================================

