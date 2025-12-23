from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.well_models import Project, Well
from app.schemas import well_schemas

router = APIRouter()

# --- ENDPOINTS PARA PROYECTOS (PADS) ---

@router.post("/", response_model=well_schemas.ProjectResponse)
def create_project(project_in: well_schemas.ProjectCreate, db: Session = Depends(get_db)):
    """Crea un nuevo proyecto (Pad) con sus propiedades base."""
    # Verificamos si ya existe un proyecto con el mismo nombre
    existing = db.query(Project).filter(Project.name == project_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="El nombre del proyecto ya existe.")
    
    # Creamos la instancia del modelo. **project_in.model_dump() expande todos los campos
    # incluyendo phi, ct, mu, k_ref, h, omega y lam.
    new_project = Project(**project_in.model_dump())
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

@router.get("/", response_model=List[well_schemas.ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    """Lista todos los proyectos disponibles."""
    return db.query(Project).all()

@router.get("/{project_id}", response_model=well_schemas.ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Obtiene el detalle de un proyecto y sus pozos asociados."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project

# --- ENDPOINTS PARA POZOS (WELLS) ---

@router.post("/{project_id}/wells", response_model=well_schemas.WellResponse)
def create_well(
    project_id: int, 
    well_in: well_schemas.WellCreate, 
    db: Session = Depends(get_db)
):
    """
    Agrega un pozo a un proyecto. 
    Aquí se recibe 'r_w' y las propiedades SRV desde el esquema WellCreate.
    """
    # 1. Verificar si el proyecto existe
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # 2. Crear el pozo. **well_in.model_dump() incluye automáticamente r_w,
    # spacing, x_f, n_f, t_0, y las propiedades SRV opcionales.
    new_well = Well(**well_in.model_dump(), project_id=project_id)
    
    db.add(new_well)
    db.commit()
    db.refresh(new_well)
    return new_well

@router.delete("/{project_id}/wells/{well_id}")
def delete_well(project_id: int, well_id: int, db: Session = Depends(get_db)):
    """Elimina un pozo específico de un proyecto."""
    well = db.query(Well).filter(Well.id == well_id, Well.project_id == project_id).first()
    if not well:
        raise HTTPException(status_code=404, detail="Pozo no encontrado")
    
    db.delete(well)
    db.commit()
    return {"detail": "Pozo eliminado correctamente"}