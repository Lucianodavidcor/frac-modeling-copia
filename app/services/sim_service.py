import numpy as np
import math
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.well_models import Project
from app.engine.physics_utils import stehfest_weights, DAY_TO_S, PSI_TO_PA, field_p, STB_TO_M3
from app.engine.adimensional import AdimConverter
from app.engine.matrix_assembly import TrilinearMatrixSolver

class SimulationService:
    def __init__(self, db: Session):
        self.db = db
        # Configuración de Stehfest (N=12 es estándar industrial)
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
        Ejecuta la simulación trilineal corrigiendo unidades y signos.
        Retorna DeltaP (Caída de Presión) en PSI positiva.
        """
        # 1. Preparar Datos
        project = self.get_project_data(project_id)
        wells = project.wells
        n_wells = len(wells)
        
        # Grilla de tiempos logarítmica
        time_steps_days = np.logspace(np.log10(t_min), np.log10(t_max), n_steps)
        
        # Inicializador de Adimensionales
        converter = AdimConverter(project)
        x_fr_ref = wells[0].x_f # Usamos la fractura del primer pozo como referencia geométrica
        
        # Convertimos parámetros de cada pozo
        wells_params = [converter.get_well_params(w, x_fr_ref) for w in wells]
        
        # Parámetros Globales en unidades SI para el cálculo de factores
        proj_params = {
            "mu_pas": converter.mu_pas,
            "ct_pa": converter.ct_pa,
            "h_m": converter.h_m,
            "k_ref_m2": converter.k_ref_m2,
            "phi": converter.phi,
            "x_fr_ref_m": x_fr_ref * 0.3048, # ft a metros
            "omega": project.omega,
            "lam": project.lam
        }

        # --- CORRECCIÓN DE ESCALA Y UNIDADES ---
        # 1. Definimos un caudal de referencia Q_ref (ej. 150 barriles/día)
        q_target_stb = 150.0 
        q_ref_m3s = q_target_stb * STB_TO_M3 / DAY_TO_S
        
        # 2. Factor de Conversión de P_D (Adimensional) a P_real (Pascales)
        # Fórmula: P_real = P_D * (q * mu) / (2 * pi * k * h)
        # Usamos k del reservorio (k_ref) ya que P_D está normalizado a eso.
        denom_scale = (2 * np.pi * converter.k_ref_m2 * converter.h_m)
        if denom_scale == 0: denom_scale = 1e-10 # Evitar división por cero
        
        p_scale_pa = (q_ref_m3s * converter.mu_pas) / denom_scale

        # Matriz para guardar resultados
        results_dp = np.zeros((len(time_steps_days), n_wells))

        # ================= BUCLE PRINCIPAL DE TIEMPO =================
        for i, t_day in enumerate(time_steps_days):
            t_sec = t_day * DAY_TO_S
            
            p_stehfest = np.zeros(n_wells, dtype=float)
            
            # --- Inversión de Stehfest ---
            for k in range(1, self.STEHFEST_N + 1):
                # A. Calcular variable de Laplace 's'
                ln2 = math.log(2.0)
                s_val = (k * ln2) / t_sec
                
                # B. Calcular Caudales ADIMENSIONALES q_D(s)
                # Para caudal constante (producción unitaria), q_D(s) = 1/s.
                # NO usamos unidades físicas aquí para no romper la matriz.
                q_D_laplace = np.zeros(n_wells, dtype=complex)
                
                for w_idx in range(n_wells):
                    t_start_sec = wells_params[w_idx]["t_start"]
                    # Aplicamos retardo temporal si el pozo empieza después (Superposición simple)
                    if t_sec > t_start_sec:
                         # q_D = 1/s * e^(-s * t_start_D) aprox
                         # Simplificación: Si el pozo está activo, input = 1/s
                         q_D_laplace[w_idx] = 1.0 / s_val
                    else:
                         q_D_laplace[w_idx] = 0.0

                # C. Resolver Matriz Matemática (Adimensional)
                # Importante: Asegúrate de tener el matrix_assembly.py corregido que te pasé antes
                solver = TrilinearMatrixSolver(s_val, n_wells)
                solver.build_matrix(wells_params, proj_params, rates_laplace=q_D_laplace)
                
                solution_full = solver.solve()
                
                # Extraer presiones de pozo adimensionales (P_wD)
                # El solver devuelve [P_pozo_1 ... P_pozo_n, P_roca_1 ... P_roca_n]
                p_wells_PD_laplace = solution_full[:n_wells]
                
                # D. Sumar a Stehfest
                weight = self.V[k-1]
                p_stehfest += weight * p_wells_PD_laplace.real

            # --- RESULTADO FINAL DEL PASO DE TIEMPO ---
            # 1. Invertir Laplace: P_D(t) = (ln2 / t) * Sum(Vi * P_s)
            pd_time_adim = (math.log(2.0) / t_sec) * p_stehfest
            
            # 2. Escalar a Unidades Reales (Pascales) y Corregir Signo
            # Multiplicamos por -1.0 porque la matriz suele resolver la ecuación difusiva
            # con convención negativa. Queremos DeltaP Positivo (Drawdown).
            final_dp_pas = abs(pd_time_adim) * p_scale_pa
            
            # 3. Convertir a PSI y guardar
            results_dp[i, :] = [field_p(val) for val in final_dp_pas]

        # ================= SALIDA =================
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