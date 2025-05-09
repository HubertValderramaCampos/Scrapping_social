"""
Servicio mejorado para capturar y analizar subtítulos de videos TikTok en tiempo real.
"""
import time
import os
import openai
from selenium.webdriver.common.by import By
from app.api.agents.services.tiktok_service.tiktok_interaction import pasar_siguiente_video, dar_like

# Inicialización del cliente de OpenAI
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analizar_contenido_politico(texto: str) -> bool:
    """
    Analiza si un texto está relacionado con temas políticos o sociales del Perú.
    
    Args:
        texto: El texto a analizar (subtítulos del video)
        
    Returns:
        bool: True si el texto está relacionado con política peruana, False en caso contrario
    """
    system_prompt = (
        "Eres un analizador de contenido experto en identificar cualquier mención o alusión a temas políticos o sociales del Perú. "
        "Analiza el siguiente texto, que corresponde a subtítulos de un video de TikTok. Debes detectar si el contenido presenta "
        "cualquier referencia, directa o indirecta, a política peruana o asuntos sociales relevantes del país. Esto incluye, pero no se limita a: "
        "protestas, denuncias ciudadanas, problemáticas sociales, corrupción, acciones del gobierno, decisiones estatales, "
        "crisis institucionales, afectaciones a comunidades, conflictos sociales, políticas públicas, y menciones a políticos, autoridades, "
        "funcionarios públicos, candidatos, expresidentes, congresistas o figuras públicas asociadas a la política nacional. "
        "Responde únicamente con 'true' si el texto está relacionado con cualquiera de estos temas. En caso contrario, responde 'false'."
    )

    user_prompt = f'Texto: "{texto}"'

    try:
        respuesta = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            max_tokens=5
        )

        contenido = respuesta.choices[0].message.content.strip().lower()
        if contenido.startswith("true"):
            return True
        elif contenido.startswith("false"):
            return False
        else:
            return False

    except Exception as e:
        print(f"Error con OpenAI: {e}")
        return False

def capturar_y_analizar_subtitulos(driver, tiempo_minimo_segundos=25):
    """
    Captura y analiza en tiempo real los subtítulos de un video de TikTok.
    Monitorea durante un tiempo mínimo y continúa capturando si detecta contenido político.
    Si es político, da like inmediatamente y continúa capturando subtítulos.
    
    Args:
        driver: El driver de Selenium WebDriver
        tiempo_minimo_segundos: Tiempo mínimo en segundos durante el cual se capturarán subtítulos (por defecto 25)
        
    Returns:
        dict: Diccionario con los subtítulos capturados, si es político y otros metadatos
    """
    print(f"Iniciando captura y análisis de subtítulos (tiempo mínimo: {tiempo_minimo_segundos}s)...")
    
    # Variables para el seguimiento
    subtitulos_unicos = set()
    texto_completo = []
    tiempo_inicio = time.time()
    tiempo_final_minimo = tiempo_inicio + tiempo_minimo_segundos
    
    # Control de análisis
    es_politico = False
    ultimo_analisis = 0
    intervalo_analisis = 5  # Analizar cada 5 segundos
    
    # Control de subtítulos
    ultimo_subtitulo_encontrado = time.time()
    max_tiempo_sin_subtitulos = 6  # Segundos máximos sin subtítulos antes de pasar al siguiente video
    
    # Control de like
    like_dado = False
    
    while True:  # Bucle infinito - continuará hasta que se detecte alguna condición de salida
        tiempo_actual = time.time()
        tiempo_transcurrido = tiempo_actual - tiempo_inicio
        
        # Si pasó el tiempo mínimo y no es político, terminamos y pasamos al siguiente video
        if tiempo_actual > tiempo_final_minimo and not es_politico:
            print(f"Tiempo mínimo cumplido ({tiempo_minimo_segundos}s) y no se detectó contenido político. Pasando al siguiente video.")
            pasar_siguiente_video(driver)
            break
            
        try:
            # Buscar subtítulos
            elementos = driver.find_elements(
                By.CSS_SELECTOR,
                "div.css-xfcgts-DivVideoClosedCaption.e15oqmov0"
            )
            
            # Si encuentra elementos, procesar
            if elementos:
                ultimo_subtitulo_encontrado = tiempo_actual
                
                for elemento in elementos:
                    texto = elemento.text.strip()
                    if texto and texto not in subtitulos_unicos:
                        subtitulos_unicos.add(texto)
                        texto_completo.append(texto)
                        print(f"[{int(tiempo_transcurrido)}s] Subtítulo: {texto}")
            
            # Si no ha encontrado subtítulos por tiempo_max_sin_subtitulos o más, pasar al siguiente video
            elif tiempo_actual - ultimo_subtitulo_encontrado >= max_tiempo_sin_subtitulos and not es_politico:
                print(f"No se han encontrado subtítulos por {max_tiempo_sin_subtitulos}s. Pasando al siguiente video...")
                pasar_siguiente_video(driver)
                # Reiniciar contadores
                ultimo_subtitulo_encontrado = tiempo_actual
                tiempo_inicio = tiempo_actual
                tiempo_final_minimo = tiempo_actual + tiempo_minimo_segundos
                subtitulos_unicos = set()
                texto_completo = []
                es_politico = False
                like_dado = False
            
            # Realizar análisis periódico después de acumular suficientes subtítulos
            if (tiempo_actual - ultimo_analisis >= intervalo_analisis and 
                len(texto_completo) > 0 and 
                not es_politico):
                
                ultimo_analisis = tiempo_actual
                texto_para_analisis = " ".join(texto_completo)
                
                print(f"[{int(tiempo_transcurrido)}s] Analizando contenido político...")
                es_politico = analizar_contenido_politico(texto_para_analisis)
                
                if es_politico:
                    print(f"[{int(tiempo_transcurrido)}s] ¡CONTENIDO POLÍTICO DETECTADO!")
                    
                    # Dar like inmediatamente al detectar contenido político
                    if not like_dado:
                        print(f"[{int(tiempo_transcurrido)}s] Dando like al video...")
                        dar_like(driver)
                        like_dado = True
                        
                    print(f"[{int(tiempo_transcurrido)}s] Continuando captura de subtítulos...")
                else:
                    print(f"[{int(tiempo_transcurrido)}s] No se detectó contenido político en este análisis.")
                    
            # Si es político y ya pasó el tiempo mínimo, verificar si hay que terminar
            if es_politico and tiempo_actual > tiempo_final_minimo:
                # Aquí solo continuamos capturando subtítulos sin analizar más
                # Si no hay subtítulos por un tiempo prolongado, podemos pasar al siguiente
                if tiempo_actual - ultimo_subtitulo_encontrado >= max_tiempo_sin_subtitulos:
                    print(f"Video político finalizado. No hay nuevos subtítulos por {max_tiempo_sin_subtitulos}s. Pasando al siguiente video...")
                    pasar_siguiente_video(driver)
                    break
        
        except Exception as e:
            print(f"Error durante captura: {e}")
            
        time.sleep(0.5)  # Pequeña pausa para no sobrecargar el CPU

    # Resultado final
    subtitulos_texto = " ".join(texto_completo)
    resultado = {
        "subtitulos": subtitulos_texto,
        "es_politico": es_politico,
        "fragmentos_capturados": len(texto_completo),
        "caracteres_totales": len(subtitulos_texto),
        "tiempo_captura": time.time() - tiempo_inicio
    }
    
    print(f"Captura finalizada: {resultado['fragmentos_capturados']} fragmentos, {resultado['caracteres_totales']} caracteres")
    print(f"Resultado del análisis: {'CONTENIDO POLÍTICO' if es_politico else 'NO es contenido político'}")
    
    return resultado