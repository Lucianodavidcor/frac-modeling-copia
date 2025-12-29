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

    def solve_laplace_unit_rate(self, s, source_idx):
        """
        Resuelve el sistema para una tasa adimensional unitaria en UN pozo específico.
        Esto permite desacoplar los efectos de cada pozo para la superposición de presión.
        """
        A = np.zeros((self.n, self.n), dtype=complex)
        b = np.zeros(self.n, dtype=complex)
        
        for i in range(self.n):
            w = self.wells[i]
            eta_di = (w.k_fi / (w.phi_fi * w.ct_fi)) / (self.p.k_mo / (self.p.phi_mo * self.p.ct_mo))
            u_i = (s / eta_di) * self.f_ki(s, 0.1, 1e-6)
            alpha_i = np.sqrt(u_i)
            cfd = (w.kf * w.wf) / (w.k_fi * w.xf)
            
            A[i, i] = 1.0 + (alpha_i / cfd)
            if i > 0: 
                A[i, i-1] = -0.2 / (w.spacing / self.L_ref)
            if i < self.n - 1:
                A[i, i+1] = -0.2 / (self.wells[i+1].spacing / self.L_ref)
        
        b[source_idx] = 1.0 / s 
        return solve(A, b)

    def solve_laplace_rates(self, s, target_pwf_d_vector):
        """
        Resuelve el sistema para obtener Tasas (q) dada una Presión (Pwf) impuesta.
        q_D(s) = [A(s)]^-1 * Pwf_D(s)
        """
        A = np.zeros((self.n, self.n), dtype=complex)
        for i in range(self.n):
            w = self.wells[i]
            eta_di = (w.k_fi / (w.phi_fi * w.ct_fi)) / (self.p.k_mo / (self.p.phi_mo * self.p.ct_mo))
            u_i = (s / eta_di) * self.f_ki(s, 0.1, 1e-6)
            alpha_i = np.sqrt(u_i)
            cfd = (w.kf * w.wf) / (w.k_fi * w.xf)
            
            A[i, i] = 1.0 + (alpha_i / cfd)
            if i > 0: 
                A[i, i-1] = -0.2 / (w.spacing / self.L_ref)
            if i < self.n - 1:
                A[i, i+1] = -0.2 / (self.wells[i+1].spacing / self.L_ref)
        
        return solve(A, target_pwf_d_vector)

    def f_ki(self, s, omega, lambd):
        """Función de transferencia de doble porosidad (Eq. 30)."""
        if lambd == 0 or (1 - omega) == 0: 
            return 1.0
        arg = np.sqrt(max(1e-12, (3.0 * (1.0 - omega) * s) / lambd))
        return omega + np.sqrt((lambd * (1.0 - omega)) / (3.0 * s)) * np.tanh(arg)

    def calculate_curve(self, days_list, n_stehfest=12):
        """
        Genera curvas de presión aplicando el principio de superposición temporal (Eq. 56).
        """
        v = self._get_stehfest_coeffs(n_stehfest)
        results = {w.name: np.zeros(len(days_list)) for w in self.wells}
        scale = (141.2 * self.p.mu * self.p.b_factor) / (self.wells[0].k_fi * self.p.h)

        for i_day, t_day in enumerate(days_list):
            dp_total = np.zeros(self.n)
            for i_prod, well_prod in enumerate(self.wells):
                well_sched = self.schedules.get(well_prod.id, [])
                q_steps = [(s.time_days, s.rate_stbd or 0.0) for s in well_sched] if well_sched else [(0.0, 200.0)]
                
                for k in range(len(q_steps)):
                    t_start, q_val = q_steps[k]
                    if t_day > t_start:
                        q_prev = q_steps[k-1][1] if k > 0 else 0.0
                        delta_q = q_val - q_prev
                        dt = t_day - t_start
                        
                        t_d = (0.00633 * self.p.k_mo * dt) / (self.p.phi_mo * self.p.mu * self.p.ct_mo * (self.L_ref**2))
                        pwd_vec = np.zeros(self.n)
                        for step in range(1, n_stehfest + 1):
                            s_laplace = step * np.log(2.0) / t_d
                            pwd_vec += v[step-1] * self.solve_laplace_unit_rate(s_laplace, i_prod).real
                        
                        dp_total += (delta_q * scale) * pwd_vec

            for i in range(self.n):
                p_final = max(0, self.p.initial_pressure - dp_total[i])
                results[self.wells[i].name][i_day] = round(p_final, 2)
        
        return {"time": days_list, "curves": {name: curve.tolist() for name, curve in results.items()}}

    def calculate_rate_curve(self, days_list, n_stehfest=12):
        """
        Versión Corregida: Calcula el DECLINO real (Tasa vs Tiempo).
        """
        v = self._get_stehfest_coeffs(n_stehfest)
        results = {w.name: [] for w in self.wells}
        
        # Escala física real para Vaca Muerta (STB/D)
        # q = (k * h * DeltaP) / (141.2 * mu * B)
        # Multiplicamos por un factor de ajuste para la adimensionalidad del modelo trilineal
        k_ref = self.wells[0].k_fi
        scale_base = (k_ref * self.p.h) / (141.2 * self.p.mu * self.p.b_factor)

        for t_day in days_list:
            t_d = (0.00633 * self.p.k_mo * t_day) / (self.p.phi_mo * self.p.mu * self.p.ct_mo * (self.L_ref**2))
            ln2_t = np.log(2.0) / t_d
            
            qd_vector = np.zeros(self.n, dtype=complex)
            for step in range(1, n_stehfest + 1):
                s = step * ln2_t
                
                # Vector de presión adimensional (SIN el 1/s extra que causaba el aumento)
                delta_p_vector = np.zeros(self.n, dtype=complex)
                for i, well in enumerate(self.wells):
                    well_sched = self.schedules.get(well.id, [])
                    start_time = well_sched[0].time_days if well_sched else 0
                    target_pwf = well_sched[0].pwf_psi if well_sched else 1000.0
                    
                    if t_day >= start_time:
                        # Delta P real en psi
                        delta_p_vector[i] = (self.p.initial_pressure - target_pwf)
                    else:
                        delta_p_vector[i] = 0.0
                
                # Resolvemos el sistema: q_D = A^-1 * DeltaP
                qd_vector += v[step - 1] * self.solve_laplace_rates(s, delta_p_vector)
            
            for i in range(self.n):
                # Aplicamos la escala para obtener barriles por día reales
                q_real = max(0, qd_vector[i].real * scale_base)
                results[self.wells[i].name].append(round(q_real, 2))
        
        return {"time": days_list, "curves": results}