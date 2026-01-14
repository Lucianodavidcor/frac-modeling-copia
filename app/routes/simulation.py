from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
from app.database import get_session
from app.models import Project, Well, ProductionSchedule
from app.solver import TrilinearSolver

import pandas as pd
import io
from fastapi.responses import StreamingResponse

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
        step_days: int = Query(5, description="Intervalo entre puntos (solo si log_scale=False)"),
        log_scale: bool = Query(False, description="Si es True, usa pasos logarítmicos para verificación Log-Log"),
        session: AsyncSession = Depends(get_session)
):
    """
    Genera una curva de presión, delta P y derivada vs tiempo.
    Soporta escala logarítmica para validación contra el paper SPE-215031-PA.
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
    schedules_map = {}
    for well in project.wells:
        sched_res = await session.execute(
            select(ProductionSchedule)
            .where(ProductionSchedule.well_id == well.id)
            .order_by(ProductionSchedule.time_days)
        )
        schedules_map[well.id] = sched_res.scalars().all()

    # 3. Configurar pasos de tiempo para la curva
    if log_scale:
        # Generamos 50 puntos desde 1e-5 hasta total_days para capturar el almacenamiento (Wellbore Storage)
        import numpy as np
        # Usamos base 10 para el espaciamiento logarítmico
        time_steps = np.logspace(-5, np.log10(total_days), 50).tolist()
    else:
        # Escala lineal estándar para monitoreo diario
        time_steps = list(range(1, total_days + 1, step_days))

    # 4. Ejecutar el Solver con la historia de producción real
    solver = TrilinearSolver(project, project.wells, schedules_map)
    try:
        # El solver ahora devuelve pwf, delta_p y derivative
        curve_results = solver.calculate_curve(time_steps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la simulación: {str(e)}")

    return {
        "project": project.name,
        "unit": "psi",
        "time_unit": "days",
        "is_log_scale": log_scale,
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

@router.get("/{project_id}/export-excel")
async def export_simulation_to_excel(
    project_id: int, 
    total_days: int = Query(1800, description="Días totales de la simulación (ej. 1800 para 5 años)"),
    step_days: int = Query(10, description="Frecuencia de pasos en días"),
    session: AsyncSession = Depends(get_session)
):
    """
    Genera un Excel con tiempos extendidos y parámetros definibles por el usuario.
    """
    # 1. Obtener proyecto y pozos
    result = await session.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.wells))
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # 2. Cargar cronogramas para superposición
    schedules_map = {}
    for well in project.wells:
        sched_res = await session.execute(
            select(ProductionSchedule).where(ProductionSchedule.well_id == well.id)
        )
        schedules_map[well.id] = sched_res.scalars().all()

    # 3. Configurar el rango de tiempo solicitado
    time_steps = list(range(1, total_days + 1, step_days))
    
    # 4. Ejecutar el Solver
    solver = TrilinearSolver(project, project.wells, schedules_map)
    pressure_data = solver.calculate_curve(time_steps)
    rate_data = solver.calculate_rate_curve(time_steps)

    # 5. Crear DataFrames
    df_pressures = pd.DataFrame(pressure_data["curves"])
    df_pressures.insert(0, "Tiempo (Días)", pressure_data["time"])

    df_rates = pd.DataFrame(rate_data["curves"])
    df_rates.insert(0, "Tiempo (Días)", rate_data["time"])

    # 6. Preparar el archivo Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_pressures.to_excel(writer, sheet_name="Presiones_psi", index=False)
        df_rates.to_excel(writer, sheet_name="Tasas_STBD", index=False)
        
        # Pestaña de configuración para registro
        config_df = pd.DataFrame([{
            "Proyecto": project.name,
            "Días Simulados": total_days,
            "Intervalo": step_days,
            "P_inicial (psi)": project.initial_pressure
        }])
        config_df.to_excel(writer, sheet_name="Configuracion", index=False)

    output.seek(0)
    
    filename = f"Reporte_{project.name.replace(' ', '_')}_{total_days}dias.xlsx"
    return StreamingResponse(
        output, 
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )