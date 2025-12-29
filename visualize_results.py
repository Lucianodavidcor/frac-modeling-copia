import requests
import matplotlib.pyplot as plt

# Configuración
API_URL = "http://127.0.0.1:8000/simulate/1/curve" # Asegurate de que el ID sea el correcto
PARAMS = {"total_days": 365, "step_days": 10}

def plot_reservoir_data():
    print(f"Solicitando datos a la API: {API_URL}...")
    
    try:
        # 1. Obtener datos de la API
        response = requests.post(API_URL, params=PARAMS)
        response.raise_for_status()
        json_data = response.json()
        
        simulation_data = json_data["data"]
        time = simulation_data["time"]
        curves = simulation_data["curves"]

        # 2. Configurar el gráfico
        plt.figure(figsize=(12, 7))
        plt.style.use('seaborn-v0_8-darkgrid') # Estilo profesional

        for well_name, pressures in curves.items():
            # Diferenciamos el pozo hijo con un estilo de línea distinto
            linestyle = '--' if "Hijo" in well_name else '-'
            linewidth = 2.5 if "Hijo" in well_name else 1.5
            
            plt.plot(time, pressures, label=well_name, linestyle=linestyle, linewidth=linewidth)

        # 3. Etiquetas y Formato (Ingeniería)
        plt.title(f"Interferencia de Pozos - {json_data['project']}", fontsize=14)
        plt.xlabel("Tiempo (Días)", fontsize=12)
        plt.ylabel("Presión de Fondo (psi)", fontsize=12)
        plt.legend(loc='best', shadow=True)
        plt.grid(True, which='both', linestyle='--', alpha=0.5)
        
        # Ajustar el eje Y para ver mejor el declino
        p_min = min([min(p) for p in curves.values()])
        p_max = 6500 # Presión inicial
        plt.ylim(p_min - 5, p_max + 5)

        print("Generando gráfico...")
        plt.savefig("resultado_interferencia.png")
        print("¡Éxito! El gráfico se guardó como 'resultado_interferencia.png'")
        plt.show()

    except Exception as e:
        print(f"Error al visualizar: {e}")

if __name__ == "__main__":
    plot_reservoir_data()