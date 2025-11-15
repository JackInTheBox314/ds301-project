from bs4 import BeautifulSoup
import requests
import pandas as pd

programs_url = "https://bulletins.nyu.edu/undergraduate/arts-science/#programstext"
soup = BeautifulSoup(requests.get(programs_url, headers={'User-Agent': "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0"}).content, 'html.parser')

sitemap = soup.find("div", class_="sitemap")
programs = sitemap.find_all("a")
programs_info = [{"name": a.get_text(strip=True),
                  "href": a.get("href"),
                  "visited": False}
                for a in programs]

df = pd.DataFrame.from_dict(programs_info)
df.to_csv("program_urls.csv", index=False)