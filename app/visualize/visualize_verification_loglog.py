import requests
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# CONFIGURACIÓN
# ==========================================
# Cambia el ID al del proyecto con initial_pressure = 1,000,000
PROJECT_ID = 2
API_URL = f"http://127.0.0.1:8000/simulate/{PROJECT_ID}/curve"


def plot_verification_final():
    # Parámetros para replicar exactamente el rango del paper
    params = {
        "total_days": 100000,
        "log_scale": True  # Vital para obtener resolución desde 10^-5 días
    }

    print(f"Solicitando datos de validación para Proyecto {PROJECT_ID}...")

    try:
        # 1. Obtener datos de la API
        response = requests.post(API_URL, params=params)
        response.raise_for_status()
        json_data = response.json()

        sim_data = json_data["data"]
        time = np.array(sim_data["time"])
        curves = sim_data["curves"]

        # 2. Configurar el estilo del gráfico
        plt.figure(figsize=(11, 8))
        plt.style.use('seaborn-v0_8-whitegrid')

        # 3. Graficar la referencia de Pozo Único (Líneas Sólidas)
        # Usamos los datos del primer pozo como referencia analítica
        first_well_name = list(curves.keys())[0]
        ref_dp = np.array(curves[first_well_name]["delta_p"])
        ref_der = np.array(curves[first_well_name]["derivative"])

        valid_ref = (time > 0) & (ref_dp > 0)

        plt.loglog(time[valid_ref], ref_dp[valid_ref], 'r-',
                   label='Single-Well Pressure (Analytical Ref)', linewidth=1.5, zorder=1)
        plt.loglog(time[valid_ref], ref_der[valid_ref], color='orange', linestyle='-',
                   label='Single-Well Derivative (Analytical Ref)', linewidth=1.5, zorder=1)

        # 4. Graficar los 3 Pozos del Simulador (Puntos/Marcadores)
        # Se verán solapados sobre la línea de referencia si el modelo es correcto
        for i, (well_name, data) in enumerate(curves.items()):
            dp = np.array(data["delta_p"])
            der = np.array(data["derivative"])
            valid = (time > 0) & (dp > 0)

            # Presión: Círculos azules
            plt.loglog(time[valid], dp[valid], 'bo',
                       label=f'Multi-Well Pressure - {well_name}' if i == 0 else "",
                       markersize=4, alpha=0.5, markeredgecolor='none', zorder=2)

            # Derivada: Cuadrados verdes
            plt.loglog(time[valid], der[valid], 'gs',
                       label=f'Multi-Well Derivative - {well_name}' if i == 0 else "",
                       markersize=4, alpha=0.5, markeredgecolor='none', zorder=2)

        # 5. Formato de Ingeniería (Fig. 6 SPE-215031-PA)
        plt.title(f"Verificación del Modelo Multi-Pozo vs Pozo Único\nProyecto: {json_data['project']}", fontsize=14)
        plt.xlabel("Time, t, days", fontsize=12)
        plt.ylabel("Δpwf and dΔpwf/dln t, psi", fontsize=12)

        # Límites idénticos al paper
        plt.xlim(1e-5, 1e5)
        plt.ylim(1e-2, 1e5)

        plt.grid(True, which="both", linestyle='--', alpha=0.4)
        plt.legend(loc='lower right', frameon=True, shadow=True, fontsize=9)

        # 6. Guardar y Mostrar
        output_file = "verificacion_final_fig6_completa.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Gráfico generado con éxito: {output_file}")
        plt.show()

    except Exception as e:
        print(f"Error en la visualización: {e}")


if __name__ == "__main__":
    plot_verification_final()