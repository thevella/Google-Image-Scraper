from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By
from urllib.parse import unquote, quote, urlparse, parse_qs
from functools import partial
from pebble import ProcessPool
from multiprocessing.managers import BaseManager
import time, json, datetime, requests, pathlib, math, mimetypes, os, sys, multiprocessing

class Counter(object):
    def __init__(self):
        self.val = multiprocessing.Value('i', 0)

    def increment(self, n=1):
        with self.val.get_lock():
            self.val.value += n

    def get_and_increment(self, n=1):
        with self.val.get_lock():
            old_val = self.val.value
            self.val.value += n
            return old_val

    @property
    def value(self):
        return self.val.value

def create_driver():
    options = FirefoxOptions()
    # Deprecated
    #options.headless = True
    options.add_argument("--headless")

    return webdriver.Firefox(options=options, service=FirefoxService(GeckoDriverManager(path="./WebDrivers").install()))


def get_image_links(searchterm, before=None, after=None, driver=None):
    
    if (not before is None and not isinstance(before, datetime.date)) or (not after is None and not isinstance(after, datetime.date)):
        raise TypeError

    exitDriver = driver is None

    if exitDriver:
        driver = create_driver()

    urlsearchterm = "+".join([quote(term, safe="") for term in searchterm.split(" ")])
    
    if not before is None:
        urlsearchterm += "+"+quote("before:{:04d}-{:02d}-{:02d}".format(before.year, before.month, before.day), safe="")

    
    if not after is None:
        urlsearchterm += "+"+quote("after:{:04d}-{:02d}-{:02d}".format(after.year, after.month, after.day), safe="")

    driver.get(f"https://www.google.com/search?q={urlsearchterm}&tbm=isch")
    
    perf_time = time.time()

    starttime = time.time()

    timeout_s = 100

    while True:
        ActionChains(driver).send_keys(Keys.PAGE_DOWN).perform()
        time.sleep(0.5)
        
        if time.time()-starttime > timeout_s:
            driver.refresh()
            starttime = time.time()
            continue

        #elements = driver.find_elements(By.XPATH, "/html/body/div[2]/c-wiz/div[3]/div[1]/div/div/div/div[1]/div[2]/div[1]/div[2]/div[1]/div")
        elements = driver.find_elements(By.XPATH, "/html/body/div[2]/c-wiz/div[3]/div[1]/div/div/div/div/div[1]/div[2]/div[1]/div[2]/div[1]/div")

        elements_button = driver.find_elements(By.XPATH, "/html/body/div[2]/c-wiz/div[3]/div[1]/div/div/div/div/div[1]/div[2]/div[2]/input")
        
        if len(elements) > 0:
            if elements[0].text == "Looks like you've reached the end":
                break
    
        if len(elements_button) > 0:
            if elements_button[0].is_displayed():
                elements_button[0].click()
    
    
    elements_images = driver.find_elements(By.CSS_SELECTOR, "div.BUooTd")
    
    [elm.click() for elm in elements_images]
    

    
    elements_images = driver.find_elements(By.XPATH, "/html/body/div[2]/c-wiz/div[3]/div[1]/div/div/div/div/div[1]/div[1]/span/div[1]/div[1]/div/div/a[1]")
    
    print("Browser time: " + str(time.time() - perf_time))
    perf_time = time.time()
    

    elm_links = [elm.get_attribute("href") for elm in elements_images]

    print("Link pulling time: " + str(time.time() - perf_time))

    perf_time = time.time()

    img_links = []
    for elm in elm_links:
        try:
            img_links.append(parse_qs(urlparse(elm).query)["imgurl"][0])
        except Exception as e:
            #print(elm.get_attribute("href"))
            continue
    print("Processing time: " + str(time.time() - perf_time))

    if exitDriver:
        driver.quit()

    return img_links

def create_save_location(holding_dir="./", num_new_files=0):
    if num_new_files < 0: raise ValueError

    if not os.path.exists(holding_dir):
        os.makedirs(holding_dir)
        return 1, int(math.log10(num_new_files))+1
    elif not os.path.isdir(holding_dir):
        raise TypeError
    
    

    filenames = [pathlib.PurePath(file).stem for file in os.listdir(holding_dir)]
    
    if len(filenames) == 0:
        return 1, int(math.log10(num_new_files)) + 1

    lastfile = max([int(file) if file.isdigit() else 0 for file in filenames])
     
    filename_len_cur = 0
    for file in filenames:
        if file.isdigit():
            filename_len_cur = len(file)
            break
    
    num_digits_new = int(math.log10(num_new_files+lastfile))+1
    
    if num_digits_new > len(filename_len_cur):
        update_file_names(holding_dir, num_digits_new)

    return lastfile, num_digits_new


def update_file_names(holding_dir="./", num_digits=1):
    filenames = os.listdir(holding_dir)

    for file in filenames:
        filestem = pathlib.PurePath(file).stem
        
        if not filestem.isdigit():
            continue
        
        os.rename(os.path.join(holding_dir, file), os.path.join(holding_dir, "{filename:0{padding}d}{fileending}".format(filename=int(filestem), padding=num_digits, fileending=pathlib.PurePath(file).suffix)))


def url_download_and_save(save_num_counter, padding, save_dir, url):
    img = None
    try:
        img = requests.get(url, headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:101.0) Gecko/20100101 Firefox/101.0"})
    except:
        return

    extension = mimetypes.guess_extension(img.headers.get('content-type', '').split(';')[0])
    
    if extension == ".html":
        return

    with open(os.path.join(save_dir, "{num:0{padding}d}{extension}".format(num=save_num_counter.get_and_increment(), padding=padding, extension=extension if not extension is None else ".jpg")), 'wb') as file:
        file.write(img.content)


#searches = ["sandy soil", "loamy silt soil"]

#save_dir = "./Images/sand"


searches_agg = [ [["sandy soil", "sand", "beachy soil"],"./Images/sand"],
                 [["soil", "loose soil", ""], "./Images/loose_soil"],
                 [["packed soil", "dry soil", "hard soil"], "./Images/hard_soil"]
                ]

datedelta = datetime.timedelta(weeks=6*4)

cycles = 10


for search_agg in searches_agg:
    searches = search_agg[0]
    save_dir = search_agg[1]

    #driver = create_driver()
    driver = None
    
    
    img_links = set()
    
    totallinks = 0
    
    try:
        for search in searches:
            date = datetime.date.today()
            
            date_sets = []
    
            for _ in range(cycles):
                date_sets.append((date, date - datedelta, ))
                date = date-datedelta
    
            img_links_result = []
    
            def get_image_links_unpacker(searchterm, before_and_after):
                driver = create_driver()
                try:
                    result = get_image_links(searchterm, before=before_and_after[0], after=before_and_after[1], driver=driver)
                    
                    driver.quit()
                    return result
                except:
                    driver.quit()
                    return []
    
    
            with ProcessPool(max_workers=min(6, cycles)) as pool:
                func = partial(get_image_links_unpacker, search)
                img_links_result = pool.map(func, date_sets, timeout=800)
    
            for img_links_elm in img_links_result.result():
                img_links.update(set(img_links_elm))
            
            searchlinks = len(img_links) - totallinks
            totallinks = len(img_links)
            
            print(list(img_links)[0])
            print(f"found {searchlinks} links in \"{search}\", {totallinks} total so far")
        
        print(f"found {len(img_links)} total links")
    except:
        if not driver is None:
            driver.quit()
        
        sys.exit()
    
    finally:
        if not driver is None:
            driver.quit()
    
    save_num, padding = create_save_location(holding_dir=save_dir, num_new_files=len(img_links))
    
    with ProcessPool(max_workers=8) as pool:
        BaseManager.register('Counter', Counter)
        manager = BaseManager()
        manager.start()
    
        counter = manager.Counter()
        
        func = partial(url_download_and_save, counter, padding, save_dir)
        pool.map(func, img_links, timeout=240)
            
    
    
    
