import requests
import matplotlib.pyplot as plt

# CONFIGURACIÓN: Apuntamos al nuevo endpoint de TASAS
API_URL = "http://127.0.0.1:8000/simulate/1/rate-curve" 
PARAMS = {"total_days": 365}

def plot_production_rates():
    print(f"Solicitando datos de producción a la API: {API_URL}...")
    
    try:
        # 1. Obtener datos de la API
        # Nota: Cambiamos a POST porque el endpoint en simulation.py es POST
        response = requests.post(API_URL, params=PARAMS)
        response.raise_for_status()
        json_data = response.json()
        
        simulation_data = json_data["data"]
        time = simulation_data["time"]
        curves = simulation_data["curves"]

        # 2. Configurar el gráfico
        plt.figure(figsize=(12, 7))
        plt.style.use('seaborn-v0_8-darkgrid') 

        for well_name, rates in curves.items():
            # Estilo visual: resaltamos el hijo con línea discontinua
            linestyle = '--' if "Hijo" in well_name else '-'
            linewidth = 2.5 if "Hijo" in well_name else 1.8
            
            plt.plot(time, rates, label=well_name, linestyle=linestyle, linewidth=linewidth)

        # 3. Etiquetas y Formato de Ingeniería
        plt.title(f"Declino por Interferencia (Tasas) - {json_data['project']}", fontsize=14)
        plt.xlabel("Tiempo (Días)", fontsize=12)
        plt.ylabel("Tasa de Producción (STB/D)", fontsize=12) # Cambiado a unidades de tasa
        plt.legend(loc='best', shadow=True)
        plt.grid(True, which='both', linestyle='--', alpha=0.5)
        
        # Ajuste automático del eje Y para ver el "salto" de producción
        all_rates = [r for curve in curves.values() for r in curve]
        if all_rates:
            plt.ylim(0, max(all_rates) * 1.1)

        print("Generando gráfico de producción...")
        plt.savefig("resultado_tasas_produccion.png")
        print("¡Éxito! El gráfico se guardó como 'resultado_tasas_produccion.png'")
        plt.show()

    except Exception as e:
        print(f"Error al visualizar tasas: {e}")

if __name__ == "__main__":
    plot_production_rates()