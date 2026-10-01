import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components
import requests, base64
from datetime import datetime
import pytz
import unicodedata

TZ_MEXICO = pytz.timezone("America/Monterrey")
st.set_page_config(page_title="Red Ambiental - V44.9 FIX ACENTOS", layout="wide", page_icon="♻️")
st.markdown("""
<style>
.stApp { background-color: #e9ecf2; }
section[data-testid="stSidebar"] { background-color: #0a2211; }
.gepp-card { background:white; border:1px solid #b0b8c8; border-radius:6px; overflow:hidden; margin-bottom:8px; box-shadow:0 1px 3px rgba(0,0,0,0.1); }
.gepp-header { background:#0f3d1f; color:white; padding:6px 12px; font-size:11px; font-weight:700; text-align:center; text-transform:uppercase; }
</style>
""", unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRdHGoaJ3BSFqaU4DIH1Wks7dROyzp3z7Z_guIBoAD7VzSXCIis14R9HMPCaDmF3omEK5RzEDlua1aR/pub?gid=1011674108&single=true&output=csv"
ID_SHEET_BOLETAS = "1-9KNHfB0syWmZNFGfti3mIEjTjFjbSz3qKiAiyXXvms"
URL_OPERADORES = "https://script.google.com/macros/s/AKfycbxfb7MVBqN_3xk5a9ICVa7X9zKWtH1s9PEfgv_QpU0iW54q6_gldoNgXbpHU8DztwI/exec"
ID_CATALOGO = ID_SHEET_BOLETAS
GID_CATALOGO = 1457146895

@st.cache_data(ttl=60)
def load():
    df = pd.read_csv(URL)
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    if 'Estatus Entrega' in df.columns: df = df.drop(columns=['Estatus Entrega'])
    mapa = {"BAXTER": "Eduardo Vidal","POLOMEX": "Felix Najera","AMAZON MTY1": "Felix Najera","AMAZON MTY2": "Felix Najera","AMAZON MTY3": "Felix Najera","JUEGOS DEL VALLE": "Felix Najera","CELESTICA": "Felix Najera","CATERPILLAR CIENEGA": "Sergio Llanes"}
    def get_coord(r):
        c = str(r.get("Coordinador","")).strip()
        if c.lower() not in ["","nan","none","sin asignar"]: return c
        return mapa.get(str(r.get("Planta","")).upper().strip(), "SIN ASIGNAR")
    if "Coordinador" not in df.columns: df["Coordinador"] = ""
    df["Coordinador"] = df.apply(get_coord, axis=1)
    for col_fix in ["Hora Entrada", "Hora Salida"]:
        if col_fix in df.columns:
            try:
                s = pd.to_datetime(df[col_fix], errors='coerce', utc=True)
                if s.notna().any():
                    s = s.dt.tz_convert(TZ_MEXICO).dt.tz_localize(None)
                    df[col_fix] = s.dt.strftime('%I:%M:%S %p')
                else:
                    s2 = pd.to_datetime(df[col_fix], errors='coerce')
                    df[col_fix] = (s2 - pd.Timedelta(hours=6)).dt.strftime('%I:%M:%S %p')
            except: pass
    return df

@st.cache_data(ttl=10)
def load_operadores():
    base_url = f"https://docs.google.com/spreadsheets/d/{ID_SHEET_BOLETAS}/export?format=csv&gid=0"
    url = base_url + f"&cachebust={datetime.now().strftime('%Y%m%d%H%M%S')}"
    try:
        df = pd.read_csv(url)
    except:
        fallback = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTib9TDIJwZ4QKnACiO-rLdyYIZCudCgaC-eSGSOSeZ5y4tQg4RsLZAq66aJMt83cfarOdD3MU2yHc5/pub?gid=0&single=true&output=csv"
        df = pd.read_csv(fallback)
    df.columns = df.columns.str.strip()
    return df

@st.cache_data(ttl=60)
def load_catalogo_operadores():
    return [
        "Agustin Castillo Sanchez",
        "Sergio Lozano Gonzalez",
        "Jorge Ibarra Serrato",
        "Alejandro Villarreal Bustamante",
        "Roberto Reyes Alanis",
        "Juan Estrada Guerra",
        "Luis Pérez Dominguez",
        "Roberto Garcia Navarro",
        "Ricardo Cazares Diaz",
        "Carlos Garcia Macias",
        "Francisco Mazuca Macias",
        "Kevin Rodriguez Lopez"
    ]

df_full = load()

def render_zebra(df_to_show, max_h="340px"):
    html = f"""<style>.zebra-table{{width:100%;border-collapse:collapse;font-size:11px;font-family:Arial;}}.zebra-table th{{background:#0f3d1f;color:white;padding:8px;text-align:left;position:sticky;top:0;z-index:2;}}.zebra-table td{{padding:7px 8px;border-bottom:1px solid #e0e0e0;}}.zebra-table tr:nth-child(even){{background:#f2f4f7;}}.zebra-table tr:nth-child(odd){{background:#ffffff;}}.zebra-table tr:hover{{background:#d1e7dd!important;}}.badge-dentro{{background:#00b050;color:white;padding:2px 6px;border-radius:10px;font-weight:bold;font-size:10px;}}.badge-fuera{{background:#ff0000;color:white;padding:2px 6px;border-radius:10px;font-weight:bold;font-size:10px;}}.badge-excelente{{background:#00b050;color:white;padding:2px 6px;border-radius:10px;font-weight:bold;font-size:10px;}}.badge-bueno{{background:#ffcc00;color:black;padding:2px 6px;border-radius:10px;font-weight:bold;font-size:10px;}}.badge-malo{{background:#ff0000;color:white;padding:2px 6px;border-radius:10px;font-weight:bold;font-size:10px;}}</style><div style="max-height:{max_h}; overflow:auto; background:white; border-radius:0 0 6px 6px;"><table class="zebra-table"><thead><tr>"""
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
            elif str(val).startswith("http"): html += f'<td><a href="{val}" target="_blank" style="color:#0f3d1f; font-weight:bold;">Ver</a></td>'
            else: html += f"<td>{val}</td>"
        html += "</tr>"
    html += "</tbody></table></div>"
    return html

with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: st.markdown("<h2 style='color:white; text-align:center;'>♻️ RED AMBIENTAL</h2>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#00ff88; text-align:center;'>MENU PRINCIPAL</h3>", unsafe_allow_html=True)
    menu = st.selectbox("🔍 Buscar módulo", ["📊 Dashboard Asistencias", "🚛 Operadores Pesaje", "⛽ Rendimiento Combustible"])
    st.markdown("---")
    if st.button("🔄 ACTUALIZAR TODO", type="primary", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.markdown("---")
    if menu == "📊 Dashboard Asistencias":
        df_full['Fecha_dt'] = pd.to_datetime(df_full['Fecha'], dayfirst=True, errors='coerce')
        try:
            min_f = df_full['Fecha_dt'].min().date(); max_f = df_full['Fecha_dt'].max().date()
            fecha_sel = st.date_input("Fecha", value=(min_f, max_f))
        except: fecha_sel = None
        plantas = ["Todas"] + sorted(df_full["Planta"].dropna().astype(str).unique().tolist()) if "Planta" in df_full.columns else ["Todas"]
        planta_sel = st.selectbox("Planta", plantas)
        coords = ["Todos"] + sorted(df_full["Coordinador"].dropna().astype(str).unique().tolist()) if "Coordinador" in df_full.columns else ["Todos"]
        coord_sel = st.selectbox("Coordinador", coords)
        dentro_sel = st.selectbox("¿Dentro?", ["Todos","DENTRO","FUERA"])

if menu == "📊 Dashboard Asistencias":
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
    total = len(df); dentro = (df['¿Dentro?_NORM']=='DENTRO').sum(); fuera = total - dentro
    components.html(f"""<div style="background:#0f3d1f; color:white; padding:10px 15px; border-radius:6px; display:flex; justify-content:space-between; align-items:center; font-family:Arial;"><span style="font-weight:800; font-size:14px;">RED AMBIENTAL | {planta_sel} | {coord_sel}</span><div style="text-align:right; font-size:11px;"><div>Total: {total} | DENTRO: {dentro} | FUERA: {fuera}</div><div id="reloj" style="font-weight:800; font-size:13px; color:#00ff88;"></div></div></div><script>function actualizarReloj(){{const ahora=new Date().toLocaleString("es-MX",{{timeZone:"America/Monterrey",weekday:'long',year:'numeric',month:'long',day:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:true}});document.getElementById("reloj").innerHTML="🕒 "+ahora.toUpperCase()+" | LIVE";}}setInterval(actualizarReloj,1000);actualizarReloj();</script>""", height=75)
    st.write("")
    busqueda = st.text_input("🔍 Buscar por Nombre, # Empleado, Planta, Coordinador, Fecha...", placeholder="Escribe aquí para filtrar...", key="buscador_global")
    if busqueda:
        busq = busqueda.upper().strip(); mask = False
        for col in ['Nombre completo','Numero Empleado','Planta','Coordinador','Fecha','Semáforo','¿Dentro?']:
            if col in df.columns:
                if isinstance(mask, bool): mask = df[col].astype(str).str.upper().str.contains(busq, na=False)
                else: mask = mask | df[col].astype(str).str.upper().str.contains(busq, na=False)
        if isinstance(mask, pd.Series):
            df = df[mask]; total = len(df); dentro = (df['¿Dentro?_NORM']=='DENTRO').sum(); fuera = total - dentro
    c1,c2,c3,c4 = st.columns([0.9,1.1,1.1,1.1])
    with c1:
        pct = (dentro/total*100) if total>0 else 0
        st.markdown(f'<div class="gepp-card" style="background:#0f2a1a; color:white; padding:15px; height:260px; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center;"><p style="font-size:10px; color:#a0c4a8; font-weight:bold;">PLANTILLA DENTRO GEOCERCA</p><p style="font-size:36px; font-weight:800; margin:15px 0 0 0;">{pct:.1f}%</p><p style="font-size:11px;">DENTRO: {dentro} / {total}</p><div style="width:35px; height:35px; background:{"#00ff66" if pct>50 else "#ff0000"}; border-radius:50%; margin-top:10px;"></div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="gepp-card"><div class="gepp-header">¿Dentro?</div>', unsafe_allow_html=True)
        fig = go.Figure(data=[go.Pie(labels=['FUERA','DENTRO'], values=[fuera, dentro], hole=0.70, marker_colors=['#ff0000','#0f3d1f'], textinfo='percent', textposition='inside', sort=False)])
        fig.update_layout(height=260, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", showlegend=True, legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center", font=dict(size=10)))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="gepp-card"><div class="gepp-header">Completa</div>', unsafe_allow_html=True)
        comp = (df['Plantilla Completa']=='Completa').sum()
        fig2 = go.Figure(data=[go.Pie(labels=['Incompleta','Completa'], values=[total-comp, comp], hole=0.70, marker_colors=['#ff8c42','#0f3d1f'], textinfo='percent', textposition='inside', sort=False)])
        fig2.update_layout(height=260, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", showlegend=True, legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center", font=dict(size=10)))
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="gepp-card"><div class="gepp-header">Semáforo</div>', unsafe_allow_html=True)
        orden = ['Malo', 'Bueno', 'Excelente']; colores_map = {'Malo': '#ff0000', 'Bueno': '#ffcc00', 'Excelente': '#00b050'}
        counts = df['Semáforo'].value_counts(); valores = [counts.get(cat, 0) for cat in orden]; colores = [colores_map[cat] for cat in orden]
        fig3 = go.Figure(data=[go.Pie(labels=orden, values=valores, hole=0.70, marker_colors=colores, sort=False, textinfo='percent', textposition='inside')])
        fig3.update_layout(height=260, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", showlegend=True, legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center", font=dict(size=10)))
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
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
    st.markdown('<div class="gepp-card"><div class="gepp-header">DETALLE - PERSONAL - PRO ZEBRA - LEYENDO DEL DRIVE</div>', unsafe_allow_html=True)
    cols_final = ['Fecha','Hora Entrada','Hora Salida','Horas Trabajadas','Nombre completo','Numero Empleado','Latitud','Longitud','¿Dentro?','Fotos','Planta','Coordinador','Semáforo']
    cols_final = [c for c in cols_final if c in df.columns]
    df_show = df[cols_final].tail(100).fillna("")
    components.html(render_zebra(df_show, "500px"), height=520, scrolling=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "🚛 Operadores Pesaje":
    st.markdown("<h1 style='color:#0f3d1f; text-align:center;'>RED AMBIENTAL</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='color:#2e7d32; text-align:center;'>🚛 Dashboard Operadores - Pesaje</h2>", unsafe_allow_html=True)
    with st.expander("📝 Registrar Nuevo Viaje", expanded=False):
        c1,c2 = st.columns(2)
        with c1:
            nombre = st.text_input("Nombre Completo", placeholder="Ej: Juan Perez Lopez", key="op_n")
            unidad = st.text_input("Numero de Unidad", placeholder="Ej: 1234", key="op_u")
        with c2:
            base = st.text_input("Base donde se encuentra", placeholder="Garcia, Cienega...", key="op_b")
            foto = st.file_uploader("Foto Boleta", type=["jpg","jpeg","png"], key="op_f")
        if st.button("💾 Guardar Registro Operador", type="primary", use_container_width=True):
            if not nombre or not unidad or not base or not foto:
                st.error("❌ Complete todos los campos obligatorios")
            else:
                with st.spinner("Procesando..."):
                    b64 = base64.b64encode(foto.getvalue()).decode('utf-8')
                    b64 = f"data:{foto.type};base64,{b64}"
                    payload = {"nombreCompleto": nombre, "unidad": unidad, "base": base, "foto": b64}
                    requests.post(URL_OPERADORES, json=payload, headers={"Content-Type":"text/plain;charset=utf-8"}, timeout=30)
                    st.success("✅ Registro guardado correctamente"); st.balloons()
                    st.cache_data.clear()
    try:
        df_op = load_operadores()
        col_nombre = [c for c in df_op.columns if 'nombre' in c.lower()][0]
        col_unidad = [c for c in df_op.columns if 'unidad' in c.lower()][0]
        col_base = [c for c in df_op.columns if 'base' in c.lower()][0]
        META_DIARIA = 3
        col_fecha = None
        for c in df_op.columns:
            if 'marca' in c.lower() or 'timestamp' in c.lower() or 'fecha' in c.lower():
                col_fecha = c; break
        hoy_mty = datetime.now(TZ_MEXICO).date()
        try:
            df_op['fecha_solo_dt'] = pd.to_datetime(df_op[col_fecha], errors='coerce', dayfirst=True)
            if df_op['fecha_solo_dt'].isna().sum() > len(df_op)//2:
                df_op['fecha_solo_dt'] = pd.to_datetime(df_op[col_fecha], errors='coerce', dayfirst=False)
            df_op['fecha_solo'] = df_op['fecha_solo_dt'].dt.date
            df_op['fecha_solo'] = df_op['fecha_solo'].fillna(hoy_mty)
        except:
            df_op['fecha_solo'] = hoy_mty
        df_hoy = df_op[df_op['fecha_solo'] == hoy_mty].copy() if 'fecha_solo' in df_op.columns else pd.DataFrame()
        if not df_hoy.empty:
            df_mostrar = df_hoy
            etiqueta_fecha = f"{hoy_mty.strftime('%d/%m/%Y')} - HOY"
            es_hoy = True
        else:
            if not df_op.empty and df_op['fecha_solo'].notna().any():
                ultima_fecha = df_op['fecha_solo'].max()
                df_mostrar = df_op[df_op['fecha_solo'] == ultima_fecha].copy()
                etiqueta_fecha = f"{ultima_fecha.strftime('%d/%m/%Y')} - ULTIMO DIA"
                es_hoy = False
            else:
                df_mostrar = pd.DataFrame()
                etiqueta_fecha = f"{hoy_mty.strftime('%d/%m/%Y')} - HOY"
                es_hoy = True
        if not df_mostrar.empty:
            prod_hoy = df_mostrar[col_nombre].value_counts().reset_index()
            prod_hoy.columns = ['Operador','Viajes_Hoy']
            prod_hoy['Productividad_%'] = (prod_hoy['Viajes_Hoy'] / META_DIARIA * 100).round(1)
            prod_hoy = prod_hoy.sort_values('Productividad_%', ascending=True)
            total_viajes_mostrar = len(df_mostrar)
            ops_hoy = prod_hoy.shape[0]
        else:
            prod_hoy = pd.DataFrame()
            total_viajes_mostrar = 0
            ops_hoy = 0
        c1,c2,c3,c4 = st.columns([0.9,1.1,1.1,1.1])
        with c1:
            color_prod = "#00b050" if total_viajes_mostrar>=3 else "#ffcc00" if total_viajes_mostrar>=1 else "#ff0000"
            st.markdown(f'''
            <div class="gepp-card" style="background:#0f2a1a; color:white; padding:15px; height:260px; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center;">
                <p style="font-size:11px; color:#a0c4a8; font-weight:bold;">TOTAL BOLETAS<br>{etiqueta_fecha}</p>
                <p style="font-size:52px; font-weight:900; margin:10px 0; line-height:1;">{total_viajes_mostrar}</p>
                <p style="font-size:13px; font-weight:bold; color:#00ff88;">BOLETAS</p>
                <p style="font-size:11px; margin-top:5px;">Operadores: {ops_hoy}<br>Acumulado: {len(df_op)}</p>
                <div style="width:40px; height:40px; background:{color_prod}; border-radius:50%; margin-top:10px; border:2px solid white;"></div>
            </div>
            ''', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="gepp-card"><div class="gepp-header">Viajes por Operador - Dona</div>', unsafe_allow_html=True)
            cnt_op = df_op[col_nombre].value_counts().reset_index(); cnt_op.columns = ['Operador','Viajes']
            fig = go.Figure(data=[go.Pie(labels=cnt_op['Operador'], values=cnt_op['Viajes'], hole=0.70, textinfo='percent', textposition='inside')])
            fig.update_layout(height=260, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", showlegend=True, legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center", font=dict(size=9)))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="gepp-card"><div class="gepp-header">Viajes por Base - Dona</div>', unsafe_allow_html=True)
            cnt_base = df_op[col_base].value_counts().reset_index(); cnt_base.columns = ['Base','Viajes']
            fig2 = go.Figure(data=[go.Pie(labels=cnt_base['Base'], values=cnt_base['Viajes'], hole=0.70, textinfo='label+percent', textposition='inside', marker=dict(colors=px.colors.sequential.Greens_r))])
            fig2.update_layout(height=260, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with c4:
            st.markdown('<div class="gepp-card"><div class="gepp-header">Top Unidades</div>', unsafe_allow_html=True)
            cnt_uni = df_op[col_unidad].value_counts().head(10).reset_index(); cnt_uni.columns = ['Unidad','Viajes']
            fig3 = px.bar(cnt_uni, x='Unidad', y='Viajes', text='Viajes', color='Viajes', color_continuous_scale='Greens')
            fig3.update_layout(height=260, margin=dict(l=10,r=10,t=10,b=30), paper_bgcolor="white", showlegend=False)
            fig3.update_traces(textposition='outside')
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        if not es_hoy:
            st.warning(f"⚠️ Hoy {hoy_mty.strftime('%d/%m/%Y')} aún no hay boletas. Mostrando último día: {etiqueta_fecha} - {total_viajes_mostrar} boletas")

        # BLOQUE FIX FUZZY - SOLO ESTO CAMBIA
        st.markdown('<div class="gepp-card"><div class="gepp-header">🚨 OPERADORES SIN REGISTRO - SOLO HOY - 12 REALES (FIX FUZZY CARLOS)</div>', unsafe_allow_html=True)
        catalogo_completo = load_catalogo_operadores()
        registrados_hoy = df_hoy[col_nombre].astype(str).str.strip().unique().tolist() if not df_hoy.empty else []

        def norm(s):
            s = str(s).strip()
            s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c)!= 'Mn')
            s = ' '.join(s.split()).upper()
            return s

        def es_mismo(reg, cat):
            r = norm(reg)
            c = norm(cat)
            if r == c: return True
            if r in c or c in r: return True
            pr = r.split()
            pc = c.split()
            if len(pr)>=2 and len(pc)>=2 and pr[0]==pc[0] and pr[1]==pc[1]:
                return True
            return False

        faltantes_hoy = []
        for cat in catalogo_completo:
            if not any(es_mismo(reg, cat) for reg in registrados_hoy):
                faltantes_hoy.append(cat)

        con_hoy_real = len(catalogo_completo) - len(faltantes_hoy)

        cs1, cs2 = st.columns([0.35, 0.65])
        with cs1:
            st.metric("Con Boleta HOY", con_hoy_real)
            st.metric("SIN Boleta HOY", len(faltantes_hoy), delta=f"-{len(faltantes_hoy)}", delta_color="inverse")
            st.caption(f"Catalogo: {len(catalogo_completo)} operadores | Registros hoy: {len(registrados_hoy)}")
            if len(faltantes_hoy)+con_hoy_real>0:
                fig_f = go.Figure(data=[go.Pie(labels=['Con HOY','Sin HOY'], values=[con_hoy_real, len(faltantes_hoy)], hole=0.65, marker_colors=['#00b050','#ff0000'], textinfo='label+value')])
                fig_f.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white")
                st.plotly_chart(fig_f, use_container_width=True)
        with cs2:
            if faltantes_hoy:
                df_falt = pd.DataFrame(faltantes_hoy, columns=['Operador - SIN REGISTRO HOY'])
                df_falt['Estatus'] = '❌ FALTA HOY'
                df_falt['Fecha'] = hoy_mty.strftime('%d/%m/%Y')
                components.html(render_zebra(df_falt, "400px"), height=420, scrolling=True)
                st.download_button("📥 Descargar Faltantes HOY", df_falt.to_csv(index=False).encode('utf-8'), f"faltantes_SOLO_HOY_{hoy_mty}.csv", "text/csv", use_container_width=True)
            else:
                st.success(f"✅ ¡TODOS los {len(catalogo_completo)} registraron HOY!")
                st.balloons()
                df_vacia = pd.DataFrame(columns=['Operador - SIN REGISTRO HOY'])
                components.html(render_zebra(df_vacia, "100px"), height=120, scrolling=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="gepp-card"><div class="gepp-header">📊 PRODUCTIVIDAD DIARIA POR OPERADOR - BARRA</div>', unsafe_allow_html=True)
        if not prod_hoy.empty:
            fig_prod = px.bar(prod_hoy, x='Productividad_%', y='Operador', orientation='h', text='Productividad_%', color='Productividad_%', color_continuous_scale=['#ff0000','#ffcc00','#00b050'], range_color=[0,150])
            fig_prod.add_vline(x=100, line_dash="dash", line_color="green", annotation_text="100% = 3 viajes")
            fig_prod.update_layout(height=400, margin=dict(l=10,r=60,t=20,b=10), paper_bgcolor="white", plot_bgcolor="white", showlegend=False)
            fig_prod.update_traces(texttemplate='%{text:.0f}% - %{customdata} viajes', customdata=prod_hoy['Viajes_Hoy'], textposition='outside')
            st.plotly_chart(fig_prod, use_container_width=True)
        else:
            st.info(f"Sin registros el día {hoy_mty.strftime('%d/%m/%Y')}.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<div class="gepp-card"><div class="gepp-header">📊 Ranking - Total de viajes por operador</div>', unsafe_allow_html=True)
        cnt_op_bar = df_op[col_nombre].value_counts().reset_index(); cnt_op_bar.columns = ['Operador','Viajes']
        cnt_op_bar = cnt_op_bar.sort_values('Viajes', ascending=True)
        fig_bar = px.bar(cnt_op_bar, x='Viajes', y='Operador', orientation='h', text='Viajes', color='Viajes', color_continuous_scale='Greens')
        fig_bar.update_layout(height=400, margin=dict(l=10,r=40,t=20,b=10), paper_bgcolor="white", plot_bgcolor="white", showlegend=False)
        fig_bar.update_traces(textposition='outside')
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<div class="gepp-card"><div class="gepp-header">DETALLE REGISTROS OPERADORES - TABLA</div>', unsafe_allow_html=True)
        cols_ocultar = [c for c in df_op.columns if 'fecha_solo' in c.lower()]
        df_show_op = df_op.drop(columns=cols_ocultar, errors='ignore').tail(100).fillna("").iloc[::-1]
        components.html(render_zebra(df_show_op, "500px"), height=540, scrolling=True)
        st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"No fue posible cargar la información de operadores: {e}")
        st.exception(e)
else:
    st.title("⛽ Rendimiento de Combustible - Próximamente")
    st.info("Módulo en preparación")
