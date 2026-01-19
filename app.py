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

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 5px; }
    .stTabs [aria-selected="true"] { background-color: #ff4b4b; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES AUXILIARES ---
def inferir_valvulopatia(foco, ciclo, patron, localizacion_soplo):
    """Infiere patología valvular basada en semiología"""
    dx_sugerido = "Soplo no específico"
    if not localizacion_soplo: return "Sin soplos reportados."

    if foco == "Aórtico":
        if ciclo == "Sistólico" and "diamante" in patron:
            dx_sugerido = "Posible Estenosis Aórtica (Evaluar: Irradiación a carótidas, pulso parvus)"
        elif ciclo == "Diastólico":
            dx_sugerido = "Posible Insuficiencia Aórtica (Evaluar: Soplo aspirativo, presión de pulso amplia)"
    elif foco == "Mitral":
        if ciclo == "Sistólico" and "Holosistólico" in patron:
            dx_sugerido = "Posible Insuficiencia Mitral (Evaluar: Irradiación a axila)"
        elif ciclo == "Diastólico":
            dx_sugerido = "Posible Estenosis Mitral (Evaluar: Chasquido de apertura, ritmo de duroziez)"
    elif foco == "Tricúspideo":
        if ciclo == "Sistólico":
            dx_sugerido = "Posible Insuficiencia Tricuspídea (Evaluar: Signo de Rivero-Carvallo, onda V en yugular)"
    elif foco == "Pulmonar":
        dx_sugerido = "Posible patología pulmonar o HTP"
            
    return dx_sugerido

# --- BASE DE DATOS DE MEDICAMENTOS ---
meds_agudos = {
    "diureticos": {
        "dosis": "Furosemida: Bolo 20-40mg IV (o 1-2.5x dosis oral previa). Infusión continua si hay resistencia diurética.",
        "renal": "En TFG < 30 ml/min: Requerimiento de dosis más altas (curva dosis-respuesta desviada).",
        "adverso": "Hipokalemia, Hipomagnesemia, Alcalosis metabólica, Falla renal prerenal, Ototoxicidad."
    },
    "vasodilatadores": {
        "dosis": "Nitroglicerina: 10-200 mcg/min. \nNitroprusiato: 0.3-5 mcg/kg/min (Solo monitorización invasiva idealmente).",
        "renal": "Nitroprusiato: Riesgo toxicidad tiocianato en ERC.",
        "adverso": "Cefalea, Hipotensión, Taquicardia refleja, Fenómeno de robo coronario."
    },
    "inotropicos": {
        "dosis": "Dobutamina: 2-20 mcg/kg/min. \nMilrinone: 0.375-0.75 mcg/kg/min. \nLevosimendán: 0.1 mcg/kg/min (sin bolo usualmente).",
        "renal": "Milrinone: Ajustar al 50-70% en falla renal. Levosimendán: No requiere ajuste mayor.",
        "adverso": "Arritmias ventriculares, Aumento consumo O2 (Isquemia), Hipotensión (Milrinone/Levo)."
    },
    "vasopresores": {
        "dosis": "Norepinefrina: 0.05 - 0.5 mcg/kg/min. Meta PAM > 65 mmHg.",
        "renal": "La vasoconstricción excesiva puede comprometer la perfusión renal, pero la hipotensión es peor.",
        "adverso": "Isquemia distal, Arritmias, Necrosis por extravasación."
    }
}

# --- ENCABEZADO ---
st.title("🫀 HemoSim: Docencia en Cardiología")
st.markdown("**Simulador de Hemodinamia en Falla Cardíaca y Guía Terapéutica Interactiva**")
st.caption("Basado en Guías ESC 2021 y AHA/ACC/HFSA 2022")

# --- BARRA LATERAL (INPUTS) ---
with st.sidebar:
    st.header("📝 Historia Clínica")
    
    # 1. Demográficos
    st.subheader("1. Filiación")
    ciudades = [
        "--- Seleccione ---",
        "Bucaramanga (Santander)", "Floridablanca (Santander)", "San Gil (Santander)", "Socorro (Santander)", "Soatá (Boyacá)", # Zonas Chagas
        "Yopal (Casanare)", "Arauca (Arauca)", "Cúcuta (N. Santander)", # Zonas Chagas
        "Bogotá D.C.", "Medellín", "Cali", "Barranquilla", "Cartagena", "Pereira", "Manizales", "Neiva", "Otra"
    ]
    ciudad = st.selectbox("Ciudad / Municipio", ciudades)
    if "Santander" in ciudad or "Boyacá" in ciudad or "Casanare" in ciudad or "Arauca" in ciudad:
        st.caption("⚠️ **Alerta Epidemiológica:** Zona endémica para Enf. de Chagas.")
        
    procedencia = st.radio("Procedencia", ["Urbana", "Rural"], horizontal=True)
    col1, col2 = st.columns(2)
    edad = col1.number_input("Edad (años)", 18, 120, 65)
    sexo = col2.selectbox("Sexo", ["Masculino", "Femenino", "Otro"])

    # 2. Síntomas
    st.subheader("2. Síntomas")
    sintomas = st.multiselect("Seleccione:", [
        "Disnea grandes esf.", "Disnea mod. esf.", "Disnea peq. esf.", "Disnea reposo",
        "Ortopnea", "Bendopnea (al agacharse)", "Disnea Paroxística Nocturna",
        "Fatiga/Asténia", "Angina"
    ])
    dias_evol = st.number_input("Días evolución", 1, 365, 5)

    # 3. Antecedentes
    st.subheader("3. Antecedentes")
    antecedentes = st.multiselect("Patológicos:", [
        "HTA", "Diabetes T2", "Dislipidemia", "Obesidad", "Enf. Coronaria", 
        "Fibrilación Auricular", "ACV", "Chagas", "EPOC"
    ])

    # 4. Signos Vitales
    st.subheader("4. Signos Vitales")
    col_v1, col_v2 = st.columns(2)
    peso = col_v1.number_input("Peso (Kg)", value=70.0)
    talla = col_v2.number_input("Talla (cm)", value=170.0)
    
    col_p1, col_p2 = st.columns(2)
    pas = col_p1.number_input("PAS (mmHg)", value=110)
    pad = col_p2.number_input("PAD (mmHg)", value=70)
    fc = col_v1.number_input("FC (lpm)", value=85)
    fr = col_v2.number_input("FR (rpm)", value=22)
    sato2 = st.number_input("SatO2 (%)", value=92)
    
    # 5. Examen Físico
    st.subheader("5. Examen Físico")
    iy = st.selectbox("Ingurgitación Yugular", ["Ausente", "Grado I (45°)", "Grado II (45°)", "Grado III (90°)"])
    rhy = st.checkbox("Reflujo Hepato-yugular")
    
    st.markdown("**Cardiopulmonar**")
    pmi = st.radio("PMI", ["Normal", "Desplazado"], horizontal=True)
    ruidos = st.radio("Ruidos", ["Rítmicos", "Arrítmicos"], horizontal=True)
    
    # Soplos
    tiene_soplo = st.checkbox("¿Tiene Soplo?")
    foco, ciclo, patron = "Aórtico", "Sistólico", "Holosistólico" # Defaults
    if tiene_soplo:
        foco = st.selectbox("Foco", ["Aórtico", "Mitral", "Tricúspideo", "Pulmonar"])
        ciclo = st.selectbox("Ciclo", ["Sistólico", "Diastólico"])
        if ciclo == "Sistólico":
            patron = st.selectbox("Patrón", ["Mesosistólico (diamante)", "Holosistólico"])
        else:
            patron = st.selectbox("Patrón", ["Decrescendo", "Click + Chasquido"])

    pulmones = st.selectbox("Ruidos Respiratorios", [
        "Murmullo vesicular", "Estertores basales", "Estertores hasta tercio medio", "Estertores universales", "Sibilancias/Roncus"
    ])
    
    st.markdown("**Extremidades (Godet)**")
    edema_ex = st.selectbox("Edema MsIs", ["Ausente", "Pies", "Hasta Rodillas", "Hasta Muslos"])
    godet = st.selectbox("Fóvea (Godet)", [
        "Sin fóvea", "Grado I (+)", "Grado II (++)", "Grado III (+++)", "Grado IV (++++)"
    ])
    
    pulsos = st.selectbox("Pulsos Distales", ["Normales", "Disminuidos", "Filiformes/Ausentes"])
    temp = st.selectbox("Temperatura Distal", ["Caliente", "Fría", "Muy Fría/Sudorosa"])
    llenado = st.number_input("Llenado Capilar (seg)", 2)

# --- CÁLCULOS AUTOMÁTICOS ---
imc = peso / ((talla/100)**2)
pam = pad + (pas - pad)/3
pp = pas - pad
ppp = (pp / pas) * 100 if pas > 0 else 0

# --- LÓGICA HEMODINÁMICA (CEREBRO) ---
# Eje Y: Congestión (PCP estimada)
score_congest = 0
if "Ortopnea" in sintomas: score_congest += 3
if "reposo" in sintomas[0] if sintomas else False: score_congest += 4
if iy == "Grado II (45°)": score_congest += 3
if iy == "Grado III (90°)": score_congest += 5
if rhy: score_congest += 2
if "Estertores" in pulmones: score_congest += 3
if edema_ex != "Ausente": score_congest += 2
if "Grado III" in godet or "Grado IV" in godet: score_congest += 2

pcp_sim = 12 + score_congest
if pcp_sim > 35: pcp_sim = 35

# Eje X: Perfusión (IC estimado)
score_perf = 2.8
if ppp < 25: score_perf -= 0.6 # Signo fuerte bajo gasto
if temp != "Caliente": score_perf -= 0.6
if llenado > 3: score_perf -= 0.4
if pulsos == "Filiformes/Ausentes": score_perf -= 0.5
if pas < 90: score_perf -= 0.4

ic_sim = max(1.0, score_perf)

# Clasificación Stevenson
if pcp_sim > 18 and ic_sim > 2.2:
    cuadrante = "B: Húmedo y Caliente"
    color_q = "orange"
elif pcp_sim > 18 and ic_sim <= 2.2:
    cuadrante = "C: Húmedo y Frío"
    color_q = "red"
elif pcp_sim <= 18 and ic_sim <= 2.2:
    cuadrante = "L: Seco y Frío"
    color_q = "blue"
else:
    cuadrante = "A: Seco y Caliente"
    color_q = "green"

# Inferencia Valvular
valvula_msg = inferir_valvulopatia(foco, ciclo, patron, tiene_soplo)

# --- INTERFAZ PRINCIPAL ---

# Métricas Superiores
col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
col_m1.metric("IMC", f"{imc:.1f}")
col_m2.metric("PAM", f"{pam:.0f} mmHg")
col_m3.metric("P. Pulso", f"{pp} mmHg")
col_m4.metric("PPP", f"{ppp:.1f} %", delta="- Hipoperfusión" if ppp < 25 else "OK", delta_color="inverse")
col_m5.metric("Stevenson", cuadrante)

if tiene_soplo:
    st.info(f"🩺 **Inferencia Valvular:** {valvula_msg}")

# Pestañas de Contenido
tabs = st.tabs(["📉 Hemodinamia Aguda", "💊 Simulación Terapéutica", "🏠 Plan Egreso (HFrEF)", "⚖️ FEVI Preservada/Leve"])

# TAB 1: STEVENSON
with tabs[0]:
    col_g1, col_g2 = st.columns([2, 1])
    with col_g1:
        # Gráfico Stevenson
        fig = go.Figure()
        fig.add_shape(type="rect", x0=0, y0=18, x1=2.2, y1=40, fillcolor="rgba(255, 0, 0, 0.15)", line_width=0, layer="below") # C
        fig.add_shape(type="rect", x0=2.2, y0=18, x1=5, y1=40, fillcolor="rgba(255, 165, 0, 0.15)", line_width=0, layer="below") # B
        fig.add_shape(type="rect", x0=0, y0=0, x1=2.2, y1=18, fillcolor="rgba(0, 0, 255, 0.15)", line_width=0, layer="below") # L
        fig.add_shape(type="rect", x0=2.2, y0=0, x1=5, y1=18, fillcolor="rgba(0, 255, 0, 0.15)", line_width=0, layer="below") # A
        
        # Etiquetas Cuadrantes
        fig.add_annotation(x=1.1, y=29, text="<b>C: Húmedo/Frío</b>", showarrow=False, font=dict(color="red", size=14))
        fig.add_annotation(x=3.6, y=29, text="<b>B: Húmedo/Caliente</b>", showarrow=False, font=dict(color="orange", size=14))
        fig.add_annotation(x=1.1, y=9, text="<b>L: Seco/Frío</b>", showarrow=False, font=dict(color="blue", size=14))
        fig.add_annotation(x=3.6, y=9, text="<b>A: Seco/Caliente</b>", showarrow=False, font=dict(color="green", size=14))

        # Paciente
        fig.add_trace(go.Scatter(x=[ic_sim], y=[pcp_sim], mode='markers+text', marker=dict(size=25, color='black'), text=["PACIENTE"], textposition="top center"))
        
        fig.update_layout(
            title="Cuadrante de Stevenson (Estimación Clínica)",
            xaxis_title="Índice Cardíaco (L/min/m²) - Perfusión",
            yaxis_title="PCP (mmHg) - Congestión",
            xaxis=dict(range=[0, 5], zeroline=False),
            yaxis=dict(range=[0, 40], zeroline=False),
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_g2:
        st.markdown("### Interpretación")
        st.markdown(f"""
        * **Congestión (Eje Y):** Basado en ortopnea, IY y Godet.
        * **Perfusión (Eje X):** Basado en PPP ({ppp:.1f}%), frialdad y sensorio.
        
        **Estado Actual:** {cuadrante}
        """)

# TAB 2: SIMULACIÓN
with tabs[1]:
    st.markdown("### 🧪 Laboratorio de Intervención")
    st.caption("Seleccione fármacos para ver el vector de efecto hemodinámico y datos farmacológicos.")
    
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    dx, dy = 0, 0
    
    with col_t1:
        if st.checkbox("Furosemida IV"):
            dy -= 8; dx += 0.1
            with st.expander("ℹ️ Detalle Furosemida"):
                st.write(meds_agudos["diureticos"]["dosis"])
                st.error(meds_agudos["diureticos"]["adverso"])
    
    with col_t2:
        if st.checkbox("Vasodilatador (NTG/NTP)"):
            dy -= 5; dx += 0.4
            with st.expander("ℹ️ Detalle Vasodilatador"):
                st.write(meds_agudos["vasodilatadores"]["dosis"])
                st.warning(meds_agudos["vasodilatadores"]["renal"])
                
    with col_t3:
        if st.checkbox("Inotrópico (Dobu/Milri)"):
            dx += 1.2; dy -= 2
            with st.expander("ℹ️ Detalle Inotrópico"):
                st.write(meds_agudos["inotropicos"]["dosis"])
                st.write(meds_agudos["inotropicos"]["renal"])
                
    with col_t4:
        if st.checkbox("Vasopresor (Norepi)"):
            dx += 0.2; dy += 2
            with st.expander("ℹ️ Detalle Vasopresor"):
                st.write(meds_agudos["vasopresores"]["dosis"])
                st.error("Usar solo en Shock Severo (PAS < 90) refractario.")

    # Gráfico Simulación
    new_ic, new_pcp = ic_sim + dx, pcp_sim + dy
    fig_sim = go.Figure(fig)
    fig_sim.add_annotation(x=new_ic, y=new_pcp, ax=ic_sim, ay=pcp_sim, xref="x", yref="y", axref="x", ayref="y", arrowwidth=3, arrowhead=2)
    fig_sim.add_trace(go.Scatter(x=[new_ic], y=[new_pcp], mode='markers', marker=dict(size=15, color='purple', symbol='x'), name="Post-Rx"))
    st.plotly_chart(fig_sim, use_container_width=True)

# TAB 3: EGRESO HFrEF
with tabs[2]:
    st.header("🏠 Plan de Egreso: HFrEF (FEVI < 40%)")
    st.subheader("1. Bloqueo Neurohormonal (GDMT - Los 4 Pilares)")
    
    gdmt_data = {
        "Pilar": ["ARNI / IECA / ARA-II", "Beta-Bloqueador", "ARM (Antag. Mineralocorticoides)", "iSGLT2"],
        "Fármaco": ["Sacubitrilo/Valsartan (1ra Línea)", "Metoprolol Succ, Carvedilol, Bisoprolol", "Espironolactona, Eplerenona", "Dapagliflozina, Empagliflozina"],
        "Tip Clínico": ["Suspender IECA 36h antes de ARNI.", "Iniciar con paciente euvolémico (seco).", "Vigilar K+ > 5.0 y Cr.", "No requiere titulación. Beneficio rápido."]
    }
    st.table(pd.DataFrame(gdmt_data))
    
    st.subheader("2. Adyuvantes Clave")
    c_a, c_b = st.columns(2)
    with c_a:
        st.info("**Corrección de Hierro:** Si Ferritina < 100 o 100-299 con IST < 20% → Hierro Carboximaltosa IV.")
    with c_b:
        st.success("**Rehabilitación Cardíaca:** Ordenar al egreso si estable. Vacunación Influenza/Neumococo.")

# TAB 4: FEVI PRESERVADA / LEVE
with tabs[3]:
    st.header("⚖️ FEVI Preservada (HFpEF ≥50%) y Levemente Reducida (HFmrEF 41-49%)")
    st.markdown("El manejo ha cambiado drásticamente con la evidencia reciente (EMPEROR-Preserved, DELIVER).")
    
    st.subheader("1. Fármacos con Evidencia Clase I (La base del tratamiento)")
    st.markdown("""
    * **iSGLT2 (Dapagliflozina / Empagliflozina):** Únicos fármacos con recomendación **Clase I, Nivel A** para reducir muerte CV y hospitalización en todo el espectro de FEVI.
    * **Diuréticos:** Recomendación Clase I solo para alivio sintomático de la congestión. No modifican mortalidad.
    """)
    
    st.subheader("2. Fármacos Clase IIb (Considerar)")
    st.markdown("""
    * **ARNI (Sacubitrilo/Valsartán):** Puede considerarse en el rango bajo de FEVI normal (HFmrEF o HFpEF con FEVI < 60%). (Estudio PARAGON-HF).
    * **ARM (Espironolactona):** Considerar si K+ normal y TFG > 30. (Estudio TOPCAT - Americas).
    * **Beta-Bloqueadores:** En HFmrEF se usan similar a HFrEF. En HFpEF **NO** se usan de rutina salvo indicación específica (ej. Fibrilación Auricular, Isquemia).
    """)
    
    st.subheader("3. Fenotipificación (Tratar la Causa)")
    st.warning("En HFpEF, buscar activamente la etiología específica es obligatorio.")
    
    fenotipos = {
        "Hipertensión": "Control estricto de PA. Fármacos preferidos: ARNI/ARA-II, ARM.",
        "Fibrilación Auricular": "Control de frecuencia o ritmo. Anticoagulación.",
        "Obesidad": "Pérdida de peso, Rehabilitación, iSGLT2.",
        "Amiloidosis Cardíaca (TTR)": "Sospechar en: Edad > 65, Túnel carpiano bilateral, HVI severa con bajo voltaje en EKG. Tto: Tafamidis.",
        "Isquemia": "Revascularización si hay síntomas anginosos."
    }
    for f, t in fenotipos.items():
        st.write(f"**{f}:** {t}")

# --- PIE DE PÁGINA ---
st.divider()
st.subheader("📚 Referencias Bibliográficas")
st.markdown("""
1. McDonagh TA, et al. **2021 ESC Guidelines for the diagnosis and treatment of acute and chronic heart failure**. *Eur Heart J*. 2021.
2. Heidenreich PA, et al. **2022 AHA/ACC/HFSA Guideline for the Management of Heart Failure**. *Circulation*. 2022.
3. Solomon SD, et al. **Dapagliflozin in Heart Failure with Mildly Reduced or Preserved Ejection Fraction (DELIVER)**. *N Engl J Med*. 2022.
4. Anker SD, et al. **Empagliflozin in Heart Failure with a Preserved Ejection Fraction (EMPEROR-Preserved)**. *N Engl J Med*. 2021.
""")


