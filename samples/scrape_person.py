import os
import json
import time
import sys
import argparse
import pickle
from pathlib import Path
from dotenv import load_dotenv
from linkedin_scraper import Person, actions
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

headless=False
cookies_file=None
user_data_dir=None
"""Initialize and return a Chrome WebDriver"""
chrome_options = Options()

if headless:
    chrome_options.add_argument("--headless")
else:
    chrome_options.add_experimental_option("detach", True)

# If user_data_dir is provided, use it to maintain session information
if user_data_dir:
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
chrome_service = Service(executable_path="/opt/homebrew/bin/chromedriver")

driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

email = os.getenv("LINKEDIN_USER")
password = os.getenv("LINKEDIN_PASSWORD")
actions.login(driver, email, password) # if email and password isnt given, it'll prompt in terminal
person = Person("https://www.linkedin.com/in/andre-iguodala-65b48ab5", driver=driver)
