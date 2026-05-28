from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import re
import os

app = Flask(__name__)
CORS(app)

# Cargar el archivo de entrenamiento
json_path = os.path.join(os.path.dirname(__file__), 'entrenamiento.json')
print(f"📂 Buscando: {json_path}")

try:
    with open(json_path, 'r', encoding='utf-8') as f:
        entrenamiento = json.load(f)
    print(f"✅ Cargados {len(entrenamiento)} ejemplos de entrenamiento")
except FileNotFoundError:
    print("❌ No se encontró entrenamiento.json, usando respuestas básicas")
    entrenamiento = []
except Exception as e:
    print(f"❌ Error: {e}")
    entrenamiento = []

# Respuestas predefinidas de respaldo
respuestas_base = {
    "hola": "🏨 ¡Hola! Soy Earby, asistente del Hotel Rosvel. ¿En qué puedo ayudarte?",
    "1": "🏠 Habitación Sencilla: $680 MXN/noche para 1 persona. Incluye A/C, Wi-Fi, baño privado.",
    "2": "❤️ Habitación Doble: $850 MXN/noche para 2 personas. Cama matrimonial, A/C, estacionamiento.",
    "3": "👨‍👩‍👧 Habitación Triple: $980 MXN/noche para 3 personas. 1 cama matrimonial + 1 individual.",
    "4": "👨‍👩‍👧‍👦 Habitación Familiar: $1,200 MXN/noche para 4 personas. 2 camas matrimoniales.",
    "precio": "💰 Precios: Sencilla $680 | Doble $850 | Triple $980 | Familiar $1,200 MXN/noche",
    "cancelar": "✅ Cancelación GRATIS con 24 horas de anticipación.",
    "ubicacion": "📍 A 600 metros de la estación del Tren Maya en Palenque, Chiapas.",
    "wifi": "📡 Wi-Fi de alta velocidad gratis en todas las habitaciones.",
    "estacionamiento": "🅿️ Estacionamiento gratuito en vía pública (privado bajo solicitud).",
    "descuento": "🎁 Código NUEVO2631 para 25% DE DESCUENTO en reserva directa.",
    "whatsapp": "📞 WhatsApp: +52 938 183 4220. Respondemos en minutos.",
    "alberca": "🌊 Ya no tenemos alberca. ¡Palenque tiene 18 cascadas para disfrutar!",
    "desayuno": "☕ Ofrecemos café por la mañana. ¡Hay restaurantes ricos a 2 minutos!"
}

def buscar_respuesta(mensaje):
    msg_lower = mensaje.lower().strip()
    
    # Saludos
    if msg_lower in ["hola", "buenas", "hey", "hola earby", "saludos"]:
        return respuestas_base["hola"]
    
    # Números sueltos
    if msg_lower == "1":
        return respuestas_base["1"]
    if msg_lower == "2":
        return respuestas_base["2"]
    if msg_lower == "3":
        return respuestas_base["3"]
    if msg_lower == "4":
        return respuestas_base["4"]
    
    # Buscar palabras clave
    for clave, respuesta in respuestas_base.items():
        if clave in msg_lower and clave not in ["1","2","3","4","hola"]:
            return respuesta
    
    # Buscar en el entrenamiento JSON
    if entrenamiento:
        for ejemplo in entrenamiento:
            input_text = ejemplo.get('input', '').lower()
            if input_text in msg_lower or msg_lower in input_text:
                respuestas = ejemplo.get('output', {}).get('respuestas_sugeridas', [])
                for r in respuestas:
                    if r.get('tono') == 'amigable':
                        return r.get('texto')
                if respuestas:
                    return respuestas[0].get('texto')
    
    # Si no encuentra nada
    return "🤔 ¿Puedes reformular? Pregúntame por precios (1,2,3,4), cancelación, ubicación, descuentos o envíame un WhatsApp al +52 938 183 4220"

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        mensaje = data.get('mensaje', '')
        respuesta = buscar_respuesta(mensaje)
        print(f"📝 Pregunta: {mensaje} -> Respuesta enviada")
        return jsonify({'respuesta': respuesta})
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'respuesta': 'Error del servidor. Escríbenos a WhatsApp +52 938 183 4220'})

@app.route('/')
def home():
    return jsonify({'status': 'Earby API funcionando', 'ejemplos': len(entrenamiento)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)