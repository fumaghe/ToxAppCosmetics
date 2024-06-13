import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from collections import Counter
import PyPDF2
import io
import os

# Funzioni definite nel tuo codice
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
    
    # Check if the values file exists before trying to read it
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
            search_name = ingredient_name.lower()
            if (search_name in data['pcpc_ingredientname'].lower() or search_name in data['pcpc_ciringredientname'].lower()):
                ingredients.append((data['pcpc_ingredientname'], data['pcpc_ingredientid']))

    if ingredients:
        for ingredient_name, ingredient_id in set(ingredients):
            if ingredient_id in values_dict:
                st.markdown(f"<h3 style='text-align: left; font-size: 20px;'>Ingredient name: {ingredient_name}</h3>", unsafe_allow_html=True)
                most_common_noael = values_dict[ingredient_id].get('most_common_NOAEL', ['N/A'])[0]
                other_noael_values = values_dict[ingredient_id].get('other_NOAEL', [])
                most_common_ld50 = values_dict[ingredient_id].get('most_common_LD50', ['N/A'])[0]
                other_ld50_values = values_dict[ingredient_id].get('other_LD50', [])
                if most_common_noael != 'N/A':
                    st.markdown(f"Most common NOAEL: {most_common_noael} mg/kg")
                    if other_noael_values:
                        st.markdown("Other NOAEL values:")
                        for value in other_noael_values:
                            st.markdown(f"<small>{value} mg/kg</small>", unsafe_allow_html=True)
                elif most_common_ld50 != 'N/A':
                    st.markdown(f"Most common LD50: {most_common_ld50} mg/kg")
                    if other_ld50_values:
                        st.markdown("Other LD50 values:")
                        for value in other_ld50_values:
                            st.markdown(f"<small>{value} mg/kg</small>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<h3 style='text-align: left; font-size: 20px;'>Ingredient name: {ingredient_name}</h3>", unsafe_allow_html=True)
                    st.write("Nessun valore NOAEL o LD50 trovato.")
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
                            most_common_noael, _ = find_most_common_value(noael_values)
                            other_noael_values = set(noael_values)
                            other_noael_values.discard(most_common_noael)
                            st.markdown(f"<h3>Ingredient name: {ingredient_name}</h3>", unsafe_allow_html=True)
                            st.markdown(f"Most common NOAEL: {most_common_noael} mg/kg")
                            if other_noael_values:
                                st.markdown("Other NOAEL values:")
                                for value in other_noael_values:
                                    st.markdown(f"<small>{value} mg/kg</small>", unsafe_allow_html=True)
                            check_and_append_values(ingredient_id, 'NOAEL', most_common_noael, list(other_noael_values), values_file_path)
                        else:
                            ld50_values = find_values(pdf_text, 'LD50')
                            if ld50_values:
                                most_common_ld50, _ = find_most_common_value(ld50_values)
                                other_ld50_values = set(ld50_values)
                                other_ld50_values.discard(most_common_ld50)
                                st.markdown(f"<h3>Ingredient name: {ingredient_name}</h3>", unsafe_allow_html=True)
                                st.markdown(f"Most common LD50: {most_common_ld50} mg/kg")
                                if other_ld50_values:
                                    st.markdown("Other LD50 values:")
                                    for value in other_ld50_values:
                                        st.markdown(f"<small>{value} mg/kg</small>", unsafe_allow_html=True)
                                check_and_append_values(ingredient_id, 'LD50', most_common_ld50, list(other_ld50_values), values_file_path)
                            else:
                                st.markdown(f"<h3>Ingredient name: {ingredient_name}</h3>", unsafe_allow_html=True)
                                st.write("Errore nel trovare il valore richiesto")
                                st.write(f"Link al pdf: {status_link}")
                    except requests.RequestException as e:
                        st.error(f"Error accessing attachment {status_link}: {e}")
                    except Exception as e:
                        st.error("Errore nell'apertura del pdf")
                        st.write(f"Link al pdf: {status_link}")
    else:
        st.write(f"Ingredient containing '{ingredient_name}' not found in the data file.")

# Funzione per gestire la cronologia delle ricerche
def update_search_history(ingredient_name):
    history_file = "search_history.txt"
    if os.path.exists(history_file):
        with open(history_file, 'r') as file:
            history = file.readlines()
        history = [line.strip() for line in history if line.strip()]
    else:
        history = []

    if ingredient_name in history:
        history.remove(ingredient_name)
    history.insert(0, ingredient_name)
    history = history[:5]

    with open(history_file, 'w') as file:
        for item in history:
            file.write(f"{item}\n")

    return history

def get_search_history():
    history_file = "search_history.txt"
    if os.path.exists(history_file):
        with open(history_file, 'r') as file:
            history = file.readlines()
        history = [line.strip() for line in history if line.strip()]
        return history
    return []

# Funzione per caricare l'elenco degli ingredienti
def load_ingredient_list(data_file_path):
    ingredient_list = []
    with open(data_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            data = eval(line.strip())
            ingredient_list.append(data['pcpc_ingredientname'])
    return sorted(set(ingredient_list))

# Layout di Streamlit
st.set_page_config(layout="wide")
st.markdown("<h1 style='text-align: center; font-size: 60px;'>CosmeticToxicity</h1>", unsafe_allow_html=True)

# Variabili di autenticazione
def login():
    st.session_state['logged_in'] = False
    
    # Creazione di colonne per regolare la larghezza dei campi di input
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col2:
        username = st.text_input("Username", key="username")
        password = st.text_input("Password", type="password", key="password")

        if st.button("Login"):
            if username == "admin" and password == "NOAELLD50":
                st.session_state['logged_in'] = True
            else:
                st.error("Username o password errata")

def main_page():
    # Percorsi dei file
    data_file_path = '/workspaces/codespaces-blank/DATASET.txt'
    values_file_path = '/workspaces/codespaces-blank/VALUES.txt'

    # Carica l'elenco degli ingredienti
    ingredient_list = load_ingredient_list(data_file_path)

    # Creazione di colonne per centrare la barra di ricerca
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col2:
        ingredient_name = st.selectbox("Cerca un ingrediente", ingredient_list)
    
    # Linea orizzontale dopo la barra di ricerca
    st.markdown("<hr style='border:1px solid white;'>", unsafe_allow_html=True)

    # Layout principale con tre colonne per la linea verticale tra i risultati e la cronologia
    col1, col_middle, col2 = st.columns([4, 1, 4])

    # Visualizza i risultati della ricerca nella colonna sinistra
    with col1:
        st.markdown(f"<h2 style='text-align: left; font-size: 36px;'>Search Result</h2>", unsafe_allow_html=True)
        if ingredient_name:
            find_ingredient_id_and_extract_link(ingredient_name, data_file_path, values_file_path)
            update_search_history(ingredient_name)
    
    # Linea verticale tra i risultati e la cronologia
    with col_middle:
        st.markdown("<div style='border-left:1px solid white;height:100%;'></div>", unsafe_allow_html=True)

    # Visualizza la cronologia delle ricerche nella colonna destra
    with col2:
        st.markdown(f"<h2 style='text-align: left; font-size: 36px;'>Search History</h2>", unsafe_allow_html=True)
        search_history = get_search_history()
        for item in search_history:
            if st.button(item):
                ingredient_name = item
                with col1:
                    find_ingredient_id_and_extract_link(ingredient_name, data_file_path, values_file_path)

    # Linea orizzontale prima del bottone per aggiornare il database
    st.markdown("<hr style='border:1px solid white; margin-top: 25px;'>", unsafe_allow_html=True)
    
    # Bottone per aggiornare il database in fondo alla pagina
    st.markdown("<div style='display: flex; justify-content: left;'>", unsafe_allow_html=True)
    if st.button("Aggiorna Database"):
        update_database()
    st.markdown("<p style='text-align: left; font-size: small;'>Clicca per aggiornare database, questa operazione potrebbe durare più qualche secondo</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    login()
else:
    if not st.session_state['logged_in']:
        login()
    else:
        main_page()