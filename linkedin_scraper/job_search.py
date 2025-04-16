import os
from typing import List
from time import sleep
import urllib.parse

from .objects import Scraper
from . import constants as c
from .jobs import Job

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


class JobSearch(Scraper):
    AREAS = ["recommended_jobs", None, "still_hiring", "more_jobs"]

    def __init__(self, driver, base_url="https://www.linkedin.com/jobs/", close_on_complete=False, scrape=True, scrape_recommended_jobs=True):
        super().__init__()
        self.driver = driver
        self.base_url = base_url

        if scrape:
            self.scrape(close_on_complete, scrape_recommended_jobs)


    def scrape(self, close_on_complete=True, scrape_recommended_jobs=True):
        if self.is_signed_in():
            self.scrape_logged_in(close_on_complete=close_on_complete, scrape_recommended_jobs=scrape_recommended_jobs)
        else:
            raise NotImplemented("This part is not implemented yet")


    def scrape_job_card(self, base_element) -> Job:
        try:
            # Updated to use the new Selenium API
            job_div = self.wait_for_element_to_load(name="job-card-list__title--link", base=base_element, log=True)
            if not job_div:
                print("Job title element not found")
                return None
                
            job_title = job_div.text.strip()
            linkedin_url = job_div.get_attribute("href")
            
            # Updated from find_element_by_class_name to find_element(By.CLASS_NAME, ...)
            company_elem = base_element.find_element(By.CLASS_NAME, "artdeco-entity-lockup__subtitle")
            company = company_elem.text if company_elem else "Unknown Company"
            
            location_elem = base_element.find_element(By.CLASS_NAME, "job-card-container__metadata-wrapper")
            location = location_elem.text if location_elem else "Unknown Location"
            
            job = Job(linkedin_url=linkedin_url, job_title=job_title, company=company, location=location, scrape=False, driver=self.driver)
            return job
        except Exception as e:
            print(f"Error scraping job card: {str(e)}")
            return None


    def scrape_logged_in(self, close_on_complete=True, scrape_recommended_jobs=True):
        driver = self.driver
        driver.get(self.base_url)
        if scrape_recommended_jobs:
            self.focus()
            sleep(self.WAIT_FOR_ELEMENT_TIMEOUT)
            job_area = self.wait_for_element_to_load(name="scaffold-finite-scroll__content", log=True)
            if not job_area:
                print("Job area not found")
                return
                
            areas = self.wait_for_all_elements_to_load(name="artdeco-card", base=job_area, log=True)
            for i, area in enumerate(areas):
                area_name = self.AREAS[i]
                if not area_name:
                    continue
                area_results = []
                # Updated from find_elements_by_class_name to find_elements(By.CLASS_NAME, ...)
                for job_posting in area.find_elements(By.CLASS_NAME, "jobs-job-board-list__item"):
                    job = self.scrape_job_card(job_posting)
                    if job:
                        area_results.append(job)
                setattr(self, area_name, area_results)
        return


    def search(self, search_term: str) -> List[Job]:
        url = os.path.join(self.base_url, "search") + f"?keywords={urllib.parse.quote(search_term)}&refresh=true"
        self.driver.get(url)
        self.scroll_to_bottom()
        self.focus()
        sleep(self.WAIT_FOR_ELEMENT_TIMEOUT)

        # Try multiple possible class names for job listings container
        job_listing = None
        possible_class_names = [
            "jobs-search__job-details",
            "scaffold-layout__detail",
            "jobs-search-results-list",
            "jobs-search-two-pane__details"
        ]
        
        for class_name in possible_class_names:
            print(f"Looking for job listing with class name: {class_name}")
            job_listing = self.wait_for_element_to_load(name=class_name, timeout=3, log=True)
            if job_listing:
                print(f"Found job listing with class name: {class_name}")
                break
                
        if not job_listing:
            print("Could not find job listing container, trying XPath approach")
            try:
                # Try finding job details by a more specific XPath
                job_listing = self.wait_for_element_to_load(
                    by=By.XPATH, 
                    name="//div[contains(@class, 'jobs-search__job-details') or contains(@class, 'jobs-details')]",
                    timeout=5, 
                    log=True
                )
            except:
                print("XPath approach failed, returning empty results")
                return []

        if not job_listing:
            print("Could not find job listings on the page")
            return []
            
        # Scroll through the page to load all job elements
        self.scroll_to_bottom()
        sleep(1)
        self.scroll_to_half()
        sleep(1)
        
        # Try different selectors for job cards
        job_cards = []
        possible_card_selectors = [
            "job-card-list",
            "jobs-search-results__list-item",
            "job-card-container",
            "jobs-search-result-item"
        ]
        
        for selector in possible_card_selectors:
            cards = self.wait_for_all_elements_to_load(name=selector, base=self.driver, timeout=3, log=False, default=[])
            if cards:
                print(f"Found job cards with selector: {selector}")
                job_cards = cards
                break
                
        if not job_cards:
            # Try finding job cards by XPath
            try:
                job_cards = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'jobs-search-results__list-item')]")
                print(f"Found {len(job_cards)} job cards by XPath")
            except:
                pass
                
        job_results = []
        for job_card in job_cards:
            job = self.scrape_job_card(job_card)
            if job:
                job_results.append(job)
                
        print(f"Found {len(job_results)} job results")
        return job_results
