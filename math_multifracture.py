import streamlit as st


def multi_tab(params=None, well_params=None, schedules=None):
    st.subheader("📐 Sistema acoplado multi-fractura — SPE-215031-PA")

    st.markdown("**Referencia: Eqs. (34–41) del paper**")

    # === Ecuación principal ===
    st.latex(r"""
    r_i = \frac{\pi \, q_{iD}}
                 {n_{Fi} \, C_{FiD} \, k_{fiD} \, x_{FiD} \, \sqrt{\alpha_{Fi}}}
           \tanh(\sqrt{\alpha_{Fi}} \, x_{FiD})
    """)

    st.markdown(r"""
    **Definiciones:**
    - \(r_i\): respuesta adimensional de la fractura i.  
    - \(q_{iD}\): caudal adimensional en fractura i.  
    - \(n_{Fi}\): número de fracturas en el pozo i.  
    - \(C_{FiD}\): compresibilidad total adimensional de fractura i.  
    - \(k_{fiD}\): permeabilidad adimensional de fractura i.  
    - \(x_{FiD}\): medio ancho adimensional de fractura i.  
    - \(\alpha_{Fi}\): parámetro de acoplamiento (ver Eq. 38).  
    """)

    # === Parámetros auxiliares ===
    st.markdown("**Coeficientes de acoplamiento (Eqs. 38–41)**")
    st.latex(r"\alpha_{Fi} = \frac{2 \, \beta_{Fi}}{C_{FiD} \, y_{eiD} \, x_{FiD}} + \frac{s}{\eta_{FiD}}")
    st.latex(r"\beta_{Fi} = \sqrt{\alpha_{Oi}} \tanh(\sqrt{\alpha_{Oi}})")
    st.latex(r"\gamma_{Oij} = \frac{\sqrt{\alpha_{Oi}}}{2 \, C_{RijD} \, \sinh(2 \sqrt{\mu_{Oj}} \, x_{eOjD})}")

    st.markdown(r"""
    **Definiciones:**
    - \(\alpha_{Fi}\): factor que combina acoplamiento geométrico + término de Laplace.  
    - \(\beta_{Fi}\): término correctivo derivado de bloques outer (Oi).  
    - \(\gamma_{Oij}\): coeficiente de interferencia entre bloques outer j y fractura i.  
    - \(y_{eiD}, x_{FiD}, x_{eOjD}\): dimensiones adimensionales.  
    - \(s\): variable de Laplace.  
    - \(\eta_{FiD}\): difusividad hidráulica adimensional.  
    """)

    # === Índices ===
    st.markdown(r"""
    **Índices y subíndices:**
    - \(i = 1,\dots,n_f\): fractura dentro de un pozo.  
    - \(j\): bloque o fractura vecino (interferencia).  
    - \(F\): fractura.  
    - \(O\): outer block.  
    - \(K\): dominio (I, O).  
    """)

    # === Concepto general ===
    st.markdown(r"""
    **Concepto:**  
    Estas ecuaciones permiten construir un sistema completo que describe:
    - El flujo en cada fractura (\(r_i\)).  
    - El acoplamiento entre fracturas de un mismo pozo.  
    - La interferencia entre fracturas de distintos pozos (a través de \(\gamma_{Oij}\)).  

    En el código, este sistema se representa implícitamente en la **matriz \(\mathbf{R}(s)\)** 
    cuando se calculan `R_self` y `R_cross`.  
    Así se pasa del caso SingleWell (solo \(R_{self}\)) al caso MultiWell con interferencia.
    """)

    # === Conexión con código y datos intermedios ===
    if params is not None:
        n_f = params["n_f"]
        spacing = params["spacing"]
        xe = params["xe"]

        st.markdown("**Ejemplo con inputs actuales:**")
        st.markdown(f"- Número de fracturas: n_f = {n_f}")
        st.markdown(f"- Spacing entre fracturas: {spacing} ft")
        st.markdown(f"- 2xe (half-length ORV): {xe} ft")
        st.markdown("→ Estos parámetros determinan la dimensión de la matriz R(s).")

def multi_tab(params, well_params=None, schedules=None):
    st.subheader("🧩 Modelo multifractura (multi-pozo)")

    if well_params:
        st.markdown("### 📊 Configuración por pozo")
        for wname, wvals in well_params.items():
            n_f = wvals["n_frac"]
            spacing = wvals["spacing"]
            st.markdown(f"- **{wname}** → {n_f} fracturas, spacing = {spacing} ft")

        st.markdown("""
        Cada pozo puede tener un número distinto de fracturas.
        Esto permite analizar configuraciones heterogéneas de completación.
        """)
    else:
        st.warning("No se pasó `well_params`. Usando defaults.")
        n_f = params.get("n_f", 10)
        st.markdown(f"- n_f (global) = {n_f}")
