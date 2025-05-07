"""
Browser automation service for TikTok scraping.
"""
import os
import json
import time
from typing import List, Dict, Any, Optional

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from fastapi import HTTPException

class TikTokBrowser:
    """Class for managing browser automation for TikTok interactions."""
    
    def __init__(self, cookies_path: str = "cookies.json"):
        """
        Initialize the TikTok browser manager.
        
        Args:
            cookies_path: Path to the JSON file containing TikTok cookies
        """
        self.cookies_path = cookies_path
        self.driver = None
        
    def _setup_browser(self):
        """
        Set up and configure the Chrome browser for TikTok automation.
        
        Returns:
            The configured browser driver
        """
        try:
            # Configure Chrome options
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-notifications")
            
            # Enable audio
            options.add_argument("--autoplay-policy=no-user-gesture-required")
            
            # Critical: Enable tab audio capture
            options.add_argument("--enable-features=TabAudioCapturing")
            
            # Create the browser instance
            driver = uc.Chrome(options=options, version_main=135)
            
            # Set window size to a common resolution
            driver.set_window_size(1280, 800)
            
            return driver
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to set up browser: {str(e)}"
            )
    
    def _load_cookies(self, driver):
        """
        Load cookies from a file and add them to the browser.
        
        Args:
            driver: The browser driver
            
        Returns:
            int: Number of successfully loaded cookies
        """
        # Check if cookies file exists
        if not os.path.exists(self.cookies_path):
            raise HTTPException(
                status_code=404,
                detail=f"Cookies file not found: {self.cookies_path}"
            )
        
        # Load cookies from file
        try:
            with open(self.cookies_path, "r", encoding="utf-8") as f:
                cookies = json.load(f)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON in cookies file: {self.cookies_path}"
            )
        
        if not cookies or not isinstance(cookies, list):
            raise HTTPException(
                status_code=400,
                detail="Cookies file contains invalid data"
            )
        
        # Delete existing cookies
        driver.delete_all_cookies()
        time.sleep(1)
        
        # Add cookies to browser
        valid_cookies = 0
        for cookie in cookies:
            try:
                # Verify required fields
                if 'name' not in cookie or 'value' not in cookie:
                    print(f"Skipping invalid cookie: {cookie}")
                    continue
                
                # Create a clean cookie dictionary
                cookie_dict = {
                    'name': cookie['name'],
                    'value': cookie['value']
                }
                
                # Add optional attributes
                for attr in ['domain', 'path', 'secure', 'httpOnly', 'expiry']:
                    if attr in cookie and cookie[attr] is not None:
                        cookie_dict[attr] = cookie[attr]
                
                # Set domain if missing
                if 'domain' not in cookie_dict or not cookie_dict['domain']:
                    cookie_dict['domain'] = '.tiktok.com'
                
                # Fix sameSite format if needed
                if 'sameSite' in cookie:
                    if cookie['sameSite'] and cookie['sameSite'].lower() in ['strict', 'lax', 'none']:
                        cookie_dict['sameSite'] = cookie['sameSite'].capitalize()
                
                # Add the cookie
                driver.add_cookie(cookie_dict)
                valid_cookies += 1
                
            except Exception as e:
                print(f"Error adding cookie {cookie.get('name', 'unknown')}: {str(e)}")
        
        print(f"Successfully added {valid_cookies} of {len(cookies)} cookies")
        return valid_cookies
    
    def _debug_cookies(self, driver):
        """
        Debug cookies to verify they were loaded correctly.
        
        Args:
            driver: The browser driver
            
        Returns:
            list: The cookies in the browser
        """
        cookies = driver.get_cookies()
        print(f"Number of cookies: {len(cookies)}")
        for i, cookie in enumerate(cookies[:5]):  # Show first 5 cookies only
            print(f"Cookie {i+1}: {cookie.get('name')} = {cookie.get('value')[:10]}...")
        return cookies
    
    def navigate_to_tiktok(self):
        """
        Navigate to TikTok with authentication.
        
        Returns:
            The configured browser driver with TikTok loaded
        """
        try:
            # Set up browser
            self.driver = self._setup_browser()
            
            # Navigate to TikTok
            print("Opening TikTok...")
            self.driver.get("https://www.tiktok.com/")
            time.sleep(5)
            
            # Load cookies
            valid_cookies = self._load_cookies(self.driver)
            
            # Debug cookies
            loaded_cookies = self._debug_cookies(self.driver)
            if len(loaded_cookies) < 2:
                print("WARNING: Very few cookies loaded, authentication may fail")
            
            # Refresh page with cookies
            print("Reloading with cookies...")
            self.driver.refresh()
            time.sleep(5)
            
            # Navigate to "For You" feed
            self._navigate_to_for_you()
            
            return self.driver
            
        except Exception as e:
            # Clean up on error
            if self.driver:
                self.driver.quit()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to navigate to TikTok: {str(e)}"
            )
    
    def _navigate_to_for_you(self):
        """Navigate to the 'For You' feed on TikTok."""
        try:
            print("Looking for 'For You' button...")
            para_ti_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Para ti']"))
            )
            para_ti_button.click()
            print("Successfully navigated to 'For You' feed")
        except TimeoutException:
            # Go directly to the feed if button not found
            print("Timeout waiting for 'For You' button, navigating directly")
            self.driver.get("https://www.tiktok.com/foryou")
            time.sleep(3)
    
    def get_video_info(self):
        """
        Get information about the current TikTok video.
        
        Returns:
            dict: Video information (URL, username, description)
        """
        try:
            # Wait for video to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//video[contains(@class, 'tiktok-video')]"))
            )
            
            # Get video URL
            video_url = self.driver.current_url
            
            # Get username
            try:
                username = self.driver.find_element(By.XPATH, "//span[contains(@class, 'author-uniqueId')]").text
            except NoSuchElementException:
                username = "No disponible"
            
            # Get description
            try:
                description = self.driver.find_element(By.XPATH, "//div[contains(@class, 'video-desc')]").text
            except NoSuchElementException:
                description = "No disponible"
            
            return {
                "video_url": video_url,
                "username": username,
                "description": description
            }
        except Exception as e:
            print(f"Error getting video info: {str(e)}")
            return {
                "video_url": self.driver.current_url,
                "username": "Error",
                "description": f"Error: {str(e)}"
            }
    
    def scroll_to_next_video(self):
        """Scroll to the next video in the feed."""
        try:
            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(3)  # Wait for next video to load
            return True
        except Exception as e:
            print(f"Error scrolling to next video: {str(e)}")
            return False
    
    def close(self):
        """Close the browser and clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None