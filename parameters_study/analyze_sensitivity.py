import numpy as np
import matplotlib.pyplot as plt
from gyro import gyroPython as gyro 
from gyro import gyro_utils
import io
import base64
import json
from concurrent.futures import ProcessPoolExecutor

def _gyro_worker(task):
    """
    Worker function to execute gyro.gyro in parallel processes.
    Sets the global input parameters in the worker process.
    """
    bins, current_args, view_angle, height, j1, j2, etr, plasma_np = task
    
    gyro.input1.viewangle = view_angle
    gyro.input2.height = height
    gyro.input3.j1 = j1
    gyro.input4.j2 = j2
    gyro.input5.etr = etr
    gyro.input6.np = plasma_np
    
    return gyro.gyro(bins, *current_args)

def parameter_impact(view_angle, height, emin, emax, etr, plasma_np, delta, nelectron, bmag, asize):
    j1 = gyro_utils.convertEminToJ1(emin)
    j2 = gyro_utils.convertEmaxToJ2(emax)
    nf = 200
    fmin = 1.0e9
    fmax = 1e12
    bins = np.logspace(np.log10(fmin), np.log10(fmax), nf)
    
    # Variables to configure the chart
    prefix = ""
    parameters = []
    tasks = []
    
    if len(delta) > 1:
        prefix = "delta"
        for current_delta in delta:
            parameters.append(current_delta)
            tasks.append((bins, [current_delta, nelectron[0], bmag[0], asize[0]], view_angle, height, j1, j2, etr, plasma_np))
    elif len(nelectron) > 1:
        prefix = "nelectron"
        for current_nelectron in nelectron:
            parameters.append(current_nelectron)
            tasks.append((bins, [delta[0], current_nelectron, bmag[0], asize[0]], view_angle, height, j1, j2, etr, plasma_np))
    elif len(bmag) > 1:
        prefix = "bmag"
        for current_bmag in bmag:
            parameters.append(current_bmag)
            tasks.append((bins, [delta[0], nelectron[0], current_bmag, asize[0]], view_angle, height, j1, j2, etr, plasma_np))
    elif len(asize) > 1:
        prefix = "asize"
        for current_asize in asize:
            parameters.append(current_asize)
            tasks.append((bins, [delta[0], nelectron[0], bmag[0], current_asize], view_angle, height, j1, j2, etr, plasma_np))

    # Parallel execution
    if tasks:
        with ProcessPoolExecutor() as executor:
            flux_results = list(executor.map(_gyro_worker, tasks))
    else:
        flux_results = []

    spectrum = plt.figure(figsize=(8, 6))
    spc = spectrum.add_subplot()
    spc.tick_params(axis='x', labelsize=14)
    spc.tick_params(axis='y', labelsize=14)

    for i in range(len(flux_results)):                
        plt.plot(bins[:], flux_results[i], label=f'{prefix} - {parameters[i]}')

    plt.xlabel('Frequency (Hz)', fontsize=14)
    plt.ylabel('Flux Density (SFU)', fontsize=14)
    # plt.xlim(1.0e9, 1.0e11)
    # plt.ylim(1e0, 1e3)
    plt.xscale('log')
    plt.yscale('log')
    plt.legend(loc='best', fontsize=16, frameon=False)
    

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    formatted_bins = ["{:.15E}".format(float(b)) for b in bins]

    formatted_flux_results = [
        {
            'prefix': prefix,
            'parameter_value': parameter_value,
            'flux': ["{:.15E}".format(float(value)) for value in flux_value]
        }
        for parameter_value, flux_value in zip(parameters, flux_results)
    ]

    result = {
        'image': img_base64,
        'bins': formatted_bins,
        'flux_results': formatted_flux_results
    }
    return json.dumps(result)
