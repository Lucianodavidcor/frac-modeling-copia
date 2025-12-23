import math
import numpy as np

def f_function(s: complex, omega: float, lam: float) -> complex:
    """
    Calcula la función de transferencia f(s) para doble porosidad.
    Referencia: Eq. (31) del paper y math_dualporosity.py
    
    Args:
        s: Variable de Laplace (compleja).
        omega: Storativity ratio (0 < omega <= 1).
        lam: Coeficiente de interporosidad (lambda).
    """
    # Protecciones numéricas para evitar división por cero
    omega = float(omega) if omega is not None else 1.0
    lam = float(lam) if lam is not None else 0.0

    if abs(lam) < 1e-12 or abs(1.0 - omega) < 1e-6:
        # Caso porosidad simple (omega=1 o lambda=0)
        return 1.0 + 0j

    # Evitamos raíz cuadrada de números negativos o ceros problemáticos
    s_val = s if abs(s) > 1e-20 else 1e-20
    
    # f(s) = omega + sqrt[ lambda*(1-omega)/(3s) ] * tanh[ sqrt(3*(1-omega)*s/lambda) ]
    term1 = math.sqrt((lam * (1.0 - omega)) / 3.0)
    term2 = math.sqrt((3.0 * (1.0 - omega)) / lam)
    
    # Manejo de tanh para argumentos complejos grandes (overflow protection)
    arg_tanh = term2 * np.sqrt(s_val)
    if arg_tanh.real > 20: 
        tanh_val = 1.0
    else:
        tanh_val = np.tanh(arg_tanh)

    return omega + (term1 / np.sqrt(s_val)) * tanh_val