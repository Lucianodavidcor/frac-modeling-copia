import requests
import matplotlib.pyplot as plt
import numpy as np

# CONFIGURACIÓN
PROJECT_ID = 1
# Nota: Asegúrate de que total_days sea alto (ej. 10000) y step_days sea pequeño 
# para capturar bien los tiempos tempranos en el log-log.
API_URL_CURVE = f"http://127.0.0.1:8000/simulate/{PROJECT_ID}/curve"
API_URL_PROJECT = f"http://127.0.0.1:8000/projects/{PROJECT_ID}"

def plot_verification_loglog():
    try:
        # 1. Obtener la Presión Inicial del proyecto
        print("Obteniendo datos del proyecto...")
        proj_resp = requests.get(API_URL_PROJECT)
        proj_resp.raise_for_status()
        p_initial = proj_resp.json()["initial_pressure"]

        # 2. Obtener los resultados de la simulación
        print(f"Solicitando curvas de simulación a: {API_URL_CURVE}...")
        params = {"total_days": 10000, "step_days": 1} # Ajusta según necesites
        response = requests.post(API_URL_CURVE, params=params)
        response.raise_for_status()
        data = response.json()["data"]
        
        time = np.array(data["time"])
        
        plt.figure(figsize=(10, 8))
        plt.style.use('seaborn-v0_8-whitegrid')

        # 3. Procesar cada pozo para calcular Delta P y Derivada
        for well_name, pressures in data["curves"].items():
            p_wf = np.array(pressures)
            delta_p = p_initial - p_wf
            
            # Solo procesamos si hay caída de presión (evitar log(0))
            valid = delta_p > 0.01
            t_v = time[valid]
            dp_v = delta_p[valid]

            if len(t_v) < 3: continue

            # Cálculo de la Derivada de Bourdet: d(DeltaP) / d(ln t)
            # Usamos diferencias centrales en el dominio logarítmico
            log_t = np.log(t_v)
            derivative = np.gradient(dp_v, log_t)

            # 4. Graficar al estilo del Paper SPE-215031-PA
            # Presión: Círculos azules (usamos markersize pequeño para claridad)
            plt.loglog(t_v, dp_v, 'bo', label=f'Pressure - {well_name}', 
                       markersize=4, alpha=0.7, markeredgecolor='none')
            
            # Derivada: Cuadrados verdes
            plt.loglog(t_v, derivative, 'gs', label=f'Derivative - {well_name}', 
                       markersize=4, alpha=0.7, markeredgecolor='none')

        # 5. Formato de Ingeniería
        plt.title(f"Verificación del Modelo (Log-Log) - Proyecto {PROJECT_ID}", fontsize=14)
        plt.xlabel("Time, t, days", fontsize=12)
        plt.ylabel("Δpwf and dΔpwf/dln t, psi", fontsize=12)
        
        # Líneas de referencia para pendientes (opcional)
        # Pendiente 1 (Wellbore Storage): 45°
        # Pendiente 1/4 (Bilinear Flow)
        # Pendiente 1/2 (Linear Flow)
        
        plt.grid(True, which="both", linestyle='--', alpha=0.5)
        plt.legend(loc='lower right', frameon=True, shadow=True)
        
        # Ajuste de límites basado en el paper (Fig 6)
        plt.xlim(1e-3, 1e5) # Empezamos en 1e-3 porque step_days=1 es el mínimo actual
        plt.ylim(1e-1, 1e5)

        print("Generando gráfico Log-Log de verificación...")
        plt.savefig("resultado_verificacion_spe_fig6.png")
        plt.show()

    except Exception as e:
        print(f"Error en la visualización: {e}")

if __name__ == "__main__":
    plot_verification_loglog()