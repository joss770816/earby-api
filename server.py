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
    texto = re.sub(r'á', 'a', texto)
    texto = re.sub(r'é', 'e', texto)
    texto = re.sub(r'í', 'i', texto)
    texto = re.sub(r'ó', 'o', texto)
    texto = re.sub(r'ú', 'u', texto)
    texto = re.sub(r'ñ', 'n', texto)
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    return texto

def calcular_similitud(mensaje, input_ejemplo):
    """Calcula cuántas palabras del mensaje están en el ejemplo"""
    palabras_mensaje = set(normalizar_texto(mensaje).split())
    palabras_ejemplo = set(normalizar_texto(input_ejemplo).split())
    
    # Excluir palabras muy cortas (menos de 3 letras)
    palabras_mensaje = {p for p in palabras_mensaje if len(p) >= 2}
    
    if not palabras_mensaje:
        return 0
    
    coincidencias = len(palabras_mensaje & palabras_ejemplo)
    total_mensaje = len(palabras_mensaje)
    
    # Si el mensaje tiene 1 palabra y coincide, devuelve 1.0
    return coincidencias / total_mensaje if total_mensaje > 0 else 0

# ========== FUNCIÓN DE BÚSQUEDA MEJORADA ==========
def buscar_respuesta(mensaje):
    mensaje = mensaje.lower().strip()
    
    # ===== 1. PRIMERO: BUSCAR EN EL FEW-SHOT =====
    mejor_match = None
    mejor_score = 0
    UMBRAL_MINIMO = 0.1  # BAJAMOS EL UMBRAL A 10% PARA PRUEBAS
    
    if entrenamiento:
        for ejemplo in entrenamiento:
            input_text = ejemplo.get('input', '')
            score = calcular_similitud(mensaje, input_text)
            
            # DEBUG: Mostrar lo que está pasando
            print(f"🔍 Comparando: '{mensaje}' vs '{input_text}' -> Score: {score:.2f}")
            
            if score > mejor_score:
                mejor_score = score
                mejor_match = ejemplo
        
        # Si encontramos un buen match
        if mejor_match and mejor_score >= UMBRAL_MINIMO:
            print(f"✅ MATCH ENCONTRADO! Score: {mejor_score:.2f}")
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
    
    # ===== 2. SI NO HAY MATCH, USAR SALUDOS =====
    if mensaje in ['hola', 'buenas', 'hola earby', 'hey', 'saludos']:
        return "🏨 ¡Hola! Soy Earby, tu asistente del Hotel Rosvel. ¿En qué puedo ayudarte?"
    
    # ===== 3. SI NADA FUNCIONA =====
    return "🤔 No entendí tu consulta. ¿Puedes ser más específico? (precios, servicios, ubicación, etc.)"
