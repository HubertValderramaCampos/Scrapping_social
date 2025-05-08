import os
import time
import openai
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException




client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def es_politica_peru(texto: str) -> bool:
    """
    Analiza si un texto está relacionado con temas políticos o sociales del Perú.
    """
    system_prompt = (
        "Eres un analizador de contenido experto en identificar cualquier mención o alusión a temas políticos o sociales del Perú. "
        "Analiza el siguiente texto, que corresponde a subtítulos de un video de TikTok. Debes detectar si el contenido presenta "
        "cualquier referencia, directa o indirecta, a política peruana o asuntos sociales relevantes del país. Esto incluye, pero no se limita a: "
        "protestas, denuncias ciudadanas, problemáticas sociales, corrupción, acciones del gobierno, decisiones estatales, "
        "crisis institucionales, afectaciones a comunidades, conflictos sociales, políticas públicas, y menciones a políticos, autoridades, "
        "funcionarios públicos, candidatos, expresidentes, congresistas o figuras públicas asociadas a la política nacional. "
        "Responde únicamente con 'true' si el texto está relacionado con cualquiera de estos temas. En caso contrario, responde 'false'."
    )

    user_prompt = f'Texto: "{texto}"'

    try:
        respuesta = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            max_tokens=5
        )

        contenido = respuesta.choices[0].message.content.strip().lower()
        if contenido.startswith("true"):
            return True
        elif contenido.startswith("false"):
            return False
        else:
            return False

    except Exception as e:
        print(f"Error con OpenAI: {e}")
        return False



def esperar_elemento(driver, by, selector, tiempo=10):

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


def dar_like(driver):
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
    print("Pasando al siguiente video...")

    try:
        # Verificar si existe el icono de 'Noticias' antes de proceder
        selector_noticias = 'svg use[xlink\\:href="#Arrow_Counter_Clockwise-3e058a80"]'
        icono_noticias = driver.find_elements(By.CSS_SELECTOR, selector_noticias)

        # Si encontramos el icono de 'Noticias', hacer clic
        if icono_noticias:
            print("Icono de 'Noticias' encontrado, haciendo clic...")
            contenedor_icono = driver.find_element(By.CSS_SELECTOR, 'svg use[xlink\\:href="#Arrow_Counter_Clockwise-3e058a80"]')
            contenedor_icono.click()
            time.sleep(1)

        # Verificar si existe el botón para repetir y hacer clic en él si está presente
        try:
            selector_repetir = 'div.css-q1bwae-DivPlayIconContainer.e1ya9dnw8 svg use[xlink\\:href="#Arrow_Counter_Clockwise-3e058a80"]'
            icono_repetir = driver.find_elements(By.CSS_SELECTOR, selector_repetir)

            if icono_repetir:
                print("Ícono de repetir encontrado, haciendo clic para desactivarlo...")
                contenedor_icono_repetir = driver.find_element(By.CSS_SELECTOR, 'div.css-q1bwae-DivPlayIconContainer.e1ya9dnw8')
                contenedor_icono_repetir.click()
                time.sleep(1)
        except Exception as e:
            print(f"No se encontró el botón de repetir: {e}")

        # Intentar encontrar y hacer clic en el botón para pasar al siguiente video
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, 'button[data-e2e="arrow-right"], button[aria-label="Siguiente video"]')
            next_button.click()
            time.sleep(3)
            print("Se pasó al siguiente video exitosamente.")
            return True
        except Exception as e:
            print("No se encontró el botón para pasar al siguiente video.")
            return False

    except Exception as e:
        print(f"Error al intentar pasar al siguiente video: {e}")
        return False