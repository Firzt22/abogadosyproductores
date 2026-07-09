import streamlit as st
import pandas as pd
import io
import os
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Tablero de Control - Legales ATM", layout="wide")

# Estilos CSS personalizados para el diseño corporativo Bordó
st.markdown("""
    <style>
    /* Cambiar el color de los títulos principales */
    .main-title {
        color: #8B1D41;
        font-family: 'Segoe UI', sans-serif;
        font-weight: bold;
        text-align: center;
        margin-bottom: 25px;
    }
    /* Estilo de los encabezados de sección */
    .section-header {
        color: #8B1D41;
        font-family: 'Segoe UI', sans-serif;
        font-weight: bold;
        margin-top: 20px;
        border-bottom: 2px solid #8B1D41;
        padding-bottom: 5px;
    }
    /* Sutil decoración para las tarjetas informativas */
    .css-1r6g72q {
        background-color: #fcf8f9;
        border-left: 5px solid #8B1D41;
    }
    /* Estilizar botones de Streamlit con color bordó */
    div.stButton > button:first-child {
        background-color: #8B1D41;
        color: white;
        border-radius: 5px;
        border: none;
    }
    div.stButton > button:first-child:hover {
        background-color: #A2244F;
        color: white;
    }
    /* Estilo personalizado para la info del responsable corporativo */
    .responsable-box {
        background-color: #fdf2f4;
        border: 1px solid #8B1D41;
        border-radius: 5px;
        padding: 12px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# MÓDULO DE AUTENTICACIÓN (LOGIN)
# -------------------------------------------------------------------------
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 class='main-title'>🔒 Ingreso al Sistema Legales</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("formulario_login"):
            usuario = st.text_input("Usuario", placeholder="Ingrese su legajo o usuario")
            contraseña = st.text_input("Contraseña", type="password", placeholder="••••••••")
            boton_ingresar = st.form_submit_button("Iniciar Sesión")
            
            if boton_ingresar:
                if usuario == "mdondo" and contraseña == "ATM2026":
                    st.session_state['autenticado'] = True
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos. Por favor, intente nuevamente.")
    st.stop()

# -------------------------------------------------------------------------
# PÁGINA PRINCIPAL (SISTEMA LOGUEADO)
# -------------------------------------------------------------------------

# Carga del logo contemplando la extensión duplicada detectada en el repositorio
if os.path.exists("atmlogo.png.png"):
    st.sidebar.image("atmlogo.png.png", use_container_width=True)
elif os.path.exists("atmlogo.png"):
    st.sidebar.image("atmlogo.png", use_container_width=True)
else:
    st.sidebar.markdown("<h2 style='color: #8B1D41; font-weight: bold; text-align: center;'>ATM SEGUROS</h2>", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>🏛️ Panel de Gestión - Mediaciones & Juicios</h1>", unsafe_allow_html=True)

# Barra lateral para la carga de datos estructurada
st.sidebar.markdown("### 📁 Carga de Información")

file_mediaciones = st.sidebar.file_uploader("Seleccione el archivo de Mediaciones", type=["xlsx", "csv"], key="uploader_m")
file_juicios = st.sidebar.file_uploader("Seleccione el archivo de Juicios", type=["xlsx", "csv"], key="uploader_j")
file_vigentes = st.sidebar.file_uploader("Seleccione el archivo de VIGENTES", type=["xlsx", "csv"], key="uploader_v")
file_responsables = st.sidebar.file_uploader("Seleccione el archivo de RESPONSABLES", type=["xlsx", "csv"], key="uploader_r")


# -------------------------------------------------------------------------
# FUNCIONES OPTIMIZADAS CON CACHE (Evitan reprocesar en cada clic)
# -------------------------------------------------------------------------

def leer_archivo(file_obj, file_name):
    """Lee el archivo basándose en su nombre original, evitando fallos de BytesIO."""
    if file_name.lower().endswith('.csv'):
        return pd.read_csv(file_obj, header=None)
    else:
        return pd.read_excel(file_obj, header=None)

def normalizar_codigo(val):
    if pd.isna(val):
        return "SIN CÓDIGO"
    val_str = str(val).strip()
    if val_str.endswith('.0'):
        val_str = val_str[:-2]
    val_upper = val_str.upper()
    return val_upper if val_upper != "" else "SIN CÓDIGO"


@st.cache_data
def procesar_archivo_responsables(file_bytes, file_name):
    """Procesa el archivo de responsables y genera los mapeos jerárquicos."""
    df_r_raw = leer_archivo(io.BytesIO(file_bytes), file_name)
    
    map_resp_prod = {}
    map_resp_org = {}
    map_resp_master = {}
    responsables_asignaciones = []
    
    # --- PRODUCTOR ---
    df_r_prod = df_r_raw[[0, 1, 6, 7]].dropna(subset=[0]).copy()
    df_r_prod[0] = df_r_prod[0].apply(normalizar_codigo)
    df_r_prod[6] = df_r_prod[6].apply(normalizar_codigo)
    df_r_prod[7] = df_r_prod[7].fillna("").astype(str).str.strip().str.upper()
    
    df_r_prod['Resp_String'] = df_r_prod.apply(lambda r: f"[{r[6]}] {r[7]}" if r[6] != "SIN CÓDIGO" else "SIN RESPONSABLE ASIGNADO", axis=1)
    map_resp_prod = df_r_prod.groupby(0)['Resp_String'].apply(lambda x: " / ".join(x.unique())).to_dict()
    
    for _, fila in df_r_prod.iterrows():
        if fila[7] != "" and fila[0] != "SIN CÓDIGO":
            responsables_asignaciones.append({'Responsable': fila[7], 'Tipo': 'Productor', 'Código': fila[0]})
    
    # --- ORGANIZADOR ---
    df_r_org = df_r_raw[[2, 3, 6, 7]].dropna(subset=[2]).copy()
    df_r_org[2] = df_r_org[2].apply(normalizar_codigo)
    df_r_org[6] = df_r_org[6].apply(normalizar_codigo)
    df_r_org[7] = df_r_org[7].fillna("").astype(str).str.strip().str.upper()
    
    df_r_org['Resp_String'] = df_r_org.apply(lambda r: f"[{r[6]}] {r[7]}" if r[6] != "SIN CÓDIGO" else "SIN RESPONSABLE ASIGNADO", axis=1)
    map_resp_org = df_r_org.groupby(2)['Resp_String'].apply(lambda x: " / ".join(x.unique())).to_dict()
    
    for _, fila in df_r_org.iterrows():
        if fila[7] != "" and fila[2] != "SIN CÓDIGO":
            responsables_asignaciones.append({'Responsable': fila[7], 'Tipo': 'Organizador', 'Código': fila[2]})
    
    # --- MASTER ---
    df_r_master = df_r_raw[[4, 5, 6, 7]].dropna(subset=[4]).copy()
    df_r_master[4] = df_r_master[4].apply(normalizar_codigo)
    df_r_master[6] = df_r_master[6].apply(normalizar_codigo)
    df_r_master[7] = df_r_master[7].fillna("").astype(str).str.strip().str.upper()
    
    df_r_master['Resp_String'] = df_r_master.apply(
        lambda r: f"[{r[6]}] {r[7]}" if r[6] != "SIN CÓDIGO" and r[7] != "" else ("SIN RESPONSABLE ASIGNADO" if r[6] == "SIN CÓDIGO" else f"[{r[6]}] SIN NOMBRE")
    , axis=1)
    
    map_resp_master = df_r_master.groupby(4)['Resp_String'].apply(
        lambda x: "  //  ".join([resp for resp in x.unique() if resp != "SIN RESPONSABLE ASIGNADO"]) 
        if len(x.unique()) > 1 else x.unique()[0]
    ).to_dict()
    
    for _, fila in df_r_master.iterrows():
        if fila[7] != "" and fila[4] != "SIN CÓDIGO":
            responsables_asignaciones.append({'Responsable': fila[7], 'Tipo': 'Master', 'Código': fila[4]})
            
    return map_resp_prod, map_resp_org, map_resp_master, responsables_asignaciones


@st.cache_data
def procesar_archivo_vigentes(file_bytes, file_name):
    """Procesa el archivo maestro de Vigentes y genera relaciones comerciales."""
    df_v_raw = leer_archivo(io.BytesIO(file_bytes), file_name)
    
    df_v_limpio = df_v_raw[[0, 1, 3, 4, 5, 6]].copy()
    df_v_limpio.columns = ['Ramo', 'Prod_Codigo', 'Org_Codigo', 'Org_Nombre', 'Master_Codigo', 'Master_Nombre']
    
    df_v_limpio['Ramo'] = df_v_limpio['Ramo'].fillna("").astype(str).str.strip()
    df_v_limpio['Prod_Codigo'] = df_v_limpio['Prod_Codigo'].apply(normalizar_codigo)
    df_v_limpio['Org_Codigo'] = df_v_limpio['Org_Codigo'].apply(normalizar_codigo)
    df_v_limpio['Org_Nombre'] = df_v_limpio['Org_Nombre'].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
    df_v_limpio['Master_Codigo'] = df_v_limpio['Master_Codigo'].apply(normalizar_codigo)
    df_v_limpio['Master_Nombre'] = df_v_limpio['Master_Nombre'].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
    
    map_prod_org = df_v_limpio[['Prod_Codigo', 'Org_Codigo']].drop_duplicates(subset=['Prod_Codigo']).set_index('Prod_Codigo')['Org_Codigo'].to_dict()
    map_prod_master = df_v_limpio[['Prod_Codigo', 'Master_Codigo']].drop_duplicates(subset=['Prod_Codigo']).set_index('Prod_Codigo')['Master_Codigo'].to_dict()
    
    df_map_org_name = df_v_limpio[df_v_limpio['Org_Nombre'] != "SIN ASIGNAR"][['Org_Codigo', 'Org_Nombre']].drop_duplicates(subset=['Org_Codigo'])
    map_org_nombres = df_map_org_name.set_index('Org_Codigo')['Org_Nombre'].to_dict()
    
    df_map_master_name = df_v_limpio[df_v_limpio['Master_Nombre'] != "SIN ASIGNAR"][['Master_Codigo', 'Master_Nombre']].drop_duplicates(subset=['Master_Codigo'])
    map_master_nombres = df_map_master_name.set_index('Master_Codigo')['Master_Nombre'].to_dict()
    
    conteo_vigentes_prod = df_v_limpio['Prod_Codigo'].value_counts().reset_index()
    conteo_vigentes_prod.columns = ['Código', 'Vigentes']

    df_v_filtrado_basura = df_v_limpio[~df_v_limpio['Org_Codigo'].isin(['CÓDIGO', 'CODIGO', 'ORGANIZADOR', 'SIN CÓDIGO'])]
    v_totales_org = df_v_filtrado_basura['Org_Codigo'].value_counts().to_dict()
    
    df_v_filtrado_basura_m = df_v_limpio[~df_v_limpio['Master_Codigo'].isin(['CÓDIGO', 'CODIGO', 'MASTER', 'SIN CÓDIGO'])]
    v_totales_master = df_v_filtrado_basura_m['Master_Codigo'].value_counts().to_dict()

    df_rel_org_prod = df_v_filtrado_basura[['Org_Codigo', 'Prod_Codigo']].drop_duplicates()
    df_rel_master_org = df_v_filtrado_basura_m[['Master_Codigo', 'Org_Codigo']].drop_duplicates()
    
    return (df_v_limpio, map_prod_org, map_prod_master, map_org_nombres, 
            map_master_nombres, conteo_vigentes_prod, v_totales_org, 
            v_totales_master, df_rel_org_prod, df_rel_master_org)


@st.cache_data
def consolidar_expedientes(file_m_bytes, file_m_name, file_j_bytes, file_j_name, map_prod_org, map_prod_master):
    """Lee y cruza de manera eficiente los dataframes de mediaciones y juicios."""
    df_m_raw = leer_archivo(io.BytesIO(file_m_bytes), file_m_name)
    df_j_raw = leer_archivo(io.BytesIO(file_j_bytes), file_j_name)
    
    # Mapas de productores desde Mediaciones y Juicios
    df_m_p_map = df_m_raw[[11, 12]].copy()
    df_m_p_map[11] = df_m_p_map[11].apply(normalizar_codigo)
    df_m_p_map[12] = df_m_p_map[12].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
    map_m_prod = df_m_p_map[df_m_p_map[12] != "SIN ASIGNAR"].drop_duplicates(subset=[11]).set_index(11)[12].to_dict()

    df_j_p_map = df_j_raw[[14, 15]].copy()
    df_j_p_map[14] = df_j_p_map[14].apply(normalizar_codigo)
    df_j_p_map[15] = df_j_p_map[15].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
    map_j_prod = df_j_p_map[df_j_p_map[15] != "SIN ASIGNAR"].drop_duplicates(subset=[14]).set_index(14)[15].to_dict()
    
    # Unificación de diccionarios de nombres de productores
    map_total_productores = {**map_m_prod, **map_j_prod}

    # Mediaciones Netas
    df_m_prod_neto = df_m_raw[[11]].copy()
    df_m_prod_neto.columns = ['Prod_Codigo']
    df_m_prod_neto['Prod_Codigo'] = df_m_prod_neto['Prod_Codigo'].apply(normalizar_codigo)
    df_m_prod_neto['Org_Codigo'] = df_m_prod_neto['Prod_Codigo'].map(map_prod_org).fillna("SIN ORGANIZADOR")
    df_m_prod_neto['Master_Codigo'] = df_m_prod_neto['Prod_Codigo'].map(map_prod_master).fillna("SIN MASTER")
    
    conteo_prod_m = df_m_prod_neto['Prod_Codigo'].value_counts().reset_index(name='Mediaciones').rename(columns={'index':'Código'})
    conteo_org_m = df_m_prod_neto['Org_Codigo'].value_counts().reset_index(name='Mediaciones').rename(columns={'index':'Org_Codigo'})
    conteo_master_m = df_m_prod_neto['Master_Codigo'].value_counts().reset_index(name='Mediaciones').rename(columns={'index':'Master_Codigo'})

    # Juicios Netos
    df_j_prod_neto = df_j_raw[[14]].copy()
    df_j_prod_neto.columns = ['Prod_Codigo']
    df_j_prod_neto['Prod_Codigo'] = df_j_prod_neto['Prod_Codigo'].apply(normalizar_codigo)
    df_j_prod_neto['Org_Codigo'] = df_j_prod_neto['Prod_Codigo'].map(map_prod_org).fillna("SIN ORGANIZADOR")
    df_j_prod_neto['Master_Codigo'] = df_j_prod_neto['Prod_Codigo'].map(map_prod_master).fillna("SIN MASTER")
    
    conteo_prod_j = df_j_prod_neto['Prod_Codigo'].value_counts().reset_index(name='Juicios').rename(columns={'index':'Código'})
    conteo_org_j = df_j_prod_neto['Org_Codigo'].value_counts().reset_index(name='Juicios').rename(columns={'index':'Org_Codigo'})
    conteo_master_j = df_j_prod_neto['Master_Codigo'].value_counts().reset_index(name='Juicios').rename(columns={'index':'Master_Codigo'})
    
    return map_total_productores, conteo_prod_m, conteo_org_m, conteo_master_m, conteo_prod_j, conteo_org_j, conteo_master_j


# --- CONTROLADOR PRINCIPAL DE CARGA ---
if file_mediaciones is not None and file_juicios is not None and file_vigentes is not None:
    
    try:
        # Leemos los bytes de los archivos requeridos para pasárselos a la caché
        m_bytes = file_mediaciones.getvalue()
        j_bytes = file_juicios.getvalue()
        v_bytes = file_vigentes.getvalue()
        
        # 1. Procesar Vigentes (Caché)
        (df_v_limpio, map_prod_org, map_prod_master, map_org_nombres, 
         map_master_nombres, conteo_vigentes_prod, v_totales_org, 
         v_totales_master, df_rel_org_prod, df_rel_master_org) = procesar_archivo_vigentes(v_bytes, file_vigentes.name)
         
        # 2. Procesar Responsables si existe (Caché)
        map_resp_prod, map_resp_org, map_resp_master, responsables_asignaciones = {}, {}, {}, []
        if file_responsables is not None:
            r_bytes = file_responsables.getvalue()
            map_resp_prod, map_resp_org, map_resp_master, responsables_asignaciones = procesar_archivo_responsables(r_bytes, file_responsables.name)
            
        # 3. Consolidar Expedientes (Caché)
        (map_total_productores, conteo_prod_m, conteo_org_m, 
         conteo_master_m, conteo_prod_j, conteo_org_j, conteo_master_j) = consolidar_expedientes(
             m_bytes, file_mediaciones.name, j_bytes, file_juicios.name, map_prod_org, map_prod_master
         )

        # Volvemos a instanciar de manera directa solo los DataFrames puros de lectura para los desgloses específicos por fila
        df_m_raw = leer_archivo(io.BytesIO(m_bytes), file_mediaciones.name)
        df_j_raw = leer_archivo(io.BytesIO(j_bytes), file_juicios.name)

        # Helper para búsquedas de nombres en tiempo de ejecución
        def buscar_nombre_productor(cod):
            return map_total_productores.get(str(cod).strip().upper(), "SIN ASIGNAR")
        def buscar_nombre_organizador(cod):
            return map_org_nombres.get(str(cod).strip().upper(), "SIN ASIGNAR")
        def buscar_nombre_master(cod):
            return map_master_nombres.get(str(cod).strip().upper(), "SIN ASIGNAR")

        # -------------------------------------------------------------------------
        # SOLAPAS PRINCIPALES DEL TABLERO (Estructura de 6 pestañas rápidas)
        # -------------------------------------------------------------------------
        tabs = st.tabs(["⚖️ Abogados", "👤 Responsables", "💼 Productor", "🏢 Organizador", "👑 Master", "🔍 Coincidencias"])
        
        # =========================================================================
        # --- SOLAPA 1: ABOGADOS ---
        # =========================================================================
        with tabs[0]:
            st.markdown("<h3 class='section-header'>⚖️ Resumen de Carga por Profesional</h3>", unsafe_allow_html=True)
            
            col_k_abogado_m = df_m_raw.iloc[:, 10].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
            conteo_m_ab = col_k_abogado_m.value_counts().reset_index(name='Mediaciones').rename(columns={'index':'Abogado'})
            
            col_n_abogado_j = df_j_raw.iloc[:, 13].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
            conteo_j_ab = col_n_abogado_j.value_counts().reset_index(name='Juicios').rename(columns={'index':'Abogado'})
            
            df_consolidado_ab = pd.merge(conteo_m_ab, conteo_j_ab, on='Abogado', how='outer').fillna(0)
            df_consolidado_ab['Mediaciones'] = df_consolidado_ab['Mediaciones'].astype(int)
            df_consolidado_ab['Juicios'] = df_consolidado_ab['Juicios'].astype(int)
            df_consolidado_ab['Total General'] = df_consolidado_ab['Mediaciones'] + df_consolidado_ab['Juicios']
            
            titulos_limpieza_ab = ['ABOGADO', 'PROFESIONAL', 'RESPONSABLE', 'SIN ASIGNAR', 'DESCONOCIDO']
            df_consolidado_ab = df_consolidado_ab[~df_consolidado_ab['Abogado'].isin(titulos_limpieza_ab)]
            df_consolidado_ab = df_consolidado_ab.sort_values(by='Total General', ascending=False).reset_index(drop=True)
            
            busqueda_ab = st.text_input("🔍 Buscar abogado por nombre:", placeholder="Escriba el apellido o nombre del profesional...")
            df_mostrar_ab = df_consolidado_ab[df_consolidado_ab['Abogado'].str.contains(busqueda_ab.strip().upper(), na=False)].reset_index(drop=True) if busqueda_ab else df_consolidado_ab

            st.write("Seleccione un abogado de la lista para desplegar el detalle analítico abajo:")
            evento_seleccion_ab = st.dataframe(df_mostrar_ab, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="tabla_abogados")
            
            filas_seleccionadas_ab = evento_seleccion_ab.get("selection", {}).get("rows", [])
            if filas_seleccionadas_ab:
                indice_fila = filas_seleccionadas_ab[0]
                abogado_seleccionado = df_mostrar_ab.iloc[indice_fila]['Abogado']
                st.markdown(f"<h3 class='section-header'>📂 Expedientes de: {abogado_seleccionado}</h3>", unsafe_allow_html=True)
                
                mask_m = df_m_raw.iloc[:, 10].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper() == abogado_seleccionado
                df_det_m = df_m_raw[mask_m].iloc[:, [2, 3, 4, 5]].copy()
                df_det_m.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                df_det_m['TIPO'] = 'M'
                
                siniestros_m_str = df_det_m['SINIESTRO'].fillna("").astype(str).str.strip()
                m_auto = df_det_m[siniestros_m_str.str.startswith("03/")].shape[0]
                m_moto = df_det_m[~siniestros_m_str.str.startswith("03/")].shape[0]
                
                mask_j = df_j_raw.iloc[:, 13].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper() == abogado_seleccionado
                df_det_j = df_j_raw[mask_j].iloc[:, [2, 3, 5, 6]].copy()
                df_det_j.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                df_det_j['TIPO'] = 'J'
                
                siniestros_j_str = df_det_j['SINIESTRO'].fillna("").astype(str).str.strip()
                j_auto = df_det_j[siniestros_j_str.str.startswith("03/")].shape[0]
                j_moto = df_det_j[~siniestros_j_str.str.startswith("03/")].shape[0]
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric(label="🚗 Mediaciones Automotor (03/)", value=m_auto)
                c2.metric(label="🏍️ Mediaciones Motovehículo", value=m_moto)
                c3.metric(label="🚗 Juicios Automotor (03/)", value=j_auto)
                c4.metric(label="🏍️ Juicios Motovehículo", value=j_moto)
                
                df_detalle_abogado = pd.concat([df_det_m, df_det_j], ignore_index=True)
                st.dataframe(df_detalle_abogado, use_container_width=True, hide_index=True)
            else:
                st.info("💡 Consejo: Haga clic en cualquier celda o fila de la tabla superior para inspeccionar el desglose de juicios y mediaciones.")
            
            st.markdown("<h3 class='section-header'>📊 Top 25 Abogados con Mayor Volumen</h3>", unsafe_allow_html=True)
            df_top25_ab = df_consolidado_ab.head(25).copy()
            if not df_top25_ab.empty:
                df_chart_ab = df_top25_ab.melt(id_vars=['Abogado'], value_vars=['Mediaciones', 'Juicios'], var_name='Tipo Expediente', value_name='Cantidad')
                fig_ab = px.bar(
                    df_chart_ab, x='Abogado', y='Cantidad', color='Tipo Expediente',
                    color_discrete_map={'Mediaciones': '#DCA7B8', 'Juicios': '#8B1D41'}, barmode='stack',
                    labels={'Cantidad': 'Cantidad de Casos', 'Abogado': 'Profesional'}
                )
                fig_ab.update_layout(xaxis={'categoryorder':'total descending'}, margin=dict(l=20, r=20, t=10, b=40), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_ab, use_container_width=True)

        # =========================================================================
        # --- SOLAPA 2: RESPONSABLES ---
        # =========================================================================
        with tabs[1]:
            st.markdown("<h3 class='section-header'>👤 Auditoría Analítica por Responsable de Control</h3>", unsafe_allow_html=True)
            
            if file_responsables is None or len(responsables_asignaciones) == 0:
                st.info("ℹ️ Cargue el archivo de Responsables en la barra lateral para procesar la información de control.")
            else:
                df_resp_base = pd.DataFrame(responsables_asignaciones)
                
                df_v_prod_ramo = df_v_limpio.groupby(['Prod_Codigo', 'Ramo']).size().unstack(fill_value=0)
                if '3' not in df_v_prod_ramo.columns: df_v_prod_ramo['3'] = 0
                if '4' not in df_v_prod_ramo.columns: df_v_prod_ramo['4'] = 0
                
                dict_prod_m = conteo_prod_m.set_index('Código')['Mediaciones'].to_dict()
                dict_prod_j = conteo_prod_j.set_index('Código')['Juicios'].to_dict()
                
                resumen_por_responsable = []
                
                for resp, grupo in df_resp_base.groupby('Responsable'):
                    if resp == "" or resp == "NOMBRE": continue
                    
                    lista_prod_controlados = set()
                    
                    for _, fila_r in grupo.iterrows():
                        tipo_c = fila_r['Tipo']
                        cod_c = fila_r['Código']
                        
                        if tipo_c == 'Productor':
                            lista_prod_controlados.add(cod_c)
                        elif tipo_c == 'Organizador':
                            prods_de_org = df_v_limpio[df_v_limpio['Org_Codigo'] == cod_c]['Prod_Codigo'].unique()
                            lista_prod_controlados.update(prods_de_org)
                        elif tipo_c == 'Master':
                            prods_de_master = df_v_limpio[df_v_limpio['Master_Codigo'] == cod_c]['Prod_Codigo'].unique()
                            lista_prod_controlados.update(prods_de_master)
                    
                    lista_prod_controlados = [p for p in lista_prod_controlados if p not in ['SIN CÓDIGO', 'CÓDIGO']]
                    
                    vigentes_auto = 0
                    vigentes_moto = 0
                    total_m = 0
                    total_j = 0
                    
                    for p_cod in lista_prod_controlados:
                        if p_cod in df_v_prod_ramo.index:
                            vigentes_auto += df_v_prod_ramo.loc[p_cod, '3']
                            vigentes_moto += df_v_prod_ramo.loc[p_cod, '4']
                        
                        total_m += dict_prod_m.get(p_cod, 0)
                        total_j += dict_prod_j.get(p_cod, 0)
                        
                    total_vigentes = vigentes_auto + vigentes_moto
                    total_expedientes = total_m + total_j
                    
                    resumen_por_responsable.append({
                        'Responsable': resp,
                        'Vigentes Auto (R3)': int(vigentes_auto),
                        'Vigentes Moto (R4)': int(vigentes_moto),
                        'Total Vigentes': int(total_vigentes),
                        'Mediaciones': int(total_m),
                        'Juicios': int(total_j),
                        'Total Casos': int(total_expedientes)
                    })
                    
                df_tabla_responsables = pd.DataFrame(resumen_por_responsable)
                if not df_tabla_responsables.empty:
                    df_tabla_responsables = df_tabla_responsables.sort_values(by='Total Casos', ascending=False).reset_index(drop=True)
                    
                    busqueda_resp = st.text_input("🔍 Filtrar Responsable de Control:", placeholder="Escriba el nombre del analista...")
                    if busqueda_resp:
                        df_tabla_responsables = df_tabla_responsables[df_tabla_responsables['Responsable'].str.contains(busqueda_resp.strip().upper(), na=False)].reset_index(drop=True)
                        
                    st.write("Seleccione un responsable para abrir las pestañas de sus estructuras controladas por separado:")
                    evento_resp = st.dataframe(df_tabla_responsables, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="tabla_nueva_responsables")
                    
                    filas_resp = evento_resp.get("selection", {}).get("rows", [])
                    if filas_resp:
                        resp_sel = df_tabla_responsables.iloc[filas_resp[0]]['Responsable']
                        st.markdown(f"<h3 class='section-header'>📋 Estructuras Comerciales Asignadas a: {resp_sel}</h3>", unsafe_allow_html=True)
                        
                        df_sub_resp = df_resp_base[df_resp_base['Responsable'] == resp_sel]
                        
                        c_prod, c_org, c_mast = st.tabs(["💼 Productores Controlados", "🏢 Organizadores Controlados", "👑 Masters Controlados"])
                        
                        with c_prod:
                            cods_p = df_sub_resp[df_sub_resp['Tipo'] == 'Productor']['Código'].unique()
                            df_p_salida = pd.DataFrame({'Código': cods_p})
                            df_p_salida['Nombre Productor'] = df_p_salida['Código'].apply(buscar_nombre_productor)
                            st.dataframe(df_p_salida, use_container_width=True, hide_index=True)
                            
                        with c_org:
                            cods_o = df_sub_resp[df_sub_resp['Tipo'] == 'Organizador']['Código'].unique()
                            df_o_salida = pd.DataFrame({'Código': cods_o})
                            df_o_salida['Nombre Organizador'] = df_o_salida['Código'].apply(buscar_nombre_organizador)
                            st.dataframe(df_o_salida, use_container_width=True, hide_index=True)
                            
                        with c_mast:
                            cods_m = df_sub_resp[df_sub_resp['Tipo'] == 'Master']['Código'].unique()
                            df_m_salida = pd.DataFrame({'Código': cods_m})
                            df_m_salida['Nombre Master'] = df_m_salida['Código'].apply(buscar_nombre_master)
                            st.dataframe(df_m_salida, use_container_width=True, hide_index=True)
                else:
                    st.warning("No se pudieron procesar datos con la estructura actual del archivo.")

        # =========================================================================
        # --- SOLAPA 3: PRODUCTOR ---
        # =========================================================================
        with tabs[2]:
            st.markdown("<h3 class='section-header'>💼 Resumen de Carga por Productor</h3>", unsafe_allow_html=True)
            
            df_consolidado_prod = pd.merge(conteo_prod_m, conteo_prod_j, on='Código', how='outer').fillna(0)
            df_consolidado_prod['Mediaciones'] = df_consolidado_prod['Mediaciones'].astype(int)
            df_consolidado_prod['Juicios'] = df_consolidado_prod['Juicios'].astype(int)
            df_consolidado_prod['Total General'] = df_consolidado_prod['Mediaciones'] + df_consolidado_prod['Juicios']
            
            df_consolidado_prod['Nombre Productor'] = df_consolidado_prod['Código'].apply(buscar_nombre_productor)
            df_consolidado_prod = pd.merge(df_consolidado_prod, conteo_vigentes_prod, on='Código', how='left').fillna({'Vigentes': 0})
            df_consolidado_prod['Vigentes'] = df_consolidado_prod['Vigentes'].astype(int)
            
            def calcular_incidencia(row):
                if row['Vigentes'] > 0:
                    return round((row['Total General'] / row['Vigentes']) * 100, 2)
                else:
                    return 100.0 if row['Total General'] > 0 else 0.0

            df_consolidado_prod['INCIDENCIA'] = df_consolidado_prod.apply(calcular_incidencia, axis=1)
            df_consolidado_prod['INCIDENCIA (%)'] = df_consolidado_prod['INCIDENCIA'].apply(lambda x: f"{x}%")
            
            df_consolidado_prod = df_consolidado_prod[['Código', 'Nombre Productor', 'Vigentes', 'INCIDENCIA (%)', 'Mediaciones', 'Juicios', 'Total General', 'INCIDENCIA']]
            
            titulos_basura = ['CÓDIGO', 'CODIGO', 'PRODUCTOR', 'NOMBRE', 'PRODUCTOR_COD', 'SIN CÓDIGO']
            df_consolidado_prod = df_consolidado_prod[~df_consolidado_prod['Código'].isin(titulos_basura)]
            df_consolidado_prod = df_consolidado_prod.sort_values(by='INCIDENCIA', ascending=False).reset_index(drop=True)
            df_mostrar_tabla_p = df_consolidado_prod.drop(columns=['INCIDENCIA'])

            busqueda_prod = st.text_input("🔍 Buscar productor (por Código o por Nombre):", placeholder="Escriba el código numérico o el nombre del productor...", key="input_bus_prod")
            df_filtrada_prod = df_mostrar_tabla_p[df_mostrar_tabla_p['Código'].str.contains(busqueda_prod.strip().upper(), na=False) | df_mostrar_tabla_p['Nombre Productor'].str.contains(busqueda_prod.strip().upper(), na=False)].reset_index(drop=True) if busqueda_prod else df_mostrar_tabla_p

            st.write("Seleccione un productor de la lista para desplegar el análisis comercial abajo:")
            evento_seleccion_prod = st.dataframe(df_filtrada_prod, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="tabla_productores")
            
            filas_seleccionadas_prod = evento_seleccion_prod.get("selection", {}).get("rows", [])
            if filas_seleccionadas_prod:
                indice_fila_prod = filas_seleccionadas_prod[0]
                cod_seleccionado = df_filtrada_prod.iloc[indice_fila_prod]['Código']
                nom_seleccionado = df_filtrada_prod.iloc[indice_fila_prod]['Nombre Productor']
                
                st.markdown(f"<h3 class='section-header'>📂 Análisis de Cartera Comercial: [{cod_seleccionado}] - {nom_seleccionado}</h3>", unsafe_allow_html=True)
                
                if file_responsables is not None:
                    resp_info = map_resp_prod.get(cod_seleccionado, "SIN RESPONSABLE ASIGNADO")
                    st.markdown(f"<div class='responsable-box'>👤 <b>Responsable Interno de Control:</b> {resp_info}</div>", unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Cargue el archivo de Responsables en la barra lateral para ver quién controla a este productor.")
                
                sub_tab_expedientes, sub_tab_vigentes = st.tabs(["📋 Historial de Expedientes", "🚗 Detalle de Pólizas Vigentes"])
                
                with sub_tab_expedientes:
                    df_m_temp = df_m_raw.copy()
                    df_m_temp[11] = df_m_temp[11].apply(normalizar_codigo)
                    mask_prod_m = df_m_temp[11] == cod_seleccionado
                    df_det_prod_m = df_m_temp[mask_prod_m].iloc[:, [2, 3, 4, 5]].copy()
                    df_det_prod_m.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                    df_det_prod_m['TIPO'] = 'M'
                    
                    siniestros_m_prod_str = df_det_prod_m['SINIESTRO'].fillna("").astype(str).str.strip()
                    m_auto_p = df_det_prod_m[siniestros_m_prod_str.str.startswith("03/")].shape[0]
                    m_moto_p = df_det_prod_m[~siniestros_m_prod_str.str.startswith("03/")].shape[0]
                    
                    df_j_temp = df_j_raw.copy()
                    df_j_temp[14] = df_j_temp[14].apply(normalizar_codigo)
                    mask_prod_j = df_j_temp[14] == cod_seleccionado
                    df_det_prod_j = df_j_temp[mask_prod_j].iloc[:, [2, 3, 5, 6]].copy()
                    df_det_prod_j.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                    df_det_prod_j['TIPO'] = 'J'
                    
                    siniestros_j_prod_str = df_det_prod_j['SINIESTRO'].fillna("").astype(str).str.strip()
                    j_auto_p = df_det_prod_j[siniestros_j_prod_str.str.startswith("03/")].shape[0]
                    j_moto_p = df_det_prod_j[~siniestros_j_prod_str.str.startswith("03/")].shape[0]
                    
                    cp1, cp2, cp3, cp4 = st.columns(4)
                    cp1.metric(label="🚗 Mediaciones Automotor (03/)", value=m_auto_p)
                    cp2.metric(label="🏍️ Mediaciones Motovehículo", value=m_moto_p)
                    cp3.metric(label="🚗 Juicios Automotor (03/)", value=j_auto_p)
                    cp4.metric(label="🏍️ Juicios Motovehículo", value=j_moto_p)
                    
                    df_detalle_prod_final = pd.concat([df_det_prod_m, df_det_prod_j], ignore_index=True)
                    st.dataframe(df_detalle_prod_final, use_container_width=True, hide_index=True)
                
                with sub_tab_vigentes:
                    st.markdown("#### 🔍 Resumen Cuantitativo de Pólizas Activas")
                    df_v_filtrado_prod = df_v_limpio[df_v_limpio['Prod_Codigo'] == cod_seleccionado]
                    
                    ramos_series = df_v_filtrado_prod['Ramo'].fillna("").astype(str).str.strip()
                    v_auto = df_v_filtrado_prod[ramos_series == "3"].shape[0]
                    v_moto = df_v_filtrado_prod[ramos_series == "4"].shape[0]
                    v_otros = df_v_filtrado_prod[~ramos_series.isin(["3", "4"])].shape[0]
                    
                    cv1, cv2, cv3 = st.columns(3)
                    cv1.metric(label="🚗 Vigentes Automotores (Ramo 3)", value=v_auto)
                    cv2.metric(label="🏍️ Vigentes Motovehículos (Ramo 4)", value=v_moto)
                    cv3.metric(label="📊 Vigentes Otros Ramos", value=v_otros)
            else:
                st.info("💡 Consejo: Haga clic en cualquier fila para inspeccionar el desglose completo.")
            
            st.markdown("<h3 class='section-header'>📊 Top 25 Productores con Mayor Volumen de Casos</h3>", unsafe_allow_html=True)
            df_top25_prod = df_consolidado_prod.sort_values(by='Total General', ascending=False).head(25).copy()
            if not df_top25_prod.empty:
                df_top25_prod['Productor Identificador'] = "[" + df_top25_prod['Código'] + "] " + df_top25_prod['Nombre Productor']
                df_chart_prod = df_top25_prod.melt(id_vars=['Productor Identificador'], value_vars=['Mediaciones', 'Juicios'], var_name='Tipo Expediente', value_name='Cantidad')
                fig_prod = px.bar(
                    df_chart_prod, x='Productor Identificador', y='Cantidad', color='Tipo Expediente',
                    color_discrete_map={'Mediaciones': '#DCA7B8', 'Juicios': '#8B1D41'}, barmode='stack'
                )
                fig_prod.update_layout(xaxis={'categoryorder':'total descending'}, margin=dict(l=20, r=20, t=10, b=40))
                st.plotly_chart(fig_prod, use_container_width=True)

        # =========================================================================
        # --- SOLAPA 4: ORGANIZADOR ---
        # =========================================================================
        with tabs[3]:
            st.markdown("<h3 class='section-header'>🏢 Resumen de Carga por Estructura Organizadora</h3>", unsafe_allow_html=True)
            
            df_consolidado_org = pd.merge(conteo_org_m, conteo_org_j, on='Org_Codigo', how='outer').fillna(0)
            df_consolidado_org['Mediaciones'] = df_consolidado_org['Mediaciones'].astype(int)
            df_consolidado_org['Juicios'] = df_consolidado_org['Juicios'].astype(int)
            df_consolidado_org['Total General'] = df_consolidado_org['Mediaciones'] + df_consolidado_org['Juicios']
            
            df_consolidado_org['Nombre Organizador'] = df_consolidado_org['Org_Codigo'].apply(buscar_nombre_organizador)
            df_consolidado_org['Vigentes'] = df_consolidado_org['Org_Codigo'].map(v_totales_org).fillna(0).astype(int)
            
            def calcular_incidencia_org(row):
                if row['Vigentes'] > 0:
                    return round((row['Total General'] / row['Vigentes']) * 100, 2)
                else:
                    return 100.0 if row['Total General'] > 0 else 0.0

            df_consolidado_org['INCIDENCIA'] = df_consolidado_org.apply(calcular_incidencia_org, axis=1)
            df_consolidado_org['INCIDENCIA (%)'] = df_consolidado_org['INCIDENCIA'].apply(lambda x: f"{x}%")
            
            df_consolidado_org = df_consolidado_org[['Org_Codigo', 'Nombre Organizador', 'Vigentes', 'INCIDENCIA (%)', 'Mediaciones', 'Juicios', 'Total General', 'INCIDENCIA']]
            df_consolidado_org.columns = ['Código', 'Nombre Organizador', 'Vigentes', 'INCIDENCIA (%)', 'Mediaciones', 'Juicios', 'Total General', 'INCIDENCIA']
            
            titulos_basura_org = ['CÓDIGO', 'CODIGO', 'ORGANIZADOR', 'SIN CÓDIGO', 'SIN ORGANIZADOR', 'SIN ASIGNAR']
            df_consolidado_org = df_consolidado_org[~df_consolidado_org['Código'].isin(titulos_basura_org)]
            df_consolidado_org = df_consolidado_org.sort_values(by='INCIDENCIA', ascending=False).reset_index(drop=True)
            df_mostrar_tabla_o = df_consolidado_org.drop(columns=['INCIDENCIA'])
            
            busqueda_org = st.text_input("🔍 Buscar Organizador (por Código o Nombre):", placeholder="Escriba el código o nombre de la estructura...", key="input_bus_org")
            df_filtrada_org = df_mostrar_tabla_o[df_mostrar_tabla_o['Código'].str.contains(busqueda_org.strip().upper(), na=False) | df_mostrar_tabla_o['Nombre Organizador'].str.contains(busqueda_org.strip().upper(), na=False)].reset_index(drop=True) if busqueda_org else df_mostrar_tabla_o

            st.write("Seleccione un organizador de la lista para desplegar el análisis corporativo abajo:")
            evento_seleccion_org = st.dataframe(df_filtrada_org, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="tabla_organizadores")
            
            filas_seleccionadas_org = evento_seleccion_org.get("selection", {}).get("rows", [])
            if filas_seleccionadas_org:
                indice_fila_org = filas_seleccionadas_org[0]
                org_cod_sel = df_filtrada_org.iloc[indice_fila_org]['Código']
                org_nom_sel = df_filtrada_org.iloc[indice_fila_org]['Nombre Organizador']
                
                st.markdown(f"<h3 class='section-header'>📂 Análisis Integrado de Estructura: [{org_cod_sel}] {org_nom_sel}</h3>", unsafe_allow_html=True)
                
                if file_responsables is not None:
                    resp_info = map_resp_org.get(org_cod_sel, "SIN RESPONSABLE ASIGNADO")
                    st.markdown(f"<div class='responsable-box'>👤 <b>Responsable Interno de Control:</b> {resp_info}</div>", unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Cargue el archivo de Responsables en la barra lateral para ver quién controla a este organizador.")

                df_prod_asociados = df_rel_org_prod[df_rel_org_prod['Org_Codigo'] == org_cod_sel].copy()
                df_prod_asociados['Nombre Productor'] = df_prod_asociados['Prod_Codigo'].apply(buscar_nombre_productor)
                
                with st.expander("🤝 Ver Carteras y Productores Vinculados a este Organizador", expanded=False):
                    st.dataframe(df_prod_asociados[['Prod_Codigo', 'Nombre Productor']].rename(columns={'Prod_Codigo':'Código Productor Agrupado', 'Nombre Productor':'Nombre del Productor'}), use_container_width=True, hide_index=True)

                sub_tab_expedientes_o, sub_tab_vigentes_o = st.tabs(["📋 Historial de Expedientes", "🚗 Detalle de Pólizas Vigentes"])
                
                with sub_tab_expedientes_o:
                    df_m_temp_o = df_m_raw.copy()
                    df_m_temp_o[11] = df_m_temp_o[11].apply(normalizar_codigo)
                    df_m_temp_o['Org_Codigo'] = df_m_temp_o[11].map(map_prod_org).fillna("SIN ORGANIZADOR")
                    df_det_org_m = df_m_temp_o[df_m_temp_o['Org_Codigo'] == org_cod_sel].iloc[:, [2, 3, 4, 5]].copy()
                    df_det_org_m.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                    df_det_org_m['TIPO'] = 'M'
                    
                    siniestros_m_org_str = df_det_org_m['SINIESTRO'].fillna("").astype(str).str.strip()
                    m_auto_o = df_det_org_m[siniestros_m_org_str.str.startswith("03/")].shape[0]
                    m_moto_o = df_det_org_m[~siniestros_m_org_str.str.startswith("03/")].shape[0]

                    df_j_temp_o = df_j_raw.copy()
                    df_j_temp_o[14] = df_j_temp_o[14].apply(normalizar_codigo)
                    df_j_temp_o['Org_Codigo'] = df_j_temp_o[14].map(map_prod_org).fillna("SIN ORGANIZADOR")
                    df_det_org_j = df_j_temp_o[df_j_temp_o['Org_Codigo'] == org_cod_sel].iloc[:, [2, 3, 5, 6]].copy()
                    df_det_org_j.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                    df_det_org_j['TIPO'] = 'J'
                    
                    siniestros_j_org_str = df_det_org_j['SINIESTRO'].fillna("").astype(str).str.strip()
                    j_auto_o = df_det_org_j[siniestros_j_org_str.str.startswith("03/")].shape[0]
                    j_moto_o = df_det_org_j[~siniestros_j_org_str.str.startswith("03/")].shape[0]

                    co1, co2, co3, co4 = st.columns(4)
                    co1.metric(label="🚗 Mediaciones Automotor (03/)", value=m_auto_o)
                    co2.metric(label="🏍️ Mediaciones Motovehículo", value=m_moto_o)
                    co3.metric(label="🚗 Juicios Automotor (03/)", value=j_auto_o)
                    co4.metric(label="🏍️ Juicios Motovehículo", value=j_moto_o)
                    
                    df_detalle_org_final = pd.concat([df_det_org_m, df_det_org_j], ignore_index=True)
                    st.dataframe(df_detalle_org_final, use_container_width=True, hide_index=True)
                
                with sub_tab_vigentes_o:
                    st.markdown("#### 🔍 Resumen Cuantitativo de Pólizas Activas del Organizador")
                    df_v_filtrado_org = df_v_limpio[df_v_limpio['Org_Codigo'] == org_cod_sel]
                    ramos_series_o = df_v_filtrado_org['Ramo'].fillna("").astype(str).str.strip()
                    v_auto_o = df_v_filtrado_org[ramos_series_o == "3"].shape[0]
                    v_moto_o = df_v_filtrado_org[ramos_series_o == "4"].shape[0]
                    v_otros_o = df_v_filtrado_org[~ramos_series_o.isin(["3", "4"])].shape[0]
                    
                    cvo1, cvo2, cvo3 = st.columns(3)
                    cvo1.metric(label="🚗 Vigentes Automotores (Ramo 3)", value=v_auto_o)
                    cvo2.metric(label="🏍️ Vigentes Motovehículos (Ramo 4)", value=v_moto_o)
                    cvo3.metric(label="📊 Vigentes Otros Ramos", value=v_otros_o)

            st.markdown("<h3 class='section-header'>📊 Top 25 Organizadores con Mayor Volumen de Casos</h3>", unsafe_allow_html=True)
            df_top25_org = df_consolidado_org.sort_values(by='Total General', ascending=False).head(25).copy()
            if not df_top25_org.empty:
                df_top25_org['Org Identificador'] = "[" + df_top25_org['Código'] + "] " + df_top25_org['Nombre Organizador']
                df_chart_org = df_top25_org.melt(id_vars=['Org Identificador'], value_vars=['Mediaciones', 'Juicios'], var_name='Tipo Expediente', value_name='Cantidad')
                fig_org = px.bar(
                    df_chart_org, x='Org Identificador', y='Cantidad', color='Tipo Expediente',
                    color_discrete_map={'Mediaciones': '#DCA7B8', 'Juicios': '#8B1D41'}, barmode='stack',
                    labels={'Cantidad': 'Cantidad de Casos', 'Org Identificador': 'Organizador'}
                )
                fig_org.update_layout(xaxis={'categoryorder':'total descending'}, margin=dict(l=20, r=20, t=10, b=40))
                st.plotly_chart(fig_org, use_container_width=True)

        # =========================================================================
        # --- SOLAPA 5: MASTER ---
        # =========================================================================
        with tabs[4]:
            st.markdown("<h3 class='section-header'>👑 Resumen de Carga por Estructura MASTER</h3>", unsafe_allow_html=True)
            
            df_consolidado_master = pd.merge(conteo_master_m, conteo_master_j, on='Master_Codigo', how='outer').fillna(0)
            df_consolidado_master['Mediaciones'] = df_consolidado_master['Mediaciones'].astype(int)
            df_consolidado_master['Juicios'] = df_consolidado_master['Juicios'].astype(int)
            df_consolidado_master['Total General'] = df_consolidado_master['Mediaciones'] + df_consolidado_master['Juicios']
            
            df_consolidado_master['Nombre Master'] = df_consolidado_master['Master_Codigo'].apply(buscar_nombre_master)
            df_consolidado_master['Vigentes'] = df_consolidado_master['Master_Codigo'].map(v_totales_master).fillna(0).astype(int)
            
            def calcular_incidencia_master(row):
                if row['Vigentes'] > 0:
                    return round((row['Total General'] / row['Vigentes']) * 100, 2)
                else:
                    return 100.0 if row['Total General'] > 0 else 0.0

            df_consolidado_master['INCIDENCIA'] = df_consolidado_master.apply(calcular_incidencia_master, axis=1)
            df_consolidado_master['INCIDENCIA (%)'] = df_consolidado_master['INCIDENCIA'].apply(lambda x: f"{x}%")
            
            df_consolidado_master = df_consolidado_master[['Master_Codigo', 'Nombre Master', 'Vigentes', 'INCIDENCIA (%)', 'Mediaciones', 'Juicios', 'Total General', 'INCIDENCIA']]
            df_consolidado_master.columns = ['Código', 'Nombre Master', 'Vigentes', 'INCIDENCIA (%)', 'Mediaciones', 'Juicios', 'Total General', 'INCIDENCIA']
            
            titulos_basura_master = ['CÓDIGO', 'CODIGO', 'MASTER', 'SIN CÓDIGO', 'SIN MASTER', 'SIN ASIGNAR']
            df_consolidado_master = df_consolidado_master[~df_consolidado_master['Código'].isin(titulos_basura_master)]
            
            df_consolidado_master = df_consolidado_master.sort_values(by='INCIDENCIA', ascending=False).reset_index(drop=True)
            df_mostrar_tabla_m = df_consolidado_master.drop(columns=['INCIDENCIA'])
            
            busqueda_master = st.text_input("🔍 Buscar Master (por Código o Nombre):", placeholder="Escriba el código o nombre de la macro-estructura...", key="input_bus_master")
            df_filtrada_master = df_mostrar_tabla_m[df_mostrar_tabla_m['Código'].str.contains(busqueda_master.strip().upper(), na=False) | df_mostrar_tabla_m['Nombre Master'].str.contains(busqueda_master.strip().upper(), na=False)].reset_index(drop=True) if busqueda_master else df_mostrar_tabla_m

            st.write("Seleccione un Master de la lista para desplegar el análisis macro abajo:")
            evento_seleccion_master = st.dataframe(df_filtrada_master, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="tabla_masters")
            
            filas_seleccionadas_master = evento_seleccion_master.get("selection", {}).get("rows", [])
            if filas_seleccionadas_master:
                indice_fila_master = filas_seleccionadas_master[0]
                master_cod_sel = df_filtrada_master.iloc[indice_fila_master]['Código']
                master_nom_sel = df_filtrada_master.iloc[indice_fila_master]['Nombre Master']
                
                st.markdown(f"<h3 class='section-header'>📂 Análisis Integrado de Macro-Estructura Master: [{master_cod_sel}] {master_nom_sel}</h3>", unsafe_allow_html=True)
                
                if file_responsables is not None:
                    resp_info = map_resp_master.get(master_cod_sel, "SIN RESPONSABLE ASIGNADO")
                    st.markdown(f"<div class='responsable-box'>👤 <b>Responsable Interno de Control:</b> {resp_info}</div>", unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Cargue el archivo de Responsables en la barra lateral para ver quién controla a este Master.")

                df_org_asociados = df_rel_master_org[df_rel_master_org['Master_Codigo'] == master_cod_sel].copy()
                df_org_asociados['Nombre Organizador'] = df_org_asociados['Org_Codigo'].apply(buscar_nombre_organizador)
                
                with st.expander("🤝 Ver Organizadores Agrupados bajo esta Estructura Master", expanded=False):
                    st.dataframe(df_org_asociados[['Org_Codigo', 'Nombre Organizador']].rename(columns={'Org_Codigo':'Código Organizador Agrupado', 'Nombre Organizador':'Nombre del Organizador'}), use_container_width=True, hide_index=True)

                sub_tab_expedientes_m, sub_tab_vigentes_m = st.tabs(["📋 Historial de Expedientes", "🚗 Detalle de Pólizas Vigentes"])
                
                with sub_tab_expedientes_m:
                    df_m_temp_master = df_m_raw.copy()
                    df_m_temp_master[11] = df_m_temp_master[11].apply(normalizar_codigo)
                    df_m_temp_master['Master_Codigo'] = df_m_temp_master[11].map(map_prod_master).fillna("SIN MASTER")
                    df_det_master_m = df_m_temp_master[df_m_temp_master['Master_Codigo'] == master_cod_sel].iloc[:, [2, 3, 4, 5]].copy()
                    df_det_master_m.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                    df_det_master_m['TIPO'] = 'M'
                    
                    siniestros_m_master_str = df_det_master_m['SINIESTRO'].fillna("").astype(str).str.strip()
                    m_auto_m = df_det_master_m[siniestros_m_master_str.str.startswith("03/")].shape[0]
                    m_moto_m = df_det_master_m[~siniestros_m_master_str.str.startswith("03/")].shape[0]

                    df_j_temp_master = df_j_raw.copy()
                    df_j_temp_master[14] = df_j_temp_master[14].apply(normalizar_codigo)
                    df_j_temp_master['Master_Codigo'] = df_j_temp_master[14].map(map_prod_master).fillna("SIN MASTER")
                    df_det_master_j = df_j_temp_master[df_j_temp_master['Master_Codigo'] == master_cod_sel].iloc[:, [2, 3, 5, 6]].copy()
                    df_det_master_j.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                    df_det_master_j['TIPO'] = 'J'
                    
                    siniestros_j_master_str = df_det_master_j['SINIESTRO'].fillna("").astype(str).str.strip()
                    j_auto_m = df_det_master_j[siniestros_j_master_str.str.startswith("03/")].shape[0]
                    j_moto_m = df_det_master_j[~siniestros_j_master_str.str.startswith("03/")].shape[0]

                    cm1, cm2, cm3, cm4 = st.columns(4)
                    cm1.metric(label="🚗 Mediaciones Automotor (03/)", value=m_auto_m)
                    cm2.metric(label="🏍️ Mediaciones Motovehículo", value=m_moto_m)
                    cm3.metric(label="🚗 Juicios Automotor (03/)", value=j_auto_m)
                    cm4.metric(label="🏍️ Juicios Motovehículo", value=j_moto_m)
                    
                    df_detalle_master_final = pd.concat([df_det_master_m, df_det_master_j], ignore_index=True)
                    st.dataframe(df_detalle_master_final, use_container_width=True, hide_index=True)
                
                with sub_tab_vigentes_m:
                    st.markdown("#### 🔍 Resumen Cuantitativo de Pólizas Activas del Master")
                    df_v_filtrado_master = df_v_limpio[df_v_limpio['Master_Codigo'] == master_cod_sel]
                    ramos_series_m = df_v_filtrado_master['Ramo'].fillna("").astype(str).str.strip()
                    v_auto_m = df_v_filtrado_master[ramos_series_m == "3"].shape[0]
                    v_moto_m = df_v_filtrado_master[ramos_series_m == "4"].shape[0]
                    v_otros_m = df_v_filtrado_master[~ramos_series_m.isin(["3", "4"])].shape[0]
                    
                    cvm1, cvm2, cvm3 = st.columns(3)
                    cvm1.metric(label="🚗 Vigentes Automotores (Ramo 3)", value=v_auto_m)
                    cvm2.metric(label="🏍️ Vigentes Motovehículos (Ramo 4)", value=v_moto_m)
                    cvm3.metric(label="📊 Vigentes Otros Ramos", value=v_otros_m)
            else:
                st.info("💡 Consejo: Haga clic en cualquier fila de Master para auditar el volumen integrado de su estructura.")

            st.markdown("<h3 class='section-header'>📊 Top 25 Masters con Mayor Volumen de Casos</h3>", unsafe_allow_html=True)
            df_top25_master = df_consolidado_master.sort_values(by='Total General', ascending=False).head(25).copy()
            if not df_top25_master.empty:
                df_top25_master['Master Identificador'] = "[" + df_top25_master['Código'] + "] " + df_top25_master['Nombre Master']
                df_chart_master = df_top25_master.melt(id_vars=['Master Identificador'], value_vars=['Mediaciones', 'Juicios'], var_name='Tipo Expediente', value_name='Cantidad')
                fig_master = px.bar(
                    df_chart_master, x='Master Identificador', y='Cantidad', color='Tipo Expediente',
                    color_discrete_map={'Mediaciones': '#DCA7B8', 'Juicios': '#8B1D41'}, barmode='stack',
                    labels={'Cantidad': 'Cantidad de Casos', 'Master Identificador': 'Master'}
                )
                fig_master.update_layout(xaxis={'categoryorder':'total descending'}, margin=dict(l=20, r=20, t=10, b=40))
                st.plotly_chart(fig_master, use_container_width=True)

        # =========================================================================
        # --- SOLAPA 6: COINCIDENCIAS ---
        # =========================================================================
        with tabs[5]:
            st.markdown("<h3 class='section-header'>🔍 Cruce y Coincidencias (Productor + Abogado)</h3>", unsafe_allow_html=True)
            
            df_m_coinc = df_m_raw[[11, 10]].copy()
            df_m_coinc.columns = ['Código Productor', 'Abogado']
            df_m_coinc['Código Productor'] = df_m_coinc['Código Productor'].apply(normalizar_codigo)
            df_m_coinc['Abogado'] = df_m_coinc['Abogado'].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
            df_g_m = df_m_coinc.groupby(['Código Productor', 'Abogado']).size().reset_index(name='Mediaciones')

            df_j_coinc = df_j_raw[[14, 13]].copy()
            df_j_coinc.columns = ['Código Productor', 'Abogado']
            df_j_coinc['Código Productor'] = df_j_coinc['Código Productor'].apply(normalizar_codigo)
            df_j_coinc['Abogado'] = df_j_coinc['Abogado'].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
            df_g_j = df_j_coinc.groupby(['Código Productor', 'Abogado']).size().reset_index(name='Juicios')

            df_coinc_total = pd.merge(df_g_m, df_g_j, on=['Código Productor', 'Abogado'], how='outer').fillna(0)
            df_coinc_total['Mediaciones'] = df_coinc_total['Mediaciones'].astype(int)
            df_coinc_total['Juicios'] = df_coinc_total['Juicios'].astype(int)
            df_coinc_total['Total Coincidencias'] = df_coinc_total['Mediaciones'] + df_coinc_total['Juicios']
            
            df_coinc_total['Nombre Productor'] = df_coinc_total['Código Productor'].apply(buscar_nombre_productor)
            df_coinc_total = df_coinc_total[['Código Productor', 'Nombre Productor', 'Abogado', 'Mediaciones', 'Juicios', 'Total Coincidencias']]
            
            titulos_filtro = ['CÓDIGO', 'CODIGO', 'PRODUCTOR', 'ABOGADO', 'PROFESIONAL', 'SIN CÓDIGO', 'SIN ASIGNAR', 'DESCONOCIDO']
            df_coinc_total = df_coinc_total[~df_coinc_total['Código Productor'].isin(titulos_filtro)]
            df_coinc_total = df_coinc_total[~df_coinc_total['Abogado'].isin(titulos_filtro)]
            df_coinc_total = df_coinc_total.sort_values(by='Total Coincidencias', ascending=False).reset_index(drop=True)
            
            busqueda_c = st.text_input("🔍 Buscador de Coincidencias:", placeholder="Busque por Código, Productor o Abogado...", key="input_coinc")
            if busqueda_c:
                bc_upper = busqueda_c.strip().upper()
                df_mostrar_coinc = df_coinc_total[df_coinc_total['Código Productor'].str.contains(bc_upper, na=False) | df_coinc_total['Nombre Productor'].str.contains(bc_upper, na=False) | df_coinc_total['Abogado'].str.contains(bc_upper, na=False)]
            else:
                df_mostrar_coinc = df_coinc_total
                
            st.write("Seleccione una fila para desplegar la cartera compartida abajo:")
            evento_seleccion_coinc = st.dataframe(df_mostrar_coinc, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="tabla_coincidencias")
            
            filas_seleccionadas_coinc = evento_seleccion_coinc.get("selection", {}).get("rows", [])
            if filas_seleccionadas_coinc:
                indice_f = filas_seleccionadas_coinc[0]
                cod_c_sel = df_mostrar_coinc.iloc[indice_f]['Código Productor']
                nom_p_sel = df_mostrar_coinc.iloc[indice_f]['Nombre Productor']
                abog_c_sel = df_mostrar_coinc.iloc[indice_f]['Abogado']
                
                st.markdown(f"<h3 class='section-header'>📂 Expedientes en Coincidencia: [{cod_c_sel}] {nom_p_sel} 🤝 {abog_c_sel}</h3>", unsafe_allow_html=True)
                
                df_m_temp_c = df_m_raw.copy()
                df_m_temp_c[11] = df_m_temp_c[11].apply(normalizar_codigo)
                df_m_temp_c[10] = df_m_temp_c[10].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
                mask_c_m = (df_m_temp_c[11] == cod_c_sel) & (df_m_temp_c[10] == abog_c_sel)
                df_det_c_m = df_m_temp_c[mask_c_m].iloc[:, [2, 3, 4, 5]].copy()
                df_det_c_m.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                df_det_c_m['TIPO'] = 'M'
                
                df_j_temp_c = df_j_raw.copy()
                df_j_temp_c[14] = df_j_temp_c[14].apply(normalizar_codigo)
                df_j_temp_c[13] = df_j_temp_c[13].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
                mask_c_j = (df_j_temp_c[14] == cod_c_sel) & (df_j_temp_c[13] == abog_c_sel)
                df_det_c_j = df_j_temp_c[mask_c_j].iloc[:, [2, 3, 5, 6]].copy()
                df_det_c_j.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                df_det_c_j['TIPO'] = 'J'
                
                df_detalle_coinc_final = pd.concat([df_det_c_m, df_det_c_j], ignore_index=True)
                st.dataframe(df_detalle_coinc_final, use_container_width=True, hide_index=True)

    except IndexError:
        st.error("Error de formato: Verifique que Mediaciones llegue a col M, Juicios a col P y VIGENTES contenga Ramo en col A, Productor en col B, Organizador en col D/E y MASTER en col F/G.")
    except Exception as e:
        st.error(f"Ocurrió un error inesperado al procesar los archivos: {e}")

else:
    st.info("👋 Bienvenido, mdondo. Por favor, cargue los tres archivos base (Mediaciones, Juicios y VIGENTES) en el panel lateral para iniciar el análisis.")
