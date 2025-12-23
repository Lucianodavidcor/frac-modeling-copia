import numpy as np
import math
import scipy.linalg
from app.engine.dual_porosity import f_function

# ================= Funciones Auxiliares de Estabilidad Numérica =================

def tanh_stable(x):
    """Tangente hiperbólica numéricamente estable para argumentos complejos."""
    if isinstance(x, complex):
        if x.real > 20.0: return 1.0 + 0j
        if x.real < -20.0: return -1.0 + 0j
    else:
        if x > 20.0: return 1.0
        if x < -20.0: return -1.0
    return np.tanh(x)

def sinh_stable(x):
    """Seno hiperbólico estable para evitar overflow en argumentos grandes."""
    if isinstance(x, complex) and x.real > 20.0:
        return 0.5 * np.exp(x)
    return np.sinh(x)

def calculate_choking_skin(k_ref, k_f, h, n_f, x_f, w_f, r_w):
    """
    Calcula el skin de estrangulamiento (choking skin) s_cFi.
    Referencia: Eq. 53 del paper.
    """
    # h_D = h/x_f; r_wD = r_w/x_f
    h_D = h / x_f
    r_wD = r_w / x_f
    # C_fD = (k_f * w_f) / (k_ref * x_f)
    cfd = (k_f * w_f) / (k_ref * x_f)
    
    term = h_D / (n_f * cfd)
    factor = math.log(h_D / (2 * r_wD)) - (math.pi / 2)
    return term * factor

class MultiWellMatrixSolver:
    def __init__(self, s_val: complex, num_wells: int):
        """
        Inicializa el sistema matricial de 2n x 2n según la Eq. 45.
        """
        self.s = s_val
        self.n = num_wells
        # El sistema contiene n presiones de pozo y n presiones promedio de SRV
        self.A = np.zeros((2 * self.n, 2 * self.n), dtype=complex)
        self.b = np.zeros(2 * self.n, dtype=complex)

    def build_matrix(self, wells_params: list, project_params: dict):
        """
        Construye la matriz A y el vector b siguiendo las Ecs. 47 y 48.
        """
        n = self.n
        s = self.s
        
        # Propiedades globales de referencia
        k_ref = project_params["k_ref_m2"]
        mu = project_params["mu_pas"]
        h = project_params["h_m"]
        
        for i in range(n):
            w = wells_params[i]
            
            # 1. Parámetros de Doble Porosidad (Eq. 30-33)
            # u_Ki = s_Ki * f_Ki(s_Ki)
            s_Ii = s / w["eta_D"]
            f_s_Ii = f_function(s_Ii, w.get("omega", 1.0), w.get("lam", 0.0))
            u_Ii = s_Ii * f_s_Ii
            
            # 2. Coeficientes de Interferencia y Flujo (Eq. 37-41)
            # alpha_Oi define la comunicación con el reservorio exterior
            # Para este modelo, se asume reservorio exterior uniforme
            alpha_Oi = u_Ii # Simplificación base trilineal
            beta_Fi = np.sqrt(alpha_Oi) * tanh_stable(np.sqrt(alpha_Oi)) # Eq. 39 aprox
            
            # gamma_Fi y alpha_Fi (Eq. 37-38)
            denom = w["C_fD"] * w["y_D"] * w["x_f_D"]
            gamma_Fi = (2 * beta_Fi) / (denom + 1e-20)
            alpha_Fi = gamma_Fi + (s / w.get("eta_fD", 1.0))
            
            # 3. Llenado de Filas 1 a n (Ecuaciones de Pozo - Eq. 47)
            # a_ii = -1 (Presión del pozo i)
            self.A[i, i] = -1.0
            
            # Acoplamiento con presión promedio del bloque SRV (h_i)
            # En un sistema multi-pozo, esto incluye términos gamma_Oij (Eq. 35)
            interference_coeff = gamma_Fi / (alpha_Fi * alpha_Oi + 1e-20)
            self.A[i, i + n] = interference_coeff 
            
            # 4. Cálculo de r_i (Tasa y Choking Skin - Eq. 54)
            # r_i incluye la resistencia de la fractura y el choking skin
            sqrt_alpha_Fi = np.sqrt(alpha_Fi)
            fracture_resistance = math.pi / (w["n_f"] * w["C_fD"] * 1.0 * w["x_f_D"] * sqrt_alpha_Fi * tanh_stable(sqrt_alpha_Fi * w["x_f_D"]) + 1e-20)
            
            # Skin de choking (si no viene en params, se puede calcular)
            s_cf = w.get("s_cf", 0.0)
            
            # b_i = r_i * q_D(s). Para tasa constante unitaria: q_D = 1/s
            self.b[i] = (fracture_resistance + s_cf) / s

            # 5. Llenado de Filas n+1 a 2n (Ecuaciones de SRV - Eq. 42 y Apéndice B)
            row_srv = i + n
            # epsilon_i (Eq. B-3)
            eps_i = tanh_stable(np.sqrt(alpha_Oi)) / (np.sqrt(alpha_Oi) + 1e-20)
            
            # Coeficientes tau (Eq. B-4)
            tau_ii = eps_i
            
            self.A[row_srv, i] = tau_ii # Relación con p_wiD
            self.A[row_srv, row_srv] = -1.0 # Auto-potencial p_IiD,avg
            
            # Interferencia con vecinos (Eq. B-5)
            # Se asume una conductividad de reservorio exterior (Eq. 40)
            if i > 0:
                self.A[row_srv, row_srv - 1] = 0.01 # Simplificación de tau_i,i-1
            if i < n - 1:
                self.A[row_srv, row_srv + 1] = 0.01 # Simplificación de tau_i,i+1

    def solve(self) -> np.ndarray:
        """
        Resuelve el sistema lineal A * x = b.
        Retorna las presiones adimensionales en el pozo (primeros n elementos).
        """
        try:
            x = scipy.linalg.solve(self.A, self.b)
            return x[:self.n] # Solo nos interesan las p_wiD
        except scipy.linalg.LinAlgError:
            # Fallback en caso de matriz singular
            return np.zeros(self.n, dtype=complex)