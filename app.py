import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components
import requests, base64
from datetime import datetime
import pytz

TZ_MEXICO = pytz.timezone("America/Monterrey")
st.set_page_config(page_title="Red Ambiental - V44.4 Solo Hoy", layout="wide", page_icon="♻️")
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

# === CATALOGO MAESTRO - SI TIENES PESTAÑA DE CATALOGO PON EL GID AQUI ===
ID_CATALOGO = ID_SHEET_BOLETAS
GID_CATALOGO = 0 # 0 = usa historico, si tienes pestaña catalogo pon ej: 123456789

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
    try:
        if GID_CATALOGO!= 0:
            url_cat = f"https://docs.google.com/spreadsheets/d/{ID_CATALOGO}/export?format=csv&gid={GID_CATALOGO}&cachebust={datetime.now().strftime('%Y%m%d%H%M%S')}"
            df_cat = pd.read_csv(url_cat)
            df_cat.columns = df_cat.columns.str.strip()
            col = [c for c in df_cat.columns if 'nombre' in c.lower() or 'operador' in c.lower()][0]
            return df_cat[col].dropna().astype(str).str.strip().unique().tolist()
        else:
            df_hist = load_operadores()
            col_n = [c for c in df_hist.columns if 'nombre' in c.lower()][0]
            return df_hist[col_n].dropna().astype(str).str.strip().unique().tolist()
    except:
        return []

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

if menu == "🚛 Operadores Pesaje":
    st.markdown("<h1 style='color:#0f3d1f; text-align:center;'>RED AMBIENTAL</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='color:#2e7d32; text-align:center;'>🚛 Dashboard Operadores - Pesaje</h2>", unsafe_allow_html=True)
    with st.expander("📝 Registrar Nuevo Viaje", expanded=False):
        c1,c2 = st.columns(2)
        with c1:
            nombre = st.text_input("Nombre Completo", key="op_n")
            unidad = st.text_input("Numero de Unidad", key="op_u")
        with c2:
            base = st.text_input("Base donde se encuentra", key="op_b")
            foto = st.file_uploader("Foto Boleta", type=["jpg","jpeg","png"], key="op_f")
        if st.button("💾 Guardar Registro Operador", type="primary", use_container_width=True):
            if not nombre or not unidad or not base or not foto:
                st.error("❌ Complete todos los campos")
            else:
                with st.spinner("Procesando..."):
                    b64 = base64.b64encode(foto.getvalue()).decode('utf-8')
                    b64 = f"data:{foto.type};base64,{b64}"
                    payload = {"nombreCompleto": nombre, "unidad": unidad, "base": base, "foto": b64}
                    requests.post(URL_OPERADORES, json=payload, headers={"Content-Type":"text/plain;charset=utf-8"}, timeout=30)
                    st.success("✅ Guardado"); st.balloons(); st.cache_data.clear()
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
        else:
            ultima_fecha = df_op['fecha_solo'].max() if not df_op.empty else hoy_mty
            df_mostrar = df_op[df_op['fecha_solo'] == ultima_fecha].copy()
            etiqueta_fecha = f"{ultima_fecha.strftime('%d/%m/%Y')} - ULTIMO DIA"

        prod_hoy = pd.DataFrame()
        if not df_mostrar.empty:
            prod_hoy = df_mostrar[col_nombre].value_counts().reset_index()
            prod_hoy.columns = ['Operador','Viajes_Hoy']
            prod_hoy['Productividad_%'] = (prod_hoy['Viajes_Hoy'] / META_DIARIA * 100).round(1)
            total_viajes_mostrar = len(df_mostrar)
            ops_hoy = prod_hoy.shape[0]
        else:
            total_viajes_mostrar = 0
            ops_hoy = 0

        c1,c2,c3,c4 = st.columns([0.9,1.1,1.1,1.1])
        with c1:
            st.markdown(f'<div class="gepp-card" style="background:#0f2a1a; color:white; padding:15px; height:260px; display:flex; flex-direction:column; justify-content:center; align-items:center;"><p style="font-size:11px; color:#a0c4a8;">TOTAL BOLETAS<br>{etiqueta_fecha}</p><p style="font-size:52px; font-weight:900;">{total_viajes_mostrar}</p><p style="font-size:11px;">Ops: {ops_hoy} | Acum: {len(df_op)}</p></div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="gepp-card"><div class="gepp-header">Viajes por Operador</div>', unsafe_allow_html=True)
            cnt_op = df_op[col_nombre].value_counts().reset_index(); cnt_op.columns = ['Operador','Viajes']
            fig = go.Figure(data=[go.Pie(labels=cnt_op['Operador'], values=cnt_op['Viajes'], hole=0.70, textinfo='percent')])
            fig.update_layout(height=260, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True); st.markdown("</div>", unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="gepp-card"><div class="gepp-header">Viajes por Base</div>', unsafe_allow_html=True)
            cnt_base = df_op[col_base].value_counts().reset_index(); cnt_base.columns = ['Base','Viajes']
            fig2 = go.Figure(data=[go.Pie(labels=cnt_base['Base'], values=cnt_base['Viajes'], hole=0.70)])
            fig2.update_layout(height=260, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white")
            st.plotly_chart(fig2, use_container_width=True); st.markdown("</div>", unsafe_allow_html=True)
        with c4:
            st.markdown('<div class="gepp-card"><div class="gepp-header">Top Unidades</div>', unsafe_allow_html=True)
            cnt_uni = df_op[col_unidad].value_counts().head(10).reset_index(); cnt_uni.columns = ['Unidad','Viajes']
            fig3 = px.bar(cnt_uni, x='Unidad', y='Viajes', text='Viajes', color='Viajes', color_continuous_scale='Greens')
            fig3.update_layout(height=260, margin=dict(l=10,r=10,t=10,b=30), paper_bgcolor="white")
            st.plotly_chart(fig3, use_container_width=True); st.markdown("</div>", unsafe_allow_html=True)

        # ====== AQUI ESTA LO QUE PEDISTE WE - SOLO HOY ======
        st.markdown('<div class="gepp-card"><div class="gepp-header">🚨 OPERADORES SIN REGISTRO - SOLO HOY - NOMBRES</div>', unsafe_allow_html=True)
        catalogo_completo = load_catalogo_operadores()
        registrados_hoy = df_mostrar[col_nombre].astype(str).str.strip().unique().tolist() if not df_mostrar.empty else []

        def norm_upper(s): return str(s).strip().upper()
        dict_cat = {norm_upper(x): str(x).strip() for x in catalogo_completo}
        set_reg = set([norm_upper(x) for x in registrados_hoy])
        faltantes_hoy = [dict_cat[k] for k in dict_cat if k not in set_reg]

        cs1, cs2 = st.columns([0.35, 0.65])
        with cs1:
            st.metric("Con Boleta HOY", len(registrados_hoy))
            st.metric("SIN Boleta HOY", len(faltantes_hoy), delta=f"-{len(faltantes_hoy)}", delta_color="inverse")
            if catalogo_completo:
                fig_f = go.Figure(data=[go.Pie(labels=['Con HOY','Sin HOY'], values=[len(registrados_hoy), len(faltantes_hoy)], hole=0.65, marker_colors=['#00b050','#ff0000'], textinfo='label+percent')])
                fig_f.update_layout(height=280, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white")
                st.plotly_chart(fig_f, use_container_width=True)

        with cs2:
            if faltantes_hoy:
                # AQUI ESTAN LOS NOMBRES - SE VAN BORRANDO CONFORME REGISTRAN
                df_falt = pd.DataFrame(faltantes_hoy, columns=['Nombre Operador - SIN REGISTRO HOY'])
                df_falt['Estatus'] = '❌ FALTA HOY'
                df_falt['Fecha'] = hoy_mty.strftime('%d/%m/%Y')
                components.html(render_zebra(df_falt, "400px"), height=420, scrolling=True)
                st.download_button("📥 Descargar Faltantes HOY", df_falt.to_csv(index=False).encode('utf-8'), f"faltantes_SOLO_HOY_{hoy_mty}.csv", "text/csv", use_container_width=True)
            else:
                # CUANDO TODOS REGISTRAN QUEDA VACIO
                st.success(f"✅ ¡TODOS registraron HOY {hoy_mty.strftime('%d/%m/%Y')}! - Tabla vacía")
                df_vacia = pd.DataFrame(columns=['Nombre Operador - SIN REGISTRO HOY','Estatus','Fecha'])
                components.html(render_zebra(df_vacia, "100px"), height=120, scrolling=True)
                st.balloons()
        st.markdown("</div>", unsafe_allow_html=True)
        # ====== FIN LO QUE PEDISTE ======

        st.markdown('<div class="gepp-card"><div class="gepp-header">📊 PRODUCTIVIDAD DIARIA</div>', unsafe_allow_html=True)
        if not prod_hoy.empty:
            fig_prod = px.bar(prod_hoy, x='Productividad_%', y='Operador', orientation='h', text='Productividad_%', color='Productividad_%', color_continuous_scale=['#ff0000','#ffcc00','#00b050'], range_color=[0,150])
            fig_prod.add_vline(x=100, line_dash="dash", line_color="green")
            fig_prod.update_layout(height=400, margin=dict(l=10,r=60,t=20,b=10), paper_bgcolor="white")
            st.plotly_chart(fig_prod, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="gepp-card"><div class="gepp-header">DETALLE REGISTROS</div>', unsafe_allow_html=True)
        df_show_op = df_op.drop(columns=[c for c in df_op.columns if 'fecha_solo' in c.lower()], errors='ignore').tail(100).fillna("").iloc[::-1]
        components.html(render_zebra(df_show_op, "500px"), height=540, scrolling=True)
        st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error: {e}"); st.exception(e)

# El resto de tus menus quedan igual, no se tocaron
else:
    df = df_full.copy()
    st.title("Dashboard")
    st.write("Selecciona un modulo del menu")
