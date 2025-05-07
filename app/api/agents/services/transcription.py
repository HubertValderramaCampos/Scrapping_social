"""
Audio transcription service using Whisper.
"""
import os
import time
import whisper
from fastapi import HTTPException

class AudioTranscriber:
    """Class for transcribing audio files to text using WhisperAI."""
    
    def __init__(self, model_size="small"):
        """
        Initialize the transcriber with the specified model size.
        
        Args:
            model_size: Size of the Whisper model to use ("tiny", "base", "small", "medium", "large")
        """
        self.model_size = model_size
        self._model = None
    
    @property
    def model(self):
        """Lazy-load the Whisper model only when needed."""
        if self._model is None:
            try:
                print(f"Loading Whisper model '{self.model_size}'...")
                self._model = whisper.load_model(self.model_size)
                print(f"Model loaded successfully")
            except Exception as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to load Whisper model: {str(e)}"
                )
        return self._model
    
    def transcribe(self, audio_file_path: str, source_language: str = "es") -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_file_path: Path to the audio file
            source_language: Language code (e.g., "es" for Spanish)
            
        Returns:
            str: Transcribed text
        """
        if not os.path.exists(audio_file_path):
            raise HTTPException(
                status_code=404, 
                detail=f"Audio file not found: {audio_file_path}"
            )
            
        try:
            start_time = time.time()
            print(f"Starting transcription of {audio_file_path}...")
            
            # Perform transcription with translation to desired language
            result = self.model.transcribe(
                audio_file_path,
                task="translate" if source_language != "en" else "transcribe",
                language=source_language
            )
            
            elapsed_time = time.time() - start_time
            print(f"Transcription completed in {elapsed_time:.2f} seconds")
            
            # Return the transcribed text
            return result["text"].strip()
            
        except Exception as e:
            print(f"Transcription error: {str(e)}")
            return f"Error en la transcripción: {str(e)}"