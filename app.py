import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN Y AUTENTICACIÓN ---
st.set_page_config(
    page_title="HemoSim: Docencia en Falla Cardíaca",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS
st.markdown("""
    <style>
    .big-font { font-size:20px !important; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 1.2rem; }
    .stAlert { padding: 0.5rem; }
    </style>
    """, unsafe_allow_html=True)

# Función de Login
def check_password():
    """Retorna True si el usuario/clave son correctos."""
    def password_entered():
        if st.session_state["username"] == "aprendefalla" and st.session_state["password"] == "javier":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Borrar clave por seguridad
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Primera vez, mostrar inputs
        st.header("🔒 Acceso Docente")
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password", on_change=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        # Clave incorrecta
        st.header("🔒 Acceso Docente")
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password", on_change=password_entered)
        st.error("😕 Usuario o contraseña incorrectos")
        return False
    else:
        # Clave correcta
        return True

if not check_password():
    st.stop()  # Detiene la ejecución si no está logueado

# --- 2. BASE DE DATOS GEOGRÁFICA Y RIESGO CHAGAS ---

# Lista de zonas de riesgo específicas proporcionadas
zonas_chagas = [
    # Boyacá
    "Boavita", "Chiscas", "Cubará", "Güicán de la Sierra", "Labranzagrande", 
    "Paya", "Pisba", "San Mateo", "Soatá", "Socotá", "Tipacoque",
    # Santander
    "Barichara", "Capitanejo", "Encinales", "Hato", "Mogotes", "San Gil", 
    "San José de Miranda", "San Vicente del Chucurí", "Socorro",
    # Casanare
    "Aguazul", "Chámeza", "Hato Corozal", "Nunchía", "Paz de Ariporo", 
    "Recetor", "Támara", "Tauramena", "Yopal",
    # Arauca
    "Arauca", "Arauquita", "Saravena", "Tame",
    # Cundinamarca
    "Choachí", "Fómeque", "Gachalá", "Medina", "Nilo", "Paratebueno", "Ubaque",
    # Norte de Santander
    "Cáchira", "Sardinata", "Toledo",
    # Cesar / Sierra Nevada
    "La Jagua de Ibirico", "Pueblo Bello", "Valledupar",
    # Antioquia
    "Liborina", "Peque", "Yolombó"
]

# Lista base de municipios (Se incluye una lista amplia + capitales + riesgo)
municipios_base = sorted(list(set(zonas_chagas + [
    "Bogotá D.C.", "Medellín", "Cali", "Barranquilla", "Cartagena", "Cúcuta", 
    "Bucaramanga", "Pereira", "Santa Marta", "Ibagué", "Pasto", "Manizales", 
    "Neiva", "Villavicencio", "Armenia", "Valledupar", "Montería", "Sincelejo", 
    "Popayán", "Tunja", "Riohacha", "Florencia", "Quibdó", "Mocoa"
])))

# --- 3. DATOS MÉDICOS Y RECURSOS ---

recursos = {
    "ritmos": "https://upload.wikimedia.org/wikipedia/commons/e/e6/Atrial_fibrillation_ECG.png", 
    "iy": "https://upload.wikimedia.org/wikipedia/commons/0/05/JVP.jpg",
    "godet": "https://upload.wikimedia.org/wikipedia/commons/0/00/Combination_of_pitting_edema_and_stasis_dermatitis.jpg",
    # Audios (Placeholders funcionales de Wikimedia)
    "audio_s3": "https://upload.wikimedia.org/wikipedia/commons/7/76/S3_heart_sound.ogg",
    "audio_s4": "https://upload.wikimedia.org/wikipedia/commons/8/87/S4_heart_sound.ogg",
    "audio_estenosis_aortica": "https://upload.wikimedia.org/wikipedia/commons/9/99/Aortic_stenosis.ogg",
    "audio_insuf_mitral": "https://upload.wikimedia.org/wikipedia/commons/5/5c/Mitral_regurgitation.ogg",
    "audio_estertores": "https://upload.wikimedia.org/wikipedia/commons/3/33/Crackles_pneumonia.ogg",
    "audio_sibilancias": "https://upload.wikimedia.org/wikipedia/commons/e/e6/Wheezing_lung_sound.ogg",
    "audio_normal_lung": "https://upload.wikimedia.org/wikipedia/commons/a/a2/Vesicular_breath_sounds.ogg"
}

antecedentes_lista = sorted([
    "Apnea del sueño", "Arteritis reumatoide", "Cardiopatía congénita", 
    "Diabetes Mellitus Tipo 2", "Dislipidemia", "Enfermedad arterial oclusiva crónica", 
    "Enfermedad carotidea", "Enfermedad cerebro-vascular (ACV)", "Enfermedad coronaria", 
    "Hipertensión arterial", "Insuficiencia cardiaca previa", "Lupus eritematoso sistémico", 
    "Obesidad", "Tabaquismo", "VIH"
])

meds_agudos = {
    "diureticos": {
        "nombre": "Furosemida / Diuréticos de Asa",
        "dosis": "• Naïve (Vírgen de tto): 20-40 mg IV.\n• Uso crónico: 1 a 2.5 veces la dosis oral total diaria en bolo IV.\n• Resistencia: Infusión continua 5-40 mg/h + Tiazida (Metolazona/HCTZ).",
        "monitor": "• Gasto Urinario (>100-150 ml/h en las primeras 6h).\n• Electrolitos: K+ (riesgo hipokalemia), Mg++ (riesgo torsades).\n• Función Renal: Esperar elevación transitoria de Creatinina (permisiva si descongestiona).",
        "adverso": "Hipokalemia, Ototoxicidad (bolos rápidos >20mg/min), Hipotensión, Alcalosis metabólica."
    },
    "vasodilatadores": {
        "nombre": "Nitroglicerina / Nitroprusiato",
        "dosis": "• NTG: Iniciar 10-20 mcg/min, titular +10-20 mcg/min c/3-5 min. Máx 200 mcg/min.\n• Nitroprusiato: 0.3 mcg/kg/min (Solo UCI con línea arterial).",
        "monitor": "• Presión Arterial (Evitar PAS < 90 mmHg).\n• Cefalea intensa (NTG).\n• Saturación O2 (puede caer por alteración V/Q).",
        "adverso": "Hipotensión severa, Taquicardia refleja, Cefalea, Robo coronario. Nitroprusiato: Toxicidad por cianuro (falla renal/hepática)."
    },
    "inotropicos": {
        "nombre": "Dobutamina / Milrinone / Levosimendán",
        "dosis": "• Dobutamina: 2-20 mcg/kg/min (Beta-1 agonista).\n• Milrinone: 0.375-0.75 mcg/kg/min (Inodilatador, no requiere bolo).\n• Levosimendán: 0.1 mcg/kg/min (Sensibilizador Ca++).",
        "monitor": "• Telemetría (Arritmias ventriculares).\n• Isquemia miocárdica (Dobu aumenta consumo O2).\n• Presión Arterial (Milrinone causa hipotensión por vasodilatación).",
        "adverso": "Taquicardia sinusal, Fibrilación auricular, Hipotensión sostenida (Milrinone), Hipokalemia."
    },
    "vasopresores": {
        "nombre": "Norepinefrina",
        "dosis": "0.05 - 0.5 mcg/kg/min. Titular para PAM > 65 mmHg.",
        "monitor": "• Signos de perfusión distal y esplácnica.\n• Invasiva obligatoria.\n• Lactato sérico.",
        "adverso": "Isquemia/Necrosis distal, Arritmias, Hipertensión severa, Aumento de postcarga VI."
    }
}

# --- 4. LÓGICA CLÍNICA ---

def inferir_valvulopatia(foco, ciclo, patron, localizacion_soplo):
    if not localizacion_soplo: return "Sin soplos reportados."
    dx = "Soplo no específico"
    if foco == "Aórtico":
        if ciclo == "Sistólico": dx = "**Posible Estenosis Aórtica** (Busca pulso parvus et tardus)."
        elif ciclo == "Diastólico": dx = "**Posible Insuficiencia Aórtica** (Busca presión de pulso amplia)."
    elif foco == "Mitral":
        if ciclo == "Sistólico": dx = "**Posible Insuficiencia Mitral** (Busca irradiación a axila)."
        elif ciclo == "Diastólico": dx = "**Posible Estenosis Mitral** (Busca chasquido de apertura)."
    elif foco == "Tricúspideo" and ciclo == "Sistólico":
        dx = "**Posible Insuficiencia Tricuspídea** (Asoc. HTP, signo Rivero-Carvallo)."
    return dx

# --- 5. INTERFAZ: BARRA LATERAL (ENTRADA DE DATOS) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063823.png", width=50)
    st.title("Historia Clínica")
    st.markdown("---")
    
    # 1. ORIGEN
    st.subheader("1. Origen y Demografía")
    ciudad = st.selectbox("Municipio de Procedencia", ["--- Seleccione ---"] + municipios_base)
    
    # ALERTA CHAGAS
    es_zona_chagas = ciudad in zonas_chagas
    if es_zona_chagas:
        st.error(f"🚨 **ALERTA EPIDEMIOLÓGICA:** {ciudad} es zona de riesgo para **Enfermedad de Chagas** (Cardiopatía Chagásica).")
    
    col_d1, col_d2 = st.columns(2)
    edad = col_d1.number_input("Edad", 18, 120, 65)
    sexo = col_d2.selectbox("Sexo", ["M", "F", "Otro"])

    # 2. ANTECEDENTES
    st.subheader("2. Antecedentes")
    antecedentes = st.multiselect("Seleccione Patologías:", antecedentes_lista)

    # 3. SÍNTOMAS
    st.subheader("3. Síntomas")
    sintomas = st.multiselect("Seleccione:", ["Disnea esfuerzo", "Disnea reposo", "Ortopnea", "Bendopnea", "DPN", "Fatiga", "Angina", "Edema MsIs"])

    # 4. SIGNOS VITALES
    st.subheader("4. Signos Vitales")
    ritmo = st.selectbox("Ritmo Monitor", ["Sinusal", "Fibrilación Auricular", "Aleteo", "TV", "Marcapasos"])
    with st.expander("Ver Ritmos (Monitor)"): st.image(recursos["ritmos"])

    c_v1, c_v2 = st.columns(2)
    pas = c_v1.number_input("PAS (mmHg)", value=110)
    pad = c_v2.number_input("PAD (mmHg)", value=70)
    fc = c_v1.number_input("FC (lpm)", value=85)
    fr = c_v2.number_input("FR (rpm)", value=22)
    sato2 = c_v1.number_input("SatO2 (%)", value=92)
    temp_c = c_v2.number_input("Temp (°C)", value=36.5, step=0.1)

    # 5. EXAMEN FÍSICO (ORDENADO)
    st.subheader("5. Examen Físico")
    
    # A. CABEZA Y CUELLO
    st.markdown("🔴 **Cabeza y Cuello**")
    iy = st.selectbox("Ingurgitación Yugular (IY)", ["Ausente", "Grado I (45°)", "Grado II (45°)", "Grado III (90°)"])
    with st.expander("Ver Grados IY"): st.image(recursos["iy"])
    rhy = st.checkbox("Reflujo Hepato-yugular")

    # B. TÓRAX (CARDIO + PULMONAR)
    st.markdown("🔴 **Tórax: Cardiovascular**")
    
    # Ruidos
    opciones_ruidos = ["R1-R2 Normales", "S3 (Galope Ventricular)"]
    if ritmo == "Sinusal":
        opciones_ruidos.extend(["S4 (Galope Atrial)", "S3 + S4 (Suma)"])
    ruidos_agregados = st.selectbox("Ruidos:", opciones_ruidos)
    if "S3" in ruidos_agregados or "S4" in ruidos_agregados:
        with st.expander("🎧 Escuchar Galopes"):
            if "S3" in ruidos_agregados: st.audio(recursos["audio_s3"]); st.caption("S3")
            if "S4" in ruidos_agregados: st.audio(recursos["audio_s4"]); st.caption("S4")

    # Soplos
    tiene_soplo = st.checkbox("¿Tiene Soplo?")
    foco, ciclo, patron = "Aórtico", "Sistólico", "Holosistólico"
    if tiene_soplo:
        foco = st.selectbox("Foco", ["Aórtico", "Mitral", "Tricúspideo", "Pulmonar"])
        ciclo = st.selectbox("Ciclo", ["Sistólico", "Diastólico"])
        patron = st.selectbox("Patrón", ["Diamante", "Holosistólico", "Decrescendo", "Click"])
        with st.expander("🎧 Escuchar Soplos"):
            if "Aórtico" in foco: st.audio(recursos["audio_estenosis_aortica"])
            elif "Mitral" in foco: st.audio(recursos["audio_insuf_mitral"])

    st.markdown("🔴 **Tórax: Pulmonar**")
    pulmones = st.selectbox("Auscultación", ["Murmullo Vesicular", "Estertores basales", "Estertores >1/2", "Sibilancias"])
    with st.expander("🎧 Escuchar Pulmón"):
        if "Estertores" in pulmones: st.audio(recursos["audio_estertores"])
        elif "Sibilancias" in pulmones: st.audio(recursos["audio_sibilancias"])
        else: st.audio(recursos["audio_normal_lung"])

    # C. ABDOMEN
    st.markdown("🔴 **Abdomen**")
    ascitis = st.checkbox("Ascitis / Onda ascítica")
    hpm = st.checkbox("Hepatomegalia dolorosa")

    # D. EXTREMIDADES
    st.markdown("🔴 **Extremidades**")
    edema_ex = st.selectbox("Edema", ["Ausente", "Maleolar", "Rodillas", "Muslos/Anasarca"])
    with st.expander("Ver Edema (Godet)"): st.image(recursos["godet"])
    pulsos = st.selectbox("Pulsos Distales", ["Normales", "Disminuidos", "Filiformes"])
    frialdad = st.radio("Temperatura Distal", ["Caliente", "Fría/Húmeda"], horizontal=True)
    llenado = st.number_input("Llenado Capilar (seg)", 2)

    # E. NEUROLÓGICO
    st.markdown("🔴 **Neurológico**")
    neuro = st.selectbox("Estado de Conciencia", ["Alerta", "Somnoliento", "Estuporoso"])

# --- 6. CÁLCULOS Y LÓGICA ---

pam = pad + (pas - pad)/3
pp = pas - pad
ppp = (pp / pas) * 100 if pas > 0 else 0

# Score Congestión (Eje X) - Stevenson
score_congest = 0
if "Ortopnea" in sintomas: score_congest += 3
if "reposo" in str(sintomas): score_congest += 4
if "Grado II" in iy or "Grado III" in iy: score_congest += 4
if rhy: score_congest += 2
if "Estertores" in pulmones: score_congest += 3
if edema_ex != "Ausente": score_congest += 2
if ascitis: score_congest += 2
if "S3" in ruidos_agregados: score_congest += 4

pcp_sim = 12 + score_congest
if pcp_sim > 38: pcp_sim = 38 

# Score Perfusión (Eje Y) - Stevenson
score_perf = 2.8
if ppp < 25: score_perf -= 0.6
if frialdad != "Caliente": score_perf -= 0.6
if llenado > 3: score_perf -= 0.4
if pulsos == "Filiformes": score_perf -= 0.5
if pas < 90: score_perf -= 0.5
if neuro != "Alerta": score_perf -= 0.5

ic_sim = max(1.0, score_perf) 

# Clasificación
if pcp_sim > 18 and ic_sim > 2.2: cuadrante = "B: Húmedo y Caliente"
elif pcp_sim > 18 and ic_sim <= 2.2: cuadrante = "C: Húmedo y Frío"
elif pcp_sim <= 18 and ic_sim <= 2.2: cuadrante = "L: Seco y Frío"
else: cuadrante = "A: Seco y Caliente"

# --- 7. PANEL PRINCIPAL ---

st.title("🫀 HemoSim: Simulador Clínico")
st.markdown("**Simulación de Casos en Falla Cardíaca Aguda** | Dr. Javier Rodríguez Prada")

# RESUMEN DE DATOS INGRESADOS (NUEVO)
with st.expander("📋 **Ver Resumen de Datos Ingresados**", expanded=True):
    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown(f"**Paciente:** {edad} años, {sexo}")
        st.markdown(f"**Procedencia:** {ciudad}")
        if es_zona_chagas: st.error("⚠️ **Riesgo Chagas**")
        st.markdown(f"**Antecedentes:** {', '.join(antecedentes) if antecedentes else 'Niega'}")
    with r2:
        st.markdown("**Signos Vitales:**")
        st.markdown(f"PA: {pas}/{pad} | FC: {fc} | FR: {fr}")
        st.markdown(f"SatO2: {sato2}% | T: {temp_c}°C")
        if sato2 < 90: st.error("🚨 Hipoxemia")
    with r3:
        st.markdown("**Hallazgos Clave:**")
        st.markdown(f"Ruidos: {ruidos_agregados}")
        st.markdown(f"Pulmón: {pulmones}")
        st.markdown(f"Perfusión: {frialdad}, Llenado {llenado}s")

# ALERTA HIPOXEMIA
if sato2 < 90:
    st.error(f"🚨 **HIPOXEMIA ({sato2}%):** Administrar O2 suplementario (Cánula/Venturi) meta >90%. Considerar VNI si hay trabajo respiratorio.")

# TABLERO HEMODINÁMICO
st.markdown("### 📊 Hemodinamia Bedside")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("PAM", f"{pam:.0f} mmHg", help="Presión de perfusión tisular.")
col_m2.metric("P. Pulso", f"{pp} mmHg", help="Refleja volumen latido.")
col_m3.metric("PPP", f"{ppp:.1f} %", delta="- Hipoperfusión" if ppp < 25 else "OK", delta_color="inverse", help="<25% predice IC bajo.")
col_m4.metric("Perfil Stevenson", cuadrante)

if tiene_soplo:
    st.info(f"🩺 **Análisis Soplo:** {inferir_valvulopatia(foco, ciclo, patron, True)}")

# TABS PRINCIPALES
tabs = st.tabs(["📉 Cuadrante Stevenson", "💊 Simulación Terapéutica", "🏠 Plan de Egreso", "📚 Referencias"])

# TAB 1: GRÁFICO
with tabs[0]:
    col_g1, col_g2 = st.columns([3, 1])
    with col_g1:
        fig = go.Figure()
        # Cuadrantes
        fig.add_shape(type="rect", x0=0, y0=2.2, x1=18, y1=5, fillcolor="rgba(144, 238, 144, 0.2)", line_width=0)
        fig.add_shape(type="rect", x0=18, y0=2.2, x1=40, y1=5, fillcolor="rgba(255, 218, 185, 0.4)", line_width=0)
        fig.add_shape(type="rect", x0=0, y0=0, x1=18, y1=2.2, fillcolor="rgba(173, 216, 230, 0.3)", line_width=0)
        fig.add_shape(type="rect", x0=18, y0=0, x1=40, y1=2.2, fillcolor="rgba(255, 182, 193, 0.4)", line_width=0)
        
        # Líneas corte
        fig.add_vline(x=18, line_dash="solid", line_color="gray")
        fig.add_hline(y=2.2, line_dash="solid", line_color="gray")
        
        # Etiquetas
        fig.add_annotation(x=9, y=4.5, text="<b>A: SECO / CALIENTE</b>", showarrow=False, font=dict(color="green"))
        fig.add_annotation(x=29, y=4.5, text="<b>B: HÚMEDO / CALIENTE</b>", showarrow=False, font=dict(color="orange"))
        fig.add_annotation(x=9, y=0.5, text="<b>L: SECO / FRÍO</b>", showarrow=False, font=dict(color="blue"))
        fig.add_annotation(x=29, y=0.5, text="<b>C: HÚMEDO / FRÍO</b>", showarrow=False, font=dict(color="red"))

        # Paciente
        fig.add_trace(go.Scatter(x=[pcp_sim], y=[ic_sim], mode='markers+text', marker=dict(size=25, color='black', line=dict(width=2, color='white')), text=["<b>PACIENTE</b>"], textposition="top center"))
        
        fig.update_layout(title="Cuadrante de Forrester/Stevenson", xaxis_title="Congestión (PCP estimada)", yaxis_title="Perfusión (IC estimado)", height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_g2:
        st.markdown("#### Interpretación")
        st.markdown(f"**Estado: {cuadrante}**")
        if cuadrante.startswith("B"): st.success("Manejo: Diuréticos + Vasodilatadores (si PA permite).")
        if cuadrante.startswith("C"): st.error("Manejo: Inotrópicos +/- Vasopresores (si shock) + Diuréticos con cautela.")
        if cuadrante.startswith("L"): st.info("Manejo: Carga de volumen con precaución.")

# TAB 2: SIMULACIÓN
with tabs[1]:
    st.markdown("### 🧪 Laboratorio de Farmacología")
    st.info("Seleccione intervenciones para ver dosis, monitoreo y efecto vectorial.")
    
    c1, c2, c3, c4 = st.columns(4)
    dx, dy = 0, 0
    sel_med = None
    
    with c1:
        if st.checkbox("Furosemida IV"): dx-=8; dy+=0.1; sel_med="diureticos"
    with c2:
        if st.checkbox("Vasodilatador"): dx-=6; dy+=0.5; sel_med="vasodilatadores"
    with c3:
        if st.checkbox("Inotrópico"): dy+=1.2; dx-=2; sel_med="inotropicos"
    with c4:
        if st.checkbox("Vasopresor"): dy+=0.2; dx+=4; sel_med="vasopresores"

    if sel_med:
        info = meds_agudos[sel_med]
        st.markdown("---")
        k1, k2 = st.columns(2)
        with k1:
            st.markdown(f"#### 💊 {info['nombre']}")
            st.info(f"**Dosis / Titulación:**\n{info['dosis']}")
        with k2:
            st.warning(f"**⚠️ Seguridad y Adversos:** {info['adverso']}")
            st.error(f"**👁️ Monitoreo de Enfermería:**\n{info['monitor']}")
        st.markdown("---")

    # Gráfico Vector
    new_pcp, new_ic = pcp_sim + dx, ic_sim + dy
    fig_s = go.Figure(fig)
    fig_s.add_annotation(x=new_pcp, y=new_ic, ax=pcp_sim, ay=ic_sim, xref="x", yref="y", axref="x", ayref="y", arrowwidth=4, arrowhead=2, arrowcolor="purple")
    fig_s.add_trace(go.Scatter(x=[new_pcp], y=[new_ic], mode='markers', marker=dict(size=20, color='purple', symbol='x'), name="Post-Rx"))
    fig_s.update_layout(height=400, title="Proyección Post-Intervención")
    st.plotly_chart(fig_s, use_container_width=True)

# TAB 3: EGRESO
with tabs[2]:
    st.header("🏠 Plan de Egreso (GDMT)")
    
    gdmt = [
        {"Pilar": "BB", "Fármaco": "Metoprolol Succ.", "Dosis Inicio": "12.5-25 mg/d", "Meta": "200 mg/d"},
        {"Pilar": "ARNI", "Fármaco": "Sacubitrilo/Valsartán", "Dosis Inicio": "24/26 mg c/12h", "Meta": "97/103 mg c/12h"},
        {"Pilar": "ARM", "Fármaco": "Espironolactona", "Dosis Inicio": "12.5-25 mg/d", "Meta": "50 mg/d"},
        {"Pilar": "iSGLT2", "Fármaco": "Dapagliflozina", "Dosis Inicio": "10 mg/d", "Meta": "10 mg/d"},
    ]
    st.dataframe(pd.DataFrame(gdmt), use_container_width=True)
    
    c_ad1, c_ad2 = st.columns(2)
    with c_ad1:
        st.info("💉 **Hierro IV:** Si Ferritina <100 o IST <20%.")
        st.success("🫀 **Rehabilitación Cardíaca:** Ordenar Clase I-A.")
    with c_ad2:
        st.warning("🛡️ **Vacunación:** Influenza (Anual) + Neumococo.")
        st.error("📉 **Seguimiento:** Cita control < 7 días post-alta.")

# TAB 4: REFERENCIAS
with tabs[3]:
    st.markdown("""
    1. **ESC Guidelines 2021** for the diagnosis and treatment of acute and chronic heart failure.
    2. **AHA/ACC/HFSA 2022 Guideline** for the Management of Heart Failure.
    3. *Clinical Assessment of Heart Failure* (Uploaded PDF).
    4. *Diagnosis and Management of Heart Failure Patients with Reduced EF* (Uploaded PDF).
    """)

st.markdown("---")
st.caption("Desarrollado por: Javier Rodríguez Prada, MD | Enero 2026")

