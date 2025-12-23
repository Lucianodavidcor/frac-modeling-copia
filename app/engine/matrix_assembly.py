import numpy as np
import math
import scipy.linalg
from app.engine.dual_porosity import f_function

# ================= Funciones Auxiliares de Estabilidad Numérica =================
# Reciclado de physics.py

def tanh_stable(x):
    """Tangente hiperbólica numéricamente estable para argumentos complejos."""
    # Evita overflow para partes reales grandes
    if isinstance(x, complex):
        if x.real > 20.0: return 1.0 + 0j
        if x.real < -20.0: return -1.0 + 0j
    else:
        if x > 20.0: return 1.0
        if x < -20.0: return -1.0
    return np.tanh(x)

def coth_stable(x):
    """Cotangente hiperbólica estable (1/tanh)."""
    # Evita división por cero
    if abs(x) < 1e-12:
        # Aproximación de Laurent: 1/x + x/3
        return (1.0 / (x + 1e-20)) + (x / 3.0)
    
    t = tanh_stable(x)
    if abs(t) < 1e-12:
        return 1e12 # Número grande si tanh es muy chica
    return 1.0 / t

def exp_clamped(z, lim=700.0):
    """Exponencial acotada para evitar overflow."""
    if isinstance(z, complex):
        real_part = np.clip(z.real, -lim, lim)
        return np.exp(complex(real_part, z.imag))
    return np.exp(np.clip(z, -lim, lim))


class MultiWellMatrixSolver:
    def __init__(self, s_val: complex, num_wells: int):
        """
        Inicializa el sistema matricial para un valor de Laplace 's'.
        Args:
            s_val: Valor de la variable de Laplace.
            num_wells: Número de pozos (n).
        """
        self.s = s_val
        self.n = num_wells
        
        # Matriz de Interacción (R) de tamaño n x n
        # R[i, j] representa la caída de presión en el pozo i causada por el pozo j
        self.R = np.zeros((self.n, self.n), dtype=complex)
        self.rhs = np.zeros(self.n, dtype=complex)

    # ================= KERNELS FÍSICOS (Ecuaciones de Flujo) =================
    # Implementación basada en physics.py y modelo trilineal (Ozkan/Brown)

    def _lambda_trilinear(self, s, k, phi, mu, ct):
        """Calcula el parámetro difusivo lambda = sqrt(s / eta)."""
        # eta = k / (phi * mu * ct)
        # lambda = sqrt( s * phi * mu * ct / k )
        val = s * phi * mu * ct / (k + 1e-20)
        return np.sqrt(val)

    def _R_slab(self, s, lambda_val, k, h, L_dist):
        """
        Solución analítica para un bloque lineal (Slab).
        Eq. base: (mu / k*h) * coth(lambda * L) / lambda
        """
        pre_factor = 1.0 / (k * h * lambda_val + 1e-20)
        # Asumimos viscosidad incluida o normalizada en la permeabilidad efectiva
        return pre_factor * coth_stable(lambda_val * L_dist)

    def _R_semi_inf(self, s, lambda_val, k, h):
        """
        Solución para un medio semi-infinito.
        Eq. base: (mu / k*h) * (1 / lambda)
        """
        return 1.0 / (k * h * lambda_val + 1e-20)

    # ================= CONSTRUCCIÓN DE LA MATRIZ =================

    def build_matrix(self, wells_params: list, project_params: dict):
        """
        Construye la matriz de interacción R paso a paso.
        
        Args:
            wells_params: Lista de dicts con datos adimensionales de cada pozo (output de adimensional.py).
            project_params: Dict con datos físicos globales (mu, ct, h, k_ref, etc.).
        """
        # Extraemos constantes globales
        mu = project_params["mu_pas"]   # Viscosidad [Pa.s]
        ct = project_params["ct_pa"]    # Compresibilidad [1/Pa]
        h = project_params["h_m"]       # Espesor [m]
        # Nota: k_ref ya se usó para adimensionalizar, aquí usamos k local de cada bloque
        
        # Recorremos la matriz R elemento por elemento
        for i in range(self.n):
            target_well = wells_params[i]
            
            for j in range(self.n):
                source_well = wells_params[j]
                
                # --- 1. Propiedades del Medio entre Pozos ---
                # Usamos las propiedades del "Outer Reservoir" (Matriz Original) para la interferencia
                # Si implementamos heterogeneidad, aquí elegiríamos k promedio
                k_res = project_params["k_ref_m2"] 
                phi_res = project_params["phi"]
                
                # Doble Porosidad Global
                f_s = f_function(self.s, project_params.get("omega", 1), project_params.get("lam", 0))
                
                # Lambda efectivo considerando doble porosidad: s -> s * f(s)
                s_eff = self.s * f_s
                lam_res = self._lambda_trilinear(s_eff, k_res, phi_res, mu, ct)

                # --- 2. Cálculo de la Interacción R_ij ---
                
                dist_y = abs(target_well["y_D"] - source_well["y_D"]) * project_params["x_fr_ref_m"]
                
                if i == j:
                    # DIAGONAL: Efecto del pozo sobre sí mismo (Self-Potential)
                    # Modelo simplificado: Flujo lineal desde el borde del SRV hacia la fractura
                    # R_ii = Resistencia SRV + Skin
                    
                    # Propiedades locales del SRV del pozo i
                    # Nota: Para rigor completo, deberíamos usar k_srv específico si existe
                    # Por ahora usamos el del reservorio para simplificar la primera versión
                    
                    # Usamos solución de slab (flujo lineal finito) hasta la distancia de interferencia media
                    # O solución semi-infinita si están muy lejos
                    val_R = self._R_semi_inf(s_eff, lam_res, k_res, h) * mu
                    
                    # Agregamos Skin (aditivo en Laplace)
                    # Skin se define como caída de presión extra: dp_skin = S * q
                    # Como R * q = dp, sumamos S a la resistencia
                    # (Ajuste simplificado, el modelo riguroso de piel es más complejo)
                    skin_term = 0.0 # Se puede implementar usando target_well['C_fD']
                    
                    self.R[i, j] = val_R + skin_term
                    
                else:
                    # FUERA DE DIAGONAL: Interferencia (Cross-Potential)
                    # Decaimiento exponencial de la presión con la distancia (Kernel 1D)
                    # R_ij = R_source * exp(-lambda * distancia)
                    
                    base_R = self._R_semi_inf(s_eff, lam_res, k_res, h) * mu
                    interferencia = exp_clamped(-lam_res * dist_y)
                    
                    self.R[i, j] = base_R * interferencia

    def solve_pressure(self, rates_laplace: np.ndarray) -> np.ndarray:
        """
        Caso Directo: Calculamos Presiones dados los Caudales.
        p_vec = R * q_vec
        """
        return np.dot(self.R, rates_laplace)

    def solve_rates(self, delta_p_laplace: np.ndarray) -> np.ndarray:
        """
        Caso Inverso: Calculamos Caudales dadas las Caídas de Presión (Pressure Control).
        q_vec = inv(R) * dp_vec
        """
        return scipy.linalg.solve(self.R, delta_p_laplace)