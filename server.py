from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import re
import os

app = Flask(__name__)
CORS(app)

# ========== CARGAR EL JSON DE RESPALDO ==========
json_path = os.path.join(os.path.dirname(__file__), 'entrenamiento.json')
print(f"📂 Buscando archivo en: {json_path}")

try:
    with open(json_path, 'r', encoding='utf-8') as f:
        entrenamiento = json.load(f)
    print(f"✅ Cargados {len(entrenamiento)} ejemplos de entrenamiento")
except Exception as e:
    print(f"❌ Error al cargar: {e}")
    entrenamiento = []

# ========== RESPUESTAS PREDEFINIDAS COMPLETAS ==========
respuestas_predefinidas = {
    "saludo": "🏨 ¡Hola! Soy Earby, tu asistente del Hotel Rosvel. ¿En qué puedo ayudarte? Pregúntame por precios, tipos de habitación (sencilla/doble/triple/familiar) o disponibilidad.",
    "1": "🏠 Habitación Sencilla: $680 MXN por noche para 1 persona. Incluye A/C, Wi-Fi, baño privado y TV. ¿Necesitas reservar?",
    "2": "❤️ Habitación Doble: $850 MXN por noche para 2 personas. Cama matrimonial, A/C, Wi-Fi y estacionamiento. ¿Te ayudo a reservar?",
    "3": "👨‍👩‍👧 Habitación Triple: $980 MXN por noche para 3 personas. 1 cama matrimonial + 1 individual, A/C, Wi-Fi.",
    "4": "👨‍👩‍👧‍👦 Habitación Familiar: $1,200 MXN por noche para 4 personas. 2 camas matrimoniales, 28m², A/C, Wi-Fi.",
    "sencilla": "🏠 Habitación Sencilla: $680 MXN por noche para 1 persona. Incluye A/C, Wi-Fi, baño privado y TV.",
    "doble": "❤️ Habitación Doble: $850 MXN por noche para 2 personas. Cama matrimonial, A/C, Wi-Fi y estacionamiento.",
    "triple": "👨‍👩‍👧 Habitación Triple: $980 MXN por noche para 3 personas. 1 cama matrimonial + 1 individual, A/C, Wi-Fi.",
    "familiar": "👨‍👩‍👧‍👦 Habitación Familiar: $1,200 MXN por noche para 4 personas. 2 camas matrimoniales, 28m², A/C, Wi-Fi.",
    "precio": "💰 Precios por noche: Sencilla $680 | Doble $850 | Triple $980 | Familiar $1,200 MXN. ¡25% OFF con código NUEVO2631!",
    "cancelar": "✅ Cancelación GRATIS con 24 horas de anticipación. Sin penalización.",
    "ubicacion": "📍 A 600 metros de la estación del Tren Maya en Palenque, Chiapas.",
    "estacionamiento": "🅿️ Estacionamiento gratuito en vía pública (privado bajo solicitud).",
    "wifi": "📡 Wi-Fi de alta velocidad gratis en TODAS las habitaciones.",
    "descuento": "🎁 Código NUEVO2631 para 25% DE DESCUENTO en reserva directa.",
    "whatsapp": "📞 WhatsApp: +52 938 183 4220. ¡Respondemos en minutos!",
    "horario": "⏰ Check-in: 15:00 hrs | Check-out: 12:00 hrs. Guardamos maletas.",
    "mascotas": "🐕 Consulta disponibilidad para mascotas. Llámanos al +52 938 183 4220.",
    "clima": "❄️ ¡Claro que sí! Clima y A/C son lo mismo. Todas las habitaciones tienen aire acondicionado individual. ¡No inventes, está bien fresco!",
    "amenidades": "🧼 ¡Sí! Incluimos jabón, shampoo, rastrillo, navaja de afeitar, papel higiénico y WC. ¡Todo para que te sientas como en casa! ¡Qué tal!!",
    "colcha": "🛏️ ¡Sí! Todas las habitaciones incluyen colcha y ropa de cama completa, súper cómoda y limpia.",
    "cama_baja": "🛌 ¡Sí! Podemos darte una cama baja si la pides en recepción. ¡Dale, sin problema!",
    "medicamentos": "💊 Uy, lo siento. No tenemos medicamentos. ¡Puff! Hay una farmacia bien cerca. ¿Te ayudo con la dirección?",
    "grupo": "📞 ¡Claro! Con todo gusto. Déjanos tus datos y nos ponemos en contacto. ¡Qué tal!!",
    "accesibilidad": "♿ ¡Claro que sí! Tenemos habitaciones en planta baja, sin barreras. ¡Con todo gusto te ayudamos!",
    "comida": "☕ Uy, todavía no tenemos restaurante. ¡Pero! Te ofrecemos un cafecito por la mañana y te sugerimos restaurantes buenísimos bien cerca.",
    "alberca": "🌊 Puff, ya no tenemos alberca. ¡Pero! Palenque tiene 18 cascadas bien chidas para nadar. ¿Te gustan las cascadas?",
    "baño": "🚽 Todas nuestras habitaciones tienen baño privado completo: WC, regadera con agua caliente, espejo y tocador amplio.",
    "fumar": "🚭 No se permite fumar dentro de las habitaciones. Puedes fumar en la terraza o áreas exteriores.",
    "microondas": "🔥 No tenemos estufa, pero ¡sí! Tenemos microondas disponible en recepción para calentar tus alimentos.",
    "toallas": "🧺 Toallas de baño y manos incluidas. Puedes pedir extras en recepción sin costo.",
    "agua": "💧 Agua caliente disponible 24/7 en todas las habitaciones.",
    "tv": "📺 TV con 50+ canales de cable, incluido en todas las habitaciones.",
    "tours": "🗺️ Tenemos convenio con agencias locales. Tours a Cascadas Roberto Barrios, Welib Ha y Zona Arqueológica.",
    "factura": "📄 Sí, facturamos con RFC y uso de CFDI. Solicítala en recepción antes del check-out."
}

def normalizar_texto(texto):
    """Limpia tildes y caracteres para que las búsquedas no fallen por acentos"""
    texto = texto.lower().strip()
    texto = re.sub(r'[á]', 'a', texto)
    texto = re.sub(r'[é]', 'e', texto)
    texto = re.sub(r'[í]', 'i', texto)
    texto = re.sub(r'[ó]', 'o', texto)
    texto = re.sub(r'[úü]', 'u', texto)
    texto = re.sub(r'[ñ]', 'n', texto)
    return texto

def buscar_respuesta(mensaje):
    mensaje_limpio = normalizar_texto(mensaje)
    
    # 1. Saludos Exactos
    if mensaje_limpio in ['hola', 'buenas', 'hola earby', 'hey', 'saludos', 'buen dia', 'buenas tardes', 'buenas noches']:
        return respuestas_predefinidas["saludo"]
    
    # 2. Números sueltos
    if mensaje_limpio in ["1", "2", "3", "4"]:
        return respuestas_predefinidas[mensaje_limpio]
    
    # 3. Mapeo de Palabras Clave (COMPLETO y arreglado para evitar choques)
    clave_respuesta = {
        "clima": [r"\bclima\b", r"\baire\b", r"\bac\b", r"\baire acondicionado\b", r"\bfresco\b", r"\bcalor\b"],
        "amenidades": [r"\bjabon\b", r"\bshampoo\b", r"\brastrillo\b", r"\bnavaja\b", r"\bpapel\b", r"\bwc\b", r"\bsanitario\b"],
        "colcha": [r"\bcolcha\b", r"\bcobija\b", r"\bsabanas\b", r"\bropa de cama\b"],
        "cama_baja": [r"\bcama baja\b", r"\bbajo de manda\b", r"\bcama a nivel\b"],
        "medicamentos": [r"\bmedicamento\b", r"\bmedicamentos\b", r"\baspirina\b", r"\bbotiquin\b", r"\bpastilla\b"],
        "grupo": [r"\bgroup\b", r"\bgrupo\b", r"\bpersonas\b"],
        "accesibilidad": [r"\bsilla ruedas\b", r"\bdiscapacidad\b", r"\bmuletas\b", r"\bplanta baja\b"],
        "comida": [r"\bdesayuno\b", r"\bcomida\b", r"\brestaurante\b", r"\bcafe\b", r"\bcafecito\b"],
        "alberca": [r"\balberca\b", r"\bpiscina\b", r"\bjacuzzi\b", r"\bpileta\b"],
        "baño": [r"\bregadera\b", r"\bespejo\b", r"\btocador\b", r"\bducha\b"],
        "fumar": [r"\bfumar\b", r"\bcigarro\b", r"\btabaco\b", r"\bvape\b"],
        "microondas": [r"\bmicroondas\b", r"\bcocinar\b", r"\bcalentar\b", r"\bestufa\b"],
        "toallas": [r"\btoalla\b", r"\btoallas\b"],
        "agua": [r"\bagua caliente\b", r"\bagua fria\b", r"\bboiler\b"],
        "tv": [r"\btv\b", r"\btelevision\b", r"\bcanales\b", r"\bcable\b"],
        "tours": [r"\btour\b", r"\btours\b", r"\bcascadas\b", r"\bruinas\b", r"\bexcursion\b"],
        "factura": [r"\bfactura\b", r"\bfacturar\b", r"\bcfdi\b", r"\brfc\b"],
        # Agregamos las que faltaban en tu lista original:
        "precio": [r"\bprecio\b", r"\bprecios\b", r"\bcosto\b", r"\bcuanto cuesta\b", r"\btarifas\b", r"\btarifa\b"],
        "descuento": [r"\bdescuento\b", r"\bdescuentos\b", r"\bpromocion\b", r"\bcodigo\b"],
        "horario": [r"\bhorario\b", r"\bhorarios\b", r"\bcheckin\b", r"\bcheckout\b", r"\bhora\b"],
        "ubicacion": [r"\bubicacion\b", r"\bdireccion\b", r"\bdonde estan\b", r"\bdonde queda\b", r"\btren maya\b"],
        "estacionamiento": [r"\bestacionamiento\b", r"\bparking\b", r"\bcochera\b"],
        "wifi": [r"\bwifi\b", r"\binternet\b", r"\bconexion\b"]
    }
    
    # Búsqueda inteligente usando expresiones regulares (Evita que "ac" rompa "estacionamiento")
    for clave, patrones in clave_respuesta.items():
        for patron in patrones:
            if re.search(patron, mensaje_limpio):
                return respuestas_predefinidas.get(clave, respuestas_predefinidas["saludo"])
                
    # 4. Detectar números embebidos en frases
    if re.search(r'\b1\b|uno|una persona|individual|solo', mensaje_limpio):
        return respuestas_predefinidas["1"]
    if re.search(r'\b2\b|dos|pareja|matrimonial|esposa|esposo', mensaje_limpio):
        return respuestas_predefinidas["2"]
    if re.search(r'\b3\b|tres|triple', mensaje_limpio):
        return respuestas_predefinidas["3"]
    if re.search(r'\b4\b|cuatro|familiar|familia', mensaje_limpio):
        return respuestas_predefinidas["4"]
    
    # 5. RESPALDO ABSOLUTO: Buscar en el archivo JSON si no cayó en las anteriores
    if entrenamiento:
        mejor_match = None
        max_coincidencias = 0
        palabras_mensaje = mensaje_limpio.split()
        
        for ejemplo in entrenamiento:
            input_text = normalizar_texto(ejemplo.get('input', ''))
            coincidencias = 0
            
            for palabra in palabras_mensaje:
                if len(palabra) >= 3 and palabra in input_text:
                    coincidencias += 1
            
            if coincidencias > max_coincidencias and coincidencias >= 1:
                max_coincidencias = coincidencias
                mejor_match = ejemplo
        
        if mejor_match:
            respuestas = mejor_match.get('output', {}).get('respuestas_sugeridas', [])
            for r in respuestas:
                if r.get('tono') == 'amigable':
                    return r.get('texto')
            if respuestas:
                return respuestas[0].get('texto')
    
    # 6. Mensaje por defecto si de verdad nada de nada hizo match
    return respuestas_predefinidas["saludo"]

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        mensaje = data.get('mensaje', '')
        respuesta = buscar_respuesta(mensaje)
        return jsonify({'respuesta': respuesta})
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'respuesta': f'Error interno: {str(e)}'})

@app.route('/')
def home():
    return jsonify({'status': 'Earby API funcionando perfectamente', 'ejemplos_json': len(entrenamiento)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
