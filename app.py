import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components
import requests, base64

st.set_page_config(page_title="Red Ambiental - V43.1 Pro Zebra", layout="wide", page_icon="♻️")

st.markdown("""
<style>
.stApp { background-color: #e9ecf2; }
section[data-testid="stSidebar"] { background-color: #0a2211; }
.gepp-card { background:white; border:1px solid #b0b8c8; border-radius:6px; overflow:hidden; margin-bottom:12px; box-shadow:0 1px 3px rgba(0,0,0,0.1); }
.gepp-header { background:#0f3d1f; color:white; padding:8px 12px; font-size:11px; font-weight:700; text-align:center; text-transform:uppercase; }
.zebra-table { width:100%; border-collapse:collapse; font-size:12px; font-family:Arial; }
.zebra-table th { background:#0f3d1f; color:white; padding:8px; text-align:left; position:sticky; top:0; }
.zebra-table td { padding:7px 8px; border-bottom:1px solid #e0e0e0; }
.zebra-table tr:nth-child(even) { background:#f2f4f7; }
.zebra-table tr:nth-child(odd) { background:#ffffff; }
.zebra-table tr:hover { background:#d1e7dd!important; }
</style>
""", unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRdHGoaJ3BSFqaU4DIH1Wks7dROyzp3z7Z_guIBoAD7VzSXCIis14R9HMPCaDmF3omEK5RzEDlua1aR/pub?gid=1011674108&single=true&output=csv"
URL_OP_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTib9TDIJwZ4QKnACiO-rLdyYIZCudCgaC-eSGSOSeZ5y4tQg4RsLZAq66aJMt83cfarOdD3MU2yHc5/pub?gid=0&single=true&output=csv"
URL_OPERADORES = "https://script.google.com/macros/s/AKfycbxfb7MVBqN_3xk5a9ICVa7X9zKWtH1s9PEfgv_QpU0iW54q6_gldoNgXbpHU8DztwI/exec"

@st.cache_data(ttl=60)
def load():
    df = pd.read_csv(URL)
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    if 'Estatus Entrega' in df.columns: df = df.drop(columns=['Estatus Entrega'])
    mapa = {"BAXTER": "Eduardo Vidal","BASE GARCIA": "Felix Najera","BASE GARCÍA": "Felix Najera","POLOMEX": "Felix Najera","AMAZON MTY1": "Felix Najera","AMAZON MTY2": "Felix Najera","AMAZON MTY3": "Felix Najera","JUEGOS DEL VALLE": "Felix Najera","CELESTICA": "Felix Najera","CATERPILLAR CIENEGA": "Sergio Llanes"}
    def get_coord(r):
        c = str(r.get("Coordinador","")).strip()
        if c.lower() not in ["","nan","none","sin asignar"]: return c
        return mapa.get(str(r.get("Planta","")).upper().strip(), "SIN ASIGNAR")
    if "Coordinador" not in df.columns: df["Coordinador"] = ""
    df["Coordinador"] = df.apply(get_coord, axis=1)
    return df

@st.cache_data(ttl=30)
def load_operadores():
    df = pd.read_csv(URL_OP_CSV)
    df.columns = df.columns.str.strip()
    return df

df_full = load()

def render_zebra(df_to_show, max_h="340px"):
    html = f"""<style>.zebra-table{{width:100%;border-collapse:collapse;font-size:11px;font-family:Arial;}}.zebra-table th{{background:#0f3d1f;color:white;padding:8px;text-align:left;position:sticky;top:0;z-index:2;}}.zebra-table td{{padding:7px 8px;border-bottom:1px solid #e0e0e0;}}.zebra-table tr:nth-child(even){{background:#f2f4f7;}}.zebra-table tr:nth-child(odd){{background:#ffffff;}}.zebra-table tr:hover{{background:#d1e7dd!important;}}</style><div style="max-height:{max_h}; overflow:auto; background:white; border-radius:0 0 6px 6px;"><table class="zebra-table"><thead><tr>"""
    for col in df_to_show.columns: html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    for _, row in df_to_show.iterrows():
        html += "<tr>"
        for col in df_to_show.columns:
            val = row[col]
            if str(val).startswith("http"): html += f'<td><a href="{val}" target="_blank" style="color:#0f3d1f; font-weight:bold;">Ver Foto</a></td>'
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
    else:
        fecha_sel = None; planta_sel = "Todas"; coord_sel = "Todos"; dentro_sel = "Todos"

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
    total = len(df); dentro = (df['¿Dentro?_NORM']=='DENTRO').sum(); fuera = total - dentro
    components.html(f"""<div style="background:#0f3d1f; color:white; padding:10px 15px; border-radius:6px; display:flex; justify-content:space-between; align-items:center; font-family:Arial;"><span style="font-weight:800; font-size:14px;">RED AMBIENTAL | {planta_sel} | {coord_sel}</span><div style="text-align:right; font-size:11px;"><div>Total: {total} | DENTRO: {dentro} | FUERA: {fuera}</div><div id="reloj" style="font-weight:800; font-size:13px; color:#00ff88;"></div></div></div><script>function actualizarReloj(){{const ahora=new Date().toLocaleString("es-MX",{{timeZone:"America/Monterrey",weekday:'long',year:'numeric',month:'long',day:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:true}});document.getElementById("reloj").innerHTML="🕒 "+ahora.toUpperCase()+" | LIVE";}}setInterval(actualizarReloj,1000);actualizarReloj();</script>""", height=75)
    c1,c2,c3,c4 = st.columns([0.9,1.1,1.1,1.1])
    with c1:
        pct = (dentro/total*100) if total>0 else 0
        st.markdown(f'<div class="gepp-card" style="background:#0f2a1a; color:white; padding:15px; height:360px; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center;"><p style="font-size:10px; color:#a0c4a8; font-weight:bold;">PLANTILLA DENTRO GEOCERCA</p><p style="font-size:42px; font-weight:800; margin:20px 0 0 0;">{pct:.1f}%</p><p style="font-size:11px;">DENTRO: {dentro} / {total}</p><div style="width:40px; height:40px; background:{"#00ff66" if pct>50 else "#ff0000"}; border-radius:50%; margin-top:15px;"></div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="gepp-card"><div class="gepp-header">¿Dentro? - Dona Centrada</div>', unsafe_allow_html=True)
        fig = go.Figure(data=[go.Pie(labels=['FUERA','DENTRO'], values=[fuera, dentro], hole=0.65, marker_colors=['#ff0000','#0f3d1f'], textinfo='percent', textposition='inside')])
        fig.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", showlegend=True, legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"))
        st.plotly_chart(fig, use_container_width=True); st.markdown("</div>", unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="gepp-card"><div class="gepp-header">Completa - Dona Centrada</div>', unsafe_allow_html=True)
        df['Plantilla Completa'] = df['Horas Trabajadas'].apply(lambda x: 'Completa' if pd.notna(x) and str(x)!='' and str(x)!='None' else 'Incompleta')
        comp = (df['Plantilla Completa']=='Completa').sum()
        fig2 = go.Figure(data=[go.Pie(labels=['Incompleta','Completa'], values=[total-comp, comp], hole=0.65, marker_colors=['#ff8c42','#0f3d1f'], textinfo='percent', textposition='inside')])
        fig2.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", showlegend=True, legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"))
        st.plotly_chart(fig2, use_container_width=True); st.markdown("</div>", unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="gepp-card"><div class="gepp-header">Semáforo - Dona Centrada</div>', unsafe_allow_html=True)
        orden = ['Malo', 'Bueno', 'Excelente']; colores_map = {'Malo': '#ff0000', 'Bueno': '#ffcc00', 'Excelente': '#00b050'}
        counts = df['Semáforo'].value_counts(); valores = [counts.get(cat, 0) for cat in orden]; colores = [colores_map[cat] for cat in orden]
        fig3 = go.Figure(data=[go.Pie(labels=orden, values=valores, hole=0.65, marker_colors=colores, textinfo='percent', textposition='inside')])
        fig3.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white", showlegend=True, legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"))
        st.plotly_chart(fig3, use_container_width=True); st.markdown("</div>", unsafe_allow_html=True)

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
                st.error("❌ Llena todo we")
            else:
                with st.spinner("Subiendo..."):
                    b64 = base64.b64encode(foto.getvalue()).decode('utf-8')
                    b64 = f"data:{foto.type};base64,{b64}"
                    payload = {"nombreCompleto": nombre, "unidad": unidad, "base": base, "foto": b64}
                    requests.post(URL_OPERADORES, json=payload, headers={"Content-Type":"text/plain;charset=utf-8"}, timeout=30)
                    st.success("✅ Guardado con madre"); st.balloons()
                    st.cache_data.clear()

    try:
        df_op = load_operadores()
        col_nombre = [c for c in df_op.columns if 'nombre' in c.lower()][0]
        col_unidad = [c for c in df_op.columns if 'unidad' in c.lower()][0]
        col_base = [c for c in df_op.columns if 'base' in c.lower()][0]

        total_viajes = len(df_op)
        operadores_unicos = df_op[col_nombre].nunique()

        c1,c2,c3,c4 = st.columns([0.9,1.1,1.1,1.1])
        with c1:
            st.markdown(f'<div class="gepp-card" style="background:#0f2a1a; color:white; padding:15px; height:380px; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center;"><p style="font-size:11px; color:#a0c4a8; font-weight:bold;">TOTAL VIAJES REGISTRADOS</p><p style="font-size:50px; font-weight:900; margin:15px 0;">{total_viajes}</p><p style="font-size:12px;">Operadores: {operadores_unicos}</p><div style="width:50px; height:50px; background:#00ff66; border-radius:50%; margin-top:15px;"></div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="gepp-card"><div class="gepp-header">Viajes por Operador - Dona Centrada</div>', unsafe_allow_html=True)
            cnt_op = df_op[col_nombre].value_counts().reset_index(); cnt_op.columns = ['Operador','Viajes']
            fig = go.Figure(data=[go.Pie(labels=cnt_op['Operador'], values=cnt_op['Viajes'], hole=0.60, textinfo='percent', textposition='inside', insidetextorientation='radial')])
            fig.update_layout(height=380, margin=dict(l=0,r=0,t=10,b=50), paper_bgcolor="white", showlegend=True, legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center", font=dict(size=9)))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="gepp-card"><div class="gepp-header">Viajes por Base - Dona Centrada</div>', unsafe_allow_html=True)
            cnt_base = df_op[col_base].value_counts().reset_index(); cnt_base.columns = ['Base','Viajes']
            fig2 = go.Figure(data=[go.Pie(labels=cnt_base['Base'], values=cnt_base['Viajes'], hole=0.60, textinfo='label+percent', textposition='inside', marker=dict(colors=px.colors.sequential.Greens_r))])
            fig2.update_layout(height=380, margin=dict(l=0,r=0,t=10,b=50), paper_bgcolor="white", showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with c4:
            st.markdown('<div class="gepp-card"><div class="gepp-header">Top Unidades con más viajes</div>', unsafe_allow_html=True)
            cnt_uni = df_op[col_unidad].value_counts().head(10).reset_index(); cnt_uni.columns = ['Unidad','Viajes']
            fig3 = px.bar(cnt_uni, x='Unidad', y='Viajes', text='Viajes', color='Viajes', color_continuous_scale='Greens')
            fig3.update_layout(height=380, margin=dict(l=10,r=10,t=10,b=30), paper_bgcolor="white", showlegend=False)
            fig3.update_traces(textposition='outside')
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # NUEVA GRAFICA: CUANTOS VIAJES HIZO CADA OPERADOR
        st.markdown('<div class="gepp-card"><div class="gepp-header">📊 Ranking - Cuantos viajes hizo cada operador</div>', unsafe_allow_html=True)
        cnt_op_bar = df_op[col_nombre].value_counts().reset_index(); cnt_op_bar.columns = ['Operador','Viajes']
        cnt_op_bar = cnt_op_bar.sort_values('Viajes', ascending=True)
        fig_bar = px.bar(cnt_op_bar, x='Viajes', y='Operador', orientation='h', text='Viajes', color='Viajes', color_continuous_scale='Greens', title=f"Total Operadores: {len(cnt_op_bar)}")
        fig_bar.update_layout(height=450, margin=dict(l=10,r=40,t=40,b=10), paper_bgcolor="white", plot_bgcolor="white", yaxis=dict(tickfont=dict(size=11)), showlegend=False)
        fig_bar.update_traces(textposition='outside', textfont=dict(size=12, color="black"))
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="gepp-card"><div class="gepp-header">DETALLE REGISTROS OPERADORES - TABLA ZEBRA EN VIVO</div>', unsafe_allow_html=True)
        df_show_op = df_op.tail(100).fillna("").iloc[::-1]
        components.html(render_zebra(df_show_op, "500px"), height=540, scrolling=True)
        st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"No pude cargar operadores: {e}")

else:
    st.title("⛽ Rendimiento de Combustible - Próximamente")
    st.info("Módulo preparado we, aquí va diesel, km, rendimiento")
