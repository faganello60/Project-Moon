import base64
from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path

import astropy.io.fits as iofits
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.dates import DateFormatter
from . import norp_utils as utils



FREQUENCIES_HZ = [1e9, 2e9, 3.75e9, 9.4e9, 17e9, 35e9, 80e9]
FREQUENCY_COLUMNS = {
    '1GHz': ('FREQ1', 'CalI_1GHz', 'DVal_1GHz'),
    '2GHz': ('FREQ2', 'CalI_2GHz', 'DVal_2GHz'),
    '3.75GHz': ('FREQ3', 'CalI_4GHz', 'DVal_4GHz'),
    '9.4GHz': ('FREQ4', 'CalI_9GHz', 'DVal_9GHz'),
    '17GHz': ('FREQ5', 'CalI_17GHz', 'DVal_17GHz'),
    '35GHz': ('FREQ6', 'CalI_35GHz', 'DVal_35GHz'),
    '80GHz': ('FREQ7', 'CalI_80GHz', 'DVal_80GHz'),
  }
FREQUENCY_HZ_BY_NAME = dict(zip(FREQUENCY_COLUMNS.keys(), FREQUENCIES_HZ))
FREQUENCY_READERS = {
    '1GHz': utils.norp_rd_1GHzI,
    '2GHz': utils.norp_rd_2GHzI,
    '3.75GHz': utils.norp_rd_4GHzI,
    '9.4GHz': utils.norp_rd_9GHzI,
    '17GHz': utils.norp_rd_17GHzI,
    '35GHz': utils.norp_rd_35GHzI,
    '80GHz': utils.norp_rd_80GHzI,
}


def get_data(filename):
    return {
        'obs_day': utils.norp_rd_obsDay(filename),
        'start_time': utils.norp_rd_sttim(filename),
        'end_time': utils.norp_rd_edtim(filename),
    }

def get_available_frequencies(filename):
    data = utils.norp_rd_existFreq(filename)
    return [freq for freq in FREQUENCY_READERS if data.get(freq) == 1]

def get_max_sfu(filename):
    frequencies = get_available_frequencies(filename)
    return {
        freq: max(FREQUENCY_READERS[freq](filename))
        for freq in frequencies
    }

def get_spectrum_graph_base64(flux, frequency, title='NoRP Spectrum'):
    spectrum = plt.figure(figsize=(8, 6))
    spectrum.add_subplot()
    plt.title(title)
    plt.plot(frequency, flux, marker='.', linestyle='None', markersize=10)
    plt.xlabel('Frequency (Hz)', fontsize=12)
    plt.ylabel('Flux Density (SFU)', fontsize=12)
    plt.xlim(0.5e9, 1e11)
    plt.ylim(0.1, 10000)
    plt.xscale('log')
    plt.yscale('log')

    buffer = BytesIO()
    spectrum.savefig(buffer, format='png', bbox_inches='tight')
    plt.close(spectrum)
    buffer.seek(0)

    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def get_full_light_curves(filename, frequency=None):
    if frequency is not None and frequency not in FREQUENCY_COLUMNS:
        raise ValueError(f'Unknown frequency: {frequency}')

    with iofits.open(filename) as hdulist:
        header = hdulist[0].header
        data = hdulist[1].data

        idlst = datetime(1979, 1, 1, tzinfo=timezone.utc)
        time = [
            datetime.fromtimestamp(tim_single + idlst.timestamp(), timezone.utc)
            for tim_single in data['Time'][0]
        ]

        frequencies = []
        for freq, (header_key, flux_key, dval_key) in FREQUENCY_COLUMNS.items():
            if frequency is not None and freq != frequency:
                continue
            if header_key not in header:
                continue
            frequencies.append(
                {
                    'name': freq,
                    'sfu': data[flux_key][0] * data[dval_key][0],
                }
            )

    return {
        'time': time,
        'frequencies': frequencies,
    }

def get_range_light_curves(filename, start_time, end_time):
    range_start = datetime.fromtimestamp(start_time / 1000, tz=timezone.utc)
    range_end = datetime.fromtimestamp(end_time / 1000, tz=timezone.utc)

    with iofits.open(filename) as hdulist:
        header = hdulist[0].header
        data = hdulist[1].data

        idlst = datetime(1979, 1, 1, tzinfo=timezone.utc)
        times = [
            datetime.fromtimestamp(tim_single + idlst.timestamp(), timezone.utc)
            for tim_single in data['Time'][0]
        ]

        if not times:
            raise ValueError('No time samples available in file.')

        istart = int(np.argmin([abs((sample - range_start).total_seconds()) for sample in times]))
        iend = int(np.argmin([abs((sample - range_end).total_seconds()) for sample in times]))

        if istart > iend:
            istart, iend = iend, istart

        # Include the point nearest to end_time in the returned slice.
        iend = min(iend + 1, len(times))

        if istart >= iend:
            raise ValueError('Selected range is empty.')

        frequencies = []
        for freq, (header_key, flux_key, dval_key) in FREQUENCY_COLUMNS.items():
            if header_key not in header:
                continue
            frequencies.append(
                {
                    'name': freq,
                    'sfu': (data[flux_key][0] * data[dval_key][0])[istart:iend],
                }
            )

    return {
        'start_index': istart,
        'end_index': iend - 1,
        'start_time': times[istart].isoformat(),
        'end_time': times[iend - 1].isoformat(),
        'time': times[istart:iend],
        'frequencies': frequencies,
    }

def remove_background_noise(filename, start_time, end_time, pre_flare_start, pre_flare_end):
    range_start = datetime.fromtimestamp(start_time / 1000, tz=timezone.utc)
    range_end = datetime.fromtimestamp(end_time / 1000, tz=timezone.utc)
    background_start = datetime.fromtimestamp(pre_flare_start / 1000, tz=timezone.utc)
    background_end = datetime.fromtimestamp(pre_flare_end / 1000, tz=timezone.utc)

    with iofits.open(filename) as hdulist:
        header = hdulist[0].header
        data = hdulist[1].data

        idlst = datetime(1979, 1, 1, tzinfo=timezone.utc)
        times = [
            datetime.fromtimestamp(tim_single + idlst.timestamp(), timezone.utc)
            for tim_single in data['Time'][0]
        ]

        if not times:
            raise ValueError('No time samples available in file.')

        istart = int(np.argmin([abs((sample - range_start).total_seconds()) for sample in times]))
        iend = int(np.argmin([abs((sample - range_end).total_seconds()) for sample in times]))
        ibackmin = int(np.argmin([abs((sample - background_start).total_seconds()) for sample in times]))
        ibackmax = int(np.argmin([abs((sample - background_end).total_seconds()) for sample in times]))

        if istart > iend:
            istart, iend = iend, istart

        if ibackmin > ibackmax:
            ibackmin, ibackmax = ibackmax, ibackmin

        # Include the point nearest to end_time in the returned slice.
        iend = min(iend + 1, len(times))

        # Include the point nearest to end_time in the background slice.
        ibackmax = min(ibackmax + 1, len(times))

        if istart >= iend:
            raise ValueError('Selected range is empty.')

        if ibackmin >= ibackmax:
            raise ValueError('Background interval is empty.')

        background_averages = {}
        corrected_frequencies = []

        for freq, (header_key, flux_key, dval_key) in FREQUENCY_COLUMNS.items():
            if header_key not in header:
                continue

            series = data[flux_key][0] * data[dval_key][0]
            background_slice = series[ibackmin:ibackmax]

            if len(background_slice) == 0:
                continue

            background = float(np.mean(background_slice))
            background_averages[freq] = background
            corrected_frequencies.append(
                {
                    'name': freq,
                    'sfu': (series - background)[istart:iend],
                }
            )

    return {
        'start_time': times[istart].isoformat(),
        'end_time': times[iend - 1].isoformat(),
        'background_start_time': times[ibackmin].isoformat(),
        'background_end_time': times[ibackmax - 1].isoformat(),
        'background_averages': background_averages,
        'time': times[istart:iend],
        'frequencies': corrected_frequencies,
    }

def get_flare_peak(filename, flare_start, flare_end, background_averages):
    flare_range_start = datetime.fromtimestamp(flare_start / 1000, tz=timezone.utc)
    flare_range_end = datetime.fromtimestamp(flare_end / 1000, tz=timezone.utc)

    with iofits.open(filename) as hdulist:
        header = hdulist[0].header
        data = hdulist[1].data

        idlst = datetime(1979, 1, 1, tzinfo=timezone.utc)
        times = [
            datetime.fromtimestamp(tim_single + idlst.timestamp(), timezone.utc)
            for tim_single in data['Time'][0]
        ]

        if not times:
            raise ValueError('No time samples available in file.')
        

        ipeakmin = int(np.argmin([abs((sample - flare_range_start).total_seconds()) for sample in times]))
        ipeakmax = int(np.argmin([abs((sample - flare_range_end).total_seconds()) for sample in times]))

        if ipeakmin > ipeakmax:
            ipeakmin, ipeakmax = ipeakmax, ipeakmin

        ipeakmax = min(ipeakmax + 1, len(times))

        if ipeakmin >= ipeakmax:
            raise ValueError('Flare interval is empty.')

        flare_peaks = {}
        spectrum_flux = []
        spectrum_frequency = []

        for freq, (header_key, flux_key, dval_key) in FREQUENCY_COLUMNS.items():
            if header_key not in header:
                continue

            if freq not in background_averages:
                continue

            series = data[flux_key][0] * data[dval_key][0]
            flare_slice = series[ipeakmin:ipeakmax]

            if len(flare_slice) == 0:
                continue

            flare_mean = float(np.mean(flare_slice))
            background = float(background_averages[freq])
            peak = flare_mean - background
            flare_peaks[freq] = peak
            spectrum_flux.append(peak)
            spectrum_frequency.append(FREQUENCY_HZ_BY_NAME[freq])

    return {
        'flare_start_time': times[ipeakmin].isoformat(),
        'flare_end_time': times[ipeakmax - 1].isoformat(),
        'flare_peaks': flare_peaks,
        'spectrum_image_base64': get_spectrum_graph_base64(
            spectrum_flux,
            spectrum_frequency,
            f'NoRP Spectrum {utils.norp_rd_obsDay(filename)}',
        ),
    }

def remove_spectrum_frequencies(filename, frequencies, fluxes, frequencies_to_remove):
    if len(frequencies) != len(fluxes):
        raise ValueError('frequencies and fluxes must have the same length.')

    remove_set = set(frequencies_to_remove)

    filtered_frequencies = []
    filtered_fluxes = []

    for frequency, flux in zip(frequencies, fluxes):
        if frequency not in FREQUENCY_HZ_BY_NAME:
            raise ValueError(f'Unknown frequency: {frequency}')

        if frequency in remove_set:
            continue

        filtered_frequencies.append(FREQUENCY_HZ_BY_NAME[frequency])
        filtered_fluxes.append(float(flux))

    return {
        'frequencies': filtered_frequencies,
        'fluxes': filtered_fluxes,
        'spectrum_image_base64': get_spectrum_graph_base64(
            filtered_fluxes,
            filtered_frequencies,
            f'NoRP Spectrum {utils.norp_rd_obsDay(filename)}',
        ),
    }