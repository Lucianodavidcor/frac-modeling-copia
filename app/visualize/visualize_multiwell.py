import requests
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# CONFIGURACIÓN
# ==========================================
PROJECT_ID = 4
TOTAL_DAYS = 100000  # <--- AHORA PUEDES CAMBIAR ESTO AQUÍ
API_URL = f"http://127.0.0.1:8000/simulate/{PROJECT_ID}/curve"


def plot_multiwell_interference_v2():
    # Parámetros dinámicos
    params = {
        "total_days": TOTAL_DAYS,
        "log_scale": True
    }

    print(f"Solicitando datos a {API_URL} por {TOTAL_DAYS} días...")

    try:
        response = requests.post(API_URL, params=params)
        response.raise_for_status()
        json_data = response.json()

        sim_data = json_data["data"]
        time = np.array(sim_data["time"])
        curves = sim_data["curves"]

        plt.figure(figsize=(10, 7))
        plt.style.use('seaborn-v0_8-whitegrid')

        styles = {
            0: {'color': '#4A90E2', 'label': 'Well-1 (25 fracs)', 'marker': 'o'},
            1: {'color': '#F5A623', 'label': 'Well-2 (11 fracs)', 'marker': 's'},
            2: {'color': '#D0021B', 'label': 'Well-3 (25 fracs)', 'marker': 'd'},
            3: {'color': '#7ED321', 'label': 'Well-4 (11 fracs)', 'marker': '^'}
        }

        for i, (well_name, data) in enumerate(curves.items()):
            dp = np.array(data["delta_p"])
            valid = (time >= 1.0) & (dp > 0)  # Empezamos en día 1 como el paper

            style = styles.get(i, {'color': None, 'label': well_name, 'marker': 'o'})

            plt.loglog(time[valid], dp[valid],
                       linestyle='-', linewidth=1.2,
                       color=style['color'],
                       marker=style['marker'], markersize=4, markevery=2,
                       label=style['label'])

        plt.title(f"Verificación Multiwell - Interferencia (Tabla 2)\nProyecto: {json_data['project']}", fontsize=13)
        plt.xlabel("Time, days", fontsize=12)
        plt.ylabel("Δp, psi", fontsize=12)

        # Ajustamos los límites dinámicamente según el TOTAL_DAYS
        plt.xlim(1e0, TOTAL_DAYS)
        plt.ylim(1e0, 1e4)

        plt.grid(True, which="both", linestyle='--', alpha=0.5)
        plt.legend(loc='lower right', frameon=True, shadow=True, fontsize=10)

        output_file = "verificacion_multiwell_fig8_v2.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Gráfico guardado como '{output_file}'")
        plt.show()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    plot_multiwell_interference_v2()