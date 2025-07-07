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
import sys

def extract_active_spans(url: str, output_file: str) -> None:
    """
    Fetches the webpage at the specified URL, extracts <span> elements with the class 'active'
    within the <div> that has classes 'legend' and 'mt-2', prints their text content, and
    saves the results or any error messages to the specified output file.

    Parameters:
    - url (str): The URL of the webpage to fetch.
    - output_file (str): The path to the file where results or error messages will be saved.
    """
    try:
        # Optional: Define headers to mimic a real browser
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/58.0.3029.110 Safari/537.3'
            )
        }

        # Send a GET request to the URL with headers
        response = requests.get(url, headers=headers, timeout=10)  # Added timeout for better handling

        # Raise an exception if the request was unsuccessful
        response.raise_for_status()

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the <div> with classes "legend" and "mt-2"
        target_div = soup.find('div', class_='legend mt-2')

        if not target_div:
            error_message = "The target <div> with class 'legend mt-2' was not found."
            # Write the error message to the output file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(error_message)
            print(error_message)  # Optional: Also print the error to console
            return  # Exit the function early

        # Find all <span> elements with class "active" within the target <div>
        active_spans = target_div.find_all('span', class_='active')

        if not active_spans:
            error_message = "No <span> elements with class 'active' were found within the target <div>."
            # Write the error message to the output file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(error_message)
            print(error_message)  # Optional: Also print the error to console
            return  # Exit the function early

        # Open the file in write mode to save the results
        with open(output_file, 'w', encoding='utf-8') as f:
            # Iterate through each active <span> and write its text content to the file
            for span in active_spans:
                span_text = span.get_text(strip=True)
                print(span_text)  # Print to console
                f.write(span_text + '\n')  # Write to file

    except requests.exceptions.HTTPError as http_err:
        error_message = f"HTTP error occurred: {http_err}"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(error_message)
        print(error_message)  # Optional: Also print the error to console

    except requests.exceptions.ConnectionError as conn_err:
        error_message = f"Connection error occurred: {conn_err}"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(error_message)
        print(error_message)  # Optional: Also print the error to console

    except requests.exceptions.Timeout as timeout_err:
        error_message = f"Timeout error occurred: {timeout_err}"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(error_message)
        print(error_message)  # Optional: Also print the error to console

    except requests.exceptions.RequestException as req_err:
        error_message = f"An error occurred: {req_err}"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(error_message)
        print(error_message)  # Optional: Also print the error to console

def get_rainbow():
    url = "https://www.blockchaincenter.net/en/bitcoin-rainbow-chart/"
    output_file = "rainbow.txt"
    extract_active_spans(url, output_file)

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
        #print(html_content)  # Prints the first 5000 characters of the page content
        
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
        fng_element = driver.find_element(By.XPATH, "//p[@class='sc-b2e3d974-0 sc-ee1f942b-1 HyxpF kwaTsJ']")
        fng_index = fng_element.text
        return fng_index
    except Exception as e:
        print(f"Error fetching from CryptoRank: {e}")
        return None
    finally:
        driver.quit()

def get_cbbi_index():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    
    url = "https://colintalkscrypto.com/cbbi/"
    driver.get(url)
    
    driver.implicitly_wait(10)

    time.sleep(5)

    page = driver.page_source

    soup = BeautifulSoup(page, 'html.parser')
    
    # Find the <h1> tag with the given classes
    score_tag = soup.find('h1', class_='title confidence-score-value')
    if score_tag:
        print('CBBI Index: ', score_tag.get_text(strip=True))
        return score_tag.get_text(strip=True)
    else:
        print("Could not find the CBBI index on the page.")
        return ""

def get_usdt_cap():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    
    url = "https://tether.to/en/transparency/?tab=usdt"
    driver.get(url)
    
    driver.implicitly_wait(10)

    time.sleep(5)

    page = driver.page_source

    soup = BeautifulSoup(page, 'html.parser')

    usdt_circulation_element = soup.find('h4', {'class': 'MuiTypography-root jss46 MuiTypography-h4'})  # Example class name
    
    if usdt_circulation_element:
        # Extract the text (USD₮ amount) from the element
        usdt_circulation = usdt_circulation_element.text.strip()
        print(f"USD₮ in circulation: {usdt_circulation}")
        return usdt_circulation
    else:
        print("Could not find the USD₮ circulation data on the page.")
        return '-1'

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
    error = False
    coinmarketcap_index = get_fear_and_greed_index_coinmarketcap()
    cryptorank_index = get_fear_and_greed_index_cryptorank()
    altcoin_index = get_altcoin_season_index()
    cbbi_index = get_cbbi_index()
    usdt_cap = get_usdt_cap()
    scan_time = datetime.utcnow().isoformat() + "Z"

    with open("fear_and_greed_index.txt", "w") as file:
        file.write(f"Scan Time: {scan_time}\n")
        if coinmarketcap_index:
            file.write(f"CoinMarketCap Fear & Greed Index: {coinmarketcap_index}\n")
        else:
            file.write("CoinMarketCap Fear & Greed Index: Error fetching data\n")
            error = True

        if cryptorank_index:
            file.write(f"CryptoRank Fear & Greed Index: {cryptorank_index}\n")
        else:
            file.write("CryptoRank Fear & Greed Index: Error fetching data\n")
            error = True
        
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
