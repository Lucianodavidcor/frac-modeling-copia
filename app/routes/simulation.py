from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.database import get_session
from app.models import Project, Well
from app.solver import TrilinearSolver

router = APIRouter(prefix="/simulate", tags=["Cálculo"])

@router.post("/{project_id}")
async def run_simulation(project_id: int, session: AsyncSession = Depends(get_session)):
    # 1. Obtener datos del proyecto
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # 2. Obtener pozos asociados
    result_wells = await session.execute(select(Well).where(Well.project_id == project_id).order_by(Well.id))
    wells = result_wells.scalars().all()
    
    if not wells:
        raise HTTPException(status_code=400, detail="El proyecto no tiene pozos")

    # 3. Ejecutar el Solver
    solver = TrilinearSolver(project, wells)
    t_interes = 30.0 # Calculamos a 30 días
    
    try:
        pressures = solver.stehfest_inversion(t_interes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el cálculo: {str(e)}")
    
    # 4. Formatear respuesta
    well_results = {}
    for i, p_val in enumerate(pressures):
        well_results[wells[i].name] = p_val

    return {
        "project": project.name,
        "days": t_interes,
        "results": well_results,
        "unit": "psi"
    }