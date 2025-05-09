"""
Endpoints para la API de TikTok Scraper.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.api.agents.services.tiktok_service.tiktok_scraper import TikTokScraperService

router = APIRouter()

@router.get("/transcribe")
async def tiktok_transcribe(num_videos: str = "1"):
    """
    Endpoint para procesar videos de TikTok y extraer información relevante.
    
    Args:
        num_videos: Número de videos a procesar
        
    Returns:
        JSONResponse con los resultados del procesamiento
    """
    try:
        # Convertimos el parámetro a entero
        num_videos_int = int(num_videos)
        if num_videos_int < 1:
            raise ValueError("El número de videos debe ser mayor que 0")
        
        # Creamos e iniciamos el servicio
        scraper_service = TikTokScraperService()
        results = await scraper_service.procesar_videos(num_videos_int)
        
        # Si hay un error, lanzamos una excepción
        if "error" in results:
            raise HTTPException(status_code=500, detail=results["error"])
        
        return results
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Parámetro inválido: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el servidor: {str(e)}")