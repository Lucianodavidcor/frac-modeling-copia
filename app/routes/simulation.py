from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
from app.database import get_session
from app.models import Project, Well, ProductionSchedule
from app.solver import TrilinearSolver

router = APIRouter(prefix="/simulate", tags=["Cálculo"])

@router.post("/{project_id}")
async def run_simulation(project_id: int, session: AsyncSession = Depends(get_session)):
    """
    Calcula la presión en los pozos para un punto fijo de 30 días.
    Útil para verificaciones rápidas de interferencia inicial.
    """
    # 1. Obtener datos del proyecto
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # 2. Obtener pozos asociados ordenados por ID
    result_wells = await session.execute(
        select(Well).where(Well.project_id == project_id).order_by(Well.id)
    )
    wells = result_wells.scalars().all()
    
    if not wells:
        raise HTTPException(status_code=400, detail="El proyecto no tiene pozos")

    # 3. Ejecutar el Solver
    solver = TrilinearSolver(project, wells)
    t_interes = 30.0
    
    try:
        pressures = solver.stehfest_inversion(t_interes)
    except Exception as e:
        # Capturamos errores numéricos
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
    step_days: int = Query(5, description="Intervalo entre puntos para la curva"),
    session: AsyncSession = Depends(get_session)
):
    """
    Genera una curva de presión vs tiempo aplicando superposición basada en los cronogramas reales.
    Retorna arrays de datos listos para graficar en el visualizador.
    """
    # 1. Obtener proyecto y cargar sus pozos asociados
    result = await session.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.wells))
    )
    project = result.scalar_one_or_none()
    
    if not project or not project.wells:
        raise HTTPException(status_code=404, detail="Proyecto o pozos no encontrados")

    # 2. Cargar los cronogramas (ProductionSchedules) para cada pozo
    # Esto es vital para que el solver aplique la superposición de tasas variables
    schedules_map = {}
    for well in project.wells:
        sched_res = await session.execute(
            select(ProductionSchedule)
            .where(ProductionSchedule.well_id == well.id)
            .order_by(ProductionSchedule.time_days)
        )
        schedules_map[well.id] = sched_res.scalars().all()

    # 3. Configurar pasos de tiempo para la curva
    time_steps = list(range(1, total_days + 1, step_days))
    
    # 4. Ejecutar el Solver con la historia de producción real
    solver = TrilinearSolver(project, project.wells, schedules_map)
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

@router.post("/{project_id}/rate-curve")
async def run_rate_simulation(project_id: int, total_days: int = 365, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Project).where(Project.id == project_id).options(selectinload(Project.wells)))
    project = result.scalar_one_or_none()
    
    schedules_map = {}
    for well in project.wells:
        sched_res = await session.execute(select(ProductionSchedule).where(ProductionSchedule.well_id == well.id).order_by(ProductionSchedule.time_days))
        schedules_map[well.id] = sched_res.scalars().all()

    solver = TrilinearSolver(project, project.wells, schedules_map)
    time_steps = list(range(1, total_days + 1, 5))
    data = solver.calculate_rate_curve(time_steps)
    
    return {"project": project.name, "unit": "stb/d", "data": data}