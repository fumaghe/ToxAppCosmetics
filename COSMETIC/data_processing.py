import requests
from bs4 import BeautifulSoup
import re
import PyPDF2
import io
import os
import streamlit as st
from collections import Counter

def extract_first_status_link(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        status_link = soup.find('table').find_all('tr')[1].find('a')['href']
        full_status_link = "https://cir-reports.cir-safety.org/" + status_link.replace("../", "")
        return full_status_link
    except requests.RequestException as e:
        st.error(f"Error accessing {url}: {e}")
    except (IndexError, TypeError) as e:
        st.error(f"Error parsing the page: {e}")

def extract_text_from_pdf(pdf_content):
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
    text = ""
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text += page.extract_text() or ""
    return text

def find_values(text, term):
    pattern = fr'{term}\s*[:/]?'
    matches = re.finditer(pattern, text, re.IGNORECASE)
    values = []
    for match in matches:
        start_index = match.end()
        words = text[start_index:start_index+100].split()[:20]
        for word in words:
            if re.match(r'\d+(\.\d+)?', word):
                values.append(word)
                break
    return values

def find_most_common_value(values):
    if not values:
        return None, 0
    count = Counter(values)
    most_common_value, most_common_count = count.most_common(1)[0]
    return most_common_value, most_common_count

def check_and_append_values(ingredient_id, term, most_common_value, other_values, values_file_path):
    with open(values_file_path, 'a', encoding='utf-8') as file:
        file.write(f"{ingredient_id}:most_common_{term}:{most_common_value}\n")
        if other_values:
            file.write(f"{ingredient_id}:other_{term}:{','.join(map(str, other_values))}\n")

def find_ingredient_id_and_extract_link(ingredient_name, data_file_path, values_file_path):
    values_dict = {}
    
    if os.path.exists(values_file_path):
        with open(values_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if ':' in line:
                    id_value_pair = line.strip().split(':')
                    if len(id_value_pair) == 3:
                        id_key = id_value_pair[0]
                        if id_key not in values_dict:
                            values_dict[id_key] = {}
                        values_dict[id_key][id_value_pair[1]] = id_value_pair[2].split(',')
                    
    with open(data_file_path, 'r', encoding='utf-8') as file:
        ingredients = []
        for line in file:
            data = eval(line.strip())
            if data['pcpc_ingredientname'] == ingredient_name or data['pcpc_ciringredientname'] == ingredient_name:
                ingredient_id = data['pcpc_ingredientid']
                status_link = extract_first_status_link(data['link'])
                if status_link:
                    try:
                        pdf_response = requests.get(status_link)
                        pdf_response.raise_for_status()
                        pdf_content = pdf_response.content
                        pdf_text = extract_text_from_pdf(pdf_content)
                        for term in ['NOAEL', 'LD50']:
                            if ingredient_id in values_dict and f"most_common_{term.lower()}" in values_dict[ingredient_id]:
                                most_common_value = values_dict[ingredient_id][f"most_common_{term.lower()}"][0]
                                other_values = values_dict[ingredient_id].get(f"other_{term.lower()}", [])
                            else:
                                values = find_values(pdf_text, term)
                                most_common_value, most_common_count = find_most_common_value(values)
                                other_values = [value for value in values if value != most_common_value]
                                check_and_append_values(ingredient_id, term.lower(), most_common_value, other_values, values_file_path)
                            st.write(f"Most common {term} value for {ingredient_name}: {most_common_value} ({most_common_count} times)")
                            if other_values:
                                st.write(f"Other {term} values for {ingredient_name}: {', '.join(other_values)}")
                    except requests.RequestException as e:
                        st.error(f"Error accessing {status_link}: {e}")
                else:
                    st.error(f"Status link not found for {ingredient_name}")
                break
        else:
            st.error(f"Ingredient '{ingredient_name}' not found in the dataset.")

def load_ingredient_list(data_file_path):
    ingredient_list = []
    with open(data_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            data = eval(line.strip())
            ingredient_list.append(data['pcpc_ingredientname'])
    return ingredient_list

def update_database():
    try:
        if os.path.exists('output_table.csv'):
            st.write('Deleting existing output_table.csv')
            os.remove('output_table.csv')

        data_file_path = 'C:\Users\AndreaFumagalli\OneDrive - ITS Angelo Rizzoli\Documenti\GitHub\ProjectWork\COSMETIC\DATASET.txt'
        ingredients = []

        with open(data_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                data = eval(line.strip())
                ingredients.append({'pcpc_ingredientname': data['pcpc_ingredientname'], 'link': data['link']})

        df = pd.DataFrame(ingredients)
        df.to_csv('output_table.csv', index=False)
        st.write('output_table.csv updated successfully')
    except Exception as e:
        st.error(f'Error updating database: {e}')
