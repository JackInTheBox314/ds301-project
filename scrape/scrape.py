from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
import requests
from pprint import pprint
from urllib.parse import urljoin

base_url = "https://bulletins.nyu.edu"

programs = pd.read_csv("program_urls.csv")

REQ_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

all_courses = []

for idx, program in tqdm(programs[:2].iterrows(), total=len(programs)):
    if str(program.get("visited", "False")) == "True":
        continue

    program_href = program["href"]
    url = base_url + program_href + "/#curriculumtext"
    print("Visiting:", url)

    html = requests.get(url, headers=REQ_HEADERS, timeout=10).content
    soup = BeautifulSoup(html, "html.parser")
    
    courselist = soup.find("table", class_="sc_courselist")
    if not courselist:
        print("No courselist table found for", url)
        continue

    headers_row = [th.get_text(strip=True) for th in courselist.find_all("th")]

    tbody = courselist.find("tbody")
    rows = tbody.find_all("tr")

    req_num = 0
    suppress_course_increments = False  # after we hit "Select one...", stop incrementing for course rows
    for tr in rows:
        row_text = tr.get_text(" ", strip=True)

        # --- Handle "Select one of the following" rows ---
        if "Select one of the following" in row_text:
            # Every time this appears, count it as a new requirement
            req_num += 1
            suppress_course_increments = True  # from now on, don't increment for course rows
            continue  # usually these rows don't have course links
        
        a = tr.find("a", class_="bubblelink code")
        if not a:
            continue  # skip non-course rows

        if "orclass" not in (tr.get("class") or []) and not suppress_course_increments:
            req_num += 1

        course_code_table = a.get_text(strip=True)
        course_href = a.get("href")
        course_url = urljoin(base_url, course_href)

        tds = tr.find_all("td")
        title_table = tds[1].get_text(" ", strip=True) if len(tds) > 1 else ""

        credits_table = ""
        last_td = tds[-1] if tds else None
        if last_td is not None and "hourscol" in (last_td.get("class") or []):
            credits_table = last_td.get_text(strip=True)

        # ----- Fetch and parse /search/ page -----
        course_code = course_code_table
        title = title_table
        credits = credits_table
        offered = ""
        description = ""
        grading = ""
        repeatable = ""
        prereqs = ""
        extra_blocks = []

        try:
            detail_resp = requests.get(course_url, headers=REQ_HEADERS, timeout=10)
            detail_resp.raise_for_status()
            detail_soup = BeautifulSoup(detail_resp.content, "html.parser")

            courseblock = detail_soup.find("div", class_="courseblock")
            if courseblock:
                # direct child divs inside .courseblock
                child_divs = [div for div in courseblock.find_all("div", recursive=False)]

                # 0: spans with code, title, credits
                if len(child_divs) >= 1:
                    spans = child_divs[0].find_all("span")
                    if len(spans) >= 1:
                        course_code = spans[0].get_text(" ", strip=True)
                    if len(spans) >= 2:
                        title = spans[1].get_text(" ", strip=True)
                    if len(spans) >= 3:
                        # e.g. "4 Credits"
                        credits = spans[2].get_text(" ", strip=True)

                # 1: typically offered
                if len(child_divs) >= 2:
                    offered_div = child_divs[1]
                    offered_span = offered_div.select_one(".detail-typically_offered")
                    if offered_span:
                        label_span = offered_span.find("span", class_="label")
                        # The actual terms are the sibling text after the <span class="label">…</span>
                        if label_span and label_span.next_sibling:
                            offered = str(label_span.next_sibling).strip()
                        else:
                            # fallback: whole string, then strip the label if present
                            raw = offered_span.get_text(" ", strip=True)
                            offered = raw.replace("Typically offered", "").strip(" :")
                    else:
                        offered = offered_div.get_text(" ", strip=True)
                
                # 2: description
                if len(child_divs) >= 3:
                    description_div = child_divs[2]
                    description = description_div.get_text(" ", strip=True).replace("\n", "")
                
                # 3: Grading
                if len(child_divs) >= 4:
                    grading_div = child_divs[3]
                    grading_span = grading_div.select_one(".detail-grading")
                    if grading_span:
                        label = grading_span.find("span", class_="label")
                        if label and label.next_sibling:
                            grading = str(label.next_sibling).strip()
                        else:
                            raw = grading_span.get_text(" ", strip=True)
                            grading = raw.replace("Grading:", "").strip()

                # 4: Repeatable for Credit
                if len(child_divs) >= 5:
                    repeat_text = child_divs[4].get_text(" ", strip=True)
                    # e.g. "Repeatable for additional credit: No"
                    if ":" in repeat_text:
                        repeatable = repeat_text.split(":", 1)[1].strip()
                    else:
                        repeatable = repeat_text.strip()

                # 5: Prerequisites (optional)
                if len(child_divs) >= 6:
                    prereq_text = child_divs[5].get_text(" ", strip=True)
                    if ":" in prereq_text:
                        prerequisites = prereq_text.split(":", 1)[1].strip()
                    else:
                        prerequisites = prereq_text.strip()


                # 6–8: other optional blocks – keep raw text just in case
                if len(child_divs) > 6:
                    for extra_div in child_divs[6:]:
                        text = extra_div.get_text(" ", strip=True)
                        if text:
                            extra_blocks.append(text)

        except Exception as e:
            print(f"Error fetching/parsing details for {course_code_table} at {course_url}: {e}")

        all_courses.append({
            "program_name": program["name"],
            "req_num": req_num,
            "course_code_table": course_code_table,
            "title_table": title_table,
            "credits_table": credits_table,

            "course_code": course_code,
            "title": title,
            "credits": credits,
            "offered": offered,
            "description": description,
            "grading": grading,
            "repeatable": repeatable,
            "prerequisites": prerequisites,
            "extra_blocks": " || ".join(extra_blocks),
            "detail_url": course_url,
        })

    # mark visited
    # programs.loc[idx, "visited"] = "True"
    
# write out
df = pd.DataFrame(all_courses)
# pprint(df.head())

df.to_csv("courses_detailed.csv", index=False)
programs.to_csv("program_urls.csv", index=False)
print("Courses_detailed.csv printed")