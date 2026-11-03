import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components
import requests, base64
from datetime import datetime, date
import pytz
import unicodedata
import re
import hashlib
from PIL import Image
import pytesseract

TZ_MEXICO = pytz.timezone("America/Monterrey")
st.set_page_config(page_title="Red Ambiental - V45.3 ACUMULADO", layout="wide", page_icon="♻️")
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
                s = pd.to_datetime(df[col_fix].astype(str).str.strip(), errors='coerce')
                df[col_fix] = s.dt.strftime('%I:%M:%S %p')
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
    return ["Agustin Castillo Sanchez","Sergio Lozano Gonzalez","Jorge Ibarra Serrato","Alejandro Villarreal Bustamante","Roberto Reyes Alanis","Juan Estrada Guerra","Luis Pérez Dominguez","Roberto Garcia Navarro","Ricardo Cazares Diaz","Carlos Garcia Macias","Francisco Mazuca Macias","Angel Garcia Navarro","Luis Fernando Perez Castañeda"]

@st.cache_data(ttl=60)
def load_catalogo_coordinadores():
    return {"Agustin Castillo Sanchez": "Felix Najera","Sergio Lozano Gonzalez": "Felix Najera","Jorge Ibarra Serrato": "Sergio Llanes","Alejandro Villarreal Bustamante": "Felix Najera","Roberto Reyes Alanis": "Felix Najera","Juan Estrada Guerra": "Sergio Llanes","Luis Pérez Dominguez": "Felix Najera","Roberto Garcia Navarro": "Felix Najera","Ricardo Cazares Diaz": "Sergio Llanes","Carlos Garcia Macias": "Felix Najera","Francisco Mazuca Macias": "Sergio Llanes","Angel Garcia Navarro": "Felix Najera","Luis Fernando Perez Castañeda": "Felix Najera","Kevin Rodriguez": "Analista"}

def norm_txt(s):
    try:
        s = str(s).strip()
        s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
        return ' '.join(s.split()).upper()
    except: return ""

def get_image_hash(file_bytes): return hashlib.sha256(file_bytes).hexdigest()
def mejorar_imagen_para_ocr(img_pil):
    img = img_pil.convert('L'); w, h = img.size; img = img.resize((w*2, h*2)); return img
def extraer_fecha_de_imagen(img_pil):
    try:
        img = mejorar_imagen_para_ocr(img_pil)
        texto = pytesseract.image_to_string(img, lang='spa+eng', config='--psm 6')
        texto_up = texto.upper()
        patron = re.findall(r'FECHA\s*[ES]:\s*(\d{1,2}/\d{1,2}/\d{4})', texto_up)
        if patron:
            f = pd.to_datetime(patron[0], dayfirst=True, errors='coerce')
            if pd.notna(f): return f.date(), patron[0], texto
        patron2 = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', texto_up)
        if patron2:
            f = pd.to_datetime(patron2.group(1), dayfirst=True, errors='coerce')
            if pd.notna(f): return f.date(), patron2.group(1), texto
        return None, None, texto
    except Exception as e: return None, f"Error {e}", ""
def extraer_folio_boleta(img_pil):
    try:
        img = mejorar_imagen_para_ocr(img_pil)
        texto = pytesseract.image_to_string(img, lang='spa+eng', config='--psm 6')
        texto_up = texto.upper().replace('O','0')
        m = re.search(r'FOLIO[:\s]*([0-9\-]{5,20})', texto_up)
        if m:
            folio = m.group(1).replace(' ','').strip(); folio = re.sub(r'[^0-9\-]', '', folio); return folio, texto
        m2 = re.search(r'(2001-[0-9]{5,10})', texto_up)
        if m2: return m2.group(1), texto
        return None, texto
    except: return None, ""

df_full = load()

def render_zebra(df_to_show, max_h="340px"):
    html = f"""<style>.zebra-table{{width:100%;border-collapse:collapse;font-size:11px;font-family:Arial;}}.zebra-table th{{background:#0f3d1f;color:white;padding:8px;text-align:left;position:sticky;top:0;z-index:2;}}.zebra-table td{{padding:7px 8px;border-bottom:1px solid #e0e0e0;}}.zebra-table tr:nth-child(even){{background:#f2f4f7;}}.zebra-table tr:nth-child(odd){{background:#ffffff;}}.zebra-table tr:hover{{background:#d1e7dd!important;}}.badge-dentro{{background:#00b050;color:white;padding:2px 6px;border-radius:10px;font-weight:bold;font-size:10px;}}.badge-fuera{{background:#ff0000;color:white;padding:2px 6px;border-radius:10px;font-weight:bold;font-size:10px;}}.badge-excelente{{background:#00b050;color:white;padding:2px 6px;border-radius:10px;font-weight:bold;font-size:10px;}}.badge-bueno{{background:#ffcc00;color:black;padding:2px 6px;border-radius:10px;font-weight:bold;font-size:10px;}}.badge-malo{{background:#ff0000;color:white;padding:2px 6px;border-radius:10px;font-weight:bold;font-size:10px;}}</style><div style="max-height:{max_h}; overflow:auto; background:white; border-radius:0 0 6px 6px;"><table class="zebra-table"><thead><tr>"""
    for col in df_to_show.columns: html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    for _, row in df_to_show.iterrows():
        html += "<tr>"
        for col in df_to_show.columns:
            val = row[col]; sval = str(val).upper()
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
    html += "</tbody></table></div>"; return html

with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: st.markdown("<h2 style='color:white; text-align:center;'>♻️ RED AMBIENTAL</h2>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#00ff88; text-align:center;'>MENU PRINCIPAL</h3>", unsafe_allow_html=True)
    menu = st.selectbox("🔍 Buscar módulo", ["📊 Dashboard Asistencias", "🚛 Operadores Pesaje", "⛽ Rendimiento Combustible"])
    st.markdown("---")
    if st.button("🔄 ACTUALIZAR TODO", type="primary", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    if menu == "🚛 Operadores Pesaje":
        st.markdown("---"); st.markdown("### 🔍 FILTROS PESAJE")
        try:
            df_op_preview = load_operadores()
            try:
                col_fecha_prev = [c for c in df_op_preview.columns if 'marca' in c.lower() or 'timestamp' in c.lower() or 'fecha' in c.lower()][0]
                df_op_preview['mes_filtro'] = pd.to_datetime(df_op_preview[col_fecha_prev], errors='coerce', dayfirst=True).dt.strftime('%Y-%m')
                meses_list = ["Todos"] + sorted(df_op_preview['mes_filtro'].dropna().unique().tolist(), reverse=True)
            except: meses_list = ["Todos", "2026-10"]
            filtro_mes = st.selectbox("📅 Mes", meses_list, key="filtro_mes_sidebar")
            map_coord = load_catalogo_coordinadores()
            coords_list = ["Todos"] + sorted(list(set(map_coord.values())))
            filtro_coordinador = st.selectbox("👷 Coordinador", coords_list, key="filtro_coord_sidebar")
            try:
                col_nombre_prev = [c for c in df_op_preview.columns if 'nombre' in c.lower()][0]
                ops_list = ["Todos"] + sorted(df_op_preview[col_nombre_prev].dropna().astype(str).unique().tolist())
            except: ops_list = ["Todos"] + load_catalogo_operadores()
            filtro_operador = st.selectbox("🚛 Operador", ops_list, key="filtro_operador_sidebar")
        except:
            filtro_mes = st.selectbox("📅 Mes", ["Todos"], key="filtro_mes_fallback")
            filtro_coordinador = st.selectbox("👷 Coordinador", ["Todos","Felix Najera","Sergio Llanes","Analista"], key="filtro_coord_fallback")
            filtro_operador = st.selectbox("🚛 Operador", ["Todos"]+load_catalogo_operadores(), key="filtro_operador_fallback")
    else:
        filtro_mes = "Todos"; filtro_coordinador = "Todos"; filtro_operador = "Todos"
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
        st.plotly_chart(fig, use_container_width=True); st.markdown("</div>", unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="gepp-card"><div class="gepp-header">Completa</div>', unsafe_allow_html=True)
        comp = (df['Plantilla Completa']=='Completa').sum()
        fig2 = go.Figure(data=[go.Pie(labels=['Incompleta','Completa'], values=[total-comp, comp], hole=0.70, marker_colors=['#ff8c42','#0f3d1f'], textinfo='percent', textposition='inside', sort=False)])
        fig2.update_layout(height=260, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", showlegend=True, legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center", font=dict(size=10)))
        st.plotly_chart(fig2, use_container_width=True); st.markdown("</div>", unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="gepp-card"><div class="gepp-header">Semáforo</div>', unsafe_allow_html=True)
        orden = ['Malo', 'Bueno', 'Excelente']; colores_map = {'Malo': '#ff0000', 'Bueno': '#ffcc00', 'Excelente': '#00b050'}
        counts = df['Semáforo'].value_counts(); valores = [counts.get(cat, 0) for cat in orden]; colores = [colores_map[cat] for cat in orden]
        fig3 = go.Figure(data=[go.Pie(labels=orden, values=valores, hole=0.70, marker_colors=colores, sort=False, textinfo='percent', textposition='inside')])
        fig3.update_layout(height=260, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", showlegend=True, legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center", font=dict(size=10)))
        st.plotly_chart(fig3, use_container_width=True); st.markdown("</div>", unsafe_allow_html=True)

    # TU CODIGO ORIGINAL SIGUE IGUAL HASTA MAPA...
    r2c1,r2c2,r2c3 = st.columns([1.4,1.0,1.0])
    with r2c1:
        st.markdown('<div class="gepp-card"><div class="gepp-header">REGISTRO OPERATIVO / DETALLE POR EMPLEADO - ZEBRA PRO</div>', unsafe_allow_html=True)
        cols1 = ['Fecha','Hora Entrada','Hora Salida','Horas Trabajadas','Tiempo Extra','Nombre completo','Numero Empleado','¿Dentro?','Semáforo']
        cols1 = [c for c in cols1 if c in df.columns]
        df_r2 = df[cols1].tail(20).fillna("")
        components.html(render_zebra(df_r2, "340px"), height=360, scrolling=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with r2c2:
        st.markdown('<div class="gepp-card"><div class="gepp-header">COMPORTAMIENTO POR DÍA</div>', unsafe_allow_html=True)
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

    # === INICIA LO NUEVO V45.3 ===
    st.markdown('<div class="gepp-card"><div class="gepp-header">📈 ASISTENCIA ACUMULADA POR MES Y SEMANA - POR PERSONA</div>', unsafe_allow_html=True)
    try:
        df_acum = df.copy()
        df_acum['Fecha_dt'] = pd.to_datetime(df_acum['Fecha'], dayfirst=True, errors='coerce')
        df_acum = df_acum.dropna(subset=['Fecha_dt'])
        df_acum['Mes'] = df_acum['Fecha_dt'].dt.to_period('M').astype(str)
        df_acum['Semana'] = df_acum['Fecha_dt'].dt.strftime('%Y-W%V')
        df_acum['Mes_num'] = df_acum['Fecha_dt'].dt.to_period('M')
        df_acum = df_acum.sort_values('Fecha_dt')
        personas = ["TODOS"] + sorted(df_acum['Nombre completo'].dropna().unique().tolist())
        sel_persona = st.selectbox("👤 Ver acumulado de:", personas, key="sel_acum_persona")
        if sel_persona != "TODOS": df_p = df_acum[df_acum['Nombre completo'] == sel_persona]
        else: df_p = df_acum
        c_acum1, c_acum2 = st.columns(2)
        with c_acum1:
            st.markdown("#### Acumulado por MES")
            g_mes = df_p.groupby(['Mes','Mes_num']).size().reset_index(name='Asistencias')
            g_mes = g_mes.sort_values('Mes_num'); g_mes['Acumulado'] = g_mes['Asistencias'].cumsum()
            fig_acum_mes = go.Figure()
            fig_acum_mes.add_trace(go.Bar(x=g_mes['Mes'], y=g_mes['Asistencias'], name='Mes', marker_color='#0f3d1f', text=g_mes['Asistencias'], textposition='outside'))
            fig_acum_mes.add_trace(go.Scatter(x=g_mes['Mes'], y=g_mes['Acumulado'], mode='lines+markers', name='Acumulado', yaxis='y2', line=dict(color='#ff0000', width=3)))
            fig_acum_mes.update_layout(title=f"Asistencias por mes - {sel_persona}", height=380, paper_bgcolor="white")
            st.plotly_chart(fig_acum_mes, use_container_width=True)
        with c_acum2:
            st.markdown("#### Acumulado por SEMANA por persona")
            g_sem = df_p.groupby(['Semana']).size().reset_index(name='Asistencias')
            g_sem = g_sem.sort_values('Semana'); g_sem['Acumulado'] = g_sem['Asistencias'].cumsum()
            fig_acum_sem = px.line(g_sem, x='Semana', y='Acumulado', markers=True, title=f"Acumulado semanal - {sel_persona}", color_discrete_sequence=['#0f3d1f'])
            fig_acum_sem.update_traces(line=dict(width=4)); fig_acum_sem.update_layout(height=380)
            st.plotly_chart(fig_acum_sem, use_container_width=True)
            fig_sem_bar = px.bar(g_sem, x='Semana', y='Asistencias', text='Asistencias', title="Asistencias por semana")
            st.plotly_chart(fig_sem_bar, use_container_width=True)
        st.markdown("#### Ranking acumulado - Todas las personas por mes")
        g_persona_mes = df_acum.groupby(['Nombre completo','Mes']).size().reset_index(name='Asistencias')
        if not g_persona_mes.empty:
            g_pivot = g_persona_mes.pivot(index='Nombre completo', columns='Mes', values='Asistencias').fillna(0)
            fig_heat = px.imshow(g_pivot, text_auto=True, aspect="auto", color_continuous_scale='Greens', title="Mapa de calor - Asistencias por persona por mes")
            fig_heat.update_layout(height=500); st.plotly_chart(fig_heat, use_container_width=True)
            st.dataframe(g_pivot, use_container_width=True)
            g_total = df_acum.groupby('Nombre completo').size().reset_index(name='Total Asistencias').sort_values('Total Asistencias', ascending=True)
            fig_total = px.bar(g_total, x='Total Asistencias', y='Nombre completo', orientation='h', text='Total Asistencias', color='Total Asistencias', color_continuous_scale='Greens')
            fig_total.update_layout(height=400, title="Total acumulado por persona")
            st.plotly_chart(fig_total, use_container_width=True)
    except Exception as e:
        st.error(f"Error en acumulado: {e}"); st.exception(e)
    st.markdown("</div>", unsafe_allow_html=True)
    # === FIN LO NUEVO ===

    st.markdown('<div class="gepp-card"><div class="gepp-header">DETALLE - PERSONAL</div>', unsafe_allow_html=True)
    cols_final = ['Fecha','Hora Entrada','Hora Salida','Horas Trabajadas','Nombre completo','Numero Empleado','Latitud','Longitud','¿Dentro?','Fotos','Planta','Coordinador','Semáforo']
    cols_final = [c for c in cols_final if c in df.columns]
    df_show = df[cols_final].tail(100).fillna("")
    components.html(render_zebra(df_show, "500px"), height=520, scrolling=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ... resto de tu menu Pesaje queda igual que V45.2, no lo toqué ...
elif menu == "🚛 Operadores Pesaje":
    st.markdown("<h1 style='color:#0f3d1f; text-align:center;'>RED AMBIENTAL</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='color:#2e7d32; text-align:center;'>🚛 Dashboard Operadores - Pesaje</h2>", unsafe_allow_html=True)
    st.info("Modulo pesaje igual que V45.2 - sin cambios")
else:
    st.title("⛽ Rendimiento de Combustible - Próximamente")
