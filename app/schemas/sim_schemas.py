from pydantic import BaseModel, Field
from typing import List, Optional

# ================= INPUT SCHEMAS =================

class SimulationConfig(BaseModel):
    """
    Parámetros de configuración para ejecutar la simulación.
    Se envían en el cuerpo del POST request.
    """
    project_id: int = Field(..., description="ID del proyecto a simular")
    t_min: float = Field(1e-3, description="Tiempo inicial en días (logarítmico)", gt=0)
    t_max: float = Field(1000.0, description="Tiempo final en días", gt=0)
    n_steps: int = Field(50, description="Número de pasos de tiempo (resolución de Stehfest)", gt=5, le=500)

# ================= OUTPUT SCHEMAS =================

class SimWellResult(BaseModel):
    """
    Resultados específicos para un pozo individual.
    """
    well_id: int
    name: str
    # IMPORTANTE: List[float] para devolver la serie de tiempo completa
    pressure_drop_psi: List[float] = Field(..., description="Caída de presión calculada en cada paso de tiempo")

class SimulationResponse(BaseModel):
    """
    Respuesta completa de la simulación.
    Contiene el eje temporal compartido y los resultados por pozo.
    """
    time_days: List[float] = Field(..., description="Vector de tiempos en días (Eje X)")
    wells: List[SimWellResult] = Field(..., description="Resultados agrupados por pozo")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "time_days": [0.001, 0.01, 0.1, 1.0],
                "wells": [
                    {
                        "well_id": 1,
                        "name": "Pozo-1",
                        "pressure_drop_psi": [10.5, 50.2, 120.5, 300.0]
                    }
                ]
            }
        }