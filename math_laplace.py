import streamlit as st
import numpy as np
import plotly.graph_objects as go

def laplace_tab(params, well_params=None, schedules=None):
    st.subheader("🔎 Evaluación en Laplace y Stehfest")

    # === 1) Transformada del caudal ===
    st.markdown("### 1️⃣ Transformada del caudal por tramos")
    st.latex(r"\hat q_j(s) = \frac{1}{s} \sum_k (q_k - q_{k-1}) e^{-s t_{k-1}}")

    t_star = st.number_input("t* [day]", 1.0, 1000.0, 10.0)
    k_steh = st.slider("k (nodo Stehfest)", 2, 12, 6)

    s_star = (k_steh*np.log(2)) / t_star / (24*3600)  # 1/s
    st.latex(fr"s^* = \frac{{{k_steh} \ln 2}}{{{t_star:.1f} \ day}} = {s_star:.3e} s^{{-1}}")

    # ejemplo de cálculo usando schedules si están disponibles
    if schedules:
        qhat_vals = []
        for wname, sched in schedules.items():
            qhat_vals.append(q_hat(sched, s_star))
        q_vec = np.array(qhat_vals)
    else:
        q_vec = np.array([1.655e8, 1.298e6])  # fallback demo

    st.latex(r"\hat q(s^*) = " + str(q_vec))

    # === 2) Parámetro difusivo y Green ===
    st.markdown("### 2️⃣ Parámetro difusivo y funciones de Green")
    st.latex(r"\lambda = \sqrt{\frac{\mu c_t}{k} s}")

    # demo con valores fijos (podés reemplazar por cálculo real con params)
    lambda_SRV = 2.866e-11
    lambda_ORV = 6.619e-11
    st.markdown(f"Valores usados: λ_SRV = {lambda_SRV:.3e}, λ_ORV = {lambda_ORV:.3e}")

    st.latex(r"\hat p(s) = R(s) \, \hat q(s)")

    # Mostrar matriz R como heatmap
    R = np.array([[1.518e21, 1.989e-169],
                  [1.989e-169, 1.518e21]])
    fig = go.Figure(data=go.Heatmap(z=R, text=R, texttemplate="%e"))
    st.plotly_chart(fig, use_container_width=True)

    # === 3) Superposición + Stehfest ===
    st.markdown("### 3️⃣ Superposición en Laplace e inversión Stehfest")
    i = st.number_input("i (destino)", 1, 5, 1)
    j = st.number_input("j (fuente)", 1, 5, 2)
    k_nodes = st.slider("N Stehfest", 2, 16, 12)

    st.latex(r"\bar p_i(s^*) = \sum_j R_{ij}(s^*) \, \hat q_j(s^*)")

    # Gráfico barras Stehfest (ejemplo aleatorio por ahora)
    steh_terms = np.random.randn(k_nodes)
    fig2 = go.Figure(data=go.Bar(x=list(range(1,k_nodes+1)), y=steh_terms))
    fig2.update_layout(xaxis_title="k (nodo)", yaxis_title="aporte")
    st.plotly_chart(fig2, use_container_width=True)

    # Kernel R vs D (demo)
    D = np.linspace(0,1500,200)
    kernel = 1e21*np.exp(-D/200)  # ejemplo
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=D, y=kernel, mode="lines", name="R_ij(s*,D)"))
    st.plotly_chart(fig3, use_container_width=True)


# ==== Utilidades de Laplace ====
def q_hat(schedule, s):
    """Transformada de Laplace de un schedule por tramos"""
    total = 0.0
    for k in range(1, len(schedule)):
        qk = schedule[k]["q"]
        qk1 = schedule[k-1]["q"]
        tprev = schedule[k-1]["t_ini"] * 24 * 3600
        total += (qk - qk1) * np.exp(-s * tprev)
    return total / s

def q_hat_multi(schedules, s):
    """Devuelve vector [q̂1(s), q̂2(s), ..., q̂N(s)]"""
    return [q_hat(schedules[w], s) for w in schedules]
