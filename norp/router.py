import os
from typing import Dict

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from .manual_norp import (
    final_payload,
    preview_payload,
    save_upload as save_manual_upload,
    validate_upload_filename,
)

from .norp import (
    process_norp_file,
    save_upload as save_norp_upload,
)

router = APIRouter()


@router.post("/norp/analyze")
async def analyze_norp_file(file: UploadFile = File(...)) -> Dict[str, object]:
    if not file.filename or not (
        file.filename.endswith(".fit")
        or file.filename.endswith(".fits")
        or file.filename.endswith(".fits.gz")
    ):
        raise HTTPException(status_code=400, detail="Envie um arquivo .fit, .fits ou .fits.gz.")

    temp_filename = await save_norp_upload(file)
    try:
        return process_norp_file(temp_filename)
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    
# 

@router.post("/norp/manual/preview")
async def preview_manual_norp(file: UploadFile = File(...)) -> Dict[str, object]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo não enviado.")
    validate_upload_filename(file.filename)

    temp_filename = await save_manual_upload(file)
    try:
        return preview_payload(temp_filename)
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

@router.post("/norp/manual/final")
async def final_manual_norp(
    file: UploadFile = File(...),
    pre_flare_start: str = Form(...),
    pre_flare_end: str = Form(...),
    peak_start: str = Form(...),
    peak_end: str = Form(...),
) -> Dict[str, object]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo não enviado.")
    validate_upload_filename(file.filename)

    temp_filename = await save_manual_upload(file)
    try:
        return final_payload(
            filename=temp_filename,
            pre_flare_start=pre_flare_start,
            pre_flare_end=pre_flare_end,
            peak_start=peak_start,
            peak_end=peak_end,
        )
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
