import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from datetime import datetime, timezone
import os

# Import utility functions from norp_utils
try:
    from .norp_utils import (
        norp_rd_obsDay, norp_rd_sttim, norp_rd_edtim, norp_rd_time,
        norp_rd_1GHzI, norp_rd_2GHzI, norp_rd_4GHzI, norp_rd_9GHzI,
        norp_rd_17GHzI, norp_rd_35GHzI, norp_rd_80GHzI
    )
except (ImportError, ValueError):
    from norp_utils import (
        norp_rd_obsDay, norp_rd_sttim, norp_rd_edtim, norp_rd_time,
        norp_rd_1GHzI, norp_rd_2GHzI, norp_rd_4GHzI, norp_rd_9GHzI,
        norp_rd_17GHzI, norp_rd_35GHzI, norp_rd_80GHzI
    )

def process_norp_data(
    filename='examples/norp020531.fits.gz',
    t_analysis_range=None,
    t_background_range=None,
    t_peak_range=None,
    frequencies_hz=[2e9, 3.75e9, 9.4e9, 17e9, 35e9],
    save_output=True,
    output_dir='examples'
):
    """
    Process NoRP data from a FITS file and generate spectrum.
    
    Parameters:
    - filename: Path to the FITS file.
    - t_analysis_range: (start, end) as datetime objects or ISO strings.
    - t_background_range: (start, end) as datetime objects or ISO strings.
    - t_peak_range: (start, end) as datetime objects or ISO strings.
    - frequencies_hz: List of frequencies to include in the final spectrum.
    - save_output: Whether to save the .dat file and plots.
    - output_dir: Directory to save results.
    """
    
    # Frequency mapping
    freq_funcs = {
        1e9: norp_rd_1GHzI,
        2e9: norp_rd_2GHzI,
        3.75e9: norp_rd_4GHzI,
        9.4e9: norp_rd_9GHzI,
        17e9: norp_rd_17GHzI,
        35e9: norp_rd_35GHzI,
        80e9: norp_rd_80GHzI
    }
    
    all_frequencies = sorted(freq_funcs.keys())
    
    # Load all time data
    tempos_dt = norp_rd_time(filename)
    tempos_df = pd.DataFrame(tempos_dt, columns=['time'])
    
    def get_indices(start_time, end_time):
        if start_time is None or end_time is None:
            return 0, len(tempos_df) - 1
        
        start_dt = pd.to_datetime(start_time)
        end_dt = pd.to_datetime(end_time)
        
        # Ensure timezone awareness if data is timezone aware
        if tempos_dt[0].tzinfo is not None:
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)
        
        imin = np.argmin(np.abs(tempos_df['time'] - start_dt))
        imax = np.argmin(np.abs(tempos_df['time'] - end_dt))
        return imin, imax

    # Analysis interval
    imin, imax = get_indices(*t_analysis_range) if t_analysis_range else (0, len(tempos_df) - 1)
    
    # Background calculation
    backgrounds = {}
    if t_background_range:
        ibackmin, ibackmax = get_indices(*t_background_range)
        for freq in all_frequencies:
            data = freq_funcs[freq](filename)
            bg_data = data[ibackmin:ibackmax]
            # Use sum/len to match notebook's exact calculation
            backgrounds[freq] = sum(bg_data) / len(bg_data) if len(bg_data) > 0 else 0
    else:
        for freq in all_frequencies:
            backgrounds[freq] = 0

    # Peak calculation
    if t_peak_range:
        ipeakmin, ipeakmax = get_indices(*t_peak_range)
    else:
        ipeakmin, ipeakmax = imin, imax # Fallback to analysis range

    peaks_minus_bg = {}
    for freq in frequencies_hz:
        if freq not in freq_funcs:
            continue
        data = freq_funcs[freq](filename)
        peak_data = data[ipeakmin:ipeakmax]
        # Use sum/len to match notebook's exact calculation
        avg_peak = sum(peak_data) / len(peak_data) if len(peak_data) > 0 else 0
        peaks_minus_bg[freq] = avg_peak - backgrounds.get(freq, 0)

    # Prepare spectrum data
    final_freqs = [f for f in frequencies_hz if f in peaks_minus_bg]
    final_flux = [peaks_minus_bg[f] for f in final_freqs]
    
    obs_day = norp_rd_obsDay(filename)
    
    if save_output:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 1. Save .dat file
        output_file = os.path.join(output_dir, f'NoRP {obs_day}.dat')
        fluxo = np.column_stack([final_freqs, final_flux])
        np.savetxt(output_file, fluxo, fmt='%.5E')
        print(f"Saved spectrum data to {output_file}")
        
        # 2. Plot Lightcurves (matches summary plot style)
        fig = plt.figure(figsize=(12, 10))
        plt.title(f'NoRP {obs_day} - Lightcurves', fontsize=14)
        
        # Define colors for different frequencies
        colors = ['blue', 'orange', 'green', 'red', 'purple', 'brown', 'pink']
        
        for i, freq in enumerate(all_frequencies):
            data = freq_funcs[freq](filename)
            label = f'{freq/1e9:g} GHz'
            # Background subtraction logic
            bg = backgrounds.get(freq, 0)
            plt.plot(tempos_dt[imin:imax], data[imin:imax] - bg, 
                     linestyle='-', linewidth=1, label=label, color=colors[i % len(colors)])
            
        plt.gca().xaxis.set_major_formatter(DateFormatter('%H:%M'))
        plt.xlabel('Time [UT]', fontsize=12)
        plt.ylabel('Flux [SFU]', fontsize=12)
        plt.legend(loc='best', frameon=True)
        plt.grid(True, alpha=0.3)
        
        lc_plot_file = os.path.join(output_dir, f'NoRP_lightcurve_{obs_day}.png')
        plt.savefig(lc_plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved lightcurves plot to {lc_plot_file}")
        
        # 3. Plot Spectrum
        plt.figure(figsize=(8, 6))
        plt.title(f'NoRP {obs_day} - Spectrum', fontsize=14)
        plt.plot (final_freqs,final_flux,marker=".", linestyle='None', markersize=10)
        plt.xlabel('Frequência (Hz)', fontsize=12)
        plt.ylabel('Densidade de fluxo (SFU)', fontsize=12)
        plt.xlim(0.8e9,1e11)
        plt.ylim(10,1000)
        plt.xscale('log')
        plt.yscale('log')
        
        spec_plot_file = os.path.join(output_dir, f'NoRP_spectrum_{obs_day}.png')
        plt.savefig(spec_plot_file, dpi=1200, bbox_inches='tight', pad_inches = 0.05)
        plt.close()
        print(f"Saved spectrum plot to {spec_plot_file}")

    return {
        'frequencies': final_freqs,
        'flux': final_flux,
        'obs_day': obs_day,
        'backgrounds': backgrounds
    }

if __name__ == "__main__":
    # Process the data using the exact parameters identified from the notebook execution
    # These sub-second times align with the specific indices selected in the original Jupyter analysis
    process_norp_data(
        t_analysis_range=('2002-05-30 23:58:00', '2002-05-31 00:29:02'),
        t_background_range=('2002-05-31 00:00:12.436', '2002-05-31 00:04:15.336'),
        t_peak_range=('2002-05-31 00:07:20.936', '2002-05-31 00:07:31.936'),
        frequencies_hz=[2e9, 3.75e9, 9.4e9, 17e9, 35e9]
    )
