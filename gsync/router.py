from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from lmfit import Parameters
import json

try:
    from gsync import gsync_api
except ImportError:
    gsync_api = None
from gsync import gsync_api_python

router = APIRouter()

class ParamModel(BaseModel):
    value: float
    vary: bool = True
    min: Optional[float] = None
    max: Optional[float] = None

class GSyncRequest(BaseModel):
    prefix: str
    freq: list[float]
    sfu: list[float]
    viewAngle: float
    height: float
    j1: int
    j2: int
    etr: float
    np: float
    params: Dict[str, ParamModel]

@router.post("/gsync")
async def gsync_endpoint(request: GSyncRequest):
    if gsync_api is None:
        raise HTTPException(status_code=500, detail="The compiled high-performance extension is not available for your system. Please use 'INITIALIZE SIMULATION (PYTHON) BETA' instead, or recompile the extension.")
    
    # Convert parameters to lmfit.Parameters
    lmfit_params = Parameters()
    for name, p in request.params.items():
        # lmfit Parameters handle None as +/- inf
        if p.vary:
            lmfit_params.add(name, value=p.value, vary=p.vary, min=p.min, max=p.max)
        else:
            lmfit_params.add(name, value=p.value, vary=p.vary)

    try:
        # # Run the simulation
        result_json = gsync_api.run_gsync(
            freq=request.freq,
            sfu=request.sfu,
            view_angle=request.viewAngle,
            height=request.height,
            j1=request.j1,
            j2=request.j2,
            etr=request.etr,
            plasma_np=request.np,
            params=lmfit_params,
            prefix=request.prefix
        )

        return {
            "status": "success",
            "data": json.loads(result_json),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/python/gsync")
async def python_gsync_endpoint(request: GSyncRequest):
    # Convert parameters to lmfit.Parameters
    lmfit_params = Parameters()
    for name, p in request.params.items():
        if p.vary:
            lmfit_params.add(name, value=p.value, vary=p.vary, min=p.min, max=p.max)
        else:
            lmfit_params.add(name, value=p.value, vary=p.vary)
    
    try:
        # # Run the simulation
        result_json = gsync_api_python.run_gsync(
            freq=request.freq,
            sfu=request.sfu,
            view_angle=request.viewAngle,
            height=request.height,
            j1=request.j1,
            j2=request.j2,
            etr=request.etr,
            plasma_np=request.np,
            params=lmfit_params,
            prefix=request.prefix
        )

        return {
            "status": "success",
            "data": json.loads(result_json),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
