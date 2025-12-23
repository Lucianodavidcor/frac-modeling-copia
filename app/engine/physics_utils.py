import numpy as np
import math

# ================= Conversión Field ↔ SI =================
PSI_TO_PA = 6894.757293168
FT_TO_M   = 0.3048
CP_TO_PAS = 1e-3

# --- UNIDADES DE PERMEABILIDAD ---
# NanoDarcies (Para Shale / No Convencional)
ND_TO_M2  = 9.869233e-22  
# MiliDarcies (Para Convencional / Pruebas de Frac-Hit)
MD_TO_M2  = 9.869233e-16  

DAY_TO_S  = 86400.0
STB_TO_M3 = 0.158987294928

def si_mu(mu_cp):     return mu_cp * CP_TO_PAS

# Función genérica: la conversión la maneja adimensional.py según el modo
def si_k_generic(k_val, factor): return k_val * factor

def si_ct(ct_invpsi): return ct_invpsi / PSI_TO_PA
def si_h(h_ft):       return h_ft * FT_TO_M
def si_L(L_ft):       return L_ft * FT_TO_M
def field_p(p_pa):    return p_pa / PSI_TO_PA

# ================= Algoritmo de Stehfest =================
def stehfest_weights(N: int) -> np.ndarray:
    """
    Calcula los coeficientes V_i para el algoritmo de Stehfest.
    N debe ser un número par (ej. 12).
    """
    if N % 2 != 0:
        raise ValueError("El número de Stehfest N debe ser par.")
    
    fac = math.factorial
    V = np.zeros(N)
    
    for k in range(1, N + 1):
        s = 0.0
        j_min = (k + 1) // 2
        j_max = min(k, N // 2)
        
        for j in range(j_min, j_max + 1):
            num = (j**(N // 2)) * fac(2 * j)
            den = (fac(N // 2 - j) * fac(j) * fac(j - 1) * fac(k - j) * fac(2 * j - k))
            s += num / den
            
        V[k-1] = s * ((-1)**(k + N // 2))
        
    return V