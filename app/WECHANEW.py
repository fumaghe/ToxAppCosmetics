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
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--headless')
    options.add_argument('--window-size=1920x1080')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def extract_href(soup, section_name):
    section = soup.find('button', string=lambda text: text and section_name in text)
    if not section:
        print(f"{section_name} section not found.")
        return None

    link = section.find_next('a', class_='das-leaf')
    if not link:
        print(f"Link not found in {section_name} section.")
        return None
    
    return link['href']

def get_toxicity_data(ingredient):
    driver = initialize_driver()
    try:
        # Make the API request to get the substance details
        api_url = f"https://chem.echa.europa.eu/api-substance/v1/substance?pageIndex=1&pageSize=100&searchText={ingredient.replace(' ', '%20')}"
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        
        # Extract the rmlId from the first item in the results
        rmlId = data['items'][0]['substanceIndex']['rmlId']
        print(f"Extracted rmlId: {rmlId}")
        
        # Make the API request to get the dossier details
        dossier_api_url = f"https://chem.echa.europa.eu/api-dossier-list/v1/dossier?pageIndex=1&pageSize=100&rmlId={rmlId}&registrationStatuses=Active"
        dossier_response = requests.get(dossier_api_url)
        dossier_response.raise_for_status()
        dossier_data = dossier_response.json()
        
        # Extract the assetExternalId from the first item in the results
        asset_external_id = dossier_data['items'][0]['assetExternalId']
        print(f"Extracted assetExternalId: {asset_external_id}")
        
        # Construct the URL for the HTML page
        html_page_url = f"https://chem.echa.europa.eu/html-pages/{asset_external_id}/index.html"
        print(f"HTML page URL: {html_page_url}")

        # Navigate to the HTML page
        print(f"Navigating to HTML page: {html_page_url}")
        driver.get(html_page_url)

        # Attendere che la pagina sia completamente caricata
        WebDriverWait(driver, 30).until(lambda driver: driver.current_url == html_page_url)

        # Estrai il link specifico per i dati di tossicità acuta
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Cerca il link nella sezione "Acute Toxicity"
        href_value = extract_href(soup, 'Acute Toxicity')
        
        # Se non trova il link nella sezione "Acute Toxicity", cerca nella sezione "Toxicological information"
        if not href_value:
            print("Trying to find link in Toxicological information section.")
            href_value = extract_href(soup, 'Toxicological information')

        if not href_value:
            print("Link not found in both sections. Printing relevant HTML for debugging:")
            print(soup.prettify())
            return

        document_url = f"https://chem.echa.europa.eu/html-pages/{asset_external_id}/documents/{href_value}.html"
        print(f"Document URL: {document_url}")

        # Navigate to the document page
        print(f"Navigating to document page: {document_url}")
        driver.get(document_url)

        # Attendere che la pagina sia completamente caricata
        WebDriverWait(driver, 30).until(lambda driver: driver.current_url == document_url)
        
        # Ottenere l'URL completo della pagina corrente
        full_url = driver.current_url
        print(f"Full document URL: {full_url}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Closing the browser...")
        driver.quit()

# Esempio di utilizzo
get_toxicity_data("1,4 Butanediol")