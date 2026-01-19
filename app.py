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
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE RECURSOS (IMÁGENES Y AUDIO) ---
recursos = {
    # IMÁGENES
    "ritmos": "https://upload.wikimedia.org/wikipedia/commons/e/e6/Atrial_fibrillation_ECG.png", 
    "iy": "https://upload.wikimedia.org/wikipedia/commons/0/05/JVP.jpg",
    "godet": "https://upload.wikimedia.org/wikipedia/commons/0/00/Combination_of_pitting_edema_and_stasis_dermatitis.jpg",
    
    # AUDIOS (Soplos y Ruidos)
    "audio_s3": "https://upload.wikimedia.org/wikipedia/commons/7/76/S3_heart_sound.ogg",
    "audio_s4": "https://upload.wikimedia.org/wikipedia/commons/8/87/S4_heart_sound.ogg",
    "audio_estenosis_aortica": "https://upload.wikimedia.org/wikipedia/commons/9/99/Aortic_stenosis.ogg",
    "audio_insuf_mitral": "https://upload.wikimedia.org/wikipedia/commons/5/5c/Mitral_regurgitation.ogg",
    "audio_estertores": "https://upload.wikimedia.org/wikipedia/commons/3/33/Crackles_pneumonia.ogg",
    "audio_sibilancias": "https://upload.wikimedia.org/wikipedia/commons/e/e6/Wheezing_lung_sound.ogg",
    "audio_normal_lung": "https://upload.wikimedia.org/wikipedia/commons/a/a2/Vesicular_breath_sounds.ogg"
}

# --- FUNCIONES AUXILIARES ---
def inferir_valvulopatia(foco, ciclo, patron, localizacion_soplo):
    dx_sugerido = "Soplo no específico"
    if not localizacion_soplo: return "Sin soplos reportados."

    if foco == "Aórtico":
        if ciclo == "Sistólico" and "diamante" in patron:
            dx_sugerido = "Posible Estenosis Aórtica (Busca: Irradiación a carótidas, pulso parvus)"
        elif ciclo == "Diastólico":
            dx_sugerido = "Posible Insuficiencia Aórtica (Busca: Soplo aspirativo, presión de pulso amplia)"
    elif foco == "Mitral":
        if ciclo == "Sistólico" and "Holosistólico" in patron:
            dx_sugerido = "Posible Insuficiencia Mitral (Busca: Irradiación a axila)"
        elif ciclo == "Diastólico":
            dx_sugerido = "Posible Estenosis Mitral (Busca: Chasquido de apertura, ritmo de duroziez)"
    return dx_sugerido

# --- DATA: FARMACOLOGÍA AGUDA ---
meds_agudos = {
    "diureticos": {
        "dosis": "Furosemida: Bolo 20-40mg IV (o 1-2.5x dosis oral previa). Infusión si hay resistencia.",
        "renal": "TFG < 30 ml/min: Requiere dosis más altas (curva dosis-respuesta a la derecha).",
        "adverso": "Hipokalemia, Hipomagnesemia, Alcalosis metabólica, Falla renal prerenal."
    },
    "vasodilatadores": {
        "dosis": "Nitroglicerina: 10-200 mcg/min. \nNitroprusiato: 0.3-5 mcg/kg/min.",
        "renal": "Nitroprusiato: Riesgo toxicidad tiocianato en ERC.",
        "adverso": "Cefalea, Hipotensión, Taquicardia refleja."
    },
    "inotropicos": {
        "dosis": "Dobutamina: 2-20 mcg/kg/min. \nMilrinone: 0.375-0.75 mcg/kg/min. \nLevosimendán: 0.1 mcg/kg/min.",
        "renal": "Milrinone: Ajustar al 50-70% en falla renal.",
        "adverso": "Arritmias, Isquemia, Hipotensión (Milrinone/Levo)."
    },
    "vasopresores": {
        "dosis": "Norepinefrina: 0.05 - 0.5 mcg/kg/min. Meta PAM > 65 mmHg.",
        "renal": "Vasoconstricción excesiva puede comprometer perfusión renal.",
        "adverso": "Isquemia distal, Arritmias."
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
        st.caption("⚠️ **Alerta:** Zona endémica Chagas.")
        
    col1, col2 = st.columns(2)
    edad = col1.number_input("Edad", 18, 120, 65)
    sexo = col2.selectbox("Sexo", ["M", "F", "Otro"])

    # 2. Síntomas
    st.subheader("2. Síntomas")
    sintomas = st.multiselect("Seleccione:", ["Disnea esfuerzo", "Disnea reposo", "Ortopnea", "Bendopnea", "DPN", "Fatiga", "Angina"])

    # 3. Signos Vitales y Ritmo
    st.subheader("3. Signos Vitales")
    # Lógica de Ritmo para S4
    ritmo = st.selectbox("Ritmo Monitor", ["Sinusal", "Fibrilación Auricular", "Aleteo", "TV", "Otro"])
    
    with st.expander("📸 Ver Patrones de Ritmo"):
        st.image(recursos["ritmos"], caption="Ej: Fibrilación Auricular", use_container_width=True)

    col_p1, col_p2 = st.columns(2)
    pas = col_p1.number_input("PAS (mmHg)", value=110)
    pad = col_p2.number_input("PAD (mmHg)", value=70)
    fc = col_p1.number_input("FC", value=85)
    sato2 = col_p2.number_input("SatO2", value=92)
    
    # 4. Examen Físico (RUIDOS ACTUALIZADOS)
    st.subheader("4. Examen Físico")
    
    st.markdown("**Ruidos Cardíacos (Galopes)**")
    # Filtro Dinámico: S4 no disponible si es FA/Aleteo
    opciones_ruidos = ["R1-R2 Normales", "S3 (Galope Ventricular)"]
    if ritmo == "Sinusal":
        opciones_ruidos.append("S4 (Galope Atrial)") # Solo si hay patada auricular
        opciones_ruidos.append("S3 + S4 (Galope de Suma)")
    
    ruidos_agregados = st.selectbox("Ruidos Agregados:", opciones_ruidos)
    
    # Reproductor de Audio S3/S4
    if "S3" in ruidos_agregados or "S4" in ruidos_agregados:
        with st.expander("🎧 Escuchar Galope"):
            if "S3" in ruidos_agregados:
                st.audio(recursos["audio_s3"], format="audio/ogg")
                st.caption("S3: Llenado rápido (Sobrecarga de Volumen)")
            if "S4" in ruidos_agregados:
                st.audio(recursos["audio_s4"], format="audio/ogg")
                st.caption("S4: Contracción Auricular (Rigidez Ventricular)")

    iy = st.selectbox("Ingurgitación Yugular", ["Ausente", "Grado I (45°)", "Grado II (45°)", "Grado III (90°)"])
    with st.expander("📸 Ver Ingurgitación"):
        st.image(recursos["iy"], caption="Estimación PVC", use_container_width=True)

    rhy = st.checkbox("Reflujo Hepato-yugular")
    
    # Soplos
    st.markdown("**Soplos**")
    tiene_soplo = st.checkbox("¿Tiene Soplo?")
    foco, ciclo, patron = "Aórtico", "Sistólico", "Holosistólico"
    if tiene_soplo:
        foco = st.selectbox("Foco", ["Aórtico", "Mitral", "Tricúspideo", "Pulmonar"])
        ciclo = st.selectbox("Ciclo", ["Sistólico", "Diastólico"])
        patron = st.selectbox("Patrón", ["Diamante", "Holosistólico", "Decrescendo", "Click+Chasquido"])
        
        with st.expander("🎧 Escuchar Ejemplo"):
            if "Aórtico" in foco and "Sistólico" in ciclo:
                st.audio(recursos["audio_estenosis_aortica"], format="audio/ogg")
            elif "Mitral" in foco and "Sistólico" in ciclo:
                st.audio(recursos["audio_insuf_mitral"], format="audio/ogg")

    # Pulmones
    st.markdown("**Pulmones**")
    pulmones = st.selectbox("Auscultación", ["Limpios", "Estertores bases", "Estertores >1/2", "Sibilancias"])
    with st.expander("🎧 Escuchar Pulmón"):
        if "Estertores" in pulmones:
            st.audio(recursos["audio_estertores"], format="audio/ogg")
        elif "Sibilancias" in pulmones:
            st.audio(recursos["audio_sibilancias"], format="audio/ogg")
        else:
            st.audio(recursos["audio_normal_lung"], format="audio/ogg")
    
    # Edema
    st.markdown("**Extremidades**")
    edema_ex = st.selectbox("Edema MsIs", ["Ausente", "Pies", "Rodillas", "Muslos"])
    godet = st.selectbox("Fóvea (Godet)", ["Sin fóvea", "Grado I (+)", "Grado II (++)", "Grado III (+++)", "Grado IV (++++)"])
    with st.expander("📸 Ver Grados Edema"):
        st.image(recursos["godet"], caption="Fóvea persistente", use_container_width=True)

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

# --- LÓGICA STEVENSON (CON S3) ---
score_congest = 0
if "Ortopnea" in sintomas: score_congest += 3
if "reposo" in str(sintomas): score_congest += 4
if "Grado II" in iy or "Grado III" in iy: score_congest += 4
if "Estertores" in pulmones: score_congest += 3
if edema_ex != "Ausente": score_congest += 2
if rhy: score_congest += 2
# S3 suma puntos de congestión (falla aguda)
if "S3" in ruidos_agregados: score_congest += 4 

pcp_sim = 12 + score_congest
if pcp_sim > 35: pcp_sim = 35 # Eje X

score_perf = 2.8
if ppp < 25: score_perf -= 0.6
if temp != "Caliente": score_perf -= 0.6
if llenado > 3: score_perf -= 0.4
if pulsos == "Filiformes": score_perf -= 0.5
if pas < 90: score_perf -= 0.4

ic_sim = max(1.0, score_perf) # Eje Y

if pcp_sim > 18 and ic_sim > 2.2:
    cuadrante = "B: Húmedo y Caliente"
elif pcp_sim > 18 and ic_sim <= 2.2:
    cuadrante = "C: Húmedo y Frío"
elif pcp_sim <= 18 and ic_sim <= 2.2:
    cuadrante = "L: Seco y Frío"
else:
    cuadrante = "A: Seco y Caliente"

# --- INTERFAZ PRINCIPAL ---

col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
col_m1.metric("PAM", f"{pam:.0f}")
col_m2.metric("P. Pulso", f"{pp}")
col_m3.metric("PPP", f"{ppp:.1f} %", delta="- Hipoperfusión" if ppp < 25 else "OK", delta_color="inverse")
col_m4.metric("Stevenson", cuadrante)
if tiene_soplo:
    col_m5.info(inferir_valvulopatia(foco, ciclo, patron, True))

tabs = st.tabs(["📉 Hemodinamia", "💊 Simulación Aguda", "🏠 Egreso (HFrEF)", "⚖️ FEVI Preservada"])

# TAB 1: STEVENSON
with tabs[0]:
    st.warning("⚠️ **Nota Clínica:** La clasificación de Stevenson está validada para **Falla Cardíaca Aguda Descompensada** (HFrEF). En FEVI preservada, los umbrales de perfusión pueden variar.")
    
    col_g1, col_g2 = st.columns([2, 1])
    with col_g1:
        fig = go.Figure()
        # Cuadrantes Forrester (X=PCP, Y=IC)
        fig.add_shape(type="rect", x0=0, y0=2.2, x1=18, y1=5, fillcolor="rgba(0, 255, 0, 0.1)", line_width=0) # A
        fig.add_shape(type="rect", x0=18, y0=2.2, x1=40, y1=5, fillcolor="rgba(255, 165, 0, 0.1)", line_width=0) # B
        fig.add_shape(type="rect", x0=0, y0=0, x1=18, y1=2.2, fillcolor="rgba(0, 0, 255, 0.1)", line_width=0) # L
        fig.add_shape(type="rect", x0=18, y0=0, x1=40, y1=2.2, fillcolor="rgba(255, 0, 0, 0.1)", line_width=0) # C
        
        fig.add_vline(x=18, line_dash="dash", line_color="gray")
        fig.add_hline(y=2.2, line_dash="dash", line_color="gray")
        
        fig.add_annotation(x=9, y=4, text="<b>A: Seco/Caliente</b>", showarrow=False, font=dict(color="green"))
        fig.add_annotation(x=29, y=4, text="<b>B: Húmedo/Caliente</b>", showarrow=False, font=dict(color="orange"))
        fig.add_annotation(x=9, y=1, text="<b>L: Seco/Frío</b>", showarrow=False, font=dict(color="blue"))
        fig.add_annotation(x=29, y=1, text="<b>C: Húmedo/Frío</b>", showarrow=False, font=dict(color="red"))

        fig.add_trace(go.Scatter(x=[pcp_sim], y=[ic_sim], mode='markers+text', marker=dict(size=25, color='black'), text=["PACIENTE"], textposition="top center"))
        
        fig.update_layout(title="Cuadrante de Stevenson (X=PCP, Y=IC)", xaxis_title="PCP (Congestión)", yaxis_title="IC (Perfusión)", height=450)
        st.plotly_chart(fig, use_container_width=True)

# TAB 2: SIMULACIÓN
with tabs[1]:
    st.markdown("### 🧪 Laboratorio de Intervención")
    c1, c2, c3, c4 = st.columns(4)
    dx, dy = 0, 0
    
    with c1:
        if st.checkbox("Furosemida"): 
            dx -= 8; dy += 0.1
            st.caption(meds_agudos["diureticos"]["dosis"])
    with c2:
        if st.checkbox("Vasodilatador"): 
            dx -= 6; dy += 0.5
            st.caption(meds_agudos["vasodilatadores"]["dosis"])
    with c3:
        if st.checkbox("Inotrópico"): 
            dy += 1.2; dx -= 2
            st.caption(meds_agudos["inotropicos"]["dosis"])
    with c4:
        if st.checkbox("Vasopresor"): 
            dy += 0.2; dx += 4
            st.caption(meds_agudos["vasopresores"]["dosis"])

    new_pcp, new_ic = pcp_sim + dx, ic_sim + dy
    fig_sim = go.Figure(fig)
    fig_sim.add_annotation(x=new_pcp, y=new_ic, ax=pcp_sim, ay=ic_sim, xref="x", yref="y", axref="x", ayref="y", arrowwidth=3, arrowhead=2, arrowcolor="black")
    fig_sim.add_trace(go.Scatter(x=[new_pcp], y=[new_ic], mode='markers', marker=dict(size=15, color='purple', symbol='x')))
    st.plotly_chart(fig_sim, use_container_width=True)

# TAB 3: EGRESO (HFrEF)
with tabs[2]:
    st.header("🏠 Plan de Egreso: HFrEF (FEVI ≤ 40%)")
    st.markdown("Esquema de Titulación GDMT.")
    
    gdmt_data = [
        {"Grupo": "Beta-Bloqueador", "Fármaco": "Succinato de Metoprolol", "Dosis Inicio": "12.5 - 25 mg c/24h", "Dosis Meta": "200 mg c/24h"},
        {"Grupo": "Beta-Bloqueador", "Fármaco": "Carvedilol", "Dosis Inicio": "3.125 mg c/12h", "Dosis Meta": "25 mg c/12h"},
        {"Grupo": "Beta-Bloqueador", "Fármaco": "Bisoprolol", "Dosis Inicio": "1.25 mg c/24h", "Dosis Meta": "10 mg c/24h"},
        {"Grupo": "ARNI (Preferido)", "Fármaco": "Sacubitrilo/Valsartán", "Dosis Inicio": "24/26 mg c/12h", "Dosis Meta": "97/103 mg c/12h"},
        {"Grupo": "IECA", "Fármaco": "Enalapril", "Dosis Inicio": "2.5 mg c/12h", "Dosis Meta": "10 - 20 mg c/12h"},
        {"Grupo": "ARM", "Fármaco": "Espironolactona", "Dosis Inicio": "12.5 - 25 mg c/24h", "Dosis Meta": "50 mg c/24h"},
        {"Grupo": "iSGLT2", "Fármaco": "Dapagliflozina / Empagliflozina", "Dosis Inicio": "10 mg c/24h", "Dosis Meta": "10 mg c/24h"},
    ]
    df_gdmt = pd.DataFrame(gdmt_data)
    st.dataframe(df_gdmt, use_container_width=True)
    st.info("Nota: Suspender IECA 36h antes de ARNI. Monitorizar K+.")

# TAB 4: FEVI PRESERVADA
with tabs[3]:
    st.header("⚖️ FEVI Preservada (HFpEF) y Levemente Reducida")
    st.success("**iSGLT2 (Dapa/Empa):** Clase I, Nivel A. 10 mg/día.")
    st.markdown("""
    * **Congestión:** Diuréticos de asa a dosis mínima.
    * **HTA:** Preferir ARNI/MRA.
    * **FA:** Anticoagulación + Control Ritmo/Frecuencia.
    """)

# --- PIE DE PÁGINA ---
st.divider()
st.subheader("📚 Referencias Bibliográficas")
st.markdown("""
1. McDonagh TA, Metra M, Adamo M, et al. **2021 ESC Guidelines for the diagnosis and treatment of acute and chronic heart failure**. Eur Heart J. 2021 Sep 21;42(36):3599-3726.
2. Heidenreich PA, Bozkurt B, Aguilar D, et al. **2022 AHA/ACC/HFSA Guideline for the Management of Heart Failure**: A Report of the American College of Cardiology/American Heart Association Joint Committee on Clinical Practice Guidelines. Circulation. 2022 May 3;145(18):e895-e1032.
3. Solomon SD, McMurray JJV, Claggett B, et al. **Dapagliflozin in Heart Failure with Mildly Reduced or Preserved Ejection Fraction (DELIVER)**. N Engl J Med. 2022 Sep 22;387(12):1089-1098.
4. Anker SD, Butler J, Filippatos G, et al. **Empagliflozin in Heart Failure with a Preserved Ejection Fraction (EMPEROR-Preserved)**. N Engl J Med. 2021 Oct 14;385(16):1451-1461.
5. Stevenson LW. **Design of therapy for advanced heart failure**. Eur J Heart Fail. 2005 Mar;7(3):323-31.
""")

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: grey;">
    Desarrollado por: <b>Javier Armando Rodriguez Prada, MD, MSc</b><br>
    Contacto: javimeduis@gmail.com | Enero 19 de 2026<br>
    <i>Impulsado por Gemini 3.0</i>
</div>
""", unsafe_allow_html=True)
