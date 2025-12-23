import numpy as np
import scipy.linalg
from app.engine.dual_porosity import f_function

class TrilinearMatrixSolver:
    def __init__(self, s_val: complex, num_wells: int):
        """
        Inicializa el sistema matricial para el Modelo Trilineal Acoplado.
        Tamaño de Matriz: 2n x 2n (n ecuaciones de pozo + n ecuaciones de reservorio).
        """
        self.s = s_val
        self.n = num_wells
        
        # El sistema es 2*n porque incluimos presiones de reservorio (SRV/ORV)
        self.size = 2 * self.n
        
        self.A = np.zeros((self.size, self.size), dtype=complex)
        self.b = np.zeros(self.size, dtype=complex)

    def _calculate_coefficients(self, wells_params: list, project_params: dict, rates_dimless: np.ndarray = None) -> dict:
        """
        Calcula coeficientes TRILINEALES. 
        IMPORTANTE: 'rates_dimless' debe ser adimensional (ej. 1/s para caudal constante).
        """
        coeffs = {
            'gamma_Fi': [], 'alpha_Fi': [], 'alpha_Oi': [],
            'gamma_Oi_prev': [], 'gamma_Oi_next': [],
            'r_i': [], 'tau_ii': [], 'tau_prev': [], 'tau_next': []
        }

        # Si no hay tasas definidas, asumimos 1.0 (Unitario)
        if rates_dimless is None:
            q_s_vec = np.ones(self.n, dtype=complex)
        else:
            q_s_vec = rates_dimless

        for i in range(self.n):
            w = wells_params[i]
            
            # --- 1. Doble Porosidad ---
            f_s = f_function(self.s, project_params.get("omega", 1), project_params.get("lam", 0))
            u_res = self.s * f_s 

            # --- 2. Reservorio Externo (ORV) ---
            eta_OiD = 1.0 
            alpha_Oi = np.sqrt(u_res / eta_OiD)
            coeffs['alpha_Oi'].append(alpha_Oi)

            # --- 3. SRV y Fractura ---
            beta_Fi = 1.0 
            C_fD = w["C_fD"]
            eta_FiD = w["eta_D"]
            
            # alpha_Fi = sqrt( (2 * beta_Fi / C_fD) + (s / eta_FiD) )
            term_alpha_f = (2 * beta_Fi / (C_fD + 1e-20)) + (self.s / eta_FiD)
            alpha_Fi = np.sqrt(term_alpha_f)
            coeffs['alpha_Fi'].append(alpha_Fi)

            # --- 4. Término de Fuente (r_i) ---
            # Tangente hiperbólica estable
            tanh_alpha = np.tanh(alpha_Fi) if alpha_Fi.real < 20 else 1.0
            
            # Denominador de la fuente trilineal
            denom = (C_fD * alpha_Fi * tanh_alpha) + 1e-20
            
            # Cálculo final de r_i (Adimensional)
            # r_i = (pi / denom) * q_D
            val_r_i = (np.pi / denom) * q_s_vec[i]
            
            coeffs['r_i'].append(val_r_i)

            # --- 5. Matriz ---
            tanh_alpha_o = np.tanh(alpha_Oi) if alpha_Oi.real < 20 else 1.0
            epsilon_i = tanh_alpha_o / (alpha_Oi + 1e-20)
            coeffs['tau_ii'].append(epsilon_i)
            coeffs['gamma_Fi'].append(1.0)

            # --- 6. Interferencia ---
            val_tau_prev = val_tau_next = 0.0
            val_gamma_prev = val_gamma_next = 0.0

            if i > 0:
                dist = abs(w["y_D"] - wells_params[i-1]["y_D"])
                coupling = np.exp(-alpha_Oi * dist)
                val_tau_prev = val_gamma_prev = coupling

            if i < self.n - 1:
                dist = abs(w["y_D"] - wells_params[i+1]["y_D"])
                coupling = np.exp(-alpha_Oi * dist)
                val_tau_next = val_gamma_next = coupling

            coeffs['tau_prev'].append(val_tau_prev)
            coeffs['tau_next'].append(val_tau_next)
            coeffs['gamma_Oi_prev'].append(val_gamma_prev)
            coeffs['gamma_Oi_next'].append(val_gamma_next)

        return coeffs

    def build_matrix(self, wells_params: list, project_params: dict, rates_dimless: np.ndarray = None):
        """
        Ensambla A y b. Acepta rates_dimless para calcular b correctamente.
        """
        coeffs = self._calculate_coefficients(wells_params, project_params, rates_dimless)
        n = self.n
        
        for i in range(n):
            # --- Bloque Pozo ---
            self.A[i, i] = -1.0 
            term_trans = coeffs['gamma_Fi'][i] * coeffs['tau_ii'][i]
            self.A[i, i + n] = term_trans
            
            if i > 0: self.A[i, i - 1 + n] = coeffs['gamma_Oi_prev'][i] * term_trans
            if i < n - 1: self.A[i, i + 1 + n] = coeffs['gamma_Oi_next'][i] * term_trans

            self.b[i] = coeffs['r_i'][i]

            # --- Bloque Roca ---
            row = i + n
            self.A[row, row] = -1.0 
            self.A[row, i] = coeffs['tau_ii'][i]

            if i > 0: self.A[row, row - 1] = coeffs['tau_prev'][i]
            if i < n - 1: self.A[row, row + 1] = coeffs['tau_next'][i]
                
            self.b[row] = 0.0

    def solve(self) -> np.ndarray:
        try:
            return np.linalg.solve(self.A, self.b)
        except np.linalg.LinAlgError:
            return np.zeros(self.size, dtype=complex)