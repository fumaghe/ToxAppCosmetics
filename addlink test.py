import sqlite3
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def add_columns_to_db(conn):
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE ingredients ADD COLUMN cir_page TEXT")
    cursor.execute("ALTER TABLE ingredients ADD COLUMN cir_pdf TEXT")
    cursor.execute("ALTER TABLE ingredients ADD COLUMN pubchem_page TEXT")
    conn.commit()

def extract_first_status_link(session, url):
    try:
        response = session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        status_links = soup.find('table').find_all('a')
        if not status_links:
            logging.warning(f"No status links found for URL: {url}")
            return None
        first_link = "https://cir-reports.cir-safety.org/" + status_links[0]['href'].replace("../", "")
        try:
            response = session.get(first_link)
            response.raise_for_status()
            return first_link
        except requests.RequestException as e:
            logging.error(f"Error accessing first status link: {first_link}, {e}")
            if len(status_links) > 1:
                second_link = "https://cir-reports.cir-safety.org/" + status_links[1]['href'].replace("../", "")
                try:
                    response = session.get(second_link)
                    response.raise_for_status()
                    return second_link
                except requests.RequestException as e:
                    logging.error(f"Error accessing second status link: {second_link}, {e}")
                    return None
            else:
                return None
    except requests.RequestException as e:
        logging.error(f"Error retrieving status link from CIR: {e}")
        return None

def get_cir_links(session, ingredient_id):
    cir_page = cir_pdf = None
    url = f"https://cir-reports.cir-safety.org/cir-ingredient-status-report/?id={ingredient_id}"
    status_link = extract_first_status_link(session, url)
    if status_link:
        cir_page = status_link
        cir_pdf = status_link.replace('/full-report', '/full-report.pdf')
    logging.info(f"Found CIR links for ID {ingredient_id}: CIR Page - {cir_page}, CIR PDF - {cir_pdf}")
    return cir_page, cir_pdf

def get_pubchem_link(session, ingredient_name):
    search_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{ingredient_name}/cids/JSON"
    try:
        response = session.get(search_url)
        response.raise_for_status()
        data = response.json()
        cid = data['IdentifierList']['CID'][0]
        pubchem_page = f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"
        logging.info(f"Found PubChem link for {ingredient_name}: {pubchem_page}")
        return pubchem_page
    except requests.RequestException as e:
        logging.error(f"Failed to fetch PubChem CID for {ingredient_name}, Status code: {response.status_code}, Error: {e}")
        return None
    except (KeyError, IndexError):
        logging.warning(f"No CID found for {ingredient_name}")
        return None

def update_ingredient_links(conn, limit=10):
    cursor = conn.cursor()
    cursor.execute("SELECT pcpc_ingredientid, pcpc_ingredientname FROM ingredients LIMIT ?", (limit,))
    ingredients = cursor.fetchall()

    results = []

    retry_strategy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    with requests.Session() as session:
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        for ingredient_id, ingredient_name in tqdm(ingredients, desc="Updating ingredients"):
            cir_page, cir_pdf = get_cir_links(session, ingredient_id)
            pubchem_page = get_pubchem_link(session, ingredient_name)

            cursor.execute("""
                UPDATE ingredients
                SET cir_page = ?, cir_pdf = ?, pubchem_page = ?
                WHERE pcpc_ingredientid = ?
            """, (cir_page, cir_pdf, pubchem_page, ingredient_id))
            
            link_string = f"CIR Page: {cir_page}, CIR PDF: {cir_pdf}, PubChem Page: {pubchem_page}"
            results.append({
                'Ingredient Name': ingredient_name,
                'Links': link_string
            })
    
    conn.commit()
    return results

def save_results_to_txt(results, filename="ingredient_links.txt"):
    with open(filename, "w") as file:
        for result in results:
            file.write(f"Ingredient Name: {result['Ingredient Name']}\n")
            file.write(f"Links: {result['Links']}\n\n")

if __name__ == "__main__":
    # Connect to the original database and create a new database for the updates
    conn_orig = sqlite3.connect('app\data\ingredients.db')
    conn_new = sqlite3.connect('app\data\ingredients2.db')

    # Copy the original database structure and data to the new database
    conn_orig.backup(conn_new)

    # Add new columns to the new database
    add_columns_to_db(conn_new)

    # Update the first 10 ingredients with the new links in the new database
    results = update_ingredient_links(conn_new, limit=10)

    # Close the database connections
    conn_orig.close()
    conn_new.close()

    # Save the results to a text file
    save_results_to_txt(results)

    print("Results saved to ingredient_links.txt")
