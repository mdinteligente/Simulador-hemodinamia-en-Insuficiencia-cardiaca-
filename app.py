import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from fpdf import FPDF
import base64
import os

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
    input[type=number] { -moz-appearance: textfield; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTENTICACIÓN ---
def check_password():
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

# --- 3. GENERADOR PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'HemoSim - Reporte de Caso Clínico', 0, 1, 'C')
        self.ln(5)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, title, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, body)
        self.ln()

def create_download_link(val, filename):
    b64 = base64.b64encode(val)
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.pdf">📥 Descargar Reporte PDF</a>'

# --- FUNCIÓN NUEVA: SOLUCIÓN PARA VIDEOS DE RITMOS ---
def mostrar_video_ritmo(url):
    """Incrusta videos de ScreenPal usando un Iframe HTML."""
    if url.startswith("http"):
        # Código HTML para el reproductor
        html_code = f"""
        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%;">
            <iframe src="{url}" frameborder="0" allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
        </div>
        """
        st.markdown(html_code, unsafe_allow_html=True)
    else:
        st.info("⚠️ Enlace de video no configurado.")

# --- 4. RECURSOS Y DATA ---

def reproducir_multimedia(ruta):
    """Reproduce audio o video verificando existencia con manejo de errores."""
    if os.path.exists(ruta):
        try:
            if ruta.endswith(".mp4"):
                # start_time=0 fuerza al video a estar listo desde el inicio
                st.video(ruta, format="video/mp4", start_time=0) 
            else:
                st.audio(ruta)
        except Exception as e:
            st.error(f"Error formato: {ruta} | {str(e)}")
    else:
        st.error(f"⚠️ Archivo no encontrado: {ruta}")

def mostrar_imagen(ruta):
    if os.path.exists(ruta):
        st.image(ruta)
    else:
        st.error(f"⚠️ Imagen no encontrada: {ruta}")

# DICCIONARIO DE RECURSOS (Corregido según su lista de archivos)
# --- 3. RECURSOS Y DATA (Mapeo Exacto a su Carpeta assets) ---
# --- 4. RECURSOS Y DATA ---

# DICCIONARIO DE RECURSOS (Base correcta + ScreenPal para Ritmos)
recursos = {
    # IMÁGENES ESTÁTICAS (Locales)
    "pvc_lewis": "assets/Medicion PVC- Sumar 5 cm.jpg", 
    
    "rx_normal": "assets/Rx de tórax normal.jpg",
    "rx_congest": "assets/Rx de tórax con congestion basal.jpg",
    "rx_edema": "assets/Rx de tórax con edema pulmonar.jpg",
    
    # RITMOS (VIDEOS EXTERNOS - SCREENPAL)
    # Reemplace estos textos con sus enlaces reales de ScreenPal
    "ritmo_sinusal": "https://go.screenpal.com/watch/cTVFFNnf1pq",
    "ritmo_fa": "https://go.screenpal.com/watch/cTXDFZnFWGz",
    "ritmo_flutter": "https://go.screenpal.com/watch/cTVFFNnf1pV",
    "ritmo_mcp": "https://go.screenpal.com/watch/cTVFFNnf1pj",

    # RUIDOS CARDIACOS (Locales .mp3)
    "r_normales": "assets/Ruidos cardiacos normales.mp3",
    "r_s3": "assets/Tercer ruido cardiaco.mp3",
    "r_s4": "assets/Cuarto ruido cardiaco.mp3",
    "r_suma": "assets/Galope de suma.mp3",

    # SOPLOS (Locales .mp3)
    "soplo_ea": "assets/Estenosis aórtica.mp3",
    "soplo_em": "assets/Estenosis mitral.mp3",
    "soplo_im": "assets/Regurgitación mitral.mp3",   
    "soplo_ia": "assets/Regurgitación aórtica.mp3",  
    
    # PULMONAR (Locales .mp4 - Se ven con st.video)
    "pulm_normal": "assets/Murmullo vesicular normal.mp4",
    "pulm_estertores": "assets/Estertores.mp4",
    "pulm_sibilancias": "assets/Sibilancias.mp4",
    "pulm_roncus": "assets/Roncus.mp4"
}
municipios_base = sorted(list(set([
    "Abejorral", "Abriaquí", "Acacías", "Acandí", "Acevedo", "Achí", "Agrado", "Agua de Dios", "Aguachica", "Aguada", "Aguadas", "Aguazul", 
    "Alejandría", "Algarrobo", "Algeciras", "Almaguer", "Almeida", "Alpujarra", "Altamira", "Alto Baudó", "Amagá", "Amalfi", "Ambalema", 
    "Anapoima", "Ancuya", "Andalucía", "Andes", "Angelópolis", "Angostura", "Anolaima", "Anorí", "Anserma", "Ansermanuevo", "Anzoátegui", 
    "Apartadó", "Apía", "Apulo", "Aquitania", "Aracataca", "Aranzazu", "Aratoca", "Arauca", "Arauquita", "Arbeláez", "Arboleda", "Arboledas", 
    "Arboletes", "Arcabuco", "Arenal", "Argelia", "Ariguaní", "Arjona", "Armenia", "Armero", "Arroyohondo", "Astrea", "Ataco", "Atrato", 
    "Ayapel", "Bagadó", "Bahía Solano", "Bajo Baudó", "Balboa", "Baranoa", "Baraya", "Barbacoas", "Barbosa", "Barichara", "Barranca de Upía", 
    "Barrancabermeja", "Barranquilla", "Becerril", "Belalcázar", "Belén", "Belén de Umbría", "Bello", "Belmira", "Beltrán", "Berbeo", 
    "Betania", "Betéitiva", "Betulia", "Bituima", "Boavita", "Bochalema", "Bogotá D.C.", "Bojacá", "Bojayá", "Bolívar", "Bosconia", "Boyacá", 
    "Briceño", "Bucaramanga", "Buenaventura", "Buenavista", "Buenos Aires", "Buesaco", "Bugalagrande", "Buriticá", "Busbanzá", "Cabrera", 
    "Cabuyaro", "Cáceres", "Cachipay", "Caicedo", "Caicedonia", "Caimito", "Cajamarca", "Cajibío", "Cajicá", "Calamar", "Calarcá", "Caldas", 
    "Caldono", "Cali", "Calima", "Caloto", "Campamento", "Campo de la Cruz", "Campoalegre", "Campohermoso", "Canalete", "Candelaria", 
    "Cantagallo", "Caparrapí", "Capitanejo", "Cáqueza", "Caracolí", "Caramanta", "Carcasí", "Carepa", "Carmen de Apicalá", "Carmen de Carupa", 
    "Carmen de Viboral", "Carolina", "Cartagena", "Cartago", "Carurú", "Casabianca", "Castilla la Nueva", "Caucasia", "Célimo", "Cepitá", 
    "Cereté", "Cerinza", "Cerrito", "Cerro San Antonio", "Chachagüí", "Chaguaní", "Chalán", "Chameza", "Chapa", "Chaparral", "Charalá", 
    "Charta", "Chía", "Chigorodó", "Chima", "Chimichagua", "Chinácota", "Chinavita", "Chinchiná", "Chinú", "Chipaque", "Chipatá", "Chiquinquirá", 
    "Chiriguaná", "Chiscas", "Chita", "Chitagá", "Chitaraque", "Chivatá", "Chivor", "Choachí", "Chocontá", "Cicuco", "Ciénaga", "Ciénaga de Oro", 
    "Cimitarra", "Circasia", "Cisneros", "Ciudad Bolívar", "Clemencia", "Cocorná", "Coello", "Cogua", "Colombia", "Colón", "Colosó", "Cómbita", 
    "Concepción", "Concordia", "Condoto", "Confines", "Consacá", "Contratación", "Convención", "Copacabana", "Coper", "Córdoba", "Corinto", 
    "Coromoro", "Corozal", "Corrales", "Cota", "Cotorra", "Covarachía", "Coveñas", "Coyaima", "Cravo Norte", "Cuaspud", "Cubará", "Cubarral", 
    "Cucaita", "Cucunubá", "Cucutilla", "Cucutilla", "Cuítiva", "Cumaral", "Cumaribo", "Cumbal", "Cumbitara", "Cunday", "Curillo", "Curití", 
    "Curumaní", "Dabeiba", "Dagua", "Dibulla", "Distracción", "Dolores", "Don Matías", "Dosquebradas", "Duitama", "Durania", "Ebéjico", 
    "El Águila", "El Bagre", "El Banco", "El Cairo", "El Calvario", "El Carmen", "El Carmen de Bolívar", "El Castillo", "El Cerrito", 
    "El Charco", "El Cocuy", "El Colegio", "El Copey", "El Doncello", "El Dorado", "El Dovio", "El Encanto", "El Espino", "El Guacamayo", 
    "El Guamo", "El Litoral del San Juan", "El Molino", "El Paso", "El Paujil", "El Peñol", "El Peñón", "El Piñon", "El Playón", "El Retén", 
    "El Retorno", "El Roble", "El Rosal", "El Rosario", "El Santuario", "El Tablón de Gómez", "El Tambo", "El Tarra", "El Zulia", "Elías", 
    "Encino", "Enciso", "Entrerríos", "Envigado", "Espinal", "Facatativá", "Falan", "Filadelfia", "Filandia", "Firavitoba", "Flandes", 
    "Florencia", "Floresta", "Florián", "Florida", "Floridablanca", "Fómeque", "Fonseca", "Fortul", "Fosca", "Francisco Pizarro", "Fredonia", 
    "Fresno", "Frontino", "Fuente de Oro", "Fundación", "Funes", "Funza", "Fúquene", "Fusagasugá", "Gachalá", "Gachancipá", "Gachantivá", 
    "Gachetá", "Galán", "Galapa", "Galeras", "Gama", "Gamarra", "Garagoa", "Garzón", "Génova", "Gigante", "Ginebra", 
    "Giraldo", "Girardot", "Girardota", "Girón", "Gómez Plata", "González", "Gramalote", "Granada", "Guaca", "Guacamayas", "Guacarí", 
    "Guachucal", "Guadalupe", "Guaduas", "Guaitarilla", "Gualmatán", "Guamal", "Guamo", "Guapí", "Guapotá", "Guaranda", "Guarne", "Guasca", 
    "Guatapé", "Guataquí", "Guatavita", "Guateque", "Guática", "Guavata", "Guayabal de Síquima", "Guayabetal", "Guayatá", "Guepsa", "Güicán", 
    "Gutiérrez", "Hacarí", "Hatillo de Loba", "Hato", "Hato Corozal", "Hatonuevo", "Heliconia", "Herrán", "Herveo", "Hispania", "Hob", "Honda", 
    "Ibagué", "Icononzo", "Iles", "Imués", "Inzá", "Ipiales", "Isnos", "Istmina", "Itagüí", "Ituango", "Izá", "Jambaló", "Jamundí", "Jardín", 
    "Jenesano", "Jericó", "Jerusalén", "Jesús María", "Jordán", "Juan de Acosta", "Junín", "Juradó", "La Apartada", "La Argentina", "La Belleza", 
    "La Calera", "La Capilla", "La Ceja", "La Celia", "La Cruz", "La Cumbre", "La Dorada", "La Esperanza", "La Estrella", "La Florida", 
    "La Gloria", "La Jagua de Ibirico", "La Jagua del Pilar", "La Llanada", "La Macarena", "La Merced", "La Mesa", "La Montañita", "La Palma", 
    "La Paz", "La Peña", "La Pintada", "La Plata", "La Playa", "La Primavera", "La Salina", "La Sierra", "La Tebaida", "La Tola", "La Unión", 
    "La Uribe", "La Vega", "La Victoria", "La Virginia", "Labateca", "Labranzagrande", "Landázuri", "Lebrija", "Leíva", "Lejanías", 
    "Lenguazaque", "Lérida", "Leticia", "Líbano", "Liborina", "Linares", "Lloró", "López", "Lorica", "Los Andes", "Los Córdobas", "Los Palmitos", 
    "Los Patios", "Los Santos", "Luruaco", "Macanal", "Macaravita", "Maceo", "Macheta", "Madrid", "Magangué", "Magüí", "Mahates", "Maicao", 
    "Majagual", "Málaga", "Malambo", "Mallama", "Manatí", "Manaure", "Maní", "Manizales", "Manta", "Manzanares", "Mapiripán", "Margarita", 
    "María la Baja", "Marinilla", "Maripí", "Mariquita", "Marmato", "Marquetalia", "Marsella", "Marulanda", "Matanza", "Medellín", "Medina", 
    "Medio Atrato", "Medio Baudó", "Medio San Juan", "Melgar", "Mercaderes", "Mesetas", "Milán", "Miraflores", "Miranda", "Mistrató", "Mitú", 
    "Mocoa", "Mogotes", "Molagavita", "Momil", "Mompós", "Mongua", "Monguí", "Moniquirá", "Montebello", "Montecristo", "Montelíbano", 
    "Montenegro", "Montería", "Monterrey", "Morales", "Morelia", "Morroa", "Mosquera", "Motavita", "Murillo", "Murindó", "Mutatá", "Mutiscua", 
    "Muzo", "Nariño", "Nátaga", "Natagaima", "Nechí", "Necoclí", "Neira", "Neiva", "Nemocón", "Nilo", "Nimaima", "Nobsa", "Nocaima", "Norcasia", 
    "Nóvita", "Nuevo Colón", "Nunchía", "Nuquí", "Obando", "Ocamonte", "Ocaña", "Oiba", "Oicatá", "Olaya", "Olaya Herrera", "Onzaga", "Oporapa", 
    "Orito", "Orocué", "Ortega", "Ospina", "Otanche", "Ovejas", "Pachavita", "Pacho", "Padilla", "Páez", "Paicol", "Pailitas", "Paime", "Paipa", 
    "Pajarito", "Palermo", "Palestina", "Palmar", "Palmar de Varela", "Palmas del Socorro", "Palmira", "Palmito", "Palocabildo", "Pamplona", 
    "Pamplonita", "Paniagua", "Pantoja", "Páramo", "Paratebueno", "Pasca", "Pasto", "Patía", "Pauna", "Paya", "Paz de Ariporo", "Paz de Río", 
    "Pedraza", "Pelaya", "Pensilvania", "Peñol", "Peque", "Pereira", "Pesca", "Piamonte", "Pie de Cuesta", "Piedras", "Piendamó", "ijao", "Pijiño del Carmen", 
    "Pinchote", "Pinillos", "Piojó", "Pisba", "Pital", "Pitalito", "Pivijay", "Planadas", "Planeta Rica", "Plato", "Policarpa", "Polonuevo", 
    "Ponedera", "Popayán", "Pore", "Potosí", "Pradera", "Prado", "Providencia", "Pueblo Bello", "Pueblo Nuevo", "Pueblo Rico", "Pueblorrico", 
    "Puebloviejo", "Puente Nacional", "Puerres", "Puerto Asís", "Puerto Berrío", "Puerto Boyacá", "Puerto Caicedo", "Puerto Carreño", 
    "Puerto Colombia", "Puerto Concordia", "Puerto Escondido", "Puerto Gaitán", "Puerto Guzmán", "Puerto Leguízamo", "Puerto Libertador", 
    "Puerto Lleras", "Puerto López", "Puerto Nare", "Puerto Nariño", "Puerto Parra", "Puerto Rico", "Puerto Rondón", "Puerto Salgar", 
    "Puerto Santander", "Puerto Tejada", "Puerto Triunfo", "Puerto Wilches", "Pulí", "Pupiales", "Puracé", "Purificación", "Purísima", 
    "Quebradanegra", "Quetame", "Quibdó", "Quimbaya", "Quinchía", "Quípama", "Quipile", "Ragonvalia", "Ramiriquí", "Ráquira", "Recetor", 
    "Regidor", "Remedios", "Remolino", "Repelón", "Restrepo", "Retiro", "Ricaurte", "Rio de Oro", "Rio Iro", "Rio Quito", "Rio Viejo", 
    "Rioblanco", "Riofrío", "Riohacha", "Rionegro", "Riosucio", "Risaralda", "Rivera", "Roberto Payán", "Roldanillo", "Roncesvalles", 
    "Rondón", "Rosas", "Rovira", "Sáchica", "Sahagún", "Saladoblanco", "Salamina", "Salazar", "Saldaña", "Salento", "Salgar", "Samacá", "Samaniego", 
    "Samaná", "Sampués", "San Agustín", "San Alberto", "San Andrés", "San Andrés Sotavento", "San Antero", "San Antonio", "San Antonio del Tequendama", 
    "San Benito", "San Benito Abad", "San Bernardo", "San Bernardo del Viento", "San Calixto", "San Carlos", "San Carlos de Guaroa", "San Cayetano", 
    "San Cristóbal", "San Diego", "San Eduardo", "San Estanislao", "San Fernando", "San Francisco", "San Gil", "San Jacinto", "San Jacinto del Cauca", 
    "San Jerónimo", "San Joaquín", "San José", "San José de la Montaña", "San José de Miranda", "San José de Pare", "San José del Fragua", 
    "San José del Guaviare", "San José del Palmar", "San Juan de Arama", "San Juan de Betulia", "San Juan de Rioseco", "San Juan de Urabá", 
    "San Juan del Cesar", "San Juan Nepomuceno", "San Juanito", "San Lorenzo", "San Luis", "San Luis de Gaceno", "San Luis de Palenque", 
    "San Marcos", "San Martín", "San Martín de Loba", "San Mateo", "San Miguel", "San Miguel de Sema", "San Onofre", "San Pablo", 
    "San Pablo de Borbur", "San Pedro", "San Pedro de Cartago", "San Pedro de Urabá", "San Pelayo", "San Rafael", "San Roque", "San Sebastián", 
    "San Sebastián de Buenavista", "San Vicente", "San Vicente del Caguán", "San Vicente del Chucurí", "San Zenón", "Sandoná", "Santa Ana", 
    "Santa Bárbara", "Santa Bárbara de Pinto", "Santa Catalina", "Santa Fe de Antioquia", "Santa Genoveva de Docorodó", "Santa Helena del Opón", 
    "Santa Isabel", "Santa Lucía", "Santa María", "Santa Marta", "Santa Rosa", "Santa Rosa de Cabal", "Santa Rosa de Osos", "Santa Rosa de Viterbo", 
    "Santa Rosa del Sur", "Santa Rosalía", "Santa Sofía", "Santana", "Santander de Quilichao", "Santiago", "Santo Domingo", "Santo Tomás", 
    "Santuario", "Sapuyes", "Saravena", "Sardinata", "Sasaima", "Sativanorte", "Sativasur", "Segovia", "Sesquilé", "Sevilla", "Siachoque", 
    "Sibaté", "Sibundoy", "Silos", "Silvania", "Silvia", "Simacota", "Simijaca", "Simití", "Sincelejo", "Sincé", "Sipí", "Sitionuevo", 
    "Soacha", "Soatá", "Socha", "Socorro", "Socotá", "Sogamoso", "Solano", "Soledad", "Solita", "Somondoco", "Sonsón", "Sopetrán", "Soplaviento", 
    "Sopó", "Sora", "Soracá", "Sotaquirá", "Sotara", "Suaita", "Suárez", "Suaza", "Subachoque", "Sucre", "Suesca", "Supatá", "Supía", "Suratá", 
    "Susa", "Susacón", "Sutamarchán", "Sutatausa", "Sutatenza", "Tabio", "Tadó", "Talaigua Nuevo", "Tamalameque", "Támara", "Tame", "Támesis", 
    "Taminango", "Tangua", "Taraira", "Tarazá", "Tarqui", "Tarso", "Tasco", "Tauramena", "Tausa", "Tello", "Tena", "Tenerife", "Tenjo", "Tenza", 
    "Teorama", "Teruel", "Tesalia", "Tibacuy", "Tibaná", "Tibasosa", "Tibirita", "Tibú", "Tierralta", "Timaná", "Timbío", "Timbiquí", "Tinjacá", 
    "Tipacoque", "Tiquisio", "Titiribí", "Toca", "Tocaima", "Tocancipá", "Togüí", "Toledo", "Tolú", "Tolú Viejo", "Tona", "Tópaga", "Topaipí", 
    "Toribío", "Toro", "Tota", "Totoró", "Trinidad", "Trujillo", "Tubará", "Tuchín", "Tuluá", "Tumaco", "Tunja", "Tununguá", "Túquerres", 
    "Turbaco", "Turbaná", "Turbo", "Turmequé", "Tuta", "Tutazá", "Ubalá", "Ubaque", "Ubaté", "Ulloa", "Umbita", "Une", "Unguía", 
    "Unión Panamericana", "Uramita", "Uribe", "Uribia", "Urrao", "Urumita", "Usiacurí", "Útica", "Valdivia", "Valencia", "Valle de San José", 
    "Valle de San Juan", "Valledupar", "Valparaíso", "Vegachí", "Vélez", "Venadillo", "Venecia", "Ventanas", "Vergara", "Versalles", "Vetas", 
    "Viani", "Victoria", "Vigía del Fuerte", "Vijes", "Villa Caro", "Villa de Leyva", "Villa del Rosario", "Villa Gamero", "Villa Garzón", 
    "Villa Rica", "Villagómez", "Villahermosa", "Villamaría", "Villanueva", "Villapinzón", "Villarrica", "Villavicencio", "Villavieja", 
    "Villeta", "Viotá", "Viracachá", "Vista Hermosa", "Viterbo", "Yacopí", "Yacuanquer", "Yaguará", "Yalí", "Yarumal", "Yavaraté", "Yolombó", 
    "Yondó", "Yopal", "Yotoco", "Yumbo", "Zambrano", "Zapatoca", "Zapayán", "Zaragoza", "Zarzal", "Zetaquira", "Zipacón", "Zipaquirá", 
    "Zona Bananera"
])))

# Zonas de Riesgo Chagas (Solo para validación epidemiológica)
zonas_chagas = [
    "Boavita", "Chiscas", "Cubará", "Güicán de la Sierra", "Labranzagrande", "Paya", "Pisba", "San Mateo", "Soatá", "Socotá", "Tipacoque",
    "Barichara", "Capitanejo", "Encinales", "Hato", "Mogotes", "San Gil", "San José de Miranda", "San Vicente del Chucurí", "Socorro",
    "Aguazul", "Chámeza", "Hato Corozal", "Nunchía", "Paz de Ariporo", "Recetor", "Támara", "Tauramena", "Yopal",
    "Arauca", "Arauquita", "Saravena", "Tame",
    "Choachí", "Fómeque", "Gachalá", "Medina", "Nilo", "Paratebueno", "Ubaque",
    "Cáchira", "Sardinata", "Toledo",
    "La Jagua de Ibirico", "Pueblo Bello", "Valledupar",
    "Liborina", "Peque", "Yolombó"
]

# Antecedentes (Lista Completa)
antecedentes_lista = sorted([
    "Apnea del sueño", "Arteritis reumatoide", "Cardiopatía congénita", "Diabetes Mellitus Tipo 2", "Dislipidemia", 
    "Enfermedad arterial oclusiva crónica", "Enfermedad carotidea", "Enfermedad cerebro-vascular (ACV)", "Enfermedad coronaria", 
    "ERC sin diálisis", "ERC en diálisis", "Hipertensión arterial", "Insuficiencia cardiaca previa", "Lupus eritematoso sistémico", 
    "Obesidad", "Tabaquismo", "VIH"
])

# Farmacología Detallada (Braunwald/Guías)
meds_agudos = {
    "oxigeno": {
        "nombre": "Oxígeno / Ventilación No Invasiva (VNI)",
        "dosis": "• **Oxígeno Suplementario:** Titular para meta de SatO2 > 90% (>95% en embarazo).\n• **Ventilación Mecánica No Invasiva (CPAP/BiPAP):** Iniciar con PEEP 5-10 cmH2O. Indicación Clase IIa si hay FR > 25 rpm, Acidosis respiratoria (pH < 7.35) o Edema Pulmonar franco para reducir precarga y trabajo respiratorio.",
        "monitor": "• Gases arteriales (control a la 1 hora post-inicio).\n• Estado de conciencia y tolerancia a la interfaz (máscara).\n• Riesgo de hipotensión (la presión positiva intratorácica reduce el retorno venoso).",
        "adverso": "Intolerancia, claustrofobia, broncoaspiración (contraindicado si hay deterioro del sensorio o vómito), resequedad de mucosas."
    },
    "liquidos": {
        "nombre": "Líquidos Endovenosos (Cristaloides)",
        "dosis": "• **Cristaloides Balanceados:** Lactato de Ringer o Solución Salina Normal 0.9%.\n• **Reto de Fluidos (Solo Perfil L - Seco/Frío):** Bolos de 250-500 cc en 15-30 minutos bajo vigilancia estricta.\n• **Objetivo:** Aumentar precarga para mejorar Volumen Sistólico (Mecanismo Frank-Starling).",
        "monitor": "• Signos de congestión pulmonar (aparición de estertores).\n• Respuesta clínica (Mejoría de Presión Arterial, Gasto Urinario, aclaramiento de Lactato).",
        "adverso": "Edema Pulmonar Agudo (iatrogénico si se administra en pacientes húmedos), Acidosis hiperclorémica (con volúmenes altos de SSN 0.9%)."
    },
    "diureticos": {
        "nombre": "Furosemida (Diurético de Asa)",
        "dosis": "• **Pacientes vírgenes de tratamiento (Naïve):** Bolo IV de 20 mg a 40 mg.\n• **Pacientes con uso crónico:** Bolo IV inicial de 1 a 2.5 veces su dosis oral total diaria.\n• **Infusión Continua:** Si hay respuesta pobre a bolos, iniciar infusión a 5 - 40 mg/hora.\n• **Bloqueo Secuencial de Nefrona:** Si hay resistencia diurética, adicionar Tiazida (Hidroclorotiazida 25mg o Metolazona).",
        "monitor": "• Gasto urinario horario (Meta > 100-150 ml/hora primeras 6 horas).\n• Electrolitos: Potasio (K+) y Magnesio (Mg++) cada 6-12 horas.\n• Función renal: Esperar elevación transitoria de Creatinina (permisiva si hay descongestión exitosa).",
        "adverso": "Hipokalemia, Hipomagnesemia, Ototoxicidad (riesgo en bolos rápidos > 20mg/min), Hipotensión, Alcalosis metabólica por contracción."
    },
    "vasodilatadores": {
        "nombre": "Vasodilatadores (Nitroglicerina / Nitroprusiato)",
        "dosis": "• **Nitroglicerina:** Iniciar infusión a 10-20 mcg/min. Titular aumentando 5-10 mcg/min cada 3-5 minutos según respuesta. Dosis máxima usual 200 mcg/min.\n• **Nitroprusiato de Sodio:** Iniciar a 0.3 mcg/kg/min. Titular hasta 5 mcg/kg/min. (Requiere línea arterial obligatoria y protección de la luz).",
        "monitor": "• Presión Arterial continua (Detener o reducir si Presión Sistólica < 90 mmHg).\n• Cefalea intensa (muy común con Nitroglicerina).\n• Saturación O2 (puede caer levemente por alteración ventilación/perfusión).",
        "adverso": "Hipotensión severa, Taquicardia refleja, Cefalea, Fenómeno de robo coronario. Nitroprusiato: Riesgo de toxicidad por cianuro/tiocianato en uso prolongado (>24-48h) o falla renal."
    },
    "inotropicos": {
        "nombre": "Inotrópicos (Dobutamina / Milrinone / Levosimendán)",
        "dosis": "• **Dobutamina:** Iniciar a 2 mcg/kg/min. Titular hasta máximo 20 mcg/kg/min (Agonista Beta-1 adrenérgico).\n• **Milrinone:** Iniciar a 0.375 mcg/kg/min. Rango 0.375 - 0.75 mcg/kg/min. (Inhibidor PDE3, inodilatador). Ajustar al 50% en falla renal. No usar bolo de carga.\n• **Levosimendán:** Infusión de 0.1 mcg/kg/min (rango 0.05 - 0.2) por 24 horas. (Sensibilizador de calcio). No usar bolo de carga rutinario.",
        "monitor": "• Monitoría electrocardiográfica continua (Riesgo de arritmias ventriculares y auriculares).\n• Signos de isquemia miocárdica (Dobutamina aumenta consumo de O2).\n• Presión Arterial (Milrinone y Levosimendán causan hipotensión por vasodilatación periférica).",
        "adverso": "Taquicardia sinusal, Fibrilación auricular, Complejos ventriculares prematuros/Taquicardia Ventricular, Hipotensión sostenida (Milrinone/Levosimendán), Hipokalemia."
    },
    "vasopresores": {
        "nombre": "Vasopresores (Norepinefrina)",
        "dosis": "• **Norepinefrina:** Iniciar a 0.05 mcg/kg/min. Titular cada 3-5 minutos hasta 0.5 mcg/kg/min o más según necesidad. Meta: Presión Arterial Media (PAM) > 65 mmHg.\n• (Vasopresor de elección en Shock Cardiogénico según guías ESC/AHA).",
        "monitor": "• Signos de perfusión distal y esplácnica (Lactato sérico, llenado capilar).\n• Acceso venoso central preferido (riesgo de necrosis por extravasación).\n• Línea arterial obligatoria para titulación precisa.",
        "adverso": "Isquemia tisular (necrosis de dedos/extremidades), Arritmias, Hipertensión severa reactiva, Aumento excesivo de la postcarga del ventrículo izquierdo (puede empeorar el gasto cardíaco si no hay inotropía adecuada)."
    }
}

# --- 5. LÓGICA CLÍNICA ---
def inferir_valvulopatia(foco, ciclo, patron, localizacion_soplo):
    if not localizacion_soplo: return "Sin soplos reportados."
    dx = "Soplo no específico"
    if foco == "Aórtico":
        if ciclo == "Sistólico": dx = "**Posible Estenosis Aórtica** (Busca pulso parvus et tardus)."
        elif ciclo == "Diastólico": dx = "**Posible Insuficiencia Aórtica** (Busca presión pulso amplia)."
    elif foco == "Mitral":
        if ciclo == "Sistólico": dx = "**Posible Insuficiencia Mitral** (Busca irradiación axila)."
        elif ciclo == "Diastólico": dx = "**Posible Estenosis Mitral** (Busca chasquido de apertura)."
    elif foco == "Pulmonar" and ciclo == "Diastólico":
         dx = "**Posible Insuficiencia Pulmonar** (Soplo de Graham Steell)."
    elif foco == "Tricúspideo" and ciclo == "Sistólico":
        dx = "**Posible Insuficiencia Tricuspídea** (Signo Rivero-Carvallo)."
    return dx

def calcular_fenotipo_fevi(fevi):
    if fevi < 40: return "HFrEF (FEVI Reducida < 40%)"
    elif 40 <= fevi < 50: return "HFmrEF (FEVI Levemente Reducida 40-49%)"
    else: return "HFpEF (FEVI Preservada ≥ 50%)"

# --- 6. INTERFAZ: BARRA LATERAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063823.png", width=50)
    st.title("Historia Clínica")
    st.markdown("---")
    
    # 1. Origen
    st.subheader("1. Origen y Demografía")
    # Usa municipios_base (la lista completa)
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
    sintomas = st.multiselect("Seleccione:", ["Disnea esfuerzo", "Disnea reposo", "Disnea Paroxística Nocturna", "Ortopnea", "Bendopnea", "Fatiga", "Angina", "Edema MsIs (Refiere)", "Vómito", "Diarrea", "Sangrado"])

    # 4. Signos Vitales
    st.subheader("4. Signos Vitales")
    # Se eliminó la opción "Otro"
    ritmo = st.selectbox("Ritmo", ["Sinusal", "Fibrilación Auricular", "Flutter Atrial", "Marcapasos"])
    
    # LÓGICA DE VIDEOS RITMOS (Mapeo corregido)
    with st.expander("Ver Monitor de Ritmo", expanded=True):
        if ritmo == "Sinusal":
            reproducir_multimedia(recursos["ritmo_sinusal"])
        elif ritmo == "Fibrilación Auricular":
            reproducir_multimedia(recursos["ritmo_fa"])
        elif ritmo == "Flutter Atrial":
            reproducir_multimedia(recursos["ritmo_flutter"])
        elif ritmo == "Marcapasos":
            reproducir_multimedia(recursos["ritmo_mcp"])
    # LÓGICA DE VIDEOS RITMOS
    if ritmo == "Sinusal":
        reproducir_multimedia(recursos["ritmo_sinusal"])
    elif ritmo == "Fibrilación Auricular":
        reproducir_multimedia(recursos["ritmo_fa"])
    elif ritmo == "Flutter Atrial":
        reproducir_multimedia(recursos["ritmo_flutter"])
    elif ritmo == "Marcapasos":
        reproducir_multimedia(recursos["ritmo_mcp"])

    c_v1, c_v2 = st.columns(2)
    pas = c_v1.number_input("PAS (mmHg)", value=120, step=1)
    pad = c_v2.number_input("PAD (mmHg)", value=80, step=1)
    fc = c_v1.number_input("FC (lpm)", value=80, step=1)
    fr = c_v2.number_input("FR (rpm)", value=18, step=1)
    sato2 = c_v1.number_input("SatO2 (%)", value=92, step=1)
    temp_c = c_v2.number_input("Temp (°C)", value=36.5, step=0.1)
    
    # 5. Examen Físico
    st.subheader("5. Examen Físico")
    
    st.markdown("🔴 **Cabeza y Cuello**")
    iy_presente = st.radio("Ingurgitación Yugular:", ["Ausente", "Presente"], horizontal=True)
    iy_desc = "Ausente"
    if iy_presente == "Presente":
        col_venosa = st.number_input("Altura columna venosa (cm) desde ángulo Louis:", 0, 20, 5)
        pvc_cmh2o = col_venosa + 5
        pvc_mmhg = pvc_cmh2o * 0.735
        iy_desc = f"Presente (PVC aprox {pvc_mmhg:.1f} mmHg)"
        st.info(f"PVC Estimada (Lewis): {pvc_cmh2o} cmH2O ≈ {pvc_mmhg:.1f} mmHg")
        with st.expander("Ver Método de Lewis"): mostrar_imagen(recursos["pvc_lewis"])
    
    rhy = st.checkbox("Reflujo Hepato-yugular")

    st.markdown("🔴 **Cardiovascular**")
    opciones_ruidos = ["R1-R2 Normales", "S3 (Galope Ventricular)"]
    if ritmo == "Sinusal":
        opciones_ruidos.extend(["S4 (Galope Atrial)", "S3 + S4 (Suma)"])
    ruidos_agregados = st.selectbox("Ruidos:", opciones_ruidos)
    
    # REPRODUCTOR INTELIGENTE (Usa la función creada arriba)
    with st.expander("🎧 Escuchar Ruidos", expanded=True):
        if "Normales" in ruidos_agregados: reproducir_multimedia(recursos["r_normales"])
        elif "S3" in ruidos_agregados: reproducir_multimedia(recursos["r_s3"])
        elif "S4" in ruidos_agregados: reproducir_multimedia(recursos["r_s4"])
        elif "Suma" in ruidos_agregados: reproducir_multimedia(recursos["r_suma"])

    tiene_soplo = st.checkbox("¿Tiene Soplo?")
    foco, ciclo, patron = "Aórtico", "Sistólico", "Holosistólico"
    if tiene_soplo:
        foco = st.selectbox("Foco", ["Aórtico", "Mitral", "Tricúspideo", "Pulmonar"])
        ciclo = st.selectbox("Ciclo", ["Sistólico", "Diastólico"])
        patron = st.selectbox("Patrón", ["Diamante", "Holosistólico", "Decrescendo", "Click", "Retumbo"])
        
        with st.expander("🎧 Escuchar Soplo"):
            if "Aórtico" in foco and ciclo == "Diastólico": reproducir_multimedia(recursos["soplo_ia"])
            elif "Mitral" in foco and ciclo == "Diastólico": reproducir_multimedia(recursos["soplo_em"])
            elif "Pulmonar" in foco and ciclo == "Diastólico": st.info("Soplo pulmonar diastólico (Graham-Steell) no disponible en audio.") # No hay archivo en lista
            elif "Aórtico" in foco: reproducir_multimedia(recursos["soplo_ea"])
            elif "Mitral" in foco: reproducir_multimedia(recursos["soplo_im"])

    st.markdown("🔴 **Tórax: Pulmonar**")
    pulmones_opciones = ["Murmullo Vesicular", "Estertores basales", "Estertores >1/2", "Sibilancias", "Roncus"]
    pulmones = st.selectbox("Auscultación", pulmones_opciones)
    with st.expander("🎧 Escuchar Pulmón"):
        if "Estertores" in pulmones: reproducir_multimedia(recursos["pulm_estertores"])
        elif "Sibilancias" in pulmones: reproducir_multimedia(recursos["pulm_sibilancias"])
        elif "Roncus" in pulmones: reproducir_multimedia(recursos["pulm_roncus"])
        else: reproducir_multimedia(recursos["pulm_normal"])

    st.markdown("🔴 **Abdomen**")
    abdomen_viscera = st.selectbox("Visceromegalias", ["Sin visceromegalias", "Hepatomegalia", "Esplenomegalia", "Hepatoesplenomegalia"])
    ascitis = st.checkbox("Onda Ascítica Presente")

    st.markdown("🔴 **Extremidades**")
    edema_ex = st.selectbox("Edema", ["Ausente", "Maleolar", "Rodillas", "Muslos"])
        
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
        fevi = st.number_input("FEVI (%)", 0, 100, 35)
        lactato = st.number_input("Lactato (mmol/L)", 0.0, 20.0, 1.0, 0.1)
        rx_patron = st.selectbox("Patrón Rx", ["Normal", "Congestión Leve/Basal", "Edema Alveolar (4 Cuadrantes)"])
        with st.expander("Ver Rx Referencia"):
            if rx_patron == "Normal": mostrar_imagen(recursos["rx_normal"])
            elif rx_patron == "Congestión Leve/Basal": mostrar_imagen(recursos["rx_congest"])
            else: mostrar_imagen(recursos["rx_edema"])
        
        c_p1, c_p2 = st.columns(2)
        tipo_peptido = c_p1.selectbox("Tipo", ["BNP", "NT-proBNP"])
        valor_peptido = c_p2.number_input("Valor (pg/mL)", 0, 50000, 0)
        
        # EXPLICACIÓN PÉPTIDOS AMPLIADA (DOCENCIA)
        if tipo_peptido == "NT-proBNP":
            st.info("""
            **Interpretación NT-proBNP (HFA/ESC 2019):**
            * **Escenario Agudo (Urgencias):**
                * < 50 años: > 450 pg/mL
                * 50-75 años: > 900 pg/mL
                * > 75 años: > 1800 pg/mL
            * **Escenario Crónico (Ambulatorio):** > 125 pg/mL
            * **Alto Valor Predictivo Negativo** para descartar falla cardíaca.
            """)
        else:
            st.info("""
            **Interpretación BNP:**
            * **Escenario Agudo:** > 400 pg/mL (Alta probabilidad). < 100 pg/mL (Descarta).
            * **Escenario Crónico:** > 35 pg/mL.
            * *Nota: El uso de Sacubitrilo/Valsartán eleva el BNP, no el NT-proBNP.*
            """)

# --- 7. CÁLCULOS Y LOGICA ---
pam = pad + (pas - pad)/3
pp = pas - pad
ppp = (pp / pas) * 100 if pas > 0 else 0
fenotipo_msg = calcular_fenotipo_fevi(fevi) if tiene_paraclinicos else "No determinado (Requiere Eco)"

# Score Congestión (Eje X)
score_congest = 0
if "Ortopnea" in sintomas: score_congest += 3
if "reposo" in str(sintomas): score_congest += 4
if "Disnea Paroxística Nocturna" in sintomas: score_congest += 3
if iy_presente == "Presente": score_congest += 4
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

if "Vómito" in sintomas or "Diarrea" in sintomas or "Sangrado" in sintomas:
    score_congest -= 3 # Pérdidas reducen congestión aparente

pcp_sim = 12 + score_congest
if pcp_sim > 38: pcp_sim = 38 
if pcp_sim < 5: pcp_sim = 5 

# Score Perfusión (Eje Y)
score_perf = 2.8
if ppp < 25: score_perf -= 0.6
if frialdad != "Caliente": score_perf -= 0.6
if llenado > 3: score_perf -= 0.4
if pulsos == "Filiformes": score_perf -= 0.5
if neuro != "Alerta": score_perf -= 0.5
if tiene_paraclinicos and lactato >= 2.0: score_perf -= 0.8

if pam < 65:
    score_perf -= 1.5 # Shock

ic_sim = max(1.0, score_perf) 

# Clasificación Stevenson
if pcp_sim > 18 and ic_sim > 2.2: cuadrante = "B: Húmedo y Caliente"
elif pcp_sim > 18 and ic_sim <= 2.2: cuadrante = "C: Húmedo y Frío"
elif pcp_sim <= 18 and ic_sim <= 2.2: cuadrante = "L: Seco y Frío"
else: cuadrante = "A: Seco y Caliente"

# --- 8. PANEL PRINCIPAL ---
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
        if "Vómito" in sintomas or "Diarrea" in sintomas: hallazgos.append("Pérdidas GI")
        if iy_presente == "Presente": hallazgos.append(f"IY ({iy_desc})")
        st.markdown(", ".join(hallazgos) if hallazgos else "Sin hallazgos mayores.")

# GENERAR PDF
if st.button("📥 Descargar Resumen del Caso (PDF)"):
    pdf = PDF()
    pdf.add_page()
    pdf.chapter_title("1. Datos del Paciente")
    pdf.chapter_body(f"Edad: {edad} | Sexo: {sexo} | Ciudad: {ciudad} (Riesgo Chagas: {'SI' if es_zona_chagas else 'NO'})")
    pdf.chapter_title("2. Perfil Hemodinámico")
    pdf.chapter_body(f"PA: {pas}/{pad} (PAM {pam:.0f}) | FC: {fc} | SatO2: {sato2}%")
    pdf.chapter_body(f"Cuadrante Stevenson: {cuadrante}")
    pdf.chapter_body(f"PPP: {ppp:.1f}% | Perfusión: {frialdad}")
    pdf.chapter_title("3. Hallazgos Clínicos")
    pdf.chapter_body(f"Ruidos: {ruidos_agregados} | Pulmón: {pulmones}")
    if "Hepato" in abdomen_viscera or ascitis: pdf.chapter_body(f"Abdomen: {abdomen_viscera} {'Ascitis' if ascitis else ''}")
    if iy_presente == "Presente": pdf.chapter_body(f"Cuello: {iy_desc}")
    if tiene_paraclinicos:
        pdf.chapter_body(f"Fenotipo FEVI: {fenotipo_msg} | Lactato: {lactato}")
    
    pdf_output = pdf.output(dest='S').encode('latin-1', 'ignore') 
    st.markdown(create_download_link(pdf_output, "Reporte_HemoSim"), unsafe_allow_html=True)

# TABLERO HEMODINÁMICO
st.markdown("### 📊 Hemodinamia Bedside")
c_m1, c_m2, c_m3, c_m4 = st.columns(4)
c_m1.metric("PAM", f"{pam:.0f} mmHg")
c_m1.caption("Presión de perfusión. < 65 mmHg define Shock.")
c_m2.metric("P. Pulso", f"{pp} mmHg")
c_m2.caption("PAS-PAD. Refleja volumen sistólico.")
c_m3.metric("PPP", f"{ppp:.1f}%", delta="Bajo" if ppp<25 else "OK", delta_color="inverse")
c_m3.caption("Si < 25%, alta probabilidad de IC < 2.2.")
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
        # MENSAJES DOCENTES DINÁMICOS
        if cuadrante.startswith("B"): 
            if pas >= 180 or pad >= 120:
                st.warning("🔥 **Fenotipo Vascular (Crisis HTA):** Redistribución. **Vasodilatador** >> Diurético.")
            else:
                st.success("🫀 **Fenotipo Cardíaco:** Sobrecarga volumen. **Diuréticos** son clave.")
        elif cuadrante.startswith("C"):
            if pas < 90:
                st.error("🚨 **Shock Cardiogénico:** **Vasopresor (Norepi)** inmediato.")
            else:
                st.warning("📉 **Bajo Gasto Normotenso:** **Inotrópicos** + Diuréticos.")
        elif cuadrante.startswith("L"):
            if pas < 90:
                st.error("🩸 **Hipovolemia/Shock:** **Líquidos IV** con cautela -> Vasopresor.")
            else:
                st.info("💧 **Perfil Seco/Frío:** Evaluar **Líquidos IV** (Reto de fluidos).")

# 2. SIMULACIÓN
with tabs[1]:
    st.markdown("### 🧪 Farmacología Aguda")
    st.info("Seleccione intervención para ver vector y **seguridad**.")
    
    cx1, cx2, cx3, cx4, cx5, cx6 = st.columns(6)
    dx, dy = 0, 0
    sel_med = None
    
    with cx1:
        if st.checkbox("Oxígeno / VNI"): 
            dx=0; dy=0; sel_med="oxigeno" # O2 no mueve cuadrante
    with cx2:
        if st.checkbox("Furosemida"): dx-=8; dy+=0.1; sel_med="diureticos" 
    with cx3:
        if st.checkbox("Vasodilatador"): dx-=8; dy+=0.8; sel_med="vasodilatadores" 
    with cx4:
        if st.checkbox("Inotrópico"): dy+=1.5; dx-=2; sel_med="inotropicos" 
    with cx5:
        if st.checkbox("Vasopresor"): dy+=0.3; dx+=1; sel_med="vasopresores" 
    with cx6:
        # CORRECCIÓN VECTORIAL: LÍQUIDOS EN PERFIL L
        # Aumentan Perfusión (Y) sustancialmente por Frank-Starling
        # Aumentan Congestión (X) moderadamente (restauran volemia)
        if st.checkbox("Líquidos IV"): dx+=4; dy+=1.5; sel_med="liquidos" 

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
    st.markdown("Esquema de Titulación GDMT y Monitoreo.")
    gdmt = [
        {"Pilar": "Beta-Bloqueador", "Fármaco": "Succinato de Metoprolol", "Inicio": "12.5-25 mg/d", "Meta": "200 mg c/24h", "Monitoreo": "FC, PA, Fatiga"},
        {"Pilar": "Beta-Bloqueador", "Fármaco": "Carvedilol", "Inicio": "3.125 mg c/12h", "Meta": "25 mg c/12h (>85kg: 50mg)", "Monitoreo": "PA (Ortostatismo)"},
        {"Pilar": "Beta-Bloqueador", "Fármaco": "Bisoprolol", "Inicio": "1.25 mg/d", "Meta": "10 mg c/24h", "Monitoreo": "FC, PA"},
        {"Pilar": "Beta-Bloqueador", "Fármaco": "Nebivolol", "Inicio": "1.25 mg/d", "Meta": "10 mg c/24h", "Monitoreo": "FC, PA (Vasodilatador)"},
        {"Pilar": "ARNI", "Fármaco": "Sacubitrilo/Valsartán", "Inicio": "24/26 mg c/12h", "Meta": "97/103 mg c/12h", "Monitoreo": "K+, Cr, PA"},
        {"Pilar": "ARM", "Fármaco": "Espironolactona", "Inicio": "12.5-25 mg/d", "Meta": "50 mg c/24h", "Monitoreo": "K+ (>5.0 suspender), Cr"},
        {"Pilar": "iSGLT2", "Fármaco": "Dapa/Empagliflozina", "Inicio": "10 mg/d", "Meta": "10 mg c/24h", "Monitoreo": "Higiene genital, Glucosa"},
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





