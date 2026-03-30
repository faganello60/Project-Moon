from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from gsync.router import router as gsync_router
from norp.router import router as norp_router
from parameters_study.router import router as sensitivity_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gsync_router)
app.include_router(sensitivity_router)
app.include_router(norp_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
