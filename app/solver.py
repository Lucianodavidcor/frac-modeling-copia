import numpy as np
import math
from scipy.linalg import solve

class TrilinearSolver:
    def __init__(self, project, wells, schedules_map=None):
        """
        Inicializa el solver con los datos del proyecto, pozos y cronogramas.
        schedules_map: Diccionario {well_id: [lista de ProductionSchedule]}
        """
        self.p = project
        self.wells = wells
        self.n = len(wells)
        self.schedules = schedules_map or {}
        # Longitud de referencia: usamos xf del primer pozo
        self.L_ref = wells[0].xf if wells else 100.0
        
    def _get_stehfest_coeffs(self, n):
        """Pre-calcula los coeficientes V_k del algoritmo de Stehfest."""
        v = np.zeros(n)
        n2 = n // 2
        for k in range(1, n + 1):
            temp_v = 0.0
            for j in range((k + 1) // 2, min(k, n2) + 1):
                num = (j**n2) * math.factorial(2 * j)
                den = (math.factorial(n2 - j) * math.factorial(j) * math.factorial(j - 1) * math.factorial(k - j) * math.factorial(2 * j - k))
                temp_v += num / den
            v[k-1] = ((-1)**(n2 + k)) * temp_v
        return v

    def solve_laplace_unit_rate(self, s, source_idx): # <-- Cambio: Agregamos source_idx
        """
        Resuelve el sistema para una tasa adimensional unitaria en UN pozo específico.
        Esto permite desacoplar los efectos de cada pozo para la superposición.
        """
        A = np.zeros((self.n, self.n), dtype=complex)
        b = np.zeros(self.n, dtype=complex)
        
        for i in range(self.n):
            w = self.wells[i]
            
            # Parámetros Adimensionales
            eta_di = (w.k_fi / (w.phi_fi * w.ct_fi)) / (self.p.k_mo / (self.p.phi_mo * self.p.ct_mo))
            u_i = (s / eta_di) * self.f_ki(s, 0.1, 1e-6)
            alpha_i = np.sqrt(u_i)
            cfd = (w.kf * w.wf) / (w.k_fi * w.xf)
            
            # Matriz de Interferencia (Diagonal y Acoplamiento)
            A[i, i] = 1.0 + (alpha_i / cfd)
            if i > 0: # Interferencia con pozo izquierdo
                A[i, i-1] = -0.2 / (w.spacing / self.L_ref)
            if i < self.n - 1: # Interferencia con pozo derecho
                A[i, i+1] = -0.2 / (self.wells[i+1].spacing / self.L_ref)
        
        # EL CAMBIO CLAVE: La tasa unitaria solo se aplica al pozo que está produciendo (source_idx)
        b[source_idx] = 1.0 / s 
        return solve(A, b)

    def f_ki(self, s, omega, lambd):
        """Función de transferencia de doble porosidad (Eq. 30)."""
        if lambd == 0 or (1 - omega) == 0: 
            return 1.0
        arg = np.sqrt(max(1e-12, (3.0 * (1.0 - omega) * s) / lambd))
        return omega + np.sqrt((lambd * (1.0 - omega)) / (3.0 * s)) * np.tanh(arg)

    def calculate_curve(self, days_list, n_stehfest=12):
        """
        Genera curvas aplicando el principio de superposición temporal (Eq. 56).
        Calcula el efecto acumulativo de cada cambio de tasa en el tiempo.
        """
        v = self._get_stehfest_coeffs(n_stehfest)
        # Inicializamos los resultados con ceros para acumular las caídas de presión
        results = {w.name: np.zeros(len(days_list)) for w in self.wells}
        
        # Escalamiento físico real (DeltaP en psi)
        scale = (141.2 * self.p.mu * self.p.b_factor) / (self.wells[0].k_fi * self.p.h)

        for i_day, t_day in enumerate(days_list):
            dp_total = np.zeros(self.n)
            
            # Aplicamos superposición para cada pozo productor
            for i_prod, well_prod in enumerate(self.wells):
                well_sched = self.schedules.get(well_prod.id, [])
                # Si no hay schedule, se usa una tasa base por defecto de 200
                q_steps = [(s.time_days, s.rate_stbd or 0.0) for s in well_sched] if well_sched else [(0.0, 200.0)]
                
                for k in range(len(q_steps)):
                    t_start, q_val = q_steps[k]
                    if t_day > t_start:
                        q_prev = q_steps[k-1][1] if k > 0 else 0.0
                        delta_q = q_val - q_prev
                        dt = t_day - t_start
                        
                        # Inversión de Stehfest para el intervalo dt
                        t_d = (0.00633 * self.p.k_mo * dt) / (self.p.phi_mo * self.p.mu * self.p.ct_mo * (self.L_ref**2))
                        pwd_vec = np.zeros(self.n)
                        for step in range(1, n_stehfest + 1):
                            s_laplace = step * np.log(2.0) / t_d
                            # LLAMADA CORREGIDA: Pasamos el índice del pozo productor (i_prod)
                            pwd_vec += v[step-1] * self.solve_laplace_unit_rate(s_laplace, i_prod).real
                        
                        dp_total += (delta_q * scale) * pwd_vec

            # Guardar resultados finales (Pini - DeltaP acumulado) para cada pozo
            for i in range(self.n):
                p_final = max(0, self.p.initial_pressure - dp_total[i])
                results[self.wells[i].name][i_day] = round(p_final, 2)
        
        # Convertimos los arrays de numpy a listas para que sean JSON serializables
        return {
            "time": days_list, 
            "curves": {name: curve.tolist() for name, curve in results.items()}
        }