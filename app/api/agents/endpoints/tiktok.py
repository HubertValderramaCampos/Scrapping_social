from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

import os
import time
import tempfile
import traceback
from typing import List, Dict, Any, Optional

# Import service modules
from app.api.agents.services.browser import TikTokBrowser
from app.api.agents.services.audio_capture import BrowserTabAudioCapture
from app.api.agents.services.transcription import AudioTranscriber
from app.api.agents.services.audio_capture_class import AudioCapture

# Import Selenium components for handling context menus
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Create router
router = APIRouter()

@router.get("/tiktok-transcribe")
def tiktok_transcribe(num_videos: int = 1, duration_per_video: int = 15):

    browser = None
    temp_dir = tempfile.mkdtemp()
    results = []
    
    try:
        # Initialize services
        browser = TikTokBrowser()
        audio_capture = BrowserTabAudioCapture(duration_seconds=duration_per_video)
        transcriber = AudioTranscriber(model_size="small")
        
        # Navigate to TikTok
        driver = browser.navigate_to_tiktok()
        
        # Process videos
        print(f"Starting to process {num_videos} videos...")
        for i in range(num_videos):
            try:
                print(f"Processing video {i+1}...")
                
                # Wait for video element to be present
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "video"))
                )
                
                # Find the video element
                video_element = driver.find_element(By.TAG_NAME, "video")
                
                # Right click on the video to open the context menu
                actions = ActionChains(driver)
                actions.context_click(video_element).perform()
                
                # Wait for the context menu to appear and click on "View video details"
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'TUXMenuItem')]//span[contains(text(), 'detalles del vídeo') or contains(text(), 'video details')]"))
                ).click()
                
                # Wait for the page to load
                time.sleep(5)
                
                # Get video information
                video_info = browser.get_video_info()
                
                # Wait for video to start playing
                time.sleep(5)
                
                # Define temporary audio file path
                audio_file_path = os.path.join(temp_dir, f"tiktok_audio_{i+1}.wav")
                
                # Capture audio
                print(f"Capturing audio from video {i+1}...")
                capture_success = audio_capture.capture_browser_audio(audio_file_path)
                
                # Transcribe audio
                if capture_success and os.path.exists(audio_file_path):
                    print(f"Transcribing audio from video {i+1}...")
                    transcription = transcriber.transcribe(audio_file_path, source_language="es")
                else:
                    transcription = "Error: No se pudo capturar el audio del video"
                
                # Store results
                results.append({
                    "video_number": i+1,
                    "video_url": video_info["video_url"],
                    "username": video_info["username"],
                    "description": video_info["description"],
                    "transcription": transcription
                })
                
                # Go back to the feed for the next video
                driver.execute_script("window.history.go(-1)")
                time.sleep(3)
                
                # Scroll to next video if needed
                if i < num_videos - 1:
                    browser.scroll_to_next_video()
                
            except Exception as e:
                # Handle errors for individual videos
                error_message = f"Error processing video {i+1}: {str(e)}"
                traceback_str = traceback.format_exc()
                print(error_message)
                print(f"Detailed error: {traceback_str}")
                
                results.append({
                    "video_number": i+1,
                    "error": error_message
                })
        
        # Cleanup
        browser.close()
        
        # Clean up temporary files
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting temp file {file_path}: {e}")
        
        # Return results
        return JSONResponse(content={
            "message": "Procesamiento y transcripción de videos completado",
            "count": len(results),
            "results": results
        })
        
    except Exception as e:
        # Handle fatal errors
        error_message = f"Error durante el procesamiento: {str(e)}"
        traceback_str = traceback.format_exc()
        print(error_message)
        print(f"Detailed error: {traceback_str}")
        
        # Cleanup
        if browser:
            browser.close()
            
        # Clean temporary files
        try:
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
        except:
            pass
            
        raise HTTPException(status_code=500, detail=error_message)


        
    except Exception as e:
        # Handle fatal errors
        error_message = f"Error durante el procesamiento: {str(e)}"
        traceback_str = traceback.format_exc()
        print(error_message)
        print(f"Detailed error: {traceback_str}")
        
        # Cleanup
        if browser:
            browser.close()
            
        # Clean temporary files
        try:
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
        except:
            pass
            
        raise HTTPException(status_code=500, detail=error_message)