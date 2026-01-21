import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(
    page_title="HemoSim: Docencia en Falla Cardíaca",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .big-font { font-size:20px !important; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 1.2rem; }
    .stAlert { padding: 0.5rem; }
    .caption-evidence { font-size: 0.8rem; color: #666; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTENTICACIÓN ---
def check_password():
    """Retorna True si el usuario/clave son correctos."""
    def password_entered():
        if (st.session_state["username"] == st.secrets["credentials"]["username"] and 
            st.session_state["password"] == st.secrets["credentials"]["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>🔐 Acceso Docente HemoSim</h2>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            st.text_input("Usuario", key="username")
            st.text_input("Contraseña", type="password", key="password", on_change=password_entered)
            st.info("Ingrese sus credenciales institucionales.")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("<h2 style='text-align: center;'>🔐 Acceso Docente HemoSim</h2>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            st.text_input("Usuario", key="username")
            st.text_input("Contraseña", type="password", key="password", on_change=password_entered)
            st.error("😕 Usuario o contraseña incorrectos")
        return False
    else:
        return True

if not check_password():
    st.stop()

# --- 3. RECURSOS Y DATA ---

# Municipios Chagas
zonas_chagas = [
    "Boavita", "Chiscas", "Cubará", "Güicán de la Sierra", "Labranzagrande", "Paya", "Pisba", "San Mateo", "Soatá", "Socotá", "Tipacoque", # Boyacá
    "Barichara", "Capitanejo", "Encinales", "Hato", "Mogotes", "San Gil", "San José de Miranda", "San Vicente del Chucurí", "Socorro", # Santander
    "Aguazul", "Chámeza", "Hato Corozal", "Nunchía", "Paz de Ariporo", "Recetor", "Támara", "Tauramena", "Yopal", # Casanare
    "Arauca", "Arauquita", "Saravena", "Tame", # Arauca
    "Choachí", "Fómeque", "Gachalá", "Medina", "Nilo", "Paratebueno", "Ubaque", # Cundinamarca
    "Cáchira", "Sardinata", "Toledo", # Norte Santander
    "La Jagua de Ibirico", "Pueblo Bello", "Valledupar", # Cesar
    "Liborina", "Peque", "Yolombó" # Antioquia
]
municipios_base = sorted(list(set(zonas_chagas + [
    "Bogotá D.C.", "Medellín", "Cali", "Barranquilla", "Cartagena", "Cúcuta", "Bucaramanga", "Pereira", "Santa Marta", "Ibagué", 
    "Pasto", "Manizales", "Neiva", "Villavicencio", "Armenia", "Montería", "Sincelejo", "Popayán", "Tunja", "Riohacha", "Florencia", "Quibdó"
])))

# Recursos Multimedia
recursos = {
    # Ritmos
    "ritmos": "https://upload.wikimedia.org/wikipedia/commons/e/e6/Atrial_fibrillation_ECG.png", 
    # Signos
    "iy": "https://upload.wikimedia.org/wikipedia/commons/0/05/JVP.jpg",
    "godet": "https://upload.wikimedia.org/wikipedia/commons/0/00/Combination_of_pitting_edema_and_stasis_dermatitis.jpg",
    # Rx Tórax
    "rx_normal": "https://upload.wikimedia.org/wikipedia/commons/a/a1/Normal_posteroanterior_%28PA%29_chest_radiograph_%28X-ray%29.jpg",
    "rx_congest": "https://upload.wikimedia.org/wikipedia/commons/2/22/Pulmonary_congestion.jpg", 
    "rx_edema": "https://upload.wikimedia.org/wikipedia/commons/6/6d/Pulmonary_edema.jpg", 
    
    # Audios
    "audio_normal_heart": "https://upload.wikimedia.org/wikipedia/commons/c/c0/Heart_normal.ogg",
    "audio_s3": "https://upload.wikimedia.org/wikipedia/commons/7/76/S3_heart_sound.ogg",
    "audio_s4": "https://upload.wikimedia.org/wikipedia/commons/8/87/S4_heart_sound.ogg",
    "audio_estenosis_aortica": "https://upload.wikimedia.org/wikipedia/commons/9/99/Aortic_stenosis.ogg",
    "audio_insuf_mitral": "https://upload.wikimedia.org/wikipedia/commons/5/5c/Mitral_regurgitation.ogg",
    "audio_insuf_aortica": "https://upload.wikimedia.org/wikipedia/commons/e/e3/Aortic_regurgitation.ogg", 
    "audio_estenosis_mitral": "https://upload.wikimedia.org/wikipedia/commons/3/30/Diastolic_rumble.ogg",
    "audio_insuf_pulmonar": "https://upload.wikimedia.org/wikipedia/commons/e/e3/Aortic_regurgitation.ogg", 
    "audio_estertores": "https://upload.wikimedia.org/wikipedia/commons/3/33/Crackles_pneumonia.ogg",
    "audio_sibilancias": "https://upload.wikimedia.org/wikipedia/commons/e/e6/Wheezing_lung_sound.ogg",
    "audio_normal_lung": "https://upload.wikimedia.org/wikipedia/commons/a/a2/Vesicular_breath_sounds.ogg"
}

# Antecedentes
antecedentes_lista = sorted([
    "Apnea del sueño", "Arteritis reumatoide", "Cardiopatía congénita", "Diabetes Mellitus Tipo 2", "Dislipidemia", 
    "Enfermedad arterial oclusiva crónica", "Enfermedad carotidea", "Enfermedad cerebro-vascular (ACV)", "Enfermedad coronaria", 
    "Hipertensión arterial", "Insuficiencia cardiaca previa", "Lupus eritematoso sistémico", "Obesidad", "Tabaquismo", "VIH"
])

meds_agudos = {
    "oxigeno": {
        "nombre": "Oxígeno / VNI",
        "dosis": "• O2: Meta SatO2 > 90%.\n• VNI (CPAP/BiPAP): Disminuye precarga y postcarga VI. Útil en edema pulmonar.",
        "monitor": "• Gases arteriales.\n• Tolerancia.",
        "adverso": "Intolerancia, Hipotensión (VNI)."
    },
    "diureticos": {
        "nombre": "Furosemida / Diuréticos de Asa",
        "dosis": "• Naïve: 20-40 mg IV.\n• Crónico: 1-2.5x dosis oral en bolo IV.\n• Resistencia: Infusión 5-40 mg/h + Tiazida.",
        "monitor": "• Gasto Urinario (>100ml/h).\n• K+, Mg++.\n• Cr.",
        "adverso": "Hipokalemia, Ototoxicidad, Hipotensión, Alcalosis."
    },
    "vasodilatadores": {
        "nombre": "Nitroglicerina / Nitroprusiato",
        "dosis": "• NTG: 10-20 mcg/min, titular.\n• NTP: 0.3 mcg/kg/min (Solo UCI).",
        "monitor": "• PA (Evitar PAS<90).\n• Cefalea.\n• SatO2.",
        "adverso": "Hipotensión, Cefalea, Robo coronario, Toxicidad cianuro."
    },
    "inotropicos": {
        "nombre": "Dobu / Milrinone / Levosimendán",
        "dosis": "• Dobu: 2-20 mcg/kg/min.\n• Milrinone: 0.375-0.75 mcg/kg/min.\n• Levo: 0.1 mcg/kg/min.",
        "monitor": "• Arritmias.\n• Isquemia.\n• PA (Hipotensión con Milri).",
        "adverso": "Taquicardia, FA, Hipotensión, Hipokalemia."
    },
    "vasopresores": {
        "nombre": "Norepinefrina",
        "dosis": "0.05 - 0.5 mcg/kg/min. Meta PAM > 65.",
        "monitor": "• Perfusión distal.\n• Línea arterial.",
        "adverso": "Isquemia distal, Arritmias, HTA severa."
    }
}

# --- 4. LÓGICA CLÍNICA ---
def inferir_valvulopatia(foco, ciclo, patron, localizacion_soplo):
    if not localizacion_soplo: return "Sin soplos reportados."
    dx = "Soplo no específico"
    if foco == "Aórtico":
        if ciclo == "Sistólico": dx = "**Posible Estenosis Aórtica** (Busca pulso parvus)."
        elif ciclo == "Diastólico": dx = "**Posible Insuficiencia Aórtica** (Busca presión pulso amplia)."
    elif foco == "Mitral":
        if ciclo == "Sistólico": dx = "**Posible Insuficiencia Mitral** (Busca irradiación axila)."
        elif ciclo == "Diastólico": dx = "**Posible Estenosis Mitral** (Busca chasquido)."
    elif foco == "Pulmonar" and ciclo == "Diastólico":
         dx = "**Posible Insuficiencia Pulmonar** (Soplo de Graham Steell)."
    elif foco == "Tricúspideo" and ciclo == "Sistólico":
        dx = "**Posible Insuficiencia Tricuspídea** (Signo Rivero-Carvallo)."
    return dx

# --- 5. INTERFAZ: BARRA LATERAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063823.png", width=50)
    st.title("Historia Clínica")
    st.markdown("---")
    
    # 1. Origen
    st.subheader("1. Origen y Demografía")
    ciudad = st.selectbox("Municipio", ["--- Seleccione ---"] + municipios_base)
    es_zona_chagas = ciudad in zonas_chagas
    if es_zona_chagas: st.error(f"🚨 **ALERTA EPIDEMIOLÓGICA:** Riesgo de Chagas en {ciudad}.")
    
    c_d1, c_d2 = st.columns(2)
    edad = c_d1.number_input("Edad", 18, 120, 65)
    sexo = c_d2.selectbox("Sexo", ["M", "F", "Otro"])

    # 2. Antecedentes
    st.subheader("2. Antecedentes")
    antecedentes = st.multiselect("Patologías:", antecedentes_lista)

    # 3. Síntomas
    st.subheader("3. Síntomas")
    sintomas = st.multiselect("Seleccione:", ["Disnea esfuerzo", "Disnea reposo", "Ortopnea", "Bendopnea", "DPN", "Fatiga", "Angina", "Edema"])
    if "Ortopnea" in sintomas: st.caption("*Ortopnea: S 73-88% / E 20-50%*")

    # 4. Signos Vitales
    st.subheader("4. Signos Vitales")
    ritmo = st.selectbox("Ritmo", ["Sinusal", "Fibrilación Auricular", "Flutter Atrial", "Marcapasos", "Otro"])
    with st.expander("Ver Ritmos"): st.image(recursos["ritmos"])

    c_v1, c_v2 = st.columns(2)
    pas = c_v1.number_input("PAS", 110)
    pad = c_v2.number_input("PAD", 70)
    fc = c_v1.number_input("FC", 85)
    fr = c_v2.number_input("FR", 22)
    sato2 = c_v1.number_input("SatO2 (%)", 92)
    temp_c = c_v2.number_input("T (°C)", 36.5, step=0.1)
    
    # 5. Examen Físico
    st.subheader("5. Examen Físico")
    
    st.markdown("🔴 **Cabeza y Cuello**")
    iy = st.selectbox("IY", ["Ausente", "Grado I (45°)", "Grado II (45°)", "Grado III (90°)"])
    rhy = st.checkbox("Reflujo Hepato-yugular")

    st.markdown("🔴 **Cardiovascular**")
    opciones_ruidos = ["R1-R2 Normales", "S3 (Galope Ventricular)"]
    if ritmo == "Sinusal":
        opciones_ruidos.extend(["S4 (Galope Atrial)", "S3 + S4 (Suma)"])
    
    ruidos_agregados = st.selectbox("Ruidos:", opciones_ruidos)
    with st.expander("🎧 Escuchar Ruidos", expanded=True):
        if "Normales" in ruidos_agregados: st.audio(recursos["audio_normal_heart"])
        elif "S3" in ruidos_agregados: st.audio(recursos["audio_s3"])
        elif "S4" in ruidos_agregados: st.audio(recursos["audio_s4"])

    # Soplos
    tiene_soplo = st.checkbox("¿Tiene Soplo?")
    foco, ciclo, patron = "Aórtico", "Sistólico", "Holosistólico"
    if tiene_soplo:
        foco = st.selectbox("Foco", ["Aórtico", "Mitral", "Tricúspideo", "Pulmonar"])
        ciclo = st.selectbox("Ciclo", ["Sistólico", "Diastólico"])
        patron = st.selectbox("Patrón", ["Diamante", "Holosistólico", "Decrescendo", "Click", "Retumbo"])
        with st.expander("🎧 Escuchar Ejemplo"):
            if "Aórtico" in foco and ciclo == "Diastólico": st.audio(recursos["audio_insuf_aortica"])
            elif "Mitral" in foco and ciclo == "Diastólico": st.audio(recursos["audio_estenosis_mitral"])
            elif "Aórtico" in foco: st.audio(recursos["audio_estenosis_aortica"])

    st.markdown("🔴 **Pulmonar**")
    pulmones = st.selectbox("Auscultación", ["Murmullo Vesicular", "Estertores basales", "Estertores >1/2", "Sibilancias"])
    with st.expander("🎧 Escuchar Pulmón"):
        if "Estertores" in pulmones: st.audio(recursos["audio_estertores"])
        elif "Sibilancias" in pulmones: st.audio(recursos["audio_sibilancias"])
        else: st.audio(recursos["audio_normal_lung"])

    st.markdown("🔴 **Abdomen/Extremidades**")
    ascitis = st.checkbox("Ascitis")
    edema_ex = st.selectbox("Edema", ["Ausente", "Maleolar", "Rodillas", "Muslos"])
    pulsos = st.selectbox("Pulsos", ["Normales", "Disminuidos", "Filiformes"])
    frialdad = st.radio("Temp. Distal", ["Caliente", "Fría/Húmeda"], horizontal=True)
    llenado = st.number_input("Llenado (seg)", 2)
    neuro = st.selectbox("Neuro", ["Alerta", "Somnoliento", "Estuporoso"])

    # 6. AYUDAS DIAGNÓSTICAS (OPCIONALES)
    st.markdown("---")
    st.subheader("6. Paraclínicos (Opcional)")
    tiene_paraclinicos = st.checkbox("¿Dispone de Ayudas Diagnósticas?", value=False)
    
    lactato = 1.0
    rx_patron = "Normal"
    tipo_peptido = "BNP"
    valor_peptido = 0
    
    if tiene_paraclinicos:
        st.caption("Ingrese los valores disponibles:")
        lactato = st.number_input("Lactato (mmol/L)", 0.0, 20.0, 1.0, 0.1)
        
        st.markdown("**Radiografía de Tórax**")
        rx_patron = st.selectbox("Patrón Rx", ["Normal", "Congestión Leve/Basal", "Edema Alveolar (4 Cuadrantes)"])
        with st.expander("Ver Rx Referencia"):
            if rx_patron == "Normal": st.image(recursos["rx_normal"])
            elif rx_patron == "Congestión Leve/Basal": st.image(recursos["rx_congest"])
            else: st.image(recursos["rx_edema"])
        
        st.markdown("**Péptidos Natriuréticos**")
        c_p1, c_p2 = st.columns(2)
        tipo_peptido = c_p1.selectbox("Tipo", ["BNP", "NT-proBNP"])
        valor_peptido = c_p2.number_input("Valor (pg/mL)", 0, 30000, 0)


# --- 6. CÁLCULOS Y LOGICA ---
pam = pad + (pas - pad)/3
pp = pas - pad
ppp = (pp / pas) * 100 if pas > 0 else 0

# Score Congestión (Eje X)
score_congest = 0
# Clínica
if "Ortopnea" in sintomas: score_congest += 3
if "reposo" in str(sintomas): score_congest += 4
if "Grado II" in iy or "Grado III" in iy: score_congest += 4
if rhy: score_congest += 2
if "Estertores" in pulmones: score_congest += 3
if edema_ex != "Ausente": score_congest += 2
if "S3" in ruidos_agregados: score_congest += 4
# Paraclínicos (Si habilitados)
if tiene_paraclinicos:
    if rx_patron == "Congestión Leve/Basal": score_congest += 2
    if rx_patron == "Edema Alveolar (4 Cuadrantes)": score_congest += 5
    # Péptidos (Umbrales de Alta Probabilidad de Congestión)
    if tipo_peptido == "BNP" and valor_peptido > 400: score_congest += 3
    if tipo_peptido == "NT-proBNP" and valor_peptido > 1000: score_congest += 3

pcp_sim = 12 + score_congest
if pcp_sim > 38: pcp_sim = 38 

# Score Perfusión (Eje Y)
score_perf = 2.8
# Clínica
if ppp < 25: score_perf -= 0.6
if frialdad != "Caliente": score_perf -= 0.6
if llenado > 3: score_perf -= 0.4
if pulsos == "Filiformes": score_perf -= 0.5
if pas < 90: score_perf -= 0.5
if neuro != "Alerta": score_perf -= 0.5
# Paraclínicos
if tiene_paraclinicos:
    if lactato > 2.0: score_perf -= 0.8 # Hiperlactatemia

ic_sim = max(1.0, score_perf) 

# Clasificación
if pcp_sim > 18 and ic_sim > 2.2: cuadrante = "B: Húmedo y Caliente"
elif pcp_sim > 18 and ic_sim <= 2.2: cuadrante = "C: Húmedo y Frío"
elif pcp_sim <= 18 and ic_sim <= 2.2: cuadrante = "L: Seco y Frío"
else: cuadrante = "A: Seco y Caliente"

# --- 7. PANEL PRINCIPAL ---
st.title("🫀 HemoSim: Simulador Clínico")
st.markdown("**Simulación de Casos en Falla Cardíaca Aguda** | Dr. Javier Rodríguez Prada")

# RESUMEN
with st.expander("📋 **Resumen de Datos**", expanded=True):
    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown(f"**Pcte:** {edad}a, {sexo}. **De:** {ciudad}")
        if es_zona_chagas: st.error("⚠️ Riesgo Chagas")
        st.markdown(f"**Antecedentes:** {', '.join(antecedentes) if antecedentes else 'Niega'}")
    with r2:
        st.markdown(f"**SV:** PA {pas}/{pad}, FC {fc}, Sat {sato2}%")
        if sato2 < 90: st.error("🚨 Hipoxemia")
        if tiene_paraclinicos and lactato > 2.0: st.error(f"⚠️ Lactato Elevado: {lactato}")
    with r3:
        st.markdown(f"**Examen:** {ruidos_agregados}, {pulmones}")
        if tiene_paraclinicos: st.markdown(f"**Ayudas:** Rx {rx_patron}, {tipo_peptido}: {valor_peptido}")
        st.markdown(f"**Perfusión:** {frialdad}, Llenado {llenado}s")

# ALERTAS CLÍNICAS
if sato2 < 90:
    st.error(f"🚨 **HIPOXEMIA ({sato2}%):** Administrar O2 suplementario. Meta >90%. Considerar gases arteriales.")

# TABLERO HEMODINÁMICO
st.markdown("### 📊 Hemodinamia Bedside (Cabecera del Paciente)")
c_m1, c_m2, c_m3, c_m4 = st.columns(4)
c_m1.metric("PAM", f"{pam:.0f} mmHg")
c_m1.caption("Presión de perfusión.")
c_m2.metric("P. Pulso", f"{pp} mmHg")
c_m2.caption("Rigidez/Volumen Latido.")
c_m3.metric("PPP", f"{ppp:.1f}%", delta="Bajo" if ppp<25 else "OK", delta_color="inverse")
c_m3.caption("Predice IC < 2.2 si <25%.")
c_m4.metric("Perfil", cuadrante)
if tiene_soplo: st.info(f"🩺 **Soplo:** {inferir_valvulopatia(foco, ciclo, patron, True)}")

# TABS
tabs = st.tabs(["📉 Stevenson", "💊 Terapéutica", "🏠 Egreso (HFrEF)", "⚖️ IC FEVI Preservada", "📚 Referencias"])

# 1. GRÁFICO
with tabs[0]:
    c_g1, c_g2 = st.columns([3, 1])
    with c_g1:
        fig = go.Figure()
        fig.add_shape(type="rect", x0=0, y0=2.2, x1=18, y1=5, fillcolor="rgba(144, 238, 144, 0.2)", line_width=0)
        fig.add_shape(type="rect", x0=18, y0=2.2, x1=40, y1=5, fillcolor="rgba(255, 218, 185, 0.4)", line_width=0)
        fig.add_shape(type="rect", x0=0, y0=0, x1=18, y1=2.2, fillcolor="rgba(173, 216, 230, 0.3)", line_width=0)
        fig.add_shape(type="rect", x0=18, y0=0, x1=40, y1=2.2, fillcolor="rgba(255, 182, 193, 0.4)", line_width=0)
        fig.add_vline(x=18, line_dash="solid", line_color="gray")
        fig.add_hline(y=2.2, line_dash="solid", line_color="gray")
        
        fig.add_annotation(x=9, y=4.5, text="<b>A: SECO / CALIENTE</b>", showarrow=False, font=dict(color="green"))
        fig.add_annotation(x=29, y=4.5, text="<b>B: HÚMEDO / CALIENTE</b>", showarrow=False, font=dict(color="orange"))
        fig.add_annotation(x=9, y=0.5, text="<b>L: SECO / FRÍO</b>", showarrow=False, font=dict(color="blue"))
        fig.add_annotation(x=29, y=0.5, text="<b>C: HÚMEDO / FRÍO</b>", showarrow=False, font=dict(color="red"))

        fig.add_trace(go.Scatter(x=[pcp_sim], y=[ic_sim], mode='markers+text', marker=dict(size=25, color='black', line=dict(width=2, color='white')), text=["<b>PACIENTE</b>"], textposition="top center"))
        fig.update_layout(title="Cuadrante Forrester/Stevenson", xaxis_title="Congestión (PCP)", yaxis_title="Perfusión (IC)", height=500)
        st.plotly_chart(fig, use_container_width=True)
    with c_g2:
        st.markdown(f"**Estado: {cuadrante}**")
        if cuadrante.startswith("B"): st.success("Manejo: Diuréticos + Vasodilatadores.")
        if cuadrante.startswith("C"): st.error("Manejo: Inotrópicos +/- Vasopresores.")
        if cuadrante.startswith("L"): st.info("Manejo: Carga de volumen con cautela.")

# 2. SIMULACIÓN
with tabs[1]:
    st.markdown("### 🧪 Farmacología Aguda")
    cx1, cx2, cx3, cx4, cx5 = st.columns(5)
    dx, dy = 0, 0
    sel_med = None
    
    with cx1:
        if st.checkbox("Oxígeno / VNI"): 
            dx+=0.1; dy-=2; sel_med="oxigeno"
    with cx2:
        if st.checkbox("Furosemida"): dx-=8; dy+=0.1; sel_med="diureticos"
    with cx3:
        if st.checkbox("Vasodilatador"): dx-=6; dy+=0.5; sel_med="vasodilatadores"
    with cx4:
        if st.checkbox("Inotrópico"): dy+=1.2; dx-=2; sel_med="inotropicos"
    with cx5:
        if st.checkbox("Vasopresor"): dy+=0.2; dx+=4; sel_med="vasopresores"

    if sel_med:
        info = meds_agudos[sel_med]
        st.markdown("---")
        k1, k2 = st.columns(2)
        with k1:
            st.markdown(f"#### 💊 {info['nombre']}")
            st.info(f"**Dosis:**\n{info['dosis']}")
        with k2:
            st.warning(f"**Adversos:** {info['adverso']}")
            st.error(f"**Monitoreo:**\n{info['monitor']}")
        st.markdown("---")
    
    new_pcp, new_ic = pcp_sim + dx, ic_sim + dy
    fig_s = go.Figure(fig)
    fig_s.add_annotation(x=new_pcp, y=new_ic, ax=pcp_sim, ay=ic_sim, xref="x", yref="y", axref="x", ayref="y", arrowwidth=4, arrowhead=2, arrowcolor="purple")
    fig_s.add_trace(go.Scatter(x=[new_pcp], y=[new_ic], mode='markers', marker=dict(size=20, color='purple', symbol='x'), name="Post-Rx"))
    st.plotly_chart(fig_s, use_container_width=True)

# 3. EGRESO
with tabs[2]:
    st.header("🏠 Egreso en FEVI Reducida (HFrEF)")
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
        st.warning("🛡️ **Vacunación:** Influenza + Neumococo.")
        st.error("📉 **Seguimiento:** Cita < 7 días.")

# 4. FEVI PRESERVADA
with tabs[3]:
    st.header("⚖️ Insuficiencia Cardíaca con FEVI Preservada (HFpEF)")
    st.markdown("FEVI ≥ 50%. El manejo se basa en fenotipos y uso de iSGLT2.")
    col_hf1, col_hf2 = st.columns(2)
    with col_hf1:
        st.success("✅ **Pilar Clase I-A**")
        st.markdown("**iSGLT2 (Dapagliflozina / Empagliflozina):** Única terapia que reduce eventos duros de forma consistente.")
    with col_hf2:
        st.warning("🔎 **Manejo por Fenotipos**")
        st.markdown("* **HTA:** ARNI/Espironolactona.\n* **FA:** Control ritmo/frecuencia.\n* **Amiloidosis TTR:** Tafamidis.")

# 5. REFERENCIAS
with tabs[4]:
    st.header("📚 Referencias Bibliográficas")
    st.subheader("📖 Texto Guía: Braunwald's Heart Disease (Edición 2026)")
    st.markdown("""
    1. **Januzzi JL, Mann DL.** *Clinical Assessment of Heart Failure* (Capítulo 56).
    2. **Felker GM, Teerlink JR.** *Diagnosis and Management of Decompensated Heart Failure* (Capítulo 57).
    3. **Diagnosis and Management of Heart Failure Patients with Reduced Ejection Fraction**.
    """)
    st.divider()
    st.subheader("🌍 Guías Internacionales")
    st.markdown("""
    4. **McDonagh TA, et al.** 2021 ESC Guidelines.
    5. **Heidenreich PA, et al.** 2022 AHA/ACC/HFSA Guideline.
    6. **Ponikowski P, et al.** AFFIRM-AHF (Hierro IV). *Lancet*. 2020.
    """)

st.markdown("---")
st.caption("Desarrollado por: Javier Rodríguez Prada, MD | Enero 2026")

