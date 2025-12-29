from pydantic import BaseModel
from typing import List, Optional

class WellCreate(BaseModel):
    name: str
    length: float
    n_f: int
    rw: float
    k_mi: float; phi_mi: float; ct_mi: float; sigma_i: float
    k_fi: float; phi_fi: float; ct_fi: float
    xf: float; wf: float; kf: float

class ProjectCreate(BaseModel):
    name: str
    h: float; mu: float; b_factor: float; initial_pressure: float
    k_mo: float; phi_mo: float; ct_mo: float; sigma_o: float
    k_fo: float; phi_fo: float; ct_fo: float