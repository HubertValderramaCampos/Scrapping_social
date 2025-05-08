from selenium.webdriver.common.by import By
import time
import re

def ext_data_ch(driver):

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
        print(f"Error al extraer datos: {e}")
        return {
            "url": None,
            "name": None
        }
