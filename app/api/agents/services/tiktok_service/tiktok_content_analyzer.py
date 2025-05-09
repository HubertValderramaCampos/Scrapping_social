"""
Servicio mejorado para capturar y analizar subtítulos de videos TikTok en tiempo real.
"""
import time
import os
import openai
from selenium.webdriver.common.by import By
from app.api.agents.services.tiktok_service.tiktok_interaction import dar_like

# Inicialización del cliente de OpenAI
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analizar_contenido_politico(texto_subtitulos: str, texto_descripcion: str = "") -> bool:
    """
    Analiza si un texto está relacionado con temas políticos o sociales del Perú.
    
    Args:
        texto_subtitulos: El texto de los subtítulos del video
        texto_descripcion: El texto de la descripción del video (opcional)
        
    Returns:
        bool: True si el texto está relacionado con política peruana, False en caso contrario
    """
    # Combinar subtítulos y descripción para el análisis
    texto_completo = texto_subtitulos
    if texto_descripcion:
        texto_descripcion+= " | DESCRIPCIÓN: " + texto_completo
    
    system_prompt = (
        'Eres un clasificador de texto que determina si una transcripción y/o descripción de TikTok contiene alguna alusión al proceso electoral presidencial de Perú 2026 o a sus precandidatos. '
        'Instrucciones: '
        '1. Recibe como entrada una transcripción de TikTok y/o su descripción. '
        '2. Devuelve únicamente: '
        '   - "true" si el texto menciona directa o indirectamente: '
        '     • El proceso electoral presidencial de 2026 (p. ej., elecciones, campaña, debates, encuestas, partidos, votaciones, candidaturas, etc.). '
        '     • Cualquier precandidatura o aspiración presidencial (incluso sin nombrar al precandidato concreto). '
        '   - "false" en caso contrario (temas distintos al proceso o candidatos presidenciales). '
        'IMPORTANTE: Si el texto habla de elecciones en otros países (como Ecuador, Colombia, etc.) pero NO menciona el proceso electoral de Perú 2026, debes responder "false". '
        'Para la detección, ten en cuenta esta lista de precandidatos oficialmente declarados para 2026 en Perú: '
        '- Keiko Fujimori — Fuerza Popular  '
        '- Rafael López Aliaga — Renovación Popular  '
        '- Carlos Álvarez — País para Todos  '
        '- Hernando de Soto — Avanza País  '
        '- César Acuña — Alianza para el Progreso  '
        '- Verónika Mendoza — Nuevo Perú  '
        '- Alfonso López Chau — Ahora Nación  '
        '- Susel Paredes — Partido Morado  '
        '- Rafael Belaunde — Acción Popular  '
        '- Alfredo Barnechea — Acción Popular  '
        '- Phillip Butters — Avanza País  '
        '- Fernando Olivera — Frente de la Esperanza  '
        '- Guillermo Bermejo — Perú Libre  '
    )

    user_prompt = f'Texto: "{texto_completo}"'

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
    Captura y analiza en tiempo real los subtítulos y la descripción de un video de TikTok.
    
    Args:
        driver: El driver de Selenium WebDriver
        tiempo_minimo_segundos: Tiempo mínimo en segundos durante el cual se capturarán subtítulos (por defecto 25)
        
    Returns:
        dict: Diccionario con los subtítulos capturados, la descripción, si es político y otros metadatos
    """
    # Extraer la descripción del video al inicio
    from app.api.agents.services.tiktok_service.tiktok_data_extractor import extraer_descripcion_video
    descripcion_info = extraer_descripcion_video(driver)
    descripcion_texto = descripcion_info["texto_completo"]
    hashtags = descripcion_info["hashtags"]
    
    print(f"Descripción del video: {descripcion_texto}")
    print(f"Hashtags encontrados: {', '.join(hashtags)}")
    
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
    max_tiempo_sin_subtitulos = 6  # Segundos máximos sin subtítulos antes de determinar que el video terminó
    
    # Control de like
    like_dado = False
    
    # Detectar fin del análisis
    analisis_completo = False
    
    while not analisis_completo:
        tiempo_actual = time.time()
        tiempo_transcurrido = tiempo_actual - tiempo_inicio
        
        # Si pasó el tiempo mínimo y no es político, terminamos
        if tiempo_actual > tiempo_final_minimo and not es_politico:
            print(f"Tiempo mínimo cumplido ({tiempo_minimo_segundos}s) y no se detectó contenido político.")
            analisis_completo = True
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
            
            # Si no ha encontrado subtítulos por tiempo_max_sin_subtitulos o más, consideramos que terminó el video
            elif tiempo_actual - ultimo_subtitulo_encontrado >= max_tiempo_sin_subtitulos and not es_politico:
                if tiempo_actual > tiempo_final_minimo:
                    print("Tiempo mínimo cumplido. Finalizando análisis.")
                    analisis_completo = True
                    break
            
            # Realizar análisis periódico después de acumular suficientes subtítulos
            if (tiempo_actual - ultimo_analisis >= intervalo_analisis and 
                len(texto_completo) > 0 and 
                not es_politico):
                
                ultimo_analisis = tiempo_actual
                texto_subtitulos = " ".join(texto_completo)
                
                print(f"[{int(tiempo_transcurrido)}s] Analizando contenido político (subtítulos + descripción)...")
                # Llamamos correctamente a la función con ambos parámetros
                es_politico = analizar_contenido_politico(texto_subtitulos, descripcion_texto)
                
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
                # Si no hay subtítulos por un tiempo prolongado, consideramos que terminó el video
                if tiempo_actual - ultimo_subtitulo_encontrado >= max_tiempo_sin_subtitulos:
                    print(f"Video político finalizado. No hay nuevos subtítulos por {max_tiempo_sin_subtitulos}s.")
                    analisis_completo = True
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
        "tiempo_captura": time.time() - tiempo_inicio,
        "like_dado": like_dado  # Agregar bandera para saber si ya se dio like
    }
    
    print(f"Captura finalizada: {resultado['fragmentos_capturados']} fragmentos, {resultado['caracteres_totales']} caracteres")
    print(f"Resultado del análisis: {'CONTENIDO POLÍTICO' if es_politico else 'NO es contenido político'}")
    
    return resultado