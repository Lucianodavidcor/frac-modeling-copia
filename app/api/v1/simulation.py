from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.sim_service import SimulationService
from app.schemas.sim_schemas import SimulationParams

router = APIRouter()

@router.post("/projects/{project_id}/simulate")
def run_project_simulation(
    project_id: int, 
    params: SimulationParams,
    db: Session = Depends(get_db)
):
    """
    Ejecuta la simulación de interferencia multi-pozo usando el motor de Laplace/Stehfest.
    
    - **project_id**: ID del proyecto (Pad) creado previamente.
    - **t_min/t_max**: Rango de tiempo en días.
    - **n_steps**: Resolución de la curva (más pasos = más lento pero más suave).
    """
    service = SimulationService(db)
    
    try:
        results = service.run_simulation(
            project_id=project_id,
            t_min=params.t_min,
            t_max=params.t_max,
            n_steps=params.n_steps
        )
        return results
        
    except HTTPException as e:
        raise e
    except Exception as e:
        # Capturamos errores matemáticos inesperados (ej. división por cero en matriz mal formada)
        raise HTTPException(status_code=500, detail=f"Error interno en el motor de simulación: {str(e)}")