import tempfile
import os

from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from . import norp
from .RequestModel.AnalyzeRangeRequestModel import AnalyzeRangeRequestModel
from .RequestModel.RemoveBGNoiseRequestModel import RemoveBGNoiseRequestModel
from .RequestModel.FlareRequestModel import FlareRequestModel
from .RequestModel.SpectrumRequestModel import SpectrumRequestModel

router = APIRouter(prefix="/norp", tags=["norp"])

def _to_json_safe(value):
    if isinstance(value, dict):
        return {key: _to_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_json_safe(item) for item in value]
    if isinstance(value, datetime):
        return int(value.timestamp() * 1000)
    if hasattr(value, "tolist"):
        return _to_json_safe(value.tolist())
    if hasattr(value, "item"):
        return value.item()
    return value

@router.post("/analyze")
async def analyze_endpoint(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo não enviado.")

    filename = None
    try:
        filename = await save_upload(file)
        data = norp.get_data(filename)
        frequencies = norp.get_available_frequencies(filename)
        light_curves = norp.get_full_light_curves(filename)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
          if filename and os.path.exists(filename):
              os.remove(filename)

    return {
        "status": "success",
        "frequencies": frequencies,
        "date_information": data,
        "light_curves": _to_json_safe(light_curves)
    }

@router.post("/analyze-range")
async def analyze_range_endpoint(
    request: Annotated[AnalyzeRangeRequestModel, Depends(AnalyzeRangeRequestModel.as_form)],
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo não enviado.")

    filename = None
    try:
        filename = await save_upload(file)
        light_curves = norp.get_range_light_curves(
            filename,
            request.start_time,
            request.end_time,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)

    return {
        "status": "success",
        "light_curves": _to_json_safe(light_curves)
    }

@router.post("/remove-background-noise")
async def remove_background_endpoint(
    request: Annotated[RemoveBGNoiseRequestModel, Depends(RemoveBGNoiseRequestModel.as_form)],
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo não enviado.")

    filename = None
    try:
        filename = await save_upload(file)
        light_curves = norp.remove_background_noise(
            filename,
            request.start_time,
            request.end_time,
            request.pre_flare_start,
            request.pre_flare_end,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)

    return {
        "status": "success",
        "light_curves": _to_json_safe(light_curves)
    }

@router.post("/flare-peak")
async def flare_peak_endpoint(
    request: Annotated[FlareRequestModel, Depends(FlareRequestModel.as_form)],
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo não enviado.")

    filename = None
    try:
        filename = await save_upload(file)
        flare_peaks = norp.get_flare_peak(
            filename,
            request.flare_start,
            request.flare_end,
            request.background_averages,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)

    return {
        "status": "success",
        "flare_peaks": _to_json_safe(flare_peaks),
    }

@router.post("/remove-frequencies")
async def remove_frequencies_endpoint(
    request: Annotated[SpectrumRequestModel, Depends(SpectrumRequestModel.as_form)],
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo não enviado.")

    filename = None
    try:
        filename = await save_upload(file)
        spectrum = norp.remove_spectrum_frequencies(
            filename,
            request.frequencies,
            request.fluxes,
            request.frequencies_to_remove,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)

    return {
        "status": "success",
        "spectrum": _to_json_safe(spectrum),
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
