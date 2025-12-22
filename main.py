import streamlit as st
import numpy as np
import plotly.graph_objects as go
from example_data import examples
import pandas as pd
import io

from physics import R_self, R_cross, invert_stehfest_vec, si_mu, si_k, si_ct, si_h, si_L, PSI_TO_PA
from geometry import svg_reservoir_parametric, svg_reservoir_scaled
from ui_inputs import sidebar_inputs, glossary
from math_dev import math_tab
from math_laplace import laplace_tab
from math_adim import adim_tab
from math_dualporosity import dual_tab
from math_skin import skin_tab
from math_multifracture import multi_tab

# ========== CONFIG ==========
st.set_page_config(page_title="SPE-215031-PA - Interferencia", layout="wide")
st.title("🛢️ SPE-215031-PA - Interferencia de pozos horizontales")

# Sidebar: elegir ejemplo
st.sidebar.markdown("### 📂 Casos de ejemplo")
example_choice = st.sidebar.selectbox("Seleccionar preset del paper:", list(examples.keys()))

# Cargar ejemplo elegido
example_params    = examples[example_choice]["params"]
example_wells     = examples[example_choice]["well_params"]
example_schedules = examples[example_choice]["schedules"]

st.sidebar.info(f"Usando preset: **{example_choice}**")

# Tabs principales
tab_inputs, tab_geometry, tab_math, tab_adim, tab_dual, tab_skin, tab_multi, tab_laplace, tab_results = st.tabs(
    ["⚙️ Inputs", "📐 Geometría", "📓 Desarrollo básico", "📊 Adimensionales",
     "🧩 Dual-porosidad", "🌀 Skin", "📐 Multi-fractura", "Laplace" ,"📈 Resultados"]
)

# ===== TAB 1: Inputs =====
with tab_inputs:
    st.subheader("Parámetros de entrada")
    params, schedules, well_params = sidebar_inputs(
        default_params=example_params,
        default_wells=example_wells,
        default_schedules=example_schedules

    )
    glossary()

# ===== TAB 2: Geometría =====
with tab_geometry:
    st.subheader("Esquema O/I")
    use_scaled = st.checkbox("Mostrar a escala (con $spacing_g$ y $2x_e$)", False)

    if use_scaled:
        wells = []
        for i in range(len(well_params)):
            wname = f"well_{i+1}"
            wells.append({
                "name": f"Pozo {i+1}",
                "n_frac": well_params[wname]["n_frac"],
                "color": "#d62728",
                "spacing": well_params[wname]["spacing"]
            })
        svg_code = svg_reservoir_scaled(wells, xe=params["xe"])
    else:
        wells = []
        for i in range(len(well_params)):
            wname = f"well_{i+1}"
            wells.append({
                "name": f"Pozo {i+1}",
                "spacing": well_params[wname]["spacing"],
                "n_frac": well_params[wname]["n_frac"],
                "color": f"hsl({(i*60)%360},70%,50%)"
            })
        svg_code = svg_reservoir_parametric(wells)

    st.components.v1.html(svg_code, height=500, scrolling=True)

# ===== TAB 3: Desarrollo matemático =====
with tab_math:
    math_tab(params, well_params)

# ===== Adimensionales =====
with tab_adim:
    adim_tab(params)

# ===== Dual-porosidad =====
with tab_dual:
    dual_tab(params)

# ===== Flow-choking skin =====
with tab_skin:
    skin_tab(params)

# ===== Multi-fractura =====
with tab_multi:
    multi_tab(params, well_params, schedules)

# ===== Laplace =====
with tab_laplace:
    laplace_tab(params, well_params, schedules)

# ===== TAB 4: Resultados =====
with tab_results:
    st.subheader("📈 Resultados de simulación")

    # --- Preparación de variables ---
    mu = si_mu(params["mu"])
    ct = si_ct(params["ct"])
    k_I = si_k(params["k_I"])
    k_O = si_k(params["k_O"])
    h = si_h(params["h"])
    Lx_I = si_L(params["LxI"])
    Lx_Oend = si_L(params["LxOend"])
    p_res = params["p_res"] * PSI_TO_PA

    avg_q_stb = np.mean([np.mean([s["q"] for s in sched]) for sched in schedules.values()])
    q_SI = avg_q_stb * 0.158987294928 / 86400

    N = len(well_params)
    spacing_m = si_L(np.mean([w["spacing"] for w in well_params.values()]))
    y_positions = np.arange(N) * spacing_m

    def p_hat_vec(s):
        Rmat = np.zeros((N, N))
        for i in range(N):
            for j in range(N):
                if i == j:
                    Rmat[i, j] = R_self(mu, ct, k_I, k_O, h, Lx_I, Lx_Oend, s)
                else:
                    Dij = abs(y_positions[i] - y_positions[j])
                    Rmat[i, j] = R_cross(mu, ct, k_O, h, Dij, s)
        q_vec = np.full(N, q_SI)
        p_vec = Rmat @ q_vec + np.full(N, p_res/s)
        return p_vec

    times = np.logspace(-2, 4, 80)  # días
    pressures = [[] for _ in range(N)]
    for t in times:
        vals = invert_stehfest_vec(p_hat_vec, t*86400, N=12)
        for i in range(N):
            pressures[i].append(vals[i] / PSI_TO_PA)

    # --- 1. Evolución de presiones ---
    fig_p = go.Figure()
    for i in range(N):
        fig_p.add_trace(go.Scatter(x=times, y=pressures[i],
                                   mode="lines+markers",
                                   name=f"Presión Pozo {i+1}"))
    fig_p.update_layout(
        title="Evolución de presiones por pozo",
        xaxis=dict(title="Tiempo (días, escala log)", type="log"),
        yaxis=dict(title="Presión (psi)")
    )
    st.plotly_chart(fig_p, use_container_width=True)
    st.caption("La caída de presión refleja el drenaje en el SRV/ORV. A tiempos largos se evidencia la interferencia entre pozos.")

    # --- 2. Δp entre pozos vecinos ---
    fig_dp = go.Figure()
    for i in range(N-1):
        delta = np.array(pressures[i]) - np.array(pressures[i+1])
        fig_dp.add_trace(go.Scatter(x=times, y=delta,
                                    mode="lines+markers",
                                    name=f"Δp Pozo {i+1}-{i+2}"))
    fig_dp.update_layout(
        title="Diferencia de presión entre pozos vecinos",
        xaxis=dict(title="Tiempo (días, log)", type="log"),
        yaxis=dict(title="Δp (psi)")
    )
    st.plotly_chart(fig_dp, use_container_width=True)
    st.caption("Un Δp alto indica fuerte interferencia (frac-hits o drenaje compartido). Un Δp bajo implica mejor balance.")

    # --- 3. Caudales programados (schedules) ---
    fig_q = go.Figure()
    for wname, sched in schedules.items():
        tvals = [s["t_ini"] for s in sched]
        qvals = [s["q"] for s in sched]
        fig_q.add_trace(go.Scatter(x=tvals, y=qvals,
                                   mode="lines+markers",
                                   line_shape="hv",
                                   name=f"Caudal {wname}"))
    fig_q.update_layout(
        title="Schedules de caudal (q vs t)",
        xaxis=dict(title="Tiempo (días)"),
        yaxis=dict(title="Caudal (STB/d)")
    )
    st.plotly_chart(fig_q, use_container_width=True)
    st.caption("Cada pozo puede arrancar en distinto tiempo y con diferente q. Esto condiciona la dinámica de interferencia.")

    # --- 4. Presiones + Caudales combinados ---
    fig_comb = go.Figure()
    for i in range(N):
        fig_comb.add_trace(go.Scatter(x=times, y=pressures[i],
                                      mode="lines",
                                      name=f"Presión Pozo {i+1}"))
    for wname, sched in schedules.items():
        tvals = [s["t_ini"] for s in sched]
        qvals = [s["q"] for s in sched]
        fig_comb.add_trace(go.Scatter(x=tvals, y=qvals,
                                      mode="lines+markers",
                                      name=f"q {wname}",
                                      yaxis="y2"))
    fig_comb.update_layout(
        title="Presiones y caudales alineados en tiempo",
        xaxis=dict(title="Tiempo (días)", type="log"),
        yaxis=dict(title="Presión (psi)"),
        yaxis2=dict(title="Caudal (STB/d)", overlaying="y", side="right")
    )
    st.plotly_chart(fig_comb, use_container_width=True)
    st.caption("Permite medir cuánto demora la respuesta de presión frente a cambios de caudal de cada pozo.")

    # --- 5. Producción acumulada ---
    fig_qcum = go.Figure()
    for wname, sched in schedules.items():
        t_days = np.linspace(1, 10000, 200)
        q_t = np.interp(t_days, [s["t_ini"] for s in sched], [s["q"] for s in sched])
        Qcum = np.cumsum(q_t) * (t_days[1]-t_days[0])
        fig_qcum.add_trace(go.Scatter(x=t_days, y=Qcum, mode="lines", name=f"Acumulado {wname}"))
    fig_qcum.update_layout(
        title="Producción acumulada",
        xaxis=dict(title="Tiempo (días)"),
        yaxis=dict(title="Q acumulado (STB)")
    )
    st.plotly_chart(fig_qcum, use_container_width=True)
    st.caption("Similar a Fig. 13 del paper. Útil para comparar producción de Parent vs Infill y evaluar pérdidas.")

    # --- 6. Δp vs q (diagnóstico de interferencia) ---
    fig_dpq = go.Figure()
    for i in range(N-1):
        delta = np.array(pressures[i]) - np.array(pressures[i+1])
        sched = schedules[f"well_{i+1}"]
        t_sched = [s["t_ini"] for s in sched]
        q_sched = [s["q"] for s in sched]
        q_interp = np.interp(times, t_sched, q_sched)
        fig_dpq.add_trace(go.Scatter(x=q_interp, y=delta,
                                     mode="lines+markers",
                                     name=f"Δp vs q (Pozo {i+1}-{i+2})"))
    fig_dpq.update_layout(
        title="Relación Δp – q (interferencia vs producción)",
        xaxis=dict(title="Caudal (STB/d)"),
        yaxis=dict(title="Δp (psi)")
    )
    st.plotly_chart(fig_dpq, use_container_width=True)
    st.caption("Muestra cómo aumenta la interferencia entre pozos vecinos a medida que se incrementa el caudal.")

    # --- 7. Presión normalizada ---
    fig_norm = go.Figure()
    for i in range(N):
        delta_p_norm = (params["p_res"] - np.array(pressures[i])) / params["p_res"]
        fig_norm.add_trace(go.Scatter(x=times, y=delta_p_norm,
                                      mode="lines+markers",
                                      name=f"Δp/p_res Pozo {i+1}"))
    fig_norm.update_layout(
        title="Presión normalizada Δp/p_res vs Tiempo",
        xaxis=dict(title="Tiempo (días, escala log)", type="log"),
        yaxis=dict(title="Δp/p_res (adimensional)")
    )
    st.plotly_chart(fig_norm, use_container_width=True)
    st.caption("Gráfico adimensional que facilita comparar distintos casos. Útil para identificar regímenes de flujo (bilinear, lineal, pseudorradial).")

    # === Valores intermedios (reales) ===
    p_final = pressures[0][-1]  # presión final del Pozo 1
    st.markdown(f"**Presión final Pozo 1:** {p_final:.1f} psi")

    q_cum = 0.0
    for sched in schedules.values():
        for i in range(1, len(sched)):
            t0, t1 = sched[i-1]["t_ini"], sched[i]["t_ini"]
            q0 = sched[i-1]["q"]
            q_cum += q0 * (t1 - t0)
    st.markdown(f"**Producción acumulada aprox (todos los pozos):** {q_cum:.0f} STB·d")

    # === Recomendaciones ===
    st.markdown("### 📝 Recomendaciones de diagnóstico")

    n_f = np.mean([w["n_frac"] for w in well_params.values()])
    spacing = np.mean([w["spacing"] for w in well_params.values()])
    kO = params["k_O"]
    skin = (params.get("k_f", 1000) * params["h"] * params.get("dp_cf", 50)) / (avg_q_stb * params["mu"])
    t_star = 1000  # días
    eta = params["k_I"] / (params["mu"]*params["ct"])
    x_fr = params["xe"]
    tD = eta * t_star*24*3600 / (x_fr**2)

    recs = []
    if n_f < 10:
        recs.append(("Número de fracturas", "⚠️", f"{n_f} → pocas, baja estimulación"))
    elif n_f > 20:
        recs.append(("Número de fracturas", "❌", f"{n_f} → muchas, interferencia"))
    else:
        recs.append(("Número de fracturas", "✅", f"{n_f} → adecuado"))

    if spacing < 200:
        recs.append(("Spacing", "❌", f"{spacing} ft → muy reducido"))
    elif spacing > 500:
        recs.append(("Spacing", "⚠️", f"{spacing} ft → amplio, subdrenaje"))
    else:
        recs.append(("Spacing", "✅", f"{spacing} ft → óptimo"))

    if kO < 50:
        recs.append(("Permeabilidad matriz", "❌", f"{kO} nD → matriz muy tight"))
    else:
        recs.append(("Permeabilidad matriz", "✅", f"{kO} nD → contribuye al drenaje"))

    if skin > 5:
        recs.append(("Skin", "❌", f"{skin:.1f} → choking severo"))
    elif skin < 0:
        recs.append(("Skin", "⚠️", f"{skin:.1f} → fractura muy conductiva"))
    else:
        recs.append(("Skin", "✅", f"{skin:.1f} → moderado"))

    if tD < 0.1:
        recs.append(("Régimen de flujo", "⚠️", f"t_D={tD:.2e} → bilinear inicial"))
    elif 0.1 <= tD <= 10:
        recs.append(("Régimen de flujo", "✅", f"t_D={tD:.2e} → lineal"))
    else:
        recs.append(("Régimen de flujo", "⚠️", f"t_D={tD:.2e} → pseudorradial"))

    df_recs = pd.DataFrame(recs, columns=["Parámetro", "Estado", "Comentario"])
    st.table(df_recs)

    # === Descargar tabla ===
    csv = df_recs.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar diagnóstico (CSV)", csv, "diagnostico.csv", "text/csv")

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_recs.to_excel(writer, index=False, sheet_name="Diagnóstico")
    st.download_button("⬇️ Descargar diagnóstico (Excel)", buffer.getvalue(),
                       "diagnostico.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
