"""
TikTok scraping and audio transcription endpoints.

This module provides FastAPI endpoints for scraping TikTok videos,
capturing their audio, and transcribing the content.
"""
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

# Create router
router = APIRouter()

@router.get("/tiktok-transcribe")
def tiktok_transcribe(num_videos: int = 1, duration_per_video: int = 15):
    """
    Process TikTok videos: navigate to videos, capture audio, and transcribe content.
    
    Args:
        num_videos: Number of videos to process
        duration_per_video: Duration in seconds to capture for each video
        
    Returns:
        JSON response with transcription results
    """
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

# Fallback endpoint using the original system audio capture approach
@router.get("/tiktok-transcribe-system-audio")
def tiktok_transcribe_system_audio(num_videos: int = 1, duration_per_video: int = 15):
    """
    Process TikTok videos using system-wide audio capture (fallback method).
    
    Args:
        num_videos: Number of videos to process
        duration_per_video: Duration in seconds to capture for each video
        
    Returns:
        JSON response with transcription results
    """
    browser = None
    temp_dir = tempfile.mkdtemp()
    results = []
    
    try:
        # Initialize services
        browser = TikTokBrowser()
        audio_capture = AudioCapture(duration_seconds=duration_per_video)
        transcriber = AudioTranscriber(model_size="small")
        
        # Navigate to TikTok
        driver = browser.navigate_to_tiktok()
        
        # Process videos
        print(f"Starting to process {num_videos} videos using system audio...")
        for i in range(num_videos):
            try:
                print(f"Processing video {i+1}...")
                
                # Get video information
                video_info = browser.get_video_info()
                
                # Wait for video to start playing
                time.sleep(5)
                
                # Define temporary audio file path
                audio_file_path = os.path.join(temp_dir, f"tiktok_audio_{i+1}.wav")
                
                # Capture audio
                print(f"Capturing system audio for video {i+1}...")
                capture_success = audio_capture.capture_system_audio(audio_file_path)
                
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
            "message": "Procesamiento y transcripción de videos completado (system audio)",
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