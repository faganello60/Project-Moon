import numpy as np
from scipy.special import j0, j1, jv, jvp

class Input1:
    viewangle = 0.0

class Input2:
    height = 0.0

class Input3:
    j1 = 1

class Input4:
    j2 = 120

class Input5:
    etr = 3.0

class Input6:
    np = 0.0

input1 = Input1()
input2 = Input2()
input3 = Input3()
input4 = Input4()
input5 = Input5()
input6 = Input6()

# Constants
PI = 4.0 * np.arctan(1.0)
DTOR = PI / 180.0
AU = 1.49597870e13
ARC2CM = (DTOR / 3600.0) * AU
M0 = 9.1094e-28
C = 2.998e10
EC = 4.803e-10
E0 = (M0 * C * C) / (1.6022e-12) / (1.0e6)
SFU = 1.0e19

# Data for SEAR function (interpolation)
XD = np.array([0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1,
               0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8,
               0.9, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.5,
               3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
FD = np.array([0.213, 0.358, 0.445, 0.583, 0.702, 0.722, 0.818,
               0.874, 0.904, 0.917, 0.919, 0.901, 0.872,
               0.832, 0.788, 0.742, 0.694, 0.655,
               0.566, 0.486, 0.414, 0.354, 0.301, 0.2, 0.13,
               0.0845, 0.0541, 0.0339, 0.0214, 0.0085,
               0.0033, 0.0013, 0.0005, 0.00019])

def bespr(n, x):
    """Derivative of Bessel function J_n(x) with respect to x."""
    return jvp(n, x)

def sear(x_val):
    """Linear interpolation equivalent to Fortran SEAR subroutine."""
    if x_val <= XD[0]:
        return FD[0] 
    if x_val >= XD[-1]:
        return FD[-1]

    i = np.searchsorted(XD, x_val)
    if i == 0: i = 1
    
    x1 = XD[i-1]
    x2 = XD[i]
    y1 = FD[i-1]
    y2 = FD[i]
    
    s = (y2 * (x_val - x1) + y1 * (x2 - x_val)) / (x2 - x1)
    return s

def refr(ffb, ffp, cs):
    """Calculate refraction index components."""
    ss = np.sqrt(1.0 - cs * cs)
    ffb2 = ffb * ffb
    ffp2 = ffp * ffp
    
    anum = 2.0 * ffp2 * (ffp2 - ffb2)
    
    term_sqrt = np.sqrt(ffb**4 * ss**4 + 4.0 * ffb2 * (ffp2 - ffb2)**2 * cs**2)
    
    dnum1 = term_sqrt - 2.0 * ffb2 * (ffp2 - ffb2) - ffb2 * ss**2
    dnum2 = -term_sqrt - 2.0 * ffb2 * (ffp2 - ffb2) - ffb2 * ss**2
    
    an1 = 1.0 + anum / dnum1
    an2 = 1.0 + anum / dnum2
    
    aknum = 2.0 * ffb * (ffp2 - ffb2) * cs
    
    dknum1 = term_sqrt - ffb2 * ss**2
    dknum2 = -term_sqrt - ffb2 * ss**2
    
    ath1 = -aknum / dknum1
    ath2 = -aknum / dknum2
    
    return an1, an2, ath1, ath2

def ssy(gamma, delta, ffb, cs, alpha):
    """Synchrotron routine (E > Etr)."""
    ss = np.sqrt(1.0 - cs * cs)
    ffc = ffb * 2.0 / 3.0 / ss / gamma / gamma * \
          (1.0 + 9.0 / 4.0 * (gamma * gamma - 1.0) / alpha / alpha / ffb / ffb)**1.5
    
    x = ffc
    
    if x <= 1.0e-3:
        f_val = 4.0 * PI / np.sqrt(3.0) / 2.67894 * (x / 2.0)**0.333333 * \
                (1.0 - 2.67894 / 2.0 * (x / 2.0)**0.66666)
    elif x > 10.0:
        f_val = np.sqrt(PI * x / 2.0) * np.exp(-x) * (1.0 + 55.0 / 72.0 / x)
    else:
        f_val = sear(x)
        
    gtot = (np.sqrt(3.0) / 4.0 / PI) * ss * f_val / \
           np.sqrt(1.0 + 9.0 / 4.0 * (gamma * gamma - 1.0) / alpha / alpha / ffb / ffb)
           
    g1em = gtot / 2.0
    g2em = gtot / 2.0
    
    h2 = (delta * gamma * (gamma + 1.0) + 2.0 * gamma * gamma - 1.0) / \
         gamma / (gamma * gamma - 1.0)
         
    g1ab = g1em / (ffb * ffb) * h2
    g2ab = g2em / (ffb * ffb) * h2
    
    return g1em, g2em, g1ab, g2ab

def gsy(gamma, delta, ffb, cs, an, ath):
    """Gyrosynchrotron routine (E < Etr)."""
    beta = np.sqrt(gamma * gamma - 1.0) / gamma
    ss = np.sqrt(1.0 - cs * cs)
    ffc = ffb * 2.0 / 3.0 / ss / gamma / gamma
    
    if ffc >= 20.0:
        return 0.0, 0.0
        
    is1 = int(ffb * gamma * (1.0 - an * beta * cs) + 1.0)
    is2 = int(ffb * gamma * (1.0 + an * beta * cs))
    
    sum12em = 0.0
    sum12ab = 0.0
    
    # Loop over harmonics
    for i in range(is1, is2 + 1):
        if i == 0: continue 
        
        cphis = (1.0 - i / ffb / gamma) / beta / cs / an
        if cphis > 1.0: cphis = 1.0
        if cphis < -1.0: cphis = -1.0
            
        sphis = np.sqrt(1.0 - cphis * cphis)
        
        denom = (1.0 - an * beta * cs * cphis)
        if denom == 0: denom = 1e-30
        
        xs = i * an * beta * ss * sphis / denom
        
        if ffb > 50.0:
            xstr = 0.8
            if gamma > 5.0: xstr = 0.9
            if gamma > 10.0: xstr = 0.95
            if gamma > 15.0: xstr = 0.96
            if xs < xstr * i:
                continue
                
        if ffb > 250.0:
            xstr = 0.9
            if gamma > 5.0: xstr = 0.92
            if gamma > 10.0: xstr = 0.97
            if gamma > 15.0: xstr = 0.98
            if xs < xstr * i:
                continue
        
        b = jv(i, xs)
        bpr = bespr(i, xs)
        
        term_paren = (cs / ss / an - beta * cphis / ss)
        f12 = (-beta * sphis * bpr + ath * term_paren * b)**2
        
        h2 = (delta * gamma * (gamma + 1.0) + 2.0 * gamma * gamma - 1.0) / \
             gamma / (gamma * gamma - 1.0)
             
        f12em = f12
        f12ab = f12 * h2
        
        s12oldem = sum12em
        sum12em += f12em
        
        s12oldab = sum12ab
        sum12ab += f12ab
        
        # Convergence check
        if s12oldem > 0.0 and s12oldab > 0.0:
            if (sum12em - s12oldem) / s12oldem < 1.0e-12 and \
               (sum12ab - s12oldab) / s12oldab < 1.0e-12:
                break
                
    g12em = sum12em / beta / 2.0 / cs * ffb / (1.0 + ath**2)
    g12ab = sum12ab / beta / 2.0 / cs / ffb / (1.0 + ath**2) / an
    
    return g12em, g12ab

def gyro(freq, delta, nelectron, bmag, asize):
    """
    Main Gyrosynchrotron calculation routine.
    """
    # Ensure freq is an array
    if np.isscalar(freq):
        freq_arr = np.array([freq], dtype=np.float64)
        is_scalar = True
    else:
        freq_arr = np.array(freq, dtype=np.float64)
        is_scalar = False
        
    kf = len(freq_arr)
    flux = np.zeros(kf, dtype=np.float64)
    
    # Global parameters
    viewangle = input1.viewangle
    height = input2.height
    j1 = input3.j1
    j2 = input4.j2
    etr = input5.etr
    np_dens = input6.np 
    
    cs = np.cos(viewangle * DTOR)
    
    if cs < 0.1 or cs > 0.95:
        pass # print('viewing angle beyond the limits')
        
    ss = np.sin(viewangle * DTOR)
    
    vb = 0.5 / PI * (EC / M0 / C) * bmag      
    vp = EC * np.sqrt(np_dens / PI / M0)      
    ffp = vp / vb                             
    alpha = (3.0 / 2.0) / ffp                 
    
    emfac = (EC * EC * EC) / (M0 * C * C)     
    abfac = 4.0 * (PI * PI) * EC              
    
    radius = asize * ARC2CM / 2.0             
    area = PI * radius * radius               
    omega = area / (AU * AU)
    volume = area * height                    
    
    # Calculate XNORM
    XNORM = 0.0
    # Fortran loop j=j1,j2 (inclusive)
    for j in range(j1, j2 + 1):
        el = 10.0**(0.025 * (j - 1) - 2.0)
        eu = 10.0**(0.025 * j - 2.0)
        em = 10.0**(0.025 * (j - 0.5) - 2.0)
        de = eu - el
        XNORM += em**(-delta) * de
        
    # Arrays for output storage
    e1d = np.zeros(kf)
    e2d = np.zeros(kf)
    a1d = np.zeros(kf)
    a2d = np.zeros(kf)
    phi1 = np.zeros(kf)
    phi2 = np.zeros(kf)
    phit = np.zeros(kf)
    
    # Loop over frequency
    for k in range(kf):
        ffb = freq_arr[k] / vb
        
        an1, an2, ath1, ath2 = refr(ffb, ffp, cs)
        
        e1 = 0.0
        e2 = 0.0
        a1 = 0.0
        a2 = 0.0
        
        for j in range(j1, j2 + 1):
            el = 10.0**(0.025 * (j - 1) - 2.0)
            eu = 10.0**(0.025 * j - 2.0)
            em = 10.0**(0.025 * (j - 0.5) - 2.0)
            de = eu - el
            
            gamma = em / E0 + 1.0
            gtr = etr / E0 + 1.0
            
            g1em = 0.0
            g2em = 0.0
            g1ab = 0.0
            g2ab = 0.0
            
            if gamma < gtr:
                if ffb > ffp:
                    an = np.sqrt(an1)
                    g1em, g1ab = gsy(gamma, delta, ffb, cs, an, ath1)
                    
                if ffb > (np.sqrt(ffp**2 + 0.25) + 0.5):
                    an = np.sqrt(an2)
                    g2em, g2ab = gsy(gamma, delta, ffb, cs, an, ath2)
                    
            elif gamma >= gtr:
                if ffb > (np.sqrt(ffp**2 + 0.25) + 0.5):
                    g1em, g2em, g1ab, g2ab = ssy(gamma, delta, ffb, cs, alpha)
            
            e1 += g1em * em**(-delta) * de * bmag * emfac
            e2 += g2em * em**(-delta) * de * bmag * emfac
            a1 += g1ab * em**(-delta) * de / bmag * abfac
            a2 += g2ab * em**(-delta) * de / bmag * abfac
            
        e1d[k] = (nelectron / XNORM) * e1 / volume
        e2d[k] = (nelectron / XNORM) * e2 / volume
        a1d[k] = (nelectron / XNORM) * a1 / volume
        a2d[k] = (nelectron / XNORM) * a2 / volume
        
        arg1 = a1d[k] * height
        if arg1 < 0.001:
            phi1[k] = e1d[k] * volume / AU / AU
        else:
            phi1[k] = omega * (e1d[k] / a1d[k]) * (1.0 - np.exp(-arg1))
            
        arg2 = a2d[k] * height
        if arg2 < 0.001:
            phi2[k] = e2d[k] * volume / AU / AU
        else:
            phi2[k] = omega * (e2d[k] / a2d[k]) * (1.0 - np.exp(-arg2))
            
        phit[k] = phi1[k] + phi2[k]
        
        if freq_arr[k] >= vb:
            flux[k] = phit[k] * SFU
        else:
            flux[k] = 0.0
            
    if is_scalar:
        return flux[0]
    return flux