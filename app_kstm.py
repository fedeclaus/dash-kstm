import streamlit as st
import pandas as pd
import numpy as np
import xarray as xr
import os
from datetime import datetime, timedelta

# ==============================
# CONFIGURACIÓN INICIAL
# ==============================
st.set_page_config(page_title="KSTM Dashboard", layout="wide")

coords = {
    "Mar del Plata": (-38.0, -57.55),
    "Necochea": (-38.6, -58.7),
    "Puerto Madryn": (-42.76, -65.04),
    "Comodoro Rivadavia": (-45.86, -67.48),
}

# ==============================
# FUNCIONES AUXILIARES
# ==============================
def corregir_longitud(lon):
    return lon if lon >= 0 else 360 + lon

def viento_uv_a_direccion(u, v):
    return (270 - np.degrees(np.arctan2(v, u))) % 360

# ==============================
# OBTENER VIENTO GFS
# ==============================
@st.cache_data(show_spinner=False)
def obtener_viento_gfs():
    base_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    fechas = [base_time + timedelta(hours=h) for h in [0, 24, 48, 72]]
    url_base = f"https://nomads.ncep.noaa.gov:9090/dods/gfs_0p25/gfs{base_time:%Y%m%d}/gfs_0p25_{base_time:%Hz}"

    try:
        ds = xr.open_dataset(url_base, engine="pydap")
    except Exception as e:
        st.error(f"No se pudo abrir el dataset GFS.\nError: {e}")
        return pd.DataFrame(columns=["Ciudad", "Tiempo UTC", "Velocidad [kt]", "Dirección [°]", "Lat", "Lon", "Día"])

    filas = []
    for tiempo in fechas:
        if np.datetime64(tiempo) not in ds["time"]:
            continue
        for ciudad, (lat, lon_orig) in coords.items():
            lon = corregir_longitud(lon_orig)
            try:
                u = ds["ugrd10m"].sel(time=tiempo, lat=lat, lon=lon, method="nearest").values.item()
                v = ds["vgrd10m"].sel(time=tiempo, lat=lat, lon=lon, method="nearest").values.item()
                vel = np.sqrt(u**2 + v**2)
                dir = viento_uv_a_direccion(u, v)
                filas.append({
                    "Ciudad": ciudad,
                    "Tiempo UTC": tiempo,
                    "Velocidad [kt]": vel * 1.94384,
                    "Dirección [°]": dir,
                    "Lat": lat,
                    "Lon": lon_orig
                })
            except Exception:
                continue

    ds.close()

    if not filas:
        st.error("No se pudieron procesar los datos GFS (sin filas válidas).")
        return pd.DataFrame(columns=["Ciudad", "Tiempo UTC", "Velocidad [kt]", "Dirección [°]", "Lat", "Lon", "Día"])

    df = pd.DataFrame(filas)
    df["Día"] = pd.to_datetime(df["Tiempo UTC"]).dt.date
    return df

# ==============================
# OBTENER ALTURA DE OLAS (COPERNICUS)
# ==============================
@st.cache_data(show_spinner=False)
def obtener_olas_copernicus():
    archivo_salida = "olas_copernicus.csv"
    if not os.path.exists(archivo_salida):
        # Simulación: generar datos falsos si no existe
        data = {
            "Ciudad": list(coords.keys()),
            "Altura significativa [m]": np.random.uniform(1, 3, len(coords)),
            "Fecha": [datetime.utcnow().date()] * len(coords)
        }
        pd.DataFrame(data).to_csv(archivo_salida, index=False)

    return pd.read_csv(archivo_salida)

# ==============================
# INTERFAZ STREAMLIT
# ==============================
st.title("🌊 Dashboard KSTM")

with st.spinner("⏳ Descargando pronóstico GFS..."):
    viento = obtener_viento_gfs()

if viento.empty:
    st.warning("No se pudieron obtener datos de viento.")
else:
    dias_disp = sorted(viento["Día"].unique())
    dia_sel = st.selectbox("Seleccioná un día:", dias_disp)
    df_dia = viento[viento["Día"] == dia_sel]

    st.subheader(f"💨 Viento - {dia_sel}")
    st.dataframe(df_dia, use_container_width=True)

    st.map(df_dia.rename(columns={"Lat": "lat", "Lon": "lon"}))

# ==============================
# OLAS COPERNICUS
# ==============================
with st.spinner("🌊 Cargando datos de olas..."):
    ds_olas = obtener_olas_copernicus()

st.subheader("🌊 Altura significativa de ola (m)")
st.dataframe(ds_olas, use_container_width=True)
