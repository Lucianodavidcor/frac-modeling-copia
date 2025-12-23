import numpy as np
import math
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.well_models import Project
# Agregamos STB_TO_M3 a las importaciones
from app.engine.physics_utils import stehfest_weights, DAY_TO_S, PSI_TO_PA, field_p, STB_TO_M3
from app.engine.adimensional import AdimConverter
from app.engine.matrix_assembly import MultiWellMatrixSolver

class SimulationService:
    def __init__(self, db: Session):
        self.db = db
        # Configuración de Stehfest (N=12 es estándar en industria)
        self.STEHFEST_N = 12
        self.V = stehfest_weights(self.STEHFEST_N)

    def get_project_data(self, project_id: int):
        """Recupera el proyecto y sus pozos, validando que existan."""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        if not project.wells:
            raise HTTPException(status_code=400, detail="El proyecto no tiene pozos cargados.")
        return project

    def run_simulation(self, project_id: int, t_min: float = 1e-3, t_max: float = 1000.0, n_steps: int = 50):
        """
        Ejecuta la simulación completa de interferencia.
        """
        # 1. Preparar Datos
        project = self.get_project_data(project_id)
        wells = project.wells
        n_wells = len(wells)
        
        # Generamos la grilla de tiempos (log-espaciada)
        time_steps_days = np.logspace(np.log10(t_min), np.log10(t_max), n_steps)
        
        # Inicializador de Adimensionales
        converter = AdimConverter(project)
        
        # Referencia espacial (usamos la fractura del primer pozo como L_ref)
        x_fr_ref = wells[0].x_f
        
        # Convertimos todos los pozos a parámetros listos para matriz
        wells_params = [converter.get_well_params(w, x_fr_ref) for w in wells]
        
        # Diccionario con propiedades globales en SI
        proj_params = {
            "mu_pas": converter.mu_pas,
            "ct_pa": converter.ct_pa,
            "h_m": converter.h_m,
            "k_ref_m2": converter.k_ref_m2,
            "phi": converter.phi,
            "x_fr_ref_m": x_fr_ref * 0.3048, # ft to m
            "omega": project.omega,
            "lam": project.lam
        }
        q_target_stb = 150.0 
        q_ref_m3s = q_target_stb * STB_TO_M3 / DAY_TO_S

        # Arrays para guardar resultados: [TimeSteps, WellIndex]
        results_dp = np.zeros((len(time_steps_days), n_wells))

        # ================= BUCLE PRINCIPAL DE TIEMPO =================
        for i, t_day in enumerate(time_steps_days):
            t_sec = t_day * DAY_TO_S
            
            # Acumulador para la suma de Stehfest
            p_stehfest = np.zeros(n_wells, dtype=float)
            
            # --- Bucle de Inversión Numérica (Stehfest) ---
            for k in range(1, self.STEHFEST_N + 1):
                # 1. Calcular variable de Laplace 's'
                ln2 = math.log(2.0)
                s_val = (k * ln2) / t_sec
                
                # 2. Instanciar y Construir la Matriz para este 's'
                solver = MultiWellMatrixSolver(s_val, n_wells)
                solver.build_matrix(wells_params, proj_params)
                
                # 3. Construir vector de Caudales en Laplace q(s)
                q_laplace = np.zeros(n_wells, dtype=complex)
                
                for w_idx in range(n_wells):
                    t_start_sec = wells_params[w_idx]["t_start"] # t_0 en segundos
                    
                    # Lógica de Superposición Temporal:
                    # Transformada de Laplace de un escalón unitario desplazado en t_start
                    # q(s) = (q_ref / s) * exp(-s * t_start)
                    
                    q_val = (q_ref_m3s / s_val) * np.exp(-s_val * t_start_sec)
                    q_laplace[w_idx] = q_val
                
                # 4. Resolver el sistema: DeltaP(s) = R(s) * q(s)
                dp_laplace = solver.solve_pressure(q_laplace)
                
                # 5. Acumular suma ponderada (Solo parte real es física)
                weight = self.V[k-1]
                p_stehfest += weight * dp_laplace.real

            # Finalizar la inversión para este paso de tiempo
            final_dp_pas = (math.log(2.0) / t_sec) * p_stehfest
            
            # Convertir Pa a PSI y guardar
            results_dp[i, :] = [field_p(val) for val in final_dp_pas]

        # ================= FORMATEO DE SALIDA =================
        output = {
            "time_days": time_steps_days.tolist(),
            "wells": []
        }
        
        for w_idx, well in enumerate(wells):
            output["wells"].append({
                "well_id": well.id,
                "name": well.name,
                "pressure_drop_psi": results_dp[:, w_idx].tolist()
            })
            
        return output