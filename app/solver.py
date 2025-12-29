import numpy as np
import math
from scipy.linalg import solve

class TrilinearSolver:
    def __init__(self, project, wells):
        self.p = project
        self.wells = wells
        self.n = len(wells)
        # Longitud de referencia: usamos xf del primer pozo
        self.L_ref = wells[0].xf if wells else 100.0
        
    def get_dimensionless_time(self, t_days):
        """
        Calcula tD (Tiempo Adimensional) basado en el ORV.
        tD = (0.00633 * k_mo * t) / (phi_mo * mu * ct_mo * Lref^2)
        """
        p = self.p
        return (0.00633 * p.k_mo * t_days) / (p.phi_mo * p.mu * p.ct_mo * (self.L_ref**2))

    def f_ki(self, s, omega, lambd):
        """
        Función de transferencia de doble porosidad (Eq. 30 del paper).
        Representa la interacción entre la matriz y las fracturas naturales.
        """
        if lambd == 0 or (1 - omega) == 0: 
            return 1.0
        # Evitamos división por cero y raíces de números negativos
        arg = np.sqrt(max(1e-12, (3.0 * (1.0 - omega) * s) / lambd))
        return omega + np.sqrt((lambd * (1.0 - omega)) / (3.0 * s)) * np.tanh(arg)

    def solve_laplace(self, s):
        """
        Resuelve el sistema de n pozos acoplados en el dominio de Laplace.
        Construye una matriz A de n x n donde A[i,j] representa la interferencia.
        """
        n = self.n
        A = np.zeros((n, n), dtype=complex)
        b = np.zeros(n, dtype=complex)
        
        for i in range(n):
            w = self.wells[i]
            
            # 1. Parámetros Adimensionales del Pozo i
            # eta_Di: Relación de difusividad entre SRV y ORV
            eta_di = (w.k_fi / (w.phi_fi * w.ct_fi)) / (self.p.k_mo / (self.p.phi_mo * self.p.ct_mo))
            
            # u_i: Difusividad combinada con doble porosidad
            u_i = (s / eta_di) * self.f_ki(s, 0.1, 1e-6)
            alpha_i = np.sqrt(u_i)
            
            # CfD: Conductividad de fractura adimensional
            cfd = (w.kf * w.wf) / (w.k_fi * w.xf)
            
            # 2. Coeficiente Principal (Diagonal)
            # Representa el flujo trilineal propio del pozo i
            A[i, i] = 1.0 + (alpha_i / cfd)
            
            # 3. Términos de Interferencia (Fuera de la diagonal)
            # La interferencia se atenúa con la distancia (spacing)
            if i > 0: # Interferencia con pozo anterior (izquierda)
                interference = 0.2 / (w.spacing / self.L_ref)
                A[i, i-1] = -interference
            if i < n - 1: # Interferencia con pozo siguiente (derecha)
                next_w_spacing = self.wells[i+1].spacing
                interference = 0.2 / (next_w_spacing / self.L_ref)
                A[i, i+1] = -interference
                
            # 4. Condición de borde: Presión constante en el pozo (pwD = 1/s)
            b[i] = 1.0 / s
            
        return solve(A, b)

    def stehfest_inversion(self, t_days, n_stehfest=12):
        """
        Inversión numérica de Laplace al tiempo real para un solo paso de tiempo.
        """
        if t_days <= 0: return [self.p.initial_pressure] * self.n
        
        t_d = self.get_dimensionless_time(t_days)
        ln2_t = np.log(2.0) / t_d
        
        # Coeficientes de Stehfest
        v = self._get_stehfest_coeffs(n_stehfest)

        pwd_vector = np.zeros(self.n, dtype=complex)
        for k in range(1, n_stehfest + 1):
            s = k * ln2_t
            pwd_vector += v[k-1] * self.solve_laplace(s)
            
        # Escalamiento físico: DeltaP = (141.2 * q * mu * B) / (k * h)
        # Asumimos una tasa q = 200 STB/D para el cálculo de presión
        scale = (141.2 * 200.0 * self.p.mu * self.p.b_factor) / (self.wells[0].k_fi * self.p.h)
        
        results = []
        for i in range(self.n):
            dp = pwd_vector[i].real * scale
            p_final = max(0, self.p.initial_pressure - dp)
            results.append(round(p_final, 2))
            
        return results

    def calculate_curve(self, days_list, n_stehfest=12):
        """
        Genera curvas completas de presión vs tiempo para todos los pozos.
        """
        v = self._get_stehfest_coeffs(n_stehfest)
        results = {w.name: [] for w in self.wells}
        times = []

        # Parámetros fijos para la escala
        scale = (141.2 * 200.0 * self.p.mu * self.p.b_factor) / (self.wells[0].k_fi * self.p.h)

        for t_day in days_list:
            if t_day <= 0: continue
            times.append(t_day)
            t_d = self.get_dimensionless_time(t_day)
            ln2_t = np.log(2.0) / t_d
            
            pwd_vector = np.zeros(self.n, dtype=complex)
            for k in range(1, n_stehfest + 1):
                s = k * ln2_t
                pwd_vector += v[k-1] * self.solve_laplace(s)
            
            for i in range(self.n):
                dp = pwd_vector[i].real * scale
                p_final = max(0, self.p.initial_pressure - dp)
                results[self.wells[i].name].append(round(p_final, 2))
        
        return {"time": times, "curves": results}

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