import streamlit as st
import numpy as np


def skin_tab(params=None,well_params=None,schedules=None):
    st.subheader("🌀 Flow-choking skin — SPE-215031-PA")

    st.markdown("**Referencia: Eq. (53) del paper**")
    st.latex(r"""
    s_{cFi} = \frac{\psi \, k_f \, h}{q_R \, B \, \mu} \, \Delta p_{cFi}
    """)

    st.markdown(r"""
    **Definiciones:**
    - $s_{cFi}$: término de skin adicional asociado a la convergencia de flujo hacia fractura i.  
    - $\Delta p_{cFi}$: caída de presión local en la conexión pozo–fractura [psi].  
    - $k_f$: permeabilidad de la fractura [nD].  
    - $h$: espesor productivo [ft].  
    - $q_R$: caudal de referencia (ej. caudal del pozo) [STB/d].  
    - $B$: factor volumétrico (adimensional).  
    - $\mu$: viscosidad [cp].  
    - $\psi$: factor de conversión (convención SPE).  

    **Índices:**
    - $c$: convergencia de flujo (choking).  
    - $F$: fractura.  
    - $i = 1, \dots, n_f$: índice de fractura.
    """)

    st.markdown(r"""
    **Concepto:**  
    Este skin no proviene de daño en la formación, sino de la **geometría del flujo**:  
    el fluido converge radialmente desde la matriz hacia la fractura, generando una 
    caída de presión extra que se suma a la respuesta del sistema lineal O/I.  

    Es un término correctivo necesario para modelar fracturas múltiples en paralelo.
    """)
     # Tomamos un caudal representativo a partir de schedules
    if schedules:
        # promedio de todos los caudales de todos los pozos
        q_stb = np.mean([np.mean([s["q"] for s in sched]) for sched in schedules.values()])
    else:
        q_stb = 1000.0  # fallback

    st.markdown(f"**Caudal representativo usado:** {q_stb:.1f} STB/d")

    # Parámetros necesarios desde params
    k_f = params.get("k_f", 1000)      # md
    h = params.get("h", 100)           # ft
    dp_cf = params.get("dp_cf", 50)    # presión de caída en fractura [psi]
    mu = params.get("mu", 1.0)         # cP

    # Cálculo del skin simplificado
    skin = (k_f * h * dp_cf) / max(q_stb * mu, 1e-12)

    st.latex(r"S = \frac{k_f \, h \, \Delta p_{cf}}{q \, \mu}")

    st.markdown(f"**Skin calculado:** {skin:.2f}")

    # Evaluación cualitativa
    if skin > 5:
        st.error(f"Skin alto ({skin:.1f}) → choking severo")
    elif skin < 0:
        st.warning(f"Skin negativo ({skin:.1f}) → fractura muy conductiva")
    else:
        st.success(f"Skin moderado ({skin:.1f})")

    # Mostrar valores usados
    st.markdown("**Valores de entrada:**")
    st.markdown(f"- $k_f = {k_f} \ md$")
    st.markdown(f"- $h = {h} \ ft$")
    st.markdown(f"- $\Delta p_cf = {dp_cf} \ psi$")
    st.markdown(f"- $μ = {mu} \ cP$")
    st.markdown(f"- $q = {q_stb:.1f} \ STB/d$")
