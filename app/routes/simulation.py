from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.database import get_session
from app.models import Project, Well
from app.solver import TrilinearSolver

router = APIRouter(prefix="/simulate", tags=["Cálculo"])

@router.post("/{project_id}")
async def run_simulation(project_id: int, session: AsyncSession = Depends(get_session)):
    """
    Calcula la presión en los pozos para un punto fijo de 30 días.
    Útil para verificaciones rápidas.
    """
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
    t_interes = 30.0
    
    try:
        pressures = solver.stehfest_inversion(t_interes)
    except Exception as e:
        # Capturamos errores numéricos (como matrices singulares)
        raise HTTPException(status_code=500, detail=f"Error en el cálculo numérico: {str(e)}")
    
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

@router.post("/{project_id}/curve")
async def run_curve_simulation(
    project_id: int, 
    total_days: int = Query(365, description="Días totales a simular"),
    step_days: int = Query(10, description="Intervalo entre puntos"),
    session: AsyncSession = Depends(get_session)
):
    """
    Genera una curva de presión vs tiempo para todos los pozos del proyecto.
    Retorna arrays listos para graficar.
    """
    # 1. Obtener datos
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    result_wells = await session.execute(select(Well).where(Well.project_id == project_id).order_by(Well.id))
    wells = result_wells.scalars().all()
    
    if not project or not wells:
        raise HTTPException(status_code=404, detail="Proyecto o pozos no encontrados")

    # 2. Definir los pasos de tiempo (de 1 día hasta total_days)
    time_steps = list(range(1, total_days + 1, step_days))
    
    # 3. Calcular curva usando el método optimizado del solver
    solver = TrilinearSolver(project, wells)
    try:
        curve_results = solver.calculate_curve(time_steps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la simulación de curva: {str(e)}")
    
    return {
        "project": project.name,
        "unit": "psi",
        "time_unit": "days",
        "data": curve_results
    }