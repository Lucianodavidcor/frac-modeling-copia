from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

# --- MODELO DE PROYECTO (Reservorio y ORV) ---

class Project(SQLModel, table=True):
    """
    Representa el sector de reservorio y propiedades del Outer Reservoir (ORV).
    Contiene la información de la roca virgen y propiedades globales.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    
    # Datos Reservorio Global
    h: float = Field(description="Thickness (ft)")
    mu: float = Field(description="Viscosity (cp)")
    b_factor: float = Field(description="Formation Volume Factor (rb/stb)")
    initial_pressure: float = Field(description="Initial Pressure (psi)")
    
    # Datos ORV (Outer Reservoir) - Matriz y Fractura Natural
    k_mo: float = Field(description="ORV Matrix Permeability (md)")
    phi_mo: float = Field(description="ORV Matrix Porosity (frac)")
    ct_mo: float = Field(description="ORV Matrix Compressibility (1/psi)")
    sigma_o: float = Field(description="ORV Shape Factor (ft-2)")
    k_fo: float = Field(description="ORV Natural Fracture Permeability (md)")
    phi_fo: float = Field(description="ORV Natural Fracture Porosity (frac)")
    ct_fo: float = Field(description="ORV Natural Fracture Compressibility (1/psi)")

    # Relaciones
    wells: List["Well"] = Relationship(back_populates="project")


# --- MODELO DE POZO (SRV y HF) ---

class Well(SQLModel, table=True):
    """
    Representa un pozo horizontal con su SRV y sus fracturas hidráulicas.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    name: str
    
    # Geometría y Ubicación
    length: float = Field(description="Well length (ft)")
    n_f: int = Field(description="Number of fractures")
    rw: float = Field(description="Wellbore radius (ft)")
    spacing: float = Field(default=500.0, description="Distance to neighbor or boundary (ft)")
    
    # Datos SRV (Inner Reservoir) - Matriz y Fractura Natural
    k_mi: float = Field(description="SRV Matrix Perm (md)")
    phi_mi: float = Field(description="SRV Matrix Porosity (frac)")
    ct_mi: float = Field(description="SRV Matrix Comp (1/psi)")
    sigma_i: float = Field(description="SRV Shape Factor (ft-2)")
    k_fi: float = Field(description="SRV Natural Frac Perm (md)")
    phi_fi: float = Field(description="SRV Natural Frac Porosity (frac)")
    ct_fi: float = Field(description="SRV Natural Frac Comp (1/psi)")
    
    # Datos HF (Hydraulic Fracture)
    xf: float = Field(description="HF Half-length (ft)")
    wf: float = Field(description="HF width (ft)")
    kf: float = Field(description="HF permeability (md)")
    c_wellbore: float = Field(default=0.0, description="Wellbore storage (bbl/psi)")

    # Relaciones
    project: Project = Relationship(back_populates="wells")
    schedules: List["ProductionSchedule"] = Relationship(back_populates="well")


# --- MODELO DE CRONOGRAMA DE PRODUCCIÓN ---

class ProductionSchedule(SQLModel, table=True):
    """
    Define los cambios de tasa o presión en el tiempo para cada pozo.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    well_id: int = Field(foreign_key="well.id")
    time_days: float = Field(description="Time since production start (days)")
    rate_stbd: Optional[float] = Field(default=None, description="Oil rate (STB/D)")
    pwf_psi: Optional[float] = Field(default=None, description="Bottomhole flowing pressure (psi)")

    well: Well = Relationship(back_populates="schedules")