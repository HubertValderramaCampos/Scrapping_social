from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from datetime import datetime, timedelta
import re
import time
import json

def convertir_numero(texto):
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

def extraer_informacion(driver):
 
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
        # Extraer fecha
        # Buscar en el contenedor de información del usuario
        fecha_element = None
        try:
            fecha_element = driver.find_element(By.CSS_SELECTOR, "span[data-e2e='browser-nickname'] span:nth-child(3)")
        except NoSuchElementException:
            # Intentar buscar en otros lugares donde pueda estar la fecha
            try:
                fecha_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'día')]")
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

def procesar_fecha(fecha_texto):
  
    fecha_actual = datetime.now()
    
    # Formato: "Hace X día(s)"
    if "Hace" in fecha_texto and "día" in fecha_texto:
        dias_regex = re.search(r'Hace (\d+)', fecha_texto)
        if dias_regex:
            dias_atras = int(dias_regex.group(1))
            return fecha_actual - timedelta(days=dias_atras)
    
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

def scrollear_comentarios(driver, max_intentos=20):
   
    print("Scrolleando para cargar todos los comentarios...")
    
    # Encontrar el contenedor de comentarios
    try:
        comentarios_container = driver.find_element(By.CSS_SELECTOR, ".css-1sg2lsz-DivCommentListContainer")
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
        ultimo_comentario = driver.find_elements(By.CSS_SELECTOR, ".css-1gstnae-DivCommentItemWrapper")[-1]
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
        
        intentos += 1
    
    # Scrollear al inicio de los comentarios para procesarlos
    primer_comentario = driver.find_elements(By.CSS_SELECTOR, ".css-1gstnae-DivCommentItemWrapper")[0]
    driver.execute_script("arguments[0].scrollIntoView();", primer_comentario)
    
    print(f"Total de comentarios cargados: {comentarios_actuales}")
    return comentarios_actuales

def extraer_comentarios(driver, limite=None):
  
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
                usuario_element = elemento.find_element(By.CSS_SELECTOR, "p.TUXText--weight-medium[letter-spacing='0.09380000000000001']")
                comentario['usuario'] = usuario_element.text
            except:
                comentario['usuario'] = "Desconocido"
            
            # Extraer contenido del comentario
            try:
                contenido_element = elemento.find_element(By.CSS_SELECTOR, "span[data-e2e='comment-level-1'] p")
                comentario['contenido'] = contenido_element.text
            except:
                comentario['contenido'] = ""
            
            # Extraer número de likes del comentario
            try:
                likes_element = elemento.find_element(By.CSS_SELECTOR, ".css-1nd5cw-DivLikeContainer .TUXText--weight-normal")
                likes_texto = likes_element.text.strip()
                comentario['likes'] = convertir_numero(likes_texto) if likes_texto else 0
            except Exception as e:
                comentario['likes'] = 0
                print(f"Error al extraer likes del comentario {i+1}: {e}")
            
            # Extraer fecha del comentario
            try:
                fecha_element = elemento.find_element(By.CSS_SELECTOR, ".css-njhskk-DivCommentSubContentWrapper span:first-child")
                fecha_texto = fecha_element.text.strip()
                comentario['fecha'] = fecha_texto
                fecha_exacta = procesar_fecha(fecha_texto)
                comentario['fecha_exacta'] = fecha_exacta.strftime('%Y-%m-%d %H:%M:%S')
            except:
                comentario['fecha'] = ""
                comentario['fecha_exacta'] = None
            
            comentarios.append(comentario)
            
            # Mostrar progreso
            if (i+1) % 10 == 0:
                print(f"Procesados {i+1} comentarios...")
    
    except Exception as e:
        print(f"Error al extraer comentarios: {e}")
    
    return comentarios


def mostrar_resultados(info, comentarios):

    print("\n===== INFORMACIÓN DEL VIDEO =====")
    print(f"Likes: {info['likes']}")
    print(f"Comentarios: {info['comentarios']}")
    print(f"Fecha: {info['fecha']} (Calculada: {info['fecha_exacta']})")
    
    print("\n===== COMENTARIOS =====")
    for i, comentario in enumerate(comentarios, 1):
        print(f"\nComentario #{i}:")
        print(f"  Usuario: {comentario['usuario']}")
        print(f"  Contenido: {comentario['contenido']}")
        print(f"  Likes: {comentario['likes']}")
        print(f"  Fecha: {comentario['fecha']} (Calculada: {comentario['fecha_exacta']})")

