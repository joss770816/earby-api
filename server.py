from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import re
import os
import random

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

# ========== FUNCIÓN DE BÚSQUEDA MEJORADA ==========
def buscar_respuesta(mensaje):
    """Busca la mejor respuesta en el archivo de entrenamiento"""
    mensaje_original = mensaje
    mensaje = mensaje.lower().strip()
    
    # 1. Saludos rápidos (no están en el JSON)
    if mensaje in ['hola', 'buenas', 'hola earby', 'hey', 'saludos', 'buen día', 'buenas tardes', 'buenas noches']:
        return "🏨 ¡Hola! Soy Earby, tu asistente del Hotel Rosvel. ¿En qué puedo ayudarte? Pregúntame por precios, tipos de habitación (sencilla/doble/triple/familiar) o disponibilidad."
    
    # 2. Buscar en el archivo de entrenamiento
    mejor_match = None
    max_coincidencias = 0
    
    # Extraer palabras clave de la pregunta (mínimo 3 letras)
    palabras_pregunta = re.findall(r'[a-záéíóúñ]+', mensaje)
    palabras_filtradas = [p for p in palabras_pregunta if len(p) >= 3]
    
    # Si no hay palabras, usar la pregunta completa
    if not palabras_filtradas:
        palabras_filtradas = [mensaje]
    
    for ejemplo in entrenamiento:
        # Obtener el input del ejemplo (normalizado)
        input_text = ejemplo.get('input', '').lower()
        palabras_input = re.findall(r'[a-záéíóúñ]+', input_text)
        
        # Calcular coincidencias
        coincidencias = 0
        for palabra in palabras_filtradas:
            if palabra in input_text:
                coincidencias += 1
        
        # Si hay coincidencias, considerar este ejemplo
        if coincidencias > 0 and coincidencias >= max_coincidencias:
            max_coincidencias = coincidencias
            mejor_match = ejemplo
    
    # Si encontramos un buen match
    if mejor_match and max_coincidencias >= 1:
        respuestas = mejor_match.get('output', {}).get('respuestas_sugeridas', [])
        
        # Seleccionar un tono (preferir 'amigable' primero)
        prioridad_tonos = ['amigable', 'formal', 'tecnico', 'urgente']
        
        for tono in prioridad_tonos:
            for r in respuestas:
                if r.get('tono') == tono:
                    return r.get('texto')
        
        # Si no hay tono, devolver la primera respuesta
        if respuestas:
            return respuestas[0].get('texto')
    
    # 3. Si no hay match, responder con un mensaje genérico
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
    print("🚀 Earby API - Hotel Rosvel (Versión Mejorada)")
    print(f"📊 Entrenamiento: {len(entrenamiento)} ejemplos")
    print("=" * 50)
    app.run(host='0.0.0.0', port=10000, debug=False)
