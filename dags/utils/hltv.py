import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.hltv.org"

BASE_URL_MATCH = (
    "{base_url}/stats/matches?startDate={ds}&endDate={ds}&rankingFilter=Top50"
)

regex = re.compile("group-(\d+) first")  # noqa: W605


def get_match_list(ds):
    url = BASE_URL_MATCH.format(base_url=BASE_URL, ds=ds)
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Error {response.status_code} for {url}")
    soup = BeautifulSoup(response.text, "html.parser")
    trs = soup.find_all("tr", {"class": regex})
    tds = [tr.find("td", {"class": "date-col"}) for tr in trs]

    urls = [f"{BASE_URL}{td.find('a')['href']}" for td in tds]
    return urls


def get_match_more_info(url):
    time.sleep(5)
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Error {response.status_code} for {url}")
    soup = BeautifulSoup(response.text, "html.parser")
    match_url = soup.find("a", {"class": "match-page-link button"})
    match_url = f"{BASE_URL}{match_url['href']}"
    return match_url


def get_match_demo_url(url):
    print("sleeping 5 seconds")
    time.sleep(5)
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Error {response.status_code} for {url}")
    soup = BeautifulSoup(response.text, "html.parser")
    demo_url = soup.find("a", {"class": "stream-box"})
    if demo_url:
        demo_url = f"{BASE_URL}{demo_url['data-demo-link']}"
        return demo_url
    return None


def download_demo(ds, url):
    time.sleep(5)
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Error {response.status_code} for {url}")
    file_name = url.split("/")[-1]
    with open("/tmp/test.txt", "w") as f:
        f.write("salut it's working")
    filename = Path(f"/tmp/{ds}/{file_name}.rar")
    with open(filename.as_posix(), "wb") as f:
        f.write(response.content)
