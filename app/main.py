from fastapi import FastAPI
from app.database import init_db
from app.routes import project

app = FastAPI(
    title="Reservoir Multi-Well API (SPE-215031-PA)",
    description="API para modelos de flujo trilineal y análisis de interferencia.",
    version="1.0.0"
)

@app.on_event("startup")
async def on_startup():
    await init_db()

# Incluimos las nuevas rutas de ingeniería
app.include_router(project.router)

@app.get("/health", tags=["Infraestructura"])
async def health_check():
    return {"status": "online", "model": "SPE-215031-PA"}