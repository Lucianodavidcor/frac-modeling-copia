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
        # N=12 es el estándar sugerido por el paper para el algoritmo de Stehfest
        self.STEHFEST_N = 12
        self.V = stehfest_weights(self.STEHFEST_N)

    def get_project_data(self, project_id: int):
        """Recupera el proyecto y sus pozos de la base de datos."""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        if not project.wells:
            raise HTTPException(status_code=400, detail="El proyecto no tiene pozos cargados.")
        return project

    def run_simulation(self, project_id: int, t_min: float = 1e-3, t_max: float = 1000.0, n_steps: int = 50):
        """
        Ejecuta la simulación de interferencia multi-pozo usando el sistema acoplado 2n x 2n.
        """
        # 1. Preparar datos y conversiones adimensionales
        project = self.get_project_data(project_id)
        wells = project.wells
        n_wells = len(wells)
        
        # Grid log-espaciado para capturar transitorios de fractura y reservorio
        time_steps_days = np.logspace(np.log10(t_min), np.log10(t_max), n_steps)
        
        converter = AdimConverter(project)
        # Usamos la fractura del primer pozo como longitud de referencia (x_FR)
        x_fr_ref = wells[0].x_f 
        
        wells_params = [converter.get_well_params(w, x_fr_ref) for w in wells]
        
        proj_params = {
            "mu_pas": converter.mu_pas,
            "ct_pa": converter.ct_pa,
            "h_m": converter.h_m,
            "k_ref_m2": converter.k_ref_m2,
            "phi": converter.phi_ref,
            "x_fr_ref_m": x_fr_ref * 0.3048 # ft a m
        }

        # --- Factor de Escala de Presión (Eq. 2 del Paper) ---
        # Bajamos la tasa de referencia a 40 STB/D para evitar caídas de presión irreales en baja permeabilidad
        q_target_stb = 40.0  
        q_ref_m3s = q_target_stb * STB_TO_M3 / DAY_TO_S
        
        # Escala: DeltaP_real = p_D * (q * mu) / (2 * pi * k * h)
        pressure_scale = (q_ref_m3s * converter.mu_pas) / (2 * math.pi * converter.k_ref_m2 * converter.h_m + 1e-20)

        # Arrays para resultados
        results_dp = np.zeros((len(time_steps_days), n_wells))
        results_der = np.zeros((len(time_steps_days), n_wells))

        # ================= BUCLE PRINCIPAL DE TIEMPO (Stehfest) =================
        for i, t_day in enumerate(time_steps_days):
            t_sec = t_day * DAY_TO_S
            p_sum = np.zeros(n_wells, dtype=float)
            der_sum = np.zeros(n_wells, dtype=float)
            
            ln2 = math.log(2.0)
            
            for k in range(1, self.STEHFEST_N + 1):
                s_val = (k * ln2) / t_sec
                
                # Instanciar el solver matricial 2n x 2n
                solver = MultiWellMatrixSolver(s_val, n_wells)
                # build_matrix ya incluye q_D(s) y exp(-s*t_start) en el vector b
                solver.build_matrix(wells_params, proj_params)
                
                # Obtener la presión de pozo acoplada en el espacio de Laplace
                p_s = solver.solve()
                
                # Opcional: Wellbore Storage (Eq. 57)
                for w_idx in range(n_wells):
                    cd = wells_params[w_idx].get("C_D", 0.0)
                    if cd > 0:
                        p_s[w_idx] = p_s[w_idx] / (1.0 + cd * s_val * p_s[w_idx])

                # Acumulación ponderada
                weight = self.V[k-1]
                p_sum += weight * p_s.real
                der_sum += weight * (s_val * p_s).real # Derivada logarítmica t*dp/dt

            # 3. Finalizar inversión numérica
            p_t_adim = (ln2 / t_sec) * p_sum
            der_t_adim = (ln2 / t_sec) * der_sum

            # Escalamiento a PSI (field_p convierte Pa -> PSI)
            results_dp[i, :] = [field_p(val * pressure_scale) for val in p_t_adim]
            results_der[i, :] = [field_p(val * pressure_scale) for val in der_t_adim]

        # ================= FORMATEO DE SALIDA =================
        output = {
            "time_days": time_steps_days.tolist(),
            "wells": []
        }
        
        for w_idx, well in enumerate(wells):
            output["wells"].append({
                "well_id": well.id,
                "name": well.name,
                "pressure_drop_psi": results_dp[:, w_idx].tolist(),
                "derivative_psi": results_der[:, w_idx].tolist()
            })
            
        return output