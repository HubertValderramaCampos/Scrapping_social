"""
Servicio para extraer datos de canales, videos y comentarios de TikTok.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from datetime import datetime, timedelta
import re
import time

def extraer_datos_canal(driver):
    """
    Extrae información del canal de TikTok del video actual.
    
    Args:
        driver: El driver de Selenium WebDriver
        
    Returns:
        dict: Diccionario con URL y nombre del canal
    """
    time.sleep(1)  

    try:
        # Obtener URL actual
        full_url = driver.current_url

        # Limpiar URL: extraer solo https://www.tiktok.com/@username
        match = re.search(r"https://www\.tiktok\.com/@[a-zA-Z0-9._]+", full_url)
        clean_url = match.group(0) if match else None

        # Extraer nombre visible del canal (nickname)
        name_element = driver.find_element(By.CLASS_NAME, "css-1xccqfx-SpanNickName")
        name = name_element.text.strip()

        return {
            "url": clean_url,
            "name": name
        }

    except Exception as e:
        print(f"Error al extraer datos del canal: {e}")
        return {
            "url": None,
            "name": None
        }

def convertir_numero(texto):
    """
    Convierte números de formato TikTok (1.2K, 3.4M, etc.) a formato numérico.
    
    Args:
        texto: Texto que contiene el número a convertir
        
    Returns:
        int: Número convertido
    """
    if not texto:
        return 0
        
    texto = texto.strip().replace(',', '')
    
    if 'K' in texto or 'k' in texto:
        # Convertir miles (K)
        valor = float(texto.replace('K', '').replace('k', ''))
        return int(valor * 1000)
    elif 'M' in texto or 'm' in texto:
        # Convertir millones (M)
        valor = float(texto.replace('M', '').replace('m', ''))
        return int(valor * 1000000)
    elif 'B' in texto or 'b' in texto:
        # Convertir billones (B) - aunque es poco probable en TikTok
        valor = float(texto.replace('B', '').replace('b', ''))
        return int(valor * 1000000000)
    else:
        # Si no tiene sufijo, convertir directamente
        return int(texto)

def procesar_fecha(fecha_texto):
    """
    Convierte un texto de fecha de TikTok a un objeto datetime.
    
    Args:
        fecha_texto: Texto que contiene la fecha
        
    Returns:
        datetime: Objeto datetime con la fecha
    """
    fecha_actual = datetime.now()

    # Formato: "Hace X día(s)"
    if "Hace" in fecha_texto and "día" in fecha_texto:
        dias_regex = re.search(r'Hace (\d+)', fecha_texto)
        if dias_regex:
            dias_atras = int(dias_regex.group(1))
            return fecha_actual - timedelta(days=dias_atras)

    # Formato: "Hace X h" (horas) o "Hace X m" (minutos) → es hoy
    elif re.search(r'Hace \d+\s*[hm]', fecha_texto):
        return fecha_actual.replace(hour=0, minute=0, second=0, microsecond=0)

    # Formato: "X-Y" donde X es el mes e Y es el día
    elif re.match(r'^\d+-\d+$', fecha_texto):
        mes, dia = map(int, fecha_texto.split('-'))
        año = fecha_actual.year
        # Ajustar el año si la fecha es futura
        if mes > fecha_actual.month or (mes == fecha_actual.month and dia > fecha_actual.day):
            año -= 1
        return datetime(año, mes, dia)

    # Formato: "YYYY-MM-DD"
    elif re.match(r'^\d{4}-\d{1,2}-\d{1,2}$', fecha_texto):
        año, mes, dia = map(int, fecha_texto.split('-'))
        return datetime(año, mes, dia)

    # Si no se reconoce el formato, devolver la fecha actual
    return fecha_actual

def extraer_informacion_video(driver):
    """
    Extrae información general del video de TikTok.
    
    Args:
        driver: Objeto WebDriver de Selenium.
        
    Returns:
        Diccionario con la información extraída.
    """
    # Inicializar diccionario para almacenar la información
    resultado = {
        'likes': 0,
        'comentarios': 0,
        'fecha': None,
        'fecha_exacta': None
    }
    
    try:
        # Extraer número de likes
        likes_element = driver.find_element(By.CSS_SELECTOR, "strong[data-e2e='like-count']")
        if likes_element:
            resultado['likes'] = convertir_numero(likes_element.text)
    except Exception as e:
        print(f"Error al extraer likes: {e}")
    
    try:
        # Extraer número de comentarios
        comentarios_element = driver.find_element(By.CSS_SELECTOR, "strong[data-e2e='comment-count']")
        if comentarios_element:
            resultado['comentarios'] = convertir_numero(comentarios_element.text)
    except Exception as e:
        print(f"Error al extraer comentarios: {e}")
    
    try:
        # Intentar diferentes métodos para obtener la fecha
        fecha_element = None
        
        # Método 1: Buscar en el span que contiene la fecha
        try:
            fecha_element = driver.find_element(By.CSS_SELECTOR, "span[data-e2e='browser-nickname'] span:nth-child(3)")
        except NoSuchElementException:
            pass
        
        # Método 2: Buscar texto que contenga formatos de fecha comunes
        if not fecha_element:
            try:
                fecha_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'día') or contains(text(), '-') or contains(text(), 'Hace')]")
                if fecha_elements:
                    fecha_element = fecha_elements[0]
            except:
                pass
        
        if fecha_element:
            fecha_texto = fecha_element.text.strip()
            resultado['fecha'] = fecha_texto
            
            # Calcular la fecha exacta según el formato
            fecha_exacta = procesar_fecha(fecha_texto)
            resultado['fecha_exacta'] = fecha_exacta.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Error al extraer fecha: {e}")
    
    return resultado

def scrollear_comentarios(driver, max_intentos=20):
    """
    Scrollea para cargar todos los comentarios del video.
    
    Args:
        driver: El driver de Selenium WebDriver
        max_intentos: Número máximo de intentos de scrolleo
        
    Returns:
        int: Número de comentarios cargados
    """
    print("Scrolleando para cargar todos los comentarios...")
    
    # Encontrar el contenedor de comentarios
    try:
        comentarios_container = driver.find_element(By.CSS_SELECTOR, ".css-7whb78-DivCommentListContainer")
    except NoSuchElementException:
        print("No se encontró el contenedor de comentarios.")
        return 0
    
    # Número inicial de comentarios
    elementos_comentarios = driver.find_elements(By.CSS_SELECTOR, ".css-1gstnae-DivCommentItemWrapper")
    comentarios_iniciales = len(elementos_comentarios)
    comentarios_actuales = comentarios_iniciales
    
    print(f"Comentarios iniciales encontrados: {comentarios_iniciales}")
    
    intentos = 0
    sin_cambios = 0
    
    # Scrollear hasta cargar todos los comentarios o llegar al límite de intentos
    while intentos < max_intentos and sin_cambios < 3:
        # Hacer scroll al último comentario
        if elementos_comentarios:
            ultimo_comentario = elementos_comentarios[-1]
            driver.execute_script("arguments[0].scrollIntoView();", ultimo_comentario)
            
            # Esperar a que carguen más comentarios
            time.sleep(2)
            
            # Contar comentarios después del scroll
            elementos_comentarios = driver.find_elements(By.CSS_SELECTOR, ".css-1gstnae-DivCommentItemWrapper")
            nuevos_comentarios = len(elementos_comentarios)
            
            print(f"Intento {intentos+1}: {nuevos_comentarios} comentarios cargados")
            
            # Verificar si se cargaron más comentarios
            if nuevos_comentarios > comentarios_actuales:
                comentarios_actuales = nuevos_comentarios
                sin_cambios = 0
            else:
                sin_cambios += 1
        else:
            print("No se encontraron comentarios para hacer scroll.")
            break
        
        intentos += 1
    
    # Scrollear al inicio de los comentarios para procesarlos
    elementos_comentarios = driver.find_elements(By.CSS_SELECTOR, ".css-1gstnae-DivCommentItemWrapper")
    if elementos_comentarios:
        primer_comentario = elementos_comentarios[0]
        driver.execute_script("arguments[0].scrollIntoView();", primer_comentario)
    
    print(f"Total de comentarios cargados: {comentarios_actuales}")
    return comentarios_actuales

def extraer_comentarios(driver, limite=None):
    """
    Extrae la información de los comentarios de un video TikTok.
    
    Args:
        driver: El driver de Selenium WebDriver
        limite: Número máximo de comentarios a extraer (None para todos)
        
    Returns:
        list: Lista de diccionarios con información de comentarios
    """
    comentarios = []
    try:
        # Primero scrollear para cargar todos los comentarios
        total_comentarios = scrollear_comentarios(driver)
        
        # Encontrar todos los elementos de comentarios
        elementos_comentarios = driver.find_elements(By.CSS_SELECTOR, ".css-1gstnae-DivCommentItemWrapper")
        
        # Establecer límite (todos o un número específico)
        if limite is None or limite > total_comentarios:
            limite = total_comentarios
        
        print(f"Extrayendo {limite} comentarios de {total_comentarios} disponibles...")
        
        # Extraer la información de cada comentario
        for i, elemento in enumerate(elementos_comentarios[:limite]):
            comentario = {}
            
            # Extraer nombre de usuario
            try:
                usuario_element = elemento.find_element(By.CSS_SELECTOR, "div[data-e2e='comment-username-1'] p.TUXText--weight-medium")
                comentario['usuario'] = usuario_element.text
            except Exception as e:
                print(f"Error al extraer usuario del comentario {i+1}: {e}")
                comentario['usuario'] = "Desconocido"
            
            # Extraer contenido del comentario
            try:
                contenido_element = elemento.find_element(By.CSS_SELECTOR, "span[data-e2e='comment-level-1'] p")
                comentario['contenido'] = contenido_element.text
            except Exception as e:
                print(f"Error al extraer contenido del comentario {i+1}: {e}")
                comentario['contenido'] = ""
            
            # Extraer número de likes del comentario
            try:
                likes_element = elemento.find_element(By.CSS_SELECTOR, ".css-1nd5cw-DivLikeContainer span.TUXText--weight-normal")
                likes_texto = likes_element.text.strip()
                comentario['likes'] = convertir_numero(likes_texto) if likes_texto else 0
            except Exception as e:
                print(f"Error al extraer likes del comentario {i+1}: {e}")
                comentario['likes'] = 0
            
            # Extraer fecha del comentario
            try:
                # Intenta con un selector más específico basado en las clases TUXText
                fecha_elements = elemento.find_elements(By.CSS_SELECTOR, 
                    "span.TUXText.TUXText--tiktok-sans.TUXText--weight-normal[style*='color: var(--ui-text-3)']")
                
                if fecha_elements:
                    fecha_texto = fecha_elements[0].text.strip()
                    comentario['fecha'] = fecha_texto
                    fecha_exacta = procesar_fecha(fecha_texto)
                    comentario['fecha_exacta'] = fecha_exacta.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    # Intento alternativo con el selector original
                    fecha_elements = elemento.find_elements(By.CSS_SELECTOR, ".css-njhskk-DivCommentSubContentWrapper span")
                    if fecha_elements:
                        fecha_texto = fecha_elements[0].text.strip()
                        comentario['fecha'] = fecha_texto
                        fecha_exacta = procesar_fecha(fecha_texto)
                        comentario['fecha_exacta'] = fecha_exacta.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        # Último intento: buscar cualquier span con el formato de fecha
                        all_spans = elemento.find_elements(By.TAG_NAME, "span")
                        fecha_encontrada = False
                        for span in all_spans:
                            texto = span.text.strip()
                            # Comprobar si el texto parece una fecha (como "Hace 5 h" o "4-27")
                            if texto.startswith("Hace") or re.match(r'\d+-\d+', texto):
                                fecha_texto = texto
                                comentario['fecha'] = fecha_texto
                                fecha_exacta = procesar_fecha(fecha_texto)
                                comentario['fecha_exacta'] = fecha_exacta.strftime('%Y-%m-%d %H:%M:%S')
                                fecha_encontrada = True
                                break
                        
                        if not fecha_encontrada:
                            raise Exception("No se encontró el elemento de fecha")
            except Exception as e:
                print(f"Error al extraer fecha del comentario {i+1}: {e}")
                comentario['fecha'] = ""
                comentario['fecha_exacta'] = None
            
            comentarios.append(comentario)
            
            # Mostrar progreso
            if (i+1) % 10 == 0:
                print(f"Procesados {i+1} comentarios...")
        
        # Subir al principio del scroll
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)  # Opcional: para asegurar que la acción tenga efecto visual
    
    except Exception as e:
        print(f"Error general al extraer comentarios: {e}")
    
    return comentarios