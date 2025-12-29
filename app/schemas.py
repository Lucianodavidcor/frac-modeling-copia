from pydantic import BaseModel, Field
from typing import Optional, List

class ProductionScheduleCreate(BaseModel):
    time_days: float = Field(..., description="Tiempo desde el inicio (días)")
    rate_stbd: Optional[float] = Field(None, description="Tasa de petróleo (STB/D)")
    pwf_psi: Optional[float] = Field(None, description="Presión de fondo (psi)")

class WellCreate(BaseModel):
    name: str
    length: float
    n_f: int
    rw: float
    spacing: float = Field(..., description="Distancia al pozo vecino o borde (ft)")
    
    # Inner Reservoir (SRV)
    k_mi: float
    phi_mi: float
    ct_mi: float
    sigma_i: float
    k_fi: float
    phi_fi: float
    ct_fi: float
    
    # Hydraulic Fracture (HF)
    xf: float
    wf: float
    kf: float

class ProjectCreate(BaseModel):
    name: str
    h: float
    mu: float
    b_factor: float
    initial_pressure: float
    
    # Outer Reservoir (ORV)
    k_mo: float
    phi_mo: float
    ct_mo: float
    sigma_o: float
    k_fo: float
    phi_fo: float
    ct_fo: float