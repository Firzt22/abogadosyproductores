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
    .main-title {
        color: #8B1D41;
        font-family: 'Segoe UI', sans-serif;
        font-weight: bold;
        text-align: center;
        margin-bottom: 25px;
    }
    .section-header {
        color: #8B1D41;
        font-family: 'Segoe UI', sans-serif;
        font-weight: bold;
        margin-top: 20px;
        border-bottom: 2px solid #8B1D41;
        padding-bottom: 5px;
    }
    .css-1r6g72q {
        background-color: #fcf8f9;
        border-left: 5px solid #8B1D41;
    }
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
if os.path.exists("atmlogo.png.png"):
    st.sidebar.image("atmlogo.png.png", use_container_width=True)
elif os.path.exists("atmlogo.png"):
    st.sidebar.image("atmlogo.png", use_container_width=True)
else:
    st.sidebar.markdown("<h2 style='color: #8B1D41; font-weight: bold; text-align: center;'>ATM SEGUROS</h2>", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>🏛️ Panel de Gestión - Mediaciones & Juicios</h1>", unsafe_allow_html=True)

st.sidebar.markdown("### 📁 Carga de Información")
file_mediaciones = st.sidebar.file_uploader("Seleccione el archivo de Mediaciones", type=["xlsx", "csv"], key="uploader_m")
file_juicios = st.sidebar.file_uploader("Seleccione el archivo de Juicios", type=["xlsx", "csv"], key="uploader_j")
file_vigentes = st.sidebar.file_uploader("Seleccione el archivo de VIGENTES", type=["xlsx", "csv"], key="uploader_v")
file_responsables = st.sidebar.file_uploader("Seleccione el archivo de RESPONSABLES", type=["xlsx", "csv"], key="uploader_r")

if file_mediaciones is not None and file_juicios is not None and file_vigentes is not None:
    
    def leer_archivo(file_obj):
        if file_obj.name.endswith('.csv'):
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

    try:
        df_m_raw = leer_archivo(file_mediaciones)
        df_j_raw = leer_archivo(file_juicios)
        df_v_raw = leer_archivo(file_vigentes)
        
        # -------------------------------------------------------------------------
        # PROCESAMIENTO DEL EXCEL DE RESPONSABLES DE CONTROL
        # -------------------------------------------------------------------------
        map_resp_prod = {}
        map_resp_org = {}
        map_resp_master = {}
        df_r_base = pd.DataFrame() # Para la nueva solapa analítica
        
        if file_responsables is not None:
            df_r_raw = leer_archivo(file_responsables).copy()
            
            # Normalizaciones básicas sobre las columnas del archivo de Responsables
            for col_idx in [0, 2, 4, 6]:
                df_r_raw[col_idx] = df_r_raw[col_idx].apply(normalizar_codigo)
            for col_idx in [1, 3, 5, 7]:
                df_r_raw[col_idx] = df_r_raw[col_idx].fillna("").astype(str).str.strip().str.upper()
                
            df_r_base = df_r_raw.copy()

            # Mapeos clásicos para inyectar en las solapas individuales
            df_r_prod = df_r_raw[[0, 1, 6, 7]].dropna(subset=[0]).copy()
            df_r_prod['Resp_String'] = df_r_prod.apply(lambda r: f"[{r[6]}] {r[7]}" if r[6] != "SIN CÓDIGO" else "SIN RESPONSABLE ASIGNADO", axis=1)
            map_resp_prod = df_r_prod.groupby(0)['Resp_String'].apply(lambda x: " / ".join(x.unique())).to_dict()
            
            df_r_org = df_r_raw[[2, 3, 6, 7]].dropna(subset=[2]).copy()
            df_r_org['Resp_String'] = df_r_org.apply(lambda r: f"[{r[6]}] {r[7]}" if r[6] != "SIN CÓDIGO" else "SIN RESPONSABLE ASIGNADO", axis=1)
            map_resp_org = df_r_org.groupby(2)['Resp_String'].apply(lambda x: " / ".join(x.unique())).to_dict()
            
            df_r_master = df_r_raw[[4, 5, 6, 7]].dropna(subset=[4]).copy()
            df_r_master['Resp_String'] = df_r_master.apply(lambda r: f"[{r[6]}] {r[7]}" if r[6] != "SIN CÓDIGO" and r[7] != "" else ("SIN RESPONSABLE ASIGNADO" if r[6] == "SIN CÓDIGO" else f"[{r[6]}] SIN NOMBRE"), axis=1)
            map_resp_master = df_r_master.groupby(4)['Resp_String'].apply(lambda x: "  //  ".join([resp for resp in x.unique() if resp != "SIN RESPONSABLE ASIGNADO"]) if len(x.unique()) > 1 else x.unique()[0]).to_dict()

        # -------------------------------------------------------------------------
        # PROCESAMIENTO Y CRUCES BASADOS EN EL EXCEL DE VIGENTES
        # -------------------------------------------------------------------------
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
        
        map_org_nombres = df_v_limpio[df_v_limpio['Org_Nombre'] != "SIN ASIGNAR"].drop_duplicates(subset=['Org_Codigo']).set_index('Org_Codigo')['Org_Nombre'].to_dict()
        map_master_nombres = df_v_limpio[df_v_limpio['Master_Nombre'] != "SIN ASIGNAR"].drop_duplicates(subset=['Master_Codigo']).set_index('Master_Codigo')['Master_Nombre'].to_dict()
        
        def buscar_nombre_organizador(cod): return map_org_nombres.get(str(cod).strip().upper(), "SIN ASIGNAR")
        def buscar_nombre_master(cod): return map_master_nombres.get(str(cod).strip().upper(), "SIN ASIGNAR")

        # Conteos brutos de pólizas vigentes por productor, organizador y master
        conteo_vigentes_prod = df_v_limpio['Prod_Codigo'].value_counts().reset_index()
        conteo_vigentes_prod.columns = ['Código', 'Vigentes']

        v_totales_org = df_v_limpio[~df_v_limpio['Org_Codigo'].isin(['CÓDIGO', 'CODIGO', 'ORGANIZADOR', 'SIN CÓDIGO'])]['Org_Codigo'].value_counts().to_dict()
        v_totales_master = df_v_limpio[~df_v_limpio['Master_Codigo'].isin(['CÓDIGO', 'CODIGO', 'MASTER', 'SIN CÓDIGO'])]['Master_Codigo'].value_counts().to_dict()

        df_rel_org_prod = df_v_limpio[~df_v_limpio['Org_Codigo'].isin(['CÓDIGO', 'CODIGO', 'ORGANIZADOR', 'SIN CÓDIGO'])][['Org_Codigo', 'Prod_Codigo']].drop_duplicates()
        df_rel_master_org = df_v_limpio[~df_v_limpio['Master_Codigo'].isin(['CÓDIGO', 'CODIGO', 'MASTER', 'SIN CÓDIGO'])][['Master_Codigo', 'Org_Codigo']].drop_duplicates()

        # -------------------------------------------------------------------------
        # CREACIÓN DE MAPAS DE PRODUCTORES (Cód -> Nombre)
        # -------------------------------------------------------------------------
        df_m_p_map = df_m_raw[[11, 12]].copy()
        df_m_p_map[11] = df_m_p_map[11].apply(normalizar_codigo)
        df_m_p_map[12] = df_m_p_map[12].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
        map_m_prod = df_m_p_map[df_m_p_map[12] != "SIN ASIGNAR"].drop_duplicates(subset=[11]).set_index(11)[12].to_dict()

        df_j_p_map = df_j_raw[[14, 15]].copy()
        df_j_p_map[14] = df_j_p_map[14].apply(normalizar_codigo)
        df_j_p_map[15] = df_j_p_map[15].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
        map_j_prod = df_j_p_map[df_j_p_map[15] != "SIN ASIGNAR"].drop_duplicates(subset=[14]).set_index(14)[15].to_dict()

        def buscar_nombre_productor(cod):
            cod_str = str(cod).strip().upper()
            if cod_str in map_j_prod: return map_j_prod[cod_str]
            if cod_str in map_m_prod: return map_m_prod[cod_str]
            return "SIN ASIGNAR"

        # -------------------------------------------------------------------------
        # PRE-PROCESAMIENTO DE CASOS JUDICIALES Y MEDIACIONES
        # -------------------------------------------------------------------------
        df_m_prod_neto = df_m_raw[[11]].copy(); df_m_prod_neto.columns = ['Prod_Codigo']
        df_m_prod_neto['Prod_Codigo'] = df_m_prod_neto['Prod_Codigo'].apply(normalizar_codigo)
        df_m_prod_neto['Org_Codigo'] = df_m_prod_neto['Prod_Codigo'].map(map_prod_org).fillna("SIN ORGANIZADOR")
        df_m_prod_neto['Master_Codigo'] = df_m_prod_neto['Prod_Codigo'].map(map_prod_master).fillna("SIN MASTER")
        
        conteo_prod_m = df_m_prod_neto['Prod_Codigo'].value_counts().to_dict()
        conteo_org_m = df_m_prod_neto['Org_Codigo'].value_counts().to_dict()
        conteo_master_m = df_m_prod_neto['Master_Codigo'].value_counts().to_dict()

        df_j_prod_neto = df_j_raw[[14]].copy(); df_j_prod_neto.columns = ['Prod_Codigo']
        df_j_prod_neto['Prod_Codigo'] = df_j_prod_neto['Prod_Codigo'].apply(normalizar_codigo)
        df_j_prod_neto['Org_Codigo'] = df_j_prod_neto['Prod_Codigo'].map(map_prod_org).fillna("SIN ORGANIZADOR")
        df_j_prod_neto['Master_Codigo'] = df_j_prod_neto['Prod_Codigo'].map(map_prod_master).fillna("SIN MASTER")
        
        conteo_prod_j = df_j_prod_neto['Prod_Codigo'].value_counts().to_dict()
        conteo_org_j = df_j_prod_neto['Org_Codigo'].value_counts().to_dict()
        conteo_master_j = df_j_prod_neto['Master_Codigo'].value_counts().to_dict()

        # -------------------------------------------------------------------------
        # ESTRUCTURACIÓN DE LAS 6 SOLAPAS DEL TABLERO
        # -------------------------------------------------------------------------
        tabs = st.tabs(["⚖️ Abogados", "💼 Productor", "🏢 Organizador", "👑 Master", "🔍 Coincidencias", "👤 Gestión Responsables"])
        
        # --- SOLAPA 1: ABOGADOS ---
        with tabs[0]:
            st.markdown("<h3 class='section-header'>⚖️ Resumen de Carga por Profesional</h3>", unsafe_allow_html=True)
            col_k_abogado_m = df_m_raw.iloc[:, 10].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
            conteo_m_ab = col_k_abogado_m.value_counts().reset_index(); conteo_m_ab.columns = ['Abogado', 'Mediaciones']
            col_n_abogado_j = df_j_raw.iloc[:, 13].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
            conteo_j_ab = col_n_abogado_j.value_counts().reset_index(); conteo_j_ab.columns = ['Abogado', 'Juicios']
            
            df_consolidado_ab = pd.merge(conteo_m_ab, conteo_j_ab, on='Abogado', how='outer').fillna(0)
            df_consolidado_ab['Mediaciones'] = df_consolidado_ab['Mediaciones'].astype(int)
            df_consolidado_ab['Juicios'] = df_consolidado_ab['Juicios'].astype(int)
            df_consolidado_ab['Total General'] = df_consolidado_ab['Mediaciones'] + df_consolidado_ab['Juicios']
            df_consolidado_ab = df_consolidado_ab[~df_consolidado_ab['Abogado'].isin(['ABOGADO', 'PROFESIONAL', 'RESPONSABLE', 'SIN ASIGNAR', 'DESCONOCIDO'])]
            df_consolidado_ab = df_consolidado_ab.sort_values(by='Total General', ascending=False).reset_index(drop=True)
            
            busqueda_ab = st.text_input("🔍 Buscar abogado por nombre:", placeholder="Escriba el apellido...")
            df_mostrar_ab = df_consolidado_ab[df_consolidado_ab['Abogado'].str.contains(busqueda_ab.strip().upper(), na=False)].reset_index(drop=True) if busqueda_ab else df_consolidado_ab
            evento_seleccion_ab = st.dataframe(df_mostrar_ab, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="tabla_abogados")
            
            filas_seleccionadas_ab = evento_seleccion_ab.get("selection", {}).get("rows", [])
            if filas_seleccionadas_ab:
                abogado_seleccionado = df_mostrar_ab.iloc[filas_seleccionadas_ab[0]]['Abogado']
                st.markdown(f"<h3 class='section-header'>📂 Expedientes de: {abogado_seleccionado}</h3>", unsafe_allow_html=True)
                
                df_det_m = df_m_raw[df_m_raw.iloc[:, 10].fillna("").astype(str).str.strip().str.upper() == abogado_seleccionado].iloc[:, [2, 3, 4, 5]].copy()
                df_det_m.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']; df_det_m['TIPO'] = 'M'
                df_det_j = df_j_raw[df_j_raw.iloc[:, 13].fillna("").astype(str).str.strip().str.upper() == abogado_seleccionado].iloc[:, [2, 3, 5, 6]].copy()
                df_det_j.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']; df_det_j['TIPO'] = 'J'
                
                st.dataframe(pd.concat([df_det_m, df_det_j], ignore_index=True), use_container_width=True, hide_index=True)

        # --- SOLAPA 2: PRODUCTOR ---
        with tabs[1]:
            st.markdown("<h3 class='section-header'>💼 Resumen de Carga por Productor</h3>", unsafe_allow_html=True)
            df_p_m = pd.DataFrame(list(conteo_prod_m.items()), columns=['Código', 'Mediaciones'])
            df_p_j = pd.DataFrame(list(conteo_prod_j.items()), columns=['Código', 'Juicios'])
            df_consolidado_prod = pd.merge(df_p_m, df_p_j, on='Código', how='outer').fillna(0)
            df_consolidado_prod['Total General'] = df_consolidado_prod['Mediaciones'] + df_consolidado_prod['Juicios']
            df_consolidado_prod['Nombre Productor'] = df_consolidado_prod['Código'].apply(buscar_nombre_productor)
            df_consolidado_prod = pd.merge(df_consolidado_prod, conteo_vigentes_prod, on='Código', how='left').fillna({'Vigentes': 0})
            df_consolidado_prod['INCIDENCIA (%)'] = df_consolidado_prod.apply(lambda r: f"{round((r['Total General']/r['Vigentes'])*100,2)}%" if r['Vigentes'] > 0 else ("100.0%" if r['Total General'] > 0 else "0.0%"), axis=1)
            
            df_consolidado_prod = df_consolidado_prod[~df_consolidado_prod['Código'].isin(['CÓDIGO', 'CODIGO', 'PRODUCTOR', 'SIN CÓDIGO'])]
            df_consolidado_prod = df_consolidado_prod.sort_values(by='Total General', ascending=False).reset_index(drop=True)
            
            busqueda_prod = st.text_input("🔍 Buscar productor:", key="bus_p")
            df_filtrada_prod = df_consolidado_prod[df_consolidado_prod['Código'].str.contains(busqueda_prod.upper()) | df_consolidado_prod['Nombre Productor'].str.contains(busqueda_prod.upper())].reset_index(drop=True) if busqueda_prod else df_consolidado_prod
            evento_seleccion_prod = st.dataframe(df_filtrada_prod.drop(columns=['Total General']), use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="t_prod")
            
            if evento_seleccion_prod.get("selection", {}).get("rows", []):
                cod_sel = df_filtrada_prod.iloc[evento_seleccion_prod["selection"]["rows"][0]]['Código']
                if file_responsables is not None:
                    st.markdown(f"<div class='responsable-box'>👤 <b>Responsable:</b> {map_resp_prod.get(cod_sel, 'SIN ASIGNAR')}</div>", unsafe_allow_html=True)

        # --- SOLAPA 3: ORGANIZADOR ---
        with tabs[2]:
            st.markdown("<h3 class='section-header'>🏢 Resumen de Carga por Estructura Organizadora</h3>", unsafe_allow_html=True)
            df_o_m = pd.DataFrame(list(conteo_org_m.items()), columns=['Código', 'Mediaciones'])
            df_o_j = pd.DataFrame(list(conteo_org_j.items()), columns=['Código', 'Juicios'])
            df_consolidado_org = pd.merge(df_o_m, df_o_j, on='Código', how='outer').fillna(0)
            df_consolidado_org['Total General'] = df_consolidado_org['Mediaciones'] + df_consolidado_org['Juicios']
            df_consolidado_org['Nombre Organizador'] = df_consolidado_org['Código'].apply(buscar_nombre_organizador)
            df_consolidado_org['Vigentes'] = df_consolidado_org['Código'].map(v_totales_org).fillna(0)
            
            df_consolidado_org = df_consolidado_org[~df_consolidado_org['Código'].isin(['CÓDIGO', 'CODIGO', 'SIN ORGANIZADOR', 'SIN CÓDIGO'])]
            df_consolidado_org = df_consolidado_org.sort_values(by='Total General', ascending=False).reset_index(drop=True)
            evento_seleccion_org = st.dataframe(df_consolidado_org, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="t_org")
            
            if evento_seleccion_org.get("selection", {}).get("rows", []):
                cod_sel_o = df_consolidado_org.iloc[evento_seleccion_org["selection"]["rows"][0]]['Código']
                if file_responsables is not None:
                    st.markdown(f"<div class='responsable-box'>👤 <b>Responsable:</b> {map_resp_org.get(cod_sel_o, 'SIN ASIGNAR')}</div>", unsafe_allow_html=True)

        # --- SOLAPA 4: MASTER ---
        with tabs[3]:
            st.markdown("<h3 class='section-header'>👑 Resumen de Carga por Estructura MASTER</h3>", unsafe_allow_html=True)
            df_ma_m = pd.DataFrame(list(conteo_master_m.items()), columns=['Código', 'Mediaciones'])
            df_ma_j = pd.DataFrame(list(conteo_master_j.items()), columns=['Código', 'Juicios'])
            df_consolidado_master = pd.merge(df_ma_m, df_ma_j, on='Código', how='outer').fillna(0)
            df_consolidado_master['Total General'] = df_consolidado_master['Mediaciones'] + df_consolidado_master['Juicios']
            df_consolidado_master['Nombre Master'] = df_consolidado_master['Código'].apply(buscar_nombre_master)
            df_consolidado_master['Vigentes'] = df_consolidado_master['Código'].map(v_totales_master).fillna(0)
            
            df_consolidado_master = df_consolidado_master[~df_consolidado_master['Código'].isin(['CÓDIGO', 'CODIGO', 'SIN MASTER', 'SIN CÓDIGO'])]
            df_consolidado_master = df_consolidado_master.sort_values(by='Total General', ascending=False).reset_index(drop=True)
            evento_seleccion_mas = st.dataframe(df_consolidado_master, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="t_master")
            
            if evento_seleccion_mas.get("selection", {}).get("rows", []):
                cod_sel_m = df_consolidado_master.iloc[evento_seleccion_mas["selection"]["rows"][0]]['Código']
                if file_responsables is not None:
                    st.markdown(f"<div class='responsable-box'>👤 <b>Responsables:</b> {map_resp_master.get(cod_sel_m, 'SIN ASIGNAR')}</div>", unsafe_allow_html=True)

        # --- SOLAPA 5: COINCIDENCIAS ---
        with tabs[4]:
            st.markdown("<h3 class='section-header'>📜 Cruce y Coincidencias (Productor + Abogado)</h3>", unsafe_allow_html=True)
            df_m_coinc = df_m_raw[[11, 10]].copy(); df_m_coinc.columns = ['Código Productor', 'Abogado']
            df_m_coinc['Código Productor'] = df_m_coinc['Código Productor'].apply(normalizar_codigo)
            df_m_coinc['Abogado'] = df_m_coinc['Abogado'].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
            df_g_m = df_m_coinc.groupby(['Código Productor', 'Abogado']).size().reset_index(name='Mediaciones')

            df_j_coinc = df_j_raw[[14, 13]].copy(); df_j_coinc.columns = ['Código Productor', 'Abogado']
            df_j_coinc['Código Productor'] = df_j_coinc['Código Productor'].apply(normalizar_codigo)
            df_j_coinc['Abogado'] = df_j_coinc['Abogado'].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
            df_g_j = df_j_coinc.groupby(['Código Productor', 'Abogado']).size().reset_index(name='Juicios')

            df_coinc_total = pd.merge(df_g_m, df_g_j, on=['Código Productor', 'Abogado'], how='outer').fillna(0)
            df_coinc_total['Total Coincidencias'] = df_coinc_total['Mediaciones'] + df_coinc_total['Juicios']
            df_coinc_total['Nombre Productor'] = df_coinc_total['Código Productor'].apply(buscar_nombre_productor)
            
            df_coinc_total = df_coinc_total[~df_coinc_total['Código Productor'].isin(['CÓDIGO', 'CODIGO', 'SIN CÓDIGO'])]
            df_coinc_total = df_coinc_total.sort_values(by='Total Coincidencias', ascending=False).reset_index(drop=True)
            st.dataframe(df_coinc_total[['Código Productor', 'Nombre Productor', 'Abogado', 'Mediaciones', 'Juicios', 'Total Coincidencias']], use_container_width=True, hide_index=True)


        # =========================================================================
        # --- NUEVA SOLAPA 6: GESTIÓN RESPONSABLES ---
        # =========================================================================
        with tabs[5]:
            st.markdown("<h3 class='section-header'>👤 Auditoría de Carga y Carteras por Responsable de Control</h3>", unsafe_allow_html=True)
            
            if file_responsables is None:
                st.info("💡 Para visualizar esta sección, por favor cargue el archivo de RESPONSABLES en la barra lateral.")
            else:
                # 1. Extraer los responsables únicos válidos (Col G y H)
                df_resp_list = df_r_base[[6, 7]].dropna(subset=[6]).copy()
                df_resp_list = df_resp_list[~df_resp_list[6].isin(['CÓDIGO', 'CODIGO', 'SIN CÓDIGO', ''])]
                df_resp_unicos = df_resp_list.drop_duplicates(subset=[6]).reset_index(drop=True)
                df_resp_unicos.columns = ['Resp_Codigo', 'Resp_Nombre']
                
                # Pre-procesar mapas de vigentes por ramo para acelerar el cruce
                df_v_3 = df_v_limpio[df_v_limpio['Ramo'] == "3"]
                df_v_4 = df_v_limpio[df_v_limpio['Ramo'] == "4"]
                
                v_prod_3 = df_v_3['Prod_Codigo'].value_counts().to_dict()
                v_prod_4 = df_v_4['Prod_Codigo'].value_counts().to_dict()
                v_prod_tot = df_v_limpio['Prod_Codigo'].value_counts().to_dict()
                
                filas_responsables_tabla = []
                
                # Calcular métricas consolidadas para cada Responsable
                for _, row_resp in df_resp_unicos.iterrows():
                    rcod = row_resp['Resp_Codigo']
                    rnom = row_resp['Resp_Nombre']
                    
                    # Encontrar todos los productores mapeados directamente a este responsable
                    prods_controlados = df_r_base[df_r_base[6] == rcod][0].unique()
                    prods_controlados = [p for p in prods_controlados if p != "SIN CÓDIGO"]
                    
                    # Calcular Vigentes de sus productores
                    v_auto = sum([v_prod_3.get(p, 0) for p in prods_controlados])
                    v_moto = sum([v_prod_4.get(p, 0) for p in prods_controlados])
                    v_total = sum([v_prod_tot.get(p, 0) for p in prods_controlados])
                    
                    # Calcular Litigiosidad (Mediaciones y Juicios) de sus productores
                    med_tot = sum([conteo_prod_m.get(p, 0) for p in prods_controlados])
                    jui_tot = sum([conteo_prod_j.get(p, 0) for p in prods_controlados])
                    exp_tot = med_tot + jui_tot
                    
                    filas_responsables_tabla.append({
                        'Código Resp.': rcod,
                        'Responsable de Control': rnom,
                        'Vigentes Auto': v_auto,
                        'Vigentes Moto': v_moto,
                        'Total Vigentes': v_total,
                        'Mediaciones': med_tot,
                        'Juicios': jui_tot,
                        'Total Expedientes': exp_tot
                    })
                    
                df_tabla_responsables = pd.DataFrame(filas_responsables_tabla)
                df_tabla_responsables = df_tabla_responsables.sort_values(by='Total Expedientes', ascending=False).reset_index(drop=True)
                
                st.write("Seleccione un responsable para desglosar detalladamente la estructura comercial bajo su supervisión:")
                evt_resp = st.dataframe(df_tabla_responsables, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="t_resp_auditoria")
                
                # Desglose de carteras controladas al seleccionar una fila
                if evt_resp.get("selection", {}).get("rows", []):
                    idx_r = evt_resp["selection"]["rows"][0]
                    resp_cod_sel = df_tabla_responsables.iloc[idx_r]['Código Resp.']
                    resp_nom_sel = df_tabla_responsables.iloc[idx_r]['Responsable de Control']
                    
                    st.markdown(f"<h3 class='section-header'>📋 Carteras Vinculadas a: {resp_nom_sel} ({resp_cod_sel})</h3>", unsafe_allow_html=True)
                    
                    # Filtrar el maestro de relaciones para este responsable
                    df_sub_r = df_r_base[df_r_base[6] == resp_cod_sel]
                    
                    sub_p, sub_o, sub_m = st.columns(3)
                    
                    with sub_p:
                        st.markdown("#### 💼 Productores Asignados")
                        p_cods = [c for c in df_sub_r[0].unique() if c != "SIN CÓDIGO"]
                        if p_cods:
                            df_p_vinc = pd.DataFrame({'Código Productor': p_cods})
                            df_p_vinc['Nombre Productor'] = df_p_vinc['Código Productor'].apply(buscar_nombre_productor)
                            df_p_vinc['Vigentes'] = df_p_vinc['Código Productor'].map(v_prod_tot).fillna(0).astype(int)
                            st.dataframe(df_p_vinc, use_container_width=True, hide_index=True)
                        else:
                            st.caption("No registra Productores directos.")
                            
                    with sub_o:
                        st.markdown("#### 🏢 Organizadores Asignados")
                        o_cods = [c for c in df_sub_r[2].unique() if c != "SIN CÓDIGO"]
                        if o_cods:
                            df_o_vinc = pd.DataFrame({'Código Org.': o_cods})
                            df_o_vinc['Nombre Organizador'] = df_o_vinc['Código Org.'].apply(buscar_nombre_organizador)
                            df_o_vinc['Vigentes'] = df_o_vinc['Código Org.'].map(v_totales_org).fillna(0).astype(int)
                            st.dataframe(df_o_vinc, use_container_width=True, hide_index=True)
                        else:
                            st.caption("No registra Organizadores directos.")
                            
                    with sub_m:
                        st.markdown("#### 👑 Masters Asignados")
                        m_cods = [c for c in df_sub_r[4].unique() if c != "SIN CÓDIGO"]
                        if m_cods:
                            df_m_vinc = pd.DataFrame({'Código Master': m_cods})
                            df_m_vinc['Nombre Master'] = df_m_vinc['Código Master'].apply(buscar_nombre_master)
                            df_m_vinc['Vigentes'] = df_m_vinc['Código Master'].map(v_totales_master).fillna(0).astype(int)
                            st.dataframe(df_m_vinc, use_container_width=True, hide_index=True)
                        else:
                            st.caption("No registra estructuras Master directas.")

    except IndexError:
        st.error("Error de formato detectado. Verifique la correcta estructura de columnas de los archivos cargados.")
    except Exception as e:
        st.error(f"Error general en el procesamiento: {e}")
else:
    st.info("👋 Bienvenido, mdondo. Por favor, cargue los archivos requeridos en el panel izquierdo para inicializar las herramientas de auditoría.")
