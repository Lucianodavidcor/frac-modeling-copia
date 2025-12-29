from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models import Project, Well, ProductionSchedule
from app.schemas import ProjectCreate, WellCreate, ProductionScheduleCreate

router = APIRouter(prefix="/projects", tags=["Ingeniería"])

@router.post("/", response_model=Project)
async def create_project(data: ProjectCreate, session: AsyncSession = Depends(get_session)):
    db_project = Project(**data.model_dump())
    session.add(db_project)
    await session.commit()
    await session.refresh(db_project)
    return db_project

@router.post("/{project_id}/wells", response_model=Well)
async def add_well(project_id: int, data: WellCreate, session: AsyncSession = Depends(get_session)):
    db_project = await session.get(Project, project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    db_well = Well(**data.model_dump(), project_id=project_id)
    session.add(db_well)
    await session.commit()
    await session.refresh(db_well)
    return db_well

@router.post("/wells/{well_id}/schedules", response_model=ProductionSchedule)
async def add_production_step(well_id: int, data: ProductionScheduleCreate, session: AsyncSession = Depends(get_session)):
    """Agrega un cambio de tasa de producción para un pozo específico en un tiempo dado."""
    db_well = await session.get(Well, well_id)
    if not db_well:
        raise HTTPException(status_code=404, detail="Pozo no encontrado")
    db_schedule = ProductionSchedule(**data.model_dump(), well_id=well_id)
    session.add(db_schedule)
    await session.commit()
    await session.refresh(db_schedule)
    return db_schedule