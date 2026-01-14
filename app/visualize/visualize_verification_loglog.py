import requests
import matplotlib.pyplot as plt
import numpy as np

# CONFIGURACIÓN
# Cambia el ID al del proyecto que acabas de crear (por tu error anterior, asumo que es el 2)
PROJECT_ID = 2
API_URL = f"http://127.0.0.1:8000/simulate/{PROJECT_ID}/curve"


def plot_verification_loglog():
    # Parámetros para la verificación del paper SPE-215031-PA (Fig. 6)
    # total_days=100000 para capturar el final de la curva (Dominio de bordes)
    # log_scale=True para obtener la resolución de 10^-5 días
    params = {
        "total_days": 100000,
        "log_scale": True
    }

    print(f"Solicitando datos de verificación a la API: {API_URL}...")

    try:
        # 1. Obtener datos de la API
        response = requests.post(API_URL, params=params)
        response.raise_for_status()
        json_data = response.json()

        simulation_results = json_data["data"]
        time = np.array(simulation_results["time"])
        curves = simulation_results["curves"]

        # 2. Configurar el gráfico
        plt.figure(figsize=(11, 8))
        plt.style.use('seaborn-v0_8-whitegrid')

        # 3. Graficar cada pozo (deberían verse los 3 iguales)
        for well_name, data in curves.items():
            dp = np.array(data["delta_p"])
            derivative = np.array(data["derivative"])

            # Filtramos valores para evitar errores en escala logarítmica (solo valores > 0)
            valid = (time > 0) & (dp > 0)

            # Estilo visual idéntico al Paper:
            # Presión (Delta P): Círculos azules
            plt.loglog(time[valid], dp[valid], 'bo',
                       label=f'Multi-Well Pressure - {well_name}',
                       markersize=4, alpha=0.6, markeredgecolor='none')

            # Derivada de Bourdet: Cuadrados verdes
            plt.loglog(time[valid], derivative[valid], 'gs',
                       label=f'Multi-Well Derivative - {well_name}',
                       markersize=4, alpha=0.6, markeredgecolor='none')

        # 4. Formato de Ingeniería (Ejes y Etiquetas)
        plt.title(f"Verificación del Modelo - Proyecto: {json_data['project']}", fontsize=14)
        plt.xlabel("Time, t, days", fontsize=12)
        plt.ylabel("Δpwf and dΔpwf/dln t, psi", fontsize=12)

        # Límites de los ejes para que coincida con la Figura 6 del paper
        plt.xlim(1e-5, 1e5)
        plt.ylim(1e-2, 1e5)

        # Rejilla técnica
        plt.grid(True, which="both", linestyle='--', alpha=0.5)
        plt.legend(loc='lower right', shadow=True, fontsize=10)

        # 5. Guardar y mostrar
        print("Generando gráfico de verificación Log-Log...")
        output_name = "resultado_verificacion_loglog_final.png"
        plt.savefig(output_name, dpi=300)
        print(f"¡Éxito! El gráfico se guardó como '{output_name}'")
        plt.show()

    except Exception as e:
        print(f"Error al visualizar la verificación: {e}")


if __name__ == "__main__":
    plot_verification_loglog()
