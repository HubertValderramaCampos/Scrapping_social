import os
import openai
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

openai.api_key = os.getenv("OPENAI_API_KEY")

async def es_politica_peru(texto: str) -> bool:

    # Construir el prompt para GPT
    system_prompt = (
        "Eres un analizador de contenido experto en identificar cualquier mención o alusión a temas políticos o sociales del Perú. "
        "Analiza el siguiente texto, que corresponde a subtítulos de un video de TikTok. Debes detectar si el contenido presenta "
        "cualquier referencia, directa o indirecta, a política peruana o asuntos sociales relevantes del país. Esto incluye, pero no se limita a: "
        "protestas, denuncias ciudadanas, problemáticas sociales, corrupción, acciones del gobierno, decisiones estatales, "
        "crisis institucionales, afectaciones a comunidades, conflictos sociales, políticas públicas, y menciones a políticos, autoridades, "
        "funcionarios públicos, candidatos, expresidentes, congresistas o figuras públicas asociadas a la política nacional. "
        "Responde únicamente con 'true' si el texto está relacionado con cualquiera de estos temas. En caso contrario, responde 'false'."
    )


    user_prompt = f"Texto: \"{texto}\""

    try:
        respuesta = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            max_tokens=5
        )

        contenido = respuesta.choices[0].message.content.strip().lower()
        # Interpretar la respuesta de GPT
        if contenido.startswith('true'):
            return True
        elif contenido.startswith('false'):
            return False
        else:
            # En caso inesperado, considerar como False
            return False

    except Exception as e:
        return False


def esperar_elemento(driver, by, selector, tiempo=10):
    """
    Espera a que un elemento esté presente en la página.
    
    Args:
        driver: El driver de Selenium WebDriver
        by: El método de localización (Por ejemplo, By.TAG_NAME)
        selector: El selector para encontrar el elemento
        tiempo: Tiempo máximo de espera en segundos
        
    Returns:
        El elemento si se encuentra, None si no
    """
    try:
        elemento = WebDriverWait(driver, tiempo).until(
            EC.presence_of_element_located((by, selector))
        )
        return elemento
    except (TimeoutException, NoSuchElementException):
        print(f"No se pudo encontrar el elemento {selector}")
        return None


def activar_subtitulos(driver):
    print("Activando subtítulos...")

    try:
        # Esperar a que el video esté presente
        video_element = esperar_elemento(driver, By.TAG_NAME, "video")
        if not video_element:
            print("No se encontró el elemento de video.")
            return False

        # Hacer clic derecho en el video
        actions = ActionChains(driver)
        actions.context_click(video_element).perform()
        time.sleep(1)

        # Clic en "Ver detalles del video"
        detalles = esperar_elemento(driver, By.XPATH, 
            "//div[@data-e2e='right-click-menu-popover_view-video-details' or contains(text(), 'Ver detalles del video')]", 3)
        detalles.click()
        time.sleep(1)

        # Clic en "Más opciones"
        mas_opciones = esperar_elemento(driver, By.XPATH, 
            "//div[@data-e2e='more-menu' or contains(text(), 'Más opciones')]", 3)
        mas_opciones.click()
        time.sleep(1)

        # Clic en "Subtítulos"
        subtitulos_option = esperar_elemento(driver, By.XPATH, 
            "//div[@data-e2e='more-menu-popover_caption' or contains(text(), 'Subtítulos') or contains(text(), 'Captions')]", 3)
        subtitulos_option.click()
        time.sleep(1)

        # Activar el switch de subtítulos
        switch = esperar_elemento(driver, By.CSS_SELECTOR, "input.TUXSwitch-input", 3)
        if switch and not switch.is_selected():
            switch.click()
            print("Switch de subtítulos activado")

        time.sleep(2)

        # Cerrar el menú
        close_button = esperar_elemento(driver, By.CSS_SELECTOR, 
            "button.TUXUnstyledButton.TUXNavBarIconButton[aria-label='close'], button[aria-label='cerrar']", 3)
        if close_button:
            close_button.click()

        print("Subtítulos activados exitosamente")
        return True

    except Exception as e:
        print(f"Error al activar subtítulos: {str(e)}")
        return False


def dar_like(driver, intentos_max=3):
    """
    Da like al video actual.
    
    Args:
        driver: El driver de Selenium WebDriver
        intentos_max: Número máximo de intentos
    
    Returns:
        True si se dio like, False si no
    """
    print("Intentando dar like...")
    
    for intento in range(intentos_max):
        try:
            # Primer método: selector CSS específico
            like_button = esperar_elemento(driver, By.CSS_SELECTOR, 
                "button.css-nmbm7z-ButtonActionItem[data-e2e='like-icon'], button[data-e2e='like-icon']", 2)
            
            if like_button:
                like_button.click()
                time.sleep(1)
                print(f"Like dado correctamente (método 1, intento {intento+1})")
                return True
                
            # Segundo método: mediante XPath
            like_button = esperar_elemento(driver, By.XPATH, "//button[.//span[@data-e2e='like-icon']]", 2)
            if like_button:
                like_button.click()
                time.sleep(1)
                print(f"Like dado correctamente (método 2, intento {intento+1})")
                return True
                
            # Tercer método: buscar por texto o atributo aria-label
            like_button = esperar_elemento(driver, By.XPATH, 
                "//button[contains(@aria-label, 'like') or contains(@aria-label, 'Me gusta')]", 2)
            if like_button:
                like_button.click()
                time.sleep(1)
                print(f"Like dado correctamente (método 3, intento {intento+1})")
                return True
                
        except Exception as e:
            print(f"Error al dar like (intento {intento+1}/{intentos_max}): {str(e)}")
            time.sleep(1)
    
    print("No se pudo dar like después de varios intentos")
    return False
            
            
def pasar_siguiente_video(driver, intentos_max=3):
    """
    Pasa al siguiente video en TikTok.
    
    Args:
        driver: El driver de Selenium WebDriver
        intentos_max: Número máximo de intentos
        
    Returns:
        True si se pasó al siguiente video, False si no
    """
    print("Pasando al siguiente video...")
    
    for intento in range(intentos_max):
        try:
            # Primer método: botón de flecha derecha
            next_button = esperar_elemento(driver, By.CSS_SELECTOR, 
                'button[data-e2e="arrow-right"], button[aria-label="Siguiente video"]', 2)
            
            if next_button:
                next_button.click()
                time.sleep(3)  # Esperamos más tiempo para que cargue el nuevo video
                print(f"Se pasó al siguiente video (método 1, intento {intento+1})")
                return True
                
            # Segundo método: pulsando la tecla flecha abajo
            video_element = esperar_elemento(driver, By.TAG_NAME, "video", 2)
            if video_element:
                actions = ActionChains(driver)
                actions.send_keys('\ue015')  # Código para la tecla flecha abajo
                actions.perform()
                time.sleep(3)
                print(f"Se pasó al siguiente video (método 2, intento {intento+1})")
                return True
                
        except Exception as e:
            print(f"Error al pasar al siguiente video (intento {intento+1}/{intentos_max}): {str(e)}")
            time.sleep(1)
    
    print("No se pudo pasar al siguiente video después de varios intentos")
    return False
    
    
def hay_subtitulos_visibles(driver):
    """
    Verifica si hay subtítulos visibles en la pantalla.
    
    Args:
        driver: El driver de Selenium WebDriver
        
    Returns:
        True si hay subtítulos visibles, False si no
    """
    try:
        # Buscar elementos de subtítulos con diferentes selectores posibles
        subtitulos = driver.find_elements(By.CSS_SELECTOR, ".caption-container, .tiktok-caption-container, .tt-caption")
        return len(subtitulos) > 0
    except:
        return False