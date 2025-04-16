import os
from typing import List
from time import sleep
import urllib.parse

from .objects import Scraper
from .jobs import Job
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

class PeopleSearch(Scraper):
    AREAS = ["recommended_jobs", None, "still_hiring", "more_jobs"]

    def __init__(self, driver, base_url="https://www.linkedin.com/", close_on_complete=False, scrape=True, scrape_recommended_jobs=True):
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


    def scrape_people_card(self, base_element) -> Job:
        print(f"[DEBUG] scrape_people_card called on element: {base_element}")
        # Use CSS selector to find the link directly
        people_link = self.wait_for_element_to_load(by=By.CSS_SELECTOR, name=".mb1 a", base=base_element)
        if people_link:
            url = people_link.get_attribute("href").split("?")[0]
            print(f"[DEBUG] Found profile link: {url}")
            return url
        else:
            print(f"[DEBUG] No profile link found in element")
            return None


    def scrape_logged_in(self, close_on_complete=True, scrape_recommended_jobs=True):
        driver = self.driver
        driver.get(self.base_url)
        if scrape_recommended_jobs:
            self.focus()
            sleep(self.WAIT_FOR_ELEMENT_TIMEOUT)
            job_area = self.wait_for_element_to_load(name="scaffold-finite-scroll__content")
            areas = self.wait_for_all_elements_to_load(name="artdeco-card", base=job_area)
            for i, area in enumerate(areas):
                area_name = self.AREAS[i]
                if not area_name:
                    continue
                area_results = []
                for job_posting in area.find_elements(By.CLASS_NAME, "jobs-job-board-list__item"):
                    job = self.scrape_people_card(job_posting)
                    area_results.append(job)
                setattr(self, area_name, area_results)
        return


    def search(self, search_term: str) -> List[Job]:
        url = os.path.join(self.base_url, "search/results/people/") + f"?keywords={urllib.parse.quote(search_term)}&refresh=true"
        self.driver.get(url)
        self.scroll_to_bottom()
        #self.focus()
        sleep(self.WAIT_FOR_ELEMENT_TIMEOUT)

        people_list_class_name = "search-marvel-srp"
        job_listing = self.wait_for_element_to_load(name=people_list_class_name)

        self.scroll_class_name_element_to_page_percent(people_list_class_name, 0.3)
        #self.focus()
        sleep(self.WAIT_FOR_ELEMENT_TIMEOUT)

        self.scroll_class_name_element_to_page_percent(people_list_class_name, 0.6)
        #self.focus()
        sleep(self.WAIT_FOR_ELEMENT_TIMEOUT)

        self.scroll_class_name_element_to_page_percent(people_list_class_name, 1)
        #self.focus()
        sleep(self.WAIT_FOR_ELEMENT_TIMEOUT)

        people_profiles = []
        # First get the first ul element
        first_ul = self.wait_for_element_to_load(
            by=By.CSS_SELECTOR,
            name=".search-marvel-srp>div>div>div>ul:first-of-type", 
            base=self.driver
        )
        # Then get all li elements inside that ul
        people_cards = first_ul.find_elements(By.TAG_NAME, "li")
        print(f"[DEBUG] Found {len(people_cards)} people card containers")
        
        for i, people_card in enumerate(people_cards):
            print(f"[DEBUG] Processing people card {i+1}/{len(people_cards)}")
            
            # Log HTML content of the card
            try:
                html_content = people_card.get_attribute('outerHTML')
                print(f"\n{'='*40}\n[HTML DEBUG] CARD {i+1} HTML:\n{'='*40}\n{html_content}\n{'='*40}\n")
            except Exception as e:
                print(f"[ERROR] Failed to get HTML for card {i+1}: {str(e)}")
            
            people = self.scrape_people_card(people_card)
            if people:
                people_profiles.append(people)
        
        print(f"[DEBUG] Total profiles collected: {len(people_profiles)}")
        return people_profiles
