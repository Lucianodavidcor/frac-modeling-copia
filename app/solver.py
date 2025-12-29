import numpy as np
import math
from scipy.linalg import solve

class TrilinearSolver:
    def __init__(self, project, wells):
        self.p = project
        self.wells = wells
        self.n = len(wells)
        # Longitud de referencia (xf del primer pozo)
        self.L_ref = wells[0].xf if wells else 100.0
        
    def get_dimensionless_time(self, t_days):
        """tD = (0.00633 * k_mo * t) / (phi_mo * mu * ct_mo * Lref^2)"""
        p = self.p
        return (0.00633 * p.k_mo * t_days) / (p.phi_mo * p.mu * p.ct_mo * (self.L_ref**2))

    def f_ki(self, s, omega, lambd):
        """Función de transferencia de doble porosidad (Eq. 30 del paper)."""
        if lambd == 0 or (1 - omega) == 0: return 1.0
        # Evitamos división por cero en el límite
        arg = np.sqrt(max(1e-12, (3.0 * (1.0 - omega) * s) / lambd))
        return omega + np.sqrt((lambd * (1.0 - omega)) / (3.0 * s)) * np.tanh(arg)

    def solve_laplace(self, s):
        """
        Resuelve el sistema de n pozos acoplados. 
        Usamos una matriz n x n donde cada fila es el balance de un pozo.
        """
        n = self.n
        A = np.zeros((n, n), dtype=complex)
        b = np.zeros(n, dtype=complex)
        
        for i in range(n):
            w = self.wells[i]
            
            # 1. Parámetros Adimensionales del Pozo i
            # Relación de difusividad (eta_Di)
            eta_di = (w.k_fi / (w.phi_fi * w.ct_fi)) / (self.p.k_mo / (self.p.phi_mo * self.p.ct_mo))
            
            # Función de doble porosidad para el SRV
            # (Usamos valores típicos de omega y lambda si no se proveen)
            u_i = (s / eta_di) * self.f_ki(s, 0.1, 1e-6)
            alpha_i = np.sqrt(u_i)
            
            # Conductividad de fractura adimensional (CfD)
            cfd = (w.kf * w.wf) / (w.k_fi * w.xf)
            
            # 2. Construcción de la fila i de la matriz
            # Coeficiente principal (Flujo trilineal + Almacenamiento)
            # Simplificación de Eq. 47: la caída de presión depende de alpha y cfd
            A[i, i] = 1.0 + (alpha_i / cfd)
            
            # 3. Interferencia (Acoplamiento lateral a través del ORV)
            # La interferencia es inversamente proporcional al spacing
            if i > 0:
                interference_factor = 0.1 / (w.spacing / self.L_ref)
                A[i, i-1] = -interference_factor
            if i < n - 1:
                next_well_spacing = self.wells[i+1].spacing
                interference_factor = 0.1 / (next_well_spacing / self.L_ref)
                A[i, i+1] = -interference_factor
                
            # 4. Condición de borde: Producción a Presión Constante (pwD = 1/s)
            b[i] = 1.0 / s
            
        return solve(A, b)

    def stehfest_inversion(self, t_days, n_stehfest=12):
        """Inversión numérica de Laplace al tiempo real."""
        if t_days <= 0: return 0.0
        
        t_d = self.get_dimensionless_time(t_days)
        ln2_t = np.log(2.0) / t_d
        
        # Coeficientes de Stehfest
        v = np.zeros(n_stehfest)
        for k in range(1, n_stehfest + 1):
            temp_v = 0.0
            for j in range((k + 1) // 2, min(k, n_stehfest // 2) + 1):
                num = (j**(n_stehfest // 2)) * math.factorial(2 * j)
                den = (math.factorial(n_stehfest // 2 - j) * math.factorial(j) * math.factorial(j - 1) * math.factorial(k - j) * math.factorial(2 * j - k))
                temp_v += num / den
            v[k-1] = ((-1)**(n_stehfest // 2 + k)) * temp_v

        # Cálculo de la presión adimensional pwD
        pwd_vector = np.zeros(self.n, dtype=complex)
        for k in range(1, n_stehfest + 1):
            s = k * ln2_t
            pwd_laplace = self.solve_laplace(s)
            pwd_vector += v[k-1] * pwd_laplace
            
        # Des-adimensionalización (Eq. 18-20 del paper)
        # DeltaP = (q * mu * B) / (2 * pi * k * h) * pwD
        # Para simplificar este paso, usamos un factor de escala de 150 psi por unidad de pwD
        factor_escala = 150.0 
        
        results = []
        for i in range(self.n):
            dp = pwd_vector[i].real * factor_escala
            p_final = self.p.initial_pressure - dp
            results.append(max(0, round(p_final, 2)))
            
        return results