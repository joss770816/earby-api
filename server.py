from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import re
import os

app = Flask(__name__)
CORS(app)

# Cargar los ejemplos de entrenamiento
json_path = os.path.join(os.path.dirname(__file__), 'entrenamiento.json')
print(f"📂 Buscando archivo en: {json_path}")

try:
    with open(json_path, 'r', encoding='utf-8') as f:
        entrenamiento = json.load(f)
    print(f"✅ Cargados {len(entrenamiento)} ejemplos de entrenamiento")
except Exception as e:
    print(f"❌ Error al cargar: {e}")
    entrenamiento = []

# ========== RESPUESTAS PREDEFINIDAS (SOLO LAS ESENCIALES) ==========
respuestas_predefinidas = {
    "saludo": "🏨 ¡Hola! Soy Earby, tu asistente del Hotel Rosvel. ¿En qué puedo ayudarte? Pregúntame por precios, tipos de habitación (sencilla/doble/triple/familiar) o disponibilidad.",
    "1": "🏠 Habitación Sencilla: $680 MXN por noche para 1 persona. Incluye A/C, Wi-Fi, baño privado y TV. ¿Necesitas reservar?",
    "2": "❤️ Habitación Doble: $850 MXN por noche para 2 personas. Cama matrimonial, A/C, Wi-Fi y estacionamiento. ¿Te ayudo a reservar?",
    "3": "👨‍👩‍👧 Habitación Triple: $980 MXN por noche para 3 personas. 1 cama matrimonial + 1 individual, A/C, Wi-Fi.",
    "4": "👨‍👩‍👧‍👦 Habitación Familiar: $1,200 MXN por noche para 4 personas. 2 camas matrimoniales, 28m², A/C, Wi-Fi.",
}

def buscar_respuesta(mensaje):
    mensaje = mensaje.lower().strip()
    
    # ========== 1. REGLAS DURAS (SOLO LAS ESENCIALES) ==========
    
    # Saludos
    if mensaje in ['hola', 'buenas', 'hola earby', 'hey', 'saludos', 'buen día', 'buenas tardes', 'buenas noches']:
        return respuestas_predefinidas["saludo"]
    
    # Números sueltos
    if mensaje in ["1", "2", "3", "4"]:
        return respuestas_predefinidas[mensaje]
    
    # ========== 2. BUSCAR EN EL JSON (PRIORIDAD) ==========
    mejor_match = None
    max_coincidencias = 0
    
    # Extraer palabras clave de la pregunta
    palabras_pregunta = re.findall(r'[a-záéíóúñ]+', mensaje)
    palabras_clave = [p for p in palabras_pregunta if len(p) > 2]
    
    # Si no hay palabras, usar la pregunta completa
    if not palabras_clave:
        palabras_clave = [mensaje]
    
    # Buscar en cada ejemplo del JSON
    for ejemplo in entrenamiento:
        input_text = ejemplo.get('input', '').lower()
        coincidencias = 0
        
        # Contar cuántas palabras clave están en el input
        for palabra in palabras_clave:
            if palabra in input_text:
                coincidencias += 1
        
        # Si encuentra coincidencias, actualizar el mejor match
        if coincidencias > max_coincidencias:
            max_coincidencias = coincidencias
            mejor_match = ejemplo
    
    # Si encontramos un buen match (al menos 1 palabra clave)
    if mejor_match and max_coincidencias >= 1:
        respuestas = mejor_match.get('output', {}).get('respuestas_sugeridas', [])
        
        # Buscar respuesta con tono 'amigable' primero
        for r in respuestas:
            if r.get('tono') == 'amigable':
                return r.get('texto')
        
        # Si no hay 'amigable', devolver la primera
        if respuestas:
            return respuestas[0].get('texto')
    
    # ========== 3. SI NADA FUNCIONA ==========
    return "🤔 No entendí tu consulta. Puedo ayudarte con:\n• Precios: escribe 1,2,3,4\n• Servicios: wifi, estacionamiento, cancelación\n• Ubicación, descuentos, horarios\n• Amenidades: jabón, shampoo, toallas\n• Contacto: WhatsApp +52 938 183 4220\n\n¿Qué necesitas saber?"

# ========== RUTAS DE LA API ==========
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        mensaje = data.get('mensaje', '')
        respuesta = buscar_respuesta(mensaje)
        print(f"📝 Pregunta: {mensaje[:50]}...")
        return jsonify({'respuesta': respuesta})
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'respuesta': f'Error: {str(e)}'})

@app.route('/')
def home():
    return jsonify({
        'status': 'Earby API funcionando',
        'ejemplos': len(entrenamiento),
        'modelo': 'Basado en entrenamiento.json'
    })

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Earby API - Hotel Rosvel (Versión con JSON Prioritario)")
    print(f"📊 Entrenamiento: {len(entrenamiento)} ejemplos")
    print("=" * 50)
    app.run(host='0.0.0.0', port=10000, debug=False)
