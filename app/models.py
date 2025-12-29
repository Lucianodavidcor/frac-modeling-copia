from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

# --- MODELO DE PROYECTO (Reservorio Global y ORV) ---

class Project(SQLModel, table=True):
    """
    Representa el sector de reservorio y propiedades del Outer Reservoir (ORV).
    Basado en las definiciones de reservorio virgen del paper[cite: 31, 66].
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    
    # Propiedades del Fluido y Formación [cite: 454]
    h: float = Field(description="Espesor de la formación (ft)")
    mu: float = Field(description="Viscosidad del fluido (cp)")
    b_factor: float = Field(description="Factor volumétrico (rb/stb)")
    initial_pressure: float = Field(description="Presión inicial (psi)")
    
    # Outer Reservoir (ORV) - Propiedades de Matriz [cite: 454]
    k_mo: float = Field(description="Permeabilidad de matriz ORV (md)")
    phi_mo: float = Field(description="Porosidad de matriz ORV (frac)")
    ct_mo: float = Field(description="Compresibilidad total matriz ORV (1/psi)")
    sigma_o: float = Field(description="Factor de forma matriz ORV (ft^-2)")
    
    # Outer Reservoir (ORV) - Propiedades de Fractura Natural [cite: 454]
    k_fo: float = Field(description="Permeabilidad de fractura natural ORV (md)")
    phi_fo: float = Field(description="Porosidad de fractura natural ORV (frac)")
    ct_fo: float = Field(description="Compresibilidad total fractura ORV (1/psi)")

    wells: List["Well"] = Relationship(back_populates="project")

# --- MODELO DE POZOS (Well, HF y SRV) ---

class Well(SQLModel, table=True):
    """
    Representa un pozo horizontal con su zona estimulada (SRV/Inner Reservoir).
    Contiene la geometría y las propiedades de las fracturas hidráulicas (HF) [cite: 60-65, 454].
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    name: str
    
    # Geometría y Espaciamiento [cite: 60, 94, 454]
    length: float = Field(description="Longitud horizontal del pozo (ft)")
    n_f: int = Field(description="Número de fracturas hidráulicas (nF)")
    rw: float = Field(description="Radio del pozo (ft)")
    spacing: float = Field(description="Espaciamiento lateral entre pozos (ft)")
    
    # Inner Reservoir (SRV) - Propiedades de Matriz [cite: 454]
    k_mi: float = Field(description="Permeabilidad de matriz SRV (md)")
    phi_mi: float = Field(description="Porosidad de matriz SRV (frac)")
    ct_mi: float = Field(description="Compresibilidad total matriz SRV (1/psi)")
    sigma_i: float = Field(description="Factor de forma matriz SRV (ft^-2)")
    
    # Inner Reservoir (SRV) - Propiedades de Fractura Natural [cite: 454]
    k_fi: float = Field(description="Permeabilidad de fractura natural SRV (md)")
    phi_fi: float = Field(description="Porosidad de fractura natural SRV (frac)")
    ct_fi: float = Field(description="Compresibilidad total fractura SRV (1/psi)")

    # Propiedades de la Fractura Hidráulica (HF) [cite: 235, 454]
    xf: float = Field(description="Media longitud de la HF (ft)")
    wf: float = Field(description="Ancho/apertura de la HF (ft)")
    kf: float = Field(description="Permeabilidad de la HF (md)")

    project: Project = Relationship(back_populates="wells")
    schedules: List["ProductionSchedule"] = Relationship(back_populates="well")

# --- MODELO DE CRONOGRAMA (Tasas/Presiones Variables) ---

class ProductionSchedule(SQLModel, table=True):
    """
    Permite definir condiciones de producción no sincrónicas y cierres[cite: 14, 525].
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    well_id: int = Field(foreign_key="well.id")
    time_days: float = Field(description="Tiempo de inicio del periodo (días)")
    rate_stbd: Optional[float] = Field(default=None, description="Tasa de producción (STB/D)")
    pwf_psi: Optional[float] = Field(default=None, description="Presión de fondo fluyente (psi)")

    well: Well = Relationship(back_populates="schedules")