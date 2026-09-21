import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Red Ambiental - Completo Restaurado", layout="wide", page_icon="♻️")

st.markdown("""
<style>
.stApp { background-color: #e9ecf2; }
section[data-testid="stSidebar"] { background-color: #0a2211; }
.gepp-card { background:white; border:1px solid #b0b8c8; border-radius:3px; overflow:hidden; margin-bottom:8px; box-shadow:0 1px 2px rgba(0,0,0,0.1); }
.gepp-header { background:#0f3d1f; color:white; padding:6px 12px; font-size:11px; font-weight:700; text-align:center; text-transform:uppercase; }
</style>
""", unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRdHGoaJ3BSFqaU4DIH1Wks7dROyzp3z7Z_guIBoAD7VzSXCIis14R9HMPCaDmF3omEK5RzEDlua1aR/pub?gid=1011674108&single=true&output=csv"

@st.cache_data(ttl=10)
def load():
    df = pd.read_csv(URL)
    df.columns = df.columns.str.strip()
    return df.loc[:, ~df.columns.str.contains('^Unnamed')]

with st.sidebar:
    st.image("logo.png", use_container_width=True)
    st.markdown("<p style='color:white; font-weight:bold;'>RED AMBIENTAL</p>", unsafe_allow_html=True)
    if st.button("🔄 ACTUALIZAR", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.selectbox("Planta", ["Todas","Base García"], key="planta")

df = load()

def norm(v): return str(v).upper().strip() if pd.notna(v) else "FUERA"
df['¿Dentro?_NORM'] = df['¿Dentro?'].apply(norm) if '¿Dentro?' in df.columns else "FUERA"

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

# HEADER
st.markdown(f"""
<div style="background:#0f3d1f; color:white; padding:10px 15px; border-radius:3px; display:flex; justify-content:space-between;">
    <span style="font-weight:800;">red ambiental | Control Plantilla - Restaurado</span>
    <span style="font-size:11px;">Total: {total} | DENTRO: {dentro} | FUERA: {fuera} | LIVE {pd.Timestamp.now().strftime('%H:%M')}</span>
</div>
""", unsafe_allow_html=True)
st.write("")

# --- FILA 1: 3 DONAS + KPI (COMO YA TENIAMOS) ---
c1,c2,c3,c4 = st.columns([0.9,1.1,1.1,1.1])

with c1:
    pct = (dentro/total*100) if total>0 else 0
    st.markdown(f'<div class="gepp-card" style="background:#0f2a1a; color:white; padding:15px; height:320px;"><p style="font-size:10px; text-align:center; color:#a0c4a8; font-weight:bold;">PLANTILLA DENTRO GEOCERCA</p><p style="font-size:42px; font-weight:800; margin:20px 0 0 0;">{pct:.1f}%</p><p style="font-size:11px; margin-top:5px;">DENTRO: {dentro} / {total}</p><div style="width:40px; height:40px; background:{"#00ff66" if pct>50 else "#ff0000"}; border-radius:50%; margin-top:15px;"></div><p style="font-size:10px; margin-top:20px;">Horas Prom: {pd.to_numeric(df["Horas Trabajadas"], errors="coerce").mean():.2f} hrs</p><p style="font-size:9px; opacity:0.6;">Dist: {df["Distancia"].iloc[-1] if "Distancia" in df.columns else ""} mts</p></div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="gepp-card"><div class="gepp-header">Plantilla Dentro Geocerca - ¿Dentro?</div>', unsafe_allow_html=True)
    fig = go.Figure(data=[go.Pie(labels=['FUERA','DENTRO'], values=[fuera, dentro], hole=0.65, marker_colors=['#ff0000','#0f3d1f'])])
    fig.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", showlegend=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c3:
    st.markdown('<div class="gepp-card"><div class="gepp-header">Plantilla Completa - Horas Trabajadas</div>', unsafe_allow_html=True)
    comp = (df['Plantilla Completa']=='Completa').sum()
    inc = total - comp
    fig2 = go.Figure(data=[go.Pie(labels=['Incompleta','Completa'], values=[inc, comp], hole=0.65, marker_colors=['#ff8c42','#0f3d1f'])])
    fig2.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", showlegend=True)
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c4:
    st.markdown('<div class="gepp-card"><div class="gepp-header">Semáforo Plantilla</div>', unsafe_allow_html=True)
    counts = df['Semáforo'].value_counts()
    fig3 = go.Figure(data=[go.Pie(labels=counts.index, values=counts.values, hole=0.65, marker_colors=['#00b050','#ffff00','#ff0000'])])
    fig3.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", legend=dict(font_size=10))
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- FILA 2: LAS GRAFICAS QUE SE BORRARON - RESTAURADAS ---
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
        fig_line.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", plot_bgcolor="white", xaxis_title="Día", yaxis_title="Registros")
        st.plotly_chart(fig_line, use_container_width=True)
    except:
        st.write("Sin datos Fecha")
    st.markdown("</div>", unsafe_allow_html=True)

with r2c3:
    st.markdown('<div class="gepp-card"><div class="gepp-header">REGISTRO POR PLANTA / COORDINADOR</div>', unsafe_allow_html=True)
    if 'Planta' in df.columns:
        seg = df['Planta'].value_counts().reset_index()
        seg.columns=['Planta','Registros']
        fig_bar = px.bar(seg, x='Planta', y='Registros', color='Registros', color_continuous_scale='Greens', text='Registros')
        fig_bar.update_layout(height=320, margin=dict(l=10,r=10,t=10,b=30), paper_bgcolor="white", plot_bgcolor="white", showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- FILA 3: MAPA + TIEMPO EXTRA (ESTA TAMBIEN SE HABIA BORRADO) ---
r3c1,r3c2 = st.columns([1.2,0.8])
with r3c1:
    st.markdown('<div class="gepp-card"><div class="gepp-header">MAPA LIVE - Latitud / Longitud</div>', unsafe_allow_html=True)
    if 'Latitud' in df.columns and 'Longitud' in df.columns:
        df_map = df.dropna(subset=['Latitud','Longitud']).copy()
        df_map['Latitud'] = pd.to_numeric(df_map['Latitud'], errors='coerce')
        df_map['Longitud'] = pd.to_numeric(df_map['Longitud'], errors='coerce')
        st.map(df_map, latitude="Latitud", longitude="Longitud", zoom=12, height=300)
    st.markdown("</div>", unsafe_allow_html=True)

with r3c2:
    st.markdown('<div class="gepp-card"><div class="gepp-header">TIEMPO EXTRA - Horas Trabajadas</div>', unsafe_allow_html=True)
    if 'Horas Trabajadas' in df.columns:
        fig_hist = px.histogram(df, x='Horas Trabajadas', nbins=10, color_discrete_sequence=['#0f3d1f'])
        fig_hist.update_layout(height=300, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", plot_bgcolor="white")
        st.plotly_chart(fig_hist, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- FILA 4: TABLA DETALLE COMPLETA ---
st.markdown('<div class="gepp-card"><div class="gepp-header">DETALLE - PERSONAL - TUS TITULOS REALES SIN ESTATUS ENTREGA</div>', unsafe_allow_html=True)
cols_final = ['Fecha','Hora Entrada','Hora Salida','Horas Trabajadas','Tiempo Extra','Nombre completo','Numero Empleado','Latitud','Longitud','Distancia','¿Dentro?','Fotos','Planta','Coordinador','Plantilla Autorizada','Semáforo']
cols_final = [c for c in cols_final if c in df.columns]
st.dataframe(df[cols_final].tail(50), use_container_width=True, height=400, column_config={"Fotos": st.column_config.LinkColumn("Fotos")})
st.markdown("</div>", unsafe_allow_html=True)

st.caption(f"© RED AMBIENTAL V41 RESTAURADO | Todas las gráficas de vuelta | {total} registros | Distancia {df['Distancia'].iloc[-1] if 'Distancia' in df.columns else ''} mts = FUERA (estás a 11km we)")