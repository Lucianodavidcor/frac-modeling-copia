import requests
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ID = 4  # ID de tu proyecto con Tabla 2
API_URL = f"http://127.0.0.1:8000/simulate/{PROJECT_ID}/curve"


def plot_fig8_replica():
    params = {"total_days": 100000, "log_scale": True}

    try:
        response = requests.post(API_URL, params=params)
        response.raise_for_status()
        curves = response.json()["data"]["curves"]
        time = np.array(response.json()["data"]["time"])

        plt.figure(figsize=(10, 7))
        plt.style.use('seaborn-v0_8-whitegrid')

        # Colores y marcadores para Analytical Well-1 a Well-4
        styles = {
            0: {'c': '#4A90E2', 'lbl': 'Analytical Well-1', 'm': 'o'},
            1: {'c': '#F5A623', 'lbl': 'Analytical Well-2', 'm': 's'},
            2: {'c': '#D0021B', 'lbl': 'Analytical Well-3', 'm': 'd'},
            3: {'c': '#7ED321', 'lbl': 'Analytical Well-4', 'm': '^'}
        }

        for i, (name, data) in enumerate(curves.items()):
            dp = np.array(data["delta_p"])
            valid = (time >= 1.0)  # Iniciamos en día 1 como el paper
            s = styles.get(i, {'c': 'black', 'lbl': name, 'm': 'x'})

            plt.loglog(time[valid], dp[valid], linestyle='-', linewidth=1.5,
                       color=s['c'], marker=s['m'], markersize=4, markevery=3,
                       label=s['lbl'])

        plt.title("Fig. 8—Verification of the multiwell model (Table 2)", fontsize=14)
        plt.xlabel("Time, days", fontsize=12)
        plt.ylabel("Δp, psi", fontsize=12)

        plt.xlim(1e0, 1e4)
        plt.ylim(1e0, 1e4)

        plt.grid(True, which="both", linestyle='--', alpha=0.5)
        plt.legend(loc='lower right', frameon=True, shadow=True, fontsize=10)

        plt.tight_layout()
        plt.savefig("verificacion_multiwell_final.png", dpi=300)
        plt.show()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    plot_fig8_replica()