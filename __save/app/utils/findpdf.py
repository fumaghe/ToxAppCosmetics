import sqlite3
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import logging
import streamlit as st

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def get_cir_links(session, ingredient_id):
    cir_page = f"https://cir-reports.cir-safety.org/cir-ingredient-status-report/?id={ingredient_id}"
    cir_pdf = extract_first_status_link(session, cir_page)
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
        logging.error(f"Failed to fetch PubChem CID for {ingredient_name}, Error: {e}")
        return None
    except (KeyError, IndexError):
        logging.warning(f"No CID found for {ingredient_name}")
        return None

def search_ingredients(start_index, end_index, stop_flag):
    conn = sqlite3.connect('app/data/ingredients.db')
    cursor = conn.cursor()
    cursor.execute("SELECT pcpc_ingredientid, pcpc_ingredientname FROM ingredients")
    ingredients = cursor.fetchall()
    ingredients = ingredients[start_index:end_index]

    retry_strategy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # CSS per personalizzare la barra di avanzamento
    st.markdown(
        """
        <style>
        .stProgress > div > div > div > div {
            background-color: red;
        }
        </style>
        """, 
        unsafe_allow_html=True
    )

    progress_bar = st.progress(0)
    total_ingredients = len(ingredients)
    progress_text = st.empty()

    for i, (ingredient_id, ingredient_name) in enumerate(ingredients):
        if stop_flag:
            break
        progress_percentage = (i + 1) / total_ingredients
        progress_bar.progress(progress_percentage)
        progress_text.text(f"Processing {ingredient_name} ({i + 1}/{total_ingredients})")

        try:
            logging.info(f"Processing ingredient: {ingredient_name}")

            cir_page, cir_pdf = get_cir_links(session, ingredient_id)
            logging.info(f"Found CIR links for {ingredient_name}: CIR Page - {cir_page}, CIR PDF - {cir_pdf}")

            pubchem_page = get_pubchem_link(session, ingredient_name)
            logging.info(f"Found PubChem link for {ingredient_name}: {pubchem_page}")

            logging.info(f"Updating ingredient: {ingredient_name} with CIR Page - {cir_page}, CIR PDF - {cir_pdf}, PubChem Page - {pubchem_page}")

            cursor.execute(
                "UPDATE ingredients SET cir_page=?, cir_pdf=?, pubchem_page=? WHERE pcpc_ingredientid=?",
                (cir_page, cir_pdf, pubchem_page, ingredient_id)
            )
            conn.commit()

            cursor.execute("SELECT cir_page, cir_pdf, pubchem_page FROM ingredients WHERE pcpc_ingredientid=?", (ingredient_id,))
            updated_values = cursor.fetchone()
            logging.info(f"Verification for {ingredient_name} - CIR Page: {updated_values[0]}, CIR PDF: {updated_values[1]}, PubChem Page: {updated_values[2]}")

        except Exception as e:
            logging.error(f"An error occurred while processing ingredient {ingredient_name}: {e}")

    conn.close()
    progress_text.text("The PDF links have been successfully updated in the database.")
    logging.info("The PDF links have been successfully updated in the database.")
