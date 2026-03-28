import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, timezone

# Add the 'norp' directory to sys.path to import norp_utils
sys.path.append(os.path.join(os.getcwd(), 'norp'))
import norp_utils

filename = 'examples/norp020531.fits.gz'
tempos_dt = norp_utils.norp_rd_time(filename)
data1GHz = norp_utils.norp_rd_1GHzI(filename)

# Target background from notebook: 149.36348
target_bg = 149.36348

# We know the times were around 00:00:11 and 00:04:16
# Convert to indices roughly
# Start time is 21:00:00.064 (2002-05-30)
# 00:00:11 is 3h 0m 11s = 10811s after start. 
# At ~10Hz, index is around 108110.

def get_approx_index(time_str):
    dt = datetime.strptime(time_str, '%H:%M:%S').replace(tzinfo=timezone.utc)
    # Adjust for the correct day (2002-05-31)
    dt = dt.replace(year=2002, month=5, day=31)
    diffs = [abs((t - dt).total_seconds()) for t in tempos_dt]
    return np.argmin(diffs)

i_start_approx = get_approx_index('00:00:11')
i_end_approx = get_approx_index('00:04:16')

print(f"Approx indices: {i_start_approx} to {i_end_approx}")

# Search a small window around these indices
best_diff = 1e9
best_range = (0, 0)

for i1 in range(i_start_approx - 20, i_start_approx + 20):
    for i2 in range(i_end_approx - 20, i_end_approx + 20):
        if i2 <= i1: continue
        avg = np.mean(data1GHz[i1:i2])
        diff = abs(avg - target_bg)
        if diff < best_diff:
            best_diff = diff
            best_range = (i1, i2)
            best_avg = avg

print(f"Best background range: {best_range} with avg {best_avg} (diff {best_diff})")
print(f"Start time: {tempos_dt[best_range[0]]}")
print(f"End time: {tempos_dt[best_range[1]]}")

# Now for peak. Target 1GHz peak minus bg: 200.33485
# So target peak avg = 200.33485 + 149.36348 = 349.69833
target_peak_avg = 200.33485 + 149.36348
i_peak_start_approx = get_approx_index('00:07:20')
i_peak_end_approx = get_approx_index('00:07:31')

best_peak_diff = 1e9
best_peak_range = (0, 0)

for i1 in range(i_peak_start_approx - 20, i_peak_start_approx + 20):
    for i2 in range(i_peak_end_approx - 20, i_peak_end_approx + 20):
        if i2 <= i1: continue
        avg = np.mean(data1GHz[i1:i2])
        diff = abs(avg - target_peak_avg)
        if diff < best_peak_diff:
            best_peak_diff = diff
            best_peak_range = (i1, i2)
            best_peak_avg = avg

print(f"Best peak range: {best_peak_range} with avg {best_peak_avg} (diff {best_peak_diff})")
print(f"Start time: {tempos_dt[best_peak_range[0]]}")
print(f"End time: {tempos_dt[best_peak_range[1]]}")
