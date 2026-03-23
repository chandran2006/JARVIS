from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import os

class WhatsAppDriver:
    _instance = None
    _driver = None

    @classmethod
    def get_driver(cls):
        # Check if existing driver is valid
        if cls._driver is not None:
            try:
                # This will raise an exception if the window is closed/crashed
                _ = cls._driver.current_url
            except Exception:
                print("Driver found but unresponsive. cleanup...")
                try:
                    cls._driver.quit()
                except Exception:
                    pass
                cls._driver = None
                
        if cls._driver is None:
            cls._driver = cls._init_driver()
        return cls._driver

    @staticmethod
    def _init_driver():
        print("Initializing Safari Driver...")
        try:
            # Safari doesn't need webdriver_manager, it's built-in on macOS.
            # You just need to enable 'Allow Remote Automation' in Safari > Develop menu.
            driver = webdriver.Safari()
            driver.maximize_window()
            return driver
        except Exception as e:
            print(f"Failed to initialize Safari: {e}")
            print("Ensure 'Allow Remote Automation' is enabled in Safari's Develop menu.")
            raise e
