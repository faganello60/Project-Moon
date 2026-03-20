from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
try:
    from gsync import gsync_api
except ImportError:
    gsync_api = None
from gsync import gsync_api_python
from lmfit import Parameters
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ParamModel(BaseModel):
    value: float
    vary: bool = True
    min: Optional[float] = None
    max: Optional[float] = None

class GSyncRequest(BaseModel):
    prefix:str
    freq: list[float]
    sfu: list[float]
    viewAngle: float
    height: float
    j1: int
    j2: int
    etr: float
    np: float
    params: Dict[str, ParamModel]

@app.post("/gsync")
async def gsync_endpoint(request: GSyncRequest):
    if gsync_api is None:
        raise HTTPException(status_code=500, detail="The compiled high-performance extension is not available for your system. Please use 'INITIALIZE SIMULATION (PYTHON) BETA' instead, or recompile the extension.")
    
    # Convert parameters to lmfit.Parameters
    lmfit_params = Parameters()
    for name, p in request.params.items():
        # lmfit Parameters handle None as +/- inf
        lmfit_params.add(name, value=p.value, vary=p.vary, min=p.min, max=p.max)
    
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
    
@app.post("/python/gsync")
async def gsync_endpoint(request: GSyncRequest):
    # Convert parameters to lmfit.Parameters
    lmfit_params = Parameters()
    for name, p in request.params.items():
        # lmfit Parameters handle None as +/- inf
        lmfit_params.add(name, value=p.value, vary=p.vary, min=p.min, max=p.max)
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
