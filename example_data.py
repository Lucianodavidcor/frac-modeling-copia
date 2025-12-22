# example_data.py
# Ejemplos del paper SPE-215031-PA (Tablas 3 y 4)
# Migrado a esquema params + well_params + schedules

import numpy as np

# === Example 1 – Rate Variations Including Shut-In (Tabla 3) ===
ex1_params = {
    # Propiedades genéricas (paper no especifica todas aquí, usamos base estándar)
    "mu": 1.0,     # cP
    "ct": 1e-6,    # 1/psi
    "k_I": 800,    # nD (SRV)
    "k_O": 150,    # nD (ORV)
    "h": 65.6,     # ft
    "LxI": 100,    # ft
    "LxOend": 2000,# ft
    "xe": 50,      # semi-spacing fracturas
    "p_res": 4350, # psi
}

ex1_well_params = {
    "well_1": {"n_frac": 25, "spacing": 300, "color": "blue"},
    "well_2": {"n_frac": 25, "spacing": 300, "color": "red"},
    "well_3": {"n_frac": 25, "spacing": 300, "color": "green"},
}

ex1_schedules = {
    "well_1": [
        {"t_ini": 0.0, "q": 0},
        {"t_ini": 1.0, "q": 1000},
        {"t_ini": 5.0, "q": 500},
        {"t_ini": 10.0, "q": 2000},
    ],
    "well_2": [
        {"t_ini": 0.0, "q": 0},
        {"t_ini": 1.0, "q": 1000},
        {"t_ini": 8.0, "q": 1500},
    ],
    "well_3": [
        {"t_ini": 0.0, "q": 0},
        {"t_ini": 3.0, "q": 1000},
        {"t_ini": 9.0, "q": 2500},
        {"t_ini": 20.0, "q": 1000},
    ],
}

# === Example 2 – Pressure Interference of Infill (Child) Well (Tabla 4) ===
ex2_params = {
    "mu": 0.83,       # cP
    "ct": 3e-5,       # 1/psi (matriz)
    "k_I": 20.0,      # md (fractura) → ~2.0e-2 md
    "k_O": 20.0,      # md (outer matriz)
    "h": 100,         # ft
    "LxI": 5000,      # ft (SRV length)
    "LxOend": 50,     # ft (outer reservoir width)
    "xe": 200,        # ft (fracture half-length)
    "p_res": 2260,    # psi (drawdown target en paper)
    "phi_f": 0.4,
    "phi_m": 0.05,
    "ct_f": 3e-4,
    "ct_m": 3e-5,
    "k_f": 200,       # md (fracturas)
    "dp_cf": 50,
}

ex2_well_params = {
    "well_1": {"n_frac": 25, "spacing": 300, "color": "blue"},
    "well_2": {"n_frac": 25, "spacing": 300, "color": "red"},
    "well_3": {"n_frac": 25, "spacing": 300, "color": "green"},
}

ex2_schedules = {
    "well_1": [
        {"t_ini": 0.0, "q": 8000},
    ],
    "well_2": [
        {"t_ini": 0.0, "q": 8000},
        {"t_ini": 380.0, "q": 7920},   # -1% approx
        {"t_ini": 2000.0, "q": 7200},  # -10% approx
        {"t_ini": 10000.0, "q": 0},    # shut-in at late time
    ],
    "well_3": [
        {"t_ini": 0.0, "q": 8000},
    ],
}
# === Example 3 – Production Interference of Infill (Child) Well (Tabla 5) ===
ex3_params = {
    "mu": 0.8,            # cP
    "ct": 2e-5,           # 1/psi (matriz)
    "k_I": 3.59e-5,       # md (inner SRV matriz k_mI0 en tabla) ≈ 3.59e-5 md
    "k_O": 2e-5,          # md (outer matriz k_mO0 en tabla)
    "h": 80,              # ft
    "LxI": 5000,          # ft
    "LxOend": 50,         # ft
    "xe": 200,            # ft (half-length fractura)
    "p_res": 3000,        # psi drawdown en tabla
    "phi_f": 0.4,
    "phi_m": 0.05,
    "ct_f": 3e-5,
    "ct_m": 2e-5,
    "k_f": 50,            # md (fracturas Parent e Infill ~5e4 md-ft / Wf 0.1 ft → ~50 md)
    "dp_cf": 50,
}

ex3_well_params = {
    "well_1": {"n_frac": 13, "spacing": 1000, "color": "blue"},   # Parent 1
    "well_2": {"n_frac": 25, "spacing": 1640, "color": "red"},    # Parent 2
    "well_3": {"n_frac": 25, "spacing": 640,  "color": "green"},  # Infill
}

# Schedules:
# - Parent wells producen desde t=0 con Δp=3000 psi (equivalente a q constante).
# - Infill arranca en t=4320 h = 180 días.
# Vamos a representarlo como caudal constante (ejemplo: 3000 STB/d) para todos.
ex3_schedules = {
    "well_1": [
        {"t_ini": 0.0, "q": 3000},
    ],
    "well_2": [
        {"t_ini": 0.0, "q": 3000},
    ],
    "well_3": [
        {"t_ini": 0.0, "q": 0},       # Inactivo hasta 180 d
        {"t_ini": 180.0, "q": 3000},  # arranca Infill
    ],
}

# === Diccionario maestro con todos los ejemplos ===
examples = {
    "Example 1 - Rate Variations": {
        "params": ex1_params,
        "well_params": ex1_well_params,
        "schedules": ex1_schedules,
    },
    "Example 2 - Infill Interference": {
        "params": ex2_params,
        "well_params": ex2_well_params,
        "schedules": ex2_schedules,
    },
    "Example 3 - Infill Child" : {
        "params": ex3_params,
        "well_params": ex3_well_params,
        "schedules": ex3_schedules,
    },
}

# === Utilidad Laplace (misma de antes) ===
def q_hat(schedule, s):
    total = 0.0
    for k in range(1, len(schedule)):
        qk = schedule[k]["q"]
        qk1 = schedule[k-1]["q"]
        tprev = schedule[k-1]["t_ini"] * 24 * 3600
        total += (qk - qk1) * np.exp(-s * tprev)
    return total / s
