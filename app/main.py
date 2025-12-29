from fastapi import FastAPI
from app.database import init_db
from app.models import Project # Importado para que SQLModel lo reconozca al crear tablas

app = FastAPI(
    title="Reservoir Multi-Well API (SPE-215031-PA)",
    description="Thought Partner: API para modelos de flujo trilineal en reservorios no convencionales.",
    version="0.1.0"
)

@app.on_event("startup")
async def on_startup():
    """Ejecutado al iniciar la aplicación."""
    await init_db()

@app.get("/health", tags=["Infraestructura"])
async def health_check():
    """Verifica la disponibilidad de la API."""
    return {
        "status": "online",
        "model": "SPE-215031-PA",
        "description": "Pressure- and Rate-Transient Model for Interfering Wells"
    }