# Simulador hemodinámico para perfiles de Stevenson (versión gráfica Streamlit)
# Autor: Docente de Cardiología - VI semestre Medicina

import streamlit as st
import matplotlib.pyplot as plt

# Clasificación de perfiles de Stevenson
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

# Cálculo de PAM (presión arterial media)
def calcular_PAM(IC, RVS, PVC):
    return round(IC * RVS / 80 + PVC, 1)

# Funciones para simular intervención farmacológica
def aplicar_inotropico(IC, delta=0.5):
    return round(IC + delta, 2)

def aplicar_diuretico(PCAP, delta=-4):
    return max(0, round(PCAP + delta, 2))

def aplicar_vasopresor(RVS, incremento_pct=0.3):
    return round(RVS * (1 + incremento_pct), 1)

# Título
title = "\U0001F4CA Simulador hemodinámico - Perfiles de Stevenson"
st.title(title)

# Inputs iniciales
IC = st.slider("Índice Cardíaco (L/min/m²)", 1.0, 4.0, 2.0, 0.1)
PCAP = st.slider("PCAP (mmHg)", 5, 35, 20)
PVC = st.slider("PVC (mmHg)", 0, 20, 8)
RVS = st.slider("RVS (dinas·s·cm⁻⁵)", 800, 2400, 1600, 50)

# Cálculos iniciales
perfil_inicial = clasificar_stevenson(IC, PCAP)
PAM_inicial = calcular_PAM(IC, RVS, PVC)

# Intervenciones simuladas
IC_inotropico = aplicar_inotropico(IC)
PCAP_diuretico = aplicar_diuretico(PCAP)
RVS_vasopresor = aplicar_vasopresor(RVS)
PAM_post = calcular_PAM(IC_inotropico, RVS_vasopresor, PVC)
perfil_post = clasificar_stevenson(IC_inotropico, PCAP_diuretico)

# Resultados
st.subheader("Resultados de la simulación")
st.markdown(f"""
- **Perfil inicial:** {perfil_inicial}  
- **PAM inicial:** {PAM_inicial} mmHg  
- **IC tras inotrópico:** {IC_inotropico} L/min/m²  
- **PCAP tras diurético:** {PCAP_diuretico} mmHg  
- **RVS tras vasopresor:** {RVS_vasopresor} dinas·s·cm⁻⁵  
- **PAM post-intervención:** {PAM_post} mmHg  
- **Perfil final:** {perfil_post}
""")

# Gráfico comparativo
fig1, ax1 = plt.subplots()
etiquetas = ['IC', 'PCAP', 'RVS', 'PAM']
iniciales = [IC, PCAP, RVS, PAM_inicial]
post = [IC_inotropico, PCAP_diuretico, RVS_vasopresor, PAM_post]

bar_width = 0.35
index = range(len(etiquetas))

ax1.bar(index, iniciales, bar_width, label='Inicial')
ax1.bar([i + bar_width for i in index], post, bar_width, label='Post')

ax1.set_xlabel('Variables')
ax1.set_ylabel('Valores')
ax1.set_title('Comparación hemodinámica')
ax1.set_xticks([i + bar_width / 2 for i in index])
ax1.set_xticklabels(etiquetas)
ax1.legend()

st.pyplot(fig1)

# Diagrama de perfiles de Stevenson
fig2, ax2 = plt.subplots(figsize=(6,6))
ax2.axvline(2.2, color='gray', linestyle='--')
ax2.axhline(18, color='gray', linestyle='--')
ax2.set_xlim(1, 4)
ax2.set_ylim(5, 35)
ax2.set_xlabel('Índice Cardíaco (L/min/m²)')
ax2.set_ylabel('PCAP (mmHg)')
ax2.set_title('Clasificación de perfiles de Stevenson')

# Etiquetas de los cuadrantes
ax2.text(3.2, 10, 'A
Compensado', fontsize=10, ha='center')
ax2.text(3.2, 28, 'B
Congestivo', fontsize=10, ha='center')
ax2.text(1.4, 28, 'C
Congestivo e
Hipoperfundido', fontsize=10, ha='center')
ax2.text(1.4, 10, 'L
Hipoperfundido seco', fontsize=10, ha='center')

# Marcar puntos del paciente antes y después
ax2.plot(IC, PCAP, 'o', label='Inicial', color='blue')
ax2.plot(IC_inotropico, PCAP_diuretico, 'o', label='Post-tratamiento', color='orange')
ax2.legend()

st.pyplot(fig2)

st.caption("\u24D8 Esta herramienta es solo educativa. No sustituye el juicio clínico ni la experiencia de un especialista.")


