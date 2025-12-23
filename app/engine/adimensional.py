import math
from app.models.well_models import Project, Well
from app.engine.physics_utils import (
    PSI_TO_PA, FT_TO_M, CP_TO_PAS, MD_TO_M2, ND_TO_M2, DAY_TO_S
)

# ================= CONFIGURACIÓN DE UNIDADES =================
INPUT_IN_MD = True  
# =============================================================

class AdimConverter:
    def __init__(self, project: Project):
        """
        Define las variables de referencia globales (Subscript R en el paper).
        Referencia: Ecs. 4, 5 y 10.
        """
        self.k_factor = MD_TO_M2 if INPUT_IN_MD else ND_TO_M2
        
        # 1. Propiedades de Referencia (SI)
        self.k_ref_m2 = project.k_ref * self.k_factor
        self.mu_pas = project.mu * CP_TO_PAS
        self.ct_pa = project.ct / PSI_TO_PA
        self.h_m = project.h * FT_TO_M
        self.phi_ref = project.phi
        
        # 2. Difusividad de Referencia (eta_R) - Eq. 4
        # eta_R = k_R / (phi_R * mu * ct_R)
        self.eta_R = self.k_ref_m2 / (self.phi_ref * self.mu_pas * self.ct_pa + 1e-20)

        # 3. Espesor adimensional global - Eq. 19
        # h_D = h / x_FR (se calcula usando el x_f del pozo de referencia luego)
        self.project = project

    def get_well_params(self, well: Well, x_fr_ref_ft: float) -> dict:
        """
        Genera parámetros adimensionales específicos por pozo.
        Normaliza todo por la longitud de referencia x_FR.
        """
        x_fr_ref_m = x_fr_ref_ft * FT_TO_M
        
        # --- Propiedades Físicas Locales ---
        k_srv = (well.k_srv if well.k_srv is not None else self.project.k_ref) * self.k_factor
        phi_srv = well.phi_srv if well.phi_srv is not None else self.project.phi
        x_f_m = well.x_f * FT_TO_M
        r_w_m = (well.r_w if well.r_w else 0.3) * FT_TO_M
        
        # --- Variables Adimensionales del Paper ---

        # 1. Semilongitud de fractura adimensional (x_fiD) - Eq. 15
        x_fD = x_f_m / x_fr_ref_m

        # 2. Difusividad adimensional (eta_Di) - Eq. 12
        eta_local = k_srv / (phi_srv * self.mu_pas * self.ct_pa + 1e-20)
        eta_D = eta_local / self.eta_R

        # 3. Espesor y Radio de pozo adimensional - Ecs. 19 y 20
        h_D = self.h_m / x_fr_ref_m
        r_wD = r_w_m / x_fr_ref_m

        # 4. Semidistancia entre fracturas adimensional (y_eIiD) - Eq. 17
        # Nota: spacing_y suele ser la distancia total, usamos la mitad para y_e
        y_e_m = (well.spacing_y * FT_TO_M) / 2.0
        y_eD = y_e_m / x_fr_ref_m

        # 5. Conductividad de fractura adimensional (C_fD) - Eq. 21
        # C_fD = (k_f * w_f) / (k_gI * x_f) 
        # well.conductivity suele estar en mD-ft, lo pasamos a adimensional
        # k_gI es la permeabilidad del SRV (k_srv)
        C_fD = (well.conductivity * self.k_factor * FT_TO_M) / (k_srv * x_f_m + 1e-20)

        # 6. Flow-Choking Skin (s_cFi) - Eq. 53
        # s_cFi = (q_iD * h_D) / (n_f * C_fD * k_fD * x_fD) * [ln(h_D/2r_wD) - pi/2]
        # Simplificando para el factor de forma radial:
        choking_factor = (h_D / (well.n_f * C_fD + 1e-20)) * (math.log(self.h_m / (2.0 * r_w_m)) - (math.pi / 2.0))

        return {
            "well_id": well.id,
            "x_f_D": x_fD,
            "eta_D": eta_D,
            "h_D": h_D,
            "r_wD": r_wD,
            "y_eD": y_eD,
            "C_fD": C_fD,
            "s_cf": choking_factor,
            "n_f": well.n_f,
            "t_start": well.t_0 * DAY_TO_S,
            # Parámetros de Doble Porosidad del pozo
            "omega": well.omega if hasattr(well, 'omega') else self.project.omega,
            "lam": well.lam if hasattr(well, 'lam') else self.project.lam
        }

    def time_to_dimensionless(self, t_seconds: float, x_fr_ref_ft: float) -> float:
        """
        Convierte tiempo real a tiempo adimensional (t_D).
        Referencia: Eq. 3.
        """
        x_ref_m = x_fr_ref_ft * FT_TO_M
        return (self.eta_R * t_seconds) / (x_ref_m ** 2)