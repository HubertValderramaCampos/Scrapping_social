import time
from selenium.webdriver.common.by import By
from app.api.agents.endpoints.utils import pasar_siguiente_video

def capturar_subtitulos(driver, duracion_segundos):
    """
    Captura los subtítulos que aparecen durante la reproducción de un video de TikTok.
    
    Args:
        driver: El driver de Selenium WebDriver
        duracion_segundos: Tiempo en segundos durante el cual se capturarán subtítulos
        
    Returns:
        String con todos los subtítulos capturados concatenados
    """
    print(f"Capturando subtítulos durante {duracion_segundos} segundos...")
    subtitulos_unicos = set()
    texto_completo = []
    tiempo_final = time.time() + duracion_segundos
    
    # Variable para controlar cuándo fue la última vez que se encontró un subtítulo
    ultimo_subtitulo_encontrado = time.time()

    while time.time() < tiempo_final:
        try:
            # Selector principal para los subtítulos
            elementos = driver.find_elements(
                By.CSS_SELECTOR,
                "div.css-xfcgts-DivVideoClosedCaption.e15oqmov0"
            )
            
            # Si encuentra elementos, actualiza el tiempo del último subtítulo encontrado
            if elementos:
                ultimo_subtitulo_encontrado = time.time()
                
                for elemento in elementos:
                    texto = elemento.text.strip()
                    if texto and texto not in subtitulos_unicos:
                        subtitulos_unicos.add(texto)
                        texto_completo.append(texto)
                        print(f"Subtítulo capturado: {texto}")
            # Si no ha encontrado subtítulos por 6 segundos o más, pasa al siguiente video
            elif time.time() - ultimo_subtitulo_encontrado >= 4:
                print("No se han encontrado subtítulos por 6 segundos. Pasando al siguiente video...")
                pasar_siguiente_video(driver)
                # Reinicia el contador después de pasar al siguiente video
                ultimo_subtitulo_encontrado = time.time()
                
        except Exception as e:
            # Ignorar errores transitorios de búsqueda
            print(f"Error al capturar subtítulos: {e}")
            pass
            
        time.sleep(0.5)

    resultado = " ".join(texto_completo)
    print(f"Captura de subtítulos finalizada. Total: {len(texto_completo)} fragmentos, {len(resultado)} caracteres")
    return resultado