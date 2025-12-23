from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

# --- Schemas para POZOS (Wells) ---

class WellBase(BaseModel):
    name: str = Field(..., example="Pozo Hijo 1")
    # Geometría y Tiempo
    spacing_x: float = Field(..., description="Distancia relativa en X [ft]", example=0.0)
    spacing_y: float = Field(..., description="Distancia relativa en Y [ft]", example=660.0)
    x_f: float = Field(..., description="Medio-ancho de fractura [ft]", gt=0)
    n_f: int = Field(..., description="Número de fracturas", gt=0)
    t_0: float = Field(0.0, description="Tiempo de inicio de producción [días] (0 = Padre)", ge=0)
    conductivity: float = Field(..., description="Conductividad adimensional (C_fD)")

    # Propiedades SRV Específicas (Opcionales)
    k_srv: Optional[float] = Field(None, description="Permeabilidad SRV específica [md]. Si se omite, usa la del Proyecto.")
    phi_srv: Optional[float] = Field(None, description="Porosidad SRV específica. Si se omite, usa la del Proyecto.")
    omega_srv: Optional[float] = Field(None, description="Omega SRV específico.")
    lam_srv: Optional[float] = Field(None, description="Lambda SRV específico.")

class WellCreate(WellBase):
    pass

class WellResponse(WellBase):
    id: int
    project_id: int
    
    model_config = ConfigDict(from_attributes=True)


# --- Schemas para PROYECTOS (Pads) ---

class ProjectBase(BaseModel):
    name: str = Field(..., example="Pad Vaca Muerta 01")
    description: Optional[str] = None
    
    # Propiedades Físicas Globales (Base)
    phi: float = Field(..., description="Porosidad Base (fracción)", gt=0, le=1)
    ct: float = Field(..., description="Compresibilidad Total [1/psi]", gt=0)
    mu: float = Field(..., description="Viscosidad del fluido [cp]", gt=0)
    k_ref: float = Field(..., description="Permeabilidad de referencia Base [md]", gt=0)
    h: float = Field(..., description="Espesor de reservorio [ft]", gt=0)
    B: float = Field(1.0, description="Factor volumétrico", gt=0)

    # Parámetros Doble Porosidad Globales
    omega: float = Field(1.0, description="Storativity Base (1 = porosidad simple)", ge=0, le=1)
    lam: float = Field(0.0, description="Interporosity Base (0 = sin flujo cruzado)", ge=0)

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    wells: List[WellResponse] = []

    model_config = ConfigDict(from_attributes=True)