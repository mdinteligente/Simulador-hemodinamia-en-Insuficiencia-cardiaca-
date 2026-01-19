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
    .metric-card { background-color: #f0f2f6; padding: 10px; border-radius: 10px; border-left: 5px solid #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

# --- ENCABEZADO ---
st.title("🫀 HemoSim: Simulador Clínico de Hemodinamia")
st.markdown("**Herramienta docente para el abordaje de la Falla Cardíaca Aguda según perfiles de Stevenson.**")
st.caption("Basado en guías ESC 2021 y AHA/ACC/HFSA 2022.")

# --- BARRA LATERAL: INGRESO DE DATOS ---
with st.sidebar:
    st.header("📝 Historia Clínica")
    
    # 1. Demográficos
    st.subheader("1. Filiación")
    ciudades = ["Floridablanca", "Bucaramanga", "Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena", "Cúcuta", "Pereira", "Manizales", "Otra"]
    ciudad = st.selectbox("Ciudad / Municipio", ciudades)
    procedencia = st.radio("Procedencia", ["Urbana", "Rural"], horizontal=True)
    col1, col2 = st.columns(2)
    edad = col1.number_input("Edad (años)", min_value=18, max_value=120, value=65)
    sexo = col2.selectbox("Sexo", ["Masculino", "Femenino", "No binario", "Otro"])

    # 2. Síntomas
    st.subheader("2. Síntomas Actuales")
    sintomas = st.multiselect("Seleccione los presentes:", [
        "Disnea grandes esfuerzos", "Disnea moderados esfuerzos", "Disnea pequeños esfuerzos",
        "Disnea en reposo", "Disnea progresiva", "Ortopnea", "Bendopnea (al agacharse)",
        "Edema de pies", "Edema hasta rodillas", "Edema hasta muslos", "Fatiga/Asténia"
    ])
    dias_evol = st.number_input("Días de evolución", min_value=1, value=5)

    # 3. Antecedentes
    st.subheader("3. Antecedentes Patológicos")
    antecedentes = st.multiselect("Seleccione:", [
        "Hipertensión Arterial", "Diabetes Tipo 2", "Dislipidemia", "Obesidad",
        "Enfermedad Coronaria", "Fibrilación Auricular", "ACV Isquémico",
        "Cardiopatía Isquémica", "Cardiopatía Hipertensiva", "Cardiopatía Chagásica", "Cardiopatía Valvular"
    ])

    # 4. Signos Vitales
    st.subheader("4. Signos Vitales")
    col_v1, col_v2 = st.columns(2)
    peso = col_v1.number_input("Peso (Kg)", value=70.0)
    talla = col_v2.number_input("Talla (cm)", value=170.0)
    ritmo = st.selectbox("Ritmo en monitor", ["Sinusal", "Fibrilación Auricular", "Aleteo Atrial", "Otro"])
    
    col_p1, col_p2 = st.columns(2)
    pas = col_p1.number_input("PAS (mmHg)", value=110)
    pad = col_p2.number_input("PAD (mmHg)", value=70)
    
    fc = col_v1.number_input("FC (lpm)", value=85)
    fr = col_v2.number_input("FR (rpm)", value=22)
    sato2 = st.number_input("SatO2 aire ambiente (%)", value=92)

    # 5. Examen Físico
    st.subheader("5. Examen Físico Detallado")
    
    # Cuello
    iy = st.selectbox("Ingurgitación Yugular (IY)", ["Ausente", "Grado I (45°)", "Grado II (45°)", "Grado III (90°)"])
    
    # Tórax
    trabajo_resp = st.selectbox("Trabajo Respiratorio", ["Sin tirajes", "Tirajes aislados", "Tirajes universales"])
    pmi = st.radio("PMI", ["Normal", "Desplazado"], horizontal=True)
    ruidos_card = st.radio("Ruidos", ["Rítmicos", "Arrítmicos"], horizontal=True)
    
    soplo = st.checkbox("¿Tiene Soplo?")
    tipo_soplo = "No"
    if soplo:
        foco = st.selectbox("Foco", ["Aórtico", "Mitral", "Tricúspideo", "Pulmonar"])
        ciclo = st.selectbox("Ciclo", ["Sistólico", "Diastólico", "Sistodiastólico"])
        if ciclo == "Sistólico":
            patron = st.selectbox("Patrón", ["Mesosistólico (diamante)", "Holosistólico"])
        elif ciclo == "Diastólico":
            patron = st.selectbox("Patrón", ["Decrescendo", "Click + Chasquido"])
    
    pulmones = st.selectbox("Ruidos Respiratorios", [
        "Murmullo vesicular normal", "No audibles", "Estertores basales", 
        "Estertores 4 cuadrantes", "Roncus/Sibilancias"
    ])
    
    # Abdomen
    abdomen_tam = st.selectbox("Abdomen Aspecto", ["Normal", "Aumentado", "Excavado"])
    visceras = st.selectbox("Visceromegalias", ["Ausente", "Hepatomegalia", "Esplenomegalia", "Hepatoesplenomegalia"])
    rhy = st.radio("Reflujo Hepato-yugular", ["Ausente", "Presente"], horizontal=True)
    ascitis = st.radio("Onda Ascítica", ["Ausente", "Presente"], horizontal=True)
    
    # Extremidades / Perfusión
    edema_ex = st.selectbox("Edema MsIs", ["Ausente", "Pies", "Hasta Rodillas", "Hasta Muslos"])
    fovea = st.selectbox("Fóvea", ["No", "Grado I", "Grado II", "Grado III"])
    pulsos = st.selectbox("Pulsos Distales", ["+++ (Normal)", "++ (Disminuido)", "+ (Filiforme)", "Ausentes"])
    llenado = st.number_input("Llenado Capilar (seg)", value=2)
    temp_distal = st.selectbox("Temperatura Distal", ["Caliente (Normal)", "Fría", "Muy Fría/Húmeda"])
    
    # Neuro
    neuro = st.selectbox("Estado Neurológico", ["Alerta", "Somnoliento", "Estuporoso", "Coma"])

# --- CÁLCULOS AUTOMÁTICOS ---
imc = peso / ((talla/100)**2)
pam = pad + (pas - pad)/3
pp = pas - pad
ppp = (pp / pas) * 100 if pas > 0 else 0

# --- LÓGICA DE CLASIFICACIÓN (HEURÍSTICA CLÍNICA) ---
# Esta sección traduce la semiología a coordenadas X (Perfusión) e Y (Congestión)
# X: Índice Cardíaco (simulado) - Normal > 2.2
# Y: PCP (simulada) - Normal < 18

# Puntaje de Congestión (Para eje Y)
score_congest = 0
if "Ortopnea" in sintomas: score_congest += 3
if "Bendopnea" in sintomas: score_congest += 1
if "Disnea en reposo" in sintomas: score_congest += 4
if iy == "Grado I (45°)": score_congest += 2
if iy == "Grado II (45°)": score_congest += 4
if iy == "Grado III (90°)": score_congest += 6
if rhy == "Presente": score_congest += 2
if "Estertores" in pulmones: score_congest += 4
if edema_ex != "Ausente": score_congest += 2
if ascitis == "Presente": score_congest += 2

# Mapeo a PCP simulada (Base 12, max ~35)
pcp_sim = 12 + score_congest
if pcp_sim > 35: pcp_sim = 35

# Puntaje de Hipoperfusión (Para eje X)
# Signos de bajo gasto restan al IC
score_perf = 2.8 # Empezamos en un IC "bonito"
if ppp < 25: score_perf -= 0.6 # Presión de pulso proporcional estrecha es signo fuerte de bajo gasto
if temp_distal != "Caliente (Normal)": score_perf -= 0.6
if llenado > 3: score_perf -= 0.4
if neuro != "Alerta": score_perf -= 0.5
if pas < 90: score_perf -= 0.3
if pulsos == "+ (Filiforme)": score_perf -= 0.4

ic_sim = max(1.0, score_perf) # Evitar valores negativos

# Clasificación de Stevenson
cuadrante = ""
if pcp_sim > 18 and ic_sim > 2.2:
    cuadrante = "B: Húmedo y Caliente (Congestión)"
    color_q = "orange"
elif pcp_sim > 18 and ic_sim <= 2.2:
    cuadrante = "C: Húmedo y Frío (Congestión + Hipoperfusión)"
    color_q = "red"
elif pcp_sim <= 18 and ic_sim <= 2.2:
    cuadrante = "L: Seco y Frío (Hipoperfusión pura)"
    color_q = "blue"
else:
    cuadrante = "A: Seco y Caliente (Compensado)"
    color_q = "green"


# --- INTERFAZ PRINCIPAL ---

# 1. Panel de Métricas
st.subheader("📊 Datos Hemodinámicos Calculados")
c1, c2, c3, c4 = st.columns(4)
c1.metric("IMC", f"{imc:.1f} kg/m²")
c2.metric("PAM", f"{pam:.0f} mmHg", help="Presión Arterial Media")
c3.metric("Presión de Pulso", f"{pp} mmHg")
c4.metric("PPP (Proporcional)", f"{ppp:.1f} %", delta_color="inverse" if ppp < 25 else "normal", delta="- Riesgo Bajo Gasto" if ppp < 25 else "Adecuado")

st.info(f"📍 **Clasificación Actual:** {cuadrante}")

# 2. Tabs: Gráfico y Simulación
tab1, tab2 = st.tabs(["📉 Cuadrante de Stevenson", "💊 Simulación Terapéutica"])

with tab1:
    st.markdown("### Perfil Hemodinámico Basal")
    
    # Crear Gráfico Stevenson Base
    fig = go.Figure()

    # Líneas de corte
    fig.add_hline(y=18, line_dash="dash", line_color="gray", annotation_text="PCP 18 mmHg")
    fig.add_vline(x=2.2, line_dash="dash", line_color="gray", annotation_text="IC 2.2 L/min")

    # Puntos (Cuadrantes de fondo)
    fig.add_shape(type="rect", x0=0, y0=18, x1=2.2, y1=40, fillcolor="rgba(255, 0, 0, 0.1)", line_width=0) # C
    fig.add_shape(type="rect", x0=2.2, y0=18, x1=5, y1=40, fillcolor="rgba(255, 165, 0, 0.1)", line_width=0) # B
    fig.add_shape(type="rect", x0=0, y0=0, x1=2.2, y1=18, fillcolor="rgba(0, 0, 255, 0.1)", line_width=0) # L
    fig.add_shape(type="rect", x0=2.2, y0=0, x1=5, y1=18, fillcolor="rgba(0, 255, 0, 0.1)", line_width=0) # A

    # Paciente
    fig.add_trace(go.Scatter(
        x=[ic_sim], y=[pcp_sim],
        mode='markers+text',
        marker=dict(size=20, color=color_q, line=dict(width=2, color='black')),
        text=["PACIENTE"], textposition="top center",
        name="Estado Actual"
    ))

    fig.update_layout(
        title="Cuadrante de Stevenson (Estimado por Clínica)",
        xaxis_title="Índice Cardíaco (Perfusión)",
        yaxis_title="PCP / Congestión (Estimada)",
        xaxis=dict(range=[0.5, 5]),
        yaxis=dict(range=[0, 40]),
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    > **Nota Docente:** La ubicación se estima mediante algoritmos basados en la PPP (<25% sugiere IC < 2.2) y signos de congestión (IY, Ortopnea). *No sustituye la medición invasiva.*
    """)

with tab2:
    st.markdown("### 💊 Laboratorio de Intervención")
    st.write("Seleccione intervenciones para ver el cambio vectorial estimado en la hemodinamia.")
    
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    
    # Estados de los botones (Simulación simple de vectores)
    delta_x = 0
    delta_y = 0
    msgs = []

    with col_t1:
        st.markdown("**Diuréticos**")
        if st.checkbox("Furosemida IV"):
            delta_y -= 8 # Baja precarga fuertemente
            delta_x += 0.1 # Mejora leve del IC al bajar distensión
            msgs.append("Furosemida: ↓↓ Precarga (Congestión)")

    with col_t2:
        st.markdown("**Vasodilatadores**")
        nitro = st.checkbox("Nitroglicerina/Nitroprusiato")
        if nitro:
            delta_y -= 5 # Baja precarga
            delta_x += 0.4 # Sube IC al bajar postcarga
            msgs.append("Vasodilatador: ↓ Precarga, ↑ IC (Baja Postcarga)")

    with col_t3:
        st.markdown("**Inotrópicos**")
        inotrop = st.checkbox("Dobutamina / Milrinone")
        levo = st.checkbox("Levosimendán")
        if inotrop or levo:
            delta_x += 1.2 # Sube IC fuertemente
            delta_y -= 2 # Baja PCP levemente
            msgs.append("Inotrópico: ↑↑ Contractilidad (IC)")

    with col_t4:
        st.markdown("**Vasopresores**")
        vaso = st.checkbox("Norepinefrina")
        if vaso:
            delta_x += 0.2 # Sube PAM, permite perfusión en shock
            delta_y += 2 # Puede aumentar precarga por venoconstricción
            msgs.append("Vasopresor: ↑ RVS (PAM), cuidado con Postcarga")

    # Calcular nueva posición
    new_ic = ic_sim + delta_x
    new_pcp = pcp_sim + delta_y
    
    # Graficar cambios
    fig_sim = go.Figure(fig) # Copiar figura base
    
    # Añadir flecha de vector
    fig_sim.add_annotation(
        x=new_ic, y=new_pcp,
        ax=ic_sim, ay=pcp_sim,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=3, arrowcolor="black"
    )
    
    # Añadir nuevo punto fantasma
    fig_sim.add_trace(go.Scatter(
        x=[new_ic], y=[new_pcp],
        mode='markers',
        marker=dict(size=15, color='purple', symbol='x'),
        name="Post-Intervención"
    ))
    
    st.plotly_chart(fig_sim, use_container_width=True)
    
    if msgs:
        st.success("Efectos Hemodinámicos:")
        for m in msgs:
            st.write(f"- {m}")

# --- PIE DE PÁGINA DOCENTE ---
st.divider()
st.markdown("### 📚 Referencias y Perlas Clínicas")
with st.expander("Ver explicaciones detalladas"):
    st.markdown("""
    1. **Presión de Pulso Proporcional (PPP):** `(PAS - PAD) / PAS`. Si es **< 25%**, predice un Índice Cardíaco < 2.2 L/min/m² con una sensibilidad del 91% (Stevenson et al). Es el mejor predictor clínico de "Frío".
    2. **Congestión (Húmedo):** La ortopnea y la ingurgitación yugular son los signos más específicos de presiones de llenado elevadas (PCP > 18-22 mmHg).
    3. **Cuadrante C (Húmedo y Frío):** Es el de peor pronóstico. El tratamiento suele requerir inotrópicos (si hay hipotensión severa/shock) o vasodilatadores (si la presión lo permite) + diuréticos.
    4. **Vasopresores:** Solo indicados en shock cardiogénico con hipotensión severa (PAS < 90 mmHg) que no responde a volumen/inotrópicos iniciales, para mantener perfusión coronaria.
    """)




