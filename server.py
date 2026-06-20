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
    print(f"❌ Error al cargar: {e}")
    entrenamiento = []

# ========== FUNCIONES DE NORMALIZACIÓN Y SIMILITUD ==========
def normalizar_texto(texto):
    """Elimina tildes, signos, y normaliza para comparación"""
    texto = texto.lower()
    # Reemplazar tildes
    texto = re.sub(r'á', 'a', texto)
    texto = re.sub(r'é', 'e', texto)
    texto = re.sub(r'í', 'i', texto)
    texto = re.sub(r'ó', 'o', texto)
    texto = re.sub(r'ú', 'u', texto)
    texto = re.sub(r'ñ', 'n', texto)
    # Eliminar signos de puntuación
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    return texto

def calcular_similitud(mensaje, input_ejemplo):
    """Calcula cuántas palabras del mensaje están en el ejemplo"""
    palabras_mensaje = set(normalizar_texto(mensaje).split())
    palabras_ejemplo = set(normalizar_texto(input_ejemplo).split())
    
    # Excluir palabras muy cortas
    palabras_mensaje = {p for p in palabras_mensaje if len(p) >= 3}
    
    if not palabras_mensaje:
        return 0
    
    coincidencias = len(palabras_mensaje & palabras_ejemplo)
    total_mensaje = len(palabras_mensaje)
    
    # Porcentaje de coincidencia
    return coincidencias / total_mensaje if total_mensaje > 0 else 0

# ========== FUNCIÓN DE BÚSQUEDA MEJORADA ==========
def buscar_respuesta(mensaje):
    mensaje_original = mensaje
    mensaje = mensaje.lower().strip()
    
    # ===== 1. PRIMERO: BUSCAR EN EL FEW-SHOT =====
    mejor_match = None
    mejor_score = 0
    UMBRAL_MINIMO = 0.3  # 30% de coincidencia
    
    if entrenamiento:
        for ejemplo in entrenamiento:
            input_text = ejemplo.get('input', '')
            score = calcular_similitud(mensaje, input_text)
            
            if score > mejor_score:
                mejor_score = score
                mejor_match = ejemplo
        
        # Si encontramos un buen match
        if mejor_match and mejor_score >= UMBRAL_MINIMO:
            respuestas = mejor_match.get('output', {}).get('respuestas_sugeridas', [])
            
            # Seleccionar el tono según la intención del usuario
            if re.search(r'urgen|prisa|ahora|inmediato|ya', mensaje):
                tono = 'urgente'
            elif re.search(r'comprar|reservar|costo|precio|pagar', mensaje):
                tono = 'formal'
            else:
                tono = 'amigable'
            
            for r in respuestas:
                if r.get('tono') == tono:
                    return r.get('texto')
            
            # Si no hay el tono, devolver la primera respuesta
            if respuestas:
                return respuestas[0].get('texto')
    
    # ===== 2. SI NO HAY MATCH, USAR SALUDOS Y NÚMEROS =====
    # (Solo lo esencial, sin reglas largas que pisen el JSON)
    
    # Saludos
    if mensaje in ['hola', 'buenas', 'hola earby', 'hey', 'saludos', 'buen día', 'buenas tardes', 'buenas noches']:
        return "🏨 ¡Hola! Soy Earby, tu asistente del Hotel Rosvel. ¿En qué puedo ayudarte? Pregúntame por precios, tipos de habitación (sencilla/doble/triple/familiar) o disponibilidad."
    
    # Números sueltos (para respuestas rápidas)
    if mensaje in ["1"]:
        return "🏠 Habitación Sencilla: $680 MXN por noche para 1 persona. Incluye A/C, Wi-Fi, baño privado y TV. ¿Necesitas reservar?"
    if mensaje in ["2"]:
        return "❤️ Habitación Doble: $850 MXN por noche para 2 personas. Cama matrimonial, A/C, Wi-Fi y estacionamiento. ¿Te ayudo a reservar?"
    if mensaje in ["3"]:
        return "👨‍👩‍👧 Habitación Triple: $980 MXN por noche para 3 personas. 1 cama matrimonial + 1 individual, A/C, Wi-Fi."
    if mensaje in ["4"]:
        return "👨‍👩‍👧‍👦 Habitación Familiar: $1,200 MXN por noche para 4 personas. 2 camas matrimoniales, 28m², A/C, Wi-Fi."
    
    # ===== 3. SI NADA FUNCIONA =====
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
        'modelo': 'Few-Shot mejorado con umbral'
    })

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Earby API - Hotel Rosvel (Con Few-Shot Mejorado)")
    print(f"📊 Entrenamiento: {len(entrenamiento)} ejemplos")
    print("=" * 50)
    app.run(host='0.0.0.0', port=10000, debug=False)
