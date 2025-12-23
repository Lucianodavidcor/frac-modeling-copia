from pydantic import BaseModel, Field

class SimulationParams(BaseModel):
    t_min: float = Field(0.01, description="Tiempo inicial de simulación [días]", gt=0)
    t_max: float = Field(1000.0, description="Tiempo final de simulación [días]", gt=0)
    n_steps: int = Field(50, description="Cantidad de pasos de tiempo (resolución)", ge=10, le=500)