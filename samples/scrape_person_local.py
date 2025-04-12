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

def init_driver(headless=False, cookies_file=None, user_data_dir=None):
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
    
    # If cookies file exists, load cookies into the driver
    if cookies_file and os.path.exists(cookies_file):
        load_cookies(driver, cookies_file)
        
    return driver

def save_cookies(driver, cookies_file):
    """Save the driver's cookies to a file"""
    # First navigate to LinkedIn to ensure cookies are for the right domain
    if "linkedin.com" not in driver.current_url:
        driver.get("https://www.linkedin.com")
        time.sleep(2)
    
    with open(cookies_file, 'wb') as file:
        pickle.dump(driver.get_cookies(), file)
    print(f"Cookies saved to {cookies_file}")

def load_cookies(driver, cookies_file):
    """Load cookies into the driver from a file"""
    # First navigate to LinkedIn to ensure we're on the right domain
    driver.get("https://www.linkedin.com")
    time.sleep(2)
    
    with open(cookies_file, 'rb') as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            # Some cookies might cause issues, so handle exceptions
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"Error adding cookie: {e}")
    
    # Refresh page to apply cookies
    driver.refresh()
    time.sleep(2)
    #print(f"Cookies loaded from {cookies_file}")

def login_to_linkedin(driver, email=None, password=None):
    """Login to LinkedIn using provided credentials"""
    if not email or not password:
        # Get credentials from environment variables
        email = os.getenv("LINKEDIN_USER")
        password = os.getenv("LINKEDIN_PASSWORD")
    
    actions.login(driver, email, password)
    time.sleep(3)  # Give time for the login to complete

def scrape_linkedin_profile(urls, output_format="json", headless=False, driver=None, close_driver=True, cookies_file=None, save_session=False):
    """
    Scrape LinkedIn profiles and return data in specified format
    
    Args:
        urls (list): List of LinkedIn profile URLs
        output_format (str): Format for output data ('json' or 'dict')
        headless (bool): Run browser in headless mode
        driver (WebDriver, optional): Existing WebDriver instance to reuse
        close_driver (bool): Whether to close the driver after scraping (default: True)
        cookies_file (str): Path to cookies file for session persistence
        save_session (bool): Whether to save the session after scraping
        
    Returns:
        tuple: (results, driver) - Results in requested format and the WebDriver instance (None if closed)
    """
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize driver if not provided
        driver_created = False
        if driver is None:
            driver = init_driver(headless, cookies_file)
            driver_created = True
        
        # Login to LinkedIn only if we created a new driver and cookies didn't establish a session
        if driver_created and (not cookies_file or not os.path.exists(cookies_file)):
            login_to_linkedin(driver, None, None)
        
        results = []
        for url in urls:
            try:
                person = Person(url, driver=driver, close_on_complete=False)
                # Remove the print statement as it's not needed
                
                # Convert Person object to a dictionary with all attributes
                person_data = {
                    "name": getattr(person, "name", None),
                    "company": getattr(person, "company", None),
                    "job_title": getattr(person, "job_title", None),
                    "location": getattr(person, "location", None),
                    "about": getattr(person, "about", None),
                    "open_to_work": getattr(person, "open_to_work", False),
                    "linkedin_url": getattr(person, "linkedin_url", url),
                    "url": url
                }
                
                # Handle experiences with all their attributes
                person_data["experiences"] = []
                if hasattr(person, "experiences"):
                    for exp in person.experiences:
                        person_data["experiences"].append({
                            "title": getattr(exp, "position_title", None),
                            "company": getattr(exp, "institution_name", None), 
                            "linkedin_url": getattr(exp, "linkedin_url", None),
                            "from_date": getattr(exp, "from_date", None),
                            "to_date": getattr(exp, "to_date", None),
                            "duration": getattr(exp, "duration", None),
                            "description": getattr(exp, "description", None),
                            "location": getattr(exp, "location", None)
                        })
                
                # Handle educations with all attributes
                person_data["educations"] = []
                if hasattr(person, "educations") and person.educations:
                    for edu in person.educations:
                        person_data["educations"].append({
                            "institution": getattr(edu, "institution_name", None),
                            "linkedin_url": getattr(edu, "linkedin_url", None),
                            "degree": getattr(edu, "degree", None),
                            "from_date": getattr(edu, "from_date", None),
                            "to_date": getattr(edu, "to_date", None),
                            "description": getattr(edu, "description", None)
                        })
                
                # Convert interests to a list of dictionaries
                person_data["interests"] = []
                if hasattr(person, "interests") and person.interests:
                    for interest in person.interests:
                        person_data["interests"].append({
                            "name": getattr(interest, "name", None)
                        })
                
                # Convert accomplishments to a list of dictionaries
                person_data["accomplishments"] = []
                if hasattr(person, "accomplishments") and person.accomplishments:
                    for acc in person.accomplishments:
                        person_data["accomplishments"].append({
                            "category": getattr(acc, "category", None),
                            "title": getattr(acc, "title", None)
                        })
                
                # Convert contacts to a list of dictionaries
                person_data["contacts"] = []
                if hasattr(person, "contacts") and person.contacts:
                    for contact in person.contacts:
                        person_data["contacts"].append({
                            "name": getattr(contact, "name", None),
                            "occupation": getattr(contact, "occupation", None),
                            "url": getattr(contact, "url", None)
                        })
                
                results.append(person_data)
            except Exception as e:
                results.append({
                    "url": url,
                    "error": str(e),
                    "success": False
                })
        
        # Save session if requested
        if save_session and cookies_file:
            save_cookies(driver, cookies_file)
        
        # Close driver only if requested
        if close_driver:
            driver.quit()
            driver = None
        
        if output_format == "json":
            return json.dumps(results), driver
        else:
            return results, driver
            
    except WebDriverException as e:
        error_data = {"error": "WebDriver error: " + str(e), "success": False}
        if output_format == "json":
            return json.dumps(error_data), None
        else:
            return error_data, None
    except Exception as e:
        error_data = {"error": "Unexpected error: " + str(e), "success": False}
        if output_format == "json":
            return json.dumps(error_data), None
        else:
            return error_data, None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape LinkedIn profiles")
    parser.add_argument("urls", nargs="+", help="LinkedIn profile URLs to scrape")
    parser.add_argument("--output", choices=["json", "dict"], default="json", 
                        help="Output format (json or dict)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--keep-browser", action="store_true", help="Keep browser open after scraping")
    parser.add_argument("--cookies-file", help="Path to save/load cookies for session persistence")
    parser.add_argument("--save-session", action="store_true", help="Save session cookies after scraping")
    
    args = parser.parse_args()
    
    # Resolve cookies_file to an absolute path if it's provided
    cookies_file = None
    if args.cookies_file:
        # print('Original cookies file path:', args.cookies_file)
        
        # Get the directory of the script itself
        script_dir = os.path.dirname(os.path.realpath(__file__))
        
        # If the path doesn't contain a directory separator, store it in the script directory
        if os.path.dirname(args.cookies_file) == '':
            cookies_file = os.path.join(script_dir, args.cookies_file)
        else:
            # Otherwise use the absolute path of what was provided
            cookies_file = os.path.abspath(args.cookies_file)
            
        # print('Absolute cookies file path:', cookies_file)
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(cookies_file) or '.', exist_ok=True)
    
    result, driver = scrape_linkedin_profile(
        args.urls, 
        args.output, 
        args.headless, 
        close_driver=not args.keep_browser,
        cookies_file=cookies_file,
        save_session=args.save_session
    )
    
    if args.output == "json":
        print(result)
    else:
        print(json.dumps(result))
        
    # Note: The browser will remain open only if --keep-browser was specified
    # You can use --cookies-file to save the session and reuse it later