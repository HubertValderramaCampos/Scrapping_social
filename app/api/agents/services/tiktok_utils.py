"""
Utility functions for TikTok processing.
"""
import os
import json
import tempfile
from typing import Dict, List, Any

def validate_cookies_file(cookies_path: str) -> List[Dict[str, Any]]:
    """
    Validate the cookies file and its contents.
    
    Args:
        cookies_path: Path to the cookies file
        
    Returns:
        List of cookies as dictionaries
        
    Raises:
        FileNotFoundError: If cookies file doesn't exist
        ValueError: If cookies file has invalid content
    """
    if not os.path.exists(cookies_path):
        raise FileNotFoundError(f"Cookies file not found: {cookies_path}")
    
    try:
        with open(cookies_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in cookies file: {e}")
    
    if not cookies or not isinstance(cookies, list):
        raise ValueError("Cookies file is empty or has an incorrect format")
    
    # Validate cookie structure
    valid_cookies = []
    for cookie in cookies:
        if 'name' in cookie and 'value' in cookie:
            valid_cookies.append(cookie)
    
    if len(valid_cookies) == 0:
        raise ValueError("No valid cookies found in file")
    
    return valid_cookies

def create_temp_directory() -> str:
    """
    Create a temporary directory for storing audio files.
    
    Returns:
        Path to the temporary directory
    """
    return tempfile.mkdtemp()

def clean_temp_directory(temp_dir: str) -> None:
    """
    Clean up all files in a temporary directory.
    
    Args:
        temp_dir: Path to the temporary directory
    """
    try:
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        os.rmdir(temp_dir)
    except Exception as e:
        print(f"Error cleaning temporary directory: {e}")

def format_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format the results for the API response.
    
    Args:
        results: List of video processing results
        
    Returns:
        Formatted response dictionary
    """
    return {
        "message": "Procesamiento y transcripción de videos completado",
        "count": len(results),
        "results": results
    }