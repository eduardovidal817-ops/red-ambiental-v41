import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components

st.set_page_config(page_title="Red Ambiental - V42 Pro Zebra LIVE", layout="wide", page_icon="♻️")

st.markdown("""
<style>
.stApp { background-color: #e9ecf2; }
section[data-testid="stSidebar"] { background-color: #0a2211; }
.gepp-card { background:white; border:1px solid #b0b8c8; border-radius:6px; overflow:hidden; margin-bottom:8px; box-shadow:0 1px 3px rgba(0,0,0,0.1); }
.gepp-header { background:#0f3d1f; color:white; padding:6px 12px; font-size:11px; font-weight:700; text-align:center; text-transform:uppercase; }
.search-box input { background:white!important; border:2px solid #0f3d1f!important; border-radius:8px!important; }
.zebra-table { width:100%; border-collapse:collapse; font-size:12px; font-family:Arial; }
.zebra-table th { background:#0f3d1f; color:white; padding:8px; text-align:left; position:sticky; top:0; }
.zebra-table td { padding:7px 8px; border-bottom:1px solid #e0e0e0; }
.zebra-table tr:nth-child(even) { background:#f2f4f7; }
.zebra-table tr:nth-child(odd) { background:#ffffff; }
.zebra-table tr:hover { background:#d1e7dd!important; }
.badge-dentro { background:#00b050; color:white; padding:2px 6px; border-radius:10px; font-weight:bold; font-size:10px; }
.badge-fuera { background:#ff0000; color:white; padding:2px 6px; border-radius:10px; font-weight:bold; font-size:10px; }
.badge-excelente { background:#00b050; color:white; padding:2px 6px; border-radius:10px; font-weight:bold; font-size:10px; }
.badge-bueno { background:#ffcc00; color:black; padding:2px 6px; border-radius:10px; font-weight:bold; font-size:10px; }
.badge-malo { background:#ff0000; color:white; padding:2px 6px; border-radius:10px; font-weight:bold; font-size:10px; }
</style>
""", unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRdHGoaJ3BSFqaU4DIH1Wks7dROyzp3z7Z_guIBoAD7VzSXCIis14R9HMPCaDmF3omEK5RzEDlua1aR/pub?gid=1011674108&single=true&output=csv"

@st.cache_data(ttl=60)
def load():
    df = pd.read_csv(URL)
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    if 'Estatus Entrega' in df.columns:
        df = df.drop(columns=['Estatus Entrega'])
    df["Plantilla Autorizada"] = df.get("Plantilla Autorizada", pd.Series([None]*len(df))).fillna("").astype(str).replace("None","").replace("nan","")
    mapa = {"BAXTER": "Eduardo Vidal","BASE GARCIA": "Felix Najera","BASE GARCÍA": "Felix Najera","POLOMEX": "Felix Najera","AMAZON MTY1": "Felix Najera","AMAZON MTY2": "Felix Najera","AMAZON MTY3": "Felix Najera","JUEGOS DEL VALLE": "Felix Najera","CELESTICA": "Felix Najera","CATERPILLAR CIENEGA": "Sergio Llanes"}
    def get_coord(r):
        c = str(r.get("Coordinador","")).strip()
        if c.lower() not in ["","nan","none","sin asignar"]: return c
        return mapa.get(str(r.get("Planta","")).upper().strip(), "SIN ASIGNAR")
    if "Coordinador" not in df.columns: df["Coordinador"] = ""
    df["Coordinador"] = df.apply(get_coord, axis=1)
    return df

df_full = load()

# FUNCION ZEBRA - PARA LAS 2 TABLAS WE
def render_zebra(df_to_show, max_h="340px"):
    html = f"""
    <style>
   .zebra-table {{ width:100%; border-collapse:collapse; font-size:11px; font-family:Arial; }}
   .zebra-table th {{ background:#0f3d1f; color:white; padding:8px; text-align:left; position:sticky; top:0; z-index:2; }}
   .zebra-table td {{ padding:7px 8px; border-bottom:1px solid #e0e0e0; }}
   .zebra-table tr:nth-child(even) {{ background:#f2f4f7; }}
   .zebra-table tr:nth-child(odd) {{ background:#ffffff; }}
   .zebra-table tr:hover {{ background:#d1e7dd!important; }}
   .badge-dentro {{ background:#00b050; color:white; padding:2px 6px; border-radius:10px; font-weight:bold; font-size:10px; }}
   .badge-fuera {{ background:#ff0000; color:white; padding:2px 6px; border-radius:10px; font-weight:bold; font-size:10px; }}
   .badge-excelente {{ background:#00b050; color:white; padding:2px 6px; border-radius:10px; font-weight:bold; font-size:10px; }}
   .badge-bueno {{ background:#ffcc00; color:black; padding:2px 6px; border-radius:10px; font-weight:bold; font-size:10px; }}
   .badge-malo {{ background:#ff0000; color:white; padding:2px 6px; border-radius:10px; font-weight:bold; font-size:10px; }}
    </style>
    <div style="max-height:{max_h}; overflow:auto; background:white; border-radius:0 0 6px 6px;">
    <table class="zebra-table"><thead><tr>
    """
    for col in df_to_show.columns: html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    for _, row in df_to_show.iterrows():
        html += "<tr>"
        for col in df_to_show.columns:
            val = row[col]
            sval = str(val).upper()
            if col == "¿Dentro?":
                if sval == "DENTRO": html += f'<td><span class="badge-dentro">DENTRO</span></td>'
                else: html += f'<td><span class="badge-fuera">FUERA</span></td>'
            elif col == "Semáforo":
                if sval == "EXCELENTE": html += f'<td><span class="badge-excelente">{val}</span></td>'
                elif sval == "BUENO": html += f'<td><span class="badge-bueno">{val}</span></td>'
                else: html += f'<td><span class="badge-malo">{val}</span></td>'
            elif col == "Fotos" and pd.notna(val) and str(val).startswith("http"): html += f'<td><a href="{val}" target="_blank" style="color:#0f3d1f; font-weight:bold;">Ver</a></td>'
            else: html += f"<td>{val}</td>"
        html += "</tr>"
    html += "</tbody></table></div>"
    return html

with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: st.markdown("<h2 style='color:white; text-align:center;'>♻️ RED AMBIENTAL</h2>", unsafe_allow_html=True)
    if st.button("🔄 ACTUALIZAR", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    df_full['Fecha_dt'] = pd.to_datetime(df_full['Fecha'], dayfirst=True, errors='coerce')
    try:
        min_f = df_full['Fecha_dt'].min().date()
        max_f = df_full['Fecha_dt'].max().date()
        fecha_sel = st.date_input("Fecha", value=(min_f, max_f))
    except: fecha_sel = None
    plantas = ["Todas"] + sorted(df_full["Planta"].dropna().astype(str).unique().tolist()) if "Planta" in df_full.columns else ["Todas"]
    planta_sel = st.selectbox("Planta", plantas)
    coords = ["Todos"] + sorted(df_full["Coordinador"].dropna().astype(str).unique().tolist()) if "Coordinador" in df_full.columns else ["Todos"]
    coord_sel = st.selectbox("Coordinador", coords)
    dentro_sel = st.selectbox("¿Dentro?", ["Todos","DENTRO","FUERA"])

df = df_full.copy()
if fecha_sel and isinstance(fecha_sel, tuple) and len(fecha_sel)==2:
    try: df = df[(df['Fecha_dt'].dt.date >= fecha_sel[0]) & (df['Fecha_dt'].dt.date <= fecha_sel[1])]
    except: pass
if planta_sel!= "Todas": df = df[df["Planta"].astype(str).str.strip() == planta_sel]
if coord_sel!= "Todos": df = df[df["Coordinador"].astype(str).str.strip() == coord_sel]
def norm(v): return str(v).upper().strip() if pd.notna(v) else "FUERA"
df['¿Dentro?_NORM'] = df['¿Dentro?'].apply(norm) if '¿Dentro?' in df.columns else "FUERA"
if dentro_sel!= "Todos": df = df[df['¿Dentro?_NORM'] == dentro_sel]
def semaforo(r):
    dentro = r['¿Dentro?_NORM']
    try: hrs = float(str(r.get('Horas Trabajadas',0)).replace('nan','0'))
    except: hrs=0
    if dentro=='DENTRO' and hrs>=7: return 'Excelente'
    elif dentro=='DENTRO': return 'Bueno'
    else: return 'Malo'
df['Semáforo'] = df.apply(semaforo, axis=1)
df['Plantilla Completa'] = df['Horas Trabajadas'].apply(lambda x: 'Completa' if pd.notna(x) and str(x)!='' and str(x)!='None' else 'Incompleta')

total = len(df)
dentro = (df['¿Dentro?_NORM']=='DENTRO').sum()
fuera = total - dentro

# HEADER + RELOJ + BUSCADOR WE
components.html(f"""
<div style="background:#0f3d1f; color:white; padding:10px 15px; border-radius:6px; display:flex; justify-content:space-between; align-items:center; font-family:Arial; box-shadow:0 2px 4px rgba(0,0,0,0.2);">
    <span style="font-weight:800; font-size:14px;">RED AMBIENTAL | {planta_sel} | {coord_sel}</span>
    <div style="text-align:right; font-size:11px; line-height:15px;">
        <div>Total: {total} | DENTRO: {dentro} | FUERA: {fuera}</div>
        <div id="reloj" style="font-weight:800; font-size:13px; color:#00ff88; margin-top:2px;"></div>
    </div>
</div>
<script>
function actualizarReloj() {{
    const ahora = new Date().toLocaleString("es-MX", {{timeZone: "America/Monterrey", weekday:'long', year:'numeric', month:'long', day:'numeric', hour:'2-digit', minute:'2-digit', second:'2-digit', hour12:true}});
    document.getElementById("reloj").innerHTML = "🕒 " + ahora.toUpperCase() + " | LIVE";
}}
setInterval(actualizarReloj, 1000);
actualizarReloj();
</script>
""", height=75)

st.write("")
# BARRA DE BUSCADOR HASTA ARRIBA WE
busqueda = st.text_input("🔍 Buscar por Nombre, # Empleado, Planta, Coordinador, Fecha...", placeholder="Escribe aquí para filtrar todo el dashboard...", key="buscador_global")

if busqueda:
    busq = busqueda.upper().strip()
    # Filtra por varias columnas
    mask = False
    for col in ['Nombre completo','Numero Empleado','Planta','Coordinador','Fecha','Semáforo','¿Dentro?']:
        if col in df.columns:
            if isinstance(mask, bool):
                mask = df[col].astype(str).str.upper().str.contains(busq, na=False)
            else:
                mask = mask | df[col].astype(str).str.upper().str.contains(busq, na=False)
    if isinstance(mask, pd.Series):
        df = df[mask]
        total = len(df)
        dentro = (df['¿Dentro?_NORM']=='DENTRO').sum()
        fuera = total - dentro

# FILA 1 DONAS
c1,c2,c3,c4 = st.columns([0.9,1.1,1.1,1.1])
with c1:
    pct = (dentro/total*100) if total>0 else 0
    st.markdown(f'<div class="gepp-card" style="background:#0f2a1a; color:white; padding:15px; height:320px; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center;"><p style="font-size:10px; color:#a0c4a8; font-weight:bold;">PLANTILLA DENTRO GEOCERCA</p><p style="font-size:42px; font-weight:800; margin:20px 0 0 0;">{pct:.1f}%</p><p style="font-size:11px;">DENTRO: {dentro} / {total}</p><div style="width:40px; height:40px; background:{"#00ff66" if pct>50 else "#ff0000"}; border-radius:50%; margin-top:15px;"></div></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="gepp-card"><div class="gepp-header">Plantilla Dentro Geocerca - ¿Dentro?</div>', unsafe_allow_html=True)
    fig = go.Figure(data=[go.Pie(labels=['FUERA','DENTRO'], values=[fuera, dentro], hole=0.65, marker_colors=['#ff0000','#0f3d1f'], textinfo='percent', textposition='inside', sort=False)])
    fig.update_layout(height=280, margin=dict(l=10,r=10,t=60,b=10), paper_bgcolor="white", showlegend=True, legend=dict(orientation="h", y=1.15, x=0.5, xanchor="center"))
    fig.update_traces(domain=dict(x=[0,1], y=[0,0.85]))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
with c3:
    st.markdown('<div class="gepp-card"><div class="gepp-header">Plantilla Completa - Horas Trabajadas</div>', unsafe_allow_html=True)
    comp = (df['Plantilla Completa']=='Completa').sum()
    fig2 = go.Figure(data=[go.Pie(labels=['Incompleta','Completa'], values=[total-comp, comp], hole=0.65, marker_colors=['#ff8c42','#0f3d1f'], textinfo='percent', textposition='inside', sort=False)])
    fig2.update_layout(height=280, margin=dict(l=10,r=10,t=60,b=10), paper_bgcolor="white", showlegend=True, legend=dict(orientation="h", y=1.15, x=0.5, xanchor="center"))
    fig2.update_traces(domain=dict(x=[0,1], y=[0,0.85]))
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
with c4:
    st.markdown('<div class="gepp-card"><div class="gepp-header">Semáforo Plantilla</div>', unsafe_allow_html=True)
    orden = ['Malo', 'Bueno', 'Excelente']
    colores_map = {'Malo': '#ff0000', 'Bueno': '#ffcc00', 'Excelente': '#00b050'}
    counts = df['Semáforo'].value_counts()
    valores = [counts.get(cat, 0) for cat in orden]
    colores = [colores_map[cat] for cat in orden]
    fig3 = go.Figure(data=[go.Pie(labels=orden, values=valores, hole=0.65, marker_colors=colores, sort=False, textinfo='percent', textposition='inside')])
    fig3.update_layout(height=280, margin=dict(l=10,r=10,t=60,b=10), paper_bgcolor="white", showlegend=True, legend=dict(orientation="h", y=1.15, x=0.5, xanchor="center"))
    fig3.update_traces(domain=dict(x=[0,1], y=[0,0.85]))
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# FILA 2 - AHORA LAS 2 ZEBRA WE
r2c1,r2c2,r2c3 = st.columns([1.4,1.0,1.0])
with r2c1:
    st.markdown('<div class="gepp-card"><div class="gepp-header">REGISTRO OPERATIVO / DETALLE POR EMPLEADO - ZEBRA PRO</div>', unsafe_allow_html=True)
    cols1 = ['Fecha','Hora Entrada','Hora Salida','Horas Trabajadas','Tiempo Extra','Nombre completo','Numero Empleado','¿Dentro?','Semáforo']
    cols1 = [c for c in cols1 if c in df.columns]
    df_r2 = df[cols1].tail(20).fillna("")
    components.html(render_zebra(df_r2, "340px"), height=360, scrolling=True)
    st.markdown("</div>", unsafe_allow_html=True)
with r2c2:
    st.markdown('<div class="gepp-card"><div class="gepp-header">COMPORTAMIENTO POR DÍA - Fecha</div>', unsafe_allow_html=True)
    try:
        df['Dia'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.day
        cnt = df.groupby('Dia').size().reset_index(name='Registros')
        fig_line = px.line(cnt, x='Dia', y='Registros', markers=True, color_discrete_sequence=['#0f3d1f'])
        fig_line.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", plot_bgcolor="white")
        st.plotly_chart(fig_line, use_container_width=True)
    except: st.write("Sin datos")
    st.markdown("</div>", unsafe_allow_html=True)
with r2c3:
    st.markdown('<div class="gepp-card"><div class="gepp-header">REGISTRO POR PLANTA / COORDINADOR</div>', unsafe_allow_html=True)
    if 'Planta' in df.columns:
        seg = df['Planta'].value_counts().reset_index()
        seg.columns=['Planta','Registros']
        fig_bar = px.bar(seg, x='Planta', y='Registros', color='Registros', color_continuous_scale='Greens', text='Registros')
        fig_bar.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=30), paper_bgcolor="white", showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# FILA 3 MAPA
r3c1,r3c2 = st.columns([1.2,0.8])
with r3c1:
    st.markdown('<div class="gepp-card"><div class="gepp-header">MAPA LIVE - Latitud / Longitud - Con Tráfico</div>', unsafe_allow_html=True)
    ver_traf = st.checkbox("Ver tráfico en vivo", value=True)
    if 'Latitud' in df.columns and 'Longitud' in df.columns:
        df_map = df.dropna(subset=['Latitud','Longitud']).copy()
        df_map['Latitud'] = pd.to_numeric(df_map['Latitud'], errors='coerce')
        df_map['Longitud'] = pd.to_numeric(df_map['Longitud'], errors='coerce')
        df_map = df_map.dropna(subset=['Latitud','Longitud'])
        if not df_map.empty:
            try:
                import folium
                from streamlit_folium import st_folium
                m = folium.Map(location=[df_map['Latitud'].mean(), df_map['Longitud'].mean()], zoom_start=12)
                if ver_traf:
                    folium.TileLayer(tiles='https://{s}.google.com/vt/lyrs=m@221097413,traffic&x={x}&y={y}&z={z}', attr='Google Traffic', subdomains=['mt0','mt1','mt2','mt3'], overlay=True).add_to(m)
                for _, row in df_map.tail(100).iterrows():
                    color = 'green' if str(row.get('¿Dentro?','')).upper()=='DENTRO' else 'red'
                    folium.CircleMarker(location=[row['Latitud'], row['Longitud']], radius=6, color=color, fill=True, popup=f"{row.get('Planta','')} - {row.get('Coordinador','')}").add_to(m)
                st_folium(m, width=700, height=350)
            except:
                st.map(df_map, latitude="Latitud", longitude="Longitud", zoom=12)
    st.markdown("</div>", unsafe_allow_html=True)
with r3c2:
    st.markdown('<div class="gepp-card"><div class="gepp-header">TIEMPO EXTRA - Horas Trabajadas</div>', unsafe_allow_html=True)
    if 'Horas Trabajadas' in df.columns:
        fig_hist = px.histogram(df, x='Horas Trabajadas', nbins=10, color_discrete_sequence=['#0f3d1f'])
        fig_hist.update_layout(height=300, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", plot_bgcolor="white")
        st.plotly_chart(fig_hist, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# FILA 4 TABLA ZEBRA PRO
st.markdown('<div class="gepp-card"><div class="gepp-header">DETALLE - PERSONAL - PRO ZEBRA - LEYENDO DEL DRIVE</div>', unsafe_allow_html=True)
cols_final = ['Fecha','Hora Entrada','Hora Salida','Horas Trabajadas','Nombre completo','Numero Empleado','Latitud','Longitud','¿Dentro?','Fotos','Planta','Coordinador','Semáforo']
cols_final = [c for c in cols_final if c in df.columns]
df_show = df[cols_final].tail(100).fillna("")
components.html(render_zebra(df_show, "500px"), height=520, scrolling=True)
st.markdown("</div>", unsafe_allow_html=True)

st.caption(f"© RED AMBIENTAL V42 PRO ZEBRA LIVE DRIVE | {total} registros | {planta_sel} | {coord_sel} | Búsqueda: {busqueda if busqueda else 'Todos'}")
