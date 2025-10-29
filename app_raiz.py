import streamlit as st
import datetime
import os

# --- Configuración inicial ---
st.set_page_config(page_title="Panel KSTM - Viento y Olas", layout="wide")

# --- Estilo para los botones (a la altura del título) ---
st.markdown("""
    <style>
    .fila-titulo {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    .titulo {
        font-size: 2rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .botones {
        display: flex;
        gap: 10px;
    }
    .botones a {
        background-color: #009688;
        color: white !important;
        text-decoration: none;
        font-weight: bold;
        padding: 10px 18px;
        border-radius: 8px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.3);
        font-family: 'sans-serif';
    }
    .botones a:hover {
        background-color: #00796b;
        color: white !important;
    }
    .botones a.satelite {
        background-color: #0066cc;
    }
    .botones a.satelite:hover {
        background-color: #004c99;
    }
    </style>
""", unsafe_allow_html=True)

# --- Encabezado con título y botones ---
st.markdown("""
<div class="fila-titulo">
  <div class="titulo">🌊 Panel de Pronóstico Marítimo (KSTM)</div>
  <div class="botones">
    <a href="https://zoom.earth/maps/satellite/#view=-35.5,-61.3,4z" 
       class="satelite" target="_blank">SATÉLITE</a>
    <a href="https://kstm-fluvial.streamlit.app/" target="_blank">PRONÓSTICO FLUVIAL</a>
  </div>
</div>
""", unsafe_allow_html=True)

# --- Descripción ---
st.markdown("""
Visualización combinada de **altura significativa de ola** (Copernicus) y **viento máximo pronosticado** (GFS)
en los principales puertos del Atlántico Sur.
""")

# --- Directorio donde están los mapas HTML ---
RUTA_MAPAS = "./mapas_html"  # o tu subcarpeta del repo

if not os.path.exists(RUTA_MAPAS):
    st.error("❌ No se encontró la carpeta con los mapas HTML.")
    st.stop()

archivos = sorted([f for f in os.listdir(RUTA_MAPAS) if f.endswith(".html")])

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

archivos_ordenados = sorted(opciones, key=lambda x: x[0])
labels = [f"Pronóstico para {x[1]}" for x in archivos_ordenados]
seleccion = st.selectbox("Seleccioná el día a visualizar:", labels, index=0)

archivo_seleccionado = archivos_ordenados[labels.index(seleccion)][0]
ruta_html = os.path.join(RUTA_MAPAS, archivo_seleccionado)

st.subheader(f"🗓️ {seleccion}")

with open(ruta_html, "r", encoding="utf-8") as f:
    html = f.read()

st.components.v1.html(html, height=700, scrolling=True)

st.markdown("---")
st.caption("Desarrollado por KSTM — Datos GFS & Copernicus")
