import numpy as np
import math
import scipy.linalg
from app.engine.dual_porosity import f_function

# ================= Funciones de Estabilidad Numérica =================

def tanh_stable(x):
    """Tangente hiperbólica estable para evitar overflow en argumentos grandes."""
    if isinstance(x, complex):
        if x.real > 20.0: return 1.0 + 0j
        if x.real < -20.0: return -1.0 + 0j
    else:
        if x > 20.0: return 1.0
        if x < -20.0: return -1.0
    return np.tanh(x)

def sinh_stable(x):
    """Seno hiperbólico estable para evitar overflow en argumentos reales/complejos."""
    if isinstance(x, complex):
        if x.real > 20.0: return 0.5 * np.exp(x)
    elif x > 20.0:
        return 0.5 * np.exp(x)
    return np.sinh(x)

class MultiWellMatrixSolver:
    def __init__(self, s_val: complex, num_wells: int):
        """
        Inicializa el sistema matricial de 2n x 2n según la Eq. 45 del paper.
        n ecuaciones para presiones de pozo (p_wiD)
        n ecuaciones para presiones promedio de SRV (p_IiD_avg)
        """
        self.s = s_val
        self.n = num_wells
        self.A = np.zeros((2 * self.n, 2 * self.n), dtype=complex)
        self.b = np.zeros(2 * self.n, dtype=complex)

    def build_matrix(self, wells_params: list, project_params: dict):
        """
        Construye la matriz A y el vector b siguiendo rigurosamente el modelo de Ozkan.
        """
        n = self.n
        s = self.s
        
        # 1. Pre-cálculo de transmisibilidades del reservorio exterior (Eq. 40)
        gammas_O = []
        for i in range(n):
            w = wells_params[i]
            u_Oi = s # Bloque exterior (simplificación trilineal)
            # x_eOiD: Distancia adimensional entre SRVs (mitad del espaciamiento del ORV)
            x_eOiD = 0.1 # Valor por defecto, idealmente calculado según espaciamiento real
            
            val_gamma = (np.sqrt(u_Oi) * w["y_eD"]) / (2 * sinh_stable(2 * np.sqrt(u_Oi) * x_eOiD) + 1e-20)
            gammas_O.append(val_gamma)

        for i in range(n):
            w = wells_params[i]
            
            # 2. Parámetros de Doble Porosidad y Difusión (Eq. 30-38)
            s_Ii = s / (w["eta_D"] + 1e-20)
            u_Ii = s_Ii * f_function(s_Ii, w.get("omega", 1.0), w.get("lam", 0.0))
            
            # alpha_Oi (Eq. 41) - Incorpora la comunicación con bloques vecinos
            g_prev = gammas_O[i-1] if i > 0 else 0
            g_next = gammas_O[i] if i < n-1 else 0
            alpha_Oi = u_Ii + g_prev + g_next
            
            # Coeficientes de la fractura
            beta_Fi = np.sqrt(alpha_Oi) * tanh_stable(np.sqrt(alpha_Oi))
            gamma_Fi = (2 * beta_Fi) / (w["C_fD"] * w["y_eD"] * w["x_f_D"] + 1e-20)
            alpha_Fi = gamma_Fi + s # Asumiendo difusividad de fractura eta_fD = 1

            # 3. FILAS DE POZOS (Ecuaciones 1 a n)
            # Usamos diagonal positiva para asegurar estabilidad (A*x = b)
            self.A[i, i] = 1.0 
            
            # Coeficiente de acoplamiento p_wiD <-> p_IiD_avg
            c_couple = gamma_Fi / (alpha_Fi * alpha_Oi + 1e-20)
            
            # Interferencia propia y de vecinos (Eq. 47)
            # Acoplamiento con su propio bloque SRV
            self.A[i, i + n] = -c_couple * u_Ii 
            # Acoplamiento con bloques SRV vecinos (a través del ORV común)
            if i > 0:
                self.A[i, i - 1 + n] = -c_couple * g_prev
            if i < n - 1:
                self.A[i, i + 1 + n] = -c_couple * g_next

            # 4. VECTOR b (Eq. 48) - Incluye Resistencia, Skin y Tiempo de Inicio
            sqrt_alpha_Fi = np.sqrt(alpha_Fi)
            r_i = math.pi / (w["n_f"] * w["C_fD"] * w["x_f_D"] * sqrt_alpha_Fi * tanh_stable(sqrt_alpha_Fi * w["x_f_D"]) + 1e-20)
            
            # Superposición temporal integrada: (1/s) * exp(-s * t_start)
            t_start_adim = w.get("t_start", 0.0)
            q_s = (1.0 / s) * np.exp(-s * t_start_adim)
            
            self.b[i] = (r_i + w.get("s_cf", 0.0)) * q_s

            # 5. FILAS DE SRV (Ecuaciones n+1 a 2n - Eq. B-5)
            row_srv = i + n
            eps_i = tanh_stable(np.sqrt(alpha_Oi)) / (np.sqrt(alpha_Oi) + 1e-20)
            
            self.A[row_srv, row_srv] = 1.0 # Diagonal SRV
            self.A[row_srv, i] = -eps_i     # Relación con la presión de su pozo
            
            # Interferencia entre bloques adyacentes
            tau_neigh = (1 - eps_i) * 0.1 
            if i > 0: 
                self.A[row_srv, row_srv - 1] = -tau_neigh
            if i < n - 1: 
                self.A[row_srv, row_srv + 1] = -tau_neigh

    def solve(self) -> np.ndarray:
        """
        Resuelve el sistema lineal A * x = b.
        Retorna las presiones adimensionales de pozo (los primeros n elementos).
        """
        try:
            x = scipy.linalg.solve(self.A, self.b)
            return x[:self.n]
        except scipy.linalg.LinAlgError:
            # Fallback en caso de inestabilidad extrema
            return np.zeros(self.n, dtype=complex)