import streamlit as st

def dual_tab(params=None):
    st.subheader("🧩 Parámetros dual-porosidad — SPE-215031-PA")

    # === Omega ===
    st.markdown("**Referencia: Eq. (26)**")
    st.latex(r"\omega_{Ki} = \frac{\phi_{fKi} c_{fKi}}{\phi_{fKi} c_{fKi} + \phi_{mKi} c_{mKi}}")
    st.markdown(r"""
    **Definiciones:**
    - $ \omega_{Ki} $: storativity (fracción de almacenamiento en fracturas).  
    - $ \phi_{fKi}, c_{fKi} $: porosidad y compresibilidad de fractura en bloque $ Ki $.  
    - $ \phi_{mKi}, c_{mKi} $: porosidad y compresibilidad de matriz en bloque $ Ki $.  

    **Índices:**
    - $K = I$: inner (fractura).  
    - $K = O$: outer (matriz).  
    - $i = 1,\dots,n$: bloque.  

    **Concepto:**  
    $\omega$ mide la proporción del almacenamiento total que reside en fracturas.
    """)

    # === Lambda ===
    st.markdown("**Referencia: Eq. (27)**")
    st.latex(r"\lambda_{Ki} = \sigma_{Ki} \left(\frac{k_{mKi}}{k_{fKi}}\right) x_{FR}^2")
    st.markdown(r"""
    **Definiciones:**
    - $\lambda_{Ki}$: interporosidad (intensidad del flujo matriz-fractura).  
    - $k_{mKi}$: permeabilidad de matriz.  
    - $k_{fKi}$: permeabilidad de fractura.  
    - $\sigma_{Ki}$: shape factor del bloque.  
    - $x_{FR}$: medio-ancho de fractura.  

    **Concepto:**  
    $\lambda$ controla qué tan rápido la matriz libera fluido hacia la fractura.
    """)

    # === Sigma ===
    st.markdown("**Referencia: Eq. (28)**")
    st.latex(r"\sigma_{Ki} = \frac{12}{h_{mKi}^2}")
    st.markdown(r"""
    **Definiciones:**
    - $\sigma_{Ki}$: factor de forma para geometría tipo slab.  
    - $h_{mKi}$: espesor de bloque matriz.  

    **Concepto:**  
    Cuanto más delgado es el bloque, más eficiente es el intercambio 
    matriz-fractura ($\sigma$ crece).
    """)

    # === f(s) ===
    st.markdown("**Referencia: Eq. (31)**")
    st.latex(r"f_{Ki}(s_{Ki}) = \frac{\tanh(\sqrt{s_{Ki}})}{\sqrt{s_{Ki}}}")
    st.markdown(r"""
    **Definiciones:**
    - $f_{Ki}(s_{Ki})$: función de transferencia entre matriz y fractura.  
    - $s_{Ki}$: variable adimensional en Laplace para el bloque Ki.  

    **Concepto:**  
    Representa la respuesta dinámica del bloque matriz al intercambio con fractura.
    """)

    # === Conexión con código ===
    if params is not None:
        phi_f = params.get("phi_f", 0.1)
        ct_f = params.get("ct_f", 1e-4)
        phi_m = params.get("phi_m", 0.05)
        ct_m = params.get("ct_m", 2e-5)
        k_m = params.get("k_m", 100)
        k_f = params.get("k_f", 1000)
        h = params["h"]
        xe = params["xe"]

        omega = (phi_f*ct_f) / (phi_f*ct_f + phi_m*ct_m)
        sigma = 12.0 / (h**2)
        lam = sigma * (k_m/k_f) * (xe**2)

        st.markdown("**Valores intermedios (según inputs actuales):**")
        st.markdown(f"- ω = {omega:.3f}")
        st.markdown(f"- σ = {sigma:.3e} [1/ft²]")
        st.markdown(f"- λ = {lam:.3e} (adimensional)")
