from dataclasses import dataclass
from time import sleep
import logging

from selenium.webdriver import Chrome
from selenium.common.exceptions import TimeoutException

from . import constants as c

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@dataclass
class Contact:
    name: str = None
    occupation: str = None
    url: str = None


@dataclass
class Institution:
    institution_name: str = None
    linkedin_url: str = None
    website: str = None
    industry: str = None
    type: str = None
    headquarters: str = None
    company_size: int = None
    founded: int = None


@dataclass
class Experience(Institution):
    from_date: str = None
    to_date: str = None
    description: str = None
    position_title: str = None
    duration: str = None
    location: str = None


@dataclass
class Education(Institution):
    from_date: str = None
    to_date: str = None
    description: str = None
    degree: str = None


@dataclass
class Interest(Institution):
    title = None


@dataclass
class Accomplishment(Institution):
    category = None
    title = None


@dataclass
class Scraper:
    driver: Chrome = None
    WAIT_FOR_ELEMENT_TIMEOUT = 5
    TOP_CARD = "pv-top-card"

    @staticmethod
    def wait(duration):
        sleep(int(duration))

    def focus(self):
        self.driver.execute_script('alert("Focus window")')
        self.driver.switch_to.alert.accept()

    def mouse_click(self, elem):
        action = webdriver.ActionChains(self.driver)
        action.move_to_element(elem).perform()

    def wait_for_element_to_load(self, by=By.CLASS_NAME, name="pv-top-card", base=None, timeout=None, log=False, default=None):
        """Wait for an element to be present on the page with improved error handling.
        
        Args:
            by: The locator strategy to use
            name: The name/value of the locator
            base: The driver or element to search within
            timeout: Custom timeout in seconds (overrides default)
            log: Whether to log timeouts
            default: Value to return if element isn't found
            
        Returns:
            The found element or default value if not found
        """
        base = base or self.driver
        timeout = timeout or self.WAIT_FOR_ELEMENT_TIMEOUT
        try:
            return WebDriverWait(base, timeout).until(
                EC.presence_of_element_located(
                    (
                        by,
                        name
                    )
                )
            )
        except TimeoutException as e:
            if log:
                print(f"Timeout waiting for element: {name}")
            return default

    def wait_for_all_elements_to_load(self, by=By.CLASS_NAME, name="pv-top-card", base=None, timeout=None, log=False, default=None):
        """Wait for all matching elements to be present on the page with improved error handling.
        
        Args:
            by: The locator strategy to use
            name: The name/value of the locator
            base: The driver or element to search within
            timeout: Custom timeout in seconds (overrides default)
            log: Whether to log timeouts
            default: Value to return if elements aren't found (default: empty list)
            
        Returns:
            The found elements or default value if not found
        """
        base = base or self.driver
        timeout = timeout or self.WAIT_FOR_ELEMENT_TIMEOUT
        default = default if default is not None else []
        
        try:
            return WebDriverWait(base, timeout).until(
                EC.presence_of_all_elements_located(
                    (
                        by,
                        name
                    )
                )
            )
        except TimeoutException as e:
            if log:
                print(f"Timeout waiting for elements: {name}")
            return default

    def is_signed_in(self):
        try:
            element = self.wait_for_element_to_load(
                By.CLASS_NAME, 
                c.VERIFY_LOGIN_ID,
                timeout=self.WAIT_FOR_ELEMENT_TIMEOUT
            )
            return element is not None
        except Exception as e:
            return False

    def scroll_to_half(self):
        self.driver.execute_script(
            "window.scrollTo(0, Math.ceil(document.body.scrollHeight/2));"
        )

    def scroll_to_bottom(self):
        self.driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);"
        )

    def scroll_class_name_element_to_page_percent(self, class_name:str, page_percent:float):
        self.driver.execute_script(
            f'elem = document.getElementsByClassName("{class_name}")[0]; elem.scrollTo(0, elem.scrollHeight*{str(page_percent)});'
        )

    def __find_element_by_class_name__(self, class_name):
        try:
            self.driver.find_element(By.CLASS_NAME, class_name)
            return True
        except:
            pass
        return False

    def __find_element_by_xpath__(self, tag_name):
        try:
            self.driver.find_element(By.XPATH,tag_name)
            return True
        except:
            pass
        return False

    def __find_enabled_element_by_xpath__(self, tag_name):
        try:
            elem = self.driver.find_element(By.XPATH,tag_name)
            return elem.is_enabled()
        except:
            pass
        return False

    @classmethod
    def __find_first_available_element__(cls, *args):
        for elem in args:
            if elem:
                return elem[0]
