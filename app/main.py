from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import projects, simulation  # <--- Importamos simulation

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/api/v1/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir Routers
app.include_router(projects.router, prefix="/api/v1", tags=["Projects & Wells"])
app.include_router(simulation.router, prefix="/api/v1", tags=["Simulation Engine"]) # <--- Registramos aquí

@app.get("/")
def root():
    return {"message": "API de Simulación Activa", "docs": "/docs"}