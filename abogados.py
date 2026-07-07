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

# Carga del logo de ATM en la barra lateral desde el Escritorio
ruta_escritorio_1 = os.path.expanduser(r"~\Desktop\atmlogo.png")
ruta_escritorio_2 = os.path.expanduser(r"~\Escritorio\atmlogo.png")

if os.path.exists(ruta_escritorio_1):
    st.sidebar.image(ruta_escritorio_1, use_container_width=True)
elif os.path.exists(ruta_escritorio_2):
    st.sidebar.image(ruta_escritorio_2, use_container_width=True)
else:
    st.sidebar.markdown("<h2 style='color: #8B1D41; font-weight: bold; text-align: center;'>ATM SEGUROS</h2>", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>🏛️ Panel de Gestión - Mediaciones & Juicios</h1>", unsafe_allow_html=True)

# Barra lateral para la carga de datos estructurada
st.sidebar.markdown("### 📁 Carga de Información")

file_mediaciones = st.sidebar.file_uploader("Seleccione el archivo de Mediaciones", type=["xlsx", "csv"], key="uploader_m")
file_juicios = st.sidebar.file_uploader("Seleccione el archivo de Juicios", type=["xlsx", "csv"], key="uploader_j")
file_vigentes = st.sidebar.file_uploader("Seleccione el archivo de VIGENTES", type=["xlsx", "csv"], key="uploader_v")

# Verificar que los tres archivos estén cargados para procesar
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
        # Carga de DataFrames puros
        df_m_raw = leer_archivo(file_mediaciones)
        df_j_raw = leer_archivo(file_juicios)
        df_v_raw = leer_archivo(file_vigentes)
        
        # -------------------------------------------------------------------------
        # PROCESAMIENTO DEL EXCEL DE VIGENTES (Columna B -> Índice 1)
        # -------------------------------------------------------------------------
        df_v_prod = df_v_raw[[1]].copy()
        df_v_prod.columns = ['Código']
        df_v_prod['Código'] = df_v_prod['Código'].apply(normalizar_codigo)
        
        # Contamos cuántas veces se repite cada código de productor en Vigentes de forma global
        conteo_vigentes = df_v_prod['Código'].value_counts().reset_index()
        conteo_vigentes.columns = ['Código', 'Vigentes']

        # Intento de rescatar nombres desde el maestro de Vigentes si tuviera columna de nombre (ej: Columna C si existiera)
        # Por ahora mapeamos de la misma forma estructurada de Juicios y Mediaciones
        # -------------------------------------------------------------------------
        # CREACIÓN DE MAPAS DE PRODUCTORES
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
        # SOLAPAS PRINCIPALES
        # -------------------------------------------------------------------------
        tabs = st.tabs(["⚖️ Abogados", "💼 Productor", "🔍 Coincidencias"])
        
        # =========================================================================
        # --- SOLAPA 1: ABOGADOS ---
        # =========================================================================
        with tabs[0]:
            st.markdown("<h3 class='section-header'>⚖️ Resumen de Carga por Profesional</h3>", unsafe_allow_html=True)
            
            col_k_abogado_m = df_m_raw.iloc[:, 10].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
            conteo_m = col_k_abogado_m.value_counts().reset_index()
            conteo_m.columns = ['Abogado', 'Mediaciones']
            
            col_n_abogado_j = df_j_raw.iloc[:, 13].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
            conteo_j = col_n_abogado_j.value_counts().reset_index()
            conteo_j.columns = ['Abogado', 'Juicios']
            
            df_consolidado_ab = pd.merge(conteo_m, conteo_j, on='Abogado', how='outer').fillna(0)
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
            
            # --- GRÁFICO TOP 25 ABOGADOS ---
            st.markdown("<h3 class='section-header'>📊 Top 25 Abogados con Mayor Volumen</h3>", unsafe_allow_html=True)
            df_top25_ab = df_consolidado_ab.head(25).copy()
            if not df_top25_ab.empty:
                df_chart_ab = df_top25_ab.melt(id_vars=['Abogado'], value_vars=['Mediaciones', 'Juicios'], var_name='Tipo Expediente', value_name='Cantidad')
                fig_ab = px.bar(
                    df_chart_ab, 
                    x='Abogado', 
                    y='Cantidad', 
                    color='Tipo Expediente',
                    color_discrete_map={'Mediaciones': '#DCA7B8', 'Juicios': '#8B1D41'},
                    barmode='stack',
                    labels={'Cantidad': 'Cantidad de Casos', 'Abogado': 'Profesional'}
                )
                fig_ab.update_layout(
                    xaxis={'categoryorder':'total descending'},
                    margin=dict(l=20, r=20, t=10, b=40),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_ab, use_container_width=True)

        # =========================================================================
        # --- SOLAPA 2: PRODUCTOR ---
        # =========================================================================
        with tabs[1]:
            st.markdown("<h3 class='section-header'>💼 Resumen de Carga por Productor</h3>", unsafe_allow_html=True)
            
            df_m_prod = df_m_raw[[11]].copy()
            df_m_prod.columns = ['Código']
            df_m_prod['Código'] = df_m_prod['Código'].apply(normalizar_codigo)
            conteo_prod_m = df_m_prod['Código'].value_counts().reset_index()
            conteo_prod_m.columns = ['Código', 'Mediaciones']
            
            df_j_prod = df_j_raw[[14]].copy()
            df_j_prod.columns = ['Código']
            df_j_prod['Código'] = df_j_prod['Código'].apply(normalizar_codigo)
            conteo_prod_j = df_j_prod['Código'].value_counts().reset_index()
            conteo_prod_j.columns = ['Código', 'Juicios']
            
            df_consolidado_prod = pd.merge(conteo_prod_m, conteo_prod_j, on='Código', how='outer').fillna(0)
            df_consolidado_prod['Mediaciones'] = df_consolidado_prod['Mediaciones'].astype(int)
            df_consolidado_prod['Juicios'] = df_consolidado_prod['Juicios'].astype(int)
            df_consolidado_prod['Total General'] = df_consolidado_prod['Mediaciones'] + df_consolidado_prod['Juicios']
            
            df_consolidado_prod['Nombre Productor'] = df_consolidado_prod['Código'].apply(buscar_nombre_productor)
            
            # Integración de la columna Vigentes
            df_consolidado_prod = pd.merge(df_consolidado_prod, conteo_vigentes, on='Código', how='left').fillna({'Vigentes': 0})
            df_consolidado_prod['Vigentes'] = df_consolidado_prod['Vigentes'].astype(int)
            
            # Cálculo de incidencia ((JUICIOS + MEDIACIONES) / VIGENTES)
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
            
            # Ordenamiento mandatorio por Incidencia (mayor a menor)
            df_consolidado_prod = df_consolidado_prod.sort_values(by='INCIDENCIA', ascending=False).reset_index(drop=True)
            df_mostrar_tabla_p = df_consolidado_prod.drop(columns=['INCIDENCIA'])

            busqueda_prod = st.text_input("🔍 Buscar productor (por Código o por Nombre):", placeholder="Escriba el código numérico o el nombre del productor...", key="input_bus_prod")
            if busqueda_prod:
                b_upper = busqueda_prod.strip().upper()
                condicion = df_mostrar_tabla_p['Código'].str.contains(b_upper, na=False) | df_mostrar_tabla_p['Nombre Productor'].str.contains(b_upper, na=False)
                df_filtrada_prod = df_mostrar_tabla_p[condicion].reset_index(drop=True)
            else:
                df_filtrada_prod = df_mostrar_tabla_p

            st.write("Seleccione un productor de la lista para desplegar el análisis analítico y comercial abajo:")
            evento_seleccion_prod = st.dataframe(df_filtrada_prod, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="tabla_productores")
            
            filas_seleccionadas_prod = evento_seleccion_prod.get("selection", {}).get("rows", [])
            if filas_seleccionadas_prod:
                indice_fila_prod = filas_seleccionadas_prod[0]
                cod_seleccionado = df_filtrada_prod.iloc[indice_fila_prod]['Código']
                nom_seleccionado = df_filtrada_prod.iloc[indice_fila_prod]['Nombre Productor']
                
                st.markdown(f"<h3 class='section-header'>📂 Análisis de Cartera Comercial: [{cod_seleccionado}] - {nom_seleccionado}</h3>", unsafe_allow_html=True)
                
                sub_tab_expedientes, sub_tab_vigentes = st.tabs(["📋 Historial de Expedientes", "🚗 Detalle de Pólizas Vigentes"])
                
                # --- SUB-SOLAPA A: EXPEDIENTES ---
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
                
                # --- SUB-SOLAPA B: VIGENTES (SÓLO MÉTRICAS - REMOVIDA TABLA DE DETALLE) ---
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
                    
                    if df_v_filtrado_prod.empty:
                        st.warning("⚠️ No se encontraron registros de pólizas activas para este código en el archivo de VIGENTES subido.")
            else:
                st.info("💡 Consejo: Haga clic en cualquier celda o fila de la tabla superior para inspeccionar el desglose de juicios, mediaciones y pólizas vigentes.")
            
            # --- GRÁFICO TOP 25 PRODUCTORES ---
            st.markdown("<h3 class='section-header'>📊 Top 25 Productores con Mayor Volumen</h3>", unsafe_allow_html=True)
            df_top25_prod = df_consolidado_prod.head(25).copy()
            if not df_top25_prod.empty:
                df_top25_prod['Productor Identificador'] = "[" + df_top25_prod['Código'] + "] " + df_top25_prod['Nombre Productor']
                df_chart_prod = df_top25_prod.melt(id_vars=['Productor Identificador'], value_vars=['Mediaciones', 'Juicios'], var_name='Tipo Expediente', value_name='Cantidad')
                fig_prod = px.bar(
                    df_chart_prod, 
                    x='Productor Identificador', 
                    y='Cantidad', 
                    color='Tipo Expediente',
                    color_discrete_map={'Mediaciones': '#DCA7B8', 'Juicios': '#8B1D41'},
                    barmode='stack',
                    labels={'Cantidad': 'Cantidad de Casos', 'Productor Identificador': 'Productor (Código y Nombre)'}
                )
                fig_prod.update_layout(
                    xaxis={'categoryorder':'total descending'},
                    margin=dict(l=20, r=20, t=10, b=40),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_prod, use_container_width=True)

        # =========================================================================
        # --- SOLAPA 3: COINCIDENCIAS ---
        # =========================================================================
        with tabs[2]:
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
            
            # Limpieza robusta incluyendo 'DESCONOCIDO'
            titulos_filtro = ['CÓDIGO', 'CODIGO', 'PRODUCTOR', 'ABOGADO', 'PROFESIONAL', 'SIN CÓDIGO', 'SIN ASIGNAR', 'DESCONOCIDO']
            df_coinc_total = df_coinc_total[~df_coinc_total['Código Productor'].isin(titulos_filtro)]
            df_coinc_total = df_coinc_total[~df_coinc_total['Abogado'].isin(titulos_filtro)]
            df_coinc_total = df_coinc_total.sort_values(by='Total Coincidencias', ascending=False).reset_index(drop=True)
            
            busqueda_c = st.text_input("🔍 Buscador de Coincidencias:", placeholder="Busque por Código, Nombre de Productor o Nombre de Abogado...", key="input_coinc")
            
            if busqueda_c:
                bc_upper = busqueda_c.strip().upper()
                condicion_c = (
                    df_coinc_total['Código Productor'].str.contains(bc_upper, na=False) |
                    df_coinc_total['Nombre Productor'].str.contains(bc_upper, na=False) |
                    df_coinc_total['Abogado'].str.contains(bc_upper, na=False)
                )
                df_mostrar_coinc = df_coinc_total[condicion_c].reset_index(drop=True)
            else:
                df_mostrar_coinc = df_coinc_total
                
            st.write("Seleccione una fila para desplegar la cartera de expedientes compartida abajo:")
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
            else:
                st.info("💡 Consejo: Haga clic en cualquier fila de la tabla de coincidencias para inspeccionar las carpetas judiciales específicas.")

    except IndexError:
        st.error("Error de formato: Verifique que Mediaciones llegue a col M, Juicios a col P y VIGENTES contenga el Ramo en col A y el Productor en col B.")
    except Exception as e:
        st.error(f"Ocurrió un error inesperado al procesar los archivos: {e}")

else:
    st.info("👋 Bienvenido, mdondo. Por favor, cargue los tres archivos (Mediaciones, Juicios y VIGENTES) en el panel lateral para iniciar el análisis.")
