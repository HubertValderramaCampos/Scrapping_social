"""
This module contains the AudioCapture class for capturing audio from a browser tab.
"""
import os
import time
import wave
import tempfile
import pyaudio

class AudioCapture:
    """
    Class for capturing audio from browser tabs.
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
    
    def capture_system_audio(self, output_file_path):
        """
        Capture audio from the system.
        
        Args:
            output_file_path: Path where the captured audio will be saved
            
        Returns:
            bool: True if capture was successful, False otherwise
        """
        try:
            # Initialize PyAudio
            audio = pyaudio.PyAudio()
            
            # Use default input device
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
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
            
            return True and os.path.exists(output_file_path)
            
        except Exception as e:
            print(f"Error capturing audio: {e}")
            return False