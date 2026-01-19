import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, time, timedelta
import plotly.express as px

# ==========================================
# 1. CONFIGURACIÓN E INICIALIZACIÓN
# ==========================================
st.set_page_config(
    page_title="Gestión Clínica 2026", 
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🏥"
)

# --- SEGURIDAD ---
try:
    USUARIOS = st.secrets["usuarios_clinica"]
except Exception as e:
    st.error("⛔ ERROR DE SEGURIDAD: No se encontraron las credenciales (Secrets).")
    st.stop()

# --- LISTAS MAESTRAS ---
ROLES = sorted([
    "Anestesiólogo cardiovascular", "Anestesiólogo general", "Auxiliar de enfermería", 
    "Auxiliar de farmacia", "Cardiólogo clínico", "Cardiólogo Ecocardiografista", 
    "Cardiólogo Hemodinamista", "Cardiólogo pediatra", "Cardiólogo-Electrofisiólogo", 
    "Cirujano cardiovascular adultos", "Cirujano cardiovascular pediátrico", 
    "Cirujano vascular", "Enfermera jefe", "Médico general", "Médico Internista", 
    "Perfusionista", "Psicóloga clínica", "Regente de farmacia", "Sonografista"
])

SEDES = sorted([
    "Barranca", "Clínica Chicamocha", "Clínica San Luis", "FOSCAL", 
    "FOSCAL Internacional", "Sede ambulatoria-Mejoras públicas"
])

# --- LISTA DE ACTIVIDADES CORREGIDA ---
ACTIVIDADES = sorted([
    "Apoyo Consulta externa", "Apoyo farmacéutico", "Apoyo procedimientos Cirugía cardiaca", 
    "Apoyo procedimientos Electrofisiología", "Apoyo procedimientos Hemodinamia", 
    "Apoyo métodos no invasivos", "Apoyo Psicología clínica", 
    "Caminata de 6 minutos (lectura)", "Caminata de 6 minutos (realización)", 
    "Cirugía cardiaca", "Consulta externa (asistida)", "Consulta externa", 
    "Eco Doppler arterial", "Eco Doppler venoso", 
    "Ecocardiograma transesofágico (realización y lectura)", 
    "Ecocardiograma transtorácico (lectura)", "Ecocardiograma transtorácico (realización)", 
    "Ecocardiograma transtorácico (realización y lectura)", 
    "Electrocardiograma (lectura)", "Electrocardiograma (toma)", 
    "Holter de EKG (implante)", "Holter de EKG (lectura)", "Holter de EKG (retiro)", 
    "Lectura Métodos no invasivos", "MAPA (implante)", "MAPA (lectura)", "MAPA (retiro)", 
    "Mesa basculante (lectura)", "Mesa basculante (realización)", 
    "Plestismografia (realización)", "Plestismografia (lectura)", 
    "Procedimientos cirugía cardiaca", "Procedimientos Electrofisiología", 
    "Procedimientos Hemodinamia", "Prueba de esfuerzo (lectura)", 
    "Prueba de esfuerzo (realización)", "Ronda asistencial", 
    "Ronda asistencial (apoyo)", "Ronda asistencial (dirección)"
])

TRABAJADORES = sorted([f"Trabajador {i}" for i in range(1, 51)])
HORAS_MILITAR = [f"{h:02d}:00" for h in range(0, 24)]

# ==========================================
# 2. FUNCIONES DEL SISTEMA (BACKEND)
# ==========================================
def get_db_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    except:
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        except:
            st.error("Error crítico: No se encontraron credenciales de Google.")
            st.stop()
    client = gspread.authorize(creds)
    return client.open("Agenda_Clinica_2026")

def cargar_datos():
    try:
        sh = get_db_connection()
        ws = sh.worksheet("Programacion")
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        cols = ["Fecha", "Dia", "Es_Festivo", "Trabajador", "Rol", "Sede", 
                "Actividad", "Hora_Inicio", "Hora_Fin", "Estado", 
                "Horas_Extras", "Horas_Nocturnas", "Usuario_Registro", "Timestamp"]
        if df.empty:
            df = pd.DataFrame(columns=cols)
        return df
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

def guardar_registro(data_dict, usuario):
    sh = get_db_connection()
    ws_prog = sh.worksheet("Programacion")
    ws_logs = sh.worksheet("Logs")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row_prog = [
        data_dict["Fecha"], data_dict["Dia"], data_dict["Es_Festivo"],
        data_dict["Trabajador"], data_dict["Rol"], data_dict["Sede"],
        data_dict["Actividad"], data_dict["Hora_Inicio"], data_dict["Hora_Fin"],
        data_dict["Estado"], data_dict["Horas_Extras"], data_dict["Horas_Nocturnas"],
        usuario, timestamp
    ]
    ws_prog.append_row(row_prog)
    ws_logs.append_row([timestamp, usuario, "Creación Actividad", str(data_dict)])

def verificar_cruce_horario(df, trabajador, fecha_str, hora_ini_str, hora_fin_str):
    if df.empty: return False
    df_worker = df[(df["Trabajador"] == trabajador) & (df["Fecha"] == fecha_str)]
    if df_worker.empty: return False

    def time_to_int(t_str): return int(t_str.replace(":", ""))
    new_start = time_to_int(hora_ini_str)
    new_end = time_to_int(hora_fin_str)

    for _, row in df_worker.iterrows():
        existing_start = time_to_int(str(row["Hora_Inicio"]))
        existing_end = time_to_int(str(row["Hora_Fin"]))
        if (new_start < existing_end) and (new_end > existing_start):
            return True
    return False

# --- LÓGICA DE CALENDARIO CSV ROBUSTA ---
@st.cache_data
def cargar_festivos_local():
    """
    Lee 'calendario.csv' manejando errores de codificación y formato.
    """
    archivo_objetivo = "calendario.csv"
    try:
        # Intento lectura UTF-8, si falla Latin-1
        try:
            df = pd.read_csv(archivo_objetivo, on_bad_lines='skip', encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(archivo_objetivo, on_bad_lines='skip', encoding='latin-1')
        
        # Corrección si todo está en una columna por comillas
        if len(df.columns) == 1:
            col_unica = df.columns[0]
            encabezados = col_unica.replace('"', '').split(',')
            df = df[col_unica].astype(str).str.replace('"', '').str.split(',', expand=True)
            if len(df.columns) == len(encabezados):
                df.columns = encabezados
            else:
                df.columns = ["Numero_dia", "Mes", "Dia_semana", "Festivo"]

        df.columns = df.columns.str.replace('"', '').str.strip()
        
        if "Festivo" not in df.columns or "Mes" not in df.columns:
            st.warning(f"⚠️ Columnas inválidas en CSV: {list(df.columns)}")
            return []

        df["Festivo_Clean"] = df["Festivo"].astype(str).str.replace('"', '').str.strip().str.upper()
        df_festivos = df[df["Festivo_Clean"] == "SI"].copy()
        
        mapa_meses = {
            "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6,
            "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12
        }
        
        lista_fechas = []
        for _, row in df_festivos.iterrows():
            try:
                d_str = str(row["Numero_dia"]).replace('"', '').strip()
                d = int(d_str)
                m_txt = str(row["Mes"]).replace('"', '').strip().upper()
                m = mapa_meses.get(m_txt)
                if m:
                    fecha_obj = datetime(2026, m, d).date()
                    lista_fechas.append(fecha_obj)
            except:
                continue 
        return lista_fechas

    except FileNotFoundError:
        st.error(f"⚠️ ERROR: No se encontró '{archivo_objetivo}'.")
        return []
    except Exception as ex:
        st.error(f"Error leyendo calendario: {ex}")
        return []

def es_festivo_personalizado(fecha_obj):
    festivos = cargar_festivos_local()
    return fecha_obj in festivos

def analizar_jornada_laboral(df, trabajador, fecha_obj, hora_ini_str, hora_fin_str):
    fecha_corte = datetime(2026, 7, 15).date()
    limite_semanal = 42 if fecha_obj >= fecha_corte else 44
    
    fmt = "%H:%M"
    t_ini = datetime.strptime(hora_ini_str, fmt)
    t_fin = datetime.strptime(hora_fin_str, fmt)
    if t_fin <= t_ini: t_fin += timedelta(days=1)
    
    duracion_nueva = (t_fin - t_ini).seconds / 3600
    
    horas_nocturnas = 0
    temp_time = t_ini
    while temp_time < t_fin:
        h = temp_time.hour
        if 21 <= h or h < 6: horas_nocturnas += 1
        temp_time += timedelta(hours=1)
        
    acumulado_semana = 0
    if not df.empty:
        semana_actual = fecha_obj.isocalendar()[1]
        df['Fecha_DT'] = pd.to_datetime(df['Fecha'])
        df_sem = df[
            (df['Trabajador'] == trabajador) & 
            (df['Fecha_DT'].dt.isocalendar().week == semana_actual) &
            (df['Fecha_DT'].dt.year == fecha_obj.year)
        ]
        for _, row in df_sem.iterrows():
            hi = datetime.strptime(str(row['Hora_Inicio']), fmt)
            hf = datetime.strptime(str(row['Hora_Fin']), fmt)
            if hf <= hi: hf += timedelta(days=1)
            acumulado_semana += (hf - hi).seconds / 3600

    total_proy = acumulado_semana + duracion_nueva
    extras = max(0, total_proy - limite_semanal)
    
    return {
        "limite": limite_semanal, "acumulado": acumulado_semana,
        "nuevo": duracion_nueva, "total": total_proy,
        "extras": extras, "nocturnas": horas_nocturnas
    }

# ==========================================
# 3. LOGIN DE USUARIO
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    col_main, _ = st.columns([1, 2])
    st.markdown("## 🔐 Acceso Seguro")
    with st.form("login"):
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        btn = st.form_submit_button("Ingresar")
        if btn:
            if u in USUARIOS and USUARIOS[u] == p:
                st.session_state['logged_in'] = True
                st.session_state['usuario'] = u
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
    st.stop()

# ==========================================
# 4. APLICACIÓN PRINCIPAL
# ==========================================
st.sidebar.title(f"👨‍⚕️ Dr(a). {st.session_state['usuario'].capitalize()}")
st.sidebar.info("Perfil: Dirección Médica / Gestión")
menu = st.sidebar.radio("Navegación", ["📅 Programación", "📊 Tablero Gerencial"])

# ------------------------------------------
# A. MÓDULO DE PROGRAMACIÓN
# ------------------------------------------
if menu == "📅 Programación":
    st.title("Programador de Actividades Clínicas")
    st.markdown("---")
    
    # === SECCIÓN DE FECHA (FUERA DEL FORM PARA RESPUESTA INMEDIATA) ===
    c_date1, c_date2 = st.columns([1, 2])
    
    with c_date1:
        st.subheader("1. Selección de Fecha")
        fecha = st.date_input("Seleccione el día", min_value=datetime(2026, 1, 1))
        
        # Lógica de Días en Español
        dias_espanol = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        dia_semana_idx = fecha.weekday()
        dia_sem_str = dias_espanol[dia_semana_idx]
        
        # Validaciones Inmediatas
        es_fin_semana = dia_semana_idx >= 5 # 5=Sábado, 6=Domingo
        es_festivo_cal = es_festivo_personalizado(fecha)
        
        # Mostrar Alertas
        st.markdown(f"### 🗓️ {dia_sem_str}")
        
        if es_festivo_cal:
            st.error("🚨 **ES FESTIVO (Según Calendario)**")
            tipo_dia = f"{dia_sem_str} (Festivo)"
        elif es_fin_semana:
            st.warning("⚠️ **FIN DE SEMANA (Sábado/Domingo)**")
            tipo_dia = f"{dia_sem_str} (Fin de Semana)"
        else:
            st.success("✅ Día Hábil Ordinario")
            tipo_dia = dia_sem_str

    with c_date2:
        st.info("ℹ️ Seleccione la fecha primero para verificar disponibilidad y festivos.")

    st.markdown("---")
    
    # === RESTO DEL FORMULARIO (DENTRO DEL FORM PARA GUARDADO EN LOTE) ===
    st.subheader("2. Detalles de la Actividad")
    
    with st.form("agenda_form"):
        c1, c2, c3 = st.columns(3)
        
        with c1:
            trabajador = st.selectbox("Trabajador", TRABAJADORES)
            rol = st.selectbox("Rol", ROLES)
        
        with c2:
            sede = st.selectbox("Sede", SEDES)
            actividad = st.selectbox("Actividad", ACTIVIDADES)
            
        with c3:
            estado = st.selectbox("Estado", ["No confirmado", "Provisional", "Confirmado", "Ejecutado"])
            st.caption("Asegúrese de confirmar con el profesional.")

        st.markdown("#### ⏱️ Franja Horaria")
        h1, h2 = st.columns(2)
        with h1: h_ini = st.selectbox("Hora Inicio", HORAS_MILITAR, index=8)
        with h2:
            idx = HORAS_MILITAR.index(h_ini)
            posibles = HORAS_MILITAR[idx+1:] if idx+1 < len(HORAS_MILITAR) else ["23:59"]
            h_fin = st.selectbox("Hora Fin", posibles)

        st.markdown("---")
        btn_save = st.form_submit_button("💾 Guardar Actividad")

    if btn_save:
        df_check = cargar_datos()
        
        # Validar cruces
        if verificar_cruce_horario(df_check, trabajador, str(fecha), h_ini, h_fin):
            st.error(f"❌ ERROR CRÍTICO: El {trabajador} ya tiene actividad programada en este horario.")
        else:
            # Análisis de Ley 2101
            analisis = analizar_jornada_laboral(df_check, trabajador, fecha, h_ini, h_fin)
            
            c_alert1, c_alert2 = st.columns(2)
            with c_alert1:
                st.info(f"**Análisis Semanal (Ley 2101)**\nLímite: {analisis['limite']}h | Acumulado: {analisis['total']}h")
                if analisis['extras'] > 0: st.warning(f"⚠️ Genera **{analisis['extras']}h EXTRAS**")
                else: st.success("✅ Dentro del límite legal.")
            
            with c_alert2:
                st.info(f"**Análisis Turno**")
                if analisis['nocturnas'] > 0: st.warning(f"🌚 **{analisis['nocturnas']}h NOCTURNAS**")
                else: st.success("☀️ Jornada Diurna")

            # Preparar datos para guardar
            nuevo_registro = {
                "Fecha": str(fecha), 
                "Dia": tipo_dia,  # Guardamos el día en español calculado arriba
                "Es_Festivo": "Sí" if es_festivo_cal else "No",
                "Trabajador": trabajador, 
                "Rol": rol, 
                "Sede": sede,
                "Actividad": actividad, 
                "Hora_Inicio": h_ini, 
                "Hora_Fin": h_fin,
                "Estado": estado, 
                "Horas_Extras": analisis['extras'], 
                "Horas_Nocturnas": analisis['nocturnas']
            }
            guardar_registro(nuevo_registro, st.session_state['usuario'])
            st.toast("✅ Registro guardado exitosamente", icon="🎉")

# ------------------------------------------
# B. MÓDULO TABLERO GERENCIAL
# ------------------------------------------
elif menu == "📊 Tablero Gerencial":
    st.title("Tablero de Control y Trazabilidad")
    
    df = cargar_datos()
    
    if df.empty:
        st.info("No hay datos para mostrar.")
    else:
        st.sidebar.markdown("---")
        st.sidebar.header("🔍 Filtros")
        
        fechas_dt = pd.to_datetime(df["Fecha"])
        min_date, max_date = fechas_dt.min().date(), fechas_dt.max().date()
        rango = st.sidebar.date_input("Rango de Fechas", [min_date, max_date])
        
        fil_sede = st.sidebar.multiselect("Sede", df["Sede"].unique())
        fil_trab = st.sidebar.multiselect("Trabajador", df["Trabajador"].unique())
        
        df_view = df.copy()
        df_view["Fecha_DT"] = pd.to_datetime(df_view["Fecha"])
        
        if isinstance(rango, list) and len(rango) == 2:
            df_view = df_view[(df_view["Fecha_DT"].dt.date >= rango[0]) & (df_view["Fecha_DT"].dt.date <= rango[1])]
            
        if fil_sede: df_view = df_view[df_view["Sede"].isin(fil_sede)]
        if fil_trab: df_view = df_view[df_view["Trabajador"].isin(fil_trab)]

        st.subheader("📅 Cronograma de Actividades (Gantt)")
        if not df_view.empty:
            df_view['Inicio_Real'] = pd.to_datetime(df_view['Fecha'] + ' ' + df_view['Hora_Inicio'])
            df_view['Fin_Real'] = pd.to_datetime(df_view['Fecha'] + ' ' + df_view['Hora_Fin'])
            
            fig_gantt = px.timeline(
                df_view, x_start="Inicio_Real", x_end="Fin_Real", y="Trabajador",
                color="Actividad", hover_data=["Sede", "Estado"],
                title="Agenda Detallada", height=400 + (len(df_view['Trabajador'].unique()) * 30)
            )
            fig_gantt.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_gantt, use_container_width=True)
        else:
            st.warning("No hay datos en el rango seleccionado.")
            
        st.divider()

        k1, k2, k3 = st.columns(3)
        total_recs = len(df_view)
        total_extras = df_view["Horas_Extras"].sum() if "Horas_Extras" in df_view.columns else 0
        ejecucion = len(df_view[df_view["Estado"] == "Ejecutado"])
        perc = (ejecucion/total_recs*100) if total_recs > 0 else 0
        
        k1.metric("Actividades Totales", total_recs)
        k2.metric("Horas Extras Proyectadas", f"{total_extras:.1f} h")
        k3.metric("% Ejecución", f"{perc:.1f}%")
        
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Carga por Sede")
            conteo_sedes = df_view['Sede'].value_counts().reset_index()
            conteo_sedes.columns = ['Sede', 'Total']
            fig_bar = px.bar(conteo_sedes, x='Sede', y='Total', color='Total', text_auto=True)
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with g2:
            st.subheader("Estado de Gestión")
            colors_state = {"No confirmado": "#FFCC80", "Provisional": "#FFD700", 
                            "Confirmado": "#A5D6A7", "Ejecutado": "#90CAF9"}
            fig_pie = px.pie(df_view, names='Estado', color='Estado', 
                             color_discrete_map=colors_state, hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("📋 Detalle de Registros")
        st.dataframe(df_view.drop(columns=["Inicio_Real", "Fin_Real", "Fecha_DT"], errors='ignore'), use_container_width=True)



