from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import re
import os

app = Flask(__name__)
CORS(app)

# ========== CARGAR EL JSON (SERVICIOS Y FAQ) ==========
json_path = os.path.join(os.path.dirname(__file__), 'entrenamiento.json')
print(f"📂 Buscando archivo en: {json_path}")

try:
    with open(json_path, 'r', encoding='utf-8') as f:
        entrenamiento = json.load(f)
    print(f"✅ Cargados {len(entrenamiento)} ejemplos de entrenamiento")
except Exception as e:
    print(f"❌ Error al cargar JSON: {e}")
    entrenamiento = []

# ========== RESPUESTAS DE RESPALDO (FALLBACKS) ==========
respuestas_predefinidas = {
    "saludo": "🏨 ¡Hola! Soy Earby, tu asistente del Hotel Rosvel. ¿En qué puedo ayudarte? Pregúntame por precios, tipos de habitación (sencilla/doble/triple/familiar) o disponibilidad.",
    "menu": "🤔 No entendí del todo. Puedo ayudarte con:\n• Precios de habitaciones (Sencilla, Doble, Triple, Familiar)\n• Servicios (Wifi, A/C, Parqueadero, Facturación)\n• Ubicación y atractivos de Palenque.\n\n¿De cuál te gustaría recibir información?",
    "grupos": "¡Claro! Con todo gusto. Para grupos de 5 o más personas, por favor déjenos sus datos (nombre y teléfono) y con todo gusto nos ponemos en contacto para ofrecerles una tarifa especial. 📞 ¡Qué tal!!"
}

PALABRAS_BASURA = {
    'para', 'una', 'uno', 'unos', 'unas', 'de', 'del', 'la', 'el', 'los', 'las', 
    'un', 'con', 'en', 'por', 'que', 'me', 'mi', 'su', 'y', 'o', 'a', 'al', '¿', '?'
}

# ========== NORMALIZACIÓN REFORZADA ==========
def normalizar_texto(texto):
    if not texto:
        return ""
    texto = texto.lower().strip()
    texto = re.sub(r'[áàäâ]', 'a', texto)
    texto = re.sub(r'[éèëê]', 'e', texto)
    texto = re.sub(r'[íìïî]', 'i', texto)
    texto = re.sub(r'[óòöô]', 'o', texto)
    texto = re.sub(r'[úùüû]', 'u', texto)
    texto = re.sub(r'ñ', 'n', texto)
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    return texto

# ========== LÓGICA CENTRALIZADA EN SERVER.PY ==========
def buscar_respuesta(mensaje):
    # 1. Limpieza de las etiquetas automáticas del Frontend
    mensaje_limpio = mensaje.replace("[Buscar Disponibilidad]", "").replace("[buscar disponibilidad]", "")
    
    # 2. Normalización
    mensaje_normalizado = normalizar_texto(mensaje_limpio)
    palabras_usuario = [p for p in mensaje_normalizado.split() if p not in PALABRAS_BASURA]
    
    # -----------------------------------------------------------------
    # CONTROL DE SALUDOS
    # -----------------------------------------------------------------
    saludos = ['hola', 'buenas', 'hola earby', 'hey', 'saludos', 'buen dia', 'buenas tardes', 'buenas noches']
    if mensaje_normalizado in saludos or not palabras_usuario:
        return respuestas_predefinidas["saludo"]

    # -----------------------------------------------------------------
    # CONTROL DE GRUPOS / MUCHAS PERSONAS (5 o más huéspedes)
    # -----------------------------------------------------------------
    if any(p in ['5', '6', '7', '8', '9', '10', 'cinco', 'seis', 'siete', 'ocho', 'nueve', 'diez'] for p in palabras_usuario):
        return respuestas_predefinidas["grupos"]
    if "familia" in palabras_usuario and ("toda" in palabras_usuario or "grande" in palabras_usuario):
        return "¡Claro! Para toda la familia les recomendamos una habitación familiar por $1,200 Pesos por noche. 😊"

    # -----------------------------------------------------------------
    # CONTROL DE HABITACIONES Y SUS COMBINACIONES (Evita confusiones)
    # -----------------------------------------------------------------
    # Variables de detección rápida
    tiene_sencilla = 'sencilla' in palabras_usuario
    tiene_doble = 'doble' in palabras_usuario or 'esposa' in palabras_usuario or 'pareja' in palabras_usuario
    tiene_triple = 'triple' in palabras_usuario
    tiene_familiar = 'familiar' in palabras_usuario
    
    tiene_3_personas = '3' in palabras_usuario or 'tres' in palabras_usuario
    tiene_4_personas = '4' in palabras_usuario or 'cuatro' in palabras_usuario
    tiene_2_personas = '2' in palabras_usuario or 'dos' in palabras_usuario

    # Cruces y conjugaciones complejas detectadas en server
    if tiene_sencilla and (tiene_4_personas or tiene_3_personas):
        return "¡Claro! Para esa cantidad de personas les recomendamos una habitación Familiar por $1,200 Pesos por Noche. 😊"
        
    if tiene_doble and tiene_3_personas:
        return "¡Claro! La tenemos como Triple en $850 MXN por noche. 1 Cama matrimonial + 1 Individual, A/C, estacionamiento gratis. 😊"
        
    if tiene_familiar and tiene_2_personas:
        return "El precio de la familiar es de $1,200, pero para 2 personas está en $980 MXN por noche. Con 2 camas matrimoniales, 28m². 😊"
        
    if tiene_triple and tiene_2_personas:
        return "¡Claro! La triple está en $980 MXN por noche con 1 cama matrimonial + 1 individual. 😊"

    # -----------------------------------------------------------------
    # PRECIOS ESTÁNDAR / MENÚ DE MARCACIÓN RÁPIDA (1, 2, 3, 4)
    # -----------------------------------------------------------------
    if tiene_sencilla or mensaje_normalizado == "1" or palabras_usuario == ['1']:
        return "🏠 Habitación Sencilla: $680 MXN la noche, ¡súper cómoda y con aire acondicionado! Incluye Wi-Fi, baño privado y TV. 🏨"
        
    if tiene_doble or mensaje_normalizado == "2" or palabras_usuario == ['2']:
        return "❤️ Habitación Doble: $850 la noche. 1 Cama Matrimonial para 2 Personas (perfecta para parejas). Si requiere camas separadas, favor de reservar Triple. Incluye aire y parking gratis. 🏨"
        
    if tiene_triple or tiene_3_personas or mensaje_normalizado == "3" or palabras_usuario == ['3']:
        return "👨‍👩‍👧 Habitación Triple: $980 la noche. Con 1 Cama Matrimonial + 1 Cama Individual, Aire Acondicionado, Baño Privado, Pantalla Plana, WIFI, Agua Caliente. 🏨"
        
    if tiene_familiar or tiene_4_personas or mensaje_normalizado == "4" or palabras_usuario == ['4']:
        return "👨‍👩‍👧‍👦 Habitación Familiar: $1,200 la noche con Impuestos Incluidos. Cuenta con 2 camas matrimoniales hasta para 4 personas, A/C, Wi-Fi. 🏨"

    # -----------------------------------------------------------------
    # ===== SISTEMA DE PUNTUACIÓN (SCORING) PARA EL JSON (SERVICIOS) =====
    # -----------------------------------------------------------------
    mejor_respuesta = None
    max_coincidencias = 0

    if entrenamiento:
        for ejemplo in entrenamiento:
            input_json_norm = normalizar_texto(ejemplo.get('input', ''))
            keywords_json = set([p for p in input_json_norm.split() if p not in PALABRAS_BASURA])
            
            coincidencias = 0
            for palabra in palabras_usuario:
                if palabra in keywords_json and len(palabra) >= 2:
                    coincidencias += 1
                    # Bonus para servicios clave del JSON
                    if palabra in ['toallas', 'cafe', 'estacionamiento', 'alberca', 'factura', 'clima', 'aire', 'wifi', 'internet', 'check']:
                        coincidencias += 3

            if coincidencias > max_coincidencias:
                max_coincidencias = coincidencias
                mejor_respuesta = ejemplo.get('output')

    # Si hace match con un servicio del JSON
    if max_coincidencias >= 1 and mejor_respuesta:
        return mejor_respuesta

    # Fallback si no comprende la oración
    return respuestas_predefinidas["menu"]

# ========== RUTAS DE LA API (DOBLE PROTECCIÓN Y FUERZA DE JSON) ==========
@app.route('/api/chat', methods=['POST', 'OPTIONS'])
@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'CORS OK'}), 200

    try:
        data = request.get_json(force=True, silent=True) or {}
        mensaje = data.get('mensaje', '')
        respuesta = buscar_respuesta(mensaje)
        
        print(f"📝 Consulta: {mensaje[:30]} -> Respuesta: {respuesta[:30]}...")
        return jsonify({'respuesta': respuesta})
        
    except Exception as e:
        print(f"❌ Error en la ruta chat: {e}")
        return jsonify({'respuesta': f'Error interno: {str(e)}'})

@app.route('/')
def home():
    return jsonify({
        'status': 'Earby API Funcionando perfectamente',
        'base_datos_json': len(entrenamiento)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)
