"""
Servicio para guardar datos de TikTok en la base de datos.
"""
import os
import re
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

def extract_video_id(url):
    """
    Extrae el ID del video de una URL de TikTok.
    
    Args:
        url: URL del video de TikTok
        
    Returns:
        str: ID del video o None si no se encuentra
    """
    if not url:
        return None
        
    # Patrón para extraer el ID del video
    pattern = r'video/(\d+)'
    match = re.search(pattern, url)
    
    return match.group(1) if match else None

def guardar_en_base_datos(info_channel, info_video, info_comments, subtitulos=None):
    """
    Guarda los datos extraídos en la base de datos.
    
    Args:
        info_channel: Diccionario con información del canal
        info_video: Diccionario con información del video
        info_comments: Lista de diccionarios con información de comentarios
        subtitulos: Texto completo de los subtítulos capturados (opcional)
        
    Returns:
        Diccionario con los IDs generados para cada inserción
    """
    # Cargar variables de entorno
    load_dotenv()
    
    # Configuración de la conexión a la base de datos
    db_config = {
        'user': os.getenv('username'),
        'password': os.getenv('password'),
        'host': os.getenv('host'),
        'port': os.getenv('port'),
        'database': os.getenv('database'),
        'sslmode': os.getenv('sslmode')
    }
    
    # Inicializar diccionario para almacenar IDs generados
    ids_generados = {
        'social_network_id': None,
        'channel_id': None,
        'scrapper_result_id': None,
        'comments_ids': [],
        'video_id': None
    }
    
    # Extraer video_id de la URL si está disponible
    video_url = info_video.get('video_url', '')
    video_id = extract_video_id(video_url) or '7501847835747388727'  # Usar ID predeterminado si no se encuentra
    ids_generados['video_id'] = video_id
    
    try:
        # Establecer conexión con la base de datos
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # 1. Insertar o obtener ID de la red social (TikTok)
        cur.execute("SELECT id FROM social_networks WHERE name = %s", ('TikTok',))
        resultado = cur.fetchone()
        
        if resultado:
            social_network_id = resultado[0]
        else:
            cur.execute("INSERT INTO social_networks (name) VALUES (%s) RETURNING id", ('TikTok',))
            social_network_id = cur.fetchone()[0]
        
        ids_generados['social_network_id'] = social_network_id
        
        # 2. Insertar o obtener ID del canal
        if info_channel.get('url') and info_channel.get('name'):
            cur.execute("SELECT id FROM channels WHERE url = %s", (info_channel['url'],))
            resultado = cur.fetchone()
            
            if resultado:
                channel_id = resultado[0]
            else:
                cur.execute(
                    "INSERT INTO channels (social_network_id, name, url) VALUES (%s, %s, %s) RETURNING id",
                    (social_network_id, info_channel['name'], info_channel['url'])
                )
                channel_id = cur.fetchone()[0]
            
            ids_generados['channel_id'] = channel_id
            
            # Verificar si ya existe un registro con este video_id
            cur.execute("SELECT id FROM scrapper_results WHERE video_id = %s", (video_id,))
            video_existente = cur.fetchone()
            
            if video_existente:
                # El video ya existe, usar ese ID y no insertar un nuevo registro
                scrapper_result_id = video_existente[0]
                ids_generados['scrapper_result_id'] = scrapper_result_id
                print(f"Video con ID {video_id} ya existe en la base de datos. No se insertará un nuevo registro.")
            else:
                # 3. Insertar resultado del scraping del video
                scraped_at = datetime.now()
                if info_video.get('fecha_exacta'):
                    try:
                        scraped_at = datetime.strptime(info_video['fecha_exacta'], '%Y-%m-%d %H:%M:%S')
                    except Exception as e:
                        print(f"Error al convertir fecha_exacta: {e}")
                
                # Preparar subtítulos (si se proporcionan)
                transcript = subtitulos if subtitulos else None
                
                cur.execute(
                    """
                    INSERT INTO scrapper_results 
                    (channel_id, comment_count, like_count, view_count, scraped_at, video_id, transcript) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s) 
                    RETURNING id
                    """,
                    (
                        channel_id, 
                        info_video.get('comentarios', 0), 
                        info_video.get('likes', 0),
                        0,  # view_count no está disponible en el código proporcionado
                        scraped_at,
                        video_id,
                        transcript
                    )
                )
                scrapper_result_id = cur.fetchone()[0]
                ids_generados['scrapper_result_id'] = scrapper_result_id
                print(f"Nuevo video con ID {video_id} insertado en la base de datos.")
            
            # 4. Insertar comentarios
            for comentario in info_comments:
                cur.execute(
                    """
                    INSERT INTO comments 
                    (scrapper_result_id, username, content, like_count) 
                    VALUES (%s, %s, %s, %s) 
                    RETURNING id
                    """,
                    (
                        scrapper_result_id,
                        comentario.get('usuario', 'Desconocido'),
                        comentario.get('contenido', ''),
                        comentario.get('likes', 0)
                    )
                )
                comment_id = cur.fetchone()[0]
                ids_generados['comments_ids'].append(comment_id)
        
        # Confirmar cambios
        conn.commit()
        print(f"Datos guardados correctamente en la base de datos.")
        print(f"Video ID: {video_id}")
        print(f"Total de comentarios guardados: {len(ids_generados['comments_ids'])}")
        
    except Exception as e:
        print(f"Error al guardar en la base de datos: {e}")
        # Revertir cambios en caso de error
        if 'conn' in locals() and conn:
            conn.rollback()
    finally:
        # Cerrar cursor y conexión
        if 'cur' in locals() and cur:
            cur.close()
        if 'conn' in locals() and conn:
            conn.close()
    
    return ids_generados