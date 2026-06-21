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

# ========== RESPUESTAS DE RESPALDO (FALLBACKS) ==========
respuestas_predefinidas = {
    "saludo": "🏨 ¡Hola! Soy Earby, tu asistente del Hotel Rosvel. ¿En qué puedo ayudarte? Pregúntame por precios, tipos de habitación (sencilla/doble/triple/familiar) o disponibilidad.",
    "menu": "🤔 No entendí del todo. Puedo ayudarte con:\n• Precios de habitaciones (Sencilla, Doble, Triple, Familiar)\n• Servicios (Wifi, A/C, Parqueadero, Facturación)\n• Ubicación y atractivos de Palenque.\n\n¿De cuál te gustaría recibir información?"
}

# Palabras comunes que no aportan significado y causaban falsos positivos
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

# ========== FUNCIÓN DE BÚSQUEDA INTELIGENTE CON SCORING ==========
def buscar_respuesta(mensaje):
    mensaje_normalizado = normalizar_texto(mensaje)
    palabras_usuario = [p for p in mensaje_normalizado.split() if p not in PALABRAS_BASURA]
    
    # Si el usuario solo envía un número suelto (Menú rápido de marcación)
    if mensaje_normalizado == "1" or (len(palabras_usuario) == 1 and palabras_usuario[0] == "1"):
        return "🏠 Habitación Sencilla: $680 MXN por noche para 1 persona. Incluye A/C, Wi-Fi, baño privado y TV. ¿Necesitas reservar?"
    if mensaje_normalizado == "2" or (len(palabras_usuario) == 1 and palabras_usuario[0] == "2"):
        return "❤️ Habitación Doble: $850 MXN por noche para 2 personas. Cama matrimonial, A/C, Wi-Fi y estacionamiento. ¿Te ayudo a reservar?"
    if mensaje_normalizado == "3" or (len(palabras_usuario) == 1 and palabras_usuario[0] == "3"):
        return "👨‍👩‍👧 Habitación Triple: $980 MXN por noche para 3 personas. 1 cama matrimonial + 1 individual, A/C, Wi-Fi. ¿Te interesa?"
    if mensaje_normalizado == "4" or (len(palabras_usuario) == 1 and palabras_usuario[0] == "4"):
        return "👨‍👩‍👧‍👦 Habitación Familiar: $1,200 MXN por noche para 4 personas. 2 camas matrimoniales, A/C, Wi-Fi."

    # Si está vacío, le mandamos el saludo cordial
    if not palabras_usuario:
        return respuestas_predefinidas["saludo"]

    # Saludos directos rápidos
    if mensaje_normalizado in ['hola', 'buenas', 'hola earby', 'hey', 'saludos', 'buen dia', 'buenas tardes', 'buenas noches']:
        return respuestas_predefinidas["saludo"]

    mejor_respuesta = None
    max_coincidencias = 0

    # ===== SISTEMA DE PUNTUACIÓN (SCORING) =====
    if entrenamiento:
        for ejemplo in entrenamiento:
            input_json_norm = normalizar_texto(ejemplo.get('input', ''))
            keywords_json = set([p for p in input_json_norm.split() if p not in PALABRAS_BASURA])
            
            # Contamos cuántas palabras importantes del usuario cruzan con este renglón del JSON
            coincidencias = 0
            for palabra in palabras_usuario:
                if palabra in keywords_json and len(palabra) >= 2:
                    coincidencias += 1
                    # Súper bonus: Si el cliente busca una categoría específica (ej. "doble", "triple", "familiar", "toallas") 
                    # y este renglón contiene exactamente esa palabra clave, le subimos la puntuación para evitar desvíos.
                    if palabra in ['sencilla', 'doble', 'triple', 'familiar', 'toallas', 'cafe', 'estacionamiento', 'alberca', 'factura']:
                        coincidencias += 2

            # Si este ejemplo supera al anterior campeón de puntos, se vuelve la mejor respuesta
            if coincidencias > max_coincidencias:
                max_coincidencias = coincidencias
                mejor_respuesta = ejemplo.get('output')

    # Si encontramos una respuesta con buena puntuación (al menos 1 match real de palabra importante)
    if max_coincidencias > 0 and mejor_respuesta:
        return mejor_respuesta

    # ===== 3. RESPUESTA POR DEFECTO (FALLBACK) =====
    return respuestas_predefinidas["menu"]

# ========== RUTAS DE LA API (DOBLE PROTECCIÓN) ==========
# ========== RUTAS DE LA API (DOBLE PROTECCIÓN Y FUERZA DE JSON) ==========
@app.route('/api/chat', methods=['POST', 'OPTIONS'])
@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    # Si es una petición de control CORS (OPTIONS), respondemos rápido 200 OK
    if request.method == 'OPTIONS':
        return jsonify({'status': 'CORS OK'}), 200

    try:
        # Usamos force=True y silent=True para que Flask extraiga el JSON 
        # sin importar si el Content-Type viene vacío desde Hostinger
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
