import streamlit as st
import datetime
import os
import re

# --- Configuración inicial ---
st.set_page_config(page_title="Panel KSTM - Viento y Olas", layout="wide")

st.title("🌊 Panel de Pronóstico Marítimo (KSTM)")
st.markdown("""
Visualización combinada de **altura significativa de ola** (Copernicus) y **viento máximo pronosticado** (GFS)
en los principales puertos del Atlántico Sur.
""")

# --- Directorio donde están los mapas HTML ---
RUTA_MAPAS = "./mapas_html"  # o la carpeta donde guardás los archivos

# --- Buscar archivos disponibles ---
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
        # Buscar fecha con regex: YYYY-MM-DD
        match = re.search(r"\d{4}-\d{2}-\d{2}", f)
        if match:
            fecha_str = match.group(0)
            fecha_dt = datetime.datetime.strptime(fecha_str, "%Y-%m-%d")
            opciones.append((f, fecha_dt.strftime("%d %b %Y")))
        else:
            st.write(f"⚠️ No se encontró fecha válida en {f}")
    except Exception as e:
        st.write(f"⚠️ Error al interpretar fecha en {f}: {e}")

if not opciones:
    st.error("No se pudo interpretar ninguna fecha de los archivos.")
    st.stop()

# --- Menú de selección ---
archivos_ordenados = sorted(opciones, key=lambda x: x[1])
labels = [f"Pronóstico para {x[1]}" for x in archivos_ordenados]
seleccion = st.selectbox("Seleccioná el día a visualizar:", labels, index=0)

# --- Mostrar el HTML correspondiente ---
archivo_seleccionado = archivos_ordenados[labels.index(seleccion)][0]
ruta_html = os.path.join(RUTA_MAPAS, archivo_seleccionado)

st.subheader(f"🗓️ {seleccion}")

# Mostrar el HTML embebido dentro del panel
with open(ruta_html, "r", encoding="utf-8") as f:
    html = f.read()

st.components.v1.html(html, height=700, scrolling=True)

st.markdown("---")
st.caption("Desarrollado por KSTM — Datos GFS & Copernicus")
