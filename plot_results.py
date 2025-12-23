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
        
        # Input para IDs de Hijos (La solución "Sin Adivinar")
        tk.Label(self.left_panel, text="IDs de Pozos Hijos (sep. por coma):", bg="#f4f4f4").pack(anchor="w", padx=5)
        self.ent_child_ids = tk.Entry(self.left_panel, width=30)
        self.ent_child_ids.insert(0, "3") # Valor por defecto (tu caso actual)
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
        labels = ["Día Inicial:", "Día Final:", "Presión Min (PSI):", "Presión Max (PSI):"]
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
        t_raw = np.array(data["time_days"])
        wells = data.get("wells", [])
        colors = ['#1f77b4', '#2ca02c', '#9467bd', '#8c564b']
        max_p = 0
        
        # --- 1. LEER IDS DE HIJOS (MANUALMENTE) ---
        try:
            child_ids_str = self.ent_child_ids.get()
            child_ids = [int(x.strip()) for x in child_ids_str.split(",") if x.strip()]
        except ValueError:
            messagebox.showwarning("Aviso", "IDs de hijos inválidos. Se asumirá ninguno.")
            child_ids = []

        for i, w in enumerate(wells):
            y_data = np.array(w.get("pressure_drop_psi", w.get("data", [])))
            well_id = w.get("well_id", -1)
            
            min_len = min(len(t_raw), len(y_data))
            t_plot, y_plot = t_raw[:min_len], y_data[:min_len]
            
            # --- 2. DETERMINAR SI ES HIJO POR ID ---
            is_child = well_id in child_ids

            # --- 3. FILTRO DE LIMPIEZA INTELIGENTE ---
            y_clean = np.copy(y_plot)
            
            # Calculamos el valor máximo de presión para este pozo
            max_val = np.nanmax(y_plot) if len(y_plot) > 0 else 1.0
            
            # Umbral dinámico: El ruido suele ser despreciable comparado con la señal máxima.
            # Usamos el 0.1% del máximo o 10 PSI, lo que sea mayor.
            threshold = max(10.0, max_val * 0.001)
            
            # Filtramos todo lo que esté por debajo del umbral (elimina la línea plana inicial)
            y_clean[y_clean <= threshold] = np.nan
            
            # Si es hijo, lógica extra para asegurar limpieza del evento de inicio
            if is_child:
                valid_indices = np.where(~np.isnan(y_clean))[0]
                if len(valid_indices) > 0:
                    first_idx = valid_indices[0]
                    # Aseguramos que lo anterior sea NaN
                    y_clean[:first_idx] = np.nan 
                    
                    # Dibujar línea vertical de inicio
                    start_t = t_plot[first_idx]
                    self.ax.axvline(x=start_t, color='gray', ls=':', alpha=0.5)
            
            # --- 4. GRAFICADO ---
            color = 'red' if is_child else colors[i % len(colors)]
            style = '--' if is_child else '-'
            label = f"{'HIJO' if is_child else 'PADRE'} ({well_id}): {w.get('name')}"
            
            if not np.all(np.isnan(y_clean)):
                self.ax.semilogx(t_plot, y_clean, label=label, color=color, 
                                 linestyle=style, linewidth=3 if is_child else 2, alpha=0.8)
                
                # Actualizar máximo para escala
                valid_vals = y_clean[~np.isnan(y_clean)]
                if len(valid_vals) > 0: 
                    max_p = max(max_p, np.nanmax(valid_vals))

        # --- CONFIGURACIÓN FINAL ---
        self.ax.invert_yaxis()
        self.ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
        self.ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
        self.ax.set_title("Depleción del Reservorio: Análisis Parent-Child", fontsize=12, fontweight='bold')
        self.ax.set_xlabel("Tiempo [Días]", fontweight='bold')
        self.ax.set_ylabel("Caída de Presión [PSI]", fontweight='bold')
        self.ax.grid(True, which="both", ls="-", alpha=0.3)
        self.ax.legend(loc='best', shadow=True)

        if max_p > 0:
            self.default_ylim = (max_p * 1.1, 0)
            self.ax.set_ylim(self.default_ylim)
        
        self.default_xlim = self.ax.get_xlim()
        self.canvas.draw()

    def apply_manual_zoom(self):
        if not self.current_data: return
        try:
            x_min = self.entries["Día Inicial:"].get()
            x_max = self.entries["Día Final:"].get()
            y_min = self.entries["Presión Min (PSI):"].get()
            y_max = self.entries["Presión Max (PSI):"].get()

            if x_min and x_max: self.ax.set_xlim(left=float(x_min), right=float(x_max))
            if y_min and y_max: self.ax.set_ylim(bottom=float(y_max), top=float(y_min))
            self.canvas.draw()
        except ValueError: messagebox.showerror("Error", "Ingrese números válidos.")

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