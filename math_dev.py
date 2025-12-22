import streamlit as st

def math_tab(params=None,well_params=None):
    """Pestaña de desarrollo matemático (SPE-215031-PA)."""
    st.subheader("📓 Desarrollo matemático - SPE-215031-PA")

    # ===== 1. Difusión =====
    with st.expander("1️⃣ Ecuación de difusión 1D"):
        st.markdown("**Referencia: Eq. (1) del paper**")
        st.latex(r"""
        \frac{\partial p}{\partial t}
        = \frac{k}{\mu \, c_t \, \phi}
          \frac{\partial^2 p}{\partial x^2}
        """)
        st.markdown(r"""
        **Definiciones:**
        - $p(x,t)$: presión en el medio poroso $[psi]$.  
        - $t$: tiempo $[días \ o \ segundos]$.  
        - $k$: permeabilidad de la roca $[nD]$ → en código: `params['k_I']` o `params['k_O']`.  
        - $\mu$: viscosidad del fluido $[cp]$ → `params['mu']`.  
        - $c_t$: compresibilidad total $[1/psi]$ → `params['ct']`.  
        - $\phi$: porosidad (adimensional).  
        - $x$: coordenada espacial $[ft]$.  

        La combinación $\phi c_t$ controla el **almacenamiento** en cada bloque.
        """)

    # ===== 2. Condiciones =====
    with st.expander("2️⃣ Condiciones iniciales y de contorno"):
        st.markdown("**Referencia: Eqs. (2-3)**")
        st.latex(r"p(x,0) = p_{res}")
        st.latex(r"\left.\frac{\partial p}{\partial x}\right|_{x=\pm L} = 0")
        st.markdown(r"""
        **Definiciones:**
        - $p_{res}$: presión inicial uniforme $[psi]$ → `params['p_res']`.  
        - Condición de no flujo en $\pm L$: $\partial p / \partial x = 0$.  

        Los bloques O/I representan un sistema **cerrado lateralmente**, consistente con esta condición.
        """)

    # ===== 3. Laplace =====
    with st.expander("3️⃣ Transformada de Laplace"):
        st.markdown("**Referencia: Eq. (5)**")
        st.latex(r"""
        s \, \hat{p}(x,s) - p_{res}
        = \frac{k}{\mu c_t}\,\frac{\mathrm{d}^2 \hat{p}}{\mathrm{d}x^2}
        + \frac{\hat q(s)}{A}\,\delta(x)
        """)
        st.markdown(r"""
        **Definiciones:**
        - $\hat{p}(x,s)$: presión en Laplace.  
        - $\hat{q}(s)$: caudal en Laplace (ej. caudal constante → $q/s$).  
        - $A$: área transversal del bloque.  
        - $\delta(x)$: fuente puntual en el pozo.  

        En el código, esto se implementa a través de las funciones `R_self` y `R_cross`.
        """)

    # ===== 4. Green =====
    with st.expander("4️⃣ Función de Green"):
        st.markdown("**Referencia: Apéndice A, Eq. (A-2)**")
        st.latex(r"""
        \hat{p}(x,s) = \int G(x,\xi,s)\,\hat{q}(\xi,s)\,d\xi
        """)
        st.markdown(r"""
        **Definiciones:**
        - $G(x,\xi,s)$: función de Green en Laplace.  
        - $\xi$: posición de la fuente.  

        En este modelo no se evalúa $G$ directamente, sino que se usan soluciones
        cerradas → $R_{self}$ y $R_{cross}$.
        """)

    # ===== 5. Resistencias =====
    with st.expander("5️⃣ Resistencias hidráulicas"):
        st.markdown("**Referencia: Eqs. (9-10)**")
        st.latex(r"R_{self}(s) \quad \text{y} \quad R_{cross}(s,D_{ij})")
        st.markdown(r"""
        **Definiciones:**
        - $R_{self}(s)$: presión inducida en un pozo por su propio caudal.  
          → `R_self(mu, ct, k_I, k_O, h, LxI, LxOend, s)`  
        - $R_{cross}(s,D_{ij})$: presión inducida en el pozo $i$ por otro pozo $j$ a distancia $D_{ij}$.  
          → `R_cross(mu, ct, k_O, h, D_ij, s)`  

        Son funciones de transferencia derivadas de las soluciones de Green en bloques O/I.
        """)

    # ===== 6. Multiwell =====
    with st.expander("6️⃣ Sistema matricial Multiwell"):
        st.markdown("**Referencia: Eq. (12)**")
        st.latex(r"""
        \hat{\mathbf{p}}(s) =
        \mathbf{R}(s)\,\hat{\mathbf{q}}(s) +
        \frac{p_{res}}{s}\,\mathbf{1}
        """)
        st.markdown(r"""
        **Definiciones:**
        - $\hat{\mathbf{p}}(s)$: vector de presiones en Laplace.  
        - $\hat{\mathbf{q}}(s)$: vector de caudales en Laplace.  
        - $\mathbf{R}(s)$: matriz de resistencias $N\times N$.  
          - Diagonal → $R_{self}$.  
          - Fuera de diagonal → $R_{cross}$.  
        - $\mathbf{1}$: vector de unos.  
        """)

    # ===== 7. Flujo trilineal =====
    # ===== 7. Flujo trilineal =====
    with st.expander("7️⃣ Flujo trilineal 1D"):
        st.markdown("**Referencia: secciones intermedias del paper**")
        st.markdown(r"""
        El flujo trilineal acopla **tres dominios**:
        1. El bloque de fractura (SRV o Inner, con alta permeabilidad $k_I$).  
        2. El bloque matriz adyacente (ORV, con baja permeabilidad $k_O$).  
        3. El continuo externo (Outer extendido).  

        Cada dominio se modela con una ecuación de difusión 1D, y se acoplan
        mediante condiciones de frontera en las interfaces.
        """)

        st.latex(r"""
        q_{total}(t) = q_{SRV}(t) + q_{ORV}(t) + q_{ext}(t)
        """)

        st.markdown(r"""
        En el código:
        - "SingleWell" usa solo $R_{self}$ (sin interferencia).  
        - "MultiWell" incluye además $R_{cross}$ entre pozos.  
        """)

        # === SVG esquema simple ===
        svg_code = """
        <svg xmlns="http://www.w3.org/2000/svg" width="700" height="150">
          <!-- SRV -->
          <rect x="50" y="40" width="180" height="70" fill="#cce6ff" stroke="black"/>
          <text x="60" y="65" font-size="14">SRV (k_I alto)</text>
          <!-- Pozo -->
          <line x1="140" y1="35" x2="140" y2="110" stroke="#d62728" stroke-width="3"/>
          <text x="120" y="30" font-size="12" fill="#d62728">Pozo</text>

          <!-- ORV -->
          <rect x="230" y="40" width="180" height="70" fill="#eeeeee" stroke="black"/>
          <text x="240" y="65" font-size="14">ORV (k_O bajo)</text>

          <!-- Externo -->
          <rect x="410" y="40" width="200" height="70" fill="#dddddd" stroke="black"/>
          <text x="420" y="65" font-size="14">Continuo externo</text>

          <!-- Flechas -->
          <line x1="230" y1="75" x2="230" y2="75" stroke="black"/>
          <line x1="50" y1="75" x2="230" y2="75" stroke="black" marker-end="url(#arrow)"/>
          <line x1="230" y1="75" x2="410" y2="75" stroke="black" marker-end="url(#arrow)"/>

          <defs>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="6" refY="3"
              orient="auto" markerUnits="strokeWidth">
              <path d="M0,0 L0,6 L9,3 z" fill="#000"/>
            </marker>
          </defs>
        </svg>
        """
        st.components.v1.html(svg_code, height=180)

    # ===== 8. Conversión de dimensiones =====
    with st.expander("8️⃣ Conversión de dimensiones"):
        st.markdown("**Unidades originales vs SI**")
        st.markdown(r"""
        - $k$: nD → m² (`si_k`)  
        - $\mu$: cp → Pa·s (`si_mu`)  
        - $c_t$: 1/psi → 1/Pa (`si_ct`)  
        - $h$: ft → m (`si_h`)  
        - $L$: ft → m (`si_L`)  
        - $p$: psi → Pa (`PSI_TO_PA`)  
        """)

    # ===== 9. Convolución =====
    with st.expander("9️⃣ Convolución en el tiempo"):
        st.markdown("**Referencia: Eq. (15)**")
        st.latex(r"""
        p(t) = p_{res} - \int_0^t R(\tau)\, q(t-\tau)\,d\tau
        """)
        st.markdown(r"""
        - $q(t)$: caudal.  
        - $R(\tau)$: kernel de respuesta.  
        
        En el código, esta integral se evalúa por **inversión numérica de Laplace** (`invert_stehfest_vec`).  
        En MultiWell, la convolución se aplica a la matriz completa $\mathbf{R}(s)$.
        """)

    # ===== 10. Datos intermedios =====
    if params is not None:
        with st.expander("📊 Datos intermedios (según inputs actuales)"):
            st.markdown(f"- $\mu$ = {params['mu']} $cp$ → viscosidad")
            st.markdown(f"- $c_t$ = {params['ct']:.1e} $1/psi$ → compresibilidad total")
            st.markdown(f"- $k_I$ = {params['k_I']} $nD$, $k_O$ = {params['k_O']} $nD$ → permeabilidades")
            st.markdown(f"- $h$ = {params['h']} $ft$ → espesor")
            st.markdown(f"- $LxI$ = {params['LxI']} $ft$, $LxOend$ = {params['LxOend']} $ft$")
            st.markdown(f"- $2x_e$ = {params['xe']} $ft$")
            st.markdown(f"- $p_res$ = {params['p_res']} $psi$ → presión inicial")
            if "q_stb" in params:
                st.markdown(f"- $q$ = {params['q_stb']} $STB/d$ → caudal de producción")

    if well_params:
        st.markdown("### 📊 Datos por pozo")
        for wname, wvals in well_params.items():
            st.markdown(f"- {wname}: spacing = {wvals['spacing']} $ft$, $n_frac$ = {wvals['n_frac']}")
    else:
        st.markdown(f"- spacing_g = {params.get('spacing','(no definido)')} $ft$, $2x_e$ = {params.get('xe','(no definido)')} $ft$")
