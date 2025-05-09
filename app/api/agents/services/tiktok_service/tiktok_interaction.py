"""
Servicio para interacciones con la interfaz de TikTok.
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def esperar_elemento(driver, by, selector, tiempo=10):
    """
    Espera a que un elemento esté presente en la página.
    
    Args:
        driver: El driver de Selenium WebDriver
        by: El método de localización (By.ID, By.XPATH, etc.)
        selector: El selector para encontrar el elemento
        tiempo: Tiempo máximo de espera en segundos
        
    Returns:
        El elemento encontrado o None si no se encuentra
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
    """
    Activa los subtítulos en el video actual de TikTok.
    
    Args:
        driver: El driver de Selenium WebDriver
        
    Returns:
        bool: True si los subtítulos fueron activados, False en caso contrario
    """
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

def dar_like(driver):
    """
    Da like al video actual.
    
    Args:
        driver: El driver de Selenium WebDriver
        
    Returns:
        bool: True si se dio like correctamente, False en caso contrario
    """
    print("Intentando dar like...")

    try:
        # Esperar 1 segundo antes de intentar localizar el botón
        time.sleep(1)
        like_button = esperar_elemento(driver, By.XPATH, "//button[.//span[@data-e2e='like-icon']]", 2)
        if like_button:
            like_button.click()
            time.sleep(1)
            print("Like dado correctamente (método XPath)")
            return True

    except Exception as e:
        print(f"Error al dar like: {str(e)}")

    print("No se pudo dar like")
    return False

def pasar_siguiente_video(driver):
    """
    Pasa al siguiente video en el feed de TikTok.
    
    Args:
        driver: El driver de Selenium WebDriver
        
    Returns:
        bool: True si se pasó al siguiente video correctamente, False en caso contrario
    """
    print("Pasando al siguiente video...")
    
    try:
        # 1. Primero buscar y desactivar el ícono de repetición si existe
        try:
            # Usando JavaScript para evitar problemas de namespace en XPath
            icono_repetir = driver.execute_script("""
                return document.querySelector('svg[width="24"][height="24"][fill="#fff"] use[*|href="#Arrow_Counter_Clockwise-3e058a80"]');
            """)
            
            if icono_repetir:
                print("Ícono de repetición encontrado, haciendo clic para desactivarlo...")
                # Navegar hacia arriba para encontrar el elemento clicable
                elemento_clicable = driver.execute_script("""
                    var svg = arguments[0];
                    // Buscar hasta 3 niveles hacia arriba para encontrar un elemento clicable
                    var parent = svg.parentNode;
                    for (var i = 0; i < 3; i++) {
                        if (parent.tagName === 'BUTTON' || parent.tagName === 'DIV') {
                            return parent;
                        }
                        parent = parent.parentNode;
                        if (!parent) break;
                    }
                    return svg.parentNode; // Devolver el padre inmediato si no encontramos nada mejor
                """, icono_repetir)
                
                driver.execute_script("arguments[0].click();", elemento_clicable)
                time.sleep(1.5)
                print("Se hizo clic en el ícono de repetición exitosamente.")
        except Exception as e:
            print(f"No se encontró el ícono de repetición o no se pudo hacer clic: {e}")
        
        # 2. Luego intentar encontrar y hacer clic en el botón para pasar al siguiente video
        try:
            # Usar JavaScript para encontrar y hacer clic en el botón
            driver.execute_script("""
                var nextButton = document.querySelector('button[data-e2e="arrow-right"]');
                if (nextButton) {
                    nextButton.scrollIntoView({block: 'center'});
                    nextButton.click();
                    return true;
                }
                return false;
            """)
            
            time.sleep(1)
            print("Se pasó al siguiente video exitosamente.")
            return True
        except Exception as e:
            print(f"Error al hacer clic en el botón de siguiente video: {e}")
            
            # Intento alternativo usando Actions
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, 'button[data-e2e="arrow-right"]')
                actions = ActionChains(driver)
                actions.move_to_element(next_button).click().perform()
                time.sleep(3)
                print("Se pasó al siguiente video usando ActionChains.")
                return True
            except Exception as e2:
                print(f"También falló el intento alternativo: {e2}")
                return False

    except Exception as e:
        print(f"Error general al intentar pasar al siguiente video: {e}")
        return False