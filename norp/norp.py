from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import sys
import tempfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from fastapi import HTTPException, UploadFile

try:
    from .norp_utils import (
        norp_rd_1GHzI,
        norp_rd_2GHzI,
        norp_rd_4GHzI,
        norp_rd_9GHzI,
        norp_rd_17GHzI,
        norp_rd_35GHzI,
        norp_rd_80GHzI,
        norp_rd_obsDay,
        norp_rd_time,
    )
except (ImportError, ValueError):
    sys.path.append(str(Path(__file__).resolve().parent))
    from norp_utils import (
        norp_rd_1GHzI,
        norp_rd_2GHzI,
        norp_rd_4GHzI,
        norp_rd_9GHzI,
        norp_rd_17GHzI,
        norp_rd_35GHzI,
        norp_rd_80GHzI,
        norp_rd_obsDay,
        norp_rd_time,
    )


FREQUENCIES_HZ = [1e9, 2e9, 3.75e9, 9.4e9, 17e9, 35e9, 80e9]
FINAL_FREQUENCIES_HZ = [1e9,2e9, 3.75e9, 9.4e9, 17e9, 35e9, 80e9]
FREQUENCY_READERS = {
    1e9: norp_rd_1GHzI,
    2e9: norp_rd_2GHzI,
    3.75e9: norp_rd_4GHzI,
    9.4e9: norp_rd_9GHzI,
    17e9: norp_rd_17GHzI,
    35e9: norp_rd_35GHzI,
    80e9: norp_rd_80GHzI,
}

def iso_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def window_dict(times: List[datetime], start_index: int, end_index: int) -> Dict[str, object]:
    start_index = max(0, start_index)
    end_index = min(len(times), end_index)
    if end_index <= start_index:
        end_index = start_index + 1
    return {
        "start_index": start_index,
        "end_index": end_index,
        "start_time": iso_time(times[start_index]),
        "end_time": iso_time(times[end_index - 1]),
    }


def load_norp_data(filename: str) -> Tuple[List[datetime], Dict[float, np.ndarray]]:
    times = list(norp_rd_time(filename))
    flux = {}
    for frequency_hz, reader in FREQUENCY_READERS.items():
        flux[frequency_hz] = np.asarray(reader(filename), dtype=float)
    return times, flux


def automatic_flare_windows(times: List[datetime], flux: Dict[float, np.ndarray]) -> Dict[str, Dict[str, object]]:
    flare_reference = flux[9.4e9]
    smooth_window = 11
    kernel = np.ones(smooth_window, dtype=float) / float(smooth_window)
    flare_smooth = np.convolve(flare_reference, kernel, mode="same")

    flare_peak_index = int(np.argmax(flare_smooth))
    local_min_search_start = max(0, flare_peak_index - 3000)
    local_min_search_end = max(local_min_search_start + 1, flare_peak_index - 600)
    local_min_relative_index = int(np.argmin(flare_smooth[local_min_search_start:local_min_search_end]))
    flare_start_index = local_min_search_start + local_min_relative_index

    local_max_search_end = min(len(flare_smooth), flare_peak_index + 1800)
    decay_reference = flare_smooth[flare_start_index]
    flare_end_index = flare_peak_index + 1
    for index in range(flare_peak_index + 1, local_max_search_end):
        if flare_smooth[index] <= decay_reference:
            flare_end_index = index
            break
    if flare_end_index <= flare_peak_index + 1:
        flare_end_index = min(len(times), flare_peak_index + 900)

    preflare_end_index = max(flare_start_index, 1)
    preflare_start_index = max(0, preflare_end_index - 2430)
    peak_start_index = max(0, flare_peak_index - 43)
    peak_end_index = min(len(times), flare_peak_index + 68)
    analysis_start_index = max(0, preflare_start_index - 1200)
    analysis_end_index = min(len(times), flare_end_index + 1200)
    postflare_start_index = min(len(times) - 1, flare_end_index)
    postflare_end_index = min(len(times), postflare_start_index + 1200)

    return {
        "analysis": window_dict(times, analysis_start_index, analysis_end_index),
        "pre_flare": window_dict(times, preflare_start_index, preflare_end_index),
        "flare": window_dict(times, flare_start_index, flare_end_index),
        "peak": window_dict(times, peak_start_index, peak_end_index),
        "post_flare": window_dict(times, postflare_start_index, postflare_end_index),
    }


def mean_in_window(values: np.ndarray, window: Dict[str, object]) -> float:
    start_index = int(window["start_index"])
    end_index = int(window["end_index"])
    cut = values[start_index:end_index]
    if len(cut) == 0:
        return 0.0
    return float(sum(cut) / len(cut))


def figure_to_base64(fig: plt.Figure) -> str:
    buffer = BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def build_lightcurves_base64(
    times: List[datetime],
    flux: Dict[float, np.ndarray],
    backgrounds: Dict[float, float],
    analysis_window: Dict[str, object],
    obs_day: str,
) -> str:
    start_index = int(analysis_window["start_index"])
    end_index = int(analysis_window["end_index"])

    fig, ax = plt.subplots(figsize=(12, 7))
    for frequency_hz in FREQUENCIES_HZ:
        ax.plot(
            times[start_index:end_index],
            flux[frequency_hz][start_index:end_index] - backgrounds[frequency_hz],
            linewidth=1,
            label=f"{frequency_hz/1e9:g} GHz",
        )
    ax.set_title(f"NoRP {obs_day} - Lightcurves")
    ax.set_xlabel("Time [UT]")
    ax.set_ylabel("Flux [SFU]")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    return figure_to_base64(fig)


def build_spectrum_base64(frequencies_hz: List[float], flux_sfu: List[float], obs_day: str) -> str:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(frequencies_hz, flux_sfu, marker=".", linestyle="None", markersize=10)
    ax.set_title(f"NoRP {obs_day} - Spectrum")
    ax.set_xlabel("Frequência (Hz)")
    ax.set_ylabel("Densidade de fluxo (SFU)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(0.8e9, 1e11)
    ax.set_ylim(10, 1000)
    ax.grid(True, alpha=0.3)
    return figure_to_base64(fig)


def process_norp_file(filename: str) -> Dict[str, object]:
    filename = str(Path(filename).resolve())
    if not Path(filename).exists():
        raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {filename}")

    times, flux = load_norp_data(filename)
    obs_day = norp_rd_obsDay(filename)
    windows = automatic_flare_windows(times, flux)

    backgrounds = {}
    for frequency_hz in FREQUENCIES_HZ:
        backgrounds[frequency_hz] = mean_in_window(flux[frequency_hz], windows["pre_flare"])

    flare_flux = {}
    for frequency_hz in FREQUENCIES_HZ:
        flare_flux[frequency_hz] = mean_in_window(flux[frequency_hz], windows["peak"]) - backgrounds[frequency_hz]

    spectrum_flux = []
    for frequency_hz in FINAL_FREQUENCIES_HZ:
        spectrum_flux.append(float(flare_flux[frequency_hz]))

    dat_preview = []
    for frequency_hz, value in zip(FINAL_FREQUENCIES_HZ, spectrum_flux):
        dat_preview.append(f"{frequency_hz:.5E} {value:.5E}")

    plots_base64 = {
        "lightcurves_png_base64": build_lightcurves_base64(
            times=times,
            flux=flux,
            backgrounds=backgrounds,
            analysis_window=windows["analysis"],
            obs_day=obs_day,
        ),
        "spectrum_png_base64": build_spectrum_base64(
            frequencies_hz=FINAL_FREQUENCIES_HZ,
            flux_sfu=spectrum_flux,
            obs_day=obs_day,
        ),
    }

    return {
        "filename": filename,
        "obs_day": obs_day,
        "frequencies_hz": FINAL_FREQUENCIES_HZ,
        "flux_sfu": spectrum_flux,
        "backgrounds": {str(key): value for key, value in backgrounds.items()},
        "flare_flux": {str(key): value for key, value in flare_flux.items()},
        "windows": windows,
        "dat_preview": dat_preview,
        "plots_base64": plots_base64,
    }


async def save_upload(upload: UploadFile) -> str:
    suffix = ".fits.gz"
    if upload.filename and upload.filename.endswith(".fit"):
        suffix = ".fit"
    if upload.filename and upload.filename.endswith(".fits"):
        suffix = ".fits"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(await upload.read())
        return temp_file.name

