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

/* TABLA PRO ZEBRA WE - BLANCA / GRIS CLARO */
div[data-testid="stDataFrame"] table tbody tr:nth-child(even) {
    background-color: #f2f4f7!important;
}
div[data-testid="stDataFrame"] table tbody tr:nth-child(odd) {
    background-color: #ffffff!important;
}
div[data-testid="stDataFrame"] table tbody tr:hover {
    background-color: #d1e7dd!important;
}
div[data-testid="stDataFrame"] thead tr th {
    background-color: #0f3d1f!important;
    color: white!important;
    font-size: 11px!important;
}
</style>
""", unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRdHGoaJ3BSFqaU4DIH1Wks7dROyzp3z7Z_guIBoAD7VzSXCIis14R9HMPCaDmF3omEK5RzEDlua1aR/pub?gid=1011674108&single=true&output=csv"

@st.cache_data(ttl=10)
def load():
    df = pd.read_csv(URL)
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    # Quitamos Estatus Entrega si viene we
    if 'Estatus Entrega' in df.columns:
        df = df.drop(columns=['Estatus Entrega'])

    # MAPEO REAL - YA NO NAN WE
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

# SIDEBAR FILTROS
with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.markdown("<h2 style='color:white; text-align:center;'>♻️ RED AMBIENTAL</h2>", unsafe_allow_html=True)

    st.markdown("<p style='color:white; font-weight:bold;'>RED AMBIENTAL</p>", unsafe_allow_html=True)
    if st.button("🔄 ACTUALIZAR", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("<p style='color:#a0c4a8; font-size:11px; font-weight:bold;'>FILTROS</p>", unsafe_allow_html=True)

    # Fecha
    df_full['Fecha_dt'] = pd.to_datetime(df_full['Fecha'], dayfirst=True, errors='coerce')
    try:
        min_f = df_full['Fecha_dt'].min().date()
        max_f = df_full['Fecha_dt'].max().date()
        fecha_sel = st.date_input("Fecha", value=(min_f, max_f))
    except:
        fecha_sel = None

    plantas = ["Todas"] + sorted(df_full["Planta"].dropna().astype(str).unique().tolist()) if "Planta" in df_full.columns else ["Todas"]
    planta_sel = st.selectbox("Planta", plantas, key="planta")

    coords = ["Todos"] + sorted(df_full["Coordinador"].dropna().astype(str).unique().tolist()) if "Coordinador" in df_full.columns else ["Todos"]
    coord_sel = st.selectbox("Coordinador", coords, key="coord")

    dentro_sel = st.selectbox("¿Dentro?", ["Todos","DENTRO","FUERA"], key="dentro")

# FILTROS LOGICA
df = df_full.copy()
if fecha_sel and isinstance(fecha_sel, tuple) and len(fecha_sel)==2:
    try:
        df = df[(df['Fecha_dt'].dt.date >= fecha_sel[0]) & (df['Fecha_dt'].dt.date <= fecha_sel[1])]
    except:
        pass
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
df['Plantilla Completa'] = df['Horas Trabajadas'].apply(lambda x: 'Completa' if pd.notna(x) and str(x)!='' and str(x)!='None' else 'Incompleta')

total = len(df)
dentro = (df['¿Dentro?_NORM']=='DENTRO').sum()
fuera = total - dentro

st.markdown(f"""
<div style="background:#0f3d1f; color:white; padding:10px 15px; border-radius:6px; display:flex; justify-content:space-between;">
    <span style="font-weight:800;">RED AMBIENTAL | {planta_sel} | {coord_sel}</span>
    <span style="font-size:11px;">Total: {total} | DENTRO: {dentro} | FUERA: {fuera} | LIVE {pd.Timestamp.now().strftime('%H:%M')}</span>
</div>
""", unsafe_allow_html=True)
st.write("")

# FILA 1 DONAS
c1,c2,c3,c4 = st.columns([0.9,1.1,1.1,1.1])
with c1:
    pct = (dentro/total*100) if total>0 else 0
    st.markdown(f'<div class="gepp-card" style="background:#0f2a1a; color:white; padding:15px; height:320px;"><p style="font-size:10px; text-align:center; color:#a0c4a8; font-weight:bold;">PLANTILLA DENTRO GEOCERCA</p><p style="font-size:42px; font-weight:800; margin:20px 0 0 0;">{pct:.1f}%</p><p style="font-size:11px;">DENTRO: {dentro} / {total}</p><div style="width:40px; height:40px; background:{"#00ff66" if pct>50 else "#ff0000"}; border-radius:50%; margin-top:15px;"></div></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="gepp-card"><div class="gepp-header">Plantilla Dentro Geocerca - ¿Dentro?</div>', unsafe_allow_html=True)
    fig = go.Figure(data=[go.Pie(labels=['FUERA','DENTRO'], values=[fuera, dentro], hole=0.65, marker_colors=['#ff0000','#0f3d1f'])])
    fig.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", showlegend=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
with c3:
    st.markdown('<div class="gepp-card"><div class="gepp-header">Plantilla Completa - Horas Trabajadas</div>', unsafe_allow_html=True)
    comp = (df['Plantilla Completa']=='Completa').sum()
    fig2 = go.Figure(data=[go.Pie(labels=['Incompleta','Completa'], values=[total-comp, comp], hole=0.65, marker_colors=['#ff8c42','#0f3d1f'])])
    fig2.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", showlegend=True)
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
with c4:
    st.markdown('<div class="gepp-card"><div class="gepp-header">Semáforo Plantilla</div>', unsafe_allow_html=True)
    counts = df['Semáforo'].value_counts()
    fig3 = go.Figure(data=[go.Pie(labels=counts.index, values=counts.values, hole=0.65, marker_colors=['#00b050','#ffff00','#ff0000'])])
    fig3.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white")
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# FILA 2
r2c1,r2c2,r2c3 = st.columns([1.4,1.0,1.0])
with r2c1:
    st.markdown('<div class="gepp-card"><div class="gepp-header">REGISTRO OPERATIVO / DETALLE POR EMPLEADO - TUS TITULOS</div>', unsafe_allow_html=True)
    cols1 = ['Fecha','Hora Entrada','Hora Salida','Horas Trabajadas','Tiempo Extra','Nombre completo','Numero Empleado','¿Dentro?','Semáforo']
    cols1 = [c for c in cols1 if c in df.columns]
    st.dataframe(df[cols1].tail(12), use_container_width=True, height=320)
    st.markdown("</div>", unsafe_allow_html=True)
with r2c2:
    st.markdown('<div class="gepp-card"><div class="gepp-header">COMPORTAMIENTO POR DÍA - Fecha</div>', unsafe_allow_html=True)
    try:
        df['Dia'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce').dt.day
        cnt = df.groupby('Dia').size().reset_index(name='Registros')
        fig_line = px.line(cnt, x='Dia', y='Registros', markers=True, color_discrete_sequence=['#0f3d1f'])
        fig_line.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", plot_bgcolor="white")
        st.plotly_chart(fig_line, use_container_width=True)
    except:
        st.write("Sin datos")
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

# FILA 3 MAPA CON TRAFICO
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
            except Exception as e:
                st.map(df_map, latitude="Latitud", longitude="Longitud", zoom=12)
                st.caption(f"Instala: pip install folium streamlit-folium - {e}")
    st.markdown("</div>", unsafe_allow_html=True)
with r3c2:
    st.markdown('<div class="gepp-card"><div class="gepp-header">TIEMPO EXTRA - Horas Trabajadas</div>', unsafe_allow_html=True)
    if 'Horas Trabajadas' in df.columns:
        fig_hist = px.histogram(df, x='Horas Trabajadas', nbins=10, color_discrete_sequence=['#0f3d1f'])
        fig_hist.update_layout(height=300, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", plot_bgcolor="white")
        st.plotly_chart(fig_hist, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# FILA 4 TABLA ZEBRA PRO
st.markdown('<div class="gepp-card"><div class="gepp-header">DETALLE - PERSONAL - TUS TITULOS REALES SIN ESTATUS ENTREGA - PRO ZEBRA</div>', unsafe_allow_html=True)
cols_final = ['Fecha','Hora Entrada','Hora Salida','Horas Trabajadas','Tiempo Extra','Nombre completo','Numero Empleado','Latitud','Longitud','Distancia','¿Dentro?','Fotos','Planta','Coordinador','Plantilla Autorizada','Semáforo']
cols_final = [c for c in cols_final if c in df.columns]
st.dataframe(df[cols_final].tail(100), use_container_width=True, height=500, column_config={"Fotos": st.column_config.LinkColumn("Fotos", display_text="Ver")})
st.markdown("</div>", unsafe_allow_html=True)

st.caption(f"© RED AMBIENTAL V42 PRO ZEBRA | {total} registros | {planta_sel} | {coord_sel} | PRO")
