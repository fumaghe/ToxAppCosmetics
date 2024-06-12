# -*- coding: utf-8 -*-
"""
FUNZIONA MA BECCA SOLO IL PRIMO
"""

import requests
from bs4 import BeautifulSoup
import re
from collections import Counter
import PyPDF2
import io

def extract_first_status_link(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        status_link = soup.find('table').find_all('tr')[1].find('a')['href']
        full_status_link = "https://cir-reports.cir-safety.org/" + status_link.replace("../", "")
        
        return full_status_link

    except requests.RequestException as e:
        print(f"Error accessing {url}: {e}")
    except (IndexError, TypeError) as e:
        print(f"Error parsing the page: {e}")

def extract_text_from_pdf(pdf_content):
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
    text = ""
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text += page.extract_text() or ""
    return text

def find_noael_values(text):
    # Pattern matching for NOAEL keyword
    pattern = r'NOAEL\s*[:/]?'
    matches = re.finditer(pattern, text, re.IGNORECASE)
    values = []
    for match in matches:
        start_index = match.end()
        words = text[start_index:start_index+100].split()[:12]  # Extracting next 12 words
        value = ' '.join(words)
        values.append(value)
    return values

def find_most_common_noael(values):
    if not values:
        return None
    count = Counter(values)
    most_common = count.most_common(1)[0]
    return most_common

def find_ingredient_id_and_extract_link(ingredient_name, data_file_path):
    with open(data_file_path, 'r', encoding='utf-8') as file:
        ingredients = []
        for line in file:
            data = eval(line.strip())
            search_name = ingredient_name.lower()
            if (search_name in data['pcpc_ingredientname'].lower() or
                search_name in data['pcpc_ciringredientname'].lower()):
                ingredients.append((data['pcpc_ingredientname'], data['pcpc_ingredientid']))

    if ingredients:
        for ingredient_name, ingredient_id in set(ingredients):
            url = f"https://cir-reports.cir-safety.org/cir-ingredient-status-report/?id={ingredient_id}"
            status_link = extract_first_status_link(url)
            if status_link:
                try:
                    response = requests.get(status_link)
                    response.raise_for_status()
                    
                    pdf_text = extract_text_from_pdf(response.content)
                    noael_values = find_noael_values(pdf_text)
                    most_common_noael = find_most_common_noael(noael_values)
                    
                    if most_common_noael:
                        print(f"Ingredient name: {ingredient_name}")
                        print(f"Most common NOAEL value: {most_common_noael[0]} ({most_common_noael[1]} times)")
                    else:
                        print(f"Ingredient name: {ingredient_name}")
                        print("No NOAEL values found.")
                except requests.RequestException as e:
                    print(f"Error accessing attachment {status_link}: {e}")
                except Exception as e:
                    print(f"Error reading PDF {status_link}: {e}")
    else:
        print(f"Ingredient containing '{ingredient_name}' not found in the data file.")

# Example usage
ingredient_name = "Kluyveromyces Extract"
data_file_path = "C:\\Users\\AndreaFumagalli\\OneDrive - ITS Angelo Rizzoli\\Desktop\\Project Work\\JSON DATASET.txt"

find_ingredient_id_and_extract_link(ingredient_name, data_file_path)