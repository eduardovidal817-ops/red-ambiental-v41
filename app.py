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
st.set_page_config(page_title="Red Ambiental - V45.1 FIX FINAL", layout="wide", page_icon="♻️")
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
            except:
                pass
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
        "Angel Garcia Navarro",
        "Luis Fernando Perez Castañeda"
    ]

@st.cache_data(ttl=60)
def load_catalogo_coordinadores():
    return {
        "Agustin Castillo Sanchez": "Felix Najera",
        "Sergio Lozano Gonzalez": "Felix Najera",
        "Jorge Ibarra Serrato": "Sergio Llanes",
        "Alejandro Villarreal Bustamante": "Felix Najera",
        "Roberto Reyes Alanis": "Felix Najera",
        "Juan Estrada Guerra": "Sergio Llanes",
        "Luis Pérez Dominguez": "Felix Najera",
        "Roberto Garcia Navarro": "Felix Najera",
        "Ricardo Cazares Diaz": "Sergio Llanes",
        "Carlos Garcia Macias": "Felix Najera",
        "Francisco Mazuca Macias": "Sergio Llanes",
        "Angel Garcia Navarro": "Felix Najera",
        "Luis Fernando Perez Castañeda": "Felix Najera",
        "Kevin Rodriguez": "Analista"
    }

def norm_txt(s):
    try:
        s = str(s).strip()
        s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
        return ' '.join(s.split()).upper()
    except:
        return ""

def get_image_hash(file_bytes):
    return hashlib.sha256(file_bytes).hexdigest()

def mejorar_imagen_para_ocr(img_pil):
    img = img_pil.convert('L')
    w, h = img.size
    img = img.resize((w*2, h*2))
    return img

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
    except Exception as e:
        return None, f"Error {e}", ""

def extraer_folio_boleta(img_pil):
    try:
        img = mejorar_imagen_para_ocr(img_pil)
        texto = pytesseract.image_to_string(img, lang='spa+eng', config='--psm 6')
        texto_up = texto.upper().replace('O','0')
        m = re.search(r'FOLIO[:\s]*([0-9\-]{5,20})', texto_up)
        if m:
            folio = m.group(1).replace(' ','').strip()
            folio = re.sub(r'[^0-9\-]', '', folio)
            return folio, texto
        m2 = re.search(r'(2001-[0-9]{5,10})', texto_up)
        if m2:
            return m2.group(1), texto
        return None, texto
    except:
        return None, ""

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
        st.markdown("---")
        st.markdown("### 🔍 FILTROS PESAJE")
        try:
            df_op_preview = load_operadores()
            try:
                col_fecha_prev = [c for c in df_op_preview.columns if 'marca' in c.lower() or 'timestamp' in c.lower() or 'fecha' in c.lower()][0]
                df_op_preview['mes_filtro'] = pd.to_datetime(df_op_preview[col_fecha_prev], errors='coerce', dayfirst=True).dt.strftime('%Y-%m')
                meses_list = ["Todos"] + sorted(df_op_preview['mes_filtro'].dropna().unique().tolist(), reverse=True)
            except:
                meses_list = ["Todos", "2026-10"]
            filtro_mes = st.selectbox("📅 Mes", meses_list, key="filtro_mes_sidebar")
            map_coord = load_catalogo_coordinadores()
            coords_list = ["Todos"] + sorted(list(set(map_coord.values())))
            filtro_coordinador = st.selectbox("👷 Coordinador", coords_list, key="filtro_coord_sidebar")
            try:
                col_nombre_prev = [c for c in df_op_preview.columns if 'nombre' in c.lower()][0]
                ops_list = ["Todos"] + sorted(df_op_preview[col_nombre_prev].dropna().astype(str).unique().tolist())
            except:
                ops_list = ["Todos"] + load_catalogo_operadores()
            filtro_operador = st.selectbox("🚛 Operador", ops_list, key="filtro_operador_sidebar")
        except:
            filtro_mes = st.selectbox("📅 Mes", ["Todos"], key="filtro_mes_fallback")
            filtro_coordinador = st.selectbox("👷 Coordinador", ["Todos","Felix Najera","Sergio Llanes","Analista"], key="filtro_coord_fallback")
            filtro_operador = st.selectbox("🚛 Operador", ["Todos"]+load_catalogo_operadores(), key="filtro_operador_fallback")
    else:
        filtro_mes = "Todos"
        filtro_coordinador = "Todos"
        filtro_operador = "Todos"
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

elif menu == "🚛 Operadores Pesaje":
    st.markdown("<h1 style='color:#0f3d1f; text-align:center;'>RED AMBIENTAL</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='color:#2e7d32; text-align:center;'>🚛 Dashboard Operadores - Pesaje</h2>", unsafe_allow_html=True)
    with st.expander("📝 Registrar Nuevo Viaje - CANDADO FECHA Y FOLIO", expanded=False):
        c1,c2 = st.columns(2)
        with c1:
            nombre = st.text_input("Nombre Completo", placeholder="Ej: Juan Perez Lopez", key="op_n")
            unidad = st.text_input("Numero de Unidad", placeholder="Ej: 1234", key="op_u")
        with c2:
            base = st.text_input("Base donde se encuentra", placeholder="Garcia, Cienega...", key="op_b")
            foto = st.file_uploader("Foto Boleta OFICIAL - SOLO DEL DIA", type=["jpg","jpeg","png"], key="op_f")
        fecha_valida = False
        folio_detectado = None
        hash_imagen = None
        folio_valido = True
        if foto:
            st.image(foto, caption="Vista previa boleta", width=350)
            file_bytes = foto.getvalue()
            hash_imagen = get_image_hash(file_bytes)
            with st.spinner("🔍 Leyendo FOLIO y Fecha E: de tu boleta oficial..."):
                try:
                    img_pil = Image.open(foto)
                    fecha_boleta, fecha_texto, _ = extraer_fecha_de_imagen(img_pil)
                    folio_temp, _ = extraer_folio_boleta(img_pil)
                    folio_detectado = folio_temp
                    hoy_mty = datetime.now(TZ_MEXICO).date()
                    if folio_detectado:
                        st.info(f"📄 Folio detectado: {folio_detectado} | Hash: {hash_imagen[:8]}")
                    else:
                        st.warning("⚠️ No detecté FOLIO automático, escríbelo abajo")
                    try:
                        df_check = load_operadores()
                        todo_texto = df_check.astype(str).values.flatten()
                        todo_joined = " ".join(todo_texto)
                        if folio_detectado and folio_detectado in todo_joined:
                            st.error(f"❌ ESTA BOLETA YA HA SIDO REGISTRADA - Folio {folio_detectado} ya existe")
                            folio_valido = False
                            fecha_valida = False
                        elif hash_imagen and hash_imagen in todo_joined:
                            st.error(f"❌ ESTA BOLETA YA HA SIDO REGISTRADA - Imagen duplicada")
                            folio_valido = False
                            fecha_valida = False
                    except: pass
                    if fecha_boleta:
                        st.info(f"📅 Fecha en boleta: {fecha_boleta.strftime('%d/%m/%Y')} | Hoy: {hoy_mty.strftime('%d/%m/%Y')}")
                        if fecha_boleta != hoy_mty:
                            st.error(f"❌ BOLETA NO ES DE HOY.")
                            fecha_valida = False
                        else:
                            if folio_valido:
                                st.success(f"✅ Boleta válida de hoy")
                                fecha_valida = True
                    else:
                        st.warning("⚠️ No pude leer Fecha E:")
                        fecha_valida = False
                except Exception as e:
                    st.error(f"Error leyendo imagen: {e}")
                    fecha_valida = False
        if foto and not folio_detectado:
            folio_manual = st.text_input("✍️ Escribe FOLIO manualmente", key="folio_manual_input")
            if folio_manual:
                folio_detectado = folio_manual.strip()
        if st.button("💾 Guardar Registro Operador", type="primary", use_container_width=True):
            if not nombre or not unidad or not base or not foto:
                st.error("❌ Complete todos los campos obligatorios")
            elif not folio_detectado:
                st.error("❌ Debes tener FOLIO.")
            elif not folio_valido:
                st.error(f"❌ No se puede guardar - ESTA BOLETA YA HA SIDO REGISTRADA")
            elif not fecha_valida:
                st.error(f"❌ No se puede guardar. La boleta debe ser del día de hoy")
            else:
                with st.spinner("Procesando..."):
                    b64 = base64.b64encode(foto.getvalue()).decode('utf-8')
                    b64 = f"data:{foto.type};base64,{b64}"
                    payload = {"nombreCompleto": nombre, "unidad": unidad, "base": base, "foto": b64, "folio": folio_detectado or "", "hash": hash_imagen or ""}
                    requests.post(URL_OPERADORES, json=payload, headers={"Content-Type":"text/plain;charset=utf-8"}, timeout=30)
                    st.success(f"✅ Registro guardado - Folio {folio_detectado}")
                    st.balloons()
                    st.cache_data.clear()
    try:
        df_op = load_operadores()
        col_nombre = [c for c in df_op.columns if 'nombre' in c.lower()][0]
        col_unidad = [c for c in df_op.columns if 'unidad' in c.lower()][0]
        col_base = [c for c in df_op.columns if 'base' in c.lower()][0]
        META_DIARIA = 4
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

        # --- FIX DEFINITIVO ACENTOS + FLOAT ---
        map_coord = load_catalogo_coordinadores()
        map_norm = {norm_txt(k): v for k, v in map_coord.items()}
        if 'Coordinadores' in df_op.columns:
            df_op['Coordinador_calc'] = df_op['Coordinadores'].apply(lambda x: str(x).strip() if str(x).strip().lower() not in ["","nan","none","sin asignar","nat","null","nan"] and str(x).strip()!="" else None)
        else:
            df_op['Coordinador_calc'] = None
        df_op['Coordinador_calc'] = df_op.apply(lambda r: r['Coordinador_calc'] if pd.notna(r['Coordinador_calc']) and str(r['Coordinador_calc']).strip()!="" else map_norm.get(norm_txt(r[col_nombre]), "Felix Najera"), axis=1)
        df_op['mes_filtro'] = pd.to_datetime(df_op[col_fecha], errors='coerce', dayfirst=True).dt.strftime('%Y-%m')
        if filtro_mes != "Todos":
            df_op = df_op[df_op['mes_filtro'] == filtro_mes]
        if filtro_coordinador != "Todos":
            df_op = df_op[df_op['Coordinador_calc'] == filtro_coordinador]
        if filtro_operador != "Todos":
            df_op = df_op[df_op[col_nombre].astype(str).str.strip() == filtro_operador]

        st.markdown('<div class="gepp-card"><div class="gepp-header">📅 FILTRO OPERADORES - POR DIA / ACUMULADO</div></div>', unsafe_allow_html=True)
        f1, f2 = st.columns([1,2])
        with f1:
            modo_vista = st.radio("Vista operadores", ["Por Día", "Acumulado por Rango"], key="modo_op_v2")
        with f2:
            if modo_vista == "Por Día":
                fechas_disp = sorted(df_op['fecha_solo'].dropna().unique(), reverse=True)
                sel_dia = st.selectbox("Selecciona día", fechas_disp, index=0, key="sel_dia_op")
                df_mostrar = df_op[df_op['fecha_solo'] == sel_dia].copy()
                df_hoy = df_mostrar.copy()
                etiqueta_fecha = sel_dia.strftime('%d/%m/%Y')
                dias_filtro = 1
            else:
                min_d = df_op['fecha_solo'].min()
                max_d = df_op['fecha_solo'].max()
                rango = st.date_input("Rango acumulado", value=(min_d, max_d), key="rango_op_v2")
                if isinstance(rango, tuple) and len(rango)==2:
                    f_ini, f_fin = rango
                    df_mostrar = df_op[(df_op['fecha_solo'] >= f_ini) & (df_op['fecha_solo'] <= f_fin)].copy()
                    ultima = df_mostrar['fecha_solo'].max() if not df_mostrar.empty else f_fin
                    df_hoy = df_op[df_op['fecha_solo'] == ultima].copy()
                    etiqueta_fecha = f"{f_ini.strftime('%d/%m/%Y')} al {f_fin.strftime('%d/%m/%Y')} - ACUMULADO"
                    dias_filtro = (f_fin - f_ini).days + 1
                else:
                    df_mostrar = df_op.copy()
                    df_hoy = df_op[df_op['fecha_solo'] == df_op['fecha_solo'].max()].copy()
                    etiqueta_fecha = "TODO ACUMULADO"
                    dias_filtro = df_mostrar['fecha_solo'].nunique() if not df_mostrar.empty else 1

        TOTAL_OPS_FIJO = 13
        META_TOTAL_DIA_FIJO = TOTAL_OPS_FIJO * META_DIARIA
        META_TOTAL_FILTRO = META_TOTAL_DIA_FIJO * dias_filtro if modo_vista == "Acumulado por Rango" else META_TOTAL_DIA_FIJO

        if not df_mostrar.empty:
            prod_hoy = df_mostrar[col_nombre].value_counts().reset_index()
            prod_hoy.columns = ['Operador','Viajes_Hoy']
            dias_unicos = df_mostrar['fecha_solo'].nunique() if modo_vista == "Acumulado por Rango" else 1
            dias_unicos = dias_unicos if dias_unicos>0 else 1
            prod_hoy['Productividad_%'] = ((prod_hoy['Viajes_Hoy']/dias_unicos)/META_DIARIA*100).round(1)
            prod_hoy = prod_hoy.sort_values('Productividad_%', ascending=True)
            total_viajes_mostrar = len(df_mostrar)
        else:
            prod_hoy = pd.DataFrame()
            total_viajes_mostrar = 0

        productividad_global = (total_viajes_mostrar / META_TOTAL_FILTRO * 100) if META_TOTAL_FILTRO>0 else 0

        c1,c2,c3,c4 = st.columns([0.9,1.1,1.1,1.1])
        with c1:
            color_prod = "#00ff66" if productividad_global>=80 else "#ffcc00" if productividad_global>=40 else "#ff3333"
            st.markdown(f'''
            <div class="gepp-card" style="background:#0a2211; color:white; padding:18px; height:380px; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center; border:2px solid #00ff88;">
                <p style="font-size:12px; color:#a0c4a8; font-weight:bold; letter-spacing:1px;">TOTAL BOLETAS<br>{etiqueta_fecha}</p>
                <p style="font-size:78px; font-weight:900; margin:8px 0 0 0; line-height:1;">{total_viajes_mostrar}</p>
                <p style="font-size:14px; font-weight:bold; color:#00ff88; margin-top:2px;">BOLETAS</p>
                <div style="width:100%; height:1px; background:#1a4d2e; margin:12px 0;"></div>
                <p style="font-size:12px; color:#a0c4a8; font-weight:bold;">PRODUCTIVIDAD DEL DIA</p>
                <p style="font-size:54px; font-weight:900; margin:4px 0; line-height:1; color:{color_prod};">{productividad_global:.2f}%</p>
                <p style="font-size:11px; color:#d0d0d0; margin-top:4px;">Meta fija: {META_TOTAL_FILTRO} viajes<br>{total_viajes_mostrar} / {META_TOTAL_FILTRO}</p>
                <div style="width:50px; height:50px; background:{color_prod}; border-radius:50%; margin-top:10px; border:3px solid white; box-shadow:0 0 12px {color_prod};"></div>
            </div>
            ''', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="gepp-card"><div class="gepp-header">Viajes por Operador - {etiqueta_fecha}</div>', unsafe_allow_html=True)
            cnt_op = df_mostrar[col_nombre].value_counts().reset_index() if not df_mostrar.empty else pd.DataFrame(columns=['Operador','Viajes'])
            cnt_op.columns = ['Operador','Viajes']
            fig = go.Figure(data=[go.Pie(labels=cnt_op['Operador'], values=cnt_op['Viajes'], hole=0.70, textinfo='label+percent', textposition='inside')])
            fig.update_layout(height=380, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="gepp-card"><div class="gepp-header">Viajes por Base - {etiqueta_fecha}</div>', unsafe_allow_html=True)
            cnt_base = df_mostrar[col_base].value_counts().reset_index() if not df_mostrar.empty else pd.DataFrame(columns=['Base','Viajes'])
            cnt_base.columns = ['Base','Viajes']
            fig2 = go.Figure(data=[go.Pie(labels=cnt_base['Base'], values=cnt_base['Viajes'], hole=0.70, textinfo='label+percent', textposition='inside')])
            fig2.update_layout(height=380, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="white")
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="gepp-card"><div class="gepp-header">Top Unidades - {etiqueta_fecha}</div>', unsafe_allow_html=True)
            cnt_uni = df_mostrar[col_unidad].value_counts().head(10).reset_index() if not df_mostrar.empty else pd.DataFrame(columns=['Unidad','Viajes'])
            cnt_uni.columns = ['Unidad','Viajes']
            fig3 = px.bar(cnt_uni, x='Unidad', y='Viajes', text='Viajes', color='Viajes', color_continuous_scale='Greens')
            fig3.update_layout(height=380, margin=dict(l=10,r=10,t=10,b=30), paper_bgcolor="white", showlegend=False)
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f'<div class="gepp-card"><div class="gepp-header">👷 VIAJES POR COORDINADOR - {etiqueta_fecha}</div>', unsafe_allow_html=True)
        c_coord1, c_coord2 = st.columns(2)
        with c_coord1:
            if not df_mostrar.empty:
                df_coord_viajes = df_mostrar.groupby('Coordinador_calc').size().reset_index(name='Viajes')
                fig_coord = px.bar(df_coord_viajes, x='Coordinador_calc', y='Viajes', text='Viajes', color='Coordinador_calc', title="Coordinador que lleva más viajes")
                fig_coord.update_traces(textposition='outside')
                fig_coord.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_coord, use_container_width=True)
        with c_coord2:
            if not df_mostrar.empty:
                total_ops_por_coord = pd.DataFrame(list(map_coord.items()), columns=['Operador','Coordinador_calc']).groupby('Coordinador_calc').size().reset_index(name='Ops_Asignados')
                total_ops_por_coord['Viajes_Asignados'] = total_ops_por_coord['Ops_Asignados'] * META_DIARIA * (dias_filtro if modo_vista!="Por Día" else 1)
                df_cumpl = df_mostrar.groupby('Coordinador_calc').size().reset_index(name='Viajes_Realizados')
                df_cumpl = pd.merge(total_ops_por_coord, df_cumpl, on='Coordinador_calc', how='left').fillna(0)
                df_cumpl['% Cumplimiento'] = (df_cumpl['Viajes_Realizados'] / df_cumpl['Viajes_Asignados'] * 100).round(1)
                fig_cumpl = px.bar(df_cumpl, x='Coordinador_calc', y='% Cumplimiento', text='% Cumplimiento', color='% Cumplimiento', title="% Cumplimiento por Coordinador", color_continuous_scale=['#ff0000','#ffcc00','#00b050'], range_color=[0,100])
                fig_cumpl.update_layout(height=400)
                st.plotly_chart(fig_cumpl, use_container_width=True)
                st.dataframe(df_cumpl, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"No fue posible cargar la información de operadores: {e}")
        st.exception(e)
else:
    st.title("⛽ Rendimiento de Combustible - Próximamente")
