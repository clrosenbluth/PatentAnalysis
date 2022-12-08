import concurrent
import random
import time
import operator
import requests as requests
from bs4 import BeautifulSoup
from concurrent import futures


def get_headers():
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 '
        'Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 '
        'Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
        'Mozilla/5.0 (Linux; Android 11; SM-G960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Mobile '
        'Safari/537.36 '
    ]
    user_agent = random.choice(user_agents)
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age = 0",
        "Sec-Ch-Ua": "\"Google Chrome\";v=\"105\", \"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"105\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "macOS",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "user-agent": user_agent
    }
    return headers


MAX_THREADS = 30


def fill_freq(classes):
    freq = {}
    for item in classes:
        if item in freq:
            freq[item] += 1
        else:
            freq[item] = 1
    freq = dict(sorted(freq.items(), key=operator.itemgetter(1), reverse=True))
    return freq


class Scraper:
    def __init__(self, links):
        self.links = links
        self.number = len(links)
        self.responses = []
        self.classes = []

    def get_content(self, url):
        resp = requests.get(url)
        self.responses.append(resp.content)
        time.sleep(0.05)

    def process_info(self, response):
        soup = BeautifulSoup(response, 'html.parser')
        for code in soup.select('[itemprop="Code"]:has(~ meta[itemprop="Leaf"])'):
            code_text = code.text
            code_desc = code.find_next('span').text
            self.classes.append(code_text + ": " + code_desc)

    def scrape(self):
        urls = self.links
        threads = min(MAX_THREADS, self.number)
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            executor.map(self.get_content, urls)
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            executor.map(self.process_info, self.responses)
        freq = fill_freq(self.classes)
        return freq
