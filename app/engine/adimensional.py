import math
from app.models.well_models import Project, Well
from app.engine.physics_utils import (
    PSI_TO_PA, FT_TO_M, CP_TO_PAS, MD_TO_M2, ND_TO_M2, DAY_TO_S
)

# ================= CONFIGURACIÓN DE UNIDADES =================
# True  = Tus datos en la DB están en MiliDarcies (mD). [Úsalo para Frac-Hit visible]
# False = Tus datos en la DB están en NanoDarcies (nD). [Úsalo para Shale real]
INPUT_IN_MD = True  
# =============================================================

class AdimConverter:
    def __init__(self, project: Project):
        """
        Calcula las variables de referencia globales del proyecto (Pad).
        """
        # Seleccionamos el factor de conversión según el interruptor
        self.k_factor = MD_TO_M2 if INPUT_IN_MD else ND_TO_M2
        
        # 1. Convertir unidades de Campo a SI 
        self.k_ref_m2 = project.k_ref * self.k_factor
        
        self.mu_pas = project.mu * CP_TO_PAS
        self.ct_pa = project.ct / PSI_TO_PA
        self.h_m = project.h * FT_TO_M
        self.phi = project.phi
        
        # 2. Difusividad Hidráulica de Referencia (eta_R) [m^2/s]
        self.eta_R = self.k_ref_m2 / (self.phi * self.mu_pas * self.ct_pa)

        # Guardamos referencias para uso posterior
        self.project = project

    def get_well_params(self, well: Well, x_fr_ref: float) -> dict:
        """
        Genera los parámetros adimensionales específicos para un pozo.
        """
        # Propiedades SRV específicas (o fallback a proyecto)
        k_srv = well.k_srv if well.k_srv is not None else self.project.k_ref
        phi_srv = well.phi_srv if well.phi_srv is not None else self.project.phi
        
        # Conversiones locales (Usando el mismo factor k_factor)
        k_srv_m2 = k_srv * self.k_factor
        
        x_f_m = well.x_f * FT_TO_M
        x_fr_ref_m = x_fr_ref * FT_TO_M
        
        # --- Variables Adimensionales (Math Engine) ---
        
        # 1. Distancias Adimensionales (Normalizadas por x_fr_ref)
        y_D = (well.spacing_y * FT_TO_M) / x_fr_ref_m
        
        # 2. Conductividad Adimensional
        C_fD = well.conductivity 
        
        # 3. Difusividad Adimensional local (eta_D)
        eta_local = k_srv_m2 / (phi_srv * self.mu_pas * self.ct_pa)
        eta_D = eta_local / self.eta_R

        return {
            "well_id": well.id,
            "y_D": y_D,
            "C_fD": C_fD,
            "eta_D": eta_D,
            "n_f": well.n_f,
            "x_f_D": x_f_m / x_fr_ref_m, 
            "t_start": well.t_0 * DAY_TO_S 
        }

    def time_to_dimensionless(self, t_seconds: float, x_fr_ref_ft: float) -> float:
        """Convierte tiempo real (s) a t_D"""
        x_ref_m = x_fr_ref_ft * FT_TO_M
        return (self.eta_R * t_seconds) / (x_ref_m ** 2)