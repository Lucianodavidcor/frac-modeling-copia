from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any

# Importamos la dependencia de base de datos.
try:
    from app.api.deps import get_db
except ImportError:
    from app.db.session import get_db

# Importamos los esquemas y el servicio
from app.schemas.sim_schemas import SimulationConfig, SimulationResponse
from app.services.sim_service import SimulationService

router = APIRouter()

@router.post("/run", response_model=SimulationResponse, summary="Ejecutar Simulación Trilineal")
def run_simulation(
    config: SimulationConfig,
    db: Session = Depends(get_db)
) -> Any:
    """
    Ejecuta el motor matemático de interferencia (Modelo Trilineal Acoplado).
    
    Recibe los parámetros de configuración y devuelve las series de tiempo de presión
    para cada pozo del proyecto.
    """
    # Instanciamos el servicio con la sesión de DB actual
    service = SimulationService(db)
    
    try:
        # Ejecutamos la lógica de negocio
        results = service.run_simulation(
            project_id=config.project_id,
            t_min=config.t_min,
            t_max=config.t_max,
            n_steps=config.n_steps
        )
        return results
        
    except HTTPException as he:
        raise he
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=f"Error de validación matemática: {str(ve)}")
    except Exception as e:
        print(f"CRITICAL ERROR in simulation: {e}") 
        raise HTTPException(status_code=500, detail=f"Error interno del motor de simulación: {str(e)}")