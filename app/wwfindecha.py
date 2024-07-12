import sqlite3
import matplotlib.pyplot as plt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import json
from tqdm import tqdm 

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
    options.add_argument('--log-level=3')  
    options.add_argument('--disable-logging')
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

def fetch_document_content(document_url):
    document_response = requests.get(document_url)
    document_response.raise_for_status()
    return document_response.content

def extract_values(text):
    pattern = re.compile(r'(NOAEL|LD50)[^0-9]*(\d+[\.,]?\d*)\s*(mg/kg bw|mg/kg|g/kg|mg/L|g/L)')
    matches = pattern.finditer(text)
    echa_value = []
    for match in matches:
        value, unit = match.group(2), match.group(3)
        echa_number = f"{value} {unit}"
        words = text.split()
        value_index = words.index(value)
        context_before = ' '.join(words[max(0, value_index-10):value_index])
        context_after = ' '.join(words[value_index+1:min(len(words), value_index+11)])
        echa_context = f"{context_before} {value} {context_after}"
        echa_value.append([echa_number, echa_context])
    return echa_value

def get_toxicity_data_for_ingredient(driver, ingredient):
    try:
        api_url = f"https://chem.echa.europa.eu/api-substance/v1/substance?pageIndex=1&pageSize=100&searchText={ingredient.replace(' ', '%20')}"
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        
        if not data['items']:
            print(f"No data found for ingredient: {ingredient}")
            return None, None
        
        rmlId = data['items'][0]['substanceIndex']['rmlId']
        print(f"Extracted rmlId: {rmlId}")
        
        dossier_api_url = f"https://chem.echa.europa.eu/api-dossier-list/v1/dossier?pageIndex=1&pageSize=100&rmlId={rmlId}&registrationStatuses=Active"
        dossier_response = requests.get(dossier_api_url)
        dossier_response.raise_for_status()
        dossier_data = dossier_response.json()
        
        if not dossier_data['items']:
            print(f"No dossier data found for rmlId: {rmlId}")
            return None, None
        
        asset_external_id = dossier_data['items'][0]['assetExternalId']
        print(f"Extracted assetExternalId: {asset_external_id}")
        
        html_page_url = f"https://chem.echa.europa.eu/html-pages/{asset_external_id}/index.html"
        print(f"HTML page URL: {html_page_url}")

        print(f"Navigating to HTML page: {html_page_url}")
        driver.get(html_page_url)

        WebDriverWait(driver, 10).until(lambda driver: driver.current_url == html_page_url)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        href_value = extract_href(soup, 'Acute Toxicity')
        
        if not href_value:
            print("Trying to find link in Toxicological information section.")
            href_value = extract_href(soup, 'Toxicological information')

        if not href_value:
            print("Link not found in both sections. Printing relevant HTML for debugging:")
            print(soup.prettify())
            return None, None

        document_url = f"https://chem.echa.europa.eu/html-pages/{asset_external_id}/documents/{href_value}.html"
        print(f"Document URL: {document_url}")

        document_content = fetch_document_content(document_url)
        
        soup = BeautifulSoup(document_content, 'html.parser')

        text_content = soup.get_text(separator=' ', strip=True)
        echa_value = extract_values(text_content)
        print("ECHA Value:", echa_value)
        return echa_value, document_url
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None

def get_toxicity_data(ingredient, driver):
    results, document_url = get_toxicity_data_for_ingredient(driver, ingredient)
    
    if not results:
        words = re.split(r'[\s/]+', ingredient)
        num_threads = max(1, len(words) // 2)
        try:
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = {executor.submit(get_toxicity_data_for_ingredient, driver, ' '.join(words[:i])): i for i in range(len(words), 0, -1)}
                for future in as_completed(futures):
                    result, url = future.result()
                    if result:
                        results = result
                        document_url = url
                        for f in futures:
                            f.cancel()
                        break
        finally:
            pass
    
    return results, document_url

def update_database(start_index, num_ingredients):
    conn = sqlite3.connect('app\data\ingredients.db')
    cursor = conn.cursor()


    cursor.execute("SELECT pcpc_ingredientid, pcpc_ingredientname FROM ingredients LIMIT ? OFFSET ?", (num_ingredients, start_index))
    ingredients = cursor.fetchall()

    driver = initialize_driver()
    total_found = 0
    times = []

    for ingredient_id, ingredient_name in tqdm(ingredients, desc="Updating database"):
        start_time = time.time()
        echa_value, echa_dossier = get_toxicity_data(ingredient_name, driver)
        end_time = time.time()

        time_taken = end_time - start_time
        times.append((ingredient_name, time_taken))
        
        if not echa_value:
            echa_value = "[]"
        else:
            echa_value = json.dumps(echa_value)  
            total_found += 1
        
        cursor.execute("UPDATE ingredients SET echa_value = ?, echa_dossier = ? WHERE pcpc_ingredientid = ?", (echa_value, echa_dossier, ingredient_id))
        conn.commit()
        print(f"Updated ingredient {ingredient_id} with echa_value and echa_dossier")

    driver.quit()
    conn.close()
    print(f"Total ingredients found: {total_found} out of {num_ingredients}")

    indices = list(range(start_index, start_index + len(times)))
    ingredients, durations = zip(*times)
    plt.figure(figsize=(12, 6))
    plt.plot(indices, durations, marker='o', linestyle='-', color='b')
    plt.xlabel('Ingredient Index')
    plt.ylabel('Time (seconds)')
    plt.title('Time Taken to Fetch ECHA Values for Ingredients')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

start_index = 5976
num_ingredients = 100

start_time = time.time()
update_database(start_index, num_ingredients)
end_time = time.time()
print(f"Time taken: {end_time - start_time} seconds")
