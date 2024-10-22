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

def get_fear_and_greed_index_coinmarketcap():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    
    url = "https://coinmarketcap.com/"
    driver.get(url)
    
    try:
        # Explicit wait for the Fear and Greed index element
        fng_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='FearAndGreedCard_score__8bXjA']"))
        )
        fng_index = fng_element.text
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
