from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import re
import os

app = Flask(__name__)
CORS(app)

# ========== CARGAR EL JSON (SÚPER DIRECTO Y LIGERO) ==========
json_path = os.path.join(os.path.dirname(__file__), 'entrenamiento.json')
print(f"📂 Buscando archivo en: {json_path}")

try:
    with open(json_path, 'r', encoding='utf-8') as f:
        entrenamiento = json.load(f)
    print(f"✅ Cargados {len(entrenamiento)} ejemplos de entrenamiento")
except Exception as e:
    print(f"❌ Error al cargar JSON: {e}")
    entrenamiento = []

# ========== RESPUESTAS HARDCODEADAS EN MEMORIA POR SEGURIDAD ==========
respuestas_predefinidas = {
    "saludo": "🏨 ¡Hola! Soy Earby, tu asistente del Hotel Rosvel. ¿En qué puedo ayudarte? Pregúntame por precios, tipos de habitación (sencilla/doble/triple/familiar) o disponibilidad.",
    "1": "🏠 Habitación Sencilla: $680 MXN por noche para 1 persona. Incluye A/C, Wi-Fi, baño privado y TV. ¿Necesitas reservar?",
    "2": "❤️ Habitación Doble: $850 MXN por noche para 2 personas. Cama matrimonial, A/C, Wi-Fi y estacionamiento. ¿Te ayudo a reservar?",
    "3": "👨‍👩‍👧 Habitación Triple: $980 MXN por noche para 3 personas. 1 cama matrimonial + 1 individual, A/C, Wi-Fi.",
    "4": "👨‍👩‍👧‍👦 Habitación Familiar: $1,200 MXN por noche para 4 personas. 2 camas matrimoniales, 28m², A/C, Wi-Fi."
}

# ========== NORMALIZACIÓN REFORZADA ==========
def normalizar_texto(texto):
    """Elimina tildes, signos, y normaliza para comparación limpia"""
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

# ========== FUNCIÓN DE BÚSQUEDA POR PALABRAS CLAVE ==========
def buscar_respuesta(mensaje):
    mensaje_normalizado = normalizar_texto(mensaje)
    palabras_usuario = mensaje_normalizado.split()
    
    if not palabras_usuario:
        return respuestas_predefinidas["saludo"]

    # ===== 1. MÁXIMA PRIORIDAD: ESCANEAR EL JSON SIN .GET() COMPLEJOS =====
    if entrenamiento:
        for ejemplo in entrenamiento:
            # Separamos en palabras clave el "input" del JSON
            keywords_json = set(normalizar_texto(ejemplo.get('input', '')).split())
            
            # Si el usuario escribe una palabra exacta del JSON de más de 2 letras, disparamos
            for palabra in palabras_usuario:
                if palabra in keywords_json and len(palabra) >= 2:
                    # Retornamos el string directo que guardamos con el script limpiador
                    return ejemplo.get('output', respuestas_predefinidas["saludo"])

    # ===== 2. SEGUNDA PRIORIDAD: SALUDOS EXACTOS =====
    if mensaje_normalizado in ['hola', 'buenas', 'hola earby', 'hey', 'saludos', 'buen dia', 'buenas tardes', 'buenas noches']:
        return respuestas_predefinidas["saludo"]
    
    # Números del menú de marcación rápida
    if mensaje_normalizado == "1":
        return respuestas_predefinidas["1"]
    if mensaje_normalizado == "2":
        return respuestas_predefinidas["2"]
    if mensaje_normalizado == "3":
        return respuestas_predefinidas["3"]
    if mensaje_normalizado == "4":
        return respuestas_predefinidas["4"]
    
    # ===== 3. RESPUESTA POR DEFECTO (FALLBACK) =====
    return respuestas_predefinidas["saludo"]

# ========== RUTAS DE LA API (DOBLE PROTECCIÓN) ==========
@app.route('/api/chat', methods=['POST', 'OPTIONS'])
@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    try:
        data = request.json or {}
        mensaje = data.get('mensaje', '')
        respuesta = buscar_respuesta(mensaje)
        print(f"📝 Consulta: {mensaje[:30]} -> Respuesta: {respuesta[:30]}...")
        return jsonify({'respuesta': respuesta})
    except Exception as e:
        print(f"❌ Error crítico en ruta chat: {e}")
        return jsonify({'respuesta': f'Error interno en el servidor: {str(e)}'})

@app.route('/')
def home():
    return jsonify({
        'status': 'Earby API Funcionando perfectamente',
        'preguntas_cargadas_json': len(entrenamiento)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)
