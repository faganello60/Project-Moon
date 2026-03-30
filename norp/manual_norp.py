from __future__ import annotations

import base64
import importlib.util
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


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def nearest_index(times: List[datetime], target: datetime) -> int:
    time_axis = np.array([item.timestamp() for item in times], dtype=float)
    return int(np.argmin(np.abs(time_axis - target.timestamp())))


def window_from_indices(times: List[datetime], start_index: int, end_index: int) -> Dict[str, object]:
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


def window_from_strings(times: List[datetime], start_time: str, end_time: str) -> Dict[str, object]:
    start_index = nearest_index(times, parse_time(start_time))
    end_index = nearest_index(times, parse_time(end_time))
    if end_index <= start_index:
        end_index = start_index + 1
    else:
        end_index += 1
    return window_from_indices(times, start_index, end_index)


def load_norp_data(filename: str) -> Tuple[List[datetime], Dict[float, np.ndarray]]:
    times = list(norp_rd_time(filename))
    flux = {}
    for frequency_hz, reader in FREQUENCY_READERS.items():
        flux[frequency_hz] = np.asarray(reader(filename), dtype=float)
    return times, flux


def automatic_preview_windows(times: List[datetime], flux: Dict[float, np.ndarray]) -> Dict[str, Dict[str, object]]:
    reference = flux[9.4e9]
    smooth = np.convolve(reference, np.ones(11, dtype=float) / 11.0, mode="same")
    peak_index = int(np.argmax(smooth))

    preflare_search_start = max(0, peak_index - 3000)
    preflare_search_end = max(preflare_search_start + 1, peak_index - 600)
    preflare_end_index = preflare_search_start + int(np.argmin(smooth[preflare_search_start:preflare_search_end]))
    preflare_start_index = max(0, preflare_end_index - 2430)

    peak_start_index = max(0, peak_index - 43)
    peak_end_index = min(len(times), peak_index + 68)
    analysis_start_index = max(0, preflare_start_index - 1200)
    analysis_end_index = min(len(times), peak_end_index + 1200)
    postflare_start_index = peak_end_index
    postflare_end_index = min(len(times), postflare_start_index + 1200)

    return {
        "analysis": window_from_indices(times, analysis_start_index, analysis_end_index),
        "pre_flare": window_from_indices(times, preflare_start_index, preflare_end_index),
        "peak": window_from_indices(times, peak_start_index, peak_end_index),
        "post_flare": window_from_indices(times, postflare_start_index, postflare_end_index),
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


def build_background_removed_lightcurve(
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

    ax.set_title(f"NoRP {obs_day} - Background Removed")
    ax.set_xlabel("Time [UT]")
    ax.set_ylabel("Flux [SFU]")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    return figure_to_base64(fig)


def build_spectrum_plot(frequencies_hz: List[float], flux_sfu: List[float], obs_day: str) -> str:
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


async def save_upload(upload: UploadFile) -> str:
    suffix = ".fits.gz"
    if upload.filename and upload.filename.endswith(".fit"):
        suffix = ".fit"
    if upload.filename and upload.filename.endswith(".fits"):
        suffix = ".fits"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(await upload.read())
        return temp_file.name


def validate_upload_filename(filename: str) -> None:
    if not (
        filename.endswith(".fit")
        or filename.endswith(".fits")
        or filename.endswith(".fits.gz")
    ):
        raise HTTPException(
            status_code=400,
            detail="Para gerar curvas de luz e espectro, envie um arquivo .fit, .fits ou .fits.gz.",
        )


def preview_payload(filename: str) -> Dict[str, object]:
    times, flux = load_norp_data(filename)
    obs_day = norp_rd_obsDay(filename)
    windows = automatic_preview_windows(times, flux)

    backgrounds = {}
    for frequency_hz in FREQUENCIES_HZ:
        backgrounds[frequency_hz] = mean_in_window(flux[frequency_hz], windows["pre_flare"])

    image_base64 = build_background_removed_lightcurve(
        times=times,
        flux=flux,
        backgrounds=backgrounds,
        analysis_window=windows["analysis"],
        obs_day=obs_day,
    )

    return {
        "obs_day": obs_day,
        "suggested_windows": windows,
        "backgrounds": {str(key): value for key, value in backgrounds.items()},
        "background_removed_lightcurve_png_base64": image_base64,
    }


def final_payload(filename: str, pre_flare_start: str, pre_flare_end: str, peak_start: str, peak_end: str) -> Dict[str, object]:
    times, flux = load_norp_data(filename)
    obs_day = norp_rd_obsDay(filename)

    pre_flare_window = window_from_strings(times, pre_flare_start, pre_flare_end)
    peak_window = window_from_strings(times, peak_start, peak_end)

    backgrounds = {}
    for frequency_hz in FREQUENCIES_HZ:
        backgrounds[frequency_hz] = mean_in_window(flux[frequency_hz], pre_flare_window)

    flare_flux = {}
    for frequency_hz in FREQUENCIES_HZ:
        flare_flux[frequency_hz] = mean_in_window(flux[frequency_hz], peak_window) - backgrounds[frequency_hz]

    final_flux = []
    for frequency_hz in FINAL_FREQUENCIES_HZ:
        final_flux.append(float(flare_flux[frequency_hz]))

    dat_preview = []
    for frequency_hz, value in zip(FINAL_FREQUENCIES_HZ, final_flux):
        dat_preview.append(f"{frequency_hz:.5E} {value:.5E}")

    spectrum_base64 = build_spectrum_plot(FINAL_FREQUENCIES_HZ, final_flux, obs_day)

    return {
        "obs_day": obs_day,
        "pre_flare_window": pre_flare_window,
        "peak_window": peak_window,
        "backgrounds": {str(key): value for key, value in backgrounds.items()},
        "flare_flux": {str(key): value for key, value in flare_flux.items()},
        "frequencies_hz": FINAL_FREQUENCIES_HZ,
        "flux_sfu": final_flux,
        "dat_preview": dat_preview,
        "spectrum_png_base64": spectrum_base64,
    }
