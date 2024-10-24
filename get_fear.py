import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import time

def get_fear_and_greed_index_from_page(html_content):
    """
    Extract the Fear and Greed index from the given HTML content.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    try:
        # Find the div containing the Fear and Greed index score
        fng_element = soup.find("div", class_="FearAndGreedCard_score__8bXjA")
        if fng_element:
            fng_index = fng_element.text.strip()
            return fng_index
        else:
            raise ValueError("Fear and Greed index element not found")
    except Exception as e:
        print(f"Error extracting Fear and Greed index: {e}")
        return None

def get_fear_and_greed_index_coinmarketcap():
    """
    Load the CoinMarketCap webpage and extract the Fear and Greed index.
    """
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run browser in headless mode
    options.add_argument('--disable-gpu')  # Disable GPU acceleration
    options.add_argument('--no-sandbox')  # Bypass OS security model
    options.add_argument('--window-size=1920,1080')  # Set window size
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.implicitly_wait(20)
    
    url = "https://coinmarketcap.com/"
    driver.get(url)

    try:
        # Wait until the page has fully loaded by waiting for a significant element
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))  # Adjust this to a reliable element
        )

        # Allow some extra time for JavaScript-rendered content to load
        time.sleep(5)

        # Get the full page source after waiting for the element
        html_content = driver.page_source
        
        # Print a portion of the page content for debugging
        print(html_content)  # Prints the first 5000 characters of the page content
        
        # Use the previously defined function to extract the Fear and Greed index from the page source
        fng_index = get_fear_and_greed_index_from_page(html_content)
        return fng_index
    except Exception as e:
        logging.error(f"Error fetching Fear and Greed index from CoinMarketCap: {e}")
        return None
    finally:
        driver.quit()

def get_fear_and_greed_index_cryptorank():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    
    url = "https://cryptorank.io/"
    driver.get(url)
    
    driver.implicitly_wait(10)
    
    try:
        fng_element = driver.find_element(By.XPATH, "//p[@class='sc-56567222-0 sc-ee1f942b-1 fzulHc kwaTsJ']")
        fng_index = fng_element.text
        return fng_index
    except Exception as e:
        print(f"Error fetching from CryptoRank: {e}")
        return None
    finally:
        driver.quit()

def get_altcoin_season_index(url: str = "https://www.blockchaincenter.net/en/altcoin-season-index/") -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()

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
    coinmarketcap_index = get_fear_and_greed_index_coinmarketcap()
    cryptorank_index = get_fear_and_greed_index_cryptorank()
    altcoin_index = get_altcoin_season_index()
    scan_time = datetime.utcnow().isoformat() + "Z"

    with open("fear_and_greed_index.txt", "w") as file:
        file.write(f"Scan Time: {scan_time}\n")
        if coinmarketcap_index:
            file.write(f"CoinMarketCap Fear & Greed Index: {coinmarketcap_index}\n")
        else:
            file.write("CoinMarketCap Fear & Greed Index: Error fetching data\n")

        if cryptorank_index:
            file.write(f"CryptoRank Fear & Greed Index: {cryptorank_index}\n")
        else:
            file.write("CryptoRank Fear & Greed Index: Error fetching data\n")
        
        if "An error occurred" not in altcoin_index:
            file.write(f"Altcoin Season Index: {altcoin_index}\n")
        else:
            file.write("Altcoin Season Index: Error fetching data\n")

if __name__ == "__main__":
    save_fear_and_greed_indices()
