from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

def get_fear_and_greed_index():
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
        fng_element = driver.find_element(By.XPATH, "//p[@class='sc-b7c6dde0-0 hbyBrk kwaTsJ']")
        fng_index = fng_element.text
        print(f"Fear & Greed Index: {fng_index}")
        
        # Save the index to a file with a timestamp to ensure it's always updated
        with open("fear_and_greed_index.txt", "w") as file:
            file.write(f"Fear & Greed Index: {fng_index}\n")
            file.write(f"Updated at: {datetime.utcnow().isoformat()}Z\n")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    get_fear_and_greed_index()
