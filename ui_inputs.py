import streamlit as st


def sidebar_inputs(default_params=None, default_wells=None, default_schedules=None):
    """
    Sidebar de inputs con valores iniciales (defaults) tomados de un ejemplo del paper.
    - default_params: dict con propiedades de roca/fluido
    - default_wells: dict con pozos {"well_1": {"n_frac":..., "spacing":..., "color":...}, ...}
    - default_schedules: dict con schedules {"well_1":[{"t_ini":..., "q":...}, ...], ...}
    """

    # Usamos copias para no modificar los originales
    params = default_params.copy() if default_params else {}
    well_params = default_wells.copy() if default_wells else {}
    schedules = default_schedules.copy() if default_schedules else {}

    st.sidebar.header("Parámetros de reservorio")
    params["mu"] = st.sidebar.number_input("Viscosidad μ (cP)", value=params.get("mu", 1.0))
    params["ct"] = st.sidebar.number_input("Compresibilidad total ct (1/psi)", value=params.get("ct", 1e-6), format="%.1e")
    params["k_I"] = st.sidebar.number_input("Permeabilidad SRV k_I (nD)", value=params.get("k_I", 500))
    params["k_O"] = st.sidebar.number_input("Permeabilidad ORV k_O (nD)", value=params.get("k_O", 100))
    params["h"] = st.sidebar.number_input("Espesor h (ft)", value=params.get("h", 80))
    params["LxI"] = st.sidebar.number_input("Longitud inner block LxI (ft)", value=params.get("LxI", 5000))
    params["LxOend"] = st.sidebar.number_input("Longitud outer block LxOend (ft)", value=params.get("LxOend", 300))
    params["xe"] = st.sidebar.number_input("xe (ft)", value=params.get("xe", 40))
    params["p_res"] = st.sidebar.number_input("Presión inicial p_res (psi)", value=params.get("p_res", 4000))

    # ==== Configuración de pozos ====
    st.sidebar.subheader("Pozos")
    n_wells = len(well_params) if well_params else 1
    params["n_wells"] = st.sidebar.number_input("Número de pozos", 1, 10, n_wells)

    for i in range(int(params["n_wells"])):
        wname = f"well_{i+1}"
        if wname not in well_params:
            well_params[wname] = {"n_frac": 10, "spacing": 300, "color": f"hsl({i*60},70%,50%)"}

        st.sidebar.markdown(f"**{wname}**")
        well_params[wname]["n_frac"] = st.sidebar.number_input(
            f"N° fracturas {wname}", min_value=1, max_value=50,
            value=well_params[wname].get("n_frac", 10), key=f"frac_{wname}"
        )
        well_params[wname]["spacing"] = st.sidebar.number_input(
            f"Espaciamiento {wname} (ft)", min_value=50, max_value=2000,
            value=well_params[wname].get("spacing", 300), key=f"spacing_{wname}"
        )

    # ==== Caudales (schedule) ====
    st.sidebar.subheader("Schedules (solo vista)")
    # 🚨 Por simplicidad solo mostramos, no editamos acá.
    # En el futuro se puede agregar editor dinámico.
    for wname, sched in schedules.items():
        st.sidebar.markdown(f"**{wname}**")
        for step in sched:
            st.sidebar.markdown(f"- t={step['t_ini']} d → q={step['q']} STB/D")

    return params, schedules, well_params


def glossary():
    """Expander con glosario de símbolos SPE-215031-PA."""
    with st.expander("📖 Glosario de símbolos (SPE-215031-PA)", expanded=False):
        st.markdown("### Parámetros del fluido y roca")
        st.markdown(r"$\mu$: Viscosidad del fluido $[cp]$")
        st.markdown(r"$c_t$: Compresibilidad total $[1/psi]$")
        st.markdown(r"$k_I$: Permeabilidad bloque interno (SRV) $[nD]$")
        st.markdown(r"$k_O$: Permeabilidad bloque externo (ORV) $[nD]$")
        st.markdown(r"$h$: Espesor del reservorio $[ft]$")

        st.markdown("### Geometría de bloques")
        st.markdown(r"$L_{x,I}$: Semi-longitud bloque I (SRV) $[ft]$")
        st.markdown(r"$L_{x,O,end}$: Semi-longitud bloque O extremo $[ft]$")
        st.markdown(r"$L_{x,O,int}$: Semi-longitud bloque O interno $[ft]$")
        st.markdown(r"$spacing_g$: Separación vertical entre pozos $[ft]$")
        st.markdown(r"$2x_e$: Ancho de bloque O (Outer) $[ft]$")

        st.markdown("### Pozos")
        st.markdown(r"$n_f$: Número de fracturas por pozo")
        st.markdown(r"$x_f$: Half-length de fractura $[ft]$")

        st.markdown("### Condiciones iniciales")
        st.markdown(r"$p_{res}$: Presión inicial del reservorio $[psi]$")
