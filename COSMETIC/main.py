import streamlit as st
import pandas as pd
import os
from data_processing import find_ingredient_id_and_extract_link, update_database, load_ingredient_list
from utils import update_search_history, get_search_history

def main_page():
    data_file_path = 'C:\Users\AndreaFumagalli\OneDrive - ITS Angelo Rizzoli\Documenti\GitHub\ProjectWork\COSMETIC\DATASET.txt'
    values_file_path = 'C:\Users\AndreaFumagalli\OneDrive - ITS Angelo Rizzoli\Documenti\GitHub\ProjectWork\COSMETIC\VALUES.txt'
    st.markdown("<h1 style='text-align: center; font-size: 80px;'>CosmeticToxicity</h1>", unsafe_allow_html=True)
    ingredient_list = load_ingredient_list(data_file_path)

    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col2:
        st.markdown(f"<h3 style='text-align: center; font-size: 20px;'>Cerca un ingrediente</h3>", unsafe_allow_html=True)
        ingredient_name = st.selectbox("", ingredient_list)
    
    st.markdown("<hr style='border:1px solid white;'>", unsafe_allow_html=True)

    col1, col_middle, col2 = st.columns([4, 0.2, 4])

    with col1:
        st.markdown(f"<h2 style='text-align: left; font-size: 30px;'>Search Result</h2>", unsafe_allow_html=True)
        if ingredient_name:
            find_ingredient_id_and_extract_link(ingredient_name, data_file_path, values_file_path)
            update_search_history(ingredient_name)
    
    with col_middle:
        st.markdown("<div style='border-left:1px solid white;height:100%;'></div>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"<h2 style='text-align: left; font-size: 30px;'>Search History</h2>", unsafe_allow_html=True)
        search_history = get_search_history()
        for item in search_history:
            if st.button(item):
                ingredient_name = item
                with col1:
                    find_ingredient_id_and_extract_link(ingredient_name, data_file_path, values_file_path)

    st.markdown("<hr style='border:1px solid white; margin-top: 25px;'>", unsafe_allow_html=True)

def dataset_page():
    csv_file_path = 'output_table.csv'

    col1, col2 = st.columns([3, 5])

    with col1:
        st.markdown("<h1 style='text-align: left; font-size: 60px;'>Dataset</h1>", unsafe_allow_html=True)
        
        data = pd.read_csv(csv_file_path)

        # Rinomina le colonne
        data = data.rename(columns={'pcpc_ingredientname': 'Ingredient', 'link': 'Website'})

        # Aggiungi una selectbox per selezionare l'ingrediente
        st.markdown("<h2 style='font-size: 18px;'>Seleziona un ingrediente</h2>", unsafe_allow_html=True)
        ingredient_name = st.selectbox("", data['Ingredient'].tolist())
        
        # Trova l'ID dell'ingrediente selezionato
        selected_ingredient = data[data['Ingredient'] == ingredient_name]
        if not selected_ingredient.empty:
            website_link = selected_ingredient['Website'].values[0]
            st.markdown(f"[Link all'ingrediente selezionato]({website_link})")

    st.markdown("<div style='display: flex; justify-content: left;'>", unsafe_allow_html=True)
    if st.button("Aggiorna Database"):
        update_database()
    st.markdown("<p style='text-align: left; font-size: small;'>Clicca per aggiornare database, questa operazione potrebbe durare più qualche secondo</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    alphabet = ['1'] + list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    selected_letter = st.radio('', alphabet, horizontal=True)

    # Filtra i dati in base alla lettera selezionata
    if selected_letter == '1':
        filtered_data = data[data['Ingredient'].apply(lambda x: re.match(r'^\d', x) is not None)]
    else:
        filtered_data = data[data['Ingredient'].str.startswith(selected_letter, na=False)]

    st.table(filtered_data)

def found_website_page():
    data_file_path = 'DATASET.txt'
    
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

st.set_page_config(layout="wide")

st.sidebar.title("Menu")
page = st.sidebar.radio("Navigazione", ("Home", "Dataset", "Found Website"))

if page == "Home":
    main_page()
elif page == "Dataset":
    dataset_page()
elif page == "Found Website":
    found_website_page()
