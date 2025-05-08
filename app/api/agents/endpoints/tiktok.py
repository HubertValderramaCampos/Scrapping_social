from fastapi import APIRouter, HTTPException, BackgroundTasks 
from fastapi.responses import JSONResponse

import os
import time
import tempfile
import traceback
from typing import List, Dict, Any, Optional

# Importación de módulos de servicio
from app.api.agents.services.browser import TikTokBrowser
from app.api.agents.services.audio_capture import BrowserTabAudioCapture
from app.api.agents.services.transcription import AudioTranscriber
from app.api.agents.services.audio_capture_class import AudioCapture

# Importación de componentes de Selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

# Importamos los utils de tiktok
from app.api.agents.endpoints.utils_tiktok.transcription import capturar_subtitulos
from app.api.agents.endpoints.utils import es_politica_peru
from app.api.agents.endpoints.utils import activar_subtitulos, dar_like, pasar_siguiente_video
from app.api.agents.endpoints.utils import esperar_elemento, hay_subtitulos_visibles

# Creación del enrutador de la API
router = APIRouter()

@router.get("/tiktok-transcribe")
async def tiktok_transcribe(num_videos: str = "1"):
    # Convertimos los parámetros a enteros
    num_videos = int(num_videos)

    browser = None
    results = []

    try:
        browser = TikTokBrowser()
        driver = browser.navigate_to_tiktok()
        print(f"Comenzando a procesar {num_videos} videos...")
        
        # Esperamos a que la página termine de cargar
        tiempo_espera = 10
        print(f"Esperando {tiempo_espera} segundos para que la página cargue completamente...")
        time.sleep(tiempo_espera)
        
        # Verificamos que estamos en la página correcta
        try:
            feed_title = esperar_elemento(driver, By.XPATH, 
                "//*[contains(text(), 'Para ti') or contains(text(), 'For You')]", 5)
            if feed_title:
                print("Estamos en la sección 'Para ti'")
            else:
                print("No se encontró la sección 'Para ti', pero continuamos el procesamiento")
        except Exception as e:
            print(f"No se pudo verificar la sección: {str(e)}")
        
        # Intentamos activar los subtítulos para el primer video
        activar_subtitulos_exitoso = activar_subtitulos(driver)
        if not activar_subtitulos_exitoso:
            print("ADVERTENCIA: No se pudieron activar los subtítulos inicialmente. Continuando de todas formas...")
        
        # Procesamos cada video
        for i in range(num_videos):
            try:
                print(f"\n=== Procesando video {i+1}/{num_videos} ===")
                
                # Esperamos a que el video cargue
                video_element = esperar_elemento(driver, By.TAG_NAME, "video", 5)
                if not video_element:
                    print(f"No se encontró el elemento de video para el video {i+1}. Intentando pasar al siguiente...")
                    continue
                            
                
                # Capturamos los subtítulos
                print("Capturando subtítulos...")
                subtitles = capturar_subtitulos(driver, 65)
                
                if not subtitles or len(subtitles.strip()) < 5:  # Verificamos que no esté vacío o sea muy corto
                    print("No se capturaron subtítulos suficientes. Pasando al siguiente video...")
                    pasar_siguiente_video(driver)
                    continue
                    
                print(f"Subtítulos capturados: {subtitles[:100]}...")  # Mostramos solo los primeros 100 caracteres
                
                # Verificamos si el contenido está relacionado con política peruana
                print("Analizando si el contenido es sobre política peruana...")
                es_politico = await es_politica_peru(subtitles)
                print(f"¿Es contenido político peruano?: {es_politico}")
                
                # Guardamos los resultados de este video
                resultado_video = {
                    "video_number": i+1,
                    "subtitulos": subtitles,
                    "es_politico": es_politico
                }
                results.append(resultado_video)
                
                # Si no es político, pasamos al siguiente video
                if not es_politico:
                    print("El contenido no es político peruano. Pasando al siguiente video...")
                    pasar_siguiente_video(driver)
                    continue
                
                # Si es político, damos like al video
                print("¡Contenido político peruano encontrado! Dando like...")
                like_exitoso = dar_like(driver)
                resultado_video["like_dado"] = like_exitoso
                
                # Si no es el último video, pasamos al siguiente
                if i < num_videos - 1:
                    print("Pasando al siguiente video...")
                    pasar_siguiente_video(driver)
                    # Esperamos un poco más para asegurar que el siguiente video cargue
                    time.sleep(3)

            except Exception as e:
                error_message = f"Error procesando el video {i+1}: {str(e)}"
                traceback_str = traceback.format_exc()
                print(f"Error: {error_message}")
                print(f"Error detallado: {traceback_str}")

                results.append({
                    "video_number": i+1,
                    "error": error_message
                })
                
                # Intentamos pasar al siguiente video si hay un error
                try:
                    print("Intentando pasar al siguiente video después de error...")
                    pasar_siguiente_video(driver)
                except Exception as e2:
                    print(f"No se pudo pasar al siguiente video después de error: {str(e2)}")

        print("Cerrando el navegador...")
        browser.close()
        return {"message": "Procesamiento completado", "results": results}

    except Exception as e:
        error_message = f"Error durante el procesamiento: {str(e)}"
        traceback_str = traceback.format_exc()
        print(f"Error general: {error_message}")
        print(f"Error detallado: {traceback_str}")

        if browser:
            try:
                browser.close()
                print("Navegador cerrado después de error")
            except:
                print("No se pudo cerrar el navegador")

        raise HTTPException(status_code=500, detail=error_message)