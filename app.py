import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="HemoSim: Docencia en Falla Cardíaca",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 5px; }
    .stTabs [aria-selected="true"] { background-color: #ff4b4b; color: white; }
    div[data-testid="stMetricValue"] { font-size: 1.2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE RECURSOS (IMÁGENES Y AUDIO) ---
recursos = {
    # IMÁGENES
    "ritmos": "https://upload.wikimedia.org/wikipedia/commons/e/e6/Atrial_fibrillation_ECG.png", 
    "iy": "https://upload.wikimedia.org/wikipedia/commons/0/05/JVP.jpg",
    "godet": "https://upload.wikimedia.org/wikipedia/commons/0/00/Combination_of_pitting_edema_and_stasis_dermatitis.jpg",
    
    # AUDIOS
    "audio_s3": "https://upload.wikimedia.org/wikipedia/commons/7/76/S3_heart_sound.ogg",
    "audio_s4": "https://upload.wikimedia.org/wikipedia/commons/8/87/S4_heart_sound.ogg",
    "audio_estenosis_aortica": "https://upload.wikimedia.org/wikipedia/commons/9/99/Aortic_stenosis.ogg",
    "audio_insuf_mitral": "https://upload.wikimedia.org/wikipedia/commons/5/5c/Mitral_regurgitation.ogg",
    "audio_estertores": "https://upload.wikimedia.org/wikipedia/commons/3/33/Crackles_pneumonia.ogg",
    "audio_sibilancias": "https://upload.wikimedia.org/wikipedia/commons/e/e6/Wheezing_lung_sound.ogg",
    "audio_normal_lung": "https://upload.wikimedia.org/wikipedia/commons/a/a2/Vesicular_breath_sounds.ogg"
}

# --- LÓGICA CLÍNICA: SOPLOS ---
def inferir_valvulopatia(foco, ciclo, patron, localizacion_soplo):
    if not localizacion_soplo: return "Sin soplos reportados."
    
    dx = "Soplo no específico"
    if foco == "Aórtico":
        if ciclo == "Sistólico":
            dx = "**Posible Estenosis Aórtica:** Obstrucción al tracto de salida. \n*Busca:* Pulso parvus et tardus, desdoblamiento paradójico de R2."
        elif ciclo == "Diastólico":
            dx = "**Posible Insuficiencia Aórtica:** Regurgitación diastólica. \n*Busca:* Presión de pulso amplia, signo de Musset."
    elif foco == "Mitral":
        if ciclo == "Sistólico":
            if "Holosistólico" in patron:
                dx = "**Posible Insuficiencia Mitral:** Regurgitación a la aurícula. \n*Busca:* Irradiación a axila, R3."
            elif "Click" in patron:
                 dx = "**Posible Prolapso VM:** Click mesosistólico."
        elif ciclo == "Diastólico":
            dx = "**Posible Estenosis Mitral:** Obstrucción llenado VI. \n*Busca:* Chasquido de apertura, retumbo diastólico."
    elif foco == "Tricúspideo":
        if ciclo == "Sistólico":
            dx = "**Posible Insuficiencia Tricuspídea:** Común en HTP. \n*Busca:* Signo de Rivero-Carvallo, onda V yugular."
            
    return dx

# --- DATA: FARMACOLOGÍA ---
meds_agudos = {
    "diureticos": {
        "nombre": "Furosemida / Diuréticos de Asa",
        "dosis": "Bolo: 20-40 mg IV (o 2x dosis oral). Infusión: 5-40 mg/h si hay resistencia.",
        "monitor": "• Gasto Urinario (>100cc/h).\n• K+ y Mg++ c/12h.\n• Función Renal diaria.",
        "adverso": "Hipokalemia, Ototoxicidad, Falla renal aguda."
    },
    "vasodilatadores": {
        "nombre": "Nitroglicerina / Nitroprusiato",
        "dosis": "NTG: 10-20 mcg/min, titular. NTP: 0.3 mcg/kg/min.",
        "monitor": "• PA invasiva recomendada.\n• Cefalea, SatO2 (shunt).",
        "adverso": "Hipotensión severa, Robo coronario, Toxicidad Tiocianato (NTP)."
    },
    "inotropicos": {
        "nombre": "Dobu / Milrinone / Levosimendán",
        "dosis": "Dobu: 2-20 mcg/kg/min. Milrinone: 0.375-0.75 mcg/kg/min.",
        "monitor": "• Arritmias ventriculares.\n• Isquemia (Dobu).\n• PA (Milrinone hipotensa).",
        "adverso": "Taquicardia, FA, Hipotensión, Hipokalemia."
    },
    "vasopresores": {
        "nombre": "Norepinefrina",
        "dosis": "0.05 - 0.5 mcg/kg/min. Meta PAM > 65.",
        "monitor": "• Perfusión distal/esplácnica.\n• Línea arterial.",
        "adverso": "Necrosis distal, Arritmias, HTA severa."
    }
}

# --- ENCABEZADO ---
st.title("🫀 HemoSim: Docencia en Cardiología")
st.markdown("**Simulador de Hemodinamia en Falla Cardíaca y Guía Terapéutica Interactiva**")
st.caption("Herramienta Docente - Dr. Javier Rodríguez Prada")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("📝 Historia Clínica")
    
    # 1. Demográficos
    st.subheader("1. Filiación")
    ciudades = [
        "--- Seleccione ---",
        "Bucaramanga (Santander)", "Floridablanca (Santander)", "San Gil (Santander)", "Socorro (Santander)", "Soatá (Boyacá)", 
        "Yopal (Casanare)", "Arauca (Arauca)", "Cúcuta (N. Santander)", 
        "Bogotá D.C.", "Medellín", "Cali", "Barranquilla", "Otra"
    ]
    ciudad = st.selectbox("Ciudad", ciudades)
    if any(x in ciudad for x in ["Santander", "Boyacá", "Casanare", "Arauca"]):
        st.warning("⚠️ **Alerta:** Zona endémica Chagas.")
        
    col1, col2 = st.columns(2)
    edad = col1.number_input("Edad", 18, 120, 65)
    sexo = col2.selectbox("Sexo", ["M", "F", "Otro"])

    # 2. Síntomas
    st.subheader("2. Síntomas")
    sintomas = st.multiselect("Seleccione:", ["Disnea esfuerzo", "Disnea reposo", "Ortopnea", "Bendopnea", "DPN", "Fatiga", "Angina"])

    # 3. Signos Vitales
    st.subheader("3. Signos Vitales")
    ritmo = st.selectbox("Ritmo Monitor", ["Sinusal", "Fibrilación Auricular", "Aleteo", "TV", "Otro"])
    with st.expander("📸 Ver Ritmos"): st.image(recursos["ritmos"], use_container_width=True)

    col_p1, col_p2 = st.columns(2)
    pas = col_p1.number_input("PAS (mmHg)", value=110)
    pad = col_p2.number_input("PAD (mmHg)", value=70)
    fc = col_p1.number_input("FC", value=85)
    sato2 = col_p2.number_input("SatO2 (%)", value=92) # Input SatO2
    
    # 4. Examen Físico
    st.subheader("4. Examen Físico")
    
    # Ruidos
    st.markdown("🔹 **Ruidos Cardíacos**")
    opciones_ruidos = ["R1-R2 Normales", "S3 (Galope Ventricular)"]
    if ritmo == "Sinusal":
        opciones_ruidos.append("S4 (Galope Atrial)")
        opciones_ruidos.append("S3 + S4 (Suma)")
    ruidos_agregados = st.selectbox("Ruidos Agregados:", opciones_ruidos)
    
    if "S3" in ruidos_agregados or "S4" in ruidos_agregados:
        with st.expander("🎧 Escuchar"):
            if "S3" in ruidos_agregados: st.audio(recursos["audio_s3"])
            if "S4" in ruidos_agregados: st.audio(recursos["audio_s4"])

    iy = st.selectbox("Ingurgitación Yugular", ["Ausente", "Grado I (45°)", "Grado II (45°)", "Grado III (90°)"])
    rhy = st.checkbox("Reflujo Hepato-yugular")
    
    # Soplos
    st.markdown("🔹 **Soplos**")
    tiene_soplo = st.checkbox("¿Tiene Soplo?")
    foco, ciclo, patron = "Aórtico", "Sistólico", "Holosistólico"
    if tiene_soplo:
        foco = st.selectbox("Foco", ["Aórtico", "Mitral", "Tricúspideo", "Pulmonar"])
        ciclo = st.selectbox("Ciclo", ["Sistólico", "Diastólico"])
        patron = st.selectbox("Patrón", ["Diamante", "Holosistólico", "Decrescendo", "Click+Chasquido"])
        with st.expander("🎧 Escuchar Ejemplo"):
            if "Aórtico" in foco and "Sistólico" in ciclo: st.audio(recursos["audio_estenosis_aortica"])
            elif "Mitral" in foco and "Sistólico" in ciclo: st.audio(recursos["audio_insuf_mitral"])

    # Pulmones
    st.markdown("🔹 **Pulmones**")
    pulmones = st.selectbox("Auscultación", ["Limpios", "Estertores bases", "Estertores >1/2", "Sibilancias"])
    with st.expander("🎧 Escuchar"):
        if "Estertores" in pulmones: st.audio(recursos["audio_estertores"])
        elif "Sibilancias" in pulmones: st.audio(recursos["audio_sibilancias"])
        else: st.audio(recursos["audio_normal_lung"])
    
    # Edema
    st.markdown("🔹 **Extremidades**")
    edema_ex = st.selectbox("Edema MsIs", ["Ausente", "Pies", "Rodillas", "Muslos"])
    godet = st.selectbox("Fóvea (Godet)", ["Sin fóvea", "Grado I (+)", "Grado II (++)", "Grado III (+++)", "Grado IV (++++)"])
    
    pulsos = st.selectbox("Pulsos", ["Normales", "Disminuidos", "Filiformes"])
    temp = st.selectbox("Temperatura", ["Caliente", "Fría", "Muy Fría"])
    llenado = st.number_input("Llenado Capilar (seg)", 2)
    
    st.divider()
    st.markdown("**Javier Armando Rodriguez Prada, MD, MSc**")
    st.caption("Enero 19, 2026 | javimeduis@gmail.com")

# --- CÁLCULOS ---
pam = pad + (pas - pad)/3
pp = pas - pad
ppp = (pp / pas) * 100 if pas > 0 else 0

# --- LÓGICA STEVENSON ---
score_congest = 0
if "Ortopnea" in sintomas: score_congest += 3
if "reposo" in str(sintomas): score_congest += 4
if "Grado II" in iy or "Grado III" in iy: score_congest += 4
if "Estertores" in pulmones: score_congest += 3
if edema_ex != "Ausente": score_congest += 2
if rhy: score_congest += 2
if "S3" in ruidos_agregados: score_congest += 4

pcp_sim = 12 + score_congest
if pcp_sim > 38: pcp_sim = 38 

score_perf = 2.8
if ppp < 25: score_perf -= 0.6
if temp != "Caliente": score_perf -= 0.6
if llenado > 3: score_perf -= 0.4
if pulsos == "Filiformes": score_perf -= 0.5
if pas < 90: score_perf -= 0.4

ic_sim = max(1.0, score_perf) 

if pcp_sim > 18 and ic_sim > 2.2:
    cuadrante = "B: Húmedo y Caliente"
elif pcp_sim > 18 and ic_sim <= 2.2:
    cuadrante = "C: Húmedo y Frío"
elif pcp_sim <= 18 and ic_sim <= 2.2:
    cuadrante = "L: Seco y Frío"
else:
    cuadrante = "A: Seco y Caliente"

# --- INTERFAZ PRINCIPAL ---

st.markdown("### 📊 Tablero Hemodinámico")

# ALERTA DE HIPOXEMIA (NUEVO)
if sato2 < 90:
    st.error(f"🚨 **ALERTA HIPOXEMIA (SatO2 {sato2}%):** Iniciar Oxígeno suplementario inmediato. Meta SatO2 > 90% (ESC/AHA). Considerar gases arteriales.")

col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
col_m1.metric("PAM", f"{pam:.0f} mmHg", help="Meta > 65 mmHg.")
col_m2.metric("P. Pulso", f"{pp} mmHg", help="Rigidez/Volumen sistólico.")
col_m3.metric("PPP", f"{ppp:.1f} %", delta="- Hipoperfusión" if ppp < 25 else "OK", delta_color="inverse", help="PPP < 25% predice IC < 2.2.")
col_m4.metric("Stevenson", cuadrante)

if tiene_soplo:
    st.info(f"🩺 **Soplo:** {inferir_valvulopatia(foco, ciclo, patron, True)}")

tabs = st.tabs(["📉 Cuadrante Stevenson", "💊 Simulación Terapéutica", "🏠 Egreso (HFrEF)", "⚖️ FEVI Preservada"])

# TAB 1: STEVENSON
with tabs[0]:
    with st.expander("ℹ️ ¿Cómo interpretar los Ejes?"):
        st.markdown("* **Eje X (Congestión):** Estado de volumen (Ortopnea, IY, S3). Corte 18 mmHg.\n* **Eje Y (Perfusión):** Gasto cardíaco (Frialdad, PPP). Corte 2.2 L/min/m².")
        
    col_g1, col_g2 = st.columns([3, 1])
    with col_g1:
        fig = go.Figure()
        fig.add_shape(type="rect", x0=0, y0=2.2, x1=18, y1=5, fillcolor="rgba(144, 238, 144, 0.2)", line_width=0) 
        fig.add_shape(type="rect", x0=18, y0=2.2, x1=40, y1=5, fillcolor="rgba(255, 218, 185, 0.4)", line_width=0)
        fig.add_shape(type="rect", x0=0, y0=0, x1=18, y1=2.2, fillcolor="rgba(173, 216, 230, 0.3)", line_width=0)
        fig.add_shape(type="rect", x0=18, y0=0, x1=40, y1=2.2, fillcolor="rgba(255, 182, 193, 0.4)", line_width=0)
        
        fig.add_vline(x=18, line_dash="solid", line_color="gray")
        fig.add_hline(y=2.2, line_dash="solid", line_color="gray")
        
        fig.add_annotation(x=9, y=4.5, text="<b>A: SECO / CALIENTE</b>", showarrow=False, font=dict(size=16, color="green"))
        fig.add_annotation(x=29, y=4.5, text="<b>B: HÚMEDO / CALIENTE</b>", showarrow=False, font=dict(size=16, color="orange"))
        fig.add_annotation(x=9, y=0.5, text="<b>L: SECO / FRÍO</b>", showarrow=False, font=dict(size=16, color="blue"))
        fig.add_annotation(x=29, y=0.5, text="<b>C: HÚMEDO / FRÍO</b>", showarrow=False, font=dict(size=16, color="red"))

        fig.add_trace(go.Scatter(x=[pcp_sim], y=[ic_sim], mode='markers+text', marker=dict(size=30, color='black', line=dict(width=2, color='white')), text=["<b>PACIENTE</b>"], textposition="top center"))
        
        fig.update_layout(title="Cuadrante de Forrester/Stevenson", xaxis_title="<b>PCP Estimada</b> mmHg", yaxis_title="<b>Índice Cardíaco Estimado</b> L/min/m²", xaxis=dict(range=[0, 40]), yaxis=dict(range=[0, 5]), height=600)
        st.plotly_chart(fig, use_container_width=True)

# TAB 2: SIMULACIÓN
with tabs[1]:
    st.markdown("### 🧪 Taller de Farmacología Aguda")
    st.info("Seleccione intervención para ver vector y **seguridad**.")
    
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    dx, dy = 0, 0
    selected_med = None
    
    with col_t1:
        if st.checkbox("Furosemida IV"): dx -= 8; dy += 0.1; selected_med = "diureticos"
    with col_t2:
        if st.checkbox("Vasodilatador"): dx -= 6; dy += 0.5; selected_med = "vasodilatadores"
    with col_t3:
        if st.checkbox("Inotrópico"): dy += 1.2; dx -= 2; selected_med = "inotropicos"
    with col_t4:
        if st.checkbox("Vasopresor"): dy += 0.2; dx += 4; selected_med = "vasopresores"

    if selected_med:
        info = meds_agudos[selected_med]
        st.markdown("---")
        c_i1, c_i2 = st.columns(2)
        with c_i1: st.markdown(f"#### 💊 {info['nombre']}"); st.write(f"**Dosis:** {info['dosis']}")
        with c_i2: st.warning(f"**Adversos:** {info['adverso']}"); st.error(f"**Monitoreo:**\n{info['monitor']}")
        st.markdown("---")

    new_pcp, new_ic = pcp_sim + dx, ic_sim + dy
    fig_sim = go.Figure(fig)
    fig_sim.update_layout(height=400, title="Proyección Post-Intervención")
    fig_sim.add_annotation(x=new_pcp, y=new_ic, ax=pcp_sim, ay=ic_sim, xref="x", yref="y", axref="x", ayref="y", arrowwidth=4, arrowhead=3, arrowcolor="purple")
    fig_sim.add_trace(go.Scatter(x=[new_pcp], y=[new_ic], mode='markers', marker=dict(size=20, color='purple', symbol='x'), name="Post-Rx"))
    st.plotly_chart(fig_sim, use_container_width=True)

# TAB 3: EGRESO (CON ADYUVANTES COMPLETOS)
with tabs[2]:
    st.header("🏠 Plan de Egreso: HFrEF (FEVI ≤ 40%)")
    
    st.subheader("1. Los 4 Pilares (GDMT)")
    gdmt_data = [
        {"Grupo": "Beta-Bloqueador", "Fármaco": "Succinato de Metoprolol", "Dosis Inicio": "12.5 - 25 mg c/24h", "Dosis Meta": "200 mg c/24h"},
        {"Grupo": "Beta-Bloqueador", "Fármaco": "Carvedilol", "Dosis Inicio": "3.125 mg c/12h", "Dosis Meta": "25 - 50 mg c/12h"},
        {"Grupo": "Beta-Bloqueador", "Fármaco": "Bisoprolol", "Dosis Inicio": "1.25 mg c/24h", "Dosis Meta": "10 mg c/24h"},
        {"Grupo": "ARNI", "Fármaco": "Sacubitrilo/Valsartán", "Dosis Inicio": "24/26 mg c/12h", "Dosis Meta": "97/103 mg c/12h"},
        {"Grupo": "ARM", "Fármaco": "Espironolactona", "Dosis Inicio": "12.5 - 25 mg c/24h", "Dosis Meta": "50 mg c/24h"},
        {"Grupo": "iSGLT2", "Fármaco": "Dapa / Empagliflozina", "Dosis Inicio": "10 mg c/24h", "Dosis Meta": "10 mg c/24h"},
    ]
    st.dataframe(pd.DataFrame(gdmt_data), use_container_width=True)
    
    st.subheader("2. Adyuvantes y Prevención (Clase I)")
    c_ady1, c_ady2 = st.columns(2)
    
    with c_ady1:
        st.info("💉 **Déficit de Hierro**")
        st.markdown("""
        * **Indicación:** Ferritina < 100 ng/mL **O** Ferritina 100-299 con IST < 20%.
        * **Tratamiento:** Hierro Carboximaltosa IV (Eg. 1000 mg). 
        * *Nota: Hierro oral NO es efectivo en FC.*
        """)
        
        st.success("🫀 **Rehabilitación Cardíaca**")
        st.markdown("Recomendación **Clase I-A**. Iniciar programa multidisciplinario al egreso para mejorar capacidad funcional y calidad de vida.")

    with c_ady2:
        st.warning("🛡️ **Vacunación**")
        st.markdown("""
        * **Influenza:** Anual.
        * **Neumococo:** Esquema secuencial (PCV13 / PPSV23).
        * **COVID-19:** Según esquema vigente.
        """)
        
        st.error("📉 **Autocuidado**")
        st.markdown("Restricción hídrica (1.5-2L) solo en hiponatremia o congestión refractaria. Pesaje diario.")

# TAB 4: FEVI PRESERVADA
with tabs[3]:
    st.header("⚖️ FEVI Preservada (HFpEF)")
    st.success("**iSGLT2 (Dapa/Empa):** Clase I, Nivel A. 10 mg/día.")
    st.markdown("* **Congestión:** Diuréticos asa. * **HTA:** ARNI/MRA. * **FA:** Anticoagulación.")

# --- PIE DE PÁGINA ---
st.divider()
st.subheader("📚 Referencias Bibliográficas")
st.markdown("""
1. McDonagh TA, et al. **2021 ESC Guidelines**. Eur Heart J. 2021.
2. Heidenreich PA, et al. **2022 AHA/ACC/HFSA Guideline**. Circulation. 2022.
3. Ponikowski P, et al. **Ferric carboxymaltose for iron deficiency at discharge after acute heart failure (AFFIRM-AHF)**. Lancet. 2020.
4. Stevenson LW. **Design of therapy for advanced heart failure**. Eur J Heart Fail. 2005.
""")

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: grey;">
    Desarrollado por: <b>Javier Armando Rodriguez Prada, MD, MSc</b><br>
    Contacto: javimeduis@gmail.com | Enero 19 de 2026<br>
    <i>Impulsado por Gemini 3.0</i>
</div>
""", unsafe_allow_html=True)

