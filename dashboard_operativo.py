# -*- coding: utf-8 -*-
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

MAPPING_MOD = {"material":"Material","jornada":"Jornada","otras":"Otras"}

for key, val in [("modulo","Material"),("subcard","impresion"),
                 ("local_id",None),("mesa",None),("search","")]:
    if key not in st.session_state:
        st.session_state[key] = val

st.markdown("""
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
<style>
    :root { --bg:#efefef; --panel:#fff; --ink:#17202a; --muted:#6f6f6f; --line:#dedede;
            --jne-red:#c91517; --jne-gray:#928e85; --jne-coral:#ef6f68; --jne-teal:#08b3a0;
            --jne-orange:#f2b15f; --green:#129c55; --shadow:0 10px 24px rgba(24,35,53,.08);
            --radius:8px; }
    * { box-sizing:border-box; }
    .stApp { background:var(--bg); color:var(--ink); font-family:"Segoe UI",Arial,sans-serif; }
    .block-container { max-width:100%; padding:0.5rem 1.5rem; }
    h1,h2,h3 { color:var(--ink) !important; }
    p { color:#495057; }
    [data-testid="stSidebar"] { background:#3f3f3f !important; color:#f8fafc; min-width:230px; }
    [data-testid="stSidebar"] > div:first-child { padding:0 !important; }
    [data-testid="stSidebar"] .brand { display:grid; gap:6px; margin-bottom:24px; }
    [data-testid="stSidebar"] .brand strong { font-size:18px; line-height:1.2; color:#f8fafc !important; }
    [data-testid="stSidebar"] .brand span, .meta { color:#cbd5e1; font-size:12px; line-height:1.45; }
    [data-testid="stSidebar"] .meta { display:grid; gap:4px; margin:18px 0; }
    [data-testid="stSidebar"] .meta strong { color:#e5e7eb; }
    [data-testid="stSidebar"] .nav { display:grid; gap:8px; margin:18px 0 26px; }
    [data-testid="stSidebar"] .nav-a { display:grid; grid-template-columns:24px 1fr auto; align-items:center; gap:8px;
        width:100%; border:1px solid transparent; border-radius:var(--radius); padding:10px 11px;
        color:#e5e7eb; background:transparent; text-decoration:none; }
    [data-testid="stSidebar"] .nav-a.active, [data-testid="stSidebar"] .nav-a:hover { background:#55524c; border-color:#716d66; }
    [data-testid="stSidebar"] .dot { width:9px; height:9px; border-radius:50%; display:inline-block; background:var(--jne-red); }
    [data-testid="stSidebar"] .dot.teal { background:var(--jne-teal); }
    [data-testid="stSidebar"] .dot.violet { background:var(--jne-coral); }
    .filter-wrap { background:var(--panel); border:1px solid var(--line); border-radius:var(--radius);
        padding:14px; box-shadow:var(--shadow); margin-bottom:16px; }

    .module-grid { display:grid; grid-template-columns:repeat(3,minmax(190px,1fr)); gap:14px; margin-bottom:16px; }
    button.module-card, button.sub-card { background:var(--panel); border:1px solid var(--line); border-radius:var(--radius);
        box-shadow:var(--shadow); cursor:pointer; font:inherit; color:var(--ink); text-align:left;
        width:100%; padding:0; }
    button.module-card { display:grid; gap:10px; padding:16px; border-left:0; border-top:8px solid var(--jne-gray);
        min-height:156px; }
    button.module-card.active { outline:2px solid rgba(201,21,23,.22); }
    button.module-card[data-module="material"] { border-top-color:var(--jne-orange); }
    button.module-card[data-module="jornada"] { border-top-color:var(--jne-teal); }
    button.module-card[data-module="otras"] { border-top-color:var(--jne-coral); }
    button.module-card .module-head { display:flex; align-items:center; justify-content:space-between; gap:10px; }
    button.module-card h2 { font-size:17px; margin:0; color:var(--ink) !important; }
    button.module-card .badge { border:1px solid #d6e2ee; border-radius:999px; padding:5px 9px; color:#344054;
        background:#fff; font-size:12px; white-space:nowrap; }
    button.module-card p { margin:0; color:var(--muted); line-height:1.35; font-size:13px; }
    .module-kpis { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; }
    .mini-kpi { background:#f8fafc; border:1px solid #e9eef5; border-radius:7px; padding:8px; }
    .mini-kpi strong { display:block; font-size:18px; line-height:1.05; color:var(--ink); font-weight:700; }
    .mini-kpi span { color:var(--muted); font-size:11px; }
    button.sub-card { display:grid; gap:8px; padding:12px; min-height:124px; align-content:start; box-shadow:none; }
    button.sub-card.active { border-color:var(--jne-red); background:#fff7f7; box-shadow:inset 0 0 0 1px rgba(201,21,23,.2); }
    button.sub-card h4 { margin:0; font-size:14px; line-height:1.25; color:var(--ink) !important; }
    button.sub-card p { color:var(--muted); font-size:12px; line-height:1.35; margin:0; }
    button.sub-card .badge { white-space:normal; line-height:1.3; border:1px solid #d6e2ee; border-radius:999px;
        padding:5px 9px; color:#344054; background:#fff; font-size:12px; }
    .sub-metrics { display:grid; grid-template-columns:repeat(3,1fr); gap:6px; margin-top:2px; }
    .sub-metrics span { border:1px solid #e4ebf3; border-radius:7px; background:#fbfdff; color:#344054;
        padding:6px; font-size:11px; line-height:1.2; }
    .sub-metrics b { display:block; color:var(--ink); font-size:14px; margin-bottom:2px; }
    .progress { height:8px; background:#e9eef5; border-radius:999px; overflow:hidden; }
    .progress i { display:block; height:100%; border-radius:inherit; }
    .workbench { display:grid; grid-template-columns:minmax(340px,1.2fr) minmax(340px,.8fr); gap:16px; align-items:start; }
    .panel { background:var(--panel); border:1px solid var(--line); border-radius:var(--radius);
        box-shadow:var(--shadow); padding:15px; }
    .panel-title { display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:12px; }
    .panel-title h3 { margin:0; font-size:16px; }
    .panel-title h3::before { content:""; display:inline-block; width:8px; height:18px; border-radius:2px;
        background:var(--jne-red); margin-right:8px; vertical-align:-3px; }
    .panel-title span { color:var(--muted); font-size:12px; }
    .card-unit { position:relative; overflow:hidden; }
    .card-unit [data-testid="stButton"] { position:absolute; top:0; left:0; width:100%; height:100%; opacity:0; z-index:3; }
    .card-unit [data-testid="stButton"] button { width:100% !important; height:100% !important; cursor:pointer;
        box-shadow:none !important; border:none !important; background:transparent !important; min-height:0 !important; padding:0 !important; }
    .card-unit > div:last-child { margin-top:-10px; }
    .detail-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin:12px 0; }
    .metric { border:1px solid var(--line); border-radius:var(--radius); padding:10px 12px; background:#fbfdff; }
    .metric span { color:var(--muted); font-size:12px; }
    .metric strong { display:block; font-size:20px; margin-top:3px; color:var(--ink); }
    .table-scroll { overflow:auto; border:1px solid var(--line); border-radius:var(--radius); max-height:330px; background:#fff; }
    table { border-collapse:collapse; width:100%; min-width:760px; font-size:12px; }
    th, td { text-align:left; padding:10px; border-bottom:1px solid #eef2f6; vertical-align:middle; }
    th { position:sticky; top:0; background:#f8fafc; color:#344054; z-index:1; font-size:11px; text-transform:uppercase; letter-spacing:.3px; }
    tr:hover td { background:#fafcff; }
    .status { display:inline-flex; min-width:84px; justify-content:center; border-radius:999px; padding:4px 8px; font-size:11px; font-weight:700; }
    .status.ok { background:#e7f6ee; color:#128047; }
    .status.warn { background:#fff3df; color:#a65f00; }
    .status.risk { background:#fdeeee; color:var(--jne-red); }
    .status.info { background:#e6f8f5; color:#078a7b; }
    .local-card { border:1px solid var(--line); border-radius:var(--radius); overflow:hidden; background:#fff; margin:12px 0; }
    .local-card-head { background:#06447b; color:#fff; padding:10px 12px; display:flex; align-items:center; justify-content:space-between; gap:8px; font-weight:800; font-size:13px; }
    .local-card-body { padding:12px; display:grid; gap:10px; }
    .local-facts { display:grid; grid-template-columns:160px 1fr; gap:7px 12px; font-size:12px; }
    .local-facts b { color:#06447b; }
    .print-detail { border-top:1px solid var(--line); padding-top:10px; display:grid; gap:8px; }
    .print-detail h4 { margin:0; font-size:13px; color:var(--ink); }
    .print-row { display:grid; grid-template-columns:minmax(135px,1.15fr) 90px 90px minmax(140px,1fr) 72px 96px;
        gap:8px; align-items:center; border:1px solid #e2e8f0; border-radius:7px; padding:8px;
        background:#fbfdff; font-size:12px; }
    .print-row strong { color:var(--ink); }
    .print-row strong em { display:block; margin-top:2px; color:var(--muted); font-style:normal; font-weight:700; }
    .print-row span { color:var(--muted); }
    .mini-progress { height:7px; border-radius:999px; background:#e9eef5; overflow:hidden; }
    .mini-progress i { display:block; height:100%; border-radius:inherit; }
    .print-row.done { border-color:#bfe8d1; background:#f4fbf7; }
    .print-row.done .mini-progress i { background:#16a05d; }
    .print-row.progressing { border-color:#f4d6a3; background:#fff9ef; }
    .print-row.progressing .mini-progress i { background:var(--jne-orange); }
    .print-row.pending { border-color:#f4d6a3; background:#fffaf0; }
    .print-row.pending .mini-progress i { background:var(--jne-orange); }
    .print-row.critical { border-color:#f1b9b9; background:#fff6f6; }
    .print-row.critical .mini-progress i { background:var(--jne-red); }
    .row-incident { grid-column:1/-1; border-top:1px solid rgba(15,23,42,.08); padding-top:6px; color:var(--muted); line-height:1.4; }
    .row-incident strong { color:#3f4755; margin-right:4px; }
    .alerts { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:16px; }
    .alert-card { border:1px solid var(--line); border-radius:var(--radius); padding:11px; background:#fff; display:grid; gap:7px; }
    .alert-card strong { font-size:13px; }
    .alert-card span { color:var(--muted); font-size:12px; line-height:1.35; }
    .description { color:var(--muted); line-height:1.45; margin:0 0 10px; font-size:13px; }
    .stSelectbox label { font-size:0.7rem !important; color:var(--muted) !important; font-weight:600; text-transform:uppercase; letter-spacing:.3px; }
    .stSelectbox div[data-baseweb="select"] > div { min-height:2rem; font-size:0.78rem; }
    div[data-testid="stMetricValue"] { font-size:1.3rem !important; color:var(--ink) !important; }
    div[data-testid="stMetricLabel"] { font-size:0.65rem !important; color:var(--muted) !important; }
    .stPyDeck iframe { border-radius:6px; border:1px solid var(--line); }
    .footer { text-align:center; padding:0.5rem 0; color:#adb5bd; font-size:0.65rem; }
    @media (max-width:1160px) { .workbench { grid-template-columns:1fr; } }
    @media (max-width:760px) { .module-grid { grid-template-columns:1fr; } .local-facts,.print-row { grid-template-columns:1fr; } .alerts { grid-template-columns:1fr; } }
</style>
""", unsafe_allow_html=True)

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
                    if pct >= 95: estado = "Validado"
                    elif pct >= 70: estado = "Completado"
                    elif pct >= 20: estado = "En proceso"
                    else: estado = "Pendiente"
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

params = st.query_params
if "modulo" in params:
    v = params["modulo"].lower()
    if v in MAPPING_MOD:
        st.session_state.modulo = MAPPING_MOD[v]
        st.session_state.subcard = None
        st.session_state.local_id = None
        st.session_state.mesa = None
if "subcard" in params:
    st.session_state.subcard = params["subcard"]

MODULOS = {
    "Material": {
        "icono": "📦", "desc": "Control de impresión, embalaje, despliegue, arribo y verificación pública del material electoral.",
        "subcards": [
            ("impresion", "Impresión de material electoral", "Cédulas, relación/lista de electores y acta padrón."),
            ("ensamblaje", "Embalaje de material electoral", "Inicio de embalaje por circunscripción y mesa."),
            ("despliegue_odpe", "Despliegue de material a ODPE", "Partida, arribo, ODPE destino, resguardo policial."),
            ("arribo_local", "Despliegue y arribo al local", "Local, mesa, arribo, resguardo, personal e incidentes."),
            ("verificacion", "Verificación pública", "Circunscripción, cantidad verificada, fecha/hora y responsable."),
        ]
    },
    "Jornada": {
        "icono": "🗳️", "desc": "Seguimiento secuencial de instalación, sufragio, escrutinio, repliegue y fiscalizadores.",
        "subcards": [
            ("instalacion", "Instalación", "Mesas, electores, horarios, evidencias e incidencias."),
            ("sufragio", "Sufragio", "Inicio de sufragio por mesa, local, electores y responsable."),
            ("escrutinio", "Escrutinio", "Cierre, actas de instalación, sufragio y escrutinio."),
            ("repliegue", "Repliegue y arribo", "Salida del local, llegada a ODPE, ONPE, FFAA/PNP."),
            ("fiscalizador", "Fiscalizador", "Asignación, despliegue, horarios, cobertura, evidencias."),
        ]
    },
    "Otras": {
        "icono": "📋", "desc": "Seguimiento de capacitación, carteles, publicación de local, propaganda y expendio de bebidas.",
        "subcards": [
            ("capacitacion", "Capacitación a miembros de mesa", "Locales con capacitación, fiscalizadores desplegados."),
            ("cartel_candidatos", "Publicación de cartel de candidatos", "Estado de cumplimiento, fecha/hora y evidencia."),
            ("publicacion_local", "Publicación de local de votación", "Visibilidad de publicación, estado, fecha/hora."),
            ("propaganda", "Propaganda electoral", "Presencia/ausencia, ubicación, riesgo, evidencia."),
            ("bebidas", "Expendio de bebidas alcohólicas", "Presencia/ausencia, evidencia, riesgo y acciones del JNE."),
        ]
    }
}

SUBCARD_ETAPA_MAP = {
    "impresion": "Impresión", "ensamblaje": "Ensamblaje", "despliegue_odpe": "Despliegue a ODPE",
    "arribo_local": "Arribo a local", "verificacion": "Verificación pública",
    "instalacion": "Instalación", "sufragio": "Sufragio", "escrutinio": "Escrutinio",
    "repliegue": "Repliegue", "fiscalizador": "Fiscalizador",
    "capacitacion": "Capacitación a miembros de mesa", "cartel_candidatos": "Publicación de cartel de candidatos",
    "publicacion_local": "Publicación de local de votación", "propaganda": "Propaganda electoral",
    "bebidas": "Expendio de bebidas alcohólicas",
}

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
            "departamento": nom, "lat": lat, "lon": lon,
            "total": int(r["total"]), "locales": int(r["locales"]),
            "radio": max(int(r["total"]), 1),
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame()

def mapa_pydeck(df, metric="mesas"):
    data = _preparar_mapa(df, metric)
    if data.empty: return None
    max_radio = data["radio"].max() or 1
    data["radio_px"] = (data["radio"] / max_radio * 50 + 10).clip(8, 60)
    capa = pdk.Layer(
        "ScatterplotLayer", data=data,
        get_position='[lon, lat]',
        get_radius="radio_px * 1000",
        get_fill_color=[59, 130, 246, 180],
        get_line_color=[255,255,255], get_line_width=3, pickable=True,
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
    if df.empty: return None
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

def exportar_csv(df, nombre):
    csv_data = io.BytesIO()
    df.to_csv(csv_data, index=False, encoding="utf-8-sig", sep=";")
    csv_data.seek(0)
    st.download_button(
        label=f"📥 Exportar {nombre}", data=csv_data,
        file_name=f"{nombre}_{AHORA.strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv", key=f"exp_{nombre}",
    )

def _hash(txt):
    h = 0
    for c in str(txt):
        h = ((h << 5) - h) + ord(c)
    return abs(h)

def estado_a_cls(estado):
    if estado in ("Completado","Validado","Realizado"): return "status ok"
    if estado in ("En proceso","Con observación"): return "status warn"
    if estado in ("Registrado","Cubierto"): return "status info"
    return "status risk"

def riesgo_a_cls(riesgo):
    if riesgo == "Leve": return "status ok"
    if riesgo == "Moderado": return "status warn"
    return "status risk"

def generar_componentes_impresion(local, mesa):
    nombres = ["Cédula de sufragio","Relación de electores","Lista de electores","Acta padrón","Cartilla de instrucción"]
    res = []
    for i, nom in enumerate(nombres):
        semilla = _hash(f"{local['id_local']}-{mesa}-{nom}")
        total = max(1, local["mesas"] * (3 if i == 0 else 1))
        pct_base = 58 + (semilla % 39)
        if nom == "Lista de electores":
            impreso = total
            pct_base = 100
        else:
            impreso = min(total, int(total * pct_base / 100))
        pct = round(impreso / total * 100) if total else 0
        if pct >= 95: estado = "Completado"
        elif pct >= 75: estado = "En proceso"
        else: estado = "Pendiente"
        hora = f"{5 + (semilla % 5):02d}:{(semilla * 7) % 60:02d}:00"
        hora_fin = f"{9 + (semilla % 5):02d}:{(semilla * 13) % 60:02d}:00"
        if estado == "Completado":
            incidencia = "Sin incidencia: proceso culminado y validado."
            accion = f"Fiscalizador verificó término a las {hora_fin}, contrastó cantidad y dejó evidencia en FLV."
        elif pct < 10:
            incidencia = "Incidencia crítica: avance menor al 10% por espera de lote validado."
            accion = f"Fiscalizador registró incidencia crítica, coordinó reposición y activó seguimiento hasta las {hora_fin}."
        else:
            incidencias_texto = [
                "Demora por entrega parcial del lote validado para impresión.",
                "Reproceso por observación de correlativo en control de calidad.",
                "Espera de conformidad técnica antes del pase a almacén.",
                "Diferencia de conteo detectada durante verificación del componente."
            ]
            acciones_texto = [
                f"Fiscalizador registró la demora, solicitó prioridad y programó verificación a las {hora_fin}.",
                f"Fiscalizador validó el conteo parcial, escaló observación y pidió actualización a las {hora_fin}.",
                f"Fiscalizador dejó constancia en FLV, coordinó nueva revisión y verificará avance a las {hora_fin}."
            ]
            incidencia = incidencias_texto[semilla % len(incidencias_texto)]
            accion = acciones_texto[semilla % len(acciones_texto)]
        if estado == "Completado": row_cls = "done"
        elif estado == "En proceso": row_cls = "progressing"
        else: row_cls = "pending"
        if pct < 10: row_cls = "critical"
        res.append({
            "nombre": nom, "hora": hora, "hora_fin": hora_fin,
            "total": total, "impreso": impreso, "pct": pct,
            "estado": estado, "cls": row_cls,
            "incidencia": incidencia, "accion": accion,
        })
    return res

def render_sidebar():
    st.sidebar.markdown(f"""
    <div class="brand"><strong>📊 Tablero Operativo Electoral</strong><span>SIPE + FLV · Prototipo</span></div>
    <div class="meta"><div>Última actualización</div><strong>{AHORA.strftime('%d/%m/%Y %H:%M')}</strong><div>Frecuencia: cada 15 minutos</div></div>
    <nav class="nav" aria-label="Módulos principales">
        <a href="?modulo=material" class="nav-a {'active' if st.session_state.modulo=='Material' else ''}"><span class="dot" style="background:#f2b15f"></span><span>📦 Material electoral</span><span>{len(MODULOS['Material']['subcards'])}</span></a>
        <a href="?modulo=jornada" class="nav-a {'active' if st.session_state.modulo=='Jornada' else ''}"><span class="dot" style="background:#08b3a0"></span><span>🗳️ Jornada electoral</span><span>{len(MODULOS['Jornada']['subcards'])}</span></a>
        <a href="?modulo=otras" class="nav-a {'active' if st.session_state.modulo=='Otras' else ''}"><span class="dot" style="background:#ef6f68"></span><span>📋 Otras actividades</span><span>{len(MODULOS['Otras']['subcards'])}</span></a>
    </nav>
    <div class="meta"><strong>Fuentes principales</strong><div>SIPE, FLV, registros de personal, locales, mesas, material electoral, incidencias y evidencias.</div></div>
    """, unsafe_allow_html=True)

def _reset_filters():
    st.session_state.local_id = None
    st.session_state.mesa = None
    for k in ["filtro_dept","filtro_prov","filtro_dist","filtro_search"]:
        st.session_state.pop(k, None)

def _on_change_dept():
    st.session_state.filtro_prov = "Todas"
    st.session_state.filtro_dist = "Todos"
    st.session_state.local_id = None
    st.session_state.mesa = None

def _on_change_prov():
    st.session_state.filtro_dist = "Todos"
    st.session_state.local_id = None
    st.session_state.mesa = None

def _on_change_dist():
    st.session_state.local_id = None
    st.session_state.mesa = None

def render_filter_bar(df_local):
    def _dept(): return st.session_state.get("filtro_dept", "Todos")
    def _prov(): return st.session_state.get("filtro_prov", "Todas")
    def _dist(): return st.session_state.get("filtro_dist", "Todos")

    st.markdown("<div class='filter-wrap'>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns([1.2, 1.2, 1.2, 1.2, 1.5, 0.6])
    with c1:
        st.selectbox("📋 Proceso", ["ERM 2026 - Elecciones Regionales y Municipales 2026"], key="filtro_proceso")
    with c2:
        dept_opts = ["Todos"] + sorted(df_local["departamento"].unique())
        st.selectbox("🏛️ Departamento", dept_opts, key="filtro_dept",
                     on_change=lambda: _on_change_dept())
    with c3:
        prov_opts = ["Todas"]
        d = _dept()
        if d == "Todos":
            prov_opts += sorted(df_local["provincia"].unique())
        else:
            prov_opts += sorted(df_local[df_local["departamento"] == d]["provincia"].unique())
        st.selectbox("📍 Provincia", prov_opts, key="filtro_prov",
                     on_change=lambda: _on_change_prov())
    with c4:
        dist_opts = ["Todos"]
        d, p = _dept(), _prov()
        if d == "Todos" and p == "Todas":
            dist_opts += sorted(df_local["distrito"].unique())
        elif p != "Todas":
            dist_opts += sorted(df_local[df_local["provincia"] == p]["distrito"].unique())
        else:
            dist_opts += sorted(df_local[df_local["departamento"] == d]["distrito"].unique())
        st.selectbox("🌆 Distrito", dist_opts, key="filtro_dist",
                     on_change=lambda: _on_change_dist())
    with c5:
        st.text_input("🔍 Búsqueda", placeholder="Local, mesa, responsable...", key="filtro_search")
    with c6:
        st.markdown("<div style='margin-top:22px;'>", unsafe_allow_html=True)
        if st.button("🔄", key="btn_reset", help="Restablecer filtros"):
            _reset_filters()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    mask = pd.Series([True] * len(df_local))
    d, p, dist = _dept(), _prov(), _dist()
    if d != "Todos": mask &= df_local["departamento"] == d
    if p != "Todas": mask &= df_local["provincia"] == p
    if dist != "Todos": mask &= df_local["distrito"] == dist
    return df_local[mask].copy()

def _on_mod_click(key):
    st.session_state.modulo = key
    st.session_state.subcard = MODULOS[key]["subcards"][0][0]
    st.session_state.local_id = None
    st.session_state.mesa = None

def render_module_cards(df_local, df_mat, df_jorn, df_actividades):
    cols = st.columns(3)
    for idx, (key, mod) in enumerate(MODULOS.items()):
        with cols[idx]:
            if key == "Material":
                subset = df_mat
            elif key == "Jornada":
                subset = df_jorn
            else:
                subset = df_actividades
            total = len(subset)
            avg_pct = int(subset["porcentaje"].mean()) if "porcentaje" in subset.columns and total else 0
            if "porcentaje" not in subset.columns:
                avg_pct = int((subset["estado"] == "Completado").sum() / max(total, 1) * 100)
            pending = int((subset["estado"] == "Pendiente").sum()) if "estado" in subset.columns else 0
            activo_mod = st.session_state.modulo == key
            card_key = f"mod_{key}"
            st.markdown(f'<div class="card-unit" id="cu-{card_key}">', unsafe_allow_html=True)
            st.markdown(f"""
            <button class="module-card {'active' if activo_mod else ''}" data-module="{key.lower()}" type="button" tabindex="-1">
                <div class="module-head"><h2>{mod['icono']} {key}</h2><span class="badge">{len(mod['subcards'])} subcards</span></div>
                <p>{mod['desc'][:80]}...</p>
                <div class="module-kpis">
                    <div class="mini-kpi"><strong>{total}</strong><span>Total</span></div>
                    <div class="mini-kpi"><strong>{avg_pct}%</strong><span>Avance</span></div>
                    <div class="mini-kpi"><strong>{pending}</strong><span>Pendiente</span></div>
                </div>
            </button>
            """, unsafe_allow_html=True)
            st.button(" ", key=card_key, on_click=_on_mod_click, args=(key,), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

def _on_sub_click(skey):
    st.session_state.subcard = skey
    st.session_state.local_id = None
    st.session_state.mesa = None

def render_subcards():
    mod = MODULOS[st.session_state.modulo]
    st.markdown(f"<h4 style='margin:0 0 10px;font-size:15px;color:#17202a;'>📂 Subcards: {mod['icono']} {st.session_state.modulo}</h4>", unsafe_allow_html=True)
    cols = st.columns(2)
    for idx, (skey, stitle, sdesc) in enumerate(mod["subcards"]):
        with cols[idx % 2]:
            es_activa = st.session_state.subcard == skey
            total_rec = random.randint(30, 120)
            avg_pct = random.randint(45, 95)
            pend = random.randint(3, 25)
            pct_color = "#16a05d" if avg_pct >= 70 else "#f2b15f" if avg_pct >= 30 else "#c91517"
            st.markdown(f'<div class="card-unit" id="cu-sub-{skey}">', unsafe_allow_html=True)
            st.markdown(f"""
            <button class="sub-card {'active' if es_activa else ''}" type="button" tabindex="-1">
                <h4>{stitle}</h4>
                <p>{sdesc}</p>
                <div class="sub-metrics">
                    <span><b>{total_rec}</b>Registros</span>
                    <span><b>{avg_pct}%</b>Avance</span>
                    <span><b>{pend}</b>Pendiente</span>
                </div>
                <div class="progress" aria-label="Avance {avg_pct}%"><i style="width:{avg_pct}%;background:{pct_color};"></i></div>
                <span class="badge">{stitle[:60]}</span>
            </button>
            """, unsafe_allow_html=True)
            st.button(" ", key=f"sub_{skey}", on_click=_on_sub_click, args=(skey,), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

def get_records_for_subcard(df_local_f, df_mat, df_jorn, df_actividades):
    mod = st.session_state.modulo
    sub = st.session_state.subcard
    rows = []
    etapa = SUBCARD_ETAPA_MAP.get(sub, "")
    if mod == "Material":
        subset = df_mat[df_mat["etapa"] == etapa] if etapa in df_mat["etapa"].values else df_mat
        for _, r in subset.iterrows():
            loc = df_local_f[df_local_f["id_local"] == r["id_local"]]
            if loc.empty: continue
            loc = loc.iloc[0]
            riesgo = "Moderado" if r["estado"] == "En proceso" else "Leve" if r["estado"] in ("Completado","Validado") else "Grave"
            rows.append({
                "departamento": loc["departamento"], "jee": loc["jee"],
                "local": loc["local"], "id_local": loc["id_local"],
                "mesa": f"M{random.randint(100000,999999)}",
                "estado": r["estado"], "avance": r["porcentaje"],
                "riesgo": riesgo, "responsable": r["responsable"],
                "incidente": "Sin incidente" if riesgo == "Leve" else ("Incidente moderado en seguimiento" if riesgo == "Moderado" else "Incidente crítico reportado"),
                "accion": "JNE verificó trazabilidad del material." if riesgo == "Leve" else "JNE activó seguimiento prioritario.",
            })
    elif mod == "Jornada":
        subset = df_jorn[df_jorn["etapa"] == etapa] if etapa in df_jorn["etapa"].values else df_jorn
        for _, r in subset.iterrows():
            loc = df_local_f[df_local_f["id_local"] == r["id_local"]]
            if loc.empty: continue
            loc = loc.iloc[0]
            pct = {"Completado": 95, "En proceso": 55, "Pendiente": 10, "Con incidencia": 40}.get(r["estado"], 50)
            riesgo = "Grave" if r["incidencia"] != "Ninguna" else "Moderado" if r["estado"] == "En proceso" else "Leve"
            rows.append({
                "departamento": loc["departamento"], "jee": loc["jee"],
                "local": loc["local"], "id_local": loc["id_local"],
                "mesa": f"M{r['id_mesa']}",
                "estado": r["estado"], "avance": pct,
                "riesgo": riesgo, "responsable": r["responsable"],
                "incidente": r["incidencia"] if r["incidencia"] != "Ninguna" else "Sin incidente",
                "accion": "JNE verificó apertura y registró evidencia." if r["incidencia"] == "Ninguna" else "JNE dispuso seguimiento y comunicó estado.",
            })
    else:
        act_map = {"capacitacion":"Capacitación a miembros de mesa","cartel_candidatos":"Publicación de cartel de candidatos",
                   "publicacion_local":"Publicación de local de votación","propaganda":"Propaganda electoral",
                   "bebidas":"Expendio de bebidas alcohólicas"}
        act_name = act_map.get(sub, "")
        subset = df_actividades[df_actividades["actividad"] == act_name] if act_name else df_actividades
        for _, r in subset.iterrows():
            loc = df_local_f[df_local_f["id_local"] == r["id_local"]]
            if loc.empty: continue
            loc = loc.iloc[0]
            pct = {"Realizado": 95, "Con observación": 60, "No realizado": 15, "Pendiente": 10}.get(r["estado"], 50)
            riesgo = "Leve" if r["estado"] == "Realizado" else "Moderado"
            rows.append({
                "departamento": loc["departamento"], "jee": loc["jee"],
                "local": loc["local"], "id_local": loc["id_local"],
                "mesa": "-",
                "estado": r["estado"], "avance": pct,
                "riesgo": riesgo, "responsable": r["responsable"] if r["responsable"] else "-",
                "incidente": r["observaciones"] if r["observaciones"] else "Sin incidente",
                "accion": "JNE registró actividad y validó cumplimiento." if r["estado"] == "Realizado" else "JNE coordinó regularización.",
            })
    df_rows = pd.DataFrame(rows)
    if not df_rows.empty:
        search = st.session_state.get("filtro_search", "").lower().strip()
        if search:
            mask_search = df_rows.apply(lambda r: search in str(r.get("local","")).lower() or search in str(r.get("responsable","")).lower() or search in str(r.get("departamento","")).lower(), axis=1)
            df_rows = df_rows[mask_search]
    return df_rows

def render_detail_panel(df_local_f, df_mat, df_jorn, df_actividades):
    rows = get_records_for_subcard(df_local_f, df_mat, df_jorn, df_actividades)
    total = len(rows)
    avg = int(rows["avance"].mean()) if total else 0
    pending = int((rows["estado"] == "Pendiente").sum()) if total else 0
    high = int((rows["riesgo"] == "Grave").sum()) if total else 0
    st.markdown(f"""
    <div class="detail-grid">
        <div class="metric"><span>Total</span><strong>{total}</strong></div>
        <div class="metric"><span>Avance</span><strong>{avg}%</strong></div>
        <div class="metric"><span>Pendiente</span><strong>{pending}</strong></div>
        <div class="metric"><span>Riesgo alto</span><strong>{high}</strong></div>
    </div>
    """, unsafe_allow_html=True)

    if not rows.empty:
        unique_locales = rows[["id_local","local","departamento"]].drop_duplicates("id_local")
        loc_opts = {f"{r['local']} ({r['departamento']})": r["id_local"] for _, r in unique_locales.iterrows()}
        sel_local_label = st.selectbox("📌 Seleccionar local para ver detalle de componentes",
                                       ["(ninguno)"] + list(loc_opts.keys()), key="sel_local_detail")
        if sel_local_label != "(ninguno)":
            lid = loc_opts[sel_local_label]
            if st.session_state.local_id != lid:
                st.session_state.local_id = lid
                st.session_state.mesa = rows[rows["id_local"] == lid].iloc[0]["mesa"] if lid in rows["id_local"].values else None
                st.rerun()

        rows_html = ""
        for _, r in rows.iterrows():
            e_cls = estado_a_cls(r["estado"])
            r_cls = riesgo_a_cls(r["riesgo"])
            rows_html += f"""
            <tr>
                <td>{r['departamento']}</td>
                <td>{r['jee']}</td>
                <td><strong>{r['local']}</strong><br><em style="color:#6f6f6f;font-size:10px;">Mesa {r['mesa']}</em></td>
                <td><span class="{e_cls}">{r['estado']}</span></td>
                <td>{r['avance']}%</td>
                <td><span class="{r_cls}">{r['riesgo']}</span></td>
                <td>{r['responsable']}</td>
                <td style="font-size:10px;color:#6f6f6f;"><strong style="color:#3f4755;">Incidente:</strong> {r['incidente']}<br><strong style="color:#3f4755;">Acción:</strong> {r['accion']}</td>
            </tr>"""
        st.markdown(f"""<div class="table-scroll"><table><thead><tr><th>Departamento</th><th>OD/MOD</th><th>Local/Mesa</th><th>Estado</th><th>Avance</th><th>Riesgo</th><th>Responsable</th><th>Incidente / acción</th></tr></thead><tbody>{rows_html}</tbody></table></div>""", unsafe_allow_html=True)
        exportar_csv(rows, f"detalle_{st.session_state.modulo}_{st.session_state.subcard}")
    else:
        st.info("No hay registros con los filtros activos.")

def render_local_card(df_local_f):
    lid = st.session_state.local_id
    if lid is None:
        return
    loc = df_local_f[df_local_f["id_local"] == lid]
    if loc.empty:
        st.info("Selecciona un local en la tabla para ver su detalle.")
        return
    loc = loc.iloc[0]
    mesa = st.session_state.mesa or f"M{random.randint(100000,999999)}"
    st.markdown(f"""
    <div class="local-card">
        <div class="local-head">
            <span>{loc['local']}</span>
            <span class="status info">Monitoreado</span>
        </div>
        <div class="local-body">
            <div class="local-facts">
                <b>Departamento</b><span>{loc['departamento']}</span>
                <b>Provincia</b><span>{loc['provincia']}</span>
                <b>Distrito</b><span>{loc['distrito']}</span>
                <b>Dirección</b><span>{loc['direccion']}</span>
                <b>Mesas</b><span>{loc['mesas']}</span>
                <b>Mesa seleccionada</b><span>{mesa}</span>
                <b>Electores</b><span>{loc['electores']}</span>
                <b>OD/MOD</b><span>{loc['jee']}</span>
            </div>
    """, unsafe_allow_html=True)

    if st.session_state.subcard == "impresion":
        comps = generar_componentes_impresion(loc, mesa)
        rows_html = ""
        for c in comps:
            rows_html += f"""
            <div class="print-row {c['cls']}">
                <strong>{c['nombre']}<em>Mesa {mesa}</em></strong>
                <span>Inicio {c['hora']}</span>
                <span>Término {c['hora_fin']}</span>
                <div class="mini-progress"><i style="width:{c['pct']}%"></i></div>
                <span>{c['impreso']}/{c['total']}</span>
                <span>{c['pct']}% · {c['estado']}</span>
                <span class="row-incident"><strong>Incidencia:</strong> {c['incidencia']} <strong>Acción fiscalizador:</strong> {c['accion']}</span>
            </div>"""
        st.markdown(f"<div class='print-detail'><h6>📄 Detalle de impresión por componente</h6>{rows_html}</div>", unsafe_allow_html=True)
    elif st.session_state.subcard == "ensamblaje":
        rows_html = ""
        for i in range(min(3, loc["mesas"])):
            sem = _hash(f"{lid}-{mesa}-emb-{i}")
            pct = 46 + (sem % 51)
            estado = "Completado" if pct >= 95 else "En proceso" if pct >= 70 else "Pendiente"
            cls = "done" if pct >= 95 else "progressing" if pct >= 70 else "pending"
            rows_html += f"""
            <div class="print-row {cls}">
                <strong>{loc['departamento']} / {loc['provincia']}<em>Mesa {mesa}</em></strong>
                <span>Inicio {6 + (sem % 7):02d}:{(sem * 5) % 60:02d}:00</span>
                <span>Término {11 + (sem % 3):02d}:{(sem * 11) % 60:02d}:00</span>
                <div class="mini-progress"><i style="width:{pct}%"></i></div>
                <span>{min(loc['mesas'], int(loc['mesas'] * pct / 100))}/{loc['mesas']}</span>
                <span>{pct}% · {estado}</span>
                <span class="row-incident"><strong>Incidencia:</strong> Demora por consolidación de componentes. <strong>Acción fiscalizador:</strong> Fiscalizador registró la demora y verificó componentes.</span>
            </div>"""
        st.markdown(f"<div class='print-detail'><h6>📦 Detalle de embalaje por circunscripción</h6>{rows_html}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="print-detail">
            <h6>📋 Resumen operativo</h6>
            <p style="font-size:11px;color:#6f6f6f;">Registro consistente con filtros activos.</p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    if st.button("🗑️ Cerrar detalle", key="btn_close_detail"):
        st.session_state.local_id = None
        st.session_state.mesa = None
        st.rerun()

def render_map_panel(df_local_f):
    st.markdown("<div class='panel-title'><h5>🗺️ Mapa interactivo del Perú</h5><span>Vista nacional</span></div>", unsafe_allow_html=True)
    scope_label = st.session_state.get("filtro_dept", "Todos") if st.session_state.get("filtro_dept", "Todos") != "Todos" else "Perú"
    st.markdown(f"<span style='font-size:11px;color:#6f6f6f;'><strong>{scope_label}</strong> · {len(df_local_f)} locales · {int(df_local_f['mesas'].sum())} mesas · {int(df_local_f['electores'].sum())} electores</span>", unsafe_allow_html=True)
    r = mapa_pydeck(df_local_f)
    if r:
        st.pydeck_chart(r, key="map_principal")
    else:
        st.info("No hay datos para mostrar en el mapa.")

def render_alerts(df_alertas):
    mod_map = {"Material": "Material electoral", "Jornada": "Jornada electoral", "Otras": "Otras actividades"}
    mod_name = mod_map.get(st.session_state.modulo, "")
    alerts = df_alertas[df_alertas["modulo_asociado"] == mod_name] if mod_name else df_alertas
    dept_f = st.session_state.get("filtro_dept", "Todos")
    if dept_f != "Todos":
        alerts = alerts[alerts["departamento"] == dept_f]
    alerts = alerts[alerts["riesgo"] != "Leve"].head(4)
    st.markdown("<div class='panel-title'><h5>⚠️ Alertas e incidencias FLV</h5><span>Panel transversal</span></div>", unsafe_allow_html=True)
    if not alerts.empty:
        st.markdown("<div class='alerts'>", unsafe_allow_html=True)
        cols = st.columns(2)
        for idx, (_, r) in enumerate(alerts.iterrows()):
            with cols[idx % 2]:
                dot_cls = "red" if r["riesgo"] == "Grave" else "amber"
                st.markdown(f"""
                <div class="alert-card">
                    <strong>FLV-{r['id_alerta']} · {r['departamento']}</strong>
                    <span>{r['categoria']}: {r['descripcion'][:60]}...</span>
                    <span><span class="nav-dot {dot_cls}"></span> Riesgo {r['riesgo']} · {r['estado']}</span>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Sin alertas activas para el filtro actual.")
    timeline = [("06:00",32),("08:00",58),("10:00",76),("12:00",69),("14:00",84),("16:00",79),("18:00",65)]
    st.markdown("<div style='margin-top:10px;'><h6 style='font-size:12px;color:#17202a;'>📈 Actividad del día</h6>", unsafe_allow_html=True)
    for hora, val in timeline:
        st.markdown(f"<div style='display:grid;grid-template-columns:50px 1fr 35px;align-items:center;gap:6px;font-size:11px;color:#6f6f6f;margin:3px 0;'><span>{hora}</span><div style='height:7px;background:#e9eef5;border-radius:999px;overflow:hidden'><div style='height:100%;width:{val}%;background:#08b3a0;border-radius:inherit'></div></div><span>{val}</span></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    dfs = generar_data()
    df_geo, df_local, df_mat, df_jorn, df_fisc, df_actores, df_alertas, df_actividades = dfs

    render_sidebar()

    st.markdown("""
    <div style="margin-bottom:10px;">
        <h1 style="font-size:1.6rem;margin:0;">📊 Monitoreo operativo electoral</h1>
        <p style="color:#6f6f6f;font-size:0.85rem;margin:2px 0 0;">
            Vista de trabajo con tarjetas KPI, mapa interactivo del Perú, subcards por módulo, detalle por departamento/local, alertas FLV y exportación.
        </p>
    </div>
    """, unsafe_allow_html=True)

    df_local_f = render_filter_bar(df_local)

    top_cols = st.columns([1, 0.2, 0.2])
    with top_cols[0]:
        pass
    with top_cols[1]:
        st.markdown(f"<span style='font-size:0.75rem;color:#6c757d;'><i class='bi bi-clock'></i> {AHORA.strftime('%d/%m/%Y %H:%M')}</span>", unsafe_allow_html=True)
    with top_cols[2]:
        pass

    st.markdown("<div class='module-grid'>", unsafe_allow_html=True)
    render_module_cards(df_local_f, df_mat, df_jorn, df_actividades)
    st.markdown("</div>", unsafe_allow_html=True)
    render_subcards()

    col_left, col_right = st.columns([0.6, 0.4])
    with col_left:
        st.markdown("<div class='panel'><div class='panel-title'><h3>📋 Detalle operativo</h3><span>0 registros</span></div>", unsafe_allow_html=True)
        render_detail_panel(df_local_f, df_mat, df_jorn, df_actividades)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_right:
        st.markdown("<div class='panel'><div class='panel-title'><h3>🗺️ Mapa</h3><span>Vista nacional</span></div>", unsafe_allow_html=True)
        render_map_panel(df_local_f)
        st.markdown("</div>", unsafe_allow_html=True)
        render_local_card(df_local_f)
        st.markdown("<div class='panel'><div class='panel-title'><h3>⚠️ Alertas e incidencias FLV</h3><span>Panel transversal</span></div>", unsafe_allow_html=True)
        render_alerts(df_alertas)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='footer'>Prototipo - Dashboard Operativo Electoral v2.0 · Datos ficticios</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
