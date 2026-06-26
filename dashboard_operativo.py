# -*- coding: utf-8 -*-
"""
Dashboard Operativo Electoral - Prototipo con datos ficticios
=============================================================
Ejecutar: streamlit run dashboard_operativo.py
"""
import os, io, csv, random, datetime, hashlib
from collections import defaultdict

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import pydeck as pdk

st.set_page_config(page_title="Tablero Operativo Electoral", page_icon="📊", layout="wide")

random.seed(42)
np.random.seed(42)
AHORA = datetime.datetime(2026, 6, 25, 20, 0, 0)
Dias = lambda n: AHORA - datetime.timedelta(days=n)

# ─────────────────────────────────────────────
#  MOCK DATA
# ─────────────────────────────────────────────
@st.cache_data
def generar_data():
    departamentos = [
        "AMAZONAS","ANCASH","APURIMAC","AREQUIPA","AYACUCHO","CAJAMARCA","CALLAO","CUSCO","HUANCAVELICA","HUANUCO",
        "ICA","JUNIN","LA LIBERTAD","LAMBAYEQUE","LIMA","LORETO","MADRE DE DIOS","MOQUEGUA","PASCO","PIURA","PUNO",
        "SAN MARTIN","TACNA","TUMBES","UCAYALI"
    ]
    jee_list = [f"JEE {d}" for d in departamentos[:12]] + ["JEE LIMA NORTE", "JEE LIMA SUR", "JEE LIMA ESTE", "JEE LIMA CENTRO"]
    odpe_list = [f"ODPE {d}" for d in departamentos[:18]]

    geo_rows = []
    local_id = 0
    mesa_id = 0
    for dept in departamentos:
        n_prov = random.randint(3, 9)
        provincias = [f"{dept[:4]}-P{i}" for i in range(1, n_prov + 1)]
        for prov in provincias:
            n_dist = random.randint(2, 6)
            for di in range(1, n_dist + 1):
                dist = f"{prov}-D{di}"
                n_locales = random.randint(1, 8)
                for li in range(1, n_locales + 1):
                    local_id += 1
                    n_mesas = random.randint(1, 15)
                    electores = n_mesas * random.randint(50, 300)
                    lat = -15 + random.uniform(-8, 8)
                    lon = -75 + random.uniform(-5, 5)
                    for mi in range(1, n_mesas + 1):
                        mesa_id += 1
                        geo_rows.append({
                            "id_local": local_id, "id_mesa": mesa_id,
                            "departamento": dept, "provincia": prov, "distrito": dist,
                            "local": f"IE {local_id} - {dist}", "cod_local": f"L{local_id:05d}",
                            "direccion": f"Av. {dist} {random.randint(100,9999)}",
                            "lat": round(lat + random.uniform(-0.02, 0.02), 6),
                            "lon": round(lon + random.uniform(-0.02, 0.02), 6),
                            "mesas": n_mesas, "electores": electores,
                            "jee": random.choice(jee_list),
                            "odpe": random.choice(odpe_list) if random.random() > 0.3 else "",
                        })
    df_geo = pd.DataFrame(geo_rows)
    df_local = df_geo[["id_local","local","cod_local","departamento","provincia","distrito",
                        "direccion","lat","lon","mesas","electores","jee","odpe"]].drop_duplicates("id_local").reset_index(drop=True)

    etapas_material = [
        ("Impresión", ["Cédula de sufragio","Relación de electores","Lista de electores","Acta padrón"]),
        ("Ensamblaje", ["Kit electoral completo"]),
        ("Despliegue a ODPE", ["Material ensamblado"]),
        ("Arribo a local", ["Material electoral"]),
        ("Verificación pública", ["Acta de verificación"]),
        ("Repliegue", ["Acta de repliegue"]),
    ]
    mat_rows = []
    for etapa_nombre, tipos in etapas_material:
        for _, loc in df_local.iterrows():
            for tipo in tipos:
                if random.random() > 0.15:
                    pct = random.randint(0, 100)
                    if pct >= 95:
                        estado = "Validado"
                    elif pct >= 70:
                        estado = "Completado"
                    elif pct >= 20:
                        estado = "En proceso"
                    else:
                        estado = "Pendiente"
                    mat_rows.append({
                        "id_local": loc["id_local"],
                        "etapa": etapa_nombre,
                        "tipo_material": tipo,
                        "cantidad_total": loc["mesas"],
                        "cantidad_procesada": int(loc["mesas"] * pct / 100),
                        "porcentaje": pct,
                        "estado": estado,
                        "fecha_inicio": Dias(random.randint(1, 30)).strftime("%d/%m/%Y %H:%M"),
                        "fecha_fin": Dias(random.randint(0, 5)).strftime("%d/%m/%Y %H:%M") if pct >= 50 else "",
                        "responsable": f"Resp-{random.randint(100,999)}",
                    })
    df_mat = pd.DataFrame(mat_rows)

    etapas_jornada = ["Instalación","Sufragio","Escrutinio"]
    est_jorn = ["Pendiente","En proceso","Completado","Con incidencia"]
    jorn_rows = []
    for _, loc in df_local.iterrows():
        for etapa in etapas_jornada:
            for mi in range(1, min(loc["mesas"], 6) + 1):
                if random.random() > 0.2:
                    estado = random.choices(est_jorn, weights=[20,15,50,15])[0]
                    hora_ini = Dias(random.randint(0, 3)).strftime("%d/%m/%Y %H:%M") if estado != "Pendiente" else ""
                    hora_fin = Dias(random.randint(0, 1)).strftime("%d/%m/%Y %H:%M") if estado == "Completado" else ""
                    jorn_rows.append({
                        "id_local": loc["id_local"],
                        "id_mesa": loc["id_local"] * 100 + mi,
                        "etapa": etapa,
                        "estado": estado,
                        "hora_inicio": hora_ini,
                        "hora_cierre": hora_fin,
                        "electores_mesa": random.randint(50, 300),
                        "incidencia": random.choice(["Ninguna","Retraso","Falta material","Conflicto","Ninguna","Ninguna"]),
                        "responsable": f"Coord-{random.randint(100,999)}",
                    })
    df_jorn = pd.DataFrame(jorn_rows)

    fisc_rows = []
    for _, loc in df_local.sample(frac=0.6).iterrows():
        n_fisc = random.randint(1, 3)
        for fi in range(n_fisc):
            cubierto = random.random() > 0.25
            fisc_rows.append({
                "id_local": loc["id_local"],
                "cod_fiscalizador": f"F{random.randint(1000,9999)}",
                "nombre": f"Fiscalizador {random.randint(100,999)}",
                "hora_inicio": Dias(random.randint(0, 2)).strftime("%d/%m/%Y %H:%M") if cubierto else "",
                "hora_cierre": Dias(random.randint(0, 1)).strftime("%d/%m/%Y %H:%M") if cubierto and random.random() > 0.5 else "",
                "estado_cobertura": "Cubierto" if cubierto else "No cubierto",
                "observaciones": "" if cubierto else "Sin registro de cobertura",
            })
    df_fisc = pd.DataFrame(fisc_rows)

    tipos_actor = ["Personal ONPE","Personeros","FFAA/PNP","Instituciones públicas"]
    actor_rows = []
    for _, loc in df_local.iterrows():
        for ta in tipos_actor:
            if random.random() > 0.3:
                asignado = random.randint(1, 6)
                registrado = random.randint(0, asignado)
                actor_rows.append({
                    "id_local": loc["id_local"],
                    "tipo_actor": ta,
                    "asignados": asignado,
                    "registrados": registrado,
                    "cobertura_pct": round(registrado / asignado * 100, 1) if asignado else 0,
                })
    df_actores = pd.DataFrame(actor_rows)

    categorias_alerta = ["Logística","Seguridad","Personal","Material","Otros"]
    riesgos = ["Leve","Moderado","Grave"]
    est_alertas = ["Pendiente","Validado","Registrado","Eliminado","Atendido"]
    alerta_rows = []
    for i in range(500):
        loc = df_local.sample(1).iloc[0]
        alerta_rows.append({
            "id_alerta": f"AL-{i+1:04d}",
            "categoria": random.choice(categorias_alerta),
            "riesgo": random.choices(riesgos, weights=[50,30,20])[0],
            "estado": random.choices(est_alertas, weights=[25,30,25,5,15])[0],
            "fecha_hora": Dias(random.randint(0, 7)).strftime("%d/%m/%Y %H:%M"),
            "departamento": loc["departamento"],
            "provincia": loc["provincia"],
            "distrito": loc["distrito"],
            "local": loc["local"],
            "id_local": loc["id_local"],
            "descripcion": f"Incidencia de tipo {random.choice(categorias_alerta)} en {loc['local']}",
            "responsable": f"JE-{random.randint(10,99)}",
            "accion": random.choice(["En evaluación","Derivado a ODPE","Atendido in situ","Pendiente de acción","Cerrado"]),
            "modulo_asociado": random.choice(["Material electoral","Jornada electoral","Otras actividades"]),
            "lat": loc["lat"],
            "lon": loc["lon"],
        })
    df_alertas = pd.DataFrame(alerta_rows)

    act_nombres = ["Capacitación a miembros de mesa","Publicación de cartel de candidatos",
                   "Publicación de local de votación","Propaganda electoral","Expendio de bebidas alcohólicas"]
    est_act = ["Pendiente","Realizado","No realizado","Con observación"]
    act_rows = []
    for _, loc in df_local.sample(frac=0.5).iterrows():
        for act in act_nombres:
            if random.random() > 0.35:
                act_rows.append({
                    "id_local": loc["id_local"],
                    "actividad": act,
                    "estado": random.choice(est_act),
                    "fecha_hora": Dias(random.randint(0, 10)).strftime("%d/%m/%Y %H:%M"),
                    "responsable": f"Fisc-{random.randint(100,999)}",
                    "observaciones": random.choice(["Sin novedad","Se realizó conforme","Pendiente de programación","Conforme"]) if random.random() > 0.5 else "",
                    "evidencia": "foto_" + hashlib.md5(str(random.random()).encode()).hexdigest()[:8] + ".jpg" if random.random() > 0.5 else "",
                })
    df_actividades = pd.DataFrame(act_rows)

    return df_geo, df_local, df_mat, df_jorn, df_fisc, df_actores, df_alertas, df_actividades

# ─────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────
st.markdown("""
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
<style>
    .stApp { background: #f8f9fa; color: #212529; }
    .block-container { max-width: 100%; padding: 0.5rem 2rem; }
    h1, h2, h3, h4, h5, h6 { color: #1a1a2e !important; }
    p { color: #495057; }
    [data-testid="stSidebar"] { background: #ffffff !important; border-right: 1px solid #e9ecef; }
    [data-testid="stSidebar"] > div:first-child { padding: 0.5rem 0.8rem !important; }
    [data-testid="stSidebar"] .sidebar-header { background: linear-gradient(135deg,#1a1a2e,#16213e); color: white; padding: 1rem; text-align: center; border-radius: 10px; margin-bottom: 0.8rem; }
    [data-testid="stSidebar"] .sidebar-header h2 { color: white !important; font-size: 1rem; margin: 0; letter-spacing: 0; text-transform: none; padding: 0; }
    [data-testid="stSidebar"] .sidebar-header small { color: #8a9bb5; font-size: 0.65rem; }
    div.stButton > button { width: 100%; text-align: left; background: transparent; border: 1px solid #e9ecef; border-radius: 8px; padding: 0.5rem 0.8rem; color: #495057 !important; font-size: 0.85rem; transition: 0.12s; }
    div.stButton > button:hover { background: #f1f3f5; border-color: #1a73e8; color: #1a73e8 !important; }
    div.stButton > button[kind="primary"] { background: #e8f0fe; border-color: #1a73e8; color: #1a73e8 !important; font-weight: 600; }
    div.stButton > button p { font-size: 0.85rem; margin: 0; }
    div.row-widget.stButton { margin-bottom: 0.15rem; }
    .kpi-card { background: white; border: 1px solid #e9ecef; border-radius: 10px; padding: 0.8rem; text-align: center; transition: 0.15s; height: 100%; box-shadow: 0 1px 2px rgba(0,0,0,0.03); }
    .kpi-card:hover { border-color: #1a73e8; box-shadow: 0 3px 10px rgba(26,115,232,0.06); }
    .kpi-icon { font-size: 1.3rem; margin-bottom: 0.2rem; }
    .kpi-value { font-size: 1.4rem; font-weight: 700; color: #1a1a2e; }
    .kpi-label { font-size: 0.7rem; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.15rem; }
    .kpi-pct { font-size: 0.75rem; font-weight: 600; margin-top: 0.15rem; }
    .pct-green { color: #198754; } .pct-yellow { color: #ffc107; } .pct-red { color: #dc3545; }
    .pct-blue { color: #1a73e8; }
    .stat-box { background: white; border: 1px solid #e9ecef; border-radius: 7px; padding: 0.5rem 0.7rem; margin-bottom: 0.35rem; }
    .stat-label { font-size: 0.7rem; color: #6c757d; }
    .stat-value { font-size: 0.95rem; font-weight: 600; color: #1a1a2e; }
    .stDataFrame { font-size: 0.78rem; }
    .stDataFrame thead th { background: #f8f9fa !important; color: #495057 !important; font-weight: 600; }
    .stTabs [data-baseweb="tab-list"] { gap: 0.2rem; background: #f8f9fa; padding: 0.25rem; border-radius: 7px; }
    .stTabs [data-baseweb="tab"] { border-radius: 5px; padding: 0.35rem 0.7rem; color: #6c757d; font-size: 0.8rem; }
    .stTabs [aria-selected="true"] { background: white; color: #1a73e8; font-weight: 600; box-shadow: 0 1px 2px rgba(0,0,0,0.06); }
    .footer { text-align: center; padding: 0.8rem 0; color: #adb5bd; font-size: 0.7rem; }
    div[data-testid="stMetricValue"] { font-size: 1.4rem !important; color: #1a1a2e !important; }
    div[data-testid="stMetricLabel"] { font-size: 0.7rem !important; color: #6c757d !important; }
    .stPyDeck iframe { border-radius: 8px; border: 1px solid #e9ecef; }
    .stSelectbox label { font-size: 0.75rem !important; color: #6c757d !important; }
    .stSelectbox div[data-baseweb="select"] > div { min-height: 2rem; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  SESIÓN
# ─────────────────────────────────────────────
if "modulo" not in st.session_state:
    st.session_state.modulo = "Inicio"

# ─────────────────────────────────────────────
#  SIDEBAR NAV
# ─────────────────────────────────────────────
def sidebar_nav():
    st.sidebar.markdown("""
    <div class="sidebar-header">
        <h2>📊 Tablero Operativo</h2>
        <small>Electoral - Prototipo</small>
    </div>
    """, unsafe_allow_html=True)

    for icono, label, key in [
        ("🏠", "Inicio", "Inicio"),
        ("📦", "Material Electoral", "Material"),
        ("🗳️", "Jornada Electoral", "Jornada"),
        ("📋", "Otras Actividades", "Actividades"),
        ("⚠️", "Alertas FLV", "Alertas"),
    ]:
        activo = st.session_state.modulo == key
        if st.sidebar.button(f"{icono} {label}", key=f"nav_{key}",
                             type="primary" if activo else "secondary",
                             use_container_width=True):
            st.session_state.modulo = key
            st.rerun()

# ─────────────────────────────────────────────
#  FILTROS (sidebar)
# ─────────────────────────────────────────────
def filtros_globales(df_local, df_mat, df_jorn, df_fisc, df_actores, df_alertas, df_actividades):
    st.sidebar.markdown("## 🔍 Filtros")

    pais = st.sidebar.selectbox("País", ["Perú"], key="filtro_pais")
    proceso = st.sidebar.selectbox("Proceso", ["ERM 2026", "EG 2026"], key="filtro_proceso")

    jee_opts = ["Todos"] + sorted(df_local["jee"].unique())
    jee_sel = st.sidebar.selectbox("JEE/ODPE", jee_opts, key="filtro_jee")

    dept_opts = ["Todos"] + sorted(df_local["departamento"].unique())
    dept_sel = st.sidebar.selectbox("Departamento", dept_opts, key="filtro_dept")

    prov_opts = ["Todas"]
    if dept_sel == "Todos":
        prov_opts += sorted(df_local["provincia"].unique())
    else:
        prov_opts += sorted(df_local[df_local["departamento"] == dept_sel]["provincia"].unique())
    prov_sel = st.sidebar.selectbox("Provincia", prov_opts, key="filtro_prov")

    dist_opts = ["Todos"]
    if dept_sel == "Todos" and prov_sel == "Todas":
        dist_opts += sorted(df_local["distrito"].unique())
    elif prov_sel != "Todas":
        dist_opts += sorted(df_local[df_local["provincia"] == prov_sel]["distrito"].unique())
    else:
        dist_opts += sorted(df_local[df_local["departamento"] == dept_sel]["distrito"].unique())
    dist_sel = st.sidebar.selectbox("Distrito", dist_opts, key="filtro_dist")

    mask = pd.Series([True] * len(df_local))
    if jee_sel != "Todos":
        mask &= df_local["jee"] == jee_sel
    if dept_sel != "Todos":
        mask &= df_local["departamento"] == dept_sel
    if prov_sel != "Todas":
        mask &= df_local["provincia"] == prov_sel
    if dist_sel != "Todos":
        mask &= df_local["distrito"] == dist_sel

    local_opts = ["Todos"] + sorted(df_local[mask]["local"].tolist())
    local_sel = st.sidebar.selectbox("Local de votación", local_opts, key="filtro_local")

    todos_estados = sorted(set(
        list(df_mat["estado"].unique()) + list(df_jorn["estado"].unique()) +
        list(df_alertas["estado"].unique()) + list(df_actividades["estado"].unique())
    ))
    est_sel = st.sidebar.selectbox("Estado", ["Todos"] + todos_estados, key="filtro_estado")
    riesgo_sel = st.sidebar.selectbox("Riesgo", ["Todos", "Leve", "Moderado", "Grave"], key="filtro_riesgo")

    st.sidebar.markdown("<hr style='margin:0.5rem 0;border-color:#e9ecef;'>")
    st.sidebar.markdown("<small style='color:#adb5bd;font-size:0.65rem;'>Datos ficticios · v1.0</small>", unsafe_allow_html=True)

    loc_ids = df_local[mask]["id_local"].tolist() if local_sel == "Todos" else df_local[df_local["local"] == local_sel]["id_local"].tolist()

    mask_mat = df_mat["id_local"].isin(loc_ids) if loc_ids else pd.Series(False, index=df_mat.index)
    if est_sel != "Todos":
        mask_mat &= df_mat["estado"] == est_sel

    mask_jorn = df_jorn["id_local"].isin(loc_ids) if loc_ids else pd.Series(False, index=df_jorn.index)
    if est_sel != "Todos":
        mask_jorn &= df_jorn["estado"] == est_sel

    mask_fisc = df_fisc["id_local"].isin(loc_ids) if loc_ids else pd.Series(False, index=df_fisc.index)

    mask_actores = df_actores["id_local"].isin(loc_ids) if loc_ids else pd.Series(False, index=df_actores.index)

    mask_alertas = df_alertas["id_local"].isin(loc_ids) if loc_ids else pd.Series(False, index=df_alertas.index)
    if est_sel != "Todos":
        mask_alertas &= df_alertas["estado"] == est_sel
    if riesgo_sel != "Todos":
        mask_alertas &= df_alertas["riesgo"] == riesgo_sel

    mask_act = df_actividades["id_local"].isin(loc_ids) if loc_ids else pd.Series(False, index=df_actividades.index)
    if est_sel != "Todos":
        mask_act &= df_actividades["estado"] == est_sel

    return (pais, df_local[mask], df_mat[mask_mat], df_jorn[mask_jorn],
            df_fisc[mask_fisc], df_actores[mask_actores],
            df_alertas[mask_alertas], df_actividades[mask_act])

# ─────────────────────────────────────────────
#  UI HELPERS
# ─────────────────────────────────────────────
def kpi_card(icon, value, label, pct=None, pct_color="blue"):
    extra = ""
    if pct is not None:
        cls = {"green":"pct-green","yellow":"pct-yellow","red":"pct-red","blue":"pct-blue"}.get(pct_color, "pct-blue")
        extra = f'<div class="kpi-pct {cls}">{pct:.1f}%</div>'
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-value">{value:,}</div>
        <div class="kpi-label">{label}</div>
        {extra}
    </div>
    """, unsafe_allow_html=True)

def barra_progreso(pct, color="#1a73e8"):
    st.markdown(f"""
    <div class="progress" style="height:8px;background:#e9ecef;border-radius:4px;">
        <div class="progress-bar" style="width:{min(pct,100)}%;background:{color};border-radius:4px;"></div>
    </div>
    """, unsafe_allow_html=True)

def exportar_csv(df, nombre):
    csv_data = io.BytesIO()
    df.to_csv(csv_data, index=False, encoding="utf-8-sig", sep=";")
    csv_data.seek(0)
    st.download_button(
        label=f"📥 Exportar {nombre}",
        data=csv_data,
        file_name=f"{nombre}_{AHORA.strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        key=f"exp_{nombre}",
    )

def pagina_segura(func):
    def wrapper(*a, **kw):
        try:
            func(*a, **kw)
        except Exception as e:
            st.error(f"Error al cargar la página: {e}")
    wrapper.__name__ = func.__name__
    return wrapper

# ─────────────────────────────────────────────
#  MAPA
# ─────────────────────────────────────────────
PERU_CENTROIDES = {
    "AMAZONAS":(-5.0,-78.0),"ANCASH":(-9.5,-77.5),"APURIMAC":(-14.0,-73.0),"AREQUIPA":(-16.0,-72.0),
    "AYACUCHO":(-13.0,-74.0),"CAJAMARCA":(-7.0,-78.5),"CALLAO":(-12.0,-77.1),"CUSCO":(-13.5,-72.0),
    "HUANCAVELICA":(-13.0,-75.0),"HUANUCO":(-9.9,-76.0),"ICA":(-14.0,-75.5),"JUNIN":(-11.5,-75.0),
    "LA LIBERTAD":(-8.0,-78.5),"LAMBAYEQUE":(-6.5,-79.5),"LIMA":(-12.0,-77.0),"LORETO":(-4.0,-74.0),
    "MADRE DE DIOS":(-12.0,-70.0),"MOQUEGUA":(-17.0,-71.0),"PASCO":(-10.5,-76.0),"PIURA":(-5.0,-80.5),
    "PUNO":(-15.5,-70.0),"SAN MARTIN":(-7.0,-76.5),"TACNA":(-18.0,-70.5),"TUMBES":(-3.5,-80.5),
    "UCAYALI":(-9.0,-75.0)
}

@st.cache_data
def _preparar_mapa(df, metric="mesas"):
    agg = df.groupby("departamento").agg(
        total=(metric, "sum"),
        locales=("id_local", "nunique"),
    ).reset_index()
    rows = []
    for _, r in agg.iterrows():
        nom = r["departamento"].upper().strip()
        lat, lon = PERU_CENTROIDES.get(nom, (-12.0, -75.0))
        rows.append({
            "departamento": nom,
            "lat": lat, "lon": lon,
            "total": int(r["total"]),
            "locales": int(r["locales"]),
            "radio": max(int(r["total"]), 1),
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame()

def mapa_pydeck(df, metric="mesas"):
    data = _preparar_mapa(df, metric)
    if data.empty:
        return None
    max_radio = data["radio"].max() or 1
    data["radio_px"] = (data["radio"] / max_radio * 50 + 10).clip(8, 60)

    capa = pdk.Layer(
        "ScatterplotLayer", data=data,
        get_position='[lon, lat]',
        get_radius="radio_px * 1000",
        get_fill_color=[59, 130, 246, 180],
        get_line_color=[255,255,255],
        get_line_width=3, pickable=True,
        radius_min_pixels=8, radius_max_pixels=60,
    )
    return pdk.Deck(
        layers=[capa],
        initial_view_state=pdk.ViewState(latitude=-9.5, longitude=-75.0, zoom=4.5, pitch=0),
        tooltip={"html":"<b>{departamento}</b><br>"+metric+": {total}<br>Locales: {locales}",
                 "style":{"backgroundColor":"#1a1c23","color":"white"}},
        map_style="light",
    )

def mapa_pydeck_puntos(df, lat_col="lat", lon_col="lon", color_col="estado", size_col=None):
    color_map = {"Pendiente":[239,68,68],"En proceso":[234,179,8],"Completado":[34,197,94],
                 "Validado":[59,130,246],"Con incidencia":[249,115,22],"Cubierto":[34,197,94],
                 "No cubierto":[239,68,68],"Leve":[59,130,246],"Moderado":[234,179,8],"Grave":[239,68,68]}
    if df.empty:
        return None
    data = df.copy()
    if size_col and size_col in data.columns:
        mx = data[size_col].max() or 1
        data["radio"] = (data[size_col] / mx * 40 + 5).clip(3, 50)
    else:
        data["radio"] = 12
    data["color_rgb"] = data[color_col].apply(
        lambda x: color_map.get(str(x).strip(), [100,130,180])
    ) if color_col in data.columns else [[100,130,180]] * len(data)

    capa = pdk.Layer(
        "ScatterplotLayer", data=data,
        get_position='[lon, lat]',
        get_radius="radio * 500",
        get_fill_color="color_rgb",
        get_line_color=[255,255,255], get_line_width=1, pickable=True,
        radius_min_pixels=4, radius_max_pixels=40,
    )
    return pdk.Deck(
        layers=[capa],
        initial_view_state=pdk.ViewState(latitude=-9.5, longitude=-75.0, zoom=4.5, pitch=0),
        tooltip={"text": "{local}" if "local" in data.columns else "{departamento}"},
        map_style="light",
    )

# ─────────────────────────────────────────────
#  PÁGINAS
# ─────────────────────────────────────────────
def pagina_inicio(df_local, pais):
    st.markdown("""
    <div style="text-align:center;padding:1.5rem 0 0.5rem;">
        <h1 style="font-size:2rem;color:#1a1a2e;">📊 Tablero Operativo Electoral</h1>
        <p style="color:#6c757d;font-size:1rem;max-width:600px;margin:0 auto;">
            Monitoreo de material electoral, jornada electoral y otras actividades de fiscalización
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1: kpi_card("🏛️", len(df_local), "Locales de votación")
    with col2: kpi_card("📋", int(df_local["mesas"].sum()), "Mesas instaladas")
    with col3: kpi_card("👥", int(df_local["electores"].sum()), "Electores hábiles")
    with col4: kpi_card("🗺️", df_local['departamento'].nunique(), "Departamentos")

    st.markdown(f"## Cobertura nacional — {pais}")
    r = mapa_pydeck(df_local)
    if r: st.pydeck_chart(r, key="map_inicio")

    st.markdown('<div class="footer">Prototipo - Dashboard Operativo Electoral v1.0</div>', unsafe_allow_html=True)

@pagina_segura
def pagina_material(df_local, df_mat):
    st.markdown("## 📦 Material Electoral")
    st.markdown("Monitoreo del avance de material electoral por etapa")

    etapas = ["Impresión","Ensamblaje","Despliegue a ODPE","Arribo a local","Verificación pública","Repliegue"]
    tabs = st.tabs([f"{i+1}. {e}" for i, e in enumerate(etapas)])

    for idx, etapa in enumerate(etapas):
        with tabs[idx]:
            df_etapa = df_mat[df_mat["etapa"] == etapa]
            if df_etapa.empty:
                st.info(f"No hay registros para la etapa {etapa}")
            else:
                total = len(df_etapa)
                completado = len(df_etapa[df_etapa["estado"].isin(["Completado","Validado"])])
                en_proceso = len(df_etapa[df_etapa["estado"] == "En proceso"])
                pendiente = len(df_etapa[df_etapa["estado"] == "Pendiente"])
                pct_avance = completado / total * 100 if total else 0

                k1, k2, k3, k4 = st.columns(4)
                with k1: kpi_card("📋", total, "Total registros")
                with k2: kpi_card("✅", completado, "Completado", pct_avance, "green")
                with k3: kpi_card("🔄", en_proceso, "En proceso", en_proceso/total*100 if total else 0, "yellow")
                with k4: kpi_card("⏳", pendiente, "Pendiente", pendiente/total*100 if total else 0, "red")

                st.markdown("### Avance por tipo de material")
                tipos = df_etapa.groupby("tipo_material").agg(
                    total=("cantidad_total","sum"),
                    procesado=("cantidad_procesada","sum"),
                ).reset_index()
                denom = tipos["total"].replace(0, 1)
                tipos["pct"] = (tipos["procesado"] / denom * 100).round(1)

                c1, c2 = st.columns([2, 1])
                with c1:
                    fig = px.bar(tipos, x="tipo_material", y="pct",
                                 color="pct", color_continuous_scale=["#ef4444","#eab308","#22c55e"],
                                 range_color=[0,100], text=tipos["pct"].apply(lambda x: f"{x:.1f}%"),
                                 custom_data=[tipos["procesado"], tipos["total"]],
                                 labels={"tipo_material":"", "pct":"%"})
                    fig.update_traces(textposition="outside",
                                     hovertemplate="<b>%{x}</b><br>Avance: %{y:.1f}%<br>Proc: %{customdata[0]}/%{customdata[1]}<extra></extra>")
                    fig.update_layout(height=300, margin=dict(t=30,b=20,l=10,r=10),
                                      paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                                      font=dict(color="#495057"),
                                      xaxis=dict(tickfont=dict(size=10)),
                                      yaxis=dict(range=[0,105], title="%"),
                                      coloraxis_showscale=False)
                    st.plotly_chart(fig, width='stretch', key=f"bar_mat_{etapa}")

                with c2:
                    st.markdown("### Resumen")
                    st.markdown(f"""
                    <div class="stat-box"><div class="stat-label">Total</div><div class="stat-value">{int(tipos['total'].sum()):,}</div></div>
                    <div class="stat-box"><div class="stat-label">Procesado</div><div class="stat-value">{int(tipos['procesado'].sum()):,}</div></div>
                    <div class="stat-box"><div class="stat-label">Avance</div><div class="stat-value">{pct_avance:.1f}%</div></div>
                    """, unsafe_allow_html=True)
                    barra_progreso(pct_avance)

                st.markdown("### Detalle por local")
                det = df_etapa.groupby("id_local").agg(
                    total=("cantidad_total","sum"),
                    procesado=("cantidad_procesada","sum"),
                    estado=("estado","first"),
                ).reset_index()
                det["pct"] = (det["procesado"] / det["total"].replace(0, 1) * 100).round(1)
                det = det.merge(df_local[["id_local","local","departamento","provincia"]], on="id_local", how="left")

                c1, c2 = st.columns([3, 2])
                with c1:
                    cols = [c for c in ["local","departamento","provincia","total","procesado","pct","estado"] if c in det.columns]
                    st.dataframe(det[cols].head(100), width='stretch', hide_index=True,
                                 column_config={"pct": st.column_config.NumberColumn("%", format="%.1f")})
                    exportar_csv(det, f"material_{etapa.replace(' ','_')}")
                with c2:
                    if not det.empty:
                        r = mapa_pydeck_puntos(
                            det.merge(df_local[["id_local","lat","lon"]], on="id_local"),
                            "lat","lon","estado", None)
                        if r: st.pydeck_chart(r, key=f"map_mat_{etapa}")

@pagina_segura
def pagina_jornada(df_local, df_jorn, df_fisc, df_actores):
    st.markdown("## 🗳️ Jornada Electoral")
    st.markdown("Seguimiento de instalación, sufragio, escrutinio, fiscalizadores y actores")

    total_locales = len(df_local)
    total_registros = len(df_jorn)
    completados = len(df_jorn[df_jorn["estado"] == "Completado"])
    incidencias = len(df_jorn[df_jorn["incidencia"] != "Ninguna"])

    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi_card("🏛️", total_locales, "Locales")
    with k2: kpi_card("📋", total_registros, "Registros jornada")
    with k3: kpi_card("✅", completados, "Completados", completados/total_registros*100 if total_registros else 0, "green")
    with k4: kpi_card("⚠️", incidencias, "Con incidencias", incidencias/total_registros*100 if total_registros else 0, "red")

    tabs = st.tabs(["Instalación","Sufragio","Escrutinio","Fiscalizadores","Actores presentes"])

    for idx, etapa in enumerate(["Instalación","Sufragio","Escrutinio"]):
        with tabs[idx]:
            df_et = df_jorn[df_jorn["etapa"] == etapa]
            if df_et.empty:
                st.info(f"Sin datos para {etapa}")
            else:
                total_e = len(df_et)
                comp = len(df_et[df_et["estado"] == "Completado"])
                proc = len(df_et[df_et["estado"] == "En proceso"])
                incid = len(df_et[df_et["incidencia"] != "Ninguna"])

                e1, e2, e3, e4 = st.columns(4)
                with e1: kpi_card("📋", total_e, "Total")
                with e2: kpi_card("✅", comp, "Completado", comp/total_e*100 if total_e else 0, "green")
                with e3: kpi_card("🔄", proc, "En proceso", proc/total_e*100 if total_e else 0, "yellow")
                with e4: kpi_card("⚠️", incid, "Incidencias", incid/total_e*100 if total_e else 0, "red")

                det = df_et.groupby("id_local").agg(
                    total=("id_mesa","count"),
                    completados=("estado", lambda x: (x == "Completado").sum()),
                    incidencias=("incidencia", lambda x: (x != "Ninguna").sum()),
                ).reset_index()
                det = det.merge(df_local[["id_local","local","departamento","provincia","lat","lon"]], on="id_local", how="left")

                c1, c2 = st.columns([3, 2])
                with c1:
                    st.dataframe(det.head(100), width='stretch', hide_index=True,
                                 column_config={"total":"Mesas","completados":"Completadas","incidencias":"Incidencias"})
                    exportar_csv(det, f"jornada_{etapa.lower()}")
                with c2:
                    if not det.empty:
                        r = mapa_pydeck_puntos(det, "lat","lon","incidencias", "total")
                        if r: st.pydeck_chart(r, key=f"map_jor_{etapa}")

                st.markdown("### Incidencias registradas")
                df_inc = df_et[df_et["incidencia"] != "Ninguna"].head(50)
                if not df_inc.empty:
                    st.dataframe(df_inc[["id_mesa","incidencia","estado","hora_inicio","responsable"]],
                                 width='stretch', hide_index=True)

    with tabs[3]:
        st.markdown("### Fiscalizadores asignados y desplegados")
        if df_fisc.empty:
            st.info("Sin datos de fiscalizadores")
        else:
            total_fisc = len(df_fisc)
            cubiertos = len(df_fisc[df_fisc["estado_cobertura"] == "Cubierto"])
            pct_cob = cubiertos / total_fisc * 100 if total_fisc else 0

            f1, f2, f3 = st.columns(3)
            with f1: kpi_card("🕵️", total_fisc, "Fiscalizadores")
            with f2: kpi_card("✅", cubiertos, "Cobertura", pct_cob, "green")
            with f3: kpi_card("❌", total_fisc - cubiertos, "Sin cobertura", 100 - pct_cob, "red")

            fisc_agg = df_fisc.groupby("id_local").agg(
                total=("cod_fiscalizador","count"),
                cubiertos=("estado_cobertura", lambda x: (x == "Cubierto").sum()),
            ).reset_index()
            fisc_agg = fisc_agg.merge(df_local[["id_local","local","departamento","lat","lon"]], on="id_local", how="left")

            c1, c2 = st.columns([3, 2])
            with c1:
                fisc_agg["pct_cob"] = (fisc_agg["cubiertos"] / fisc_agg["total"].replace(0, 1) * 100).round(1)
                st.dataframe(fisc_agg[["local","departamento","total","cubiertos","pct_cob"]].head(100),
                             width='stretch', hide_index=True)
                exportar_csv(fisc_agg, "fiscalizadores")
            with c2:
                if not fisc_agg.empty:
                    r = mapa_pydeck_puntos(fisc_agg, "lat","lon","cubiertos", "total")
                    if r: st.pydeck_chart(r, key="map_fisc")

    with tabs[4]:
        st.markdown("### Actores presentes en locales de votación")
        if df_actores.empty:
            st.info("Sin datos de actores")
        else:
            res_act = df_actores.groupby("tipo_actor").agg(
                asignados=("asignados","sum"),
                registrados=("registrados","sum"),
            ).reset_index()
            res_act["cobertura"] = (res_act["registrados"] / res_act["asignados"].replace(0, 1) * 100).round(1)

            cols_a = st.columns(len(res_act))
            for i, (_, r) in enumerate(res_act.iterrows()):
                with cols_a[i]:
                    kpi_card("👤", int(r["registrados"]), r["tipo_actor"], r["cobertura"], "green")

            st.dataframe(res_act, width='stretch', hide_index=True,
                         column_config={"cobertura": st.column_config.NumberColumn("Cobertura %", format="%.1f")})

@pagina_segura
def pagina_actividades(df_local, df_actividades):
    st.markdown("## 📋 Otras Actividades de Fiscalización")
    st.markdown("Monitoreo de capacitación, carteles, propaganda y más")

    actividades = df_actividades["actividad"].unique()
    if len(actividades) == 0:
        st.info("No hay actividades registradas")
        return

    tabs = st.tabs([(a[:18] + "...") if len(a) > 18 else a for a in actividades])

    for idx, act in enumerate(actividades):
        with tabs[idx]:
            df_act = df_actividades[df_actividades["actividad"] == act]
            if df_act.empty:
                st.info(f"Sin datos para {act}")
            else:
                total_a = len(df_act)
                realizados = len(df_act[df_act["estado"] == "Realizado"])
                pendientes = len(df_act[df_act["estado"] == "Pendiente"])
                pct = realizados / total_a * 100 if total_a else 0

                a1, a2, a3, a4 = st.columns(4)
                with a1: kpi_card("📋", total_a, "Total")
                with a2: kpi_card("✅", realizados, "Realizado", pct, "green")
                with a3: kpi_card("⏳", pendientes, "Pendiente", pendientes/total_a*100 if total_a else 0, "red")
                with a4: kpi_card("📸", int(df_act["evidencia"].notna().sum()), "Con evidencia")

                det_act = df_act.merge(df_local[["id_local","local","departamento","provincia"]], on="id_local", how="left")
                cols = [c for c in ["local","departamento","provincia","estado","fecha_hora","responsable","observaciones"] if c in det_act.columns]
                st.dataframe(det_act[cols].head(100), width='stretch', hide_index=True)
                exportar_csv(det_act, f"actividad_{idx}")

@pagina_segura
def pagina_alertas(df_alertas, df_local):
    st.markdown("## ⚠️ Alertas e Incidencias FLV")
    st.markdown("Panel transversal de consulta, seguimiento y detalle de incidencias")

    total_al = len(df_alertas)
    pendientes = len(df_alertas[df_alertas["estado"] == "Pendiente"])
    graves = len(df_alertas[df_alertas["riesgo"] == "Grave"])
    atendidas = len(df_alertas[df_alertas["estado"].isin(["Atendido","Validado"])])
    eliminadas = len(df_alertas[df_alertas["estado"] == "Eliminado"])

    a1, a2, a3, a4, a5 = st.columns(5)
    with a1: kpi_card("⚠️", total_al, "Total alertas")
    with a2: kpi_card("⏳", pendientes, "Pendientes", pendientes/total_al*100 if total_al else 0, "red")
    with a3: kpi_card("🔴", graves, "Graves", graves/total_al*100 if total_al else 0, "red")
    with a4: kpi_card("✅", atendidas, "Atendidas", atendidas/total_al*100 if total_al else 0, "green")
    with a5: kpi_card("🗑️", eliminadas, "Eliminadas")

    c1, c2 = st.columns(2)
    with c1:
        if not df_alertas.empty:
            fig = px.pie(df_alertas, names="estado", title="Por estado", color_discrete_sequence=px.colors.qualifier.Set3)
            fig.update_layout(paper_bgcolor="#ffffff", font=dict(color="#495057"), title=dict(font=dict(color="#1a1a2e")))
            st.plotly_chart(fig, width='stretch', key="pie_alert_estado")
    with c2:
        if not df_alertas.empty:
            fig = px.pie(df_alertas, names="riesgo", title="Por riesgo", color="riesgo",
                         color_discrete_map={"Leve":"#3b82f6","Moderado":"#eab308","Grave":"#ef4444"})
            fig.update_layout(paper_bgcolor="#ffffff", font=dict(color="#495057"), title=dict(font=dict(color="#1a1a2e")))
            st.plotly_chart(fig, width='stretch', key="pie_alert_riesgo")

    st.markdown("### Tendencia de alertas (últimos 7 días)")
    if not df_alertas.empty:
        df_alertas["fecha_dt"] = pd.to_datetime(df_alertas["fecha_hora"], format="%d/%m/%Y %H:%M", errors="coerce")
        trend = df_alertas.groupby(df_alertas["fecha_dt"].dt.date).size().reset_index(name="cantidad")
        if not trend.empty:
            fig = px.line(trend, x="fecha_dt", y="cantidad", markers=True, title="Evolución diaria", line_shape="spline")
            fig.update_layout(paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                              font=dict(color="#495057"), title=dict(font=dict(color="#1a1a2e")),
                              xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#e9ecef"))
            fig.update_traces(line=dict(color="#3b82f6", width=3), marker=dict(size=8, color="#3b82f6"))
            st.plotly_chart(fig, width='stretch', key="trend_alertas")

    st.markdown("### Mapa de alertas")
    if not df_alertas.empty:
        r = mapa_pydeck_puntos(df_alertas, "lat","lon","riesgo", None)
        if r: st.pydeck_chart(r, key="map_alertas")

    st.markdown("### Lista de alertas")
    cols = [c for c in ["id_alerta","categoria","riesgo","estado","fecha_hora","departamento","provincia","local","descripcion","responsable","accion"] if c in df_alertas.columns]
    st.dataframe(df_alertas[cols].head(200), width='stretch', hide_index=True,
                 column_config={"descripcion": st.column_config.TextColumn("Descripción", width="large")})
    exportar_csv(df_alertas, "alertas_flv")

# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    df_geo, df_local, df_mat, df_jorn, df_fisc, df_actores, df_alertas, df_actividades = generar_data()

    sidebar_nav()

    pais, df_local_f, df_mat_f, df_jorn_f, df_fisc_f, df_actores_f, df_alertas_f, df_actividades_f = filtros_globales(
        df_local, df_mat, df_jorn, df_fisc, df_actores, df_alertas, df_actividades
    )

    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;background:white;border:1px solid #e9ecef;border-radius:10px;padding:0.5rem 1rem;margin-bottom:1rem;">
        <div><span style="color:#6c757d;font-size:0.8rem;"><i class="bi bi-database"></i> Datos ficticios - Prototipo</span></div>
        <div><span style="color:#6c757d;font-size:0.8rem;"><i class="bi bi-clock"></i> Última actualización: {AHORA.strftime('%d/%m/%Y %H:%M')}</span></div>
        <div><span style="color:#6c757d;font-size:0.8rem;">
            Locales: <b style="color:#1a1a2e;">{len(df_local_f):,}</b> &nbsp;|&nbsp;
            Mesas: <b style="color:#1a1a2e;">{int(df_local_f['mesas'].sum()):,}</b> &nbsp;|&nbsp;
            Electores: <b style="color:#1a1a2e;">{int(df_local_f['electores'].sum()):,}</b>
        </span></div>
    </div>
    """, unsafe_allow_html=True)

    mod = st.session_state.modulo

    if mod == "Inicio":
        pagina_inicio(df_local_f, pais)
    elif mod == "Material":
        pagina_material(df_local_f, df_mat_f)
    elif mod == "Jornada":
        pagina_jornada(df_local_f, df_jorn_f, df_fisc_f, df_actores_f)
    elif mod == "Actividades":
        pagina_actividades(df_local_f, df_actividades_f)
    elif mod == "Alertas":
        pagina_alertas(df_alertas_f, df_local_f)


if __name__ == "__main__":
    main()
