from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.well_models import Project, Well
from app.schemas.well_schemas import ProjectCreate, ProjectResponse, WellCreate, WellResponse

router = APIRouter()

# --- Rutas de PROYECTOS ---

@router.post("/projects/", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    # 1. Verificar si ya existe un proyecto con ese nombre
    db_project = db.query(Project).filter(Project.name == project.name).first()
    if db_project:
        raise HTTPException(status_code=400, detail="Ya existe un proyecto con ese nombre.")
    
    # 2. Crear la instancia del modelo DB
    new_project = Project(**project.model_dump())
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

@router.get("/projects/", response_model=List[ProjectResponse])
def read_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    projects = db.query(Project).offset(skip).limit(limit).all()
    return projects

@router.get("/projects/{project_id}", response_model=ProjectResponse)
def read_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project

# --- Rutas de POZOS (Anidados en Proyectos) ---

@router.post("/projects/{project_id}/wells/", response_model=WellResponse)
def create_well_for_project(
    project_id: int, 
    well: WellCreate, 
    db: Session = Depends(get_db)
):
    # 1. Verificar que el proyecto exista
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # 2. Crear el pozo vinculado
    new_well = Well(**well.model_dump(), project_id=project_id)
    db.add(new_well)
    db.commit()
    db.refresh(new_well)
    return new_well