import time
import requests
import json
import sqlite3
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def process_ingredient(session, db_path, ingredient):
    ingredient_name = ingredient[1]
    ingredient_id = ingredient[0]

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT pubchem_page FROM ingredients WHERE pcpc_ingredientid=?", (ingredient_id,))
    existing_record = cursor.fetchone()
    if existing_record and existing_record[0]:
        conn.close()
        logging.info(f"Ingredient: {ingredient_name} - PubChem page already present in database")
        return

    result = {
        'pcpc_ingredientid': ingredient_id,
        'pcpc_ingredientname': ingredient_name,
        'pubchem_page': ''
    }

    name_parts = ingredient_name.split()
    found_cid = False
    while name_parts:
        short_name = ' '.join(name_parts)
        logging.info(f"Trying with name: {short_name}")
        cid = get_pubchem_cid(session, short_name)
        if cid:
            result['pubchem_page'] = f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"
            cursor.execute("UPDATE ingredients SET pubchem_page = ? WHERE pcpc_ingredientid = ?",
                           (result['pubchem_page'], ingredient_id))
            conn.commit()
            logging.info(f"Ingredient: {ingredient_name} - PubChem page found: {result['pubchem_page']}")
            found_cid = True
            break
        name_parts.pop()
    
    if not found_cid:
        logging.info(f"Ingredient: {ingredient_name} - No CID found")
    
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

    cursor.execute("SELECT * FROM ingredients WHERE pubchem_page IS NULL OR pubchem_page = '' LIMIT ? OFFSET ?", (num_ingredients, start_index))
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

db_path = 'ingredients.db'

test_retrieval(db_path, start_index=1000, num_ingredients=50)
