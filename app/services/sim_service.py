import numpy as np
import math
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.well_models import Project
from app.engine.physics_utils import stehfest_weights, DAY_TO_S, field_p, STB_TO_M3, PSI_TO_PA
from app.engine.adimensional import AdimConverter
from app.engine.matrix_assembly import MultiWellMatrixSolver

class SimulationService:
    def __init__(self, db: Session):
        self.db = db
        # N=12 es el estándar sugerido por el paper para el algoritmo de Stehfest [cite: 421]
        self.STEHFEST_N = 12
        self.V = stehfest_weights(self.STEHFEST_N)

    def get_project_data(self, project_id: int):
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        if not project.wells:
            raise HTTPException(status_code=400, detail="El proyecto no tiene pozos cargados.")
        return project

    def run_simulation(self, project_id: int, t_min: float = 1e-3, t_max: float = 1000.0, n_steps: int = 50):
        """
        Ejecuta la simulación de interferencia multi-pozo usando el sistema 2n x 2n.
        """
        # 1. Cargar datos y preparar el conversor adimensional [cite: 110]
        project = self.get_project_data(project_id)
        wells = project.wells
        n_wells = len(wells)
        
        # Grid log-espaciado para capturar transitorios de fractura y reservorio [cite: 453]
        time_steps_days = np.logspace(np.log10(t_min), np.log10(t_max), n_steps)
        
        converter = AdimConverter(project)
        # Usamos la fractura del primer pozo como longitud de referencia (x_FR) [cite: 174]
        x_fr_ref = wells[0].x_f 
        
        # Generar parámetros para cada pozo (incluye choking skin y eta_D) [cite: 208, 403]
        wells_params = [converter.get_well_params(w, x_fr_ref) for w in wells]
        
        proj_params = {
            "mu_pas": converter.mu_pas,
            "ct_pa": converter.ct_pa,
            "h_m": converter.h_m,
            "k_ref_m2": converter.k_ref_m2,
            "phi": converter.phi_ref,
            "x_fr_ref_m": x_fr_ref * 0.3048, # ft a m
            "omega": project.omega,
            "lam": project.lam
        }

        # Resultados de caída de presión para cada pozo en cada tiempo
        results_dp = np.zeros((len(time_steps_days), n_wells))

        # ================= BUCLE PRINCIPAL DE TIEMPO (Stehfest) [cite: 418] =================
        for i, t_day in enumerate(time_steps_days):
            t_sec = t_day * DAY_TO_S
            p_stehfest = np.zeros(n_wells, dtype=float)
            
            # --- Inversión Numérica de Laplace ---
            for k in range(1, self.STEHFEST_N + 1):
                ln2 = math.log(2.0)
                s_val = (k * ln2) / t_sec
                
                # Instanciar el solver matricial 2n x 2n del paper [cite: 383]
                solver = MultiWellMatrixSolver(s_val, n_wells)
                
                # Construir el sistema (Matriz A y Vector b)
                # El vector b ahora incorpora el término exp(-s * t_start) 
                solver.build_matrix(wells_params, proj_params)
                
                # Resolver el sistema acoplado de interferencia 
                # x = [p_w1D, ..., p_wnD, p_I1D_avg, ..., p_InD_avg]
                p_wiD_vector = solver.solve()
                
                # Acumulación de la suma de Stehfest
                weight = self.V[k-1]
                p_stehfest += weight * p_wiD_vector.real

            # Finalizar inversión para este paso de tiempo
            # p(t) = (ln2 / t) * sum(V_k * p_s)
            final_p_adim = (ln2 / t_sec) * p_stehfest
            
            # 2. Des-adimensionalización de la Presión [cite: 113]
            # DeltaP = p_wiD * (q * B * mu) / (k * h)
            # Como p_wiD ya escaló con q_ref en el b_vector, solo convertimos unidades
            results_dp[i, :] = [field_p(val * (PSI_TO_PA / 1.0)) for val in final_p_adim]

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