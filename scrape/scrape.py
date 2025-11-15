from bs4 import BeautifulSoup
from selenium import webdriver
from tqdm import tqdm
import requests

base_url = "https://bulletins.nyu.edu"
programs_url = base_url + "/undergraduate/arts-science/#programstext"
soup = BeautifulSoup(requests.get(programs_url, headers={'User-Agent': "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0"}).content, 'html.parser')

sitemap = soup.find("div", class_="sitemap")
programs = sitemap.find_all("a")
programs_info = [{"name": a.get_text(strip=True), "href": a.get("href"), "visited": False} for a in programs]

print(programs_info)

driver = webdriver.Chrome()

for program in programs_info:
    if program['visited']:
        continue
    url = base_url + program['href']
    driver.get(url)
    """
    uncomment below when fully implemented
    """
    # program['visited'] = True