from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
import requests
from pprint import pprint

base_url = "https://bulletins.nyu.edu"

programs = pd.read_csv("program_urls.csv")[:1]

for idx, program in tqdm(programs.iterrows(), total=len(programs)):
    if program['visited'] == "True":
        continue
    url = base_url + program['href'] + "/#curriculumtext"
    headers = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    html = requests.get(url, headers=headers).content
    soup = BeautifulSoup(html, "html.parser")
    
    courselist = soup.find("table", class_="sc_courselist")
    headers = [th.get_text(strip=True) for th in courselist.find_all("th")]
    
    courselist_rows = courselist.find("tbody").find_all("tr")[1:] # skip first row (which is "Minor Requirements")
    pprint(courselist_rows)
    
    
    """
    uncomment below when fully implemented
    """
    # program['visited'] = True
    
programs.to_csv("program_urls.csv", index=False)