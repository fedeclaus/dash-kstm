import streamlit as st
import pandas as pd
import numpy as np
import xarray as xr
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from copernicusmarine import login, subset

# ======================================
# CONFIGURACIÓN GENERAL
# ======================================
st.set_page_config(page_title="🌊 Dashboard Marítimo KS-TM", layout="wide")
st.title("🌊 Pronóstico Marítimo Integrado — Viento y Olas (KS-TM)")

st.markdown("""
Tablero integrado con pronóstico de **viento GFS (00Z)** y **altura significativa de ola (Copernicus Marine)**  
para los principales puertos del litoral argentino.
""")

# ======================================
# COORDENADAS DE PUERTOS
# ======================================
coords = {
    "Mar del Plata": (-38.03, -57.5),
    "Bahía Blanca": (-39.0, -61.9),
    "San Antonio": (-40.82, -64.8),
    "Puerto Madryn": (-42.7, -65.02),
    "Rawson": (-43.3, -65.14),
    "Comodoro Rivadavia": (-45.9, -67.38),
    "Caleta Olivia": (-46.45, -67.55),
    "Puerto Deseado": (-47.76, -65.87),
    "San Julián": (-49.30, -67.6),
    "Punta Quilla": (-50.11, -68.46),
    "Río Gallegos": (-51.6, -68.96),
}

# ======================================
# FUNCIONES AUXILIARES
# ======================================
def corregir_longitud(lon):
    return lon if lon >= 0 else 360 + lon

def viento_uv_a_direccion(u, v):
    return (270 - np.degrees(np.arctan2(v, u))) % 360

# ======================================
# FUNCIÓN: DESCARGAR VIENTO GFS
# ======================================
@st.cache_data(show_spinner=False)
def obtener_viento_gfs():
    base_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    fechas = [base_time + timedelta(hours=h) for h in [0, 24, 48, 72]]
    url = f"https://nomads.ncep.noaa.gov:9090/dods/gfs_0p25/gfs{base_time:%Y%m%d}/gfs_0p25_{base_time:%Hz}"

    st.info("💨 Descargando pronóstico GFS desde NOAA...")
    try:
        ds = xr.open_dataset(url)
    except Exception as e:
        st.error(f"No se pudo abrir el dataset GFS. Error:\n{e}")
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
        st.error("No se pudieron procesar datos GFS válidos.")
        return pd.DataFrame(columns=["Ciudad", "Tiempo UTC", "Velocidad [kt]", "Dirección [°]", "Lat", "Lon", "Día"])

    df = pd.DataFrame(filas)
    df["Día"] = pd.to_datetime(df["Tiempo UTC"]).dt.date
    return df

# ======================================
# FUNCIÓN: DESCARGAR OLAS COPERNICUS
# ======================================
@st.cache_data(show_spinner=False)
def obtener_olas_copernicus():
    st.info("🌊 Descargando pronóstico de olas Copernicus...")
    username = st.secrets["username"]
    password = st.secrets["password"]

    try:
        login(username=username, password=password, force_overwrite=True)
    except Exception as e:
        st.error(f"No se pudo autenticar con Copernicus: {e}")
        return None

    fecha_hoy = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    fecha_4d = fecha_hoy + timedelta(days=4)
    archivo_salida = "olas_atlantico_sur.nc"

    if not os.path.exists(archivo_salida):
        subset(
            dataset_id="cmems_mod_glo_wav_anfc_0.083deg_PT3H-i",
            variables=["VHM0"],
            minimum_longitude=-80,
            maximum_longitude=-50,
            minimum_latitude=-60,
            maximum_latitude=-33,
            start_datetime=fecha_hoy.isoformat(),
            end_datetime=fecha_4d.isoformat(),
            output_filename=archivo_salida
        )
    try:
        ds = xr.open_dataset(archivo_salida)
        return ds
    except Exception as e:
        st.error(f"No se pudo abrir el archivo de olas: {e}")
        return None

# ======================================
# DESCARGA DE DATOS
# ======================================
with st.spinner("🔄 Cargando datos meteorológicos..."):
    viento = obtener_viento_gfs()
    ds_olas = obtener_olas_copernicus()

if viento.empty or ds_olas is None:
    st.stop()

# ======================================
# SELECCIÓN DE DÍA
# ======================================
st.sidebar.header("🗓️ Día del pronóstico")
dias_disp = sorted(viento["Día"].unique())
dia_sel = st.sidebar.selectbox("Elegí el día a visualizar:", dias_disp)
df_dia = viento[viento["Día"] == dia_sel]

# Seleccionamos olas del mismo día
olas_dia = ds_olas["VHM0"].sel(time=slice(str(dia_sel), str(dia_sel + timedelta(days=1)))).max(dim="time")
lon = ds_olas["longitude"].values
lat = ds_olas["latitude"].values
X, Y = np.meshgrid(lon, lat)
Z = olas_dia.values

# ======================================
# MAPA INTERACTIVO
# ======================================
m = folium.Map(location=[-44, -63], zoom_start=5, tiles="cartodbpositron")

# Capas de olas
mask_3 = np.where(Z > 3, 1, np.nan)
mask_4 = np.where(Z > 4, 1, np.nan)
mask_6 = np.where(Z > 6, 1, np.nan)

def add_overlay(data, color, name):
    import io
    from PIL import Image
    fig, ax = plt.subplots(figsize=(6, 5))
    plt.contourf(X, Y, data, levels=[0.5, 1.5], colors=[color], alpha=0.4)
    plt.axis("off")
    buf = io.BytesIO()
    plt.savefig(buf, format="png", transparent=True, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    overlay = folium.raster_layers.ImageOverlay(
        image=Image.open(buf),
        bounds=[[-60, -80], [-33, -50]],
        name=name,
        opacity=0.5,
    )
    overlay.add_to(m)

add_overlay(mask_3, "yellow", ">3 m")
add_overlay(mask_4, "orange", ">4 m")
add_overlay(mask_6, "red", ">6 m")

# Marcadores de viento
def color_viento(v):
    if v > 30:
        return "red"
    elif v > 20:
        return "orange"
    else:
        return "green"

for _, r in df_dia.iterrows():
    folium.CircleMarker(
        location=[r["Lat"], r["Lon"]],
        radius=7,
        color=color_viento(r["Velocidad [kt]"]),
        fill=True,
        fill_color=color_viento(r["Velocidad [kt]"]),
        popup=folium.Popup(
            f"<b>{r['Ciudad']}</b><br>"
            f"Velocidad: {r['Velocidad [kt]']:.1f} kt<br>"
            f"Dirección: {r['Dirección [°]']:.0f}°",
            max_width=200,
        ),
    ).add_to(m)

folium.LayerControl().add_to(m)

st_folium(m, width=1200, height=700)

st.markdown("""
### 🧭 Leyenda
**Viento:** 🟢 ≤ 20 kt | 🟠 20–30 kt | 🔴 > 30 kt  
**Olas:** 🟡 > 3 m | 🟧 > 4 m | 🔴 > 6 m  
---
_Actualizado: {} UTC_
""".format(datetime.utcnow().strftime("%Y-%m-%d %H:%M")))
