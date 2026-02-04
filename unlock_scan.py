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

def get_projects(html, debug=False):
    soup = BeautifulSoup(html, 'html.parser')
    result = []

    if debug:
        with open('debug_unlocks_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("DEBUG: Saved HTML to debug_unlocks_page.html")

    # Strategy 1: Find table rows with links to token pages
    # Look for <tr> elements that contain links starting with /token/
    all_rows = soup.find_all('tr')
    print(f'Total TR elements found: {len(all_rows)}')

    for row in all_rows:
        # Skip header rows (usually contain <th> instead of <td>)
        if row.find('th'):
            continue

        # Look for links that point to token pages
        link_tag = row.find('a', href=lambda x: x and '/token/' in x)
        if link_tag:
            link = link_tag.get('href', '')
            # Try to get the token name from nearby text
            # Usually it's in a div near the link or the link text itself
            text = None

            # Try to find token name in the first td
            first_td = row.find('td')
            if first_td:
                # Look for text in nested divs
                divs = first_td.find_all('div')
                for div in divs:
                    div_text = div.get_text(strip=True)
                    # Token names are usually short and don't contain special chars
                    if div_text and len(div_text) < 30 and not div_text.startswith('$'):
                        text = div_text
                        break

            if not text:
                text = link_tag.get_text(strip=True)

            if not text:
                # Extract from URL as fallback
                text = link.split('/')[-1].upper()

            if link and text:
                print(f"Found: {link} -> {text}")
                result.append([link, text])

    print('TAGS size: ', len(result))
    return result

def get_date(html, project, offset_hours=3, debug=False):
    soup = BeautifulSoup(html, 'html.parser')

    if debug:
        safe_name = project.replace('/', '_').replace(' ', '_')
        with open(f'debug_token_{safe_name}.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"DEBUG: Saved HTML to debug_token_{safe_name}.html")

    # Strategy 1: Look for unlock date/time patterns in the page
    # Common patterns: dates like "Feb 15, 2026" or "15 Feb 26" with times
    import re

    # Try to find date patterns in text content
    page_text = soup.get_text()

    # Look for "Next Unlock" or similar sections
    next_unlock_pattern = re.search(
        r'(?:Next\s+Unlock|Upcoming\s+Unlock|Next\s+Event)[:\s]*([A-Za-z]{3})\s+(\d{1,2}),?\s+(\d{2,4})\s+(\d{1,2}:\d{2}\s*(?:AM|PM)?)',
        page_text,
        re.IGNORECASE
    )

    if next_unlock_pattern:
        month, day, year, time_str = next_unlock_pattern.groups()
        if len(year) == 2:
            year = '20' + year
        utc_time_str = f"{day} {month} {year} {time_str}"
        try:
            utc_time = datetime.strptime(utc_time_str, "%d %b %Y %I:%M %p")
        except ValueError:
            try:
                utc_time = datetime.strptime(utc_time_str, "%d %b %Y %H:%M")
            except ValueError:
                print(f"Could not parse date for {project}: {utc_time_str}")
                return project, "Unknown"

        local_time = utc_time + timedelta(hours=offset_hours)
        local_time_str = local_time.strftime("%d %b %y %I:%M %p")
        print(project, local_time_str)
        return project, local_time_str

    # Strategy 2: Look for time elements or data attributes
    time_elements = soup.find_all(['time', 'span', 'div'], attrs={'datetime': True})
    for elem in time_elements:
        dt_str = elem.get('datetime', '')
        if dt_str:
            try:
                utc_time = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                local_time = utc_time + timedelta(hours=offset_hours)
                local_time_str = local_time.strftime("%d %b %y %I:%M %p")
                print(project, local_time_str)
                return project, local_time_str
            except ValueError:
                continue

    # Strategy 3: Original method with flexible class matching
    tags = soup.find_all('div', class_=lambda x: x and 'flex' in x and 'items-center' in x and 'justify-between' in x)

    if tags:
        try:
            # Look for date components in the last matching tag
            date_divs = tags[-1].find_all('div', class_=lambda x: x and 'font-' in str(x))
            if len(date_divs) >= 4:
                year = date_divs[-3].text.strip()
                month = date_divs[-2].text.strip()
                day = date_divs[-1].text.strip()
                time_str = date_divs[0].text.strip()

                utc_time_str = f"{day} {month} {year} {time_str.replace(' : ', ':')}"
                utc_time = datetime.strptime(utc_time_str, "%d %b %y %I:%M %p")
                local_time = utc_time + timedelta(hours=offset_hours)
                local_time_str = local_time.strftime("%d %b %y %I:%M %p")
                print(project, local_time_str)
                return project, local_time_str
        except (IndexError, ValueError) as e:
            print(f"Strategy 3 failed for {project}: {e}")

    print(f"Could not find unlock date for {project}")
    return project, "Unknown"

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
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Optional: Run in headless mode
        # options.add_argument('--headless=new')
    
        try:
            # Let undetected-chromedriver handle version matching automatically
            self.driver = uc.Chrome(options=options, version_main=None)
        except Exception as e:
            print(f"Failed to initialize with auto-version, trying with use_subprocess: {e}")
            # Fallback: try with use_subprocess=False
            self.driver = uc.Chrome(options=options, use_subprocess=False, version_main=None)
            
        self.driver.implicitly_wait(10)
        self.driver.set_page_load_timeout(60)
    
        # Apply selenium-stealth configurations
        stealth(self.driver,
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

    def wait_for_table(self, timeout=30):
        """Wait for the table to load by checking for tr elements with links"""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        try:
            # Wait for any table row with a token link to appear
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "tr a[href*='/token/']"))
            )
            return True
        except Exception as e:
            print(f"Timeout waiting for table: {e}")
            return False

    def scroll_to_load(self, scrolls=3, delay=2):
        """Scroll down to trigger lazy loading"""
        for i in range(scrolls):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(delay)

    def get_page(self):
        return self.driver.page_source

    def close(self):
        self.driver.quit()

class Unlock:
    def __init__(self, debug=False):
        self.debug = debug

    def check(self):
        browser = ChromeBrowserN(1)
        try:
            browser.load_page("https://tokenomist.ai/unlocks")

            # Wait for the table to load (SPA)
            if browser.wait_for_table(timeout=30):
                print("Table loaded successfully")
            else:
                print("Table did not load within timeout, proceeding anyway...")

            # Scroll to load more content
            browser.scroll_to_load(scrolls=3, delay=2)
            time.sleep(3)

            page = browser.get_page()
            projects = get_projects(page, debug=self.debug)
            print('Projects: ', projects)

            if not projects:
                print("WARNING: No projects found. The website structure may have changed.")
                print("Enable debug mode to save HTML for analysis.")
                if self.debug:
                    print("Debug HTML saved. Check debug_unlocks_page.html")
                return

            tokens = {}

            # Filter projects to only those in our currency list
            currency_lower = [c.lower() for c in s.currency]

            for project in projects:
                # Extract token symbol from the link or name
                token_symbol = project[0].split('/')[-1].upper()
                project_name = project[1].upper()

                # Check if this token is in our watchlist
                if token_symbol.lower() in currency_lower or any(c in project_name for c in s.currency):
                    browser.load_page("https://tokenomist.ai" + project[0])
                    time.sleep(5)
                    page = browser.get_page()
                    token, dtt = get_date(page, project[1], debug=self.debug)
                    tokens[token] = dtt

            self.save_unlocks(tokens)
        finally:
            browser.close()

    def save_unlocks(self, tokens):
        with open('token_unlocks.txt', 'w') as file:
            for token, unlock_time in tokens.items():
                file.write(f"{token}: {unlock_time}\n")

def unlock_scan(debug=False):
    Unlock(debug=debug).check()

if __name__ == "__main__":
    import sys
    debug_mode = '--debug' in sys.argv
    unlock_scan(debug=debug_mode)
