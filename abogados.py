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
    /* Sutil decoración para las tarjetas informativas y responsables */
    .css-1r6g72q, .responsable-card {
        background-color: #fcf8f9;
        border-left: 5px solid #8B1D41;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 15px;
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

file_mediaciones = st.sidebar.file_uploader("1. Archivo de Mediaciones", type=["xlsx", "csv"], key="uploader_m")
file_juicios = st.sidebar.file_uploader("2. Archivo de Juicios", type=["xlsx", "csv"], key="uploader_j")
file_vigentes = st.sidebar.file_uploader("3. Archivo de VIGENTES", type=["xlsx", "csv"], key="uploader_v")
file_responsables = st.sidebar.file_uploader("4. Excel de Responsables Internos", type=["xlsx", "csv"], key="uploader_r")

# Verificar que los cuatro archivos estén cargados para procesar
if file_mediaciones is not None and file_juicios is not None and file_vigentes is not None and file_responsables is not None:
    
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
        # Carga de DataFrames puros
        df_m_raw = leer_archivo(file_mediaciones)
        df_j_raw = leer_archivo(file_juicios)
        df_v_raw = leer_archivo(file_vigentes)
        df_r_raw = leer_archivo(file_responsables)
        
        # -------------------------------------------------------------------------
        # PROCESAMIENTO DEL EXCEL DE RESPONSABLES INTERNOS
        # Col A(0): Cód Prod, Col C(2): Cód Org, Col E(4): Cód Master, Col G(6): Cód Resp, Col H(7): Nom Resp
        # -------------------------------------------------------------------------
        map_resp_prod = {}
        map_resp_org = {}
        map_resp_master = {}
        
        # Empezamos desde la fila 0 evaluando que no sea el encabezado en texto literal
        for idx, row in df_r_raw.iterrows():
            cod_resp = str(row[6]).strip() if pd.notna(row[6]) else ""
            nom_resp = str(row[7]).strip().upper() if pd.notna(row[7]) else ""
            
            if cod_resp and nom_resp and "RESPONSABLE" not in cod_resp:
                txt_responsable = f"[{cod_resp}] {nom_resp}"
                
                # Mapeo por Productor (Col A / Index 0)
                if pd.notna(row[0]):
                    c_prod = normalizar_codigo(row[0])
                    if c_prod not in ["CÓDIGO", "CODIGO", "SIN CÓDIGO"]:
                        map_resp_prod[c_prod] = txt_responsable
                        
                # Mapeo por Organizador (Col C / Index 2)
                if pd.notna(row[2]):
                    c_org = normalizar_codigo(row[2])
                    if c_org not in ["CÓDIGO", "CODIGO", "SIN CÓDIGO"]:
                        map_resp_org[c_org] = txt_responsable
                        
                # Mapeo por Master (Col E / Index 4)
                if pd.notna(row[4]):
                    c_master = normalizar_codigo(row[4])
                    if c_master not in ["CÓDIGO", "CODIGO", "SIN CÓDIGO"]:
                        map_resp_master[c_master] = txt_responsable

        # -------------------------------------------------------------------------
        # PROCESAMIENTO Y CRUCES BASADOS EN EL EXCEL DE VIGENTES
        # Col A(0):Ramo, Col B(1):Cód Prod, Col D(3):Cód Org, Col E(4):Nom Org, Col F(5):Cód Master, Col G(6):Nom Master
        # -------------------------------------------------------------------------
        df_v_limpio = df_v_raw[[0, 1, 3, 4, 5, 6]].copy()
        df_v_limpio.columns = ['Ramo', 'Prod_Codigo', 'Org_Codigo', 'Org_Nombre', 'Master_Codigo', 'Master_Nombre']
        
        df_v_limpio['Ramo'] = df_v_limpio['Ramo'].fillna("").astype(str).str.strip()
        df_v_limpio['Prod_Codigo'] = df_v_limpio['Prod_Codigo'].apply(normalizar_codigo)
        df_v_limpio['Org_Codigo'] = df_v_limpio['Org_Codigo'].apply(normalizar_codigo)
        df_v_limpio['Org_Nombre'] = df_v_limpio['Org_Nombre'].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
        df_v_limpio['Master_Codigo'] = df_v_limpio['Master_Codigo'].apply(normalizar_codigo)
        df_v_limpio['Master_Nombre'] = df_v_limpio['Master_Nombre'].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
        
        # 1. Mapas únicos jerárquicos (Prod -> Org y Prod -> Master)
        df_map_prod_to_org = df_v_limpio[['Prod_Codigo', 'Org_Codigo']].drop_duplicates(subset=['Prod_Codigo'])
        map_prod_org = df_map_prod_to_org.set_index('Prod_Codigo')['Org_Codigo'].to_dict()
        
        df_map_prod_to_master = df_v_limpio[['Prod_Codigo', 'Master_Codigo']].drop_duplicates(subset=['Prod_Codigo'])
        map_prod_master = df_map_prod_to_master.set_index('Prod_Codigo')['Master_Codigo'].to_dict()
        
        # 2. Mapeos de códigos a nombres descriptivos
        df_map_org_name = df_v_limpio[['Org_Codigo', 'Org_Nombre']].drop_duplicates(subset=['Org_Codigo'])
        df_map_org_name = df_map_org_name[df_map_org_name['Org_Nombre'] != "SIN ASIGNAR"]
        map_org_nombres = df_map_org_name.set_index('Org_Codigo')['Org_Nombre'].to_dict()
        
        df_map_master_name = df_v_limpio[['Master_Codigo', 'Master_Nombre']].drop_duplicates(subset=['Master_Codigo'])
        df_map_master_name = df_map_master_name[df_map_master_name['Master_Nombre'] != "SIN ASIGNAR"]
        map_master_nombres = df_map_master_name.set_index('Master_Codigo')['Master_Nombre'].to_dict()
        
        def buscar_nombre_organizador(cod):
            return map_org_nombres.get(str(cod).strip().upper(), "SIN ASIGNAR")
            
        def buscar_nombre_master(cod):
            return map_master_nombres.get(str(cod).strip().upper(), "SIN ASIGNAR")

        # 3. Conteos globales de pólizas vigentes por nivel comercial
        conteo_vigentes_prod = df_v_limpio['Prod_Codigo'].value_counts().reset_index()
        conteo_vigentes_prod.columns = ['Código', 'Vigentes']

        df_v_filtrado_basura = df_v_limpio[~df_v_limpio['Org_Codigo'].isin(['CÓDIGO', 'CODIGO', 'ORGANIZADOR', 'SIN CÓDIGO'])]
        v_totales_org = df_v_filtrado_basura['Org_Codigo'].value_counts().to_dict()
        
        df_v_filtrado_basura_m = df_v_limpio[~df_v_limpio['Master_Codigo'].isin(['CÓDIGO', 'CODIGO', 'MASTER', 'SIN CÓDIGO'])]
        v_totales_master = df_v_filtrado_basura_m['Master_Codigo'].value_counts().to_dict()

        # 4. Relaciones de estructuras jerárquicas cruzadas para listados
        df_rel_org_prod = df_v_filtrado_basura[['Org_Codigo', 'Prod_Codigo']].drop_duplicates()
        df_rel_master_org = df_v_filtrado_basura_m[['Master_Codigo', 'Org_Codigo']].drop_duplicates()

        # -------------------------------------------------------------------------
        # CREACIÓN DE MAPAS DE PRODUCTORES (Cód -> Nombre)
        # -------------------------------------------------------------------------
        df_m_p_map = df_m_raw[[11, 12]].copy()
        df_m_p_map[11] = df_m_p_map[11].apply(normalizar_codigo)
        df_m_p_map[12] = df_m_p_map[12].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
        df_m_p_map = df_m_p_map[df_m_p_map[12] != "SIN ASIGNAR"]
        map_m_prod = df_m_p_map.drop_duplicates(subset=[11]).set_index(11)[12].to_dict()

        df_j_p_map = df_j_raw[[14, 15]].copy()
        df_j_p_map[14] = df_j_p_map[14].apply(normalizar_codigo)
        df_j_p_map[15] = df_j_p_map[15].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
        df_j_p_map = df_j_p_map[df_j_p_map[15] != "SIN ASIGNAR"]
        map_j_prod = df_j_p_map.drop_duplicates(subset=[14]).set_index(14)[15].to_dict()

        def buscar_nombre_productor(cod):
            cod_str = str(cod).strip().upper()
            if cod_str in map_j_prod: return map_j_prod[cod_str]
            if cod_str in map_m_prod: return map_m_prod[cod_str]
            return "SIN ASIGNAR"

        # -------------------------------------------------------------------------
        # PRE-PROCESAMIENTO DE CASOS POR PRODUCTOR Y TRASLADO HACIA ESTRUCTURAS SUPERIORES
        # -------------------------------------------------------------------------
        # Mediaciones
        df_m_prod_neto = df_m_raw[[11]].copy()
        df_m_prod_neto.columns = ['Prod_Codigo']
        df_m_prod_neto['Prod_Codigo'] = df_m_prod_neto['Prod_Codigo'].apply(normalizar_codigo)
        df_m_prod_neto['Org_Codigo'] = df_m_prod_neto['Prod_Codigo'].map(map_prod_org).fillna("SIN ORGANIZADOR")
        df_m_prod_neto['Master_Codigo'] = df_m_prod_neto['Prod_Codigo'].map(map_prod_master).fillna("SIN MASTER")
        
        conteo_prod_m = df_m_prod_neto['Prod_Codigo'].value_counts().reset_index(name='Mediaciones')
        conteo_prod_m.columns = ['Código', 'Mediaciones']
        conteo_org_m = df_m_prod_neto['Org_Codigo'].value_counts().reset_index(name='Mediaciones')
        conteo_org_m.columns = ['Org_Codigo', 'Mediaciones']
        conteo_master_m = df_m_prod_neto['Master_Codigo'].value_counts().reset_index(name='Mediaciones')
        conteo_master_m.columns = ['Master_Codigo', 'Mediaciones']

        # Juicios
        df_j_prod_neto = df_j_raw[[14]].copy()
        df_j_prod_neto.columns = ['Prod_Codigo']
        df_j_prod_neto['Prod_Codigo'] = df_j_prod_neto['Prod_Codigo'].apply(normalizar_codigo)
        df_j_prod_neto['Org_Codigo'] = df_j_prod_neto['Prod_Codigo'].map(map_prod_org).fillna("SIN ORGANIZADOR")
        df_j_prod_neto['Master_Codigo'] = df_j_prod_neto['Prod_Codigo'].map(map_prod_master).fillna("SIN MASTER")
        
        conteo_prod_j = df_j_prod_neto['Prod_Codigo'].value_counts().reset_index(name='Juicios')
        conteo_prod_j.columns = ['Código', 'Juicios']
        conteo_org_j = df_j_prod_neto['Org_Codigo'].value_counts().reset_index(name='Juicios')
        conteo_org_j.columns = ['Org_Codigo', 'Juicios']
        conteo_master_j = df_j_prod_neto['Master_Codigo'].value_counts().reset_index(name='Juicios')
        conteo_master_j.columns = ['Master_Codigo', 'Juicios']

        # -------------------------------------------------------------------------
        # SOLAPAS PRINCIPALES DEL TABLERO
        # -------------------------------------------------------------------------
        tabs = st.tabs(["⚖️ Abogados", "💼 Productor", "🏢 Organizador", "👑 Master", "🔍 Coincidencias"])
        
        # =========================================================================
        # --- SOLAPA 1: ABOGADOS ---
        # =========================================================================
        with tabs[0]:
            st.markdown("<h3 class='section-header'>⚖️ Resumen de Carga por Profesional</h3>", unsafe_allow_html=True)
            
            col_k_abogado_m = df_m_raw.iloc[:, 10].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
            conteo_m_ab = col_k_abogado_m.value_counts().reset_index()
            conteo_m_ab.columns = ['Abogado', 'Mediaciones']
            
            col_n_abogado_j = df_j_raw.iloc[:, 13].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
            conteo_j_ab = col_n_abogado_j.value_counts().reset_index()
            conteo_j_ab.columns = ['Abogado', 'Juicios']
            
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
        # --- SOLAPA 2: PRODUCTOR ---
        # =========================================================================
        with tabs[1]:
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
                
                # REQUISITO NUEVO: Mostrar responsable interno del productor seleccionado
                resp_prod_encontrado = map_resp_prod.get(cod_seleccionado, "🚫 NO ASIGNADO EN EXCEL DE RESPONSABLES")
                st.markdown(f"""
                <div class="responsable-card">
                    <span style="font-size: 1.15em;">👤 <b>Responsable Interno de Control:</b> {resp_prod_encontrado}</span>
                </div>
                """, unsafe_allow_html=True)
                
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
                    df_v_analisis = df_v_raw.copy()
                    df_v_analisis[1] = df_v_analisis[1].apply(normalizar_codigo)
                    df_v_filtrado_prod = df_v_analisis[df_v_analisis[1] == cod_seleccionado]
                    
                    ramos_series = df_v_filtrado_prod[0].fillna("").astype(str).str.strip()
                    v_auto = df_v_filtrado_prod[ramos_series == "3"].shape[0]
                    v_moto = df_v_filtrado_prod[ramos_series == "4"].shape[0]
                    v_otros = df_v_filtrado_prod[~ramos_series.isin(["3", "4"])].shape[0]
                    
                    cv1, cv2, cv3 = st.columns(3)
                    cv1.metric(label="🚗 Vigentes Automotores (Ramo 3)", value=v_auto)
                    cv2.metric(label="🏍️ Vigentes Motovehículos (Ramo 4)", value=v_moto)
                    cv3.metric(label="📊 Vigentes Otros Ramos", value=v_otros)

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
        # --- SOLAPA 3: ORGANIZADOR ---
        # =========================================================================
        with tabs[2]:
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
                
                # REQUISITO NUEVO: Mostrar responsable interno del organizador seleccionado
                resp_org_encontrado = map_resp_org.get(org_cod_sel, "🚫 NO ASIGNADO EN EXCEL DE RESPONSABLES")
                st.markdown(f"""
                <div class="responsable-card">
                    <span style="font-size: 1.15em;">👤 <b>Responsable Interno de Control:</b> {resp_org_encontrado}</span>
                </div>
                """, unsafe_allow_html=True)
                
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
        # --- SOLAPA 4: MASTER ---
        # =========================================================================
        with tabs[3]:
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
                
                # REQUISITO NUEVO: Mostrar responsable interno del Master seleccionado
                resp_master_encontrado = map_resp_master.get(master_cod_sel, "🚫 NO ASIGNADO EN EXCEL DE RESPONSABLES")
                st.markdown(f"""
                <div class="responsable-card">
                    <span style="font-size: 1.15em;">👤 <b>Responsable Interno de Control:</b> {resp_master_encontrado}</span>
                </div>
                """, unsafe_allow_html=True)
                
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
        # --- SOLAPA 5: COINCIDENCIAS ---
        # =========================================================================
        with tabs[4]:
            st.markdown("<h3 class='section-header'>📜 Cruce y Coincidencias (Productor + Abogado)</h3>", unsafe_allow_html=True)
            
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
        st.error("Error de formato: Verifique que Mediaciones llegue a col M, Juicios a col P, VIGENTES tenga Ramo en A/Prod en B/Org en D y E/Master en F y G; y Responsables mapee A(Prod), C(Org), E(Master) y G/H(Responsable).")
    except Exception as e:
        st.error(f"Ocurrió un error inesperado al procesar los archivos: {e}")

else:
    st.info("👋 Bienvenido, mdondo. Por favor, cargue los cuatro archivos requeridos (Mediaciones, Juicios, VIGENTES y el Maestro de Responsables Comerciales) en el panel izquierdo para iniciar el tablero corporativo.")
