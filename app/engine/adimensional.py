import math
from app.models.well_models import Project, Well
from app.engine.physics_utils import (
    PSI_TO_PA, FT_TO_M, CP_TO_PAS, ND_TO_M2, DAY_TO_S
)

class AdimConverter:
    def __init__(self, project: Project):
        """
        Calcula las variables de referencia globales del proyecto (Pad).
        Basado en math_adim.py
        """
        # 1. Convertir unidades de Campo a SI para cálculos internos correctos
        self.k_ref_m2 = project.k_ref * ND_TO_M2
        self.mu_pas = project.mu * CP_TO_PAS
        self.ct_pa = project.ct / PSI_TO_PA
        self.h_m = project.h * FT_TO_M
        self.phi = project.phi
        
        # 2. Difusividad Hidráulica de Referencia (eta_R) [m^2/s]
        # eta = k / (phi * mu * ct)
        self.eta_R = self.k_ref_m2 / (self.phi * self.mu_pas * self.ct_pa)

        # Guardamos referencias para uso posterior
        self.project = project

    def get_well_params(self, well: Well, x_fr_ref: float) -> dict:
        """
        Genera los parámetros adimensionales específicos para un pozo.
        
        Args:
            well: Objeto Well de la DB.
            x_fr_ref: Longitud de fractura de referencia (usualmente la del Padre) para normalizar distancias.
        """
        # Propiedades SRV específicas (o fallback a proyecto)
        k_srv = well.k_srv if well.k_srv is not None else self.project.k_ref
        phi_srv = well.phi_srv if well.phi_srv is not None else self.project.phi
        
        # Conversiones locales
        k_srv_m2 = k_srv * ND_TO_M2
        x_f_m = well.x_f * FT_TO_M
        x_fr_ref_m = x_fr_ref * FT_TO_M
        
        # --- Variables Adimensionales (Math Engine) ---
        
        # 1. Distancias Adimensionales (Normalizadas por x_fr_ref)
        # y_D = distancia / x_f_referencia
        y_D = (well.spacing_y * FT_TO_M) / x_fr_ref_m
        
        # 2. Conductividad Adimensional de Fractura (C_fD)
        # Ya viene calculada o se pasa directo si el input es C_fD.
        # Si el input fuera conductividad en md-ft, la fórmula sería:
        # C_fD = (k_f * w) / (k_res * x_f)
        C_fD = well.conductivity 
        
        # 3. Difusividad Adimensional local (eta_D)
        # Si el SRV tiene k distinta, eta cambia.
        # eta_local = k_srv / (phi_srv * mu * ct)
        eta_local = k_srv_m2 / (phi_srv * self.mu_pas * self.ct_pa)
        eta_D = eta_local / self.eta_R

        return {
            "well_id": well.id,
            "y_D": y_D,
            "C_fD": C_fD,
            "eta_D": eta_D,
            "n_f": well.n_f,
            "x_f_D": x_f_m / x_fr_ref_m, # Relación de longitudes si son distintas
            "t_start": well.t_0 * DAY_TO_S # Tiempo de inicio en segundos (para Stehfest)
        }

    def time_to_dimensionless(self, t_seconds: float, x_fr_ref_ft: float) -> float:
        """Convierte tiempo real (s) a t_D"""
        x_ref_m = x_fr_ref_ft * FT_TO_M
        # t_D = (eta_R * t) / x_ref^2
        return (self.eta_R * t_seconds) / (x_ref_m ** 2)