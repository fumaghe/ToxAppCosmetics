import time
import requests
import re
import json
from bs4 import BeautifulSoup
import PyPDF2
import io
from tqdm import tqdm
import sqlite3
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib.pyplot as plt
import pandas as pd

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Helper functions to retrieve data from CIR and PubChem
def get_pubchem_cid(session, ingredient_name):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{ingredient_name}/cids/JSON"
    try:
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
        cid = str(data['IdentifierList']['CID'][0])
        return cid
    except (requests.RequestException, KeyError, IndexError, ValueError) as e:
        logging.error(f"Error retrieving PubChem CID for {ingredient_name}: {e}")
        return None

def get_ld50_pubchem(session, cid):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON/"
    try:
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
        sections = data['Record']['Section']
        ld50_values = []
        def extract_ld50(sections):
            for section in sections:
                if 'Section' in section:
                    extract_ld50(section['Section'])
                if 'Information' in section:
                    for info in section['Information']:
                        if 'Value' in info and 'StringWithMarkup' in info['Value']:
                            for item in info['Value']['StringWithMarkup']:
                                if 'LD50' in item['String']:
                                    ld50_values.append(item['String'])
        extract_ld50(sections)
        return ld50_values if ld50_values else None
    except (requests.RequestException, KeyError, IndexError, ValueError) as e:
        logging.error(f"Error retrieving LD50 from PubChem for CID {cid}: {e}")
        return None

def extract_first_status_link(session, url):
    try:
        response = session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        status_links = soup.find('table').find_all('a')
        if not status_links:
            return None
        first_link = "https://cir-reports.cir-safety.org/" + status_links[0]['href'].replace("../", "")
        try:
            response = session.get(first_link)
            response.raise_for_status()
            return first_link
        except requests.RequestException:
            if len(status_links) > 1:
                second_link = "https://cir-reports.cir-safety.org/" + status_links[1]['href'].replace("../", "")
                try:
                    response = session.get(second_link)
                    response.raise_for_status()
                    return second_link
                except requests.RequestException:
                    return None
            else:
                return None
    except requests.RequestException as e:
        logging.error(f"Error retrieving status link from CIR: {e}")
        return None

def extract_text_from_pdf(pdf_content):
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
    text = ""
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text += page.extract_text() or ""
    return text

def find_values(text, term):
    pattern = fr'{term}\s*[:/]?'
    if term == "LD50":
        pattern = fr'LD\s*[\n]*50\s*[:/]?'
    matches = re.finditer(pattern, text, re.IGNORECASE)
    values = []
    for match in matches:
        start_index = match.end()
        words = text[start_index:start_index+100].split()[:20]  # Estendi a 20 parole per catturare il valore e l'unità
        for i in range(len(words)):
            if re.match(r'\d+(\.\d+)?', words[i]):  # Cattura il valore numerico
                if i + 1 < len(words) and re.match(r'[a-zA-Z/]+', words[i + 1]):  # Cattura l'unità di misura
                    value = f"{words[i]} {words[i + 1]}"
                    values.append((value, start_index))
                    break
                else:
                    values.append((words[i], start_index))
                    break
    return values

def save_context(text, values):
    contexts = []
    for value, start_index in values:
        text_before = text[:start_index].split()[-10:]
        text_after = text[start_index:].split()[:10]
        context = ' '.join(text_before + [f"{value}"] + text_after)
        contexts.append(context)
    return contexts

def process_ingredient(session, db_path, ingredient):
    ingredient_name = ingredient['pcpc_ingredientname']
    ingredient_id = ingredient['pcpc_ingredientid']

    # Open a new SQLite connection in each thread
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if ingredient is already in the database
    cursor.execute("SELECT * FROM ingredients WHERE pcpc_ingredientid=?", (ingredient_id,))
    existing_record = cursor.fetchone()
    if existing_record:
        conn.close()
        return {
            'pcpc_ingredientid': ingredient_id,
            'pcpc_ingredientname': ingredient_name,
            'NOAEL_CIR': json.loads(existing_record[2]),
            'LD50_CIR': json.loads(existing_record[3]),
            'LD50_PubChem': json.loads(existing_record[4])
        }, 0, 0, bool(existing_record[2]), bool(existing_record[4])

    result = {
        'pcpc_ingredientid': ingredient_id,
        'pcpc_ingredientname': ingredient_name,
        'NOAEL_CIR': [],
        'LD50_CIR': [],
        'LD50_PubChem': []
    }

    # Search in CIR
    start_time_cir = time.time()
    url = f"https://cir-reports.cir-safety.org/cir-ingredient-status-report/?id={ingredient_id}"
    status_link = extract_first_status_link(session, url)
    cir_values_found = False
    if status_link:
        try:
            response = session.get(status_link)
            response.raise_for_status()
            pdf_text = extract_text_from_pdf(response.content)
            noael_values = find_values(pdf_text, 'NOAEL')
            ld50_values = find_values(pdf_text, 'LD50')
            if noael_values:
                result['NOAEL_CIR'] = [(v[0], save_context(pdf_text, [v])) for v in noael_values]
                cir_values_found = True
            if ld50_values:
                result['LD50_CIR'] = [(v[0], save_context(pdf_text, [v])) for v in ld50_values]
                cir_values_found = True
        except Exception as e:
            logging.error(f"Error processing CIR data for {ingredient_name}: {e}")
    end_time_cir = time.time() - start_time_cir

    # Search in PubChem
    start_time_pubchem = time.time()
    cid = get_pubchem_cid(session, ingredient_name)
    pubchem_values_found = False
    if cid:
        ld50_values = get_ld50_pubchem(session, cid)
        if ld50_values:
            result['LD50_PubChem'] = [(v, []) for v in ld50_values]
            pubchem_values_found = True
    end_time_pubchem = time.time() - start_time_pubchem

    # Save the result to SQLite
    cursor.execute("INSERT INTO ingredients (pcpc_ingredientid, pcpc_ingredientname, NOAEL_CIR, LD50_CIR, LD50_PubChem) VALUES (?, ?, ?, ?, ?)",
                   (ingredient_id, ingredient_name, json.dumps(result['NOAEL_CIR']), json.dumps(result['LD50_CIR']), json.dumps(result['LD50_PubChem'])))
    conn.commit()
    conn.close()

    return result, end_time_cir, end_time_pubchem, cir_values_found, pubchem_values_found

# Main testing function
def test_retrieval(data_file_path, db_path, start_index=3000, num_ingredients=1000000):
    with open(data_file_path, 'r', encoding='utf-8') as file:
        ingredients = [eval(line.strip()) for line in file]

    ingredients = ingredients[start_index:]
    total_ingredients = len(ingredients)
    cir_found = 0
    pubchem_found = 0
    both_found = 0
    neither_found = 0
    cir_search_times = []
    pubchem_search_times = []
    results = []
    not_found = []

    # Create the SQLite database and table if not exists
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS ingredients
                      (pcpc_ingredientid TEXT PRIMARY KEY,
                       pcpc_ingredientname TEXT,
                       NOAEL_CIR TEXT,
                       LD50_CIR TEXT,
                       LD50_PubChem TEXT)''')
    conn.close()

    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=5) as executor:  # Riduci il numero di thread
            futures = [executor.submit(process_ingredient, session, db_path, ingredient) for ingredient in ingredients]
            for future in tqdm(as_completed(futures), desc="Processing ingredients", total=len(futures)):
                try:
                    result, end_time_cir, end_time_pubchem, cir_values_found, pubchem_values_found = future.result()
                    results.append(result)
                    cir_search_times.append(end_time_cir)
                    pubchem_search_times.append(end_time_pubchem)
                    if cir_values_found:
                        cir_found += 1
                    if pubchem_values_found:
                        pubchem_found += 1
                    if cir_values_found and pubchem_values_found:
                        both_found += 1
                    if not cir_values_found and not pubchem_values_found:
                        neither_found += 1
                        not_found.append(result['pcpc_ingredientname'])
                except Exception as e:
                    logging.error(f"Error processing ingredient: {e}")

    # Summary statistics
    total_time_cir = sum(cir_search_times)
    total_time_pubchem = sum(pubchem_search_times)
    accuracy_output = (
        f"CIR found: {cir_found}/{total_ingredients} in {total_time_cir:.2f} seconds\n"
        f"PubChem found: {pubchem_found}/{total_ingredients} in {total_time_pubchem:.2f} seconds\n"
        f"Both found: {both_found}/{total_ingredients}\n"
        f"Neither found: {neither_found}/{total_ingredients}\n"
        f"At least one found: {total_ingredients - neither_found}/{total_ingredients}\n"
    )

    with open("ACCURACY.txt", "w") as accuracy_file:
        accuracy_file.write(accuracy_output)

    with open("NOTFOUND.txt", "w") as notfound_file:
        for ingredient in not_found:
            notfound_file.write(f"{ingredient}\n")

    # Plotting search times
    plot_search_times(cir_search_times, pubchem_search_times)

def plot_search_times(cir_search_times, pubchem_search_times):
    plt.figure(figsize=(12, 6))
    
    # Combine both search times and label them
    search_times = cir_search_times + pubchem_search_times
    labels = ['CIR'] * len(cir_search_times) + ['PubChem'] * len(pubchem_search_times)
    
    # Create DataFrame
    df = pd.DataFrame({'Search Times (s)': search_times, 'Source': labels})

    # Plot histogram
    for source in df['Source'].unique():
        subset = df[df['Source'] == source]
        plt.hist(subset['Search Times (s)'], bins=30, alpha=0.5, label=source)

    plt.xlabel('Time (seconds)')
    plt.ylabel('Frequency')
    plt.title('Distribution of Search Times for CIR and PubChem')
    plt.legend(loc='upper right')
    plt.grid(True)
    plt.savefig('search_times_distribution.png')

# Paths to the data files
data_file_path = 'DATASET.txt'
db_path = 'ingredients.db'

# Running the test
test_retrieval(data_file_path, db_path, start_index=3000, num_ingredients=1000000)
