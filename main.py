# -*- coding: utf-8 -*-
"""
Created on Sun Jul 12 11:02:06 2020

@author: OHyic

"""
#Import libraries
import os
import concurrent.futures
from GoogleImageScraper import GoogleImageScraper
from datetime import timedelta
import argparse

if __name__ == "__main__":
    # arg_parser = argparse.ArgumentParser(description="Download Images from Google Images using selenium")
    # arg_parser.add_argument('')

    headless = True                     # True = No Chrome GUI

    search_terms = [(["gravel -bike", "pea gravel -bike", "coarse gravel -bike", "gravel foundation -bike"], "./images2/gravel/",),
                    (["sandy ground -beach", "sand foundation -beach", "sand -beach", "construction sand"], "./images2/sand/",),
                    (["loamy soil", "loamy ground", "loam construction", "loam"], "./images2/loam/",),
                    (["clay ground", "clay soil", "clay -pottery", "clay construction"], "./images2/clay/",),
                    (["packed soil", "hard soil", "compacted soil"], "./images2/compacted_soil/",),
                    (["mixed aggregate", "mixed soil and gravel", "diverse ground texture", "highway shoulder"], "./images2/mixed_soil/",)]

    date_num_ranges = 5
    date_delta = timedelta(weeks=7*4)

    pages_num: int = 2

    threads_search_num: int = 5
    threads_download_num: int = 10

    driver_type = GoogleImageScraper.DriverType.Firefox 
    driver_headless: bool = True


    gimage = GoogleImageScraper(search_terms[0][0], search_terms[0][1], date_num_ranges, date_delta, pages_num, threads_search_num, \
                                threads_download_num, driver_type, driver_headless)

    for (terms, save_loc) in search_terms:
        gimage.search_terms = terms
        gimage.save_location = save_loc
        gimage.run()

