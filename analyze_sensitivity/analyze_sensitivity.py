import numpy as np
import matplotlib.pyplot as plt
from gyro import gyroPython as gyro  

import io
import base64
import json

def test_parameter_impact(view_angle, height, j1, j2, etr, plasma_np, delta, nelectron, bmag, asize):
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

    nf = 200
    fmin = 1.0e9
    fmax = 1e12
    bins = np.logspace(np.log10(fmin), np.log10(fmax), nf)
    
    prefix = ""
    variable_parameter = []
    
    if len(delta) > 1:
        prefix = "Delta"
    elif len(nelectron) > 1:
        prefix = "nelectron"
    elif len(bmag) > 1:
        prefix = "bmag"
    elif len(asize) > 1:
        prefix = "asize"


    delta_bf = delta
    nelectron_bf = nelectron
    bmag_bf = bmag[0]
    asize_bf = asize

    results = []

    flux = gyro.gyro(bins, delta_bf, nelectron_bf, bmag_bf, asize_bf)
    flux2 = gyro.gyro(bins, delta_bf, nelectron_bf, bmag[1], asize_bf)
    flux3 = gyro.gyro(bins, delta_bf, nelectron_bf, bmag[2], asize_bf)
    flux4 = gyro.gyro(bins, delta_bf, nelectron_bf, bmag[3], asize_bf)

    spectrum = plt.figure(figsize=(8, 6))
    spc = spectrum.add_subplot()
    spc.tick_params(axis='x', labelsize=14)
    spc.tick_params(axis='y', labelsize=14)

    plt.plot(bins[:], flux[:], 'r-', label='FITTING')
    plt.plot(bins[:], flux2[:], 'b-', label='FITTING-2')
    plt.plot(bins[:], flux3[:], 'g-', label='FITTING-3')
    plt.plot(bins[:], flux4[:], 'm-', label='FITTING-3')

    plt.xlabel('Frequency (Hz)', fontsize=14)
    plt.ylabel('Flux Density (SFU)', fontsize=14)
    plt.xlim(1.0e9, 1.0e11)
    plt.ylim(1e0, 1e3)
    plt.xscale('log')
    plt.yscale('log')
    plt.legend(loc='best', fontsize=16, frameon=False)
    

    # buf = io.BytesIO()
    # plt.savefig(buf, format='png')
    # buf.seek(0)
    # img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    # plt.close()

    # formatted_bins = ["{:.15E}".format(float(b)) for b in bins]
    # formatted_flux = ["{:.15E}".format(float(f)) for f in flux]

    # result = {
    #     'image': img_base64,
    #     'bins': formatted_bins,
    #     'flux': formatted_flux,
    #     'fit_report': result.fit_report(),
    #     'best_values': result.best_values
    # }
    # return json.dumps(result)
    plt.show()

if __name__ == "__main__":
    test_parameter_impact(
        view_angle=60.0e0,
        height=1.0e9,
        j1=1,
        j2=120,
        etr=2.5e0,
        plasma_np=1.0e9,
        delta=2.5e0,
        nelectron=1.0e33,
        bmag=[300.0e0/2, 300.0e0, 300.0e0*1.5, 300.0e0*2],
        asize = 20.0e0
    )