# Importamos los módulos necesarios de FastAPI
from fastapi import APIRouter, HTTPException 
from fastapi.responses import JSONResponse

# Importamos librerías estándar y de terceros
import json
import time
import os
import tempfile
import traceback
from typing import Optional, List, Dict, Any

# Importamos Chrome sin detección y herramientas de Selenium
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Importamos la librería Whisper para transcripción de audio
import whisper

# Importamos librerías para captura de audio
import pyaudio
import wave
import numpy as np
from pydub import AudioSegment
import soundcard as sc

# Creamos el enrutador para los endpoints
router = APIRouter()

# Función para depurar las cookies y verificar que estén correctamente cargadas
def debug_cookies(driver):
    """Imprime todas las cookies en la sesión actual del navegador"""
    cookies = driver.get_cookies()
    print(f"Número de cookies: {len(cookies)}")
    for i, cookie in enumerate(cookies):
        print(f"Cookie {i+1}: {cookie.get('name')} = {cookie.get('value')[:10]}...")
    return cookies

# Función para transcribir un archivo de audio a texto en español
def transcribe_audio(audio_file_path: str) -> str:
    try:
        # Cargamos el modelo pequeño de Whisper
        model = whisper.load_model("small")
        
        # Transcribimos el audio usando la opción de traducción
        result = model.transcribe(
            audio_file_path,
            task="translate",
            language="es"
        )
        
        # Retornamos el texto transcrito
        return result["text"]
    except Exception as e:
        # Mostramos el error en consola y lo retornamos
        print(f"Error durante la transcripción: {e}")
        return f"Error en la transcripción: {str(e)}"

# Clase para capturar el audio que se reproduce en el sistema
# Clase para capturar el audio específicamente del navegador


# Endpoint único para procesar TikTok - captura audio y transcribe
@router.get("/tiktok-transcribe")
def tiktok_transcribe(num_videos: int = 1, duration_per_video: int = 15):
    driver = None
    audio_capture = AudioCapture(duration_seconds=duration_per_video)
    results = []
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Ruta al archivo de cookies
        cookies_path = "cookies.json"

        # Validamos que el archivo de cookies exista
        if not os.path.exists(cookies_path):
            raise HTTPException(status_code=404, detail="Archivo cookies.json no encontrado.")

        # Cargamos las cookies desde el archivo
        with open(cookies_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)
            
        # Verificamos que el archivo de cookies tenga contenido válido
        if not cookies or not isinstance(cookies, list):
            raise HTTPException(status_code=400, detail="El archivo de cookies está vacío o tiene un formato incorrecto.")

        # Configuramos las opciones de Chrome
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--use-fake-ui-for-media-stream")
        options.add_argument("--use-fake-device-for-media-stream")
        options.add_argument("--disable-notifications")
        
        # Importante: Mantener el audio habilitado
        options.add_argument("--autoplay-policy=no-user-gesture-required")
        
        # Indicamos la versión del ChromeDriver
        driver = uc.Chrome(options=options, version_main=135)
        
        # Primero navegamos a TikTok sin cookies
        print("Abriendo TikTok sin cookies...")
        driver.get("https://www.tiktok.com/")
        
        # Esperamos unos segundos para que cargue la página completamente
        time.sleep(5)
        
        # Limpiamos todas las cookies existentes
        driver.delete_all_cookies()
        time.sleep(1)

        # Agregamos las cookies al navegador
        print(f"Intentando cargar {len(cookies)} cookies...")
        valid_cookies = 0
        
        for cookie in cookies:
            try:
                # Verificamos que la cookie tenga los campos obligatorios
                if 'name' not in cookie or 'value' not in cookie:
                    print(f"Omitiendo cookie inválida sin nombre o valor: {cookie}")
                    continue
                
                # Creamos una copia limpia de la cookie
                cookie_dict = {
                    'name': cookie['name'],
                    'value': cookie['value']
                }
                
                # Agregamos atributos opcionales si existen
                for attr in ['domain', 'path', 'secure', 'httpOnly', 'expiry']:
                    if attr in cookie and cookie[attr] is not None:
                        cookie_dict[attr] = cookie[attr]
                
                # Aseguramos que el dominio sea correcto si no está presente
                if 'domain' not in cookie_dict or not cookie_dict['domain']:
                    cookie_dict['domain'] = '.tiktok.com'
                
                # Corregimos el formato de sameSite si existe
                if 'sameSite' in cookie:
                    # Convertimos a formato correcto según Selenium
                    if cookie['sameSite'].lower() in ['strict', 'lax', 'none']:
                        cookie_dict['sameSite'] = cookie['sameSite'].capitalize()
                
                # Intentamos agregar la cookie
                driver.add_cookie(cookie_dict)
                valid_cookies += 1
                
            except Exception as e:
                print(f"Error al agregar cookie {cookie.get('name', 'desconocida')}: {str(e)}")
        
        print(f"Se agregaron correctamente {valid_cookies} de {len(cookies)} cookies")
        
        # Verificamos las cookies cargadas
        loaded_cookies = debug_cookies(driver)
        if len(loaded_cookies) < 2:
            print("ADVERTENCIA: Se cargaron muy pocas cookies, la autenticación puede fallar")

        # Refrescamos la página con las cookies cargadas
        print("Recargando página con las cookies...")
        driver.refresh()
        time.sleep(5)
        
        # Intentamos ir a la página "Para ti" de TikTok
        try:
            print("Buscando botón 'Para ti'...")
            para_ti_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Para ti']"))
            )
            para_ti_button.click()
            print("Navegado exitosamente al feed 'Para ti'")
        except TimeoutException:
            # Si no se encuentra el botón, vamos directamente al feed de "Para ti"
            print("Tiempo de espera agotado para el botón 'Para ti', navegando directamente")
            driver.get("https://www.tiktok.com/foryou")
            time.sleep(3)
        
        # Procesamos la cantidad de videos especificada
        print(f"Comenzando a procesar {num_videos} videos...")
        for i in range(num_videos):
            try:
                print(f"Procesando video {i+1}...")
                
                # Esperamos a que el video cargue en el DOM
                video_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//video[contains(@class, 'tiktok-video')]"))
                )
                
                # Obtenemos la URL actual del video
                video_url = driver.current_url
                print(f"URL del video {i+1}: {video_url}")
                
                # Capturamos información adicional del video cuando esté disponible
                try:
                    username = driver.find_element(By.XPATH, "//span[contains(@class, 'author-uniqueId')]").text
                except:
                    username = "No disponible"
                
                try:
                    description = driver.find_element(By.XPATH, "//div[contains(@class, 'video-desc')]").text
                except:
                    description = "No disponible"
                
                # Esperamos un momento para que el video comience a reproducirse automáticamente
                # No intentamos manipular el volumen ni hacer clic - dejamos que TikTok lo reproduzca solo
                time.sleep(5)
                
                # Definimos la ruta del archivo de audio temporal
                audio_file_path = os.path.join(temp_dir, f"tiktok_audio_{i+1}.wav")
                
                # Capturamos el audio que se está reproduciendo
                print(f"Capturando audio del video {i+1} durante {duration_per_video} segundos...")
                capture_success = audio_capture.capture_system_audio(audio_file_path)
                
                if capture_success and os.path.exists(audio_file_path):
                    # Transcribimos el audio capturado
                    print(f"Transcribiendo audio capturado del video {i+1}...")
                    transcription = transcribe_audio(audio_file_path)
                else:
                    # Si falló la captura, usamos un mensaje de error
                    print(f"Falló la captura de audio para el video {i+1}")
                    transcription = "Error: No se pudo capturar el audio del video"
                
                # Guardamos los resultados en la lista
                results.append({
                    "video_number": i+1,
                    "video_url": video_url,
                    "username": username,
                    "description": description,
                    "transcription": transcription
                })
                
                # Hacemos scroll hacia el siguiente video si no es el último
                if i < num_videos - 1:
                    print(f"Desplazando al siguiente video...")
                    driver.execute_script("window.scrollBy(0, 500);")
                    time.sleep(3)  # Esperamos a que cargue el siguiente video
                
            except Exception as e:
                # Si hay error con un video específico, lo registramos con más detalle
                error_message = f"Error al procesar video {i+1}: {str(e)}"
                traceback_str = traceback.format_exc()
                print(error_message)
                print(f"Stacktrace detallado: {traceback_str}")
                
                results.append({
                    "video_number": i+1,
                    "error": error_message,
                    "traceback": traceback_str[:500]  # Limitamos el tamaño del stacktrace
                })
                
                # Implementamos un mecanismo simple de reintento
                retry_count = 0
                max_retries = 2
                while retry_count < max_retries:
                    retry_count += 1
                    print(f"Reintentando video {i+1} (intento {retry_count}/{max_retries})...")
                    try:
                        # Esperamos un poco más antes del reintento
                        time.sleep(5)
                        
                        # Refrescamos la página o navegamos de nuevo si es necesario
                        if retry_count == 1:
                            driver.refresh()
                        else:
                            driver.get("https://www.tiktok.com/foryou")
                        
                        time.sleep(5)
                        
                        # Buscamos de nuevo el video
                        video_element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, "//video[contains(@class, 'tiktok-video')]"))
                        )
                        
                        # Esperamos a que se reproduzca
                        time.sleep(5)
                        
                        # Intentamos capturar el audio nuevamente
                        audio_file_path = os.path.join(temp_dir, f"tiktok_audio_{i+1}_retry{retry_count}.wav")
                        capture_success = audio_capture.capture_system_audio(audio_file_path)
                        
                        if capture_success and os.path.exists(audio_file_path):
                            transcription = transcribe_audio(audio_file_path)
                            
                            # Actualizamos el resultado previo con la información del reintento exitoso
                            results[-1] = {
                                "video_number": i+1,
                                "video_url": driver.current_url,
                                "username": "Reintentos",
                                "description": f"Capturado en el reintento {retry_count}",
                                "transcription": transcription
                            }
                            
                            # Si tuvimos éxito, salimos del bucle de reintentos
                            print(f"Reintento {retry_count} exitoso!")
                            break
                            
                    except Exception as retry_e:
                        print(f"Error en el reintento {retry_count}: {str(retry_e)}")
                        # Si fallamos en el último reintento, continuamos con el siguiente video
        
        # Cerramos el navegador una vez procesados los videos
        print("Procesamiento de videos completado, cerrando navegador")
        driver.quit()
        
        # Limpiamos los archivos temporales
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error al eliminar archivo temporal {file_path}: {e}")
        
        # Retornamos los resultados
        return JSONResponse(content={
            "message": "Procesamiento y transcripción de videos completado",
            "count": len(results),
            "results": results
        })
        
    except Exception as e:
        # Nos aseguramos de cerrar el navegador en caso de error
        error_message = f"Error durante el procesamiento de videos: {str(e)}"
        traceback_str = traceback.format_exc()
        print(error_message)
        print(f"Stacktrace detallado: {traceback_str}")
        
        try:
            if driver:
                driver.quit()
        except:
            pass
            
        # Limpiamos los archivos temporales en caso de error
        try:
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
        except:
            pass
            
        raise HTTPException(status_code=500, detail=error_message)