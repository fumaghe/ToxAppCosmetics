import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from collections import Counter
import PyPDF2
import io
import os
import json
import webbrowser

# Set the page configuration
st.set_page_config(layout="wide", page_title="CosmeticToxicity", page_icon="🧴")

def extract_first_status_link(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        status_links = soup.find('table').find_all('a')

        if not status_links:
            st.error("No links found on the page.")
            return None
        
        # Extract the first link
        first_link = "https://cir-reports.cir-safety.org/" + status_links[0]['href'].replace("../", "")
        
        # Try the first link
        try:
            response = requests.get(first_link)
            response.raise_for_status()
            return first_link
        except requests.RequestException:
            # If the first link fails, check if there's a second link
            if len(status_links) > 1:
                second_link = "https://cir-reports.cir-safety.org/" + status_links[1]['href'].replace("../", "")
                try:
                    response = requests.get(second_link)
                    response.raise_for_status()
                    return second_link
                except requests.RequestException as e:
                    st.error(f"Error accessing both links: {e}")
                    return None
            else:
                st.error("Error accessing the first link and no second link available.")
                return None

    except requests.RequestException as e:
        st.error(f"Error accessing {url}: {e}")
    except (IndexError, TypeError) as e:
        st.error(f"Error parsing the page: {e}")
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
        pattern = fr'LD\s*[\n]*50\s*[:/]?'  # Gestisce i newline tra LD e 50
    
    matches = re.finditer(pattern, text, re.IGNORECASE)
    values = []
    for match in matches:
        start_index = match.end()
        words = text[start_index:start_index+100].split()[:20]  # Estrae 20 parole dopo il match
        for word in words:
            if re.match(r'\d+(\.\d+)?', word):  # Trova il valore numerico
                values.append((word, start_index))  # Aggiunge il valore e l'indice di inizio
                break
    return values

def display_values(common_values, pdf_text):
    if not common_values:
        st.write("No values found.")
        return

    for value, occurrences in common_values:
        with st.expander(f"Value: {value} mg/kg"):
            for i, (_, start_index) in enumerate(occurrences, 1):
                text_before = pdf_text[:start_index].split()[-20:]
                text_after = pdf_text[start_index:].split()[:20]
                surrounding_text = ' '.join(text_before + [f"<span style='color:red; font-weight:bold;'>{value}</span>"] + text_after)
                st.write(f"Occurrence {i}:")
                st.markdown(f"...{surrounding_text}...", unsafe_allow_html=True)



def find_most_common_values(values):
    if not values:
        return []
    count = Counter([v for v, _ in values])
    most_common = count.most_common(3)  # Ottiene i 3 più comuni
    common_values = []
    for value, _ in most_common:
        occurrences = [(v, idx) for v, idx in values if v == value]
        contexts = [(value, idx) for value, idx in occurrences]
        common_values.append((value, contexts))
    return common_values

def check_and_append_values(ingredient_id, term, most_common_value, other_values, values_file_path):
    values_dict = {}
    
    # Carica i dati esistenti
    if os.path.exists(values_file_path):
        with open(values_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if ':' in line:
                    id_value_pair = line.strip().split(':')
                    if len(id_value_pair) == 4:
                        id_key = id_value_pair[0]
                        if id_key not in values_dict:
                            values_dict[id_key] = {}
                        if id_value_pair[1] not in values_dict[id_key]:
                            values_dict[id_key][id_value_pair[1]] = []
                        try:
                            contexts = json.loads(id_value_pair[3])
                        except json.JSONDecodeError:
                            contexts = []
                        values_dict[id_key][id_value_pair[1]].append((id_value_pair[2], contexts))

    # Aggiungi i nuovi valori e contesti
    if ingredient_id not in values_dict:
        values_dict[ingredient_id] = {}
    values_dict[ingredient_id][f"most_common_{term}"] = [most_common_value]
    values_dict[ingredient_id][f"other_{term}"] = other_values

    # Salva nuovamente tutti i dati
    with open(values_file_path, 'w', encoding='utf-8') as file:
        for id_key, terms in values_dict.items():
            for term_key, values in terms.items():
                for value, contexts in values:
                    file.write(f"{id_key}:{term_key}:{value}:{json.dumps(contexts)}\n")


def display_saved_values(values, ingredient_id, term, values_file_path, selections_file):
    if not values:
        st.write("No values found.")
        return

    saved_selections = load_selected_values(ingredient_id, term, selections_file)

    for value, contexts in values:
        is_selected = st.checkbox(f"Value: {value} mg/kg", value=(value in saved_selections), key=f"{ingredient_id}_{term}_{value}")
        if is_selected and value not in saved_selections:
            saved_selections.append(value)
        elif not is_selected and value in saved_selections:
            saved_selections.remove(value)

        with st.expander("Context"):
            for context in contexts:
                highlighted_context = context.replace(value, f"<span style='color:red; font-weight:bold;'>{value}</span>")
                st.markdown(highlighted_context, unsafe_allow_html=True)

    save_selected_values(ingredient_id, term, saved_selections, selections_file)


def load_selected_values(ingredient_id, term, selections_file):
    if os.path.exists(selections_file):
        with open(selections_file, 'r', encoding='utf-8') as file:
            all_selections = json.load(file)
        return all_selections.get(f"{ingredient_id}_{term}", [])
    return []

def save_selected_values(ingredient_id, term, selected_values, selections_file):
    if os.path.exists(selections_file):
        with open(selections_file, 'r', encoding='utf-8') as file:
            all_selections = json.load(file)
    else:
        all_selections = {}

    all_selections[f"{ingredient_id}_{term}"] = selected_values

    with open(selections_file, 'w', encoding='utf-8') as file:
        json.dump(all_selections, file)


def save_selected_values(ingredient_id, term, selected_values, values_file_path):
    selections_file = f"{values_file_path}_selections.json"
    if os.path.exists(selections_file):
        with open(selections_file, 'r', encoding='utf-8') as file:
            all_selections = json.load(file)
    else:
        all_selections = {}

    all_selections[f"{ingredient_id}_{term}"] = selected_values

    with open(selections_file, 'w', encoding='utf-8') as file:
        json.dump(all_selections, file)

def load_selected_values(ingredient_id, term, values_file_path):
    selections_file = f"{values_file_path}_selections.json"
    if os.path.exists(selections_file):
        with open(selections_file, 'r', encoding='utf-8') as file:
            all_selections = json.load(file)
        return all_selections.get(f"{ingredient_id}_{term}", [])
    return []

def find_ingredient_id_and_extract_link(ingredient_name, data_file_path, values_file_path):
    selections_file = f"{values_file_path}_selections.json"
    values_dict = {}
    
    # Carica i dati esistenti
    if os.path.exists(values_file_path):
        with open(values_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if ':' in line:
                    id_value_pair = line.strip().split(':')
                    if len(id_value_pair) == 4:
                        id_key = id_value_pair[0]
                        if id_key not in values_dict:
                            values_dict[id_key] = {}
                        if id_value_pair[1] not in values_dict[id_key]:
                            values_dict[id_key][id_value_pair[1]] = []
                        try:
                            contexts = json.loads(id_value_pair[3])
                        except json.JSONDecodeError:
                            contexts = []
                        values_dict[id_key][id_value_pair[1]].append((id_value_pair[2], contexts))

    # Cerca l'ingrediente
    with open(data_file_path, 'r', encoding='utf-8') as file:
        ingredients = []
        for line in file:
            data = eval(line.strip())
            search_name = ingredient_name.lower()
            if (search_name in data['pcpc_ingredientname'].lower() or search_name in data['pcpc_ciringredientname'].lower()):
                ingredients.append((data['pcpc_ingredientname'], data['pcpc_ingredientid']))

    if ingredients:
        for ingredient_name, ingredient_id in set(ingredients):
            st.markdown(f"<h3 style='text-align: left; font-size: 20px;'>Ingredient name: {ingredient_name}</h3>", unsafe_allow_html=True)
            if ingredient_id in values_dict:
                most_common_noael = values_dict[ingredient_id].get('most_common_NOAEL', [['N/A', []]])[0]
                other_noael_values = values_dict[ingredient_id].get('other_NOAEL', [])
                most_common_ld50 = values_dict[ingredient_id].get('most_common_LD50', [['N/A', []]])[0]
                other_ld50_values = values_dict[ingredient_id].get('other_LD50', [])
                selected_noael = most_common_noael[0] if most_common_noael[0] != 'N/A' else None
                selected_ld50 = most_common_ld50[0] if most_common_ld50[0] != 'N/A' else None

                if most_common_noael[0] != 'N/A':
                    st.markdown(f"**Most common NOAEL:** {most_common_noael[0]} mg/kg")
                    with st.expander("Most common NOAEL context"):
                        for context in most_common_noael[1]:
                            st.write(context)
                    if other_noael_values:
                        st.markdown("**Other NOAEL values:**")
                        display_saved_values(other_noael_values, ingredient_id, 'NOAEL', values_file_path, selections_file)
                elif most_common_ld50[0] != 'N/A':
                    st.markdown(f"**Most common LD50:** {most_common_ld50[0]} mg/kg")
                    with st.expander("Most common LD50 context"):
                        for context in most_common_ld50[1]:
                            st.write(context)
                    if other_ld50_values:
                        st.markdown("**Other LD50 values:**")
                        display_saved_values(other_ld50_values, ingredient_id, 'LD50', values_file_path, selections_file)
                else:
                    st.write("No NOAEL or LD50 values found.")
            else:
                url = f"https://cir-reports.cir-safety.org/cir-ingredient-status-report/?id={ingredient_id}"
                status_link = extract_first_status_link(url)
                if status_link:
                    try:
                        response = requests.get(status_link)
                        response.raise_for_status()
                        pdf_text = extract_text_from_pdf(response.content)
                        
                        noael_values = find_values(pdf_text, 'NOAEL')
                        if noael_values:
                            most_common_noael_values = find_most_common_values(noael_values)
                            st.markdown(f"**Most common NOAEL:** {most_common_noael_values[0][0]} mg/kg")
                            st.write(f"[Link to PDF]({status_link})")
                            display_values([most_common_noael_values[0]], pdf_text)

                            if len(most_common_noael_values) > 1:
                                st.markdown("**Other NOAEL values:**")
                                for value, occurrences in most_common_noael_values[1:]:
                                    st.markdown(f"<small>{value} mg/kg</small>", unsafe_allow_html=True)
                                    display_values([(value, occurrences)], pdf_text)

                            check_and_append_values(ingredient_id, 'NOAEL', (most_common_noael_values[0][0], [pdf_text[max(0, idx - 200):idx + 200] for _, idx in most_common_noael_values[0][1]]), [(v, [pdf_text[max(0, idx - 200):idx + 200] for _, idx in occurrences]) for v, occurrences in most_common_noael_values[1:]], values_file_path)
                        else:
                            ld50_values = find_values(pdf_text, 'LD50')
                            if ld50_values:
                                most_common_ld50_values = find_most_common_values(ld50_values)
                                st.markdown(f"**Most common LD50:** {most_common_ld50_values[0][0]} mg/kg")
                                st.write(f"[Link to PDF]({status_link})")
                                display_values([most_common_ld50_values[0]], pdf_text)

                                if len(most_common_ld50_values) > 1:
                                    st.markdown("**Other LD50 values:**")
                                    for value, occurrences in most_common_ld50_values[1:]:
                                        st.markdown(f"<small>{value} mg/kg</small>", unsafe_allow_html=True)
                                        display_values([(value, occurrences)], pdf_text)

                                check_and_append_values(ingredient_id, 'LD50', (most_common_ld50_values[0][0], [pdf_text[max(0, idx - 200):idx + 200] for _, idx in most_common_ld50_values[0][1]]), [(v, [pdf_text[max(0, idx - 200):idx + 200] for _, idx in occurrences]) for v, occurrences in most_common_ld50_values[1:]], values_file_path)
                            else:
                                st.write("Error finding the required value.")
                                st.write(f"[Link to PDF]({status_link})")
                                with open(values_file_path, 'a', encoding='utf-8') as file:
                                    file.write(f"{ingredient_id}:status_link:{status_link}\n")
                    except requests.RequestException as e:
                        st.error(f"Error accessing attachment {status_link}: {e}")
                    except Exception as e:
                        st.error("Error opening the PDF")
                        st.write(f"[Link to PDF]({status_link})")
                        with open(values_file_path, 'a', encoding='utf-8') as file:
                            file.write(f"{ingredient_id}:status_link:{status_link}\n")

            # Update button for each ingredient
            with st.form(key=f"update_form_{ingredient_id}"):
                st.markdown(f"**Update value for {ingredient_name}**")
                value_type = st.selectbox("Select value type", ["NOAEL", "LD50"], key=f"value_type_{ingredient_id}")
                new_value = st.text_input("Enter new value", key=f"new_value_{ingredient_id}")
                submit_button = st.form_submit_button(label="Submit")

                if submit_button and new_value:
                    update_value_in_file(ingredient_id, value_type, new_value, values_file_path)
                    st.success(f"Value for {ingredient_name} updated successfully.")
                    st.experimental_rerun()

    else:
        st.write(f"Ingredient containing '{ingredient_name}' not found in the data file.")



def update_value_in_file(ingredient_id, value_type, new_value, values_file_path):
    lines = []
    updated = False

    if os.path.exists(values_file_path):
        with open(values_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

    with open(values_file_path, 'w', encoding='utf-8') as file:
        for line in lines:
            if line.startswith(f"{ingredient_id}:most_common_{value_type}"):
                file.write(f"{ingredient_id}:most_common_{value_type}:{new_value}\n")
                updated = True
            elif line.startswith(f"{ingredient_id}:other_{value_type}"):
                # Rimuovi il valore vecchio se presente
                other_values = line.strip().split(':')[2].split(',')
                if new_value not in other_values:
                    other_values.append(new_value)
                file.write(f"{ingredient_id}:other_{value_type}:{','.join(other_values)}\n")
                updated = True
            else:
                file.write(line)

        if not updated:
            file.write(f"{ingredient_id}:most_common_{value_type}:{new_value}\n")

def get_search_history():
    if os.path.exists("search_history.txt"):
        with open("search_history.txt", "r", encoding="utf-8") as file:
            history = [line.strip() for line in file.readlines()]
        return history
    return []

def update_search_history(search_term):
    with open("search_history.txt", "a", encoding="utf-8") as file:
        file.write(f"{search_term}\n")

def load_ingredient_list(data_file_path):
    ingredient_list = []
    with open(data_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            data = eval(line.strip())
            ingredient_list.append(data['pcpc_ingredientname'])
    return ingredient_list

def update_database():
    # Add your database update here
    st.success("Database updated successfully!")

def main_page():
    data_file_path = '/workspaces/codespaces-blank/DATASET.txt'
    values_file_path = '/workspaces/codespaces-blank/VALUES.txt'
    
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        st.image("/workspaces/codespaces-blank/Toxic.png", use_column_width=True)
        
    ingredient_list = load_ingredient_list(data_file_path)

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h3 style='text-align: center;'>Search for an ingredient</h3>", unsafe_allow_html=True)
        ingredient_name = st.selectbox("", ingredient_list)
    
    st.markdown("<hr>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 4, 1])

    with col2:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h2>Search Result</h2>", unsafe_allow_html=True)
        if ingredient_name:
            find_ingredient_id_and_extract_link(ingredient_name, data_file_path, values_file_path)

    col1, col2, col3 = st.columns([4, 2, 4])
    with col2:
        update_search_history(ingredient_name)
        st.markdown("</div>", unsafe_allow_html=True)


def toxicity_calculator_page():
    data_file_path = '/workspaces/codespaces-blank/DATASET.txt'
    cosmetics_file_path = '/workspaces/codespaces-blank/cosmetics.json'

    st.markdown("<h1 style='font-size: 32px;'>Toxicity Calculator</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)

    with col1:
        cosmetic_name = st.text_input("Cosmetic Name")
        
        if "ingredients" not in st.session_state:
            st.session_state.ingredients = []

        selected_ingredient = st.selectbox("Select Ingredient to Add", load_ingredient_list(data_file_path), key="selected_ingredient")
        
        if st.button("Add Ingredient"):
            st.session_state.ingredients.append(selected_ingredient)

        toxicity_status = st.radio("Is the cosmetic toxic?", ("Yes", "No"))

        if st.button("Save Cosmetic"):
            new_cosmetic = {
                "Cosmetic Name": cosmetic_name,
                "Ingredients": st.session_state.ingredients,
                "Toxic": toxicity_status
            }
            if os.path.exists(cosmetics_file_path):
                with open(cosmetics_file_path, 'r', encoding='utf-8') as file:
                    cosmetics_data = json.load(file)
            else:
                cosmetics_data = []

            cosmetics_data.append(new_cosmetic)

            with open(cosmetics_file_path, 'w', encoding='utf-8') as file:
                json.dump(cosmetics_data, file, indent=4)

            st.session_state.ingredients = []
            st.experimental_rerun()

    with col2:
        st.markdown(f"<h2>Cosmetic: {cosmetic_name}</h2>", unsafe_allow_html=True)
        st.markdown("### Ingredients Added:")
        for ingredient in st.session_state.ingredients:
            st.markdown(f"- {ingredient}")
        st.markdown(f"### Toxic: {toxicity_status}")

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("<h3>Delete Cosmetic</h3>", unsafe_allow_html=True)
    if os.path.exists(cosmetics_file_path):
        with open(cosmetics_file_path, 'r', encoding='utf-8') as file:
            cosmetics_data = json.load(file)
        
        cosmetic_names = [cosmetic["Cosmetic Name"] for cosmetic in cosmetics_data]
        selected_cosmetic = st.selectbox("Select Cosmetic to Delete", cosmetic_names)
        
        if st.button("Delete Cosmetic"):
            cosmetics_data = [cosmetic for cosmetic in cosmetics_data if cosmetic["Cosmetic Name"] != selected_cosmetic]
            with open(cosmetics_file_path, 'w', encoding='utf-8') as file:
                json.dump(cosmetics_data, file, indent=4)
            st.success("Cosmetic deleted successfully.")
            st.experimental_rerun()

    st.markdown("<h3>Delete Ingredient from Cosmetic</h3>", unsafe_allow_html=True)
    if os.path.exists(cosmetics_file_path):
        with open(cosmetics_file_path, 'r', encoding='utf-8') as file:
            cosmetics_data = json.load(file)
        
        selected_cosmetic = st.selectbox("Select Cosmetic", cosmetic_names, key="delete_ingredient_cosmetic")
        ingredients_to_delete = [cosmetic for cosmetic in cosmetics_data if cosmetic["Cosmetic Name"] == selected_cosmetic][0].get("Ingredients", [])
        selected_ingredient_to_delete = st.selectbox("Select Ingredient to Delete", ingredients_to_delete)
        
        if st.button("Delete Ingredient"):
            for cosmetic in cosmetics_data:
                if cosmetic["Cosmetic Name"] == selected_cosmetic:
                    cosmetic["Ingredients"] = [ing for ing in cosmetic["Ingredients"] if ing != selected_ingredient_to_delete]
                    break
            with open(cosmetics_file_path, 'w', encoding='utf-8') as file:
                json.dump(cosmetics_data, file, indent=4)
            st.success("Ingredient deleted successfully.")
            st.experimental_rerun()

def dataset_page():
    csv_file_path = '/workspaces/codespaces-blank/output_table.csv'

    col1, col2 = st.columns([5, 5])

    with col1:
        st.markdown("<h1>Dataset</h1>", unsafe_allow_html=True)
        
        data = pd.read_csv(csv_file_path)
        data = data.rename(columns={'pcpc_ingredientname': 'Ingredient', 'link': 'Website'})

        st.markdown("<h2>Select an ingredient</h2>", unsafe_allow_html=True)
        ingredient_name = st.selectbox("", data['Ingredient'].tolist())
        
        selected_ingredient = data[data['Ingredient'] == ingredient_name]
        if not selected_ingredient.empty:
            website_link = selected_ingredient['Website'].values[0]
            st.markdown(f"[Link to selected ingredient]({website_link})")

    if st.button("Update Database"):
        update_database()
    st.markdown("<p>Click to update the database. This operation may take a few seconds.</p>", unsafe_allow_html=True)

    alphabet = ['1'] + list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    selected_letter = st.radio('', alphabet, horizontal=True)

    if selected_letter == '1':
        filtered_data = data[data['Ingredient'].apply(lambda x: re.match(r'^\d', x) is not None)]
    else:
        filtered_data = data[data['Ingredient'].str.startswith(selected_letter, na=False)]

    st.table(filtered_data)

def found_website_page():
    data_file_path = '/workspaces/codespaces-blank/DATASET.txt'
    
    st.markdown("<h1>Found Website</h1>", unsafe_allow_html=True)
    
    ingredient_name = st.text_input("Enter ingredient name")
    
    if st.button("Find"):
        ingredient_id = find_ingredient_id(ingredient_name, data_file_path)
        
        if ingredient_id:
            report_url = f"https://cir-reports.cir-safety.org/cir-ingredient-status-report/?id={ingredient_id}"
            st.write(f"Ingredient ID for '{ingredient_name}': {ingredient_id}")
            st.write(f"Opening CIR report: {report_url}")
            webbrowser.open(report_url)
        else:
            st.write(f"Ingredient '{ingredient_name}' not found in the data file.")

def find_ingredient_id(ingredient_name, data_file_path):
    with open(data_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            data = eval(line.strip())
            if data['pcpc_ingredientname'] == ingredient_name or data['pcpc_ciringredientname'] == ingredient_name:
                return data['pcpc_ingredientid']
    return None

# Custom CSS for styling
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
        
        body {
            font-family: 'Roboto', sans-serif;
            background-color: #f7f9fc;
        }
        
        h1, h2, h3, h4, h5, h6 {
            font-weight: 700;
        }
        
        .sidebar .sidebar-content {
            background-color: #f0f2f6;
        }
        
        .stButton>button {
            background-color: #ff3131;
            color: white;
            border-radius: 5px;
            border: none;
            padding: 10px 24px;
            font-size: 16px;
            font-weight: 500;
        }
        
        .stButton>button:hover {
            background-color: #ff3131;
        }
        
        .stTextInput>div>div>input {
            border-radius: 5px;
            padding: 10px;
            border: none;
            font-size: 16px;
        }
        
        .stSelectbox>div>div>div>div {
            border-radius: 5px;
            border: none;
            font-size: 16px;
        }
        
        .stTable {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        
        .stMarkdown h2 {
            border-bottom: 2px solid #FF3131;
            padding-bottom: 5px;
        }
        
        hr {
            border: none;
            height: 1px;
            background: #ccc;
            margin: 20px 0;
        }
        
        .stMarkdown ul {
            padding-left: 20px;
        }
        
        .stMarkdown ul li {
            margin-bottom: 5px;
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar menu
st.sidebar.title("Menu")
page = st.sidebar.radio("Navigation", ("Home", "Toxicity Calculator", "Certified Cosmetics", "Ingredient Information", "Dataset", "Safety News and Updates"))

if page == "Home":
    main_page()
elif page == "Dataset":
    dataset_page()
elif page == "Toxicity Calculator":
    toxicity_calculator_page()
elif page == "Ingredient Information":
    "Working in Progress"
elif page == "Safety News and Updates":
    "Working in Progress"
elif page == "Certified Cosmetics":
    "Working in Progress"
