"""
Servicio principal para la extracción de datos de TikTok.
"""
import time
import traceback
import os
import openai
from typing import List, Dict, Any

from selenium.webdriver.common.by import By
from app.api.agents.services.tiktok_service.browser_tiktok import TikTokBrowser
from app.api.agents.services.tiktok_service.tiktok_interaction import esperar_elemento, activar_subtitulos, dar_like, pasar_siguiente_video
from app.api.agents.services.tiktok_service.tiktok_data_extractor import extraer_datos_canal, extraer_informacion_video, extraer_comentarios
from app.api.agents.services.tiktok_service.tiktok_database import guardar_en_base_datos
from app.api.agents.services.tiktok_service.tiktok_content_analyzer import capturar_y_analizar_subtitulos


class TikTokScraperService:
    """
    Servicio para orquestar la extracción de datos de TikTok.
    """
    
    def __init__(self):
        """Inicializa el servicio de extracción de datos."""
        self.browser = None
        
    async def procesar_videos(self, num_videos: int) -> Dict[str, Any]:
        """
        Procesa videos de TikTok para buscar contenido político de Perú.
        
        Args:
            num_videos: Número de videos a procesar
            
        Returns:
            Diccionario con resultados del procesamiento
        """
        self.browser = None
        results = []
        
        try:
            self.browser = TikTokBrowser()
            driver = self.browser.navigate_to_tiktok()
            print(f"Comenzando a procesar {num_videos} videos...")
            
            # Esperamos a que la página termine de cargar
            tiempo_espera = 5
            print(f"Esperando {tiempo_espera} segundos para que la página cargue completamente...")
            time.sleep(tiempo_espera)
            
            # Verificamos que estamos en la página correcta
            try:
                feed_title = esperar_elemento(driver, By.XPATH, 
                    "//*[contains(text(), 'Para ti') or contains(text(), 'For You')]", 5)
                if feed_title:
                    print("Estamos en la sección 'Para ti'")
                else:
                    print("No se encontró la sección 'Para ti'")
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
                    
                    # Capturamos y analizamos los subtítulos con la nueva función
                    print("Iniciando captura y análisis de subtítulos en tiempo real...")
                    resultado_subtitulos = capturar_y_analizar_subtitulos(driver, 25)
                    
                    subtitulos = resultado_subtitulos["subtitulos"]
                    es_politico = resultado_subtitulos["es_politico"]
                    
                    # Si no se capturaron suficientes subtítulos, pasamos al siguiente
                    if not subtitulos or len(subtitulos.strip()) < 5:
                        print("No se capturaron subtítulos suficientes. Pasando al siguiente video...")
                        pasar_siguiente_video(driver)
                        continue
                    
                    print(f"Subtítulos capturados: {subtitulos[:100]}...")
                              
                    # Si no es político, pasamos al siguiente video
                    if not es_politico:
                        print("El contenido no es político peruano. Pasando al siguiente video...")
                        pasar_siguiente_video(driver)
                        continue
                    
                    # Si es político, damos like al video, extraemos información y guardamos en la DB
                    print("Contenido político peruano encontrado, Dando like...")

                    dar_like(driver)
    
                    print("Extrayendo información del video...")
                    info_channel = extraer_datos_canal(driver)
                    info_video = extraer_informacion_video(driver)
                    info_comments = extraer_comentarios(driver)
                    
                    print("Guardando información en la base de datos...")
                    guardar_en_base_datos(info_channel, info_video, info_comments)
    
                    # Guardamos resultados para devolver
                    video_result = {
                        "video_number": i+1,
                        "subtitles": subtitulos[:100] + "...",
                        "is_political": True,
                        "channel": info_channel,
                        "stats": {
                            "likes": info_video.get('likes', 0),
                            "comments": info_video.get('comentarios', 0)
                        },
                        "detalles_analisis": {
                            "fragmentos_capturados": resultado_subtitulos["fragmentos_capturados"],
                            "caracteres_totales": resultado_subtitulos["caracteres_totales"],
                            "tiempo_captura": resultado_subtitulos["tiempo_captura"]
                        }
                    }
                    results.append(video_result)
                    
                    # Si no es el último video, pasamos al siguiente
                    if i < num_videos - 1:
                        print("Pasando al siguiente video...")
                        pasar_siguiente_video(driver)
                        # Esperamos un poco más para asegurar que el siguiente video cargue
                        time.sleep(2)
    
                except Exception as e:
                    error_message = f"Error procesando el video {i+1}: {str(e)}"
                    traceback_str = traceback.format_exc()
                    print(f"Error: {error_message}")
                    print(f"Error detallado: {traceback_str}")
    
                    results.append({
                        "video_number": i+1,
                        "error": error_message
                    })
                    
                    try:
                        print("Intentando pasar al siguiente video después de error...")
                        pasar_siguiente_video(driver)
                    except Exception as e2:
                        print(f"No se pudo pasar al siguiente video después de error: {str(e2)}")
    
            print("Cerrando el navegador...")
            self.browser.close()
            return {"message": "Procesamiento completado", "results": results}
    
        except Exception as e:
            error_message = f"Error durante el procesamiento: {str(e)}"
            traceback_str = traceback.format_exc()
            print(f"Error general: {error_message}")
            print(f"Error detallado: {traceback_str}")
    
            if self.browser:
                try:
                    self.browser.close()
                    print("Navegador cerrado después de error")
                except:
                    print("No se pudo cerrar el navegador")
    
            return {"error": error_message, "results": results}
        
    def cleanup(self):
        """Limpia los recursos utilizados."""
        if self.browser:
            try:
                self.browser.close()
            except:
                pass