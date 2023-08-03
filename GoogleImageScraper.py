from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By
from urllib.parse import quote, urlparse, parse_qs

import time, datetime

# Just for typing
from os import PathLike
from typing import List
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

from ImageScraper import ImageScraper

class GoogleImageScraper(ImageScraper):

    @staticmethod
    def get_image_links(searchterm: str, driver: RemoteWebDriver, before: datetime.date | None = None, after: datetime.date | None = None, pages_num: int = -1) -> List[str]:
        if (not before is None and not isinstance(before, datetime.date)) or (not after is None and not isinstance(after, datetime.date)):
            raise TypeError


        urlsearchterm = "+".join([quote(term, safe="") for term in searchterm.split(" ")])
        
        if not before is None:
            urlsearchterm += "+"+quote("before:{:04d}-{:02d}-{:02d}".format(before.year, before.month, before.day), safe="")

        
        if not after is None:
            urlsearchterm += "+"+quote("after:{:04d}-{:02d}-{:02d}".format(after.year, after.month, after.day), safe="")

        driver.get(f"https://www.google.com/search?q={urlsearchterm}&tbm=isch")
        
        perf_time = time.time()

        starttime = time.time()

        timeout_s = 50

        num_pages = 0

        while num_pages < pages_num or pages_num == -1:
            ActionChains(driver).send_keys(Keys.PAGE_DOWN).perform()
            time.sleep(0.25)
            
            if time.time() - starttime > timeout_s:
                driver.refresh()
                starttime = time.time()
                continue

            elements = driver.find_elements(By.XPATH, "/html/body/div[2]/c-wiz/div[3]/div[1]/div/div/div/div/div[1]/div[2]/div[1]/div[2]/div[1]/div")

            elements_button = driver.find_elements(By.XPATH, "/html/body/div[2]/c-wiz/div[3]/div[1]/div/div/div/div/div[1]/div[2]/div[2]/input")
            
            if len(elements) > 0:
                if elements[0].text == "Looks like you've reached the end":
                    break
        
            if len(elements_button) > 0:
                if elements_button[0].is_displayed():
                    elements_button[0].click()
                    num_pages += 1
                    starttime = time.time()
        
        
        elements_images = driver.find_elements(By.CSS_SELECTOR, "div.BUooTd")
        
        [elm.click() for elm in elements_images]
        

        
        elements_images = driver.find_elements(By.XPATH, "/html/body/div[2]/c-wiz/div[3]/div[1]/div/div/div/div/div[1]/div[1]/span/div[1]/div[1]/div/div/a[1]")
        
        # print("Browser time: {:.2f}".format(time.time() - perf_time))
        perf_time = time.time()
        

        elm_links = [elm.get_attribute("href") for elm in elements_images]

        # print("Link pulling time: {:.2f}".format(time.time() - perf_time))

        perf_time = time.time()

        img_links = []
        for elm in elm_links:
            try:
                img_links.append(parse_qs(urlparse(elm).query)["imgurl"][0])
            except Exception as e:
                #print(elm.get_attribute("href"))
                continue
        # print("Processing time: {:.2f}".format(time.time() - perf_time))

        return img_links








#searches = ["sandy soil", "loamy silt soil"]

#save_dir = "./Images/sand"


searches_agg = [ [["sandy soil", "sand", "beachy soil"],"./Images/sand"],
                 [["soil", "loose soil", ""], "./Images/loose_soil"],
                 [["packed soil", "dry soil", "hard soil"], "./Images/hard_soil"]
                ]


            
    
    
    
