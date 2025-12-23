import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import json
import numpy as np

# Librerías de Matplotlib para integración con Tkinter
import matplotlib
matplotlib.use("TkAgg") 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.ticker as ticker

class FractureHitViewerPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Análisis de Interferencia - Visor de Pozos Padres e Hijo")
        self.root.geometry("1200x850")
        
        # --- LAYOUT ---
        self.left_panel = tk.Frame(root, width=320, bg="#f4f4f4")
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        self.right_panel = tk.Frame(root, bg="white")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- PANEL IZQUIERDO: CONFIGURACIÓN ---
        tk.Label(self.left_panel, text="1. Configuración de Pozos", font=("Arial", 11, "bold"), bg="#f4f4f4").pack(pady=(10,5))
        
        # Input para IDs de Hijos
        tk.Label(self.left_panel, text="IDs de Pozos Hijos (sep. por coma):", bg="#f4f4f4").pack(anchor="w", padx=5)
        self.ent_child_ids = tk.Entry(self.left_panel, width=30)
        self.ent_child_ids.insert(0, "8") # Valor por defecto actualizado a tu JSON (Infill Central es ID 8)
        self.ent_child_ids.pack(padx=5, pady=5)

        # --- PANEL IZQUIERDO: JSON ---
        tk.Label(self.left_panel, text="2. Pegar JSON de Simulación", font=("Arial", 11, "bold"), bg="#f4f4f4").pack(pady=(15,5))
        self.text_area = scrolledtext.ScrolledText(self.left_panel, width=38, height=15, font=("Consolas", 9))
        self.text_area.pack(padx=5, pady=5)
        
        btn_plot = tk.Button(self.left_panel, text="🔄 PROCESAR Y GRAFICAR", command=self.process_json, 
                             bg="#2196F3", fg="white", font=("Arial", 10, "bold"), height=2)
        btn_plot.pack(fill=tk.X, padx=5, pady=10)

        # --- PANEL IZQUIERDO: ZOOM ---
        tk.Label(self.left_panel, text="3. Control de Rango (Manual)", font=("Arial", 11, "bold"), bg="#f4f4f4").pack(pady=(20,5))
        
        frame_zoom = tk.Frame(self.left_panel, bg="#f4f4f4")
        frame_zoom.pack(padx=5, fill=tk.X)

        # Entradas X e Y
        labels = ["Día Inicial:", "Día Final:", "Presión Min:", "Presión Max:"]
        self.entries = {}
        for i, label in enumerate(labels):
            tk.Label(frame_zoom, text=label, bg="#f4f4f4").grid(row=i, column=0, sticky="w", pady=2)
            entry = tk.Entry(frame_zoom, width=12)
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.entries[label] = entry

        btn_apply = tk.Button(self.left_panel, text="🔎 APLICAR ZOOM", command=self.apply_manual_zoom, 
                              bg="#FF9800", fg="black", font=("Arial", 9, "bold"))
        btn_apply.pack(fill=tk.X, padx=5, pady=10)
        
        btn_reset = tk.Button(self.left_panel, text="↺ RESTABLECER VISTA", command=self.reset_view, 
                              bg="#607D8B", fg="white", font=("Arial", 9))
        btn_reset.pack(fill=tk.X, padx=5, pady=2)

        # --- PANEL DERECHO: GRÁFICO ---
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.text(0.5, 0.5, "Esperando datos...", ha='center', va='center')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_panel)
        self.canvas.draw()
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.right_panel)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.current_data = None
        self.default_xlim = (None, None)
        self.default_ylim = (None, None)

    def process_json(self):
        json_str = self.text_area.get('1.0', tk.END).strip()
        if not json_str: return
        try:
            data = json.loads(json_str)
            self.current_data = data
            self.plot_graph(data)
        except Exception as e:
            messagebox.showerror("Error", f"Problema con el JSON o los datos: {e}")

    def plot_graph(self, data):
        self.ax.clear()
        
        # Validar datos mínimos
        if "time_days" not in data or "wells" not in data:
            self.ax.text(0.5, 0.5, "JSON inválido: Faltan 'time_days' o 'wells'", ha='center', va='center')
            self.canvas.draw()
            return

        t_raw = np.array(data["time_days"])
        wells = data.get("wells", [])
        colors = ['#1f77b4', '#2ca02c', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        # Variables para calcular límites globales
        global_min_p = float('inf')
        global_max_p = float('-inf')
        has_data = False
        
        # --- 1. LEER IDS DE HIJOS ---
        try:
            child_ids_str = self.ent_child_ids.get()
            child_ids = [int(x.strip()) for x in child_ids_str.split(",") if x.strip()]
        except ValueError:
            child_ids = []

        # --- 2. BUCLE DE GRAFICADO ---
        for i, w in enumerate(wells):
            y_data = np.array(w.get("pressure_drop_psi", w.get("data", [])))
            well_id = w.get("well_id", -1)
            name = w.get("name", f"Pozo {well_id}")
            
            # Sincronizar longitudes (cortar al más corto por seguridad)
            min_len = min(len(t_raw), len(y_data))
            if min_len == 0: continue
            
            t_plot, y_plot = t_raw[:min_len], y_data[:min_len]
            
            # Actualizar límites globales
            current_min = np.nanmin(y_plot)
            current_max = np.nanmax(y_plot)
            if current_min < global_min_p: global_min_p = current_min
            if current_max > global_max_p: global_max_p = current_max
            has_data = True

            # Estilo
            is_child = well_id in child_ids
            color = 'red' if is_child else colors[i % len(colors)]
            style = '--' if is_child else '-'
            width = 2.5 if is_child else 1.5
            label = f"{'[HIJO]' if is_child else '[PADRE]'} {name}"
            
            # Graficar SIN FILTROS DE RUIDO (Mostrar todo lo que devuelve el simulador)
            self.ax.semilogx(t_plot, y_plot, label=label, color=color, 
                             linestyle=style, linewidth=width, alpha=0.9)

        # --- 3. CONFIGURACIÓN FINAL DEL EJE ---
        if has_data:
            # Margen del 5% para que no toque los bordes
            margin = (global_max_p - global_min_p) * 0.05
            if margin == 0: margin = 1.0
            self.default_ylim = (global_min_p - margin, global_max_p + margin)
            self.ax.set_ylim(self.default_ylim)
        else:
            self.ax.text(0.5, 0.5, "Sin datos válidos para graficar", ha='center', va='center')

        # Formateo
        self.ax.set_title("Resultados de Simulación Trilineal (Caída de Presión)", fontsize=12, fontweight='bold')
        self.ax.set_xlabel("Tiempo [Días]", fontweight='bold')
        self.ax.set_ylabel("Delta P [PSI]", fontweight='bold')
        
        self.ax.grid(True, which="major", ls="-", alpha=0.5)
        self.ax.grid(True, which="minor", ls=":", alpha=0.2)
        
        # Formateador Inteligente para el Eje Y (Maneja millones y negativos)
        def format_y(x, pos):
            if abs(x) >= 1e4 or (abs(x) < 1e-2 and x != 0):
                return '{:.1e}'.format(x) # Notación científica para valores grandes/pequeños
            return '{:,.0f}'.format(x) # Enteros con comas para rangos normales

        self.ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_y))
        self.ax.xaxis.set_major_formatter(ticker.LogFormatterMathtext()) # Formato Log bonito para eje X
        
        self.ax.legend(loc='best', shadow=True, fontsize='small')
        
        self.default_xlim = self.ax.get_xlim()
        self.canvas.draw()

    def apply_manual_zoom(self):
        if not self.current_data: return
        try:
            x_min = self.entries["Día Inicial:"].get()
            x_max = self.entries["Día Final:"].get()
            y_min = self.entries["Presión Min:"].get()
            y_max = self.entries["Presión Max:"].get()

            # Validación básica
            if x_min and x_max: 
                self.ax.set_xlim(left=float(x_min), right=float(x_max))
            
            # Nota: Matplotlib usa (bottom, top). 
            # Si el usuario quiere ver de -20 a 100, bottom=-20, top=100.
            if y_min and y_max: 
                self.ax.set_ylim(bottom=float(y_min), top=float(y_max))
                
            self.canvas.draw()
        except ValueError: messagebox.showerror("Error", "Ingrese números válidos (Punto decimal .)")

    def reset_view(self):
        if not self.current_data: return
        for entry in self.entries.values(): entry.delete(0, tk.END)
        self.ax.set_xlim(self.default_xlim)
        self.ax.set_ylim(self.default_ylim)
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = FractureHitViewerPro(root)
    root.mainloop()