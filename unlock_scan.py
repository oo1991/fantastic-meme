import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta, timezone
import time
from settings import s
import undetected_chromedriver as uc
from selenium_stealth import stealth

def get_projects(html, debug=False):
    soup = BeautifulSoup(html, 'html.parser')
    result = []
    seen_links = set()

    # Always save HTML when debugging or when we need to troubleshoot
    if debug:
        with open('debug_unlocks_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("DEBUG: Saved HTML to debug_unlocks_page.html")

    # Known navigation paths to exclude when matching /<slug> token links
    nav_paths = {
        '/', '/overview', '/update', '/auth/signin', '/pricing',
        '/onchain-claim', '/fundraising/screener',
        '/buyback/compare', '/buyback/screener',
        '/burn/compare', '/burn/screener',
        '/wenunlocks', '/insights', '/builder/landing',
    }

    # Strategy 0: New URL format — token pages are now /<slug> links inside table rows
    # Also extract time-left from the 7th td in each row
    tbody = soup.find('tbody')
    if tbody:
        rows = tbody.find_all('tr', class_=lambda x: x and 'cursor-pointer' in x)
        print(f'Total table rows found: {len(rows)}')
        for row in rows:
            # Find the token link in this row
            link_tag = row.find('a', href=True)
            if not link_tag:
                continue
            link = link_tag.get('href', '')
            if not (link.startswith('/')
                    and link.count('/') == 1
                    and link not in nav_paths
                    and not link.startswith('/#')):
                continue
            if link in seen_links:
                continue
            seen_links.add(link)

            text = link_tag.get_text(strip=True)
            if not text or len(text) > 50:
                text = link.strip('/').upper()

            # Extract time-left from the 7th td (0-indexed: tds[6])
            time_left = ""
            tds = row.find_all('td')
            if len(tds) >= 7:
                button = tds[6].find('button')
                if button:
                    divs = button.find_all('div', recursive=False)
                    if len(divs) >= 3:
                        # 3rd div contains the countdown grid with D/H/M/S spans
                        countdown_spans = divs[2].find_all('span')
                        # Spans alternate: value, unit, value, unit...
                        parts = [s.get_text(strip=True) for s in countdown_spans]
                        # Pair them up: "0" "D" "15" "H" "56" "M" "9" "S"
                        time_left = " ".join(f"{parts[i]}{parts[i+1]}" for i in range(0, len(parts) - 1, 2))

            if link and text:
                print(f"Found: {text} -> {time_left}")
                result.append([link, text, time_left])

    # Strategy 1: Find all links to token pages anywhere in the document
    # Check for various URL patterns: /token/, token.unlocks.app, /unlocks/
    if not result:
        all_links = soup.find_all('a', href=lambda x: x and ('/token/' in x or 'token.unlocks.app' in x))
        print(f'Total links with /token/ or token.unlocks.app found: {len(all_links)}')

        for link_tag in all_links:
            link = link_tag.get('href', '')
            if link in seen_links:
                continue
            seen_links.add(link)

            # Try to get the token name
            text = link_tag.get_text(strip=True)
            if not text or len(text) > 50:
                # Extract from URL as fallback
                text = link.split('/')[-1].upper()

            if link and text:
                print(f"Found: {link} -> {text}")
                result.append([link, text])

    # Strategy 2: If no /token/ links, try /unlocks/ links
    if not result:
        all_links = soup.find_all('a', href=lambda x: x and '/unlocks/' in x)
        print(f'Total links with /unlocks/ found: {len(all_links)}')
        for link_tag in all_links:
            link = link_tag.get('href', '')
            if link in seen_links:
                continue
            seen_links.add(link)
            text = link_tag.get_text(strip=True)
            if not text:
                text = link.split('/')[-1].upper()
            if link and text:
                print(f"Found: {link} -> {text}")
                result.append([link, text])

    # Strategy 3: Look for any links that might be token-related
    if not result:
        # Look for links in table rows
        all_rows = soup.find_all('tr')
        print(f'Total TR elements found: {len(all_rows)}')
        for row in all_rows:
            links = row.find_all('a', href=True)
            for link_tag in links:
                link = link_tag.get('href', '')
                # Skip navigation/external links
                if link.startswith('#') or link.startswith('http') and 'tokenomist' not in link:
                    continue
                if link in seen_links:
                    continue
                seen_links.add(link)
                text = link_tag.get_text(strip=True)
                if link and text and len(text) < 50:
                    print(f"Found in TR: {link} -> {text}")
                    result.append([link, text])

    # Strategy 4: Debug - print all links found on page
    if not result:
        print("DEBUG: No projects found. Listing all links on page:")
        all_links = soup.find_all('a', href=True)[:20]  # First 20 links
        for link_tag in all_links:
            print(f"  Link: {link_tag.get('href', '')} -> {link_tag.get_text(strip=True)[:50]}")

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
    def _make_options(self):
        options = uc.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
        return options

    def _detect_chrome_version(self):
        import subprocess, re, platform
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["reg", "query", r"HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon", "/v", "version"],
                    capture_output=True, text=True
                )
                match = re.search(r"(\d+)\.\d+\.\d+\.\d+", result.stdout)
            else:
                result = subprocess.run(["google-chrome", "--version"], capture_output=True, text=True)
                match = re.search(r"(\d+)\.\d+\.\d+\.\d+", result.stdout)
            if match:
                return int(match.group(1))
        except Exception as e:
            print(f"Could not detect Chrome version: {e}")
        return None

    def _create_driver(self, version, headless=True):
        opts = self._make_options() if headless else self._make_options_visible()
        try:
            driver = uc.Chrome(options=opts, version_main=version)
        except Exception as e:
            print(f"Failed to initialize, trying with use_subprocess: {e}")
            opts = self._make_options() if headless else self._make_options_visible()
            driver = uc.Chrome(options=opts, use_subprocess=False, version_main=version)
        driver.implicitly_wait(10)
        driver.set_page_load_timeout(60)
        return driver

    def _make_options_visible(self):
        options = uc.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
        return options

    def _apply_stealth(self, driver):
        """Apply stealth measures. Returns True if driver is still alive."""
        try:
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                        Object.defineProperty(window, 'outerWidth', { value: 1920 });
                        Object.defineProperty(window, 'outerHeight', { value: 1080 });
                        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                    """
                }
            )
        except Exception as e:
            print(f"CDP injection failed: {e}")
            return False

        try:
            stealth(driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True)
        except Exception:
            pass  # stealth is optional if CDP worked
        return True

    def __init__(self, num):
        version = self._detect_chrome_version()
        if version:
            print(f"Detected Chrome major version: {version}")

        # Try headless first, fall back to visible if driver session dies
        self.driver = self._create_driver(version, headless=True)
        if not self._apply_stealth(self.driver):
            print("Headless driver died, falling back to visible mode")
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = self._create_driver(version, headless=False)
            self._apply_stealth(self.driver)
    
    def load_page(self, url):
        self.driver.get(url)

    def wait_for_table(self, timeout=30):
        """Wait for the table to load by checking for tr elements with links"""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        try:
            # Wait for any table row with a link to appear
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "tbody tr a[href]"))
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

    def _try_load_projects(self, browser):
        """Load tokenomist.ai and extract projects. Returns list or empty list."""
        browser.load_page("https://tokenomist.ai")

        # Wait for Cloudflare challenge and SPA to fully load
        time.sleep(10)

        if browser.wait_for_table(timeout=45):
            print("Table loaded successfully")
        else:
            print("Table did not load within timeout, proceeding anyway...")

        # Scroll to load more content
        browser.scroll_to_load(scrolls=5, delay=3)
        time.sleep(5)

        page = browser.get_page()
        return get_projects(page, debug=self.debug), page

    def check(self):
        # Retry up to 3 times — Cloudflare challenge may block the first attempt
        max_attempts = 3
        projects = []
        page = ""

        for attempt in range(1, max_attempts + 1):
            browser = ChromeBrowserN(1)
            try:
                projects, page = self._try_load_projects(browser)
                print('Projects: ', projects)
                if projects:
                    break
                print(f"Attempt {attempt}/{max_attempts}: No projects found, retrying...")
            finally:
                browser.close()

            if attempt < max_attempts:
                time.sleep(10)

        if not projects:
            print("WARNING: No projects found after all attempts. The website structure may have changed.")
            with open('debug_unlocks_page.html', 'w', encoding='utf-8') as f:
                f.write(page)
            print("Debug HTML saved to debug_unlocks_page.html")
            with open('token_unlocks.txt', 'w') as f:
                f.write(f"# No unlock data available - website may have changed structure\n")
                f.write(f"# Last attempt: {datetime.now().isoformat()}\n")
            return

        tokens = {}

        # Filter projects to only those in our currency list
        currency_lower = [c.lower() for c in s.currency]

        now = datetime.now(timezone.utc) + timedelta(hours=3)  # UTC+3 local time

        for project in projects:
            token_symbol = project[0].split('/')[-1].upper()
            project_name = project[1].upper()
            time_left = project[2] if len(project) > 2 else ""

            # Check if this token is in our watchlist
            if token_symbol.lower() in currency_lower or any(c in project_name for c in s.currency):
                unlock_date = self._countdown_to_date(time_left, now)
                tokens[project_name] = unlock_date

        self.save_unlocks(tokens)

    def _countdown_to_date(self, countdown, now):
        """Convert '1D 3H 8M 46S' countdown to '26 Feb 05 03:08 AM' format."""
        import re
        days = hours = minutes = seconds = 0
        for match in re.finditer(r'(\d+)\s*([DHMS])', countdown):
            val, unit = int(match.group(1)), match.group(2)
            if unit == 'D':
                days = val
            elif unit == 'H':
                hours = val
            elif unit == 'M':
                minutes = val
            elif unit == 'S':
                seconds = val
        unlock_time = now + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        return unlock_time.strftime("%d %b %y %I:%M %p")

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
