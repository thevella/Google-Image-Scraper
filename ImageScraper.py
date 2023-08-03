from enum import IntEnum, auto

import datetime, requests, pathlib, math, mimetypes, os
from tqdm import tqdm

# Multi-Process
from functools import partial
from pebble import ProcessPool
from multiprocessing.managers import BaseManager
from multiprocessing import Lock, Value

# Selenium
from selenium import webdriver
# Firefox
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
# Chrome
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions

# Managers
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager

# Just for typing
from typing import List, Any, Tuple, Literal
from selenium.webdriver.common.options import ArgOptions
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from os import PathLike

# Sketchyness
import inspect


class Counter(object):
    def __init__(self, start_val:int = 0) -> None:
        self.val = Value('i', start_val)

    def increment(self, n:int = 1) -> None:
        with self.val.get_lock():
            self.val.value += n

    def get_and_increment(self, n:int = 1) -> int:
        with self.val.get_lock():
            old_val = self.val.value
            self.val.value += n
            return old_val

    @property
    def value(self) -> int:
        return self.val.value


class ImageScraper:
    class DriverType(IntEnum):
        Firefox = auto()
        Chrome = auto()

    search_terms: str | List[str]
    save_location: str | PathLike
    
    date_num_ranges: int
    date_delta: datetime.timedelta | int
    
    pages_num: int
    
    threads_search_num: int
    threads_download_num: int

    driver_type: DriverType
    driver_headless: bool
    driver_options: ArgOptions | None

    driver_lock = Lock()

    def __init__(self, search_terms: str | List[str], save_location: str | PathLike | None = None, date_num_ranges: int = 10,
                        date_delta: datetime.timedelta | int = datetime.timedelta(weeks=6*4), pages_num: int = 3, 
                        threads_search_num: int = 4, threads_download_num: int = 8, driver_type: DriverType = DriverType.Firefox, 
                        driver_headless: bool = True, driver_options: ArgOptions | None = None,
                        ) -> None:
        
        if isinstance(search_terms, str):
            self.search_terms = [search_terms]
        elif isinstance(search_terms, list) and all([isinstance(search_term, str) for search_term in search_terms]):
            self.search_terms = search_terms
        else:
            ImageScraper._raise_type_error(search_terms, ["str", "List[str]"])

        if save_location is None:
            self.save_location = "./Images/"
        elif isinstance(save_location, PathLike) or isinstance(save_location, str):
            self.save_location = save_location
        else:
            ImageScraper._raise_type_error(save_location, ["str", "PathLike", "None"])
        
        if isinstance(date_num_ranges, int):
            if date_num_ranges < 0:
                raise ValueError("date_num_ranges must be >= 0")
            self.date_num_ranges = date_num_ranges
        else:
            ImageScraper._raise_type_error(date_num_ranges, ["int"])
        
        if isinstance(date_delta, datetime.timedelta):
            self.date_delta = date_delta
        elif isinstance(date_delta, int):
            self.date_delta = datetime.timedelta(weeks=date_delta)
        else:
            ImageScraper._raise_type_error(date_delta, ["datetime.timedelta", "int"])

        if isinstance(pages_num, int):
            self.pages_num = pages_num
        else:
            ImageScraper._raise_type_error(pages_num, ["int"])
        
        if isinstance(threads_search_num, int):
            self.threads_search_num = threads_search_num
        else:
            ImageScraper._raise_type_error(threads_search_num, ["int"])

        if isinstance(threads_download_num, int):
            self.threads_download_num = threads_download_num
        else:
            ImageScraper._raise_type_error(threads_download_num, ["int"])

        if isinstance(driver_type, ImageScraper.DriverType):
            self.driver_type = driver_type
        else:
            ImageScraper._raise_type_error(driver_type, ["ImageScraper.DriverType"])

        if isinstance(driver_headless, bool):
            self.driver_headless = driver_headless
        else:
            ImageScraper._raise_type_error(driver_headless, ["bool"])
        
        if isinstance(driver_options, ArgOptions) or driver_options is None:
            self.driver_options = driver_options
        else:
            ImageScraper._raise_type_error(driver_options, ["ArgOptions", "None"])
        


    @staticmethod
    def _raise_type_error(var: Any, valid_types: List[str]):
        if not isinstance(valid_types, list) or not all([ isinstance(valid_type, str) for valid_type in valid_types ]):
            ImageScraper._raise_type_error(valid_types, [ "List[str]" ])
        
        frame = inspect.currentframe()
        frame = inspect.getouterframes(frame)[1]
        string = inspect.getframeinfo(frame[0]).code_context[0].strip()
        arg = string[string.find('(') + 1:-1].split(',')[0]
        
        name = None

        if arg.find('=') != -1:
            name = arg.split('=')[1].strip()
        else:
            name = arg

        type_str = ""

        if len(valid_types) == 1:
            type_str = valid_types[0]
        elif len(valid_types) == 2:
            type_str = ' or '.join(valid_types)
        else:
            type_str = ', '.join(valid_types[:-1])
            type_str = type_str[:-2] + ' or ' + valid_types[-1]
        
        raise TypeError("{} must be {} - but was given {}".format(name, type_str, type(var)))
        

    @staticmethod
    def create_driver(driver_type: DriverType = DriverType.Firefox, driver_headless: bool = True, driver_options: ArgOptions | None = None) -> RemoteWebDriver:
        webdriver_path = "./webdrivers"
        
        driver = None
        options = None

        if driver_type == ImageScraper.DriverType.Firefox:
            
            if driver_options is not None:
                if type(driver_options) is not FirefoxOptions:
                    ImageScraper._raise_type_error(driver_options, ["None", "FirefoxOptions"])

                options = driver_options
            else:
                options = FirefoxOptions()

            if driver_headless:
                options.add_argument("--headless")

            driver = webdriver.Firefox(options=options, service=FirefoxService(GeckoDriverManager(path=webdriver_path).install()))
        elif driver_type == ImageScraper.DriverType.Chrome:

            if driver_options is not None:
                if type(driver_options) is not ChromeOptions:
                    ImageScraper._raise_type_error(driver_options, ["None", "ChromeOptions"])

                options = driver_options
            else:
                options = ChromeOptions()

            if driver_headless:
                options.add_argument("--headless")

            driver = webdriver.Chrome(options=options, service=ChromeService(ChromeDriverManager(path=webdriver_path).install()))

        else:
            raise NotImplementedError("Only supported driver types are Firefox and Chrome")

        return driver
    
    def _create_driver(self) -> RemoteWebDriver:
        return ImageScraper.create_driver(self.driver_type, self.driver_headless, self.driver_options)
    
    @staticmethod
    def create_save_location(holding_dir: PathLike | str = "./", num_new_files: int = 0) -> Tuple[Literal[0], int] | Tuple[int, int]:
        if num_new_files < 0: raise ValueError

        if not os.path.exists(holding_dir):
            os.makedirs(holding_dir)
            return 0, int(math.log10(num_new_files))+1
        elif not os.path.isdir(holding_dir):
            raise ValueError

        filenames = [pathlib.PurePath(file).stem for file in os.listdir(holding_dir)]
        
        if len(filenames) == 0:
            return 0, int(math.log10(num_new_files)) + 1

        lastfile = max([int(file) if file.isdigit() else 0 for file in filenames])
        
        filename_len_cur = 0
        for file in filenames:
            if file.isdigit():
                filename_len_cur = len(file)
                break
        
        num_digits_new = int(math.log10(num_new_files+lastfile))+1
        
        if num_digits_new > len(filename_len_cur):
            ImageScraper.update_file_names(holding_dir, num_digits_new)

        return lastfile + 1, num_digits_new

    @staticmethod
    def update_file_names(holding_dir: PathLike | str = "./", num_digits: int = 1) -> None:
        filenames = os.listdir(holding_dir)

        for file in filenames:
            filestem = pathlib.PurePath(file).stem
            
            if not filestem.isdigit():
                continue
            
            os.rename(os.path.join(holding_dir, file), os.path.join(holding_dir, "{filename:0{padding}d}{fileending}".format(filename=int(filestem), padding=num_digits, fileending=pathlib.PurePath(file).suffix)))

    @staticmethod
    def url_download_and_save(save_num_counter: Counter, padding: int, save_dir: str | PathLike, url: str) -> None:
        img = None
        try:
            img = requests.get(url, headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:101.0) Gecko/20100101 Firefox/101.0"}, timeout=200)
        except:
            return False

        extension = mimetypes.guess_extension(img.headers.get('content-type', '').split(';')[0])
        
        if extension == ".html":
            return False

        with open(os.path.join(save_dir, "{num:0{padding}d}{extension}".format(num=save_num_counter.get_and_increment(), padding=padding, extension=extension if not extension is None else ".jpg")), 'wb') as file:
            file.write(img.content)

        return True


    def get_image_links_unpacker(self, before_and_after_search: Tuple[datetime.date, datetime.date, str], driver: RemoteWebDriver | None = None) -> List[str]:
        (before, after, searchterm) = before_and_after_search
        
        driver_quit = False

        if driver is None:
            driver_quit = True
            with self.driver_lock:
                driver = self.create_driver()
        
        result = []
        try:
            result = self.get_image_links(searchterm, driver, before=before, after=after, pages_num=self.pages_num)
        except BaseException as e:
            print(e.__str__)
        finally:
            if driver_quit:
                with self.driver_lock:
                    driver.quit()

            return result

    def run(self, driver: RemoteWebDriver | None = None) -> None:
        
        img_links = set()
        
        # totallinks = 0
        
        date_sets = []

        for search_term in self.search_terms:
            date = datetime.date.today()
    
            for _ in range(self.date_num_ranges):
                date_sets.append((date, date - self.date_delta, search_term,))
                date = date - self.date_delta
    
        img_links_result = []

        num_search_workers = min(self.threads_search_num, self.date_num_ranges*len(self.search_terms))

        if num_search_workers == 1 or driver is not None:
            driver_quit = False

            if driver is None:
                driver_quit = True
                driver = self._create_driver()

            try:
                counter = 0

                for date_set in tqdm(date_sets):
                    img_links.update(set(self.get_image_links_unpacker(date_set, driver=driver)))

                    # counter += 1
                    # if counter % self.date_num_ranges == 0:
                    #     print(f"\nfound {len(img_links)} links after {counter} sessions\n")

            except BaseException as e:
                if driver_quit:
                    driver.close()
                    driver = None

                raise e
            
            finally:
                if driver_quit and driver is not None:
                    driver.close()

        else:
            with ProcessPool(max_workers=num_search_workers) as pool:
                img_links_result = pool.map(self.get_image_links_unpacker, date_sets, timeout=1000)

                counter = 0
                with tqdm(total=len(date_sets)) as progress:
                    for img_links_elm in img_links_result.result():
                        img_links.update(set(img_links_elm))
                        
                        # counter += 1
                        # if counter % self.date_num_ranges == 0:
                        #     print(f"\nfound {len(img_links)} links after {counter:03d} sessions\n")
                        
                        progress.update(1)
            
            # searchlinks = len(img_links) - totallinks
            # totallinks = len(img_links)
            
            # print(list(img_links)[0])
            #print(f"found {searchlinks} links in \"{search_term}\", {totallinks} total so far")
        
        print(f"\nfound {len(img_links)} total links in {len(self.search_terms)} search terms\n")

        
        save_num, padding = ImageScraper.create_save_location(holding_dir = self.save_location, num_new_files=len(img_links))
        
        BaseManager.register('Counter', Counter)
        manager = BaseManager()
        manager.start()
    
        counter = manager.Counter(save_num)
        
        func = partial(ImageScraper.url_download_and_save, counter, padding, self.save_location)

        if self.threads_download_num == 1:
            results = []
            for img_link in tqdm(img_links):
                results.append(func(img_link))

        else:
            with ProcessPool(max_workers=self.threads_download_num) as pool:
                results = pool.map(func, img_links, timeout=250)

                new_results = []

                with tqdm(total=len(img_links)) as progress:
                    for result in results.result():
                        new_results.append(result)
                        progress.update(1)
                results = new_results

        num_saved = 0

        num_saved = len([True for result in results if result == True])

        print(f"\nsaved {num_saved} out of {len(results)}\n")


    @staticmethod
    def get_image_links(searchterm: str, driver: RemoteWebDriver, before: datetime.date | None = None, after: datetime.date | None = None, pages_num: int = -1) -> List[str]:
        pass