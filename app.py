import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Red Ambiental - V42 Pro Zebra", layout="wide", page_icon="♻️")

st.markdown("""
<style>
.stApp { background-color: #e9ecf2; }
section[data-testid="stSidebar"] { background-color: #0a2211; }
.gepp-card { background:white; border:1px solid #b0b8c8; border-radius:6px; overflow:hidden; margin-bottom:8px; box-shadow:0 1px 3px rgba(0,0,0,0.1); }
.gepp-header { background:#0f3d1f; color:white; padding:6px 12px; font-size:11px; font-weight:700; text-align:center; text-transform:uppercase; }
</style>
""", unsafe_allow_html=True)

# LEE DEL DRIVE - TU SHEET PUBLICADO
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRdHGoaJ3BSFqaU4DIH1Wks7dROyzp3z7Z_guIBoAD7VzSXCIis14R9HMPCaDmF3omEK5RzEDlua1aR/pub?gid=1011674108&single=true&output=csv"

@st.cache_data(ttl=60)
def load():
    df = pd.read_csv(URL)
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    if 'Estatus Entrega' in df.columns:
        df = df.drop(columns=['Estatus Entrega'])
    df["Plantilla Autorizada"] = df.get("Plantilla Autorizada", pd.Series([None]*len(df))).fillna("").replace("None","").replace("none","")

    mapa = {
        "BAXTER": "Eduardo Vidal",
        "BASE GARCIA": "Felix Najera", "BASE GARCÍA": "Felix Najera",
        "POLOMEX": "Felix Najera", "AMAZON MTY1": "Felix Najera",
        "AMAZON MTY2": "Felix Najera", "AMAZON MTY3": "Felix Najera",
        "JUEGOS DEL VALLE": "Felix Najera", "CELESTICA": "Felix Najera",
        "CATERPILLAR CIENEGA": "Sergio Llanes",
    }
    def get_coord(r):
        c = str(r.get("Coordinador","")).strip()
        if c.lower() not in ["","nan","none","sin asignar"]:
            return c
        return mapa.get(str(r.get("Planta","")).upper().strip(), "SIN ASIGNAR")
    if "Coordinador" not in df.columns:
        df["Coordinador"] = ""
    df["Coordinador"] = df.apply(get_coord, axis=1)
    return df

df_full = load()

with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.markdown("<h2 style='color:white; text-align:center;'>♻️ RED AMBIENTAL</h2>", unsafe_allow_html=True)
    if st.button("🔄 ACTUALIZAR", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    df_full['Fecha_dt'] = pd.to_datetime(df_full['Fecha'], dayfirst=True, errors='coerce')
    try:
        min_f = df_full['Fecha_dt'].min().date()
        max_f = df_full['Fecha_dt'].max().date()
        fecha_sel = st.date_input("Fecha", value=(min_f, max_f))
    except:
        fecha_sel = None
    plantas = ["Todas"] + sorted(df_full["Planta"].dropna().astype(str).unique().tolist()) if "Planta" in df_full.columns else ["Todas"]
    planta_sel = st.selectbox("Planta", plantas)
    coords = ["Todos"] + sorted(df_full["Coordinador"].dropna().astype(str).unique().tolist()) if "Coordinador" in df_full.columns else ["Todos"]
    coord_sel = st.selectbox("Coordinador", coords)
    dentro_sel = st.selectbox("¿Dentro?", ["Todos","DENTRO","FUERA"])

df = df_full.copy()
if fecha_sel and isinstance(fecha_sel, tuple) and len(fecha_sel)==2:
    try:
        df = df[(df['Fecha_dt'].dt.date >= fecha_sel[0]) & (df['Fecha_dt'].dt.date <= fecha_sel[1])]
    except: pass
if planta_sel!= "Todas":
    df = df[df["Planta"].astype(str).str.strip() == planta_sel]
if coord_sel!= "Todos":
    df = df[df["Coordinador"].astype(str).str.strip() == coord_sel]
def norm(v): return str(v).upper().strip() if pd.notna(v) else "FUERA"
df['¿Dentro?_NORM'] = df['¿Dentro?'].apply(norm) if '¿Dentro?' in df.columns else "FUERA"
if dentro_sel!= "Todos":
    df = df[df['¿Dentro?_NORM'] == dentro_sel]

def semaforo(r):
    dentro = r['¿Dentro?_NORM']
    try: hrs = float(str(r.get('Horas Trabajadas',0)).replace('nan','0'))
    except: hrs=0
    if dentro=='DENTRO' and hrs>=7: return 'Excelente'
    elif dentro=='DENTRO': return 'Bueno'
    else: return 'Malo'
df['Semáforo'] = df.apply(semaforo, axis=1)

total = len(df)
dentro = (df['¿Dentro?_NORM']=='DENTRO').sum()
fuera = total - dentro

# TABLA PRO ZEBRA CON HTML REAL - ESTA SI JALA WE
def render_zebra(df_to_show):
    html = """
    <style>
   .zebra-table { width:100%; border-collapse:collapse; font-size:12px; font-family:Arial; }
   .zebra-table th { background:#0f3d1f; color:white; padding:8px; text-align:left; position:sticky; top:0; }
   .zebra-table td { padding:7px 8px; border-bottom:1px solid #e0e0e0; }
   .zebra-table tr:nth-child(even) { background:#f2f4f7; }
   .zebra-table tr:nth-child(odd) { background:#ffffff; }
   .zebra-table tr:hover { background:#d1e7dd!important; }
   .badge-dentro { background:#00b050; color:white; padding:2px 6px; border-radius:10px; font-weight:bold; font-size:10px; }
   .badge-fuera { background:#ff0000; color:white; padding:2px 6px; border-radius:10px; font-weight:bold; font-size:10px; }
    </style>
    <div style="max-height:500px; overflow:auto; background:white;">
    <table class="zebra-table">
    <thead><tr>
    """
    for col in df_to_show.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    for _, row in df_to_show.iterrows():
        html += "<tr>"
        for col in df_to_show.columns:
            val = row[col]
            if col == "¿Dentro?":
                if str(val).upper() == "DENTRO":
                    html += f'<td><span class="badge-dentro">DENTRO</span></td>'
                else:
                    html += f'<td><span class="badge-fuera">FUERA</span></td>'
            elif col == "Fotos" and pd.notna(val) and str(val).startswith("http"):
                html += f'<td><a href="{val}" target="_blank" style="color:#0f3d1f; font-weight:bold;">Ver</a></td>'
            else:
                html += f"<td>{val}</td>"
        html += "</tr>"
    html += "</tbody></table></div>"
    return html

st.markdown(f'<div style="background:#0f3d1f; color:white; padding:10px; border-radius:6px;">RED AMBIENTAL | {planta_sel} | {coord_sel} | Total:{total} | LIVE {pd.Timestamp.now().strftime("%H:%M")}</div>', unsafe_allow_html=True)

# FILA TABLA FINAL PRO
st.markdown('<div class="gepp-card"><div class="gepp-header">DETALLE - PERSONAL - PRO ZEBRA - LEYENDO DEL DRIVE</div>', unsafe_allow_html=True)
cols_final = ['Fecha','Hora Entrada','Hora Salida','Horas Trabajadas','Nombre completo','Numero Empleado','Latitud','Longitud','¿Dentro?','Fotos','Planta','Coordinador','Semáforo']
cols_final = [c for c in cols_final if c in df.columns]
df_show = df[cols_final].tail(100).fillna("")

# RENDER HTML ZEBRA
st.markdown(render_zebra(df_show), unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.caption(f"© RED AMBIENTAL V42 PRO ZEBRA DRIVE | {URL[:60]}... | {total} registros")
