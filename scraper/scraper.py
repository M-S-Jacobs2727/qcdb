import io
import logging
from pathlib import Path
import random
import re
import time

from bs4 import BeautifulSoup
from PIL import Image
import requests

LOG = logging.getLogger("log")
LOG.setLevel("INFO")
HND = logging.StreamHandler()
LOG.addHandler(HND)

def download_newspost(soup: BeautifulSoup, save_path: Path):
    d = soup(id="newspost")[0]
    LOG.debug(d.contents)

    lines = list()
    for c in d.contents:
        if c.string:
            lines.append(c.string.strip())
    
    newspost = '\n'.join(lines)
    save_path.write_text(newspost)
    LOG.debug(f"Saved to {save_path}")

def download_strip(soup: BeautifulSoup, save_path: Path, base_url: str):
    image_url: str = soup(id="strip")[0]["src"]
    LOG.debug(image_url)

    image_content = requests.get(base_url + image_url).content
    image_file = io.BytesIO(image_content)
    Image.open(image_file).convert("RGB").save(save_path, "PNG")
    LOG.debug(f"Saved to {save_path}")

def get_latest_strip_number(soup: BeautifulSoup):
    latest_url: str = soup("a", string="Latest")[0]["href"]
    LOG.debug(f"{latest_url = }")
    idx = latest_url.find("=")
    num = int(latest_url[idx+1:])
    return num

def get_all_titles():
    page = requests.get("https://www.questionablecontent.net/archive.php")
    LOG.info(f"Request returned status code {page.status_code}")
    soup = BeautifulSoup(page.content, "lxml")
    container = soup.find("div", id="container")
    LOG.debug(f"{container = }")
    links = container.find_all("a", href=True, string=True)
    LOG.debug(f"{links = }")

    strip_titles: list[tuple[int, str]] = list()
    for link in links:
        if link.string:
            m = re.match(r"Comic\s+(\d+):(.*)", link.string)
            if m is not None:
                strip_titles.append((int(m.group(1)), m.group(2)))
    
    return strip_titles

def filter_titles(strip_titles: list[tuple[int, str]]):
    strip_titles.sort(key=lambda x: x[0])
    titles = [strip_titles[0]]
    for (num1, title1), (num2, title2) in zip(strip_titles[:-1], strip_titles[1:]):
        if num1 != num2:
            titles.append((num2, title2))
    return titles

def write_titles(titles: list[tuple[int, str]], save_path: Path):
    with open(save_path, "w") as f:
        for num, title in titles:
            f.write(f"{num} {title}\n")
    LOG.info(f"Saved to {save_path}")

def main():
    base_url = "https://www.questionablecontent.net/"
    page = requests.get(base_url + "view.php?comic=1")
    LOG.info(f"Request returned status code {page.status_code}")

    soup = BeautifulSoup(page.content, "lxml")
    latest_number = get_latest_strip_number(soup)
    LOG.debug(f"Latest strip: {latest_number}")

    strips_dir = Path() / "scraper/strips"
    newsposts_dir = Path() / "scraper/newsposts"

    if not newsposts_dir.is_dir():
        raise FileNotFoundError(newsposts_dir)
    if not strips_dir.is_dir():
        raise FileNotFoundError(strips_dir)
    LOG.info("Both dirs exist")

    strip_nums = list(range(1, latest_number + 1))
    strip_files = [strips_dir / f"{i}.png" for i in strip_nums]
    newsposts_files = [newsposts_dir / f"{i}.txt" for i in strip_nums]
    urls = [base_url + f"view.php?comic={i}" for i in strip_nums]

    for i, strip_file, newsposts_file, url in zip(strip_nums, strip_files, newsposts_files, urls):
        if strip_file.is_file() and newsposts_file.is_file():
            continue

        secs = random.uniform(0.1, 2.0)
        LOG.debug(f"Sleeping for {secs:.3f} seconds")
        time.sleep(secs)

        page = requests.get(url)
        LOG.info(f"Request returned status code {page.status_code}")

        soup = BeautifulSoup(page.content, "lxml")
        
        if not strip_file.is_file():
            LOG.info(f"Downloading strip {i}")
            download_strip(soup, strip_file, base_url)

        if not newsposts_file.is_file():
            LOG.info("Downloading newspost")
            download_newspost(soup, newsposts_file)

def main2():
    outfile = Path("scraper/data/characters.txt")
    names = outfile.read_text().split("\n")

    page = requests.get("https://questionablecontent.fandom.com/wiki/Category:Characters")
    soup = BeautifulSoup(page.content, "lxml")

    links = list()
    for name in names:
        url_suffix = soup("a", string=name)[0]["href"]
        links.append(f"https://questionablecontent.fandom.com{url_suffix}")

    with open(outfile, "w") as f:
        for name, url in zip(names, links):
            f.write(f"{name} {url}\n")

    # results = soup("div", class_="category-page__first-char")
    # names = list()
    # for result in results:
    #     for name in result.parent("a", string=True):
    #         start = name.string[:4]
    #         if start not in ["Cate", "Temp", "List"]:
    #             names.append(name.string)
    # print(names)
    # outfile.write_text("\n".join(names))

if __name__ == "__main__":
    main2()
