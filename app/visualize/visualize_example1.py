import requests
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# CONFIGURACIÓN
# ==========================================
PROJECT_ID = 5
DIAS_SIMULACION = 1000  # Tiempo dinámico
BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/simulate/{PROJECT_ID}/curve"


def plot_example1_final_v2():
    # Solicitamos la simulación
    params = {"total_days": DIAS_SIMULACION, "log_scale": True}

    try:
        response = requests.post(API_URL, params=params)
        response.raise_for_status()
        json_data = response.json()

        curves = json_data["data"]["curves"]
        time = np.array(json_data["data"]["time"])

        # Crear figura ancha para que no se vea "chico"
        fig, ax1 = plt.subplots(figsize=(16, 9))
        ax2 = ax1.twinx()

        # Definimos estilos con ZORDER para que el azul se vea sobre el naranja
        styles = {
            "Well 1": {"c": "#1F4E79", "ls_q": "--", "lbl_p": "Δpwf,1", "lbl_q": "q1", "z": 10},
            "Well 2": {"c": "#ED7D31", "ls_q": "-.", "lbl_p": "Δpwf,2", "lbl_q": "q2", "z": 9},
            "Well 3": {"c": "#7F7F7F", "ls_q": ":", "lbl_p": "Δpwf,3", "lbl_q": "q3", "z": 8}
        }

        # 1. Graficar Presiones (Eje Izquierdo - Semilog)
        for name, data in curves.items():
            dp = np.array(data["delta_p"])
            s = styles.get(name, {"c": "black", "lbl_p": name, "z": 1})

            # Usamos alpha=0.8 y zorder para manejar la superposición de la línea azul
            ax1.semilogx(time, dp, color=s["c"], label=s["lbl_p"],
                         linewidth=3, alpha=0.85, zorder=s["z"])

        # 2. Graficar Tasas (Eje Derecho - Escalones)
        t_final = time[-1]
        well_rates = {
            "Well 1": [(0, 0), (1, 1000), (5, 500), (10, 2000), (t_final, 2000)],
            "Well 2": [(0, 0), (1, 1000), (8, 1500), (9, 2500), (t_final, 2500)],
            "Well 3": [(0, 0), (3, 1000), (5, 0), (9, 2500), (20, 1000), (t_final, 1000)]
        }
        for name, sched in well_rates.items():
            t_s, q_s = zip(*sched)
            s = styles.get(name)
            if s:
                ax2.step(t_s, q_s, where='post', color=s["c"],
                         linestyle=s["ls_q"], label=s["lbl_q"], alpha=0.5, linewidth=1.5)

        # ==========================================
        # LÍMITES Y FORMATO (Réplica Fig 9)
        # ==========================================
        # El tiempo inicia en 0.1 como en el paper para ver los saltos claramente
        ax1.set_xlim(0.1, DIAS_SIMULACION)

        # PRESIÓN fija en 500 psi como pediste
        ax1.set_ylim(0, 500)

        # TASA fija en 3000 STB/D
        ax2.set_ylim(0, 3000)

        ax1.set_xlabel('Time, t, days', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Δpwf,i, psi', fontsize=14, fontweight='bold')
        ax2.set_ylabel('qi, stb/d', fontsize=14, fontweight='bold')

        ax1.grid(True, which="both", linestyle='--', alpha=0.3)

        # Combinar leyendas y moverlas fuera del gráfico
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left',
                   bbox_to_anchor=(1.08, 0.5), frameon=True, fontsize=12)

        plt.title(f"Figura 9 - Variaciones de Tasa y Cierre (Ejemplo 1)\nProyecto: {json_data['project']}",
                  fontsize=16, pad=20)

        # Ajustar margen derecho para la leyenda
        plt.subplots_adjust(right=0.85)

        plt.show()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    plot_example1_final_v2()