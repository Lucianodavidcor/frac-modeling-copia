from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    # Datos Reservorio Global [cite: 454]
    h: float = Field(description="Thickness (ft)")
    mu: float = Field(description="Viscosity (cp)")
    b_factor: float = Field(description="FVF (rb/stb)")
    initial_pressure: float = Field(description="Pini (psi)")
    # Datos ORV (Outer Reservoir) [cite: 99, 454]
    k_mo: float = Field(description="Matrix Perm (md)")
    phi_mo: float = Field(description="Matrix Porosity (frac)")
    ct_mo: float = Field(description="Matrix Compressibility (1/psi)")
    sigma_o: float = Field(description="Shape Factor (ft-2)")
    k_fo: float = Field(description="Nat. Frac Perm (md)")
    phi_fo: float = Field(description="Nat. Frac Porosity (frac)")
    ct_fo: float = Field(description="Nat. Frac Compressibility (1/psi)")

    wells: List["Well"] = Relationship(back_populates="project")

class Well(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    name: str
    length: float = Field(description="Well length (ft)")
    n_f: int = Field(description="Number of fractures")
    rw: float = Field(description="Wellbore radius (ft)")
    # Datos SRV (Inner Reservoir) [cite: 98, 454]
    k_mi: float = Field(description="SRV Matrix Perm (md)")
    phi_mi: float = Field(description="SRV Matrix Porosity (frac)")
    ct_mi: float = Field(description="SRV Matrix Comp (1/psi)")
    sigma_i: float = Field(description="SRV Shape Factor (ft-2)")
    k_fi: float = Field(description="SRV Nat. Frac Perm (md)")
    phi_fi: float = Field(description="SRV Nat. Frac Porosity (frac)")
    ct_fi: float = Field(description="SRV Nat. Frac Comp (1/psi)")
    # Datos HF (Hydraulic Fracture) [cite: 33, 454]
    xf: float = Field(description="HF Half-length (ft)")
    wf: float = Field(description="HF width (ft)")
    kf: float = Field(description="HF permeability (md)")

    project: Project = Relationship(back_populates="wells")