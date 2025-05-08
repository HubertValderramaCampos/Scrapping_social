import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

def guardar_en_base_datos(info_channel, info_video, info_comments):
    """
    Guarda los datos extraídos en la base de datos.
    
    Args:
        info_channel: Diccionario con información del canal
        info_video: Diccionario con información del video
        info_comments: Lista de diccionarios con información de comentarios
        
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
        'comments_ids': []
    }
    
    try:
        # Establecer conexión con la base de datos
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # 1. Insertar o obtener ID de la red social (TikTok)
        cur.execute(
            "SELECT id FROM social_networks WHERE name = %s",
            ('TikTok',)
        )
        resultado = cur.fetchone()
        
        if resultado:
            social_network_id = resultado[0]
        else:
            cur.execute(
                "INSERT INTO social_networks (name) VALUES (%s) RETURNING id",
                ('TikTok',)
            )
            social_network_id = cur.fetchone()[0]
        
        ids_generados['social_network_id'] = social_network_id
        
        # 2. Insertar o obtener ID del canal
        if info_channel['url'] and info_channel['name']:
            cur.execute(
                "SELECT id FROM channels WHERE url = %s",
                (info_channel['url'],)
            )
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
            
            # 3. Insertar resultado del scraping del video
            scraped_at = datetime.now()
            if info_video.get('fecha_exacta'):
                try:
                    scraped_at = datetime.strptime(info_video['fecha_exacta'], '%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    print(f"Error al convertir fecha_exacta: {e}")
            
            cur.execute(
                """
                INSERT INTO scrapper_results 
                (channel_id, comment_count, like_count, view_count, scraped_at) 
                VALUES (%s, %s, %s, %s, %s) 
                RETURNING id
                """,
                (
                    channel_id, 
                    info_video.get('comentarios', 0), 
                    info_video.get('likes', 0),
                    0,  # view_count no está disponible en el código proporcionado
                    scraped_at
                )
            )
            scrapper_result_id = cur.fetchone()[0]
            ids_generados['scrapper_result_id'] = scrapper_result_id
            
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
        print(f"Total de comentarios guardados: {len(ids_generados['comments_ids'])}")
        
    except Exception as e:
        print(f"Error al guardar en la base de datos: {e}")
        # Revertir cambios en caso de error
        if conn:
            conn.rollback()
    finally:
        # Cerrar cursor y conexión
        if cur:
            cur.close()
        if conn:
            conn.close()
    
    return ids_generados