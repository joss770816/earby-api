from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import re
import os

app = Flask(__name__)
CORS(app)

# ========== CARGAR EL JSON ==========
json_path = os.path.join(os.path.dirname(__file__), 'entrenamiento.json')
print(f"📂 Buscando archivo en: {json_path}")

try:
    with open(json_path, 'r', encoding='utf-8') as f:
        entrenamiento = json.load(f)
    print(f"✅ Cargados {len(entrenamiento)} ejemplos de entrenamiento")
except Exception as e:
    print(f"❌ Error al cargar JSON: {e}")
    entrenamiento = []

# ========== NORMALIZACIÓN REFORZADA ==========
def normalizar_texto(texto):
    """Elimina tildes, signos, y normaliza para comparación limpia"""
    if not texto:
        return ""
    texto = texto.lower().strip()
    # Reemplazar tildes recurrentes
    texto = re.sub(r'[áàäâ]', 'a', texto)
    texto = re.sub(r'[éèëê]', 'e', texto)
    texto = re.sub(r'[íìïî]', 'i', texto)
    texto = re.sub(r'[óòöô]', 'o', texto)
    texto = re.sub(r'[úùüû]', 'u', texto)
    texto = re.sub(r'ñ', 'n', texto)
    # Quitar signos de puntuación e interrogación
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    return texto

# ========== FUNCIÓN DE BÚSQUEDA POR CONTENIDO ==========
def buscar_respuesta(mensaje):
    mensaje_normalizado = normalizar_texto(mensaje)
    palabras_usuario = mensaje_normalizado.split()
    
    if not palabras_usuario:
        return "🤔 No enviaste ningún mensaje, tío."

    # ===== 1. MÁXIMA PRIORIDAD: RECORRER EL JSON DE ENTRENAMIENTO =====
    if entrenamiento:
        for ejemplo in entrenamiento:
            # Normalizamos las palabras clave del bloque del JSON
            keywords_json = normalizar_texto(ejemplo.get('input', '')).split()
            
            # Verificamos si alguna palabra del usuario hace match exacto con las keywords
            for palabra in palabras_usuario:
                if palabra in keywords_json and len(palabra) >= 2: # Evita falsos positivos con letras de 1 carácter
                    respuestas = ejemplo.get('output', {}).get('respuestas_sugeridas', [])
                    
                    # Detectar el tono solicitado
                    if re.search(r'urgen|prisa|ahora|ya', mensaje_normalizado):
                        tono = 'urgente'
                    elif re.search(r'comprar|reservar|costo|precio|pagar', mensaje_normalizado):
                        tono = 'formal'
                    else:
                        tono = 'amigable'
                    
                    # Buscar la respuesta que coincida con el tono
                    for r in respuestas:
                        if r.get('tono') == tono:
                            return r.get('texto')
                    
                    # Respaldo: si no hay match de tono, regresa la primera disponible
                    if respuestas:
                        return respuestas[0].get('texto')

    # ===== 2. SEGUNDA PRIORIDAD: SALUDOS HARDCODEADOS =====
    if mensaje_normalizado in ['hola', 'buenas', 'hola earby', 'hey', 'saludos', 'buen dia', 'buenas tardes', 'buenas noches']:
        return "🏨 ¡Hola! Soy Earby, tu asistente del Hotel Rosvel. ¿En qué puedo ayudarte? Pregúntame por precios, tipos de habitación (sencilla/doble/triple/familiar) o disponibilidad."
    
    # Números sueltos del menú
    if mensaje_normalizado == "1":
        return "🏠 Habitación Sencilla: $680 MXN por noche para 1 persona. Incluye A/C, Wi-Fi, baño privado y TV. ¿Necesitas reservar?"
    if mensaje_normalizado == "2":
        return "❤️ Habitación Doble: $850 MXN por noche para 2 personas. Cama matrimonial, A/C, Wi-Fi y estacionamiento. ¿Te ayudo a reservar?"
    if mensaje_normalizado == "3":
        return "👨‍wohn Habitación Triple: $980 MXN por noche para 3 personas. 1 cama matrimonial + 1 individual, A/C, Wi-Fi."
    if mensaje_normalizado == "4":
        return "👨‍👩‍👧‍👦 Habitación Familiar: $1,200 MXN por noche para 4 personas. 2 camas matrimoniales, 28m², A/C, Wi-Fi."
    
    # ===== 3. RESPUESTA POR DEFECTO (FALLBACK) =====
    return "🤔 No entendí tu consulta. Puedo ayudarte con:\n• Precios: escribe 1, 2, 3, 4\n• Servicios: wifi, aire acondicionado, factura, estacionamiento\n• Ubicación: Tren Maya\n\n¿De qué te gustaría recibir información?"

# ========== RUTAS DE LA API ==========
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json or {}
        mensaje = data.get('mensaje', '')
        respuesta = buscar_respuesta(mensaje)
        print(f"📝 Consulta: {mensaje} -> Respuesta: {respuesta[:30]}...")
        return jsonify({'respuesta': respuesta})
    except Exception as e:
        print(f"❌ Error en la ruta /api/chat: {e}")
        return jsonify({'respuesta': f'Error interno: {str(e)}'})

@app.route('/')
def home():
    return jsonify({
        'status': 'Earby API Funcionando perfectamente',
        'base_datos_json': len(entrenamiento)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)
