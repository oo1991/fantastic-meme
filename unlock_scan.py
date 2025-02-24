import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import time
from settings import s
import undetected_chromedriver as uc
from selenium_stealth import stealth

def get_projects(html):
    soup = BeautifulSoup(html, 'html.parser')
    result = []

    tags = soup.find_all('tr', {'class': 'group cursor-pointer border-b-[1px] border-background-secondary bg-background hover:bg-[#F6E8ED] dark:border-background-dark-secondary dark:bg-background-dark hover:dark:bg-[#351226]'})
    print('TAGS size: ', len(tags))
    for tag in tags:
        td_tags = tag.find('td', {'class': 'bg-background group-hover:bg-[#F6E8ED] dark:bg-background-dark group-hover:dark:bg-[#351226] after:duration-300 after:transition-shadow after:absolute after:-bottom-px after:right-0 after:top-0 after:w-[20px] after:shadow-table-col-left desktop:after:shadow-none after:translate-x-full after:opacity-0'})
        link = td_tags.find('a')['href']
        print(link)
        text = td_tags.find('div').find('div').text
        print(text)
        
        result.append([link, text])
    
    return result

def get_date(html, project, offset_hours=3):
    soup = BeautifulSoup(html, 'html.parser')

    tags = soup.find_all('div', {'class': 'mb-4 flex items-center justify-between'})

    year = tags[-1].find_all('div', {'class': 'font-inter tracking-[-0.12px] text-[13px] leading-[16px] font-medium text-left'})[-3].text
    month = tags[-1].find_all('div', {'class': 'font-inter tracking-[-0.12px] text-[13px] leading-[16px] font-medium text-left'})[-2].text
    day = tags[-1].find_all('div', {'class': 'font-inter tracking-[-0.12px] text-[13px] leading-[16px] font-medium text-left'})[-1].text
    time_str = tags[-1].find_all('div', {'class': 'font-inter tracking-[-0.12px] text-[13px] leading-[16px] font-medium text-left'})[0].text

    utc_time_str = f"{day} {month} {year} {time_str.replace(' : ', ':')} UTC"
    utc_time_str = utc_time_str.replace(" UTC", "")  # Remove ' UTC' for parsing
    utc_time = datetime.strptime(utc_time_str, "%d %b %y %I:%M %p")
    local_time = utc_time + timedelta(hours=offset_hours)
    local_time_str = local_time.strftime("%d %b %y %I:%M %p")
    print(project, local_time_str)

    return project, local_time_str

def extract_token_unlock_data(html):
    soup = BeautifulSoup(html, 'html.parser')

    market_cap = soup.find_all('div', {'class': 'text-right shrink-0 whitespace-nowrap'})

    dates = []
    times = []

    for m in market_cap:
        date = m.find('p', {'class': 'un-font-inter un-text-[10px] un-leading-[12px] laptop:un-text-[12px] laptop:un-leading-[16px] un-font-medium un-font-inter un-text-right text-white dark:text-white-dark'}).text
        dates.append(date)
        time = m.find('p', {'class': 'un-font-inter un-text-[10px] un-leading-[12px] laptop:un-text-[12px] laptop:un-leading-[16px] un-font-normal un-font-inter un-text-right text-white-secondary dark:text-white-dark-secondary'}).text
        times.append(time)

    rr = soup.find_all('span', {'class': 'un-inline-flex un-w-fit un-h-fit un-rounded-[4px] un-bg-black-disabled dark:un-bg-black-dark-disabled un-text-black-secondary dark:un-text-black-dark-secondary un-px-[4px] un-py-[2px] un-font-dmmono un-text-[10px] un-leading-[12px]'})

    token_names = []

    for r in rr:
        if r.text not in token_names:
            token_names.append(r.text)

    result = {}

    for token, date, time in zip(token_names, dates, times):
        if token in s.currency:
            result[token] = f"{date} {time}"

    return result

def load_file(filename):
    with open(filename, 'r') as file:
        file_contents = file.read()
    return file_contents

def save_page(page):
    with open('unlock.txt', 'w') as file:
        file.write(page)

class ChromeBrowserN:
    def __init__(self, num):
        #options = webdriver.ChromeOptions()
        #options.add_argument('--headless')
        #self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        #self.driver.implicitly_wait(10)
        options = uc.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36")
        
        # Optional: Run in headless mode
        # options.add_argument('--headless=new')
    
        self.driver = uc.Chrome(options=options)
        self.driver.implicitly_wait(10)
        self.driver.set_page_load_timeout(10)
    
        # Apply selenium-stealth configurations
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)
    
        # Execute additional JavaScript to hide automation fingerprints
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                    Object.defineProperty(window, 'outerWidth', { value: 1920 });
                    Object.defineProperty(window, 'outerHeight', { value: 1080 });
                """
            }
        )
    
    def load_page(self, url):
        self.driver.get(url)
    
    def get_page(self):
        return self.driver.page_source

    def close(self):
        self.driver.quit()

class Unlock:
    def __init__(self):
        pass

    def check(self):
        browser = ChromeBrowserN(1)
        browser.load_page("https://tokenomist.ai/unlocks")
        time.sleep(3)

        page = browser.get_page()
        projects = get_projects(page)
        print('Projects: ', projects)

        tokens = {}

        for project in projects:
            browser.load_page("https://tokenomist.ai" + project[0])
            time.sleep(5)
            page = browser.get_page()
            token, dtt = get_date(page, project[1])
            tokens[token] = dtt

        browser.close()

        self.save_unlocks(tokens)

    def save_unlocks(self, tokens):
        with open('token_unlocks.txt', 'w') as file:
            for token, unlock_time in tokens.items():
                file.write(f"{token}: {unlock_time}\n")

def unlock_scan():
    Unlock().check()

if __name__ == "__main__":
    unlock_scan()
