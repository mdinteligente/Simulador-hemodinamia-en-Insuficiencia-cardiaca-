# Simulador clínico de perfiles de Stevenson - Generador de casos
# Autor: Docente de Cardiología - VI semestre Medicina

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# --- Función para clasificación de perfiles de Stevenson ---
def clasificar_stevenson(IC, PCAP):
    if IC >= 2.2 and PCAP <= 18:
        return "Perfil A - Compensado"
    elif IC >= 2.2 and PCAP > 18:
        return "Perfil B - Congestivo"
    elif IC < 2.2 and PCAP > 18:
        return "Perfil C - Congestivo e Hipoperfundido"
    elif IC < 2.2 and PCAP <= 18:
        return "Perfil L - Hipoperfundido seco"
    else:
        return "No clasificado"

# --- Título y descripción ---
st.set_page_config(layout="wide")
st.title("🩺 Generador de casos clínicos - Perfiles hemodinámicos de Stevenson")
st.markdown("Este simulador permite construir casos clínicos personalizados para explorar perfiles hemodinámicos de Stevenson y simular efectos farmacológicos.")

# --- Sección 1: Datos demográficos ---
st.header("1️⃣ Datos demográficos")
col1, col2 = st.columns(2)
with col1:
    ciudades = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena", "Bucaramanga", "Cúcuta", "Pereira", "Manizales", "Armenia", "Ibagué", "Villavicencio"]
    ciudad = st.selectbox("Ciudad o Municipio", ciudades)
    edad = st.number_input("Edad (años)", min_value=1, max_value=110, step=1)
with col2:
    procedencia = st.radio("Procedencia", ["Urbana", "Rural"])
    sexo = st.radio("Sexo", ["Masculino", "Femenino", "No binario", "Otro"])

# --- Sección 2: Síntomas ---
st.header("2️⃣ Síntomas principales")
sintomas = st.multiselect("Seleccione los síntomas presentes", [
    "Disnea con esfuerzos grandes",
    "Disnea con esfuerzos moderados",
    "Disnea con esfuerzos pequeños",
    "Disnea en reposo",
    "Disnea que progresó del esfuerzo al reposo",
    "Disnea en decúbito (ortopnea)",
    "Disnea al agacharse o amarrarse los zapatos",
    "Edemas de pies",
    "Edema de pies a rodillas",
    "Edema de pies a muslos",
    "Fatiga"
])
dias_evol = st.number_input("Días de evolución", min_value=0, step=1)

# --- Sección 3: Antecedentes ---
st.header("3️⃣ Antecedentes personales")
antecedentes = st.multiselect("Seleccione los antecedentes", [
    "Hipertensión arterial", "Diabetes tipo 2", "Dislipidemia", "Obesidad",
    "Enfermedad coronaria", "Fibrilación auricular", "ACV isquémico",
    "Cardiopatía isquémica", "Cardiopatía hipertensiva", "Cardiopatía chagásica",
    "Cardiopatía valvular"
])

# --- Sección 4: Signos vitales ---
st.header("4️⃣ Signos vitales")
col3, col4 = st.columns(2)
with col3:
    peso = st.number_input("Peso (kg)", min_value=20.0, max_value=200.0, step=0.5)
    talla = st.number_input("Talla (cm)", min_value=100, max_value=220)
    FC = st.number_input("Frecuencia cardíaca (lpm)", min_value=20)
    FR = st.number_input("Frecuencia respiratoria (rpm)", min_value=8)
    SatO2 = st.number_input("SatO2 sin oxígeno (%)", min_value=40.0, max_value=100.0)
with col4:
    ritmo = st.selectbox("Ritmo en monitor", ["Sinusal", "Fibrilación auricular", "Aleteo auricular", "Otro"])
    PAS = st.number_input("PAS (mmHg)", min_value=50)
    PAD = st.number_input("PAD (mmHg)", min_value=30)

# Cálculos derivados
IMC = round(peso / ((talla / 100) ** 2), 1) if talla > 0 else 0
PAM = round((2 * PAD + PAS) / 3, 1)
PP = PAS - PAD
PPP = round(PP / PAS, 2) if PAS > 0 else 0

st.markdown(f"**IMC calculado:** {IMC} kg/m²")
st.markdown(f"**PAM:** {PAM} mmHg")
st.markdown(f"**Presión de pulso:** {PP} mmHg")
st.markdown(f"**Presión de pulso proporcional:** {PPP}")

# --- Sección 5: Parámetros hemodinámicos (para Stevenson) ---
st.header("5️⃣ Parámetros hemodinámicos para perfil Stevenson")
col5, col6 = st.columns(2)
with col5:
    IC = st.slider("Índice Cardíaco (L/min/m²)", 1.0, 4.0, 2.0, 0.1)
with col6:
    PCAP = st.slider("Presión capilar pulmonar (mmHg)", 5, 35, 20)

perfil = clasificar_stevenson(IC, PCAP)
st.success(f"Perfil de Stevenson: {perfil}")

# --- Gráfico de cuadrantes de Stevenson ---
st.header("📊 Cuadrantes de Stevenson")
fig, ax = plt.subplots(figsize=(6, 6))
ax.axvline(2.2, color='gray', linestyle='--')
ax.axhline(18, color='gray', linestyle='--')
ax.set_xlim(1, 4)
ax.set_ylim(5, 35)
ax.set_xlabel('Índice Cardíaco (L/min/m²)')
ax.set_ylabel('PCAP (mmHg)')
ax.set_title('Clasificación de perfiles de Stevenson')
ax.grid(True, linestyle=':')

# Etiquetas de los cuadrantes
ax.text(3.3, 10, 'A\nCompensado', fontsize=10, ha='center')
ax.text(3.3, 30, 'B\nCongestivo', fontsize=10, ha='center')
ax.text(1.5, 30, 'C\nCongestivo e\nHipoperfundido', fontsize=10, ha='center')
ax.text(1.5, 10, 'L\nHipoperfundido seco', fontsize=10, ha='center')

# Punto del paciente
ax.plot(IC, PCAP, 'o', color='red', markersize=10, label='Paciente')
ax.legend()

st.pyplot(fig)

st.caption("ℹ️ Esta herramienta es solo educativa. No sustituye el juicio clínico profesional.")



