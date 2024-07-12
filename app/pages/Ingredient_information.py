import sys
import os
import requests
from bs4 import BeautifulSoup
import sqlite3
from tqdm import tqdm
import streamlit as st

# Funzione per trovare il link di un ingrediente
def trova_link(ingrediente):
    base_url = "https://cosmileeurope.eu/wp-content/plugins/inci-db-search/search.php?s="
    parametri = "&l=it-IT&n=10&p=https%3A%2F%2Fcosmileeurope.eu%2Fit%2Finci%2Fingrediente"
    
    def fetch_link(query):
        url = f"{base_url}{query.replace(' ', '%20')}{parametri}"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        link = soup.find('a', class_='inci_box_link-link')
        if link:
            return link['href']
        return None
    
    link = fetch_link(ingrediente)
    if not link:
        words = ingrediente.split()
        while words:
            words.pop()
            partial_ingrediente = ' '.join(words)
            link = fetch_link(partial_ingrediente)
            if link:
                break
    return link

# Funzione per estrarre informazioni dalla pagina dell'ingrediente
def estrai_informazioni(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    info = {}
    
    # Estrazione delle sezioni principali
    main_content = soup.find('div', class_='inci_db')
    if main_content:
        sections = main_content.find_all(['h2', 'h3', 'p', 'a'])
        current_section = None
        
        for tag in sections:
            if tag.name == 'h2':
                current_section = tag.get_text(strip=True)
                info[current_section] = []
            elif current_section:
                if tag.name == 'a' and 'inci_box_link-link' in tag.get('class', []):
                    info[current_section].append(tag.get_text(strip=True))
                else:
                    info[current_section].append(tag.get_text(strip=True))
    
    return info

def get_db_connection():
    conn = sqlite3.connect('app/data/ingredients.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_pubchem_page(ingredient_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT pubchem_page FROM ingredients WHERE pcpc_ingredientname = ?"
    cursor.execute(query, (ingredient_name,))
    result = cursor.fetchone()
    conn.close()
    return result['pubchem_page'] if result else None

# Funzione per caricare la lista degli ingredienti dal database
def load_ingredient_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT pcpc_ingredientname FROM ingredients"
    cursor.execute(query)
    ingredients = [row['pcpc_ingredientname'] for row in cursor.fetchall()]
    conn.close()
    return ingredients

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=League+Spartan:wght@400;700&display=swap');
    
    * {
        font-family: 'League Spartan', sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<h1 style='text-align: center; font-size: 50px;'>Ingredient Informations</h1>", unsafe_allow_html=True)

ingredient_list = load_ingredient_list()

selected_ingredient = st.selectbox("Select an Ingredient", ingredient_list)

if selected_ingredient:
    st.markdown(f"<h4>{selected_ingredient} - Cosmile Europe Information</h4>", unsafe_allow_html=True)
    link = trova_link(selected_ingredient)
    if link:
        informazioni = estrai_informazioni(link)
        for key, value in informazioni.items():
            st.markdown(f"**{key}:**\n")
            if isinstance(value, list):
                for item in value:
                    if item.endswith('.'):
                        item = item[:-1]
                    st.markdown(f"{item}")
            else:
                if value.endswith('.'):
                    value = value[:-1]
                st.markdown(value)
            st.markdown("\n")
    else:
        st.warning("No Cosmile Europe information found for the selected ingredient.")

    pubchem_url = get_pubchem_page(selected_ingredient)
    
    if pubchem_url:
        st.markdown(f"<h4>{selected_ingredient} - PubChem Page</h4>", unsafe_allow_html=True)
        st.markdown(
            f'<iframe src="{pubchem_url}" width="100%" height="800px"></iframe>',
            unsafe_allow_html=True
        )
    else:
        st.warning("No PubChem page URL found for the selected ingredient.")
