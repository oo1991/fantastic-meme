from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

def get_fear_and_greed_index_coinmarketcap():
    # Set up the Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode (no GUI)
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    # Navigate to CoinMarketCap
    url = "https://coinmarketcap.com/"
    driver.get(url)

    # Wait for the page to load and locate the Fear & Greed Index element
    driver.implicitly_wait(10)  # Wait for up to 10 seconds for elements to be found

    try:
        fng_element = driver.find_element(By.XPATH, "//span[contains(@class, 'sc-d1ede7e3-0 cbgGwO base-text')]")
        fng_index = fng_element.text
        return fng_index
    except Exception as e:
        print(f"Error fetching from CoinMarketCap: {e}")
        return None
    finally:
        driver.quit()

def get_fear_and_greed_index_cryptorank():
    # Set up the Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode (no GUI)
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    # Navigate to CryptoRank.io
    url = "https://cryptorank.io/"
    driver.get(url)

    # Wait for the page to load and locate the Fear & Greed Index element
    driver.implicitly_wait(10)  # Wait for up to 10 seconds for elements to be found

    try:
        # Locate the Fear & Greed Index element using the appropriate class or tag
        fng_element = driver.find_element(By.XPATH, "//p[@class='sc-b7cd6de0-0 sc-ee1f942b-1 hDybRk kwaTsJ']")
        fng_index = fng_element.text
        return fng_index
    except Exception as e:
        print(f"Error fetching from CryptoRank: {e}")
        return None
    finally:
        driver.quit()

def save_fear_and_greed_indices():
    coinmarketcap_index = get_fear_and_greed_index_coinmarketcap()
    cryptorank_index = get_fear_and_greed_index_cryptorank()
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

if __name__ == "__main__":
    save_fear_and_greed_indices()
