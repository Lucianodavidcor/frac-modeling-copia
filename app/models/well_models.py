from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    
    # --- Propiedades Globales (Roca Matriz Original / Fallback) ---
    phi = Column(Float)       # Porosidad Matriz
    ct = Column(Float)        # Compresibilidad total
    mu = Column(Float)        # Viscosidad
    k_ref = Column(Float)     # Permeabilidad de referencia (k_m)
    h = Column(Float)         # Espesor
    B = Column(Float, default=1.0) # Factor volumétrico
    
    # Parámetros de Doble Porosidad Globales
    omega = Column(Float, default=1.0) 
    lam = Column(Float, default=0.0)

    wells = relationship("Well", back_populates="project")

class Well(Base):
    __tablename__ = "wells"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    project_id = Column(Integer, ForeignKey("projects.id"))
    
    # --- Geometría y Tiempo ---
    spacing_x = Column(Float) # Coordenada X relativa
    spacing_y = Column(Float) # Coordenada Y relativa (Espaciamiento)
    x_f = Column(Float)       # Longitud de media fractura
    n_f = Column(Integer)     # Número de fracturas
    r_w = Column(Float, default=0.3) # Radio de pozo (ft)
    t_0 = Column(Float, default=0.0) # Tiempo de inicio (0=Padre, >0=Hijo)
    conductivity = Column(Float) # C_fD o conductividad de fractura

    # --- Propiedades SRV Específicas del Pozo (Opcionales) ---
    # Si estos valores son NULL, el sistema usará los del Project (k_ref, phi, etc.)
    k_srv = Column(Float, nullable=True)     # Permeabilidad del SRV de este pozo
    phi_srv = Column(Float, nullable=True)   # Porosidad del SRV de este pozo
    omega_srv = Column(Float, nullable=True) # Omega específico del SRV
    lam_srv = Column(Float, nullable=True)   # Lambda específico del SRV

    project = relationship("Project", back_populates="wells")