from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from . import analyze_sensitivity
import json

router = APIRouter()

class ParameterImpactRequest(BaseModel):
    viewAngle: float
    height: float
    emin: float
    emax: float
    etr: float
    np: float
    delta: List[float]
    nelectron: List[float]
    bmag: List[float]
    asize: List[float]

@router.post("/parameterImpact")
async def analyze_sensitivity_endpoint(request: ParameterImpactRequest):

    try:
        check_arrays(request.delta, request.nelectron, request.bmag, request.asize)
        result_json = analyze_sensitivity.parameter_impact(
            view_angle=request.viewAngle,
            height=request.height,
            emin=request.emin,
            emax=request.emax,
            etr=request.etr,
            plasma_np=request.np,
            delta=request.delta,
            nelectron=request.nelectron,
            bmag=request.bmag,
            asize=request.asize
        )
        return {
            "status": "success",
            "data": json.loads(result_json),
    }
    except ValueError as e:
      raise HTTPException(status_code=400, detail=str(e))  

def check_arrays(*arrays):
    # Validation of empty arrays: No array can be empty.
    for i, arr in enumerate(arrays):
        if len(arr) == 0:
            raise ValueError("Nenhum array pode estar vazio")

    # Multiple element validation: An array can have a maximum size greater than 1.
    value = sum(1 for arr in arrays if len(arr) > 1)
    
    if value > 1:
        raise ValueError("Atualmente só é permitido testar uma váriável por vez")