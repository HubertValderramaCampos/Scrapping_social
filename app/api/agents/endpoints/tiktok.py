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
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Creación del enrutador de la API
router = APIRouter()

@router.get("/tiktok-transcribe")
def tiktok_transcribe(num_videos: int = 1, duration_per_video: int = 15):

    browser = None
    temp_dir = tempfile.mkdtemp()
    results = []
    
    try:
        # Inicialización de servicios
        browser = TikTokBrowser()
        audio_capture = BrowserTabAudioCapture(duration_seconds=duration_per_video)
        transcriber = AudioTranscriber(model_size="small")
        
        # Navegar a TikTok
        driver = browser.navigate_to_tiktok()
        
        print(f"Starting to process {num_videos} videos...")
        for i in range(num_videos):
            try:
                print(f"Processing video {i+1}...")
                
                # Esperar a que el elemento de video esté presente
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "video"))
                )
                
                # Obtener el elemento de video
                video_element = driver.find_element(By.TAG_NAME, "video")
                
                # Clic derecho sobre el video para abrir el menú contextual
                actions = ActionChains(driver)
                actions.context_click(video_element).perform()
                time.sleep(1)

                
                # Hacer clic en "detalles del vídeo"
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@data-e2e='right-click-menu-popover_view-video-details']"))
                ).click()
                # Esperar que la página de detalles cargue
                time.sleep(5)
                
                # Obtener información del video
                video_info = browser.get_video_info()
                
                # Esperar que el video comience a reproducirse
                time.sleep(5)
                
                          
                # Hacer scroll al siguiente video si aplica
                if i < num_videos - 1:
                    browser.scroll_to_next_video()
                
            except Exception as e:
                # Manejo de errores individuales por video
                error_message = f"Error processing video {i+1}: {str(e)}"
                traceback_str = traceback.format_exc()
                print(error_message)
                print(f"Detailed error: {traceback_str}")
                
                results.append({
                    "video_number": i+1,
                    "error": error_message
                })
        
        # Cierre del navegador
        browser.close()


        
    except Exception as e:
        # Manejo de errores fatales
        error_message = f"Error durante el procesamiento: {str(e)}"
        traceback_str = traceback.format_exc()
        print(error_message)
        print(f"Detailed error: {traceback_str}")
        
        if browser:
            browser.close()
            
        raise HTTPException(status_code=500, detail=error_message)
