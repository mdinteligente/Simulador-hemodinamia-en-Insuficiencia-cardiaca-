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
    /* Ajuste para inputs numéricos */
    input[type=number] { -moz-appearance: textfield; }
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
    "ritmos": "https://upload.wikimedia.org/wikipedia/commons/e/e6/Atrial_fibrillation_ECG.png", 
    "iy": "https://upload.wikimedia.org/wikipedia/commons/0/05/JVP.jpg",
    "godet": "https://upload.wikimedia.org/wikipedia/commons/0/00/Combination_of_pitting_edema_and_stasis_dermatitis.jpg",
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

# Farmacología Detallada (Sin Abreviaturas)
meds_agudos = {
    "oxigeno": {
        "nombre": "Oxígeno / Ventilación No Invasiva (VNI)",
        "dosis": "**Oxígeno:** Titular para saturación > 90% (>95% en embarazo).\n**VNI (CPAP/BiPAP):** Iniciar con PEEP 5-10 cmH2O. Indicado en edema pulmonar agudo, acidosis respiratoria o distrés respiratorio.",
        "monitor": "• Gases arteriales (control a la hora).\n• Estado de conciencia y tolerancia a la máscara.\n• Riesgo de hipotensión (la presión positiva intratorácica reduce el retorno venoso).",
        "adverso": "Resequedad de mucosas, claustrofobia, broncoaspiración (si hay deterioro del sensorio), barotrauma (raro)."
    },
    "diureticos": {
        "nombre": "Furosemida (Diurético de Asa)",
        "dosis": "**Pacientes vírgenes de tratamiento:** Bolo IV 20-40 mg.\n**Pacientes con uso crónico:** Bolo IV de 1 a 2.5 veces su dosis oral total diaria.\n**Infusión continua:** Si hay respuesta pobre a bolos, iniciar 5-40 mg/hora.\n**Combinación:** Si hay resistencia, agregar Tiazida (Hidroclorotiazida o Metolazona).",
        "monitor": "• Gasto urinario horario (Meta > 100-150 ml/hora).\n• Electrolitos: Potasio (K+), Magnesio (Mg++) cada 6-12h.\n• Función renal: Esperar elevación transitoria de Creatinina (permisiva si hay descongestión).",
        "adverso": "Hipokalemia, Hipomagnesemia, Ototoxicidad (infusiones rápidas), Hipotensión, Alcalosis metabólica."
    },
    "vasodilatadores": {
        "nombre": "Vasodilatadores (Nitroglicerina / Nitroprusiato)",
        "dosis": "**Nitroglicerina:** Iniciar 10-20 mcg/min. Titular ↑ 5-10 mcg/min cada 3-5 min. Dosis máxima usual 200 mcg/min.\n**Nitroprusiato de Sodio:** Iniciar 0.3 mcg/kg/min. Titular hasta 5 mcg/kg/min (Requiere línea arterial obligatoria).",
        "monitor": "• Presión Arterial continua (Detener si PAS < 90 mmHg).\n• Cefalea intensa (común con Nitroglicerina).\n• Saturación O2 (puede caer por alteración V/Q).",
        "adverso": "Hipotensión severa, Taquicardia refleja, Cefalea, Fenómeno de robo coronario. Nitroprusiato: Toxicidad por cianuro/tiocianato en uso prolongado o falla renal."
    },
    "inotropicos": {
        "nombre": "Inotrópicos (Dobutamina / Milrinone)",
        "dosis": "**Dobutamina:** 2-20 mcg/kg/min (Agonista Beta-1).\n**Milrinone:** 0.375-0.75 mcg/kg/min (Inhibidor PDE3, inodilatador, requiere ajuste en falla renal).\n**Levosimendán:** 0.1 mcg/kg/min (Sensibilizador de calcio).",
        "monitor": "• Monitoría electrocardiográfica continua (Arritmias ventriculares/auriculares).\n• Signos de isquemia (Dobutamina aumenta consumo O2).\n• Presión Arterial (Milrinone y Levosimendán causan hipotensión).",
        "adverso": "Taquicardia sinusal, Fibrilación auricular, Complejos ventriculares prematuros, Hipotensión sostenida (Milrinone), Hipokalemia."
    },
    "vasopresores": {
        "nombre": "Vasopresores (Norepinefrina)",
        "dosis": "**Norepinefrina:** 0.05 - 0.5 mcg/kg/min. Titular para PAM > 65 mmHg.\n(Vasopresor de elección en Shock Cardiogénico según guías).",
        "monitor": "• Signos de perfusión distal y esplácnica (Lactato).\n• Acceso venoso central preferido (riesgo de extravasación).\n• Línea arterial obligatoria.",
        "adverso": "Isquemia tisular (necrosis distal), Arritmias, Hipertensión severa, Aumento excesivo de la postcarga del ventrículo izquierdo."
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
    elif foco == "Pulmonar" and ciclo == "Diastólico":
         dx = "**Posible Insuficiencia Pulmonar** (Soplo de Graham Steell)."
    elif foco == "Tricúspideo" and ciclo == "Sistólico":
        dx = "**Posible Insuficiencia Tricuspídea** (Signo de Rivero-Carvallo)."
    return dx

def calcular_fenotipo_fevi(fevi):
    if fevi < 40: return "HFrEF (FEVI Reducida < 40%)"
    elif 40 <= fevi < 50: return "HFmrEF (FEVI Levemente Reducida 40-49%)"
    else: return "HFpEF (FEVI Preservada ≥ 50%)"

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
    sintomas = st.multiselect("Seleccione:", ["Disnea esfuerzo", "Disnea reposo", "Ortopnea", "Bendopnea", "DPN", "Fatiga", "Angina", "Edema MsIs (Subjetivo)"])

    # 4. Signos Vitales
    st.subheader("4. Signos Vitales")
    ritmo = st.selectbox("Ritmo", ["Sinusal", "Fibrilación Auricular", "Flutter Atrial", "Marcapasos", "Otro"])
    with st.expander("Ver Ritmos"): st.image(recursos["ritmos"])

    c_v1, c_v2 = st.columns(2)
    pas = c_v1.number_input("PAS (mmHg)", value=110, step=1)
    pad = c_v2.number_input("PAD (mmHg)", value=70, step=1)
    fc = c_v1.number_input("FC (lpm)", value=80, step=1)
    fr = c_v2.number_input("FR (rpm)", value=22, step=1)
    sato2 = c_v1.number_input("SatO2 (%)", value=92, step=1)
    temp_c = c_v2.number_input("Temp (°C)", value=36.5, step=0.1)
    
    # 5. Examen Físico
    st.subheader("5. Examen Físico")
    
    st.markdown("🔴 **Cabeza y Cuello**")
    iy = st.selectbox("IY", ["Ausente", "Grado I (45°)", "Grado II (45°)", "Grado III (90°)"])
    with st.expander("Ver Grados IY"): st.image(recursos["iy"])
    rhy = st.checkbox("Reflujo Hepato-yugular")

    st.markdown("🔴 **Tórax: Cardiovascular**")
    opciones_ruidos = ["R1-R2 Normales", "S3 (Galope Ventricular)"]
    if ritmo == "Sinusal":
        opciones_ruidos.extend(["S4 (Galope Atrial)", "S3 + S4 (Suma)"])
    
    ruidos_agregados = st.selectbox("Ruidos:", opciones_ruidos)
    with st.expander("🎧 Escuchar Ruidos", expanded=True):
        if "Normales" in ruidos_agregados: st.audio(recursos["audio_normal_heart"])
        elif "S3" in ruidos_agregados: st.audio(recursos["audio_s3"])
        elif "S4" in ruidos_agregados: st.audio(recursos["audio_s4"])

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

    st.markdown("🔴 **Tórax: Pulmonar**")
    pulmones = st.selectbox("Auscultación", ["Murmullo Vesicular", "Estertores basales", "Estertores >1/2", "Sibilancias"])
    with st.expander("🎧 Escuchar Pulmón"):
        if "Estertores" in pulmones: st.audio(recursos["audio_estertores"])
        elif "Sibilancias" in pulmones: st.audio(recursos["audio_sibilancias"])
        else: st.audio(recursos["audio_normal_lung"])

    st.markdown("🔴 **Abdomen**")
    abdomen_viscera = st.selectbox("Visceromegalias", ["Sin visceromegalias", "Hepatomegalia", "Esplenomegalia", "Hepatoesplenomegalia"])
    ascitis = st.checkbox("Onda Ascítica Presente")

    st.markdown("🔴 **Extremidades**")
    edema_ex = st.selectbox("Edema", ["Ausente", "Maleolar", "Rodillas", "Muslos"])
    if edema_ex != "Ausente":
        godet = st.selectbox("Fóvea (Godet)", ["Grado I (+)", "Grado II (++)", "Grado III (+++)", "Grado IV (++++)"])
        with st.expander("Ver Escala Godet"): st.image(recursos["godet"])
        
    pulsos = st.selectbox("Pulsos", ["Normales", "Disminuidos", "Filiformes"])
    frialdad = st.radio("Temp. Distal", ["Caliente", "Fría/Húmeda"], horizontal=True)
    llenado = st.number_input("Llenado Capilar (seg)", value=2, step=1)

    st.markdown("🔴 **Neurológico**")
    neuro = st.selectbox("Estado Conciencia", ["Alerta", "Somnoliento", "Estuporoso"])

    # 6. AYUDAS DIAGNÓSTICAS
    st.markdown("---")
    st.subheader("6. Paraclínicos (Opcional)")
    tiene_paraclinicos = st.checkbox("¿Habilitar Ayudas Diagnósticas?", value=False)
    
    lactato = 1.0
    rx_patron = "Normal"
    tipo_peptido = "BNP"
    valor_peptido = 0
    fevi = 55
    
    if tiene_paraclinicos:
        st.caption("Ingrese datos disponibles:")
        
        # Ecocardiograma
        st.markdown("**Ecocardiograma**")
        fevi = st.number_input("FEVI (%)", 0, 100, 35, help="Define el Fenotipo (Reducida/Preservada)")
        
        # Lactato
        lactato = st.number_input("Lactato (mmol/L)", 0.0, 20.0, 1.0, 0.1)
        
        # Rx
        st.markdown("**Radiografía de Tórax**")
        rx_patron = st.selectbox("Patrón Rx", ["Normal", "Congestión Leve/Basal", "Edema Alveolar (4 Cuadrantes)"])
        with st.expander("Ver Rx Referencia"):
            if rx_patron == "Normal": st.image(recursos["rx_normal"])
            elif rx_patron == "Congestión Leve/Basal": st.image(recursos["rx_congest"])
            else: st.image(recursos["rx_edema"])
        
        # Péptidos
        st.markdown("**Péptidos Natriuréticos**")
        c_p1, c_p2 = st.columns(2)
        tipo_peptido = c_p1.selectbox("Tipo", ["BNP", "NT-proBNP"])
        valor_peptido = c_p2.number_input("Valor (pg/mL)", 0, 50000, 0)
        
        if tipo_peptido == "NT-proBNP":
            st.caption(f"**Criterios HFA/ESC 2019:**\n• <50a: >450 | 50-75a: >900 | >75a: >1800 pg/mL")
        else:
            st.caption("**Criterio Agudo (BNP):** >400 pg/mL")

# --- 6. CÁLCULOS Y LOGICA ---
pam = pad + (pas - pad)/3
pp = pas - pad
ppp = (pp / pas) * 100 if pas > 0 else 0
fenotipo_msg = calcular_fenotipo_fevi(fevi) if tiene_paraclinicos else "No determinado (Requiere Eco)"

# Score Congestión (Eje X)
score_congest = 0
if "Ortopnea" in sintomas: score_congest += 3
if "reposo" in str(sintomas): score_congest += 4
if "Edema" in str(sintomas): score_congest += 1 # Edema subjetivo suma leve
if "Grado II" in iy or "Grado III" in iy: score_congest += 4
if rhy: score_congest += 2
if "Estertores" in pulmones: score_congest += 3
if edema_ex != "Ausente": score_congest += 2
if ascitis: score_congest += 2
if "Hepato" in abdomen_viscera: score_congest += 2
if "S3" in ruidos_agregados: score_congest += 4

if tiene_paraclinicos:
    if rx_patron == "Congestión Leve/Basal": score_congest += 2
    if rx_patron == "Edema Alveolar (4 Cuadrantes)": score_congest += 5
    
    is_positive_np = False
    if tipo_peptido == "BNP" and valor_peptido > 400: is_positive_np = True
    elif tipo_peptido == "NT-proBNP":
        if edad < 50 and valor_peptido > 450: is_positive_np = True
        elif 50 <= edad <= 75 and valor_peptido > 900: is_positive_np = True
        elif edad > 75 and valor_peptido > 1800: is_positive_np = True
    if is_positive_np: score_congest += 3

pcp_sim = 12 + score_congest
if pcp_sim > 38: pcp_sim = 38 

# Score Perfusión (Eje Y)
score_perf = 2.8
if ppp < 25: score_perf -= 0.6
if frialdad != "Caliente": score_perf -= 0.6
if llenado > 3: score_perf -= 0.4
if pulsos == "Filiformes": score_perf -= 0.5
if neuro != "Alerta": score_perf -= 0.5
if tiene_paraclinicos and lactato >= 2.0: score_perf -= 0.8

# AJUSTE CRÍTICO: HIPOTENSIÓN (SHOCK)
# Si PAM < 65, forzar desplazamiento hacia la izquierda (Mala perfusión)
if pam < 65:
    score_perf -= 1.0 # Penalización fuerte por hipotensión

ic_sim = max(1.0, score_perf) 

# Clasificación Stevenson
if pcp_sim > 18 and ic_sim > 2.2: cuadrante = "B: Húmedo y Caliente"
elif pcp_sim > 18 and ic_sim <= 2.2: cuadrante = "C: Húmedo y Frío"
elif pcp_sim <= 18 and ic_sim <= 2.2: cuadrante = "L: Seco y Frío"
else: cuadrante = "A: Seco y Caliente"

# --- 7. PANEL PRINCIPAL ---
st.title("🫀 HemoSim: Simulador Clínico")
st.markdown("**Simulación de Casos en Falla Cardíaca Aguda** | Dr. Javier Rodríguez Prada")

# RESUMEN
with st.expander("📋 **Ficha de Resumen Clínico**", expanded=True):
    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown(f"**Paciente:** {edad} años, {sexo}.")
        st.markdown(f"**Procedencia:** {ciudad}.")
        if es_zona_chagas: st.error("⚠️ **Alerta Epidemiológica:** Zona Endémica Chagas.")
        if tiene_paraclinicos: st.info(f"**Fenotipo (Eco):** {fenotipo_msg}")
    with r2:
        st.markdown(f"**Signos Vitales:** PA {pas}/{pad} | FC {fc} | FR {fr} | T {temp_c}°C")
        if sato2 < 90: st.error(f"🚨 **Hipoxemia:** SatO2 {sato2}%")
        else: st.markdown(f"**SatO2:** {sato2}%")
        if pam < 65: st.error(f"⚠️ **HIPOTENSIÓN/SHOCK:** PAM {pam:.0f} mmHg")
        if tiene_paraclinicos and lactato >= 2.0: st.error(f"⚠️ **Hipoperfusión:** Lactato {lactato} mmol/L")
    with r3:
        st.markdown("**Hallazgos Positivos:**")
        hallazgos = []
        if "S3" in ruidos_agregados: hallazgos.append("R3 presente")
        if "Estertores" in pulmones: hallazgos.append("Estertores")
        if edema_ex != "Ausente": hallazgos.append(f"Edema {edema_ex}")
        if ascitis: hallazgos.append("Ascitis")
        if "Hepato" in abdomen_viscera: hallazgos.append(abdomen_viscera)
        if "Ortopnea" in sintomas: hallazgos.append("Ortopnea")
        if "Edema" in str(sintomas): hallazgos.append("Edema (Refiere)")
        st.markdown(", ".join(hallazgos) if hallazgos else "Sin hallazgos mayores de congestión.")

# TABLERO HEMODINÁMICO (EXPLICADO)
st.markdown("### 📊 Hemodinamia Bedside (Cabecera del Paciente)")
c_m1, c_m2, c_m3, c_m4 = st.columns(4)

c_m1.metric("PAM", f"{pam:.0f} mmHg")
c_m1.caption("**Presión Arterial Media:** Presión promedio en un ciclo. < 65 mmHg compromete la perfusión de órganos vitales.")

c_m2.metric("P. Pulso", f"{pp} mmHg")
c_m2.caption("**Presión de Pulso (PAS-PAD):** Refleja el volumen latido y la rigidez arterial. < 25% de la PAS sugiere bajo gasto.")

c_m3.metric("PPP", f"{ppp:.1f}%", delta="Bajo" if ppp<25 else "OK", delta_color="inverse")
c_m3.caption("**Presión de Pulso Proporcional (PP/PAS):** Si es < 25%, predice un Índice Cardíaco < 2.2 L/min/m² (Sensibilidad 91%).")

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
    st.caption("Seleccione la intervención para ver el cambio vectorial y la información farmacológica.")
    cx1, cx2, cx3, cx4, cx5 = st.columns(5)
    dx, dy = 0, 0
    sel_med = None
    
    with cx1:
        if st.checkbox("Oxígeno / VNI"): 
            dx=0; dy=0; sel_med="oxigeno" # O2 no cambia el fenotipo hemodinámico primario (Stevenson), aunque mejora la oxigenación.
    with cx2:
        if st.checkbox("Furosemida"): dx-=8; dy+=0.1; sel_med="diureticos" # Baja PCP
    with cx3:
        if st.checkbox("Vasodilatador"): dx-=6; dy+=0.5; sel_med="vasodilatadores" # Baja PCP, Sube IC (Baja postcarga)
    with cx4:
        if st.checkbox("Inotrópico"): dy+=1.2; dx-=2; sel_med="inotropicos" # Sube IC, Baja PCP leve
    with cx5:
        if st.checkbox("Vasopresor"): dy+=0.3; dx+=2; sel_med="vasopresores" # Sube IC (Saca de shock), puede subir PCP leve

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
    if sel_med and sel_med != "oxigeno":
        fig_s.add_annotation(x=new_pcp, y=new_ic, ax=pcp_sim, ay=ic_sim, xref="x", yref="y", axref="x", ayref="y", arrowwidth=4, arrowhead=2, arrowcolor="purple")
        fig_s.add_trace(go.Scatter(x=[new_pcp], y=[new_ic], mode='markers', marker=dict(size=20, color='purple', symbol='x'), name="Post-Rx"))
    
    st.plotly_chart(fig_s, use_container_width=True)

# 3. EGRESO
with tabs[2]:
    st.header("🏠 Egreso en FEVI Reducida (HFrEF)")
    st.markdown("Esquema de Titulación GDMT.")
    gdmt = [
        {"Pilar": "Beta-Bloqueador", "Fármaco": "Succinato de Metoprolol", "Dosis Inicio": "12.5-25 mg c/24h", "Meta": "200 mg c/24h", "Monitoreo": "FC, PA, Fatiga"},
        {"Pilar": "Beta-Bloqueador", "Fármaco": "Carvedilol", "Dosis Inicio": "3.125 mg c/12h", "Meta": "25 mg c/12h (>85kg: 50mg)", "Monitoreo": "FC, PA (Hipotensión ortostática)"},
        {"Pilar": "Beta-Bloqueador", "Fármaco": "Bisoprolol", "Dosis Inicio": "1.25 mg c/24h", "Meta": "10 mg c/24h", "Monitoreo": "FC, PA"},
        {"Pilar": "Beta-Bloqueador", "Fármaco": "Nebivolol", "Dosis Inicio": "1.25 mg c/24h", "Meta": "10 mg c/24h", "Monitoreo": "FC, PA (Vasodilatador)"},
        {"Pilar": "ARNI", "Fármaco": "Sacubitrilo/Valsartán", "Dosis Inicio": "24/26 mg c/12h", "Meta": "97/103 mg c/12h", "Monitoreo": "PA, K+, Creatinina"},
        {"Pilar": "ARM", "Fármaco": "Espironolactona", "Dosis Inicio": "12.5-25 mg c/24h", "Meta": "50 mg c/24h", "Monitoreo": "K+ (>5.0 suspender), Creatinina"},
        {"Pilar": "iSGLT2", "Fármaco": "Dapa/Empagliflozina", "Dosis Inicio": "10 mg c/24h", "Meta": "10 mg c/24h", "Monitoreo": "Higiene genital, Glucosa (bajo riesgo hipo)"},
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
    st.subheader("🌍 Guías y Consensos Internacionales")
    st.markdown("""
    4. **Mueller C, et al.** Heart Failure Association of the European Society of Cardiology practical guidance on the use of natriuretic peptide concentrations. *Eur J Heart Fail*. 2019.
    5. **McDonagh TA, et al.** 2021 ESC Guidelines.
    6. **Heidenreich PA, et al.** 2022 AHA/ACC/HFSA Guideline.
    7. **Ponikowski P, et al.** AFFIRM-AHF (Hierro IV). *Lancet*. 2020.
    8. **Anker SD, et al.** EMPEROR-Preserved. *N Engl J Med*. 2021.
    9. **Solomon SD, et al.** DELIVER. *N Engl J Med*. 2022.
    """)

st.markdown("---")
st.caption("Desarrollado por: Javier Rodríguez Prada, MD | Enero 2026")
