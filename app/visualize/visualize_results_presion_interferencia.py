import requests
import matplotlib.pyplot as plt

# CONFIGURACIÓN: Apuntamos al endpoint de CURVA DE PRESIÓN
API_URL = "http://127.0.0.1:8000/simulate/1/curve" 
PARAMS = {"total_days": 1800, "step_days": 15} # step_days=5 para mayor suavidad en los cambios

def plot_pressure_data():
    print(f"Solicitando curvas de presión a la API: {API_URL}...")
    
    try:
        # 1. Obtener datos de la API (Usamos POST según la definición en simulation.py)
        response = requests.post(API_URL, params=PARAMS)
        response.raise_for_status()
        json_data = response.json()
        
        simulation_data = json_data["data"]
        time = simulation_data["time"]
        curves = simulation_data["curves"]

        # 2. Configurar el gráfico
        plt.figure(figsize=(12, 7))
        plt.style.use('seaborn-v0_8-darkgrid') 

        for well_name, pressures in curves.items():
            # Estilo: Línea discontinua para el pozo Hijo para identificarlo rápido
            linestyle = '--' if "Hijo" in well_name else '-'
            linewidth = 2.5 if "Hijo" in well_name else 1.8
            
            plt.plot(time, pressures, label=well_name, linestyle=linestyle, linewidth=linewidth)

        # 3. Etiquetas y Formato Profesional
        plt.title(f"Simulación de Presión - Proyecto: {json_data['project']}", fontsize=14)
        plt.xlabel("Tiempo (Días)", fontsize=12)
        plt.ylabel("Presión de Fondo (psi)", fontsize=12)
        plt.legend(loc='best', shadow=True)
        plt.grid(True, which='both', linestyle='--', alpha=0.5)
        
        # Ajuste del eje Y para centrarse en la zona de interés
        all_pressures = [p for curve in curves.values() for p in curve]
        if all_pressures:
            p_min = min(all_pressures)
            p_max = max(all_pressures)
            plt.ylim(p_min - 50, p_max + 50)

        print("Generando gráfico de presión...")
        plt.savefig("resultado_presion_interferencia.png")
        print("¡Éxito! El gráfico se guardó como 'resultado_presion_interferencia.png'")
        plt.show()

    except Exception as e:
        print(f"Error al visualizar presiones: {e}")

if __name__ == "__main__":
    plot_pressure_data()