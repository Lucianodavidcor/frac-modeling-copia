import numpy as np
import math
from scipy.linalg import solve


class TrilinearSolver:
    def __init__(self, project, wells, schedules_map=None):
        self.p = project
        self.wells = wells
        self.n = len(wells)
        self.schedules = schedules_map or {}
        # Longitud de referencia (usualmente xf)
        self.L_ref = wells[0].xf if wells else 100.0

    def _get_stehfest_coeffs(self, n):
        """Calcula los coeficientes V_k de Stehfest."""
        v = np.zeros(n)
        n2 = n // 2
        for k in range(1, n + 1):
            temp_v = 0.0
            for j in range((k + 1) // 2, min(k, n2) + 1):
                num = (j ** n2) * math.factorial(2 * j)
                den = (math.factorial(n2 - j) * math.factorial(j) * math.factorial(j - 1) * math.factorial(
                    k - j) * math.factorial(2 * j - k))
                temp_v += num / den
            v[k - 1] = ((-1) ** (n2 + k)) * temp_v
        return v

    def solve_laplace_unit_rate(self, s, source_idx):
        A = np.eye(self.n, dtype=complex)
        b = np.zeros(self.n, dtype=complex)

        w_prod = self.wells[source_idx]

        # Parámetros dinámicos de la DB
        omega = (w_prod.phi_fi * w_prod.ct_fi) / max(1e-10,
                                                     (w_prod.phi_fi * w_prod.ct_fi + w_prod.phi_mi * w_prod.ct_mi))
        lambd = (w_prod.sigma_i * w_prod.k_mi * (self.L_ref ** 2)) / max(1e-10, w_prod.k_fi)

        u_i = s * self.f_ki(s, omega, lambd)
        alpha_i = np.sqrt(u_i)
        cfd = (w_prod.kf * w_prod.wf) / max(1e-10, (w_prod.k_fi * w_prod.xf))

        # --- FÓRMULA TRILINEAL CORRECTA (EJEMPLO 1) ---
        # psi vincula la fractura con el reservorio
        psi = np.sqrt((2.0 / cfd) * alpha_i * np.tanh(max(1e-8, alpha_i)))

        # La solución debe ser PwD = pi / (s * Cfd * psi * tanh(psi))
        pwd_self = np.pi / (s * cfd * psi * np.tanh(max(1e-8, psi)))
        b[source_idx] = pwd_self

        for j in range(self.n):
            if j == source_idx: continue
            dist_d = abs(self.wells[j].spacing * (j - source_idx)) / self.L_ref
            b[j] = pwd_self * np.exp(-alpha_i * dist_d)

        return solve(A, b)

    def f_ki(self, s, omega, lambd):
        """Función de transferencia de doble porosidad (Warren & Root)."""
        if lambd == 0 or (1 - omega) == 0: return 1.0
        arg = np.sqrt(max(1e-12, (3.0 * (1.0 - omega) * s) / lambd))
        return omega + np.sqrt((lambd * (1.0 - omega)) / (3.0 * s)) * np.tanh(arg)

    def calculate_curve(self, days_list, n_stehfest=12):
        """Ejecuta la simulación y aplica Stehfest para volver al dominio del tiempo."""
        v = self._get_stehfest_coeffs(n_stehfest)
        results = {w.name: {"pwf": [], "delta_p": [], "derivative": []} for w in self.wells}

        k_ref = self.wells[0].k_fi
        scale = (4.064 * self.p.mu * self.p.b_factor) / (k_ref * self.p.h)

        temp_pwf = {w.name: [] for w in self.wells}

        for t_day in days_list:
            dp_total = np.zeros(self.n)
            for i_prod, well_prod in enumerate(self.wells):
                well_sched = self.schedules.get(well_prod.id, [])
                q_steps = [(s.time_days, s.rate_stbd or 0.0) for s in well_sched]

                phi_ref = well_prod.phi_fi
                ct_ref = well_prod.ct_fi
                c_well_val = getattr(well_prod, 'c_wellbore', 0.0)
                c_d = (0.8936 * c_well_val) / (phi_ref * ct_ref * self.p.h * (self.L_ref ** 2))

                for k in range(len(q_steps)):
                    t_start, q_val = q_steps[k]
                    if t_day > t_start:
                        # Tasa distribuida por fractura
                        q_per_fracture = (q_val - (q_steps[k - 1][1] if k > 0 else 0.0)) / well_prod.n_f
                        dt = t_day - t_start
                        t_d_local = (0.00633 * k_ref * dt) / (phi_ref * self.p.mu * ct_ref * (self.L_ref ** 2))
                        if t_d_local <= 0: continue

                        ln2_td = np.log(2.0) / t_d_local
                        pwd_vec_sum = np.zeros(self.n, dtype=complex)
                        for step in range(1, n_stehfest + 1):
                            s_lap = step * ln2_td
                            sol_lap = self.solve_laplace_unit_rate(s_lap, i_prod)

                            # Almacenamiento del pozo (Wellbore Storage)
                            if c_d > 0:
                                sol_lap[i_prod] = sol_lap[i_prod] / (1.0 + c_d * (s_lap ** 2) * sol_lap[i_prod])

                            pwd_vec_sum += v[step - 1] * sol_lap

                        # Inversión de Stehfest y escalamiento a PSI
                        dp_total += (q_per_fracture * scale) * (pwd_vec_sum.real * ln2_td)

            for i, well in enumerate(self.wells):
                p_val = round(max(0, self.p.initial_pressure - dp_total[i]), 2)
                temp_pwf[well.name].append(p_val)

        # Cálculo de la Derivada de Bourdet para el gráfico Log-Log
        t_arr = np.array(days_list)
        for name in temp_pwf:
            pwf_arr = np.array(temp_pwf[name])
            dp_arr = self.p.initial_pressure - pwf_arr
            if len(t_arr) > 2:
                log_t = np.log(t_arr)
                deriv = np.gradient(dp_arr, log_t)
            else:
                deriv = np.zeros_like(dp_arr)

            results[name]["pwf"] = pwf_arr.tolist()
            results[name]["delta_p"] = dp_arr.tolist()
            results[name]["derivative"] = [round(d, 2) for d in deriv.tolist()]

        return {"time": days_list, "curves": results}
