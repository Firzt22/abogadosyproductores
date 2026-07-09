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

# Barra lateral para la carga de datos estructurada
st.sidebar.markdown("### 📁 Carga de Información")

file_mediaciones = st.sidebar.file_uploader("Seleccione el archivo de Mediaciones", type=["xlsx", "csv"], key="uploader_m")
file_juicios = st.sidebar.file_uploader("Seleccione el archivo de Juicios", type=["xlsx", "csv"], key="uploader_j")
file_vigentes = st.sidebar.file_uploader("Seleccione el archivo de VIGENTES", type=["xlsx", "csv"], key="uploader_v")
file_responsables = st.sidebar.file_uploader("Seleccione el archivo de RESPONSABLES", type=["xlsx", "csv"], key="uploader_r")

# Verificar que los tres archivos base obligatorios estén cargados
if file_mediaciones is not None and file_juicios is not None and file_vigentes is not None:
    
    @st.cache_data(show_spinner=False)
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
        # 1. Carga inicial optimizada en caché de los archivos crudos
        df_m_raw = leer_archivo(file_mediaciones)
        df_j_raw = leer_archivo(file_juicios)
        df_v_raw = leer_archivo(file_vigentes)
        
        # 2. Estructuración y Normalización global de columnas críticas (Evita llamadas diferidas a .apply)
        df_m_clean = df_m_raw.copy()
        df_m_clean['Prod_Codigo'] = df_m_clean[11].apply(normalizar_codigo)
        df_m_clean['Abogado'] = df_m_clean[10].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
        df_m_clean['Siniestro_Str'] = df_m_clean[2].fillna("").astype(str).str.strip()
        df_m_clean['Es_Auto'] = df_m_clean['Siniestro_Str'].str.startswith("03/")
        
        df_j_clean = df_j_raw.copy()
        df_j_clean['Prod_Codigo'] = df_j_clean[14].apply(normalizar_codigo)
        df_j_clean['Abogado'] = df_j_clean[13].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
        df_j_clean['Siniestro_Str'] = df_j_clean[2].fillna("").astype(str).str.strip()
        df_j_clean['Es_Auto'] = df_j_clean['Siniestro_Str'].str.startswith("03/")
        
        df_v_limpio = df_v_raw[[0, 1, 3, 4, 5, 6]].copy()
        df_v_limpio.columns = ['Ramo', 'Prod_Codigo', 'Org_Codigo', 'Org_Nombre', 'Master_Codigo', 'Master_Nombre']
        df_v_limpio['Ramo'] = df_v_limpio['Ramo'].fillna("").astype(str).str.strip()
        df_v_limpio['Prod_Codigo'] = df_v_limpio['Prod_Codigo'].apply(normalizar_codigo)
        df_v_limpio['Org_Codigo'] = df_v_limpio['Org_Codigo'].apply(normalizar_codigo)
        df_v_limpio['Org_Nombre'] = df_v_limpio['Org_Nombre'].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
        df_v_limpio['Master_Codigo'] = df_v_limpio['Master_Codigo'].apply(normalizar_codigo)
        df_v_limpio['Master_Nombre'] = df_v_limpio['Master_Nombre'].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()

        # -------------------------------------------------------------------------
        # PROCESAMIENTO DEL EXCEL DE RESPONSABLES
        # -------------------------------------------------------------------------
        map_resp_prod = {}
        map_resp_org = {}
        map_resp_master = {}
        responsables_asignaciones = []
        
        if file_responsables is not None:
            df_r_raw = leer_archivo(file_responsables)
            
            # Productor
            df_r_prod = df_r_raw[[0, 1, 6, 7]].dropna(subset=[0]).copy()
            df_r_prod[0] = df_r_prod[0].apply(normalizar_codigo)
            df_r_prod[6] = df_r_prod[6].apply(normalizar_codigo)
            df_r_prod[7] = df_r_prod[7].fillna("").astype(str).str.strip().str.upper()
            df_r_prod['Resp_String'] = df_r_prod.apply(lambda r: f"[{r[6]}] {r[7]}" if r[6] != "SIN CÓDIGO" else "SIN RESPONSABLE ASIGNADO", axis=1)
            map_resp_prod = df_r_prod.groupby(0)['Resp_String'].apply(lambda x: " / ".join(x.unique())).to_dict()
            
            for _, fila in df_r_prod.iterrows():
                if fila[7] != "" and fila[0] != "SIN CÓDIGO":
                    responsables_asignaciones.append({'Responsable': fila[7], 'Tipo': 'Productor', 'Código': fila[0]})
            
            # Organizador
            df_r_org = df_r_raw[[2, 3, 6, 7]].dropna(subset=[2]).copy()
            df_r_org[2] = df_r_org[2].apply(normalizar_codigo)
            df_r_org[6] = df_r_org[6].apply(normalizar_codigo)
            df_r_org[7] = df_r_org[7].fillna("").astype(str).str.strip().str.upper()
            df_r_org['Resp_String'] = df_r_org.apply(lambda r: f"[{r[6]}] {r[7]}" if r[6] != "SIN CÓDIGO" else "SIN RESPONSABLE ASIGNADO", axis=1)
            map_resp_org = df_r_org.groupby(2)['Resp_String'].apply(lambda x: " / ".join(x.unique())).to_dict()
            
            for _, fila in df_r_org.iterrows():
                if fila[7] != "" and fila[2] != "SIN CÓDIGO":
                    responsables_asignaciones.append({'Responsable': fila[7], 'Tipo': 'Organizador', 'Código': fila[2]})
            
            # Master
            df_r_master = df_r_raw[[4, 5, 6, 7]].dropna(subset=[4]).copy()
            df_r_master[4] = df_r_master[4].apply(normalizar_codigo)
            df_r_master[6] = df_r_master[6].apply(normalizar_codigo)
            df_r_master[7] = df_r_master[7].fillna("").astype(str).str.strip().str.upper()
            df_r_master['Resp_String'] = df_r_master.apply(
                lambda r: f"[{r[6]}] {r[7]}" if r[6] != "SIN CÓDIGO" and r[7] != "" else ("SIN RESPONSABLE ASIGNADO" if r[6] == "SIN CÓDIGO" else f"[{r[6]}] SIN NOMBRE"), axis=1
            )
            map_resp_master = df_r_master.groupby(4)['Resp_String'].apply(
                lambda x: "  //  ".join([resp for resp in x.unique() if resp != "SIN RESPONSABLE ASIGNADO"]) if len(x.unique()) > 1 else x.unique()[0]
            ).to_dict()
            
            for _, fila in df_r_master.iterrows():
                if fila[7] != "" and fila[4] != "SIN CÓDIGO":
                    responsables_asignaciones.append({'Responsable': fila[7], 'Tipo': 'Master', 'Código': fila[4]})

        # -------------------------------------------------------------------------
        # DICCIONARIOS Y MAPEOS DE ESTRUCTURAS COMERCIALES
        # -------------------------------------------------------------------------
        map_prod_org = df_v_limpio.drop_duplicates(subset=['Prod_Codigo']).set_index('Prod_Codigo')['Org_Codigo'].to_dict()
        map_prod_master = df_v_limpio.drop_duplicates(subset=['Prod_Codigo']).set_index('Prod_Codigo')['Master_Codigo'].to_dict()
        
        map_org_nombres = df_v_limpio[df_v_limpio['Org_Nombre'] != "SIN ASIGNAR"].drop_duplicates(subset=['Org_Codigo']).set_index('Org_Codigo')['Org_Nombre'].to_dict()
        map_master_nombres = df_v_limpio[df_v_limpio['Master_Nombre'] != "SIN ASIGNAR"].drop_duplicates(subset=['Master_Codigo']).set_index('Master_Codigo')['Master_Nombre'].to_dict()
        
        def buscar_nombre_organizador(cod): return map_org_nombres.get(str(cod).strip().upper(), "SIN ASIGNAR")
        def buscar_nombre_master(cod): return map_master_nombres.get(str(cod).strip().upper(), "SIN ASIGNAR")

        # Conteos e indexación rápida de pólizas vigentes
        conteo_vigentes_prod = df_v_limpio['Prod_Codigo'].value_counts().reset_index()
        conteo_vigentes_prod.columns = ['Código', 'Vigentes']

        df_v_filtrado_basura = df_v_limpio[~df_v_limpio['Org_Codigo'].isin(['CÓDIGO', 'CODIGO', 'ORGANIZADOR', 'SIN CÓDIGO'])]
        v_totales_org = df_v_filtrado_basura['Org_Codigo'].value_counts().to_dict()
        
        df_v_filtrado_basura_m = df_v_limpio[~df_v_limpio['Master_Codigo'].isin(['CÓDIGO', 'CODIGO', 'MASTER', 'SIN CÓDIGO'])]
        v_totales_master = df_v_filtrado_basura_m['Master_Codigo'].value_counts().to_dict()

        df_rel_org_prod = df_v_filtrado_basura[['Org_Codigo', 'Prod_Codigo']].drop_duplicates()
        df_rel_master_org = df_v_filtrado_basura_m[['Master_Codigo', 'Org_Codigo']].drop_duplicates()

        # Unificación del mapeo de Productores (Código -> Nombre)
        df_m_p_map = df_m_clean[[11, 12]].copy()
        df_m_p_map[12] = df_m_p_map[12].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
        map_m_prod = df_m_p_map[df_m_p_map[12] != "SIN ASIGNAR"].drop_duplicates(subset=[11]).set_index(11)[12].to_dict()

        df_j_p_map = df_j_clean[[14, 15]].copy()
        df_j_p_map[15] = df_j_p_map[15].fillna("SIN ASIGNAR").astype(str).str.strip().str.upper()
        map_j_prod = df_j_p_map[df_j_p_map[15] != "SIN ASIGNAR"].drop_duplicates(subset=[14]).set_index(14)[15].to_dict()

        # Combinamos diccionarios de forma rápida
        map_global_prod_nombres = {**map_m_prod, **map_j_prod}
        def buscar_nombre_productor(cod): return map_global_prod_nombres.get(str(cod).strip().upper(), "SIN ASIGNAR")

        # Asignación de dependencias jerárquicas en los DataFrames principales
        df_m_clean['Org_Codigo'] = df_m_clean['Prod_Codigo'].map(map_prod_org).fillna("SIN ORGANIZADOR")
        df_m_clean['Master_Codigo'] = df_m_clean['Prod_Codigo'].map(map_prod_master).fillna("SIN MASTER")
        
        df_j_clean['Org_Codigo'] = df_j_clean['Prod_Codigo'].map(map_prod_org).fillna("SIN ORGANIZADOR")
        df_j_clean['Master_Codigo'] = df_j_clean['Prod_Codigo'].map(map_prod_master).fillna("SIN MASTER")

        # Conteos agregados listos para visualización
        conteo_prod_m = df_m_clean['Prod_Codigo'].value_counts().reset_index(name='Mediaciones').rename(columns={'index': 'Código'})
        conteo_org_m = df_m_clean['Org_Codigo'].value_counts().reset_index(name='Mediaciones')
        conteo_master_m = df_m_clean['Master_Codigo'].value_counts().reset_index(name='Mediaciones')
        
        conteo_prod_j = df_j_clean['Prod_Codigo'].value_counts().reset_index(name='Juicios').rename(columns={'index': 'Código'})
        conteo_org_j = df_j_clean['Org_Codigo'].value_counts().reset_index(name='Juicios')
        conteo_master_j = df_j_clean['Master_Codigo'].value_counts().reset_index(name='Juicios')

        # -------------------------------------------------------------------------
        # SOLAPAS PRINCIPALES DEL TABLERO
        # -------------------------------------------------------------------------
        tabs = st.tabs(["⚖️ Abogados", "👤 Responsables", "💼 Productor", "🏢 Organizador", "👑 Master", "🔍 Coincidencias"])
        
        # =========================================================================
        # --- SOLAPA 1: ABOGADOS ---
        # =========================================================================
        with tabs[0]:
            st.markdown("<h3 class='section-header'>⚖️ Resumen de Carga por Profesional</h3>", unsafe_allow_html=True)
            
            conteo_m_ab = df_m_clean['Abogado'].value_counts().reset_index(name='Mediaciones').rename(columns={'index': 'Abogado'})
            conteo_j_ab = df_j_clean['Abogado'].value_counts().reset_index(name='Juicios').rename(columns={'index': 'Abogado'})
            
            df_consolidado_ab = pd.merge(conteo_m_ab, conteo_j_ab, on='Abogado', how='outer').fillna(0)
            df_consolidado_ab['Mediaciones'] = df_consolidado_ab['Mediaciones'].astype(int)
            df_consolidado_ab['Juicios'] = df_consolidado_ab['Juicios'].astype(int)
            df_consolidado_ab['Total General'] = df_consolidado_ab['Mediaciones'] + df_consolidado_ab['Juicios']
            
            titulos_limpieza_ab = {'ABOGADO', 'PROFESIONAL', 'RESPONSABLE', 'SIN ASIGNAR', 'DESCONOCIDO'}
            df_consolidado_ab = df_consolidado_ab[~df_consolidado_ab['Abogado'].isin(titulos_limpieza_ab)]
            df_consolidado_ab = df_consolidado_ab.sort_values(by='Total General', ascending=False).reset_index(drop=True)
            
            busqueda_ab = st.text_input("🔍 Buscar abogado por nombre:", placeholder="Escriba el apellido o nombre del profesional...")
            df_mostrar_ab = df_consolidado_ab[df_consolidado_ab['Abogado'].str.contains(busqueda_ab.strip().upper(), na=False)].reset_index(drop=True) if busqueda_ab else df_consolidado_ab

            st.write("Seleccione un abogado de la lista para desplegar el detalle analítico abajo:")
            evento_seleccion_ab = st.dataframe(df_mostrar_ab, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="tabla_abogados")
            
            filas_seleccionadas_ab = evento_seleccion_ab.get("selection", {}).get("rows", [])
            if filas_seleccionadas_ab:
                abogado_seleccionado = df_mostrar_ab.iloc[filas_seleccionadas_ab[0]]['Abogado']
                st.markdown(f"<h3 class='section-header'>📂 Expedientes de: {abogado_seleccionado}</h3>", unsafe_allow_html=True)
                
                df_det_m = df_m_clean[df_m_clean['Abogado'] == abogado_seleccionado].copy()
                m_auto = df_det_m['Es_Auto'].sum()
                m_moto = len(df_det_m) - m_auto
                df_det_m_vista = df_det_m.iloc[:, [2, 3, 4, 5]].copy()
                df_det_m_vista.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                df_det_m_vista['TIPO'] = 'M'
                
                df_det_j = df_j_clean[df_j_clean['Abogado'] == abogado_seleccionado].copy()
                j_auto = df_det_j['Es_Auto'].sum()
                j_moto = len(df_det_j) - j_auto
                df_det_j_vista = df_det_j.iloc[:, [2, 3, 5, 6]].copy()
                df_det_j_vista.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                df_det_j_vista['TIPO'] = 'J'
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric(label="🚗 Mediaciones Automotor (03/)", value=int(m_auto))
                c2.metric(label="🏍️ Mediaciones Motovehículo", value=int(m_moto))
                c3.metric(label="🚗 Juicios Automotor (03/)", value=int(j_auto))
                c4.metric(label="🏍️ Juicios Motovehículo", value=int(j_moto))
                
                df_detalle_abogado = pd.concat([df_det_m_vista, df_det_j_vista], ignore_index=True)
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
                            lista_prod_controlados.update(df_v_limpio[df_v_limpio['Org_Codigo'] == cod_c]['Prod_Codigo'].unique())
                        elif tipo_c == 'Master':
                            lista_prod_controlados.update(df_v_limpio[df_v_limpio['Master_Codigo'] == cod_c]['Prod_Codigo'].unique())
                    
                    lista_prod_controlados = [p for p in lista_prod_controlados if p not in {'SIN CÓDIGO', 'CÓDIGO'}]
                    
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
                        
                    resumen_por_responsable.append({
                        'Responsable': resp,
                        'Vigentes Auto (R3)': int(vigentes_auto),
                        'Vigentes Moto (R4)': int(vigentes_moto),
                        'Total Vigentes': int(vigentes_auto + vigentes_moto),
                        'Mediaciones': int(total_m),
                        'Juicios': int(total_j),
                        'Total Casos': int(total_m + total_j)
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
                            st.dataframe(pd.DataFrame({'Código': cods_p, 'Nombre Productor': [buscar_nombre_productor(c) for c in cods_p]}), use_container_width=True, hide_index=True)
                            
                        with c_org:
                            cods_o = df_sub_resp[df_sub_resp['Tipo'] == 'Organizador']['Código'].unique()
                            st.dataframe(pd.DataFrame({'Código': cods_o, 'Nombre Organizador': [buscar_nombre_organizador(c) for c in cods_o]}), use_container_width=True, hide_index=True)
                            
                        with c_mast:
                            cods_m = df_sub_resp[df_sub_resp['Tipo'] == 'Master']['Código'].unique()
                            st.dataframe(pd.DataFrame({'Código': cods_m, 'Nombre Master': [buscar_nombre_master(c) for c in cods_m]}), use_container_width=True, hide_index=True)
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
            
            # Cálculo vectorizado veloz de Incidencias
            v_vals = df_consolidado_prod['Vigentes'].values
            tg_vals = df_consolidado_prod['Total General'].values
            df_consolidado_prod['INCIDENCIA'] = np.where(v_vals > 0, np.round((tg_vals / v_vals) * 100, 2), np.where(tg_vals > 0, 100.0, 0.0))
            df_consolidado_prod['INCIDENCIA (%)'] = df_consolidado_prod['INCIDENCIA'].astype(str) + "%"
            
            df_consolidado_prod = df_consolidado_prod[['Código', 'Nombre Productor', 'Vigentes', 'INCIDENCIA (%)', 'Mediaciones', 'Juicios', 'Total General', 'INCIDENCIA']]
            titulos_basura = {'CÓDIGO', 'CODIGO', 'PRODUCTOR', 'NOMBRE', 'PRODUCTOR_COD', 'SIN CÓDIGO'}
            df_consolidado_prod = df_consolidado_prod[~df_consolidado_prod['Código'].isin(titulos_basura)]
            df_consolidado_prod = df_consolidado_prod.sort_values(by='INCIDENCIA', ascending=False).reset_index(drop=True)
            df_mostrar_tabla_p = df_consolidado_prod.drop(columns=['INCIDENCIA'])

            busqueda_prod = st.text_input("🔍 Buscar productor (por Código o por Nombre):", placeholder="Escriba el código numérico o el nombre del productor...", key="input_bus_prod")
            df_filtrada_prod = df_mostrar_tabla_p[df_mostrar_tabla_p['Código'].str.contains(busqueda_prod.strip().upper(), na=False) | df_mostrar_tabla_p['Nombre Productor'].str.contains(busqueda_prod.strip().upper(), na=False)].reset_index(drop=True) if busqueda_prod else df_mostrar_tabla_p

            st.write("Seleccione un productor de la lista para desplegar el análisis comercial abajo:")
            evento_seleccion_prod = st.dataframe(df_filtrada_prod, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="tabla_productores")
            
            filas_seleccionadas_prod = evento_seleccion_prod.get("selection", {}).get("rows", [])
            if filas_seleccionadas_prod:
                cod_seleccionado = df_filtrada_prod.iloc[filas_seleccionadas_prod[0]]['Código']
                nom_seleccionado = df_filtrada_prod.iloc[filas_seleccionadas_prod[0]]['Nombre Productor']
                
                st.markdown(f"<h3 class='section-header'>📂 Análisis de Cartera Comercial: [{cod_seleccionado}] - {nom_seleccionado}</h3>", unsafe_allow_html=True)
                
                if file_responsables is not None:
                    st.markdown(f"<div class='responsable-box'>👤 <b>Responsable Interno de Control:</b> {map_resp_prod.get(cod_seleccionado, 'SIN RESPONSABLE ASIGNADO')}</div>", unsafe_allow_html=True)
                
                sub_tab_expedientes, sub_tab_vigentes = st.tabs(["📋 Historial de Expedientes", "🚗 Detalle de Pólizas Vigentes"])
                
                with sub_tab_expedientes:
                    df_det_prod_m = df_m_clean[df_m_clean['Prod_Codigo'] == cod_seleccionado].copy()
                    m_auto_p = df_det_prod_m['Es_Auto'].sum()
                    m_moto_p = len(df_det_prod_m) - m_auto_p
                    df_det_prod_m_v = df_det_prod_m.iloc[:, [2, 3, 4, 5]].copy()
                    df_det_prod_m_v.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                    df_det_prod_m_v['TIPO'] = 'M'
                    
                    df_det_prod_j = df_j_clean[df_j_clean['Prod_Codigo'] == cod_seleccionado].copy()
                    j_auto_p = df_det_prod_j['Es_Auto'].sum()
                    j_moto_p = len(df_det_prod_j) - j_auto_p
                    df_det_prod_j_v = df_det_prod_j.iloc[:, [2, 3, 5, 6]].copy()
                    df_det_prod_j_v.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                    df_det_prod_j_v['TIPO'] = 'J'
                    
                    cp1, cp2, cp3, cp4 = st.columns(4)
                    cp1.metric(label="🚗 Mediaciones Automotor (03/)", value=int(m_auto_p))
                    cp2.metric(label="🏍️ Mediaciones Motovehículo", value=int(m_moto_p))
                    cp3.metric(label="🚗 Juicios Automotor (03/)", value=int(j_auto_p))
                    cp4.metric(label="🏍️ Juicios Motovehículo", value=int(j_moto_p))
                    
                    st.dataframe(pd.concat([df_det_prod_m_v, df_det_prod_j_v], ignore_index=True), use_container_width=True, hide_index=True)
                
                with sub_tab_vigentes:
                    df_v_filtrado_prod = df_v_limpio[df_v_limpio['Prod_Codigo'] == cod_seleccionado]
                    ramos_series = df_v_filtrado_prod['Ramo'].values
                    v_auto = np.sum(ramos_series == "3")
                    v_moto = np.sum(ramos_series == "4")
                    v_otros = len(df_v_filtrado_prod) - (v_auto + v_moto)
                    
                    cv1, cv2, cv3 = st.columns(3)
                    cv1.metric(label="🚗 Vigentes Automotores (Ramo 3)", value=int(v_auto))
                    cv2.metric(label="🏍️ Vigentes Motovehículos (Ramo 4)", value=int(v_moto))
                    cv3.metric(label="📊 Vigentes Otros Ramos", value=int(v_otros))

            st.markdown("<h3 class='section-header'>📊 Top 25 Productores con Mayor Volumen de Casos</h3>", unsafe_allow_html=True)
            df_top25_prod = df_consolidado_prod.sort_values(by='Total General', ascending=False).head(25).copy()
            if not df_top25_prod.empty:
                df_top25_prod['Productor Identificador'] = "[" + df_top25_prod['Código'] + "] " + df_top25_prod['Nombre Productor']
                df_chart_prod = df_top25_prod.melt(id_vars=['Productor Identificador'], value_vars=['Mediaciones', 'Juicios'], var_name='Tipo Expediente', value_name='Cantidad')
                fig_prod = px.bar(df_chart_prod, x='Productor Identificador', y='Cantidad', color='Tipo Expediente', color_discrete_map={'Mediaciones': '#DCA7B8', 'Juicios': '#8B1D41'}, barmode='stack')
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
            
            v_org_vals = df_consolidado_org['Vigentes'].values
            tg_org_vals = df_consolidado_org['Total General'].values
            df_consolidado_org['INCIDENCIA'] = np.where(v_org_vals > 0, np.round((tg_org_vals / v_org_vals) * 100, 2), np.where(tg_org_vals > 0, 100.0, 0.0))
            df_consolidado_org['INCIDENCIA (%)'] = df_consolidado_org['INCIDENCIA'].astype(str) + "%"
            
            df_consolidado_org = df_consolidado_org[['Org_Codigo', 'Nombre Organizador', 'Vigentes', 'INCIDENCIA (%)', 'Mediaciones', 'Juicios', 'Total General', 'INCIDENCIA']]
            df_consolidado_org.columns = ['Código', 'Nombre Organizador', 'Vigentes', 'INCIDENCIA (%)', 'Mediaciones', 'Juicios', 'Total General', 'INCIDENCIA']
            
            titulos_basura_org = {'CÓDIGO', 'CODIGO', 'ORGANIZADOR', 'SIN CÓDIGO', 'SIN ORGANIZADOR', 'SIN ASIGNAR'}
            df_consolidado_org = df_consolidado_org[~df_consolidado_org['Código'].isin(titulos_basura_org)]
            df_consolidado_org = df_consolidado_org.sort_values(by='INCIDENCIA', ascending=False).reset_index(drop=True)
            df_mostrar_tabla_o = df_consolidado_org.drop(columns=['INCIDENCIA'])
            
            busqueda_org = st.text_input("🔍 Buscar Organizador (por Código o Nombre):", placeholder="Escriba el código o nombre de la estructura...", key="input_bus_org")
            df_filtrada_org = df_mostrar_tabla_o[df_mostrar_tabla_o['Código'].str.contains(busqueda_org.strip().upper(), na=False) | df_mostrar_tabla_o['Nombre Organizador'].str.contains(busqueda_org.strip().upper(), na=False)].reset_index(drop=True) if busqueda_org else df_mostrar_tabla_o

            st.write("Seleccione un organizador de la lista para desplegar el análisis corporativo abajo:")
            evento_seleccion_org = st.dataframe(df_filtrada_org, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="tabla_organizadores")
            
            filas_seleccionadas_org = evento_seleccion_org.get("selection", {}).get("rows", [])
            if filas_seleccionadas_org:
                org_cod_sel = df_filtrada_org.iloc[filas_seleccionadas_org[0]]['Código']
                org_nom_sel = df_filtrada_org.iloc[filas_seleccionadas_org[0]]['Nombre Organizador']
                
                st.markdown(f"<h3 class='section-header'>📂 Análisis Integrado de Estructura: [{org_cod_sel}] {org_nom_sel}</h3>", unsafe_allow_html=True)
                
                if file_responsables is not None:
                    st.markdown(f"<div class='responsable-box'>👤 <b>Responsable Interno de Control:</b> {map_resp_org.get(org_cod_sel, 'SIN RESPONSABLE ASIGNADO')}</div>", unsafe_allow_html=True)

                df_prod_asociados = df_rel_org_prod[df_rel_org_prod['Org_Codigo'] == org_cod_sel].copy()
                df_prod_asociados['Nombre Productor'] = df_prod_asociados['Prod_Codigo'].apply(buscar_nombre_productor)
                
                with st.expander("🤝 Ver Carteras y Productores Vinculados a este Organizador", expanded=False):
                    st.dataframe(df_prod_asociados[['Prod_Codigo', 'Nombre Productor']].rename(columns={'Prod_Codigo':'Código Productor Agrupado', 'Nombre Productor':'Nombre del Productor'}), use_container_width=True, hide_index=True)

                sub_tab_expedientes_o, sub_tab_vigentes_o = st.tabs(["📋 Historial de Expedientes", "🚗 Detalle de Pólizas Vigentes"])
                
                with sub_tab_expedientes_o:
                    df_det_org_m = df_m_clean[df_m_clean['Org_Codigo'] == org_cod_sel].copy()
                    m_auto_o = df_det_org_m['Es_Auto'].sum()
                    m_moto_o = len(df_det_org_m) - m_auto_o
                    df_det_org_m_v = df_det_org_m.iloc[:, [2, 3, 4, 5]].copy()
                    df_det_org_m_v.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                    df_det_org_m_v['TIPO'] = 'M'
                    
                    df_det_org_j = df_j_clean[df_j_clean['Org_Codigo'] == org_cod_sel].copy()
                    j_auto_o = df_det_org_j['Es_Auto'].sum()
                    j_moto_o = len(df_det_org_j) - j_auto_o
                    df_det_org_j_v = df_det_org_j.iloc[:, [2, 3, 5, 6]].copy()
                    df_det_org_j_v.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                    df_det_org_j_v['TIPO'] = 'J'

                    co1, co2, co3, co4 = st.columns(4)
                    co1.metric(label="🚗 Mediaciones Automotor (03/)", value=int(m_auto_o))
                    co2.metric(label="🏍️ Mediaciones Motovehículo", value=int(m_moto_o))
                    co3.metric(label="🚗 Juicios Automotor (03/)", value=int(j_auto_o))
                    co4.metric(label="🏍️ Juicios Motovehículo", value=int(j_moto_o))
                    
                    st.dataframe(pd.concat([df_det_org_m_v, df_det_org_j_v], ignore_index=True), use_container_width=True, hide_index=True)
                
                with sub_tab_vigentes_o:
                    df_v_filtrado_org = df_v_limpio[df_v_limpio['Org_Codigo'] == org_cod_sel]
                    v_o_ramos = df_v_filtrado_org['Ramo'].values
                    v_auto_o = np.sum(v_o_ramos == "3")
                    v_moto_o = np.sum(v_o_ramos == "4")
                    v_otros_o = len(df_v_filtrado_org) - (v_auto_o + v_moto_o)
                    
                    cvo1, cvo2, cvo3 = st.columns(3)
                    cvo1.metric(label="🚗 Vigentes Automotores (Ramo 3)", value=int(v_auto_o))
                    cvo2.metric(label="🏍️ Vigentes Motovehículos (Ramo 4)", value=int(v_moto_o))
                    cvo3.metric(label="📊 Vigentes Otros Ramos", value=int(v_otros_o))

            st.markdown("<h3 class='section-header'>📊 Top 25 Organizadores con Mayor Volumen de Casos</h3>", unsafe_allow_html=True)
            df_top25_org = df_consolidado_org.sort_values(by='Total General', ascending=False).head(25).copy()
            if not df_top25_org.empty:
                df_top25_org['Org Identificador'] = "[" + df_top25_org['Código'] + "] " + df_top25_org['Nombre Organizador']
                df_chart_org = df_top25_org.melt(id_vars=['Org Identificador'], value_vars=['Mediaciones', 'Juicios'], var_name='Tipo Expediente', value_name='Cantidad')
                fig_org = px.bar(df_chart_org, x='Org Identificador', y='Cantidad', color='Tipo Expediente', color_discrete_map={'Mediaciones': '#DCA7B8', 'Juicios': '#8B1D41'}, barmode='stack')
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
            
            v_m_vals = df_consolidado_master['Vigentes'].values
            tg_m_vals = df_consolidado_master['Total General'].values
            df_consolidado_master['INCIDENCIA'] = np.where(v_m_vals > 0, np.round((tg_m_vals / v_m_vals) * 100, 2), np.where(tg_m_vals > 0, 100.0, 0.0))
            df_consolidado_master['INCIDENCIA (%)'] = df_consolidado_master['INCIDENCIA'].astype(str) + "%"
            
            df_consolidado_master = df_consolidado_master[['Master_Codigo', 'Nombre Master', 'Vigentes', 'INCIDENCIA (%)', 'Mediaciones', 'Juicios', 'Total General', 'INCIDENCIA']]
            df_consolidado_master.columns = ['Código', 'Nombre Master', 'Vigentes', 'INCIDENCIA (%)', 'Mediaciones', 'Juicios', 'Total General', 'INCIDENCIA']
            
            titulos_basura_master = {'CÓDIGO', 'CODIGO', 'MASTER', 'SIN CÓDIGO', 'SIN MASTER', 'SIN ASIGNAR'}
            df_consolidado_master = df_consolidado_master[~df_consolidado_master['Código'].isin(titulos_basura_master)]
            df_consolidado_master = df_consolidado_master.sort_values(by='INCIDENCIA', ascending=False).reset_index(drop=True)
            df_mostrar_tabla_m = df_consolidado_master.drop(columns=['INCIDENCIA'])
            
            busqueda_master = st.text_input("🔍 Buscar Master (por Código o Nombre):", placeholder="Escriba el código o nombre de la macro-estructura...", key="input_bus_master")
            df_filtrada_master = df_mostrar_tabla_m[df_mostrar_tabla_m['Código'].str.contains(busqueda_master.strip().upper(), na=False) | df_mostrar_tabla_m['Nombre Master'].str.contains(busqueda_master.strip().upper(), na=False)].reset_index(drop=True) if busqueda_master else df_mostrar_tabla_m

            st.write("Seleccione un Master de la lista para desplegar el análisis macro abajo:")
            evento_seleccion_master = st.dataframe(df_filtrada_master, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="tabla_masters")
            
            filas_seleccionadas_master = evento_seleccion_master.get("selection", {}).get("rows", [])
            if filas_seleccionadas_master:
                master_cod_sel = df_filtrada_master.iloc[filas_seleccionadas_master[0]]['Código']
                master_nom_sel = df_filtrada_master.iloc[filas_seleccionadas_master[0]]['Nombre Master']
                
                st.markdown(f"<h3 class='section-header'>📂 Análisis Integrado de Macro-Estructura Master: [{master_cod_sel}] {master_nom_sel}</h3>", unsafe_allow_html=True)
                
                if file_responsables is not None:
                    st.markdown(f"<div class='responsable-box'>👤 <b>Responsable Interno de Control:</b> {map_resp_master.get(master_cod_sel, 'SIN RESPONSABLE ASIGNADO')}</div>", unsafe_allow_html=True)

                df_org_asociados = df_rel_master_org[df_rel_master_org['Master_Codigo'] == master_cod_sel].copy()
                df_org_asociados['Nombre Organizador'] = df_org_asociados['Org_Codigo'].apply(buscar_nombre_organizador)
                
                with st.expander("🤝 Ver Organizadores Agrupados bajo esta Estructura Master", expanded=False):
                    st.dataframe(df_org_asociados[['Org_Codigo', 'Nombre Organizador']].rename(columns={'Org_Codigo':'Código Organizador Agrupado', 'Nombre Organizador':'Nombre del Organizador'}), use_container_width=True, hide_index=True)

                sub_tab_expedientes_m, sub_tab_vigentes_m = st.tabs(["📋 Historial de Expedientes", "🚗 Detalle de Pólizas Vigentes"])
                
                with sub_tab_expedientes_m:
                    df_det_master_m = df_m_clean[df_m_clean['Master_Codigo'] == master_cod_sel].copy()
                    m_auto_m = df_det_master_m['Es_Auto'].sum()
                    m_moto_m = len(df_det_master_m) - m_auto_m
                    df_det_master_m_v = df_det_master_m.iloc[:, [2, 3, 4, 5]].copy()
                    df_det_master_m_v.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                    df_det_master_m_v['TIPO'] = 'M'
                    
                    df_det_master_j = df_j_clean[df_j_clean['Master_Codigo'] == master_cod_sel].copy()
                    j_auto_m = df_det_master_j['Es_Auto'].sum()
                    j_moto_m = len(df_det_master_j) - j_auto_m
                    df_det_master_j_v = df_det_master_j.iloc[:, [2, 3, 5, 6]].copy()
                    df_det_master_j_v.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                    df_det_master_j_v['TIPO'] = 'J'

                    cm1, cm2, cm3, cm4 = st.columns(4)
                    cm1.metric(label="🚗 Mediaciones Automotor (03/)", value=int(m_auto_m))
                    cm2.metric(label="🏍️ Mediaciones Motovehículo", value=int(m_moto_m))
                    cm3.metric(label="🚗 Juicios Automotor (03/)", value=int(j_auto_m))
                    cm4.metric(label="🏍️ Juicios Motovehículo", value=int(j_moto_m))
                    
                    st.dataframe(pd.concat([df_det_master_m_v, df_det_master_j_v], ignore_index=True), use_container_width=True, hide_index=True)
                
                with sub_tab_vigentes_m:
                    df_v_filtrado_master = df_v_limpio[df_v_limpio['Master_Codigo'] == master_cod_sel]
                    v_m_ramos = df_v_filtrado_master['Ramo'].values
                    v_auto_m = np.sum(v_m_ramos == "3")
                    v_moto_m = np.sum(v_m_ramos == "4")
                    v_otros_m = len(df_v_filtrado_master) - (v_auto_m + v_moto_m)
                    
                    cvm1, cvm2, cvm3 = st.columns(3)
                    cvm1.metric(label="🚗 Vigentes Automotores (Ramo 3)", value=int(v_auto_m))
                    cvm2.metric(label="🏍️ Vigentes Motovehículos (Ramo 4)", value=int(v_moto_m))
                    cvm3.metric(label="📊 Vigentes Otros Ramos", value=int(v_otros_m))

            st.markdown("<h3 class='section-header'>📊 Top 25 Masters con Mayor Volumen de Casos</h3>", unsafe_allow_html=True)
            df_top25_master = df_consolidado_master.sort_values(by='Total General', ascending=False).head(25).copy()
            if not df_top25_master.empty:
                df_top25_master['Master Identificador'] = "[" + df_top25_master['Código'] + "] " + df_top25_master['Nombre Master']
                df_chart_master = df_top25_master.melt(id_vars=['Master Identificador'], value_vars=['Mediaciones', 'Juicios'], var_name='Tipo Expediente', value_name='Cantidad')
                fig_master = px.bar(df_chart_master, x='Master Identificador', y='Cantidad', color='Tipo Expediente', color_discrete_map={'Mediaciones': '#DCA7B8', 'Juicios': '#8B1D41'}, barmode='stack')
                fig_master.update_layout(xaxis={'categoryorder':'total descending'}, margin=dict(l=20, r=20, t=10, b=40))
                st.plotly_chart(fig_master, use_container_width=True)

        # =========================================================================
        # --- SOLAPA 6: COINCIDENCIAS ---
        # =========================================================================
        with tabs[5]:
            st.markdown("<h3 class='section-header'>📜 Cruce y Coincidencias (Productor + Abogado)</h3>", unsafe_allow_html=True)
            
            df_g_m = df_m_clean.groupby(['Prod_Codigo', 'Abogado']).size().reset_index(name='Mediaciones').rename(columns={'Prod_Codigo': 'Código Productor'})
            df_g_j = df_j_clean.groupby(['Prod_Codigo', 'Abogado']).size().reset_index(name='Juicios').rename(columns={'Prod_Codigo': 'Código Productor'})

            df_coinc_total = pd.merge(df_g_m, df_g_j, on=['Código Productor', 'Abogado'], how='outer').fillna(0)
            df_coinc_total['Mediaciones'] = df_coinc_total['Mediaciones'].astype(int)
            df_coinc_total['Juicios'] = df_coinc_total['Juicios'].astype(int)
            df_coinc_total['Total Coincidencias'] = df_coinc_total['Mediaciones'] + df_coinc_total['Juicios']
            df_coinc_total['Nombre Productor'] = df_coinc_total['Código Productor'].apply(buscar_nombre_productor)
            df_coinc_total = df_coinc_total[['Código Productor', 'Nombre Productor', 'Abogado', 'Mediaciones', 'Juicios', 'Total Coincidencias']]
            
            titulos_filtro = {'CÓDIGO', 'CODIGO', 'PRODUCTOR', 'ABOGADO', 'PROFESIONAL', 'SIN CÓDIGO', 'SIN ASIGNAR', 'DESCONOCIDO'}
            df_coinc_total = df_coinc_total[~df_coinc_total['Código Productor'].isin(titulos_filtro) & ~df_coinc_total['Abogado'].isin(titulos_filtro)]
            df_coinc_total = df_coinc_total.sort_values(by='Total Coincidencias', ascending=False).reset_index(drop=True)
            
            busqueda_c = st.text_input("🔍 Buscador de Coincidencias:", placeholder="Busque por Código, Productor o Abogado...", key="input_coinc")
            if busqueda_c:
                bc_upper = busqueda_c.strip().upper()
                df_mostrar_coinc = df_coinc_total[df_coinc_total['Código Productor'].str.contains(bc_upper, na=False) | df_coinc_total['Nombre Productor'].str.contains(bc_upper, na=False) | df_coinc_total['Abogado'].str.contains(bc_upper, na=False)].reset_index(drop=True)
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
                
                df_det_c_m = df_m_clean[(df_m_clean['Prod_Codigo'] == cod_c_sel) & (df_m_clean['Abogado'] == abog_c_sel)].iloc[:, [2, 3, 4, 5]].copy()
                df_det_c_m.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                df_det_c_m['TIPO'] = 'M'
                
                df_det_c_j = df_j_clean[(df_j_clean['Prod_Codigo'] == cod_c_sel) & (df_j_clean['Abogado'] == abog_c_sel)].iloc[:, [2, 3, 5, 6]].copy()
                df_det_c_j.columns = ['SINIESTRO', 'CARATULA', 'FECHA DE SINIESTRO', 'DETALLE EXPEDIENTE']
                df_det_c_j['TIPO'] = 'J'
                
                st.dataframe(pd.concat([df_det_c_m, df_det_c_j], ignore_index=True), use_container_width=True, hide_index=True)

    except IndexError:
        st.error("Error de formato: Verifique que Mediaciones llegue a col M, Juicios a col P y VIGENTES contenga Ramo en col A, Productor en col B, Organizador en col D/E y MASTER en col F/G.")
    except Exception as e:
        st.error(f"Ocurrió un error inesperado al procesar los archivos: {e}")

else:
    st.info("👋 Bienvenido, mdondo. Por favor, cargue los tres archivos base (Mediaciones, Juicios y VIGENTES) en el panel lateral para iniciar el análisis.")
