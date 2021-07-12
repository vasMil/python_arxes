# webdriver - used because eurostat is dynamic (that is, uses Javascript)
# so I need a way to parse the code before scraping - selenium is the easiest way I found
from selenium import webdriver
# interact with the website (enter, click, etc.)
from selenium.webdriver.common.keys import Keys
# extract the .tsv.gz file
import gzip
# interact with os
import shutil
import os
# sleep
import time
# regex
import re
# csv format library
import csv


# will unzip the file (that is in current directory) to a txt with the same filename
# will also delete the compressed file
def unzip_gz(filename, extension):
    cur_dir = os.getcwd()
    # unzip the file
    tin_file = cur_dir + '/' + filename + extension
    with gzip.open(tin_file, 'r') as file_in:
        with open(filename + '.txt', 'wb') as file_out:
            shutil.copyfileobj(file_in, file_out)
    # remove the zip you downloaded with selenium
    os.remove(tin_file)


# Initialize a driver with some settings
# and launches the desired url
def start_driver():
    # path to the driver selenium will use
    path = "chromedriver.exe"
    # Changing the download folder, it is only valid for current session
    cur_dir = os.getcwd()
    chrome_options = webdriver.ChromeOptions()
    # headless -> do not open a chrome browser as a window
    chrome_options.headless = False
    prefs = {'download.default_directory': cur_dir}
    chrome_options.add_experimental_option('prefs', prefs)
    # initializing the driver
    driver = webdriver.Chrome(path, options=chrome_options)
    url = "https://ec.europa.eu/eurostat/web/main/data/database"
    driver.get(url)
    return driver


# Uses the open driver and navigates in eurostat
# uses eurostat search-bar in order to locate the files with title tile
# downloads the files and goes back to where it started, so it multiple calls are possible in the same session
def eurostat_search(driver, title):
    # get to the search bar in eurostat (the name of which is text in the html code)
    search = driver.find_element_by_name("text")
    # types in the search bar the file I am looking for
    search.send_keys(title)
    # press enter (to search)
    search.send_keys(Keys.RETURN)
    # finds the box with the correct title
    downloader = driver.find_element_by_link_text(title)
    # clicks that title
    downloader.click()
    # finds the link that will give me the file
    downloader = driver.find_element_by_link_text("Download table")
    # click on the element (download button, which will download a .tsv.gz file
    downloader.click()
    # get the code name of the dataset you are downloading
    product_section_left_list = driver.find_elements_by_class_name("product-section-left")
    code = ""
    for product_section_left in product_section_left_list:
        temp = product_section_left.text
        if temp.find("Code: ") != -1:
            code = temp.split("\n")[0].split(" ")[1]
            break
    # If code is empty then, I don't have the name of the file I downloaded - thus I need to throw
    # TODO: Get the filename (code), just from the contents of the folder (matching the extension)
    if code == "":
        print("Did not manage to get the code of the dataset!")
        exit(1)
    driver.back()
    driver.back()
    return code


# closes the driver, given in arguments, but before doing so,
# it ensures that the files in list filename downloaded successfully
def close_driver(driver, filenames, extension):
    flag = 0
    # Wait until expected file is downloaded and in current path (max 10 sec)
    for filename in filenames:
        time_cnt = 0
        while os.path.exists(os.getcwd() + '/' + filename + extension) != 1:
            time.sleep(2)
            time_cnt += 2
            if time_cnt >= 10:
                # close the tab you opened
                driver.close()
                print(f"File: {filename+extension} did not download!")
                flag = 1
                exit(1)
    driver.close()


# web_scraping main -> Will download and decompress files
# The result is txt files in directory Web_Scraping_Results
def get_files(ws_argv):
    # If directory already exists delete it
    if os.path.exists("Web_Scraping_Results") == 1:
        # Note: rmtree fails if folder tree contains read-only files
        shutil.rmtree("Web_Scraping_Results")
    os.mkdir("Web_Scraping_Results")
    # Create a list in which I will store the names of the files I downloaded
    filenames = []
    extension = ".tsv.gz"
    driver = start_driver()
    # iterate through the requested files (IMPORTANT: the titles should be exact!)
    # search for them and download 'em
    for arg in ws_argv:
        filename = eurostat_search(driver, arg)
        filenames.append(filename)
    close_driver(driver, filenames, extension)
    # unzip files
    for filename in filenames:
        unzip_gz(filename, ".tsv.gz")
        # Move files to directory Web_Scraping_Results, so everything is organized
        os.rename(filename + ".txt", "Web_Scraping_Results/" + filename + ".txt")
        full_path = "Web_Scraping_Results/" + filename + ".txt"
        # Do some data manipulation and save data in a csv fromat
        tsv_to_csv(full_path)
        # Delete the .txt files (since you now have the .csv)
        os.remove(full_path)
    # return the list of names so you may later manipulate the data
    return filenames


# ------------------------------------------------ Data manipulation ------------------------------------------------- #

# Gets the path of a file and splits it into a list
# 0-> path | 1-> filename | 3-> extension
def spilt_filename(full_path):
    # get the path of the file (if included)
    path = re.findall(r"(.*/+)*", full_path)[0]
    # remove that path from the file name
    file_with_ext = re.sub(r"(.*/+)*", "", full_path)
    # get the extension of the file (assuming there is only one)
    ext = re.findall(r"(\..*)", file_with_ext)[0]
    # ignore the extension
    f_name = re.findall(r".*(?=\.)", file_with_ext)[0]
    path_list = [path, f_name, ext]
    return path_list


# manipulate the first line
def csv_fix_first_line(first_line):
    # the first columns in the tsv file are being seperated by commas
    first_line = first_line.split(',')
    # a stupid way to do resident = "c_resid"
    resident = first_line[0]
    # a stupid way to do geo = "geo"
    geo = re.findall(r"(\w+)(?=\\)", first_line[3])[0]
    # the rest of the columns are seperated by tabs
    years = first_line[3].split("\t")
    # the fist argument is "geo/time", not a year so I remove it
    years.pop(0)
    # convert everything else into integers
    years = [int(year) for year in years]
    # target first line: "c_resid", "geo", 2008, 2009, etc.
    years.insert(0, resident)
    years.insert(1, geo)
    return years


# Convert the tsv file you downloaded into a csv file
def tsv_to_csv(file):
    # open input file (tsv)
    inp = open(file, 'r')
    # open output file (csv)
    path_list = spilt_filename(file)
    out = open(path_list[0]+path_list[1]+".csv", 'w')
    csv_out = csv.writer(out, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
    # first line of csv (different from the rest - not really)
    first_line = inp.readline()
    first_line = csv_fix_first_line(first_line)
    csv_out.writerow(first_line)
    # the rest of the csv file
    lines = inp.readlines()
    for line in lines:
        labels = line.split(',')
        residency = labels[0]
        country = labels[3].split('\t').pop(0)
        # values is a list that will contain all arithmetic values of a specific row
        values = re.findall(r"(\d+|:)[\s]", re.sub(country, "", labels[3]))
        if len(values) != 12:
            print(f"Data corrupted! First wrong line:\n{line}")
            exit(1)
        # Ternary Operator combined with one line for loop - python is weird
        values = [value if value == ':' else int(value) for value in values]
        # Append info at the beggining of each csv line
        values.insert(0, residency)
        values.insert(1, country)
        csv_out.writerow(values)
    # close mi files
    inp.close()
    out.close()


# # TODO: Μη κλέβεις κλέφτη - this is not web scraping...
# # This is the first attmpt, it worked but it was quite big for a function
# # so I decided to split it into start_driver(), eurostat_search() and close_driver()
# # will keep the code around just in case (last time I checked it was working)
# # This code uses codes in order to get the requested file from eurostat (ex. tin00174)
# def get_tin_file(code, extension):
#     # path to the driver selenium will use
#     path = "chromedriver.exe"
#     # Changing the download folder, it is only valid for current session
#     cur_dir = os.getcwd()
#     chrome_options = webdriver.ChromeOptions()
#     # headless -> do not open a chrome browser as a window
#     chrome_options.headless = False
#     prefs = {'download.default_directory': cur_dir}
#     chrome_options.add_experimental_option('prefs', prefs)
#     # initializing the driver
#     driver = webdriver.Chrome(path, options=chrome_options)
#     url = "https://ec.europa.eu/eurostat/web/main/data/database"
#     driver.get(url)
#     # get to the search bar in eurostat (the name of which is text in the html code)
#     search = driver.find_element_by_name("text")
#     # types in the search bar the file I am looking for
#     search.send_keys(code)
#     # press enter (to search)
#     search.send_keys(Keys.RETURN)
#     # use xpath of the button that downloads the compressed file
#     downloader = driver.find_element_by_xpath("//*[@id=\"search-results-container\"]/div[2]/div/div[1]/div/a[3]")
#     downloader.click()
#     # Wait until expected file is downloaded and in current path (max 10 sec)
#     time_cnt = 0
#     while os.path.exists(os.getcwd() + '/' + code + extension) != 1:
#         time.sleep(2)
#         time_cnt += 2
#         if time_cnt >= 10:
#             # close the tab you opened
#             driver.close()
#             print(f"File: {code+extension} did not download!")
#             exit(1)
#     driver.close()
#
#
# # get_tin_file("tin00175", ".tsv.gz")
