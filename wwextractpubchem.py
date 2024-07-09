import time
import requests
import json
import sqlite3
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import re

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Helper functions to retrieve data from PubChem
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

def extract_values_with_context(text, term="LD50"):
    pattern = fr'({term}\s*[:/]?\s*\d+(\.\d+)?\s*[a-zA-Z/]*|(\d+(\.\d+)?\s*mg/kg))'
    matches = re.finditer(pattern, text, re.IGNORECASE)
    values = []
    for match in matches:
        value = match.group(0)
        start_index = match.start()
        words = text[max(0, start_index-100):start_index+100].split()
        context_start = max(0, words.index(value.split()[0]) - 10)
        context_end = min(len(words), context_start + 21)
        context = ' '.join(words[context_start:context_end])
        values.append((value, context))
    return values

def extract_ld50_from_section(section):
    ld50_values = []
    if isinstance(section, dict):
        if 'StringWithMarkup' in section:
            for item in section['StringWithMarkup']:
                ld50_values.extend(extract_values_with_context(item['String']))
        else:
            for key, value in section.items():
                ld50_values.extend(extract_ld50_from_section(value))
    elif isinstance(section, list):
        for item in section:
            ld50_values.extend(extract_ld50_from_section(item))
    return ld50_values

def get_ld50_pubchem(session, cid):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON/"
    try:
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
        sections = data['Record']['Section']
        ld50_values = extract_ld50_from_section(sections)
        return ld50_values if ld50_values else None
    except (requests.RequestException, KeyError, IndexError, ValueError) as e:
        logging.error(f"Error retrieving LD50 from PubChem for CID {cid}: {e}")
        return None

def process_ingredient(session, db_path, ingredient):
    ingredient_name = ingredient[1]
    ingredient_id = ingredient[0]

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT LD50_PubChem FROM ingredients WHERE pcpc_ingredientid=?", (ingredient_id,))
    existing_record = cursor.fetchone()
    if existing_record and existing_record[0] not in [None, '[]']:
        conn.close()
        logging.info(f"Ingredient: {ingredient_name} - LD50 values already present in database")
        return

    result = {
        'pcpc_ingredientid': ingredient_id,
        'pcpc_ingredientname': ingredient_name,
        'LD50_PubChem': []
    }

    name_parts = ingredient_name.split()
    found_values = False
    while name_parts:
        short_name = ' '.join(name_parts)
        logging.info(f"Trying with name: {short_name}")
        cid = get_pubchem_cid(session, short_name)
        if cid:
            ld50_values = get_ld50_pubchem(session, cid)
            if ld50_values:
                result['LD50_PubChem'] = ld50_values
                cursor.execute("UPDATE ingredients SET LD50_PubChem = ? WHERE pcpc_ingredientid = ?",
                               (json.dumps(result['LD50_PubChem']), ingredient_id))
                conn.commit()
                logging.info(f"Ingredient: {ingredient_name} - LD50 values found: {result['LD50_PubChem']}")
                found_values = True
                break
        name_parts.pop()
    
    if not found_values:
        logging.info(f"Ingredient: {ingredient_name} - No CID found or no LD50 values found")
    
    conn.close()

def test_retrieval(db_path, start_index=0, num_ingredients=1000000):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS ingredients
                      (pcpc_ingredientid TEXT PRIMARY KEY,
                       pcpc_ingredientname TEXT,
                       NOAEL_CIR TEXT,
                       LD50_CIR TEXT,
                       LD50_PubChem TEXT,
                       value_updated TEXT,
                       cir_page TEXT,
                       cir_pdf TEXT,
                       pubchem_page TEXT)''')

    cursor.execute("SELECT * FROM ingredients WHERE LD50_PubChem IS NULL OR LD50_PubChem = '[]' LIMIT ? OFFSET ?", (num_ingredients, start_index))
    ingredients = cursor.fetchall()
    conn.close()

    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_ingredient, session, db_path, ingredient) for ingredient in ingredients]
            for future in tqdm(as_completed(futures), desc="Processing ingredients", total=len(futures)):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Error processing ingredient: {e}")

# Path to the database
db_path = 'ingredients.db'

# Running the test
test_retrieval(db_path, start_index=0, num_ingredients=6056)
