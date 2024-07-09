from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import requests

def initialize_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--remote-debugging-port=9222')  # Aggiunge il port debugging
    options.add_argument('--disable-software-rasterizer')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def get_toxicity_data(ingredient):
    driver = initialize_driver()
    try:
        # Make the API request to get the substance details
        api_url = f"https://chem.echa.europa.eu/api-substance/v1/substance?pageIndex=1&pageSize=100&searchText={ingredient.replace(' ', '%20')}"
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        
        # Extract the rmlId from the first item in the results
        rmlId = data['items'][0]['substanceIndex']['rmlId']
        print(f"Extracted rmlId: {rmlId}")
        
        # Navigate to the dossier list page
        dossier_url = f"https://chem.echa.europa.eu/{rmlId}/dossier-list/reach/dossiers/active?searchText={ingredient.replace(' ', '%20')}"
        print(f"Navigating to dossier list page: {dossier_url}")
        driver.get(dossier_url)
        
        wait = WebDriverWait(driver, 30)
        
        # Accept cookies, if present
        try:
            accept_cookies_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//button[text()="Accept all cookies"]'))
            )
            accept_cookies_button.click()
            print("Cookies accepted")
        except Exception as e:
            print("Cookies acceptance button not found or already accepted.")
        
        # Accept the legal notice, if present
        try:
            accept_terms_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//button[text()="I Accept the terms"]'))
            )
            accept_terms_button.click()
            print("Terms accepted")
            time.sleep(2)
        except Exception as e:
            print("Legal notice acceptance not found or already accepted.")
        
        print("Finding the first dossier link...")
        # Scroll the page to ensure all elements are loaded
        driver.execute_script("window.scrollTo(0, 500);")  # Scroll down a bit
        time.sleep(2)  # Add a pause to allow elements to load

        # Extract the page source
        page_source = driver.page_source

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')

        # Find the first dossier link
        first_dossier_link = soup.select_one('a.das-button-icon.das-button-secondary[href^="/100.003.443/dossier-view/"]')
        if not first_dossier_link:
            print("First dossier link not found. Printing relevant HTML for debugging:")
            print(soup.prettify())
            return

        href_value = first_dossier_link['href']
        dossier_view_url = f"https://chem.echa.europa.eu{href_value}"
        print(f"First dossier link: {dossier_view_url}")

        # Navigate to the dossier view page
        print(f"Navigating to dossier view page: {dossier_view_url}")
        driver.get(dossier_view_url)

        # Attendere che l'URL della pagina cambi
        WebDriverWait(driver, 30).until(lambda driver: driver.current_url != dossier_view_url)
        
        # Ottenere l'URL completo della pagina corrente
        full_url = driver.current_url
        print(f"Full dossier URL: {full_url}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Closing the browser...")
        driver.quit()

# Esempio di utilizzo
get_toxicity_data("1,4 Butanediol")
