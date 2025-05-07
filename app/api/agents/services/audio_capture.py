"""
Audio capture service for browser tabs using Chrome's media capabilities.
"""
import os
import time
import wave
import tempfile
import numpy as np
from pydub import AudioSegment
import pyaudio

class BrowserTabAudioCapture:
    """
    Class for capturing audio specifically from a browser tab using 
    Chrome's tab audio capture capability.
    """
    def __init__(self, duration_seconds=15, sample_rate=16000, channels=1):
        """
        Initialize the audio capture with configurable parameters.
        
        Args:
            duration_seconds: Length of audio to capture in seconds
            sample_rate: Audio sample rate
            channels: Number of audio channels (1=mono, 2=stereo)
        """
        self.duration_seconds = duration_seconds
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = 1024
        
    def capture_browser_audio(self, output_file_path):
        """
        Capture audio from the active browser tab using Chrome's audio capture.
        
        This method relies on Chrome being launched with the appropriate flags:
        --enable-features=TabAudioCapturing
        
        Args:
            output_file_path: Path where the captured audio will be saved
            
        Returns:
            bool: True if capture was successful, False otherwise
        """
        try:
            # Initialize PyAudio
            audio = pyaudio.PyAudio()
            
            # Find the appropriate input device that represents browser audio
            browser_device_index = None
            
            for i in range(audio.get_device_count()):
                device_info = audio.get_device_info_by_index(i)
                device_name = device_info.get('name', '').lower()
                
                # Look for a device that might be browser or Chrome related
                if ('chrome' in device_name or 'browser' in device_name or 
                    'tab' in device_name or 'application' in device_name):
                    browser_device_index = i
                    print(f"Found browser audio device: {device_name}")
                    break
            
            # If no browser-specific device is found, use the default input
            if browser_device_index is None:
                print("No browser-specific audio device found, using default input")
                browser_device_index = audio.get_default_input_device_info()['index']
            
            # Open audio stream
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=browser_device_index,
                frames_per_buffer=self.chunk_size
            )
            
            print(f"Recording audio for {self.duration_seconds} seconds...")
            
            # Calculate number of chunks to read
            num_chunks = int(self.sample_rate / self.chunk_size * self.duration_seconds)
            audio_frames = []
            
            # Record audio
            for i in range(num_chunks):
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                audio_frames.append(data)
                
                # Print progress every second
                if i % int(self.sample_rate / self.chunk_size) == 0:
                    seconds_done = i // int(self.sample_rate / self.chunk_size)
                    print(f"Recording: {seconds_done}/{self.duration_seconds} seconds")
            
            # Stop and close the stream
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # Save audio to WAV file
            with wave.open(output_file_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(audio_frames))
            
            print(f"Audio saved to {output_file_path}")
            
            # Normalize audio amplitude if needed
            self._normalize_audio(output_file_path)
            
            return True and os.path.exists(output_file_path)
            
        except Exception as e:
            print(f"Error capturing browser audio: {e}")
            return False
    
    def _normalize_audio(self, file_path):
        """
        Normalize the audio volume to improve transcription quality.
        
        Args:
            file_path: Path to the audio file to normalize
        """
        try:
            # Load audio with pydub
            audio = AudioSegment.from_wav(file_path)
            
            # Check if audio is too quiet
            if audio.dBFS < -25:
                # Normalize to -15dB
                normalized_audio = audio.normalize(headroom=15)
                normalized_audio.export(file_path, format="wav")
                print(f"Audio normalized from {audio.dBFS:.1f}dB to {normalized_audio.dBFS:.1f}dB")
        except Exception as e:
            print(f"Warning: Could not normalize audio: {e}")