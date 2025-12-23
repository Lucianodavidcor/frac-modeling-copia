import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import json
import numpy as np

# Librerías de Matplotlib para integración con Tkinter
import matplotlib
matplotlib.use("TkAgg") # Backend para interfaces gráficas
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.ticker as ticker

class FractureHitViewerPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Fracture Hit Analytics - Visor Profesional")
        self.root.geometry("1200x800")
        
        # --- LAYOUT PRINCIPAL (Dos Paneles) ---
        self.left_panel = tk.Frame(root, width=300, bg="#f0f0f0")
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        self.right_panel = tk.Frame(root, bg="white")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ================= PANEL IZQUIERDO (CONTROLES) =================
        
        tk.Label(self.left_panel, text="1. Datos de Simulación", font=("Arial", 11, "bold"), bg="#f0f0f0").pack(pady=(10,5))
        
        self.text_area = scrolledtext.ScrolledText(self.left_panel, width=35, height=15, font=("Consolas", 9))
        self.text_area.pack(padx=5, pady=5)
        
        btn_plot = tk.Button(self.left_panel, text="🔄 PROCESAR JSON", command=self.process_json, 
                             bg="#2196F3", fg="white", font=("Arial", 10, "bold"), height=2)
        btn_plot.pack(fill=tk.X, padx=5, pady=10)

        # --- SECCIÓN DE ZOOM MANUAL ---
        tk.Label(self.left_panel, text="2. Control de Zoom (Ejes)", font=("Arial", 11, "bold"), bg="#f0f0f0").pack(pady=(20,5))
        
        frame_zoom = tk.Frame(self.left_panel, bg="#f0f0f0")
        frame_zoom.pack(padx=5, fill=tk.X)

        # Entradas X (Tiempo)
        tk.Label(frame_zoom, text="Tiempo Min (Días):", bg="#f0f0f0").grid(row=0, column=0, sticky="w")
        self.ent_xmin = tk.Entry(frame_zoom, width=10)
        self.ent_xmin.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(frame_zoom, text="Tiempo Max (Días):", bg="#f0f0f0").grid(row=1, column=0, sticky="w")
        self.ent_xmax = tk.Entry(frame_zoom, width=10)
        self.ent_xmax.grid(row=1, column=1, padx=5, pady=2)

        # Entradas Y (Presión)
        tk.Label(frame_zoom, text="Presión Min (PSI):", bg="#f0f0f0").grid(row=2, column=0, sticky="w")
        self.ent_ymin = tk.Entry(frame_zoom, width=10)
        self.ent_ymin.grid(row=2, column=1, padx=5, pady=2)

        tk.Label(frame_zoom, text="Presión Max (PSI):", bg="#f0f0f0").grid(row=3, column=0, sticky="w")
        self.ent_ymax = tk.Entry(frame_zoom, width=10)
        self.ent_ymax.grid(row=3, column=1, padx=5, pady=2)

        btn_apply = tk.Button(self.left_panel, text="🔎 APLICAR ZOOM", command=self.apply_manual_zoom, 
                              bg="#FF9800", fg="black", font=("Arial", 9, "bold"))
        btn_apply.pack(fill=tk.X, padx=5, pady=10)
        
        btn_reset = tk.Button(self.left_panel, text="↺ RESET VISTA", command=self.reset_view, 
                              bg="#607D8B", fg="white", font=("Arial", 9))
        btn_reset.pack(fill=tk.X, padx=5, pady=2)

        # ================= PANEL DERECHO (MATPLOTLIB) =================
        
        # Figura vacía inicial
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.text(0.5, 0.5, "Pegue el JSON y pulse Procesar", ha='center', va='center')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_panel)
        self.canvas.draw()
        
        # Barra de Herramientas (Zoom con mouse, Pan, Save)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.right_panel)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Variables de estado
        self.current_data = None
        self.default_xlim = (None, None)
        self.default_ylim = (None, None)

    def process_json(self):
        json_str = self.text_area.get('1.0', tk.END).strip()
        if not json_str:
            return

        try:
            data = json.loads(json_str)
            self.current_data = data
            self.plot_graph(data)
        except Exception as e:
            messagebox.showerror("Error", f"JSON Inválido: {e}")

    def plot_graph(self, data):
        self.ax.clear()
        
        t_raw = np.array(data["time_days"])
        wells = data["wells"]
        
        # Colores profesionales
        colors = ['#1f77b4', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        max_p = 0
        
        for i, w in enumerate(wells):
            name = w.get("name", f"Well {w.get('well_id')}")
            y_data = np.array(w["pressure_drop_psi"] if "pressure_drop_psi" in w else w["data"])
            
            # 1. Alineación de datos
            min_len = min(len(t_raw), len(y_data))
            t_plot = t_raw[:min_len]
            y_plot = y_data[:min_len]
            
            # 2. Identificar si es Pozo Hijo (Inicia después con ceros/ruido)
            # Analizamos si el primer 10% de los datos es básicamente 0 o ruido < 1 psi
            is_child = np.all(np.abs(y_plot[:max(1, int(min_len*0.1))]) < 1.0)

            # 3. FILTRO DE RUIDO AVANZADO
            # Eliminamos valores negativos y ruido de oscilación (Gibbs)
            y_clean = np.copy(y_plot)
            y_clean[y_clean <= 0.5] = np.nan # Presiones negativas o casi cero son ruido
            
            # Si es hijo, buscamos el "punto de ignición" (donde sube de verdad)
            if is_child:
                # Buscamos el primer índice donde la presión es significativa y creciente
                threshold = 5.0 # psi
                start_indices = np.where(y_plot > threshold)[0]
                if len(start_indices) > 0:
                    first_real_idx = start_indices[0]
                    # Limpiamos todo lo que hay antes del inicio real para borrar el "ringing"
                    y_clean[:first_real_idx] = np.nan
                    
                    # Dibujamos línea vertical de inicio de producción
                    start_t = t_plot[first_real_idx]
                    self.ax.axvline(x=start_t, color='gray', ls=':', alpha=0.6)
                    self.ax.text(start_t, 1, f' Inicio {name}', rotation=90, 
                                 verticalalignment='bottom', fontsize=8, color='gray')

            # 4. Estilo de línea
            color = 'red' if is_child else colors[i % len(colors)]
            style = '--' if is_child else '-'
            width = 3.0 if is_child else 2.0
            label = f"HIJO: {name}" if is_child else f"PADRE: {name}"

            # 5. Graficar (Solo si hay datos que sobrevivieron al filtro)
            if not np.all(np.isnan(y_clean)):
                self.ax.semilogx(t_plot, y_clean, label=label, 
                                 linestyle=style, linewidth=width, color=color, alpha=0.8)
                
                # Calcular límites para el eje Y
                valid_vals = y_clean[~np.isnan(y_clean)]
                if len(valid_vals) > 0:
                    max_p = max(max_p, np.nanmax(valid_vals))

        # --- CONFIGURACIÓN DE EJES ---
        self.ax.invert_yaxis() # Depleción hacia abajo
        
        # Formato de números: 1,000,000 en vez de 1e6
        self.ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
        self.ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
        
        self.ax.set_title("Simulación de Interferencia (Fracture Hit Detectado)", fontsize=13, fontweight='bold')
        self.ax.set_xlabel("Tiempo [Días]", fontweight='bold')
        self.ax.set_ylabel("Caída de Presión [PSI]\n(Hacia abajo = Más Agotamiento)", fontweight='bold')
        
        self.ax.grid(True, which="major", ls="-", alpha=0.5)
        self.ax.grid(True, which="minor", ls=":", alpha=0.2)
        
        # Ajustar leyenda para que no tape las curvas
        self.ax.legend(loc='best', frameon=True, shadow=True, fontsize=9)

        # Ajuste de límites automático inteligente
        if max_p > 0:
            self.ax.set_ylim(bottom=max_p * 1.1, top=0)

        self.canvas.draw()

    def apply_manual_zoom(self):
        if self.current_data is None: return
        
        try:
            # Obtener valores
            x_min = float(self.ent_xmin.get()) if self.ent_xmin.get() else None
            x_max = float(self.ent_xmax.get()) if self.ent_xmax.get() else None
            y_min = float(self.ent_ymin.get()) if self.ent_ymin.get() else None
            y_max = float(self.ent_ymax.get()) if self.ent_ymax.get() else None

            # Aplicar X
            if x_min is not None or x_max is not None:
                self.ax.set_xlim(left=x_min, right=x_max)
            
            # Aplicar Y
            if y_min is not None or y_max is not None:
                # Al estar invertido el eje, "bottom" es el valor numérico mayor
                self.ax.set_ylim(bottom=y_max, top=y_min)

            self.canvas.draw()
            
        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese números válidos (use punto para decimales).")

    def reset_view(self):
        if self.current_data is None: return
        self.ent_xmin.delete(0, tk.END)
        self.ent_xmax.delete(0, tk.END)
        self.ent_ymin.delete(0, tk.END)
        self.ent_ymax.delete(0, tk.END)
        
        # Restaurar autoescala
        self.ax.set_xlim(self.default_xlim)
        self.ax.set_ylim(self.default_ylim)
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = FractureHitViewerPro(root)
    root.mainloop()