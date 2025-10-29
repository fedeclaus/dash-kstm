import streamlit as st
import datetime
import os

# --- Configuración inicial ---
st.set_page_config(page_title="Panel KSTM - Viento y Olas", layout="wide")

# --- Botones superiores alineados ---
st.markdown("""
    <style>
    .botones-derecha {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        display: flex;
        gap: 10px;
    }
    .botones-derecha a {
        background-color: #009688;
        color: white !important;
        text-decoration: none;
        font-weight: bold;
        padding: 10px 18px;
        border-radius: 8px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.3);
        font-family: 'sans-serif';
    }
    .botones-derecha a:hover {
        background-color: #00796b;
        color: white !important;
    }
    .botones-derecha a.satelite {
        background-color: #0066cc;
    }
    .botones-derecha a.satelite:hover {
        background-color: #004c99;
    }
    </style>

    <div class="botones-derecha">
        <a href="https://zoom.earth/maps/satellite/#view=-35.5,-61.3,4z" 
           class="satelite" target="_blank">SATÉLITE</a>
        <a href="https://kstm-fluvial.streamlit.app/" target="_blank">PRONÓSTICO FLUVIAL</a>
    </div>
""", unsafe_allow_html=True)

# --- Título principal ---
st.title("🌊 Panel de Pronóstico Marítimo (KSTM)")
st.markdown("""
Visualización combinada de **altura significativa de ola** (Copernicus) y **viento máximo pronosticado** (GFS)
en los principales puertos del Atlántico Sur.
""")

# --- Directorio donde están los mapas HTML ---
RUTA_MAPAS = "./mapas_html"  # o tu subcarpeta del repo

if not os.path.exists(RUTA_MAPAS):
    st.error("❌ No se encontró la carpeta con los mapas HTML.")
    st.stop()

archivos = sorted(
    [f for f in os.listdir(RUTA_MAPAS) if f.endswith(".html")]
)

if not archivos:
    st.warning("No hay mapas HTML disponibles.")
    st.stop()

# --- Crear menú desplegable con fechas ---
opciones = []
for f in archivos:
    try:
        fecha_str = f.replace("mapa_combinado_", "").replace(".html", "")
        fecha_dt = datetime.datetime.strptime(fecha_str, "%Y-%m-%d")
        opciones.append((f, fecha_dt.strftime("%d %b %Y")))
    except:
        pass

if not opciones:
    st.error("No se pudo interpretar ninguna fecha de los archivos.")
    st.stop()

# --- Menú de selección ---
archivos_ordenados = sorted(opciones, key=lambda x: x[0])
labels = [f"Pronóstico para {x[1]}" for x in archivos_ordenados]
seleccion = st.selectbox("Seleccioná el día a visualizar:", labels, index=0)

archivo_seleccionado = archivos_ordenados[labels.index(seleccion)][0]
ruta_html = os.path.join(RUTA_MAPAS, archivo_seleccionado)

st.subheader(f"🗓️ {seleccion}")

# --- Mostrar HTML embebido ---
with open(ruta_html, "r", encoding="utf-8") as f:
    html = f.read()

st.components.v1.html(html, height=700, scrolling=True)

st.markdown("---")
st.caption("Desarrollado por KSTM — Datos GFS & Copernicus")
