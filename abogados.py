import streamlit as st
import pandas as pd

# Configuración de la página de Streamlit
st.set_page_config(page_title="Control de Responsables", layout="wide")
st.title("Sistema de Control de Responsables Internos")

# ==============================================================================
# 1. CARGA Y PROCESAMIENTO DEL NUEVO EXCEL
# ==============================================================================
@st.cache_data
def cargar_datos():
    # Reemplaza "responsables.xlsx" por el nombre exacto de tu archivo
    # Forzamos la lectura de las columnas A hasta la H (índices 0 al 7) ignorando cabeceras rotas
    df = pd.read_excel("responsables.xlsx", usecols="A:H", header=None)
    
    # Renombramos las columnas según tu especificación exacta por posiciones de letras
    df.columns = [
        'prod_codigo', 'prod_nombre',       # Columna A, B (Productor)
        'org_codigo', 'org_nombre',         # Columna C, D (Organizador)
        'master_codigo', 'master_nombre',   # Columna E, F (Master)
        'resp_codigo', 'resp_nombre'        # Columna G, H (Responsable común)
    ]
    
    # Limpiamos los datos eliminando espacios vacíos y convirtiendo todo a texto para evitar fallas de tipo
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        
    return df

# Inicializamos el DataFrame
try:
    df_responsables = cargar_datos()
except Exception as e:
    st.error(f"Error al cargar el archivo Excel: {e}")
    st.stop()


# ==============================================================================
# 2. CREACIÓN DE LAS SOLAPAS (TABS) EN STREAMLIT
# ==============================================================================
tab1, tab2, tab3 = st.tabs(["Productor", "Organizador", "Master"])

# ------------------------------------------------------------------------------
# SOLAPA 1: PRODUCTOR (Columnas A y B -> Responsable en G y H)
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("Consulta de Responsables por Productor")
    
    # Filtramos filas donde el nombre del productor no esté vacío u "nan"
    df_prod = df_responsables[df_responsables['prod_nombre'] != 'nan']
    lista_productores = sorted(df_prod['prod_nombre'].unique())
    
    if lista_productores:
        productor_elegido = st.selectbox("Seleccione un Productor:", lista_productores, key="sb_prod")
        
        # Buscamos la fila correspondiente al productor elegido
        fila_prod = df_prod[df_prod['prod_nombre'] == productor_elegido].iloc[0]
        
        # Guardamos los datos del responsable asignado (G y H)
        cod_resp = fila_prod['resp_codigo']
        nom_resp = fila_prod['resp_nombre']
        
        # Mostramos la información limpia en pantalla sin etiquetas genéricas
        if cod_resp != 'nan' and nom_resp != 'nan':
            st.info(f"**Responsable Interno de Control:** {cod_resp} - {nom_resp}")
        else:
            st.warning("Este productor no tiene un responsable asignado en el archivo.")
    else:
        st.info("No se encontraron productores en el archivo cargado.")

# ------------------------------------------------------------------------------
# SOLAPA 2: ORGANIZADOR (Columnas C y D -> Responsable en G y H)
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("Consulta de Responsables por Organizador")
    
    # Filtramos filas donde el nombre del organizador no esté vacío u "nan"
    df_org = df_responsables[df_responsables['org_nombre'] != 'nan']
    lista_organizadores = sorted(df_org['org_nombre'].unique())
    
    if lista_organizadores:
        organizador_elegido = st.selectbox("Seleccione un Organizador:", lista_organizadores, key="sb_org")
        
        # Buscamos la fila correspondiente al organizador elegido
        fila_org = df_org[df_org['org_nombre'] == organizador_elegido].iloc[0]
        
        # Guardamos los datos del responsable asignado (G y H)
        cod_resp = fila_org['resp_codigo']
        nom_resp = fila_org['resp_nombre']
        
        if cod_resp != 'nan' and nom_resp != 'nan':
            st.info(f"**Responsable Interno de Control:** {cod_resp} - {nom_resp}")
        else:
            st.warning("Este organizador no tiene un responsable asignado en el archivo.")
    else:
        st.info("No se encontraron organizadores en el archivo cargado.")

# ------------------------------------------------------------------------------
# SOLAPA 3: MASTER (Columnas E y F -> Responsable en G y H)
# ------------------------------------------------------------------------------
with tab3:
    st.subheader("Consulta de Responsables por Master")
    
    # Filtramos filas donde el nombre del master no esté vacío u "nan"
    df_master = df_responsables[df_responsables['master_nombre'] != 'nan']
    lista_masters = sorted(df_master['master_nombre'].unique())
    
    if lista_masters:
        master_elegido = st.selectbox("Seleccione un Master:", lista_masters, key="sb_master")
        
        # Buscamos la fila correspondiente al master elegido
        fila_master = df_master[df_master['master_nombre'] == master_elegido].iloc[0]
        
        # Guardamos los datos del responsable asignado (G y H)
        cod_resp = fila_master['resp_codigo']
        nom_resp = fila_master['resp_nombre']
        
        if cod_resp != 'nan' and nom_resp != 'nan':
            st.info(f"**Responsable Interno de Control:** {cod_resp} - {nom_resp}")
        else:
            st.warning("Este Master no tiene un responsable asignado en el archivo.")
    else:
        st.info("No se encontraron Masters en el archivo cargado.")
