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

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Specifica il percorso all'eseguibile di Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Funzione per normalizzare il testo
def preprocess_text(text):
    text = re.sub(r'\s+', ' ', text)  # Sostituisce spazi multipli con uno singolo
    text = text.replace('\n', ' ')    # Rimuove le nuove righe
    return text

# Funzione per trovare valori e contesti nel testo
def find_values_and_contexts(text, terms):
    results = {}
    text = preprocess_text(text)  # Normalizza il testo
    for term in terms:
        pattern = fr'{term}\s*[:;,\(]?\s*\d*[\d\s\./]*(?:mg/kg|g/kg|ml/kg|µg/kg)?'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        term_results = []
        for match in matches:
            value = match.group().strip()
            context_start = max(0, match.start() - 100)
            context_end = min(len(text), match.end() + 100)
            context = text[context_start:context_end]
            term_results.append((value, context))
        results[term] = term_results
    return results

# Funzione per cercare e caricare il PDF specifico per ogni ingrediente
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

# Funzione per ottenere il PDF specifico per ogni ingrediente
def get_pdf_for_ingredient(session, ingredient_id):
    url = f"https://cir-reports.cir-safety.org/cir-ingredient-status-report/?id={ingredient_id}"
    pdf_link = extract_first_status_link(session, url)
    if pdf_link:
        response = session.get(pdf_link)
        if response.status_code == 200:
            return io.BytesIO(response.content)
    return None

# Leggi i primi 150 ingredienti dal file CSV
ingredients_df = pd.read_csv('Ingredients_with_missing_values.csv').head(3)

# Connetti al database
conn = sqlite3.connect('ingredients.db')
cursor = conn.cursor()

# Lista di termini da cercare
terms = ["NOAEL", "LD50"]

# Sessione di richieste
session = requests.Session()

# Loop attraverso i primi 150 ingredienti
for index, row in ingredients_df.iterrows():
    ingredient_name = row['pcpc_ingredientname']
    logging.info(f"Processing ingredient: {ingredient_name}")

    # Recupera il pcpc_ingredientid dal database
    cursor.execute("SELECT pcpc_ingredientid, NOAEL_CIR, LD50_CIR FROM ingredients WHERE pcpc_ingredientname=?", (ingredient_name,))
    result = cursor.fetchone()
    if result:
        pcpc_ingredientid, existing_noael, existing_ld50 = result
        logging.info(f"Found pcpc_ingredientid: {pcpc_ingredientid} for ingredient: {ingredient_name}")
    else:
        logging.warning(f"No pcpc_ingredientid found for ingredient: {ingredient_name}")
        continue

    # Salta se i valori sono già presenti
    if existing_noael and existing_ld50:
        logging.info(f"Values already exist for ingredient: {ingredient_name}. Skipping...")
        continue

    # Cerca e carica il PDF specifico per l'ingrediente
    pdf_content = get_pdf_for_ingredient(session, pcpc_ingredientid)
    if not pdf_content:
        logging.warning(f"PDF not found for ingredient: {ingredient_name}")
        continue

    logging.info(f"PDF found and loaded for ingredient: {ingredient_name}")

    # Apri il PDF
    pdf = fitz.open(stream=pdf_content, filetype="pdf")

    extracted_text = ""
    for page_num in range(len(pdf)):
        page = pdf.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes()))
        text = pytesseract.image_to_string(img, lang='eng')
        extracted_text += text + "\n\n"

    results = find_values_and_contexts(extracted_text, terms)

    # Aggiorna i valori esistenti con i nuovi valori trovati
    if "NOAEL" in results and results["NOAEL"]:
        updated_noael = json.loads(existing_noael) if existing_noael else []
        updated_noael.extend(results["NOAEL"])
        cursor.execute(
            "UPDATE ingredients SET NOAEL_CIR=? WHERE pcpc_ingredientid=?",
            (json.dumps(updated_noael), pcpc_ingredientid)
        )
        logging.info(f"Updated NOAEL values for ingredient: {ingredient_name}")

    if "LD50" in results and results["LD50"]:
        updated_ld50 = json.loads(existing_ld50) if existing_ld50 else []
        updated_ld50.extend(results["LD50"])
        cursor.execute(
            "UPDATE ingredients SET LD50_CIR=? WHERE pcpc_ingredientid=?",
            (json.dumps(updated_ld50), pcpc_ingredientid)
        )
        logging.info(f"Updated LD50 values for ingredient: {ingredient_name}")

# Commit delle modifiche e chiudi la connessione
conn.commit()
conn.close()

logging.info("Il testo è stato estrapolato con successo e salvato nel database.")
