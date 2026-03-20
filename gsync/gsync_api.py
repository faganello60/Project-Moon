from lmfit import Parameters, Model
import numpy as np
import matplotlib.pyplot as plt
from . import gyro

import io
import base64
import json

def run_gsync(freq, sfu, view_angle, height, j1, j2, etr, plasma_np, params, prefix):
    xdata = freq
    ydata = sfu

    # Fixed parameters
    #
    #     viewangle     viewing angle (angle between B and the line of sight) [deg]
    #
    #     0 < cs < 1 :
    #     cs can take on any positive value greater than 0 and less than 1;
    #     the appropriate formulae for cs = 0 are given in Ramaty (1969);
    #     it appears that the routine works well for 0.1 < cs < 0.95.
    #
    #     height        source height [cm]
    #
    #     j1 and j2 define the range of electron energies used in the integration
    #
    #     j1            index to define Emin [MeV]
    #     j2            index to define Emax [MeV]
    #
    #     Examples:
    #
    #     j1=1 ; j2=120 corresponds to  10 keV  -   10 MeV
    #     j1=29; j2=160 corresponds to  50 keV  -  100 MeV
    #     j1=41; j2=160 corresponds to 100 keV  -  100 MeV
    #     j1=41; j2=200 corresponds to 100 keV  - 1000 MeV
    #
    #     etr           gyro/sync transition energy [MeV]
    #
    #     np            plasma density [cm^-3]


    gyro.input1.viewangle = view_angle
    gyro.input2.height = height
    gyro.input3.j1 = j1
    gyro.input4.j2 = j2
    gyro.input5.etr = etr
    gyro.input6.np = plasma_np

    # # Build the model for data-fitting with LMFIT
    #
    # Variable parameters
    #
    #     delta        spectral index of electron distribution
    #     nelectron    total number of electrons
    #     bmag         magnetic field [gauss] (assumed uniform)
    #     asize        source size [arc sec]
    #
    #

    def func(freq, delta, nelectron, bmag, asize):
        return gyro.gyro(freq, delta, nelectron, bmag, asize)

    gmodel = Model(func)


    #
    # Set variable parameters
    #
    # value: initial guess (must be in the range [min,max])
    # vary: fixed (False) or variable (True)
    # min: minimum value
    # max: maximum value
    #

    params = params

    # Fitting

    result = gmodel.fit(ydata, params, freq=xdata)
    # result.best_fit # unused expression

    # Plot data and model spectrum with the best-fit parameters
    #
    # nf logarithmic bins of frequency [Hz] in the range [fmin, fmax]
    #

    nf = 200
    fmin = 1.0e9
    fmax = 1e12
    bins = np.logspace(np.log10(fmin), np.log10(fmax), nf)

    # Set the best-fit parameters

    delta_bf = result.params['delta'].value
    nelectron_bf = result.params['nelectron'].value
    bmag_bf = result.params['bmag'].value
    asize_bf = result.params['asize'].value

    # Plot

    flux =[]
    for i in range (len(bins)):
        flux.append(gyro.gyro(bins[i],delta_bf,nelectron_bf,bmag_bf,asize_bf))

    spectrum = plt.figure(figsize=(8, 6))
    spc = spectrum.add_subplot()
    spc.tick_params(axis='x', labelsize=14)
    spc.tick_params(axis='y', labelsize=14)

    plt.plot(xdata, ydata, 's', markersize=8, label=f'SOL-{prefix}')
    plt.plot(bins[:], flux[:], 'r-', label='FITTING')
    plt.xlabel('Frequency (Hz)', fontsize=14)
    plt.ylabel('Flux Density (SFU)', fontsize=14)
    plt.xlim(1.0e9, 1.0e11)
    plt.ylim(1e0, 1e3)
    plt.xscale('log')
    plt.yscale('log')
    plt.legend(loc='best', fontsize=16, frameon=False)
    

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    formatted_bins = ["{:.15E}".format(float(b)) for b in bins]
    formatted_flux = ["{:.15E}".format(float(f)) for f in flux]

    result = {
        'image': img_base64,
        'bins': formatted_bins,
        'flux': formatted_flux,
        'fit_report': result.fit_report(),
        'best_values': result.best_values
    }
    return json.dumps(result)