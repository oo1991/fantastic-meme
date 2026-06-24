import requests

def _bs4():
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup
    except ModuleNotFoundError:
        raise ModuleNotFoundError(
            "Missing dependency 'bs4' (BeautifulSoup). Install with:\n"
            "  pip install beautifulsoup4\n"
            "Or on Debian/Ubuntu: sudo apt-get install python3-bs4"
        )
from datetime import datetime, UTC
def _selenium():
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.service import Service as ChromeService
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        return webdriver, By, ChromeService, WebDriverWait, EC, ChromeDriverManager
    except ModuleNotFoundError:
        raise ModuleNotFoundError(
            "Missing Selenium dependencies. Install with:\n"
            "  pip install selenium webdriver-manager\n"
            "Or on Debian/Ubuntu: sudo apt-get install python3-selenium"
        )
import logging
import time
import sys

# Valid rainbow-band labels (the 2023 Bitcoin Rainbow Chart). Used to reject
# any unexpected text so scraper junk never reaches the output file.
RAINBOW_BANDS = {
    "Maximum Bubble Territory",
    "Sell. Seriously, SELL!",
    "FOMO intensifies",
    "Is this a bubble?",
    "HODL!",
    "Still cheap",
    "Accumulate",
    "BUY!",
    "Basically a Fire Sale",
}

# JS run in the rendered page: for every rainbow chart on the page, return its
# nearest preceding heading text plus the currently-highlighted band label.
# blockchaincenter.net now ships a client-rendered React app where each chart is
# a `.rainbow-container` and the active band is `.rainbow-legend-item.active`.
_RAINBOW_PROBE_JS = r"""
const out = [];
for (const c of document.querySelectorAll('div.rainbow-container')) {
  // Walk up/back to find the nearest heading describing this chart.
  let heading = '';
  let el = c;
  outer:
  while (el) {
    let p = el.previousElementSibling;
    while (p) {
      if (p.matches && p.matches('h1,h2,h3')) { heading = p.innerText; break outer; }
      const hd = p.querySelector && p.querySelector('h1,h2,h3');
      if (hd) { heading = hd.innerText; break outer; }
      p = p.previousElementSibling;
    }
    el = el.parentElement;
  }
  const active = c.querySelector('div.rainbow-legend-item.active');
  out.push({ heading: (heading || '').trim(), band: active ? active.innerText.trim() : '' });
}
return out;
"""


def _pick_rainbow_band(charts):
    """Choose the band from the modern 'Bitcoin Rainbow Chart'.

    The page now renders two charts: 'The Original Chart' (a legacy regression
    whose active band sits at the degenerate 'Bitcoin is dead' extreme) and 'The
    2023 Bitcoin Rainbow Chart' (the canonical one). Prefer the latter; among
    several, prefer the highest year in the heading.
    """
    import re

    def year(h):
        m = re.search(r'(20\d{2})', h or '')
        return int(m.group(1)) if m else -1

    # 1) Headings that mention "rainbow chart", with a recognised band.
    named = [c for c in charts
             if 'rainbow chart' in (c['heading'] or '').lower()
             and c['band'] in RAINBOW_BANDS]
    if named:
        return max(named, key=lambda c: year(c['heading']))['band']

    # 2) Any chart with a recognised band (skips the 'Bitcoin is dead' original).
    valid = [c for c in charts if c['band'] in RAINBOW_BANDS]
    if valid:
        return max(valid, key=lambda c: year(c['heading']))['band']

    return None


def get_rainbow():
    url = "https://www.blockchaincenter.net/en/bitcoin-rainbow-chart/"
    output_file = "rainbow.txt"

    webdriver, By, ChromeService, WebDriverWait, EC, ChromeDriverManager = _selenium()
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')

    driver = None
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(60)
        driver.get(url)

        # The chart is client-rendered; wait for at least one legend to appear.
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.rainbow-legend-item.active'))
            )
        except Exception:
            pass  # fall through; the probe below will report if nothing rendered
        time.sleep(2)

        charts = driver.execute_script(_RAINBOW_PROBE_JS) or []
        band = _pick_rainbow_band(charts)

        if band:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(band + '\n')
            print(f"Bitcoin Rainbow Chart band: {band}")
        else:
            error_message = "Could not determine the Bitcoin Rainbow Chart band (page structure may have changed)."
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(error_message)
            print(error_message)
            print(f"Probed charts: {charts}")
    except Exception as e:
        error_message = f"An error occurred while fetching the Bitcoin Rainbow Chart: {e}"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(error_message)
        print(error_message)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

def get_fear_and_greed_index_coinmarketcap():
    """
    Fetch the Fear & Greed index value and classification via the
    Alternative.me public API (same underlying index as CoinMarketCap).
    """
    for attempt in range(3):
        try:
            resp = requests.get(
                "https://api.alternative.me/fng/?limit=1&format=json",
                timeout=10,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/126.0 Safari/537.36"
                    )
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict) and "data" in data and data["data"]:
                entry = data["data"][0]
                value = entry.get("value", "").strip()
                classification = entry.get("value_classification", "").strip()
                if value:
                    return f"{value} ({classification})" if classification else value
            return None
        except Exception as e:
            print(f"Error fetching Fear & Greed index (CoinMarketCap), attempt {attempt + 1}/3: {e}")
            if attempt < 2:
                time.sleep(5)
    return None

def get_fear_and_greed_index_cryptorank():
    """
    Fetch the Fear & Greed index via a stable API instead of
    scraping CryptoRank's frequently-changing DOM. Keeps the
    existing label in the report while providing reliable data.
    """
    for attempt in range(3):
        try:
            # Alternative.me provides a public Fear & Greed API
            # Docs: https://api.alternative.me/fng/
            resp = requests.get(
                "https://api.alternative.me/fng/?limit=1&format=json",
                timeout=10,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/126.0 Safari/537.36"
                    )
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict) and "data" in data and data["data"]:
                value = data["data"][0].get("value")
                if value:
                    return value.strip()
            return None
        except Exception as e:
            print(f"Error fetching Fear & Greed index (API fallback), attempt {attempt + 1}/3: {e}")
            if attempt < 2:
                time.sleep(5)
    return None

def get_cbbi_index():
    try:
        resp = requests.get(
            "https://colintalkscrypto.com/cbbi/data/latest.json",
            timeout=15,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0 Safari/537.36"
                )
            },
        )
        resp.raise_for_status()
        data = resp.json()
        confidence = data.get("Confidence", {})
        if not confidence:
            print("CBBI API returned no Confidence data.")
            return ""
        latest_ts = max(confidence.keys(), key=int)
        score = round(confidence[latest_ts] * 100)
        print(f"CBBI Index: {score}%")
        return f"{score}%"
    except Exception as e:
        print(f"Error fetching CBBI Index: {e}")
        return ""

def get_usdt_cap():
    webdriver, By, ChromeService, WebDriverWait, EC, ChromeDriverManager = _selenium()
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')

    driver = None
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(60)
        
        url = "https://tether.to/en/transparency/?tab=usdt"
        driver.get(url)
        
        driver.implicitly_wait(10)
    
        time.sleep(5)
    
        page = driver.page_source
    
        BeautifulSoup = _bs4()
        soup = BeautifulSoup(page, 'html.parser')
    
        usdt_circulation_element = soup.find('h4', {'class': 'MuiTypography-root jss46 MuiTypography-h4'})  # Example class name
        
        if usdt_circulation_element:
            # Extract the text (USDT amount) from the element
            usdt_circulation = usdt_circulation_element.text.strip()
            print(f"USDT in circulation: {usdt_circulation}")
            return usdt_circulation
        else:
            print("Could not find the USDT circulation data on the page.")
            return '-1'
    except Exception as e:
        print(f"Error fetching USDT Cap: {e}")
        return '-1'
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

def get_altcoin_season_index(url: str = "https://www.blockchaincenter.net/en/altcoin-season-index/") -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()

        BeautifulSoup = _bs4()
        soup = BeautifulSoup(response.content, 'html.parser')

        index_div = soup.find('div', style=lambda value: value and 'font-size:88px' in value)

        if index_div:
            altcoin_index = index_div.text.strip()
            return altcoin_index
        else:
            return "Could not find the Altcoin Season Index on the page. The structure of the page might have changed."

    except requests.exceptions.RequestException as e:
        return f"An error occurred while fetching the Altcoin Season Index: {e}"

def save_fear_and_greed_indices():
    error = False
    coinmarketcap_index = get_fear_and_greed_index_coinmarketcap()
    cryptorank_index = get_fear_and_greed_index_cryptorank()
    altcoin_index = get_altcoin_season_index()
    cbbi_index = get_cbbi_index()
    usdt_cap = get_usdt_cap()
    scan_time = datetime.now(UTC).isoformat().replace('+00:00', 'Z')

    with open("fear_and_greed_index.txt", "w", encoding='utf-8') as file:
        file.write(f"Scan Time: {scan_time}\n")
        if coinmarketcap_index:
            file.write(f"CoinMarketCap Fear & Greed Index: {coinmarketcap_index}\n")
        else:
            file.write("CoinMarketCap Fear & Greed Index: Error fetching data (non-fatal)\n")

        if cryptorank_index:
            file.write(f"CryptoRank Fear & Greed Index: {cryptorank_index}\n")
        else:
            file.write("CryptoRank Fear & Greed Index: Error fetching data (non-fatal)\n")
        
        if "An error occurred" not in altcoin_index:
            file.write(f"Altcoin Season Index: {altcoin_index}\n")
        else:
            file.write("Altcoin Season Index: Error fetching data\n")
            error = True

        if cbbi_index:
            file.write(f"CBBI Index: {cbbi_index}\n")
        else:
            file.write("CBBI Index: Error fetching data\n")
            error = True

        if usdt_cap:
            file.write(f"USDT Cap: {usdt_cap}\n")
        else:
            file.write("USDT Cap: Error fetching data\n")
            error = True

    if error:
        sys.exit(1)

if __name__ == "__main__":
    save_fear_and_greed_indices()
    get_rainbow()
