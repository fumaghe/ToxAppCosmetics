import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import sqlite3
from utils.db_utils import load_ingredient_list

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

# Streamlit page
st.markdown("<h1>Ingredient Information</h1>", unsafe_allow_html=True)

ingredient_list = load_ingredient_list()

# Select ingredient
selected_ingredient = st.selectbox("Select an Ingredient", ingredient_list)

if selected_ingredient:
    pubchem_url = get_pubchem_page(selected_ingredient)
    
    if pubchem_url:
        st.markdown(f"<h4>{selected_ingredient} - PubChem Page</h4>", unsafe_allow_html=True)
        st.markdown(
            f'<iframe src="{pubchem_url}" width="100%" height="800px"></iframe>',
            unsafe_allow_html=True
        )
    else:
        st.warning("No PubChem page URL found for the selected ingredient.")
