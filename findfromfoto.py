import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import sqlite3
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
import logging
import json
import streamlit as st

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\n', ' ')
    return text

def find_values_and_contexts(text, terms):
    results = {}
    text = preprocess_text(text)
    for term in terms:
        pattern = fr'{term}\s*[:;,\(]?\s*(\d*[\d\s\./]*(?:mg/kg|g/kg|ml/kg|µg/kg)?)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        term_results = []
        for match in matches:
            value = match.group(1).strip()
            if value:
                context_start = max(0, match.start() - 100)
                context_end = min(len(text), match.end() + 100)
                context = text[context_start:context_end]
                term_results.append((value, context))
        results[term] = term_results
    return results

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

def get_pdf_for_ingredient(session, ingredient_id):
    url = f"https://cir-reports.cir-safety.org/cir-ingredient-status-report/?id={ingredient_id}"
    pdf_link = extract_first_status_link(session, url)
    if pdf_link:
        response = session.get(pdf_link)
        if response.status_code == 200:
            return io.BytesIO(response.content)
    return None

def process_ingredients_from_csv(selected_ingredients, stop_flag):
    ingredients_df = pd.read_csv('Ingredients_with_missing_values.csv')
    ingredients_df = ingredients_df[ingredients_df['pcpc_ingredientname'].isin(selected_ingredients)]

    conn = sqlite3.connect('app/data/ingredients.db')
    cursor = conn.cursor()

    terms = ["NOAEL", "LD50"]

    session = requests.Session()

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
    total_ingredients = len(ingredients_df)
    progress_text = st.empty()

    updated_ingredients = []

    for i, (index, row) in enumerate(ingredients_df.iterrows()):
        if stop_flag:
            break
        ingredient_name = row['pcpc_ingredientname']
        progress_percentage = (i + 1) / total_ingredients
        progress_bar.progress(progress_percentage)
        progress_text.text(f"Processing {ingredient_name} ({i + 1}/{total_ingredients})")

        cursor.execute("SELECT pcpc_ingredientid, NOAEL_CIR, LD50_CIR FROM ingredients WHERE pcpc_ingredientname=?", (ingredient_name,))
        result = cursor.fetchone()
        if result:
            pcpc_ingredientid, existing_noael, existing_ld50 = result
            logging.info(f"Found pcpc_ingredientid: {pcpc_ingredientid} for ingredient: {ingredient_name}")
        else:
            logging.warning(f"No pcpc_ingredientid found for ingredient: {ingredient_name}")
            continue

        pdf_content = get_pdf_for_ingredient(session, pcpc_ingredientid)
        if not pdf_content:
            logging.warning(f"PDF not found for ingredient: {ingredient_name}")
            continue

        logging.info(f"PDF found and loaded for ingredient: {ingredient_name}")

        pdf = fitz.open(stream=pdf_content, filetype="pdf")

        extracted_text = ""
        for page_num in range(len(pdf)):
            page = pdf.load_page(page_num)
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes()))
            text = pytesseract.image_to_string(img, lang='eng')
            extracted_text += text + "\n\n"

        results = find_values_and_contexts(extracted_text, terms)

        noael_updated = False
        ld50_updated = False

        if "NOAEL" in results and results["NOAEL"]:
            cursor.execute(
                "UPDATE ingredients SET NOAEL_CIR=? WHERE pcpc_ingredientid=?",
                (json.dumps(results["NOAEL"]), pcpc_ingredientid)
            )
            logging.info(f"Updated NOAEL values for ingredient: {ingredient_name}")
            noael_updated = True

        if "LD50" in results and results["LD50"]:
            cursor.execute(
                "UPDATE ingredients SET LD50_CIR=? WHERE pcpc_ingredientid=?",
                (json.dumps(results["LD50"]), pcpc_ingredientid)
            )
            logging.info(f"Updated LD50 values for ingredient: {ingredient_name}")
            ld50_updated = True

        if noael_updated or ld50_updated:
            updated_ingredients.append(ingredient_name)

    conn.commit()
    conn.close()

    if updated_ingredients:
        ingredients_df = ingredients_df[~ingredients_df['pcpc_ingredientname'].isin(updated_ingredients)]
        ingredients_df.to_csv('Ingredients_with_missing_values.csv', index=False)

    progress_text.text("The text has been successfully extracted and saved in the database.")
    logging.info("The text has been successfully extracted and saved in the database.")
