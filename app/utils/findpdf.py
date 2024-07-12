import sqlite3
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import logging
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_session():
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
    return session

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

def process_ingredient(session, ingredient):
    ingredient_id, ingredient_name, cir_page_existing, cir_pdf_existing = ingredient
    if cir_page_existing and cir_pdf_existing:
        logging.info(f"Skipping {ingredient_name}, CIR links already present.")
        return ingredient_id, None, None 

    try:
        cir_page, cir_pdf = get_cir_links(session, ingredient_id)
        return ingredient_id, cir_page, cir_pdf
    except Exception as e:
        logging.error(f"An error occurred while processing ingredient {ingredient_name}: {e}")
        return ingredient_id, None, None

def update_database(batch_updates):
    with sqlite3.connect('app/data/ingredients.db') as conn:
        cursor = conn.cursor()
        cursor.executemany(
            "UPDATE ingredients SET cir_page=?, cir_pdf=? WHERE pcpc_ingredientid=?",
            batch_updates
        )
        conn.commit()

def search_ingredients(start_index, end_index, stop_flag):
    with sqlite3.connect('app/data/ingredients.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT pcpc_ingredientid, pcpc_ingredientname, cir_page, cir_pdf FROM ingredients")
        ingredients = cursor.fetchall()[start_index:end_index]

    session = create_session()

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

    batch_size = 10
    batch_updates = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ingredient = {executor.submit(process_ingredient, session, ingredient): ingredient for ingredient in ingredients}
        for i, future in enumerate(as_completed(future_to_ingredient)):
            if stop_flag:
                break

            ingredient_id, cir_page, cir_pdf = future.result()

            if cir_page or cir_pdf:
                batch_updates.append((cir_page, cir_pdf, ingredient_id))

            if len(batch_updates) >= batch_size:
                update_database(batch_updates)
                batch_updates = []

            progress_percentage = (i + 1) / total_ingredients
            progress_bar.progress(progress_percentage)
            progress_text.text(f"Processing {future_to_ingredient[future][1]} ({i + 1}/{total_ingredients})")

    if batch_updates:
        update_database(batch_updates)

    progress_text.text("The PDF links have been successfully updated in the database.")
    logging.info("The PDF links have been successfully updated in the database.")
