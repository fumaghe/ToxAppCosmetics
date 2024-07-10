import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import sqlite3
import streamlit as st
import pandas as pd
import re
from app.utils.db_utils import update_database

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

def get_db_connection():
    conn = sqlite3.connect('app/data/ingredients.db')
    conn.row_factory = sqlite3.Row
    return conn

def load_data_from_db():
    conn = get_db_connection()
    query = """
    SELECT pcpc_ingredientname AS Ingredient, cir_page AS CIR_Page, cir_pdf AS CIR_PDF, pubchem_page AS PubChem_Page, echa_dossier AS ECHA_Dossier
    FROM ingredients
    """
    data = pd.read_sql_query(query, conn)
    conn.close()
    return data

# Load data from the database
data = load_data_from_db()

st.markdown("<h1 style='text-align: center; font-size: 50px;'>Dataset</h1>", unsafe_allow_html=True)

# Page layout
col1, col2 = st.columns([5, 5])

with col1:
    
    st.markdown("<h4>Select an ingredient</h4>", unsafe_allow_html=True)
    ingredient_name = st.selectbox("", data['Ingredient'].tolist(), label_visibility='collapsed')
    
    selected_ingredient = data[data['Ingredient'] == ingredient_name]
    if not selected_ingredient.empty:
        cir_page = selected_ingredient['CIR_Page'].values[0]
        cir_pdf = selected_ingredient['CIR_PDF'].values[0]
        pubchem_page = selected_ingredient['PubChem_Page'].values[0]
        echa_dossier = selected_ingredient['ECHA_Dossier'].values[0]
        
        st.markdown(f"[Link to CIR Page]({cir_page})")
        st.markdown(f"[Link to CIR PDF]({cir_pdf})")
        st.markdown(f"[Link to PubChem Page]({pubchem_page})")
        st.markdown(f"[Link to ECHA Dossier]({echa_dossier})")

if st.button("Update Database"):
    update_database()
st.markdown("<p>Click to update the database. This operation may take a few seconds.</p>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)
alphabet = ['1'] + list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
selected_letter = st.radio('', alphabet, horizontal=True)

if selected_letter == '1':
    filtered_data = data[data['Ingredient'].apply(lambda x: re.match(r'^\d', x) is not None)]
else:
    filtered_data = data[data['Ingredient'].str.startswith(selected_letter, na=False)]

# Convert URLs to clickable links with a symbol
def make_clickable(val):
    if pd.notna(val):
        return f'<a href="{val}" target="_blank" class="link-symbol">&#128279;</a>'  # Unicode character for link symbol
    return ''

# Apply the function to the relevant columns using .loc to avoid SettingWithCopyWarning
filtered_data.loc[:, 'CIR_Page'] = filtered_data['CIR_Page'].apply(make_clickable)
filtered_data.loc[:, 'CIR_PDF'] = filtered_data['CIR_PDF'].apply(make_clickable)
filtered_data.loc[:, 'PubChem_Page'] = filtered_data['PubChem_Page'].apply(make_clickable)
filtered_data.loc[:, 'ECHA_Dossier'] = filtered_data['ECHA_Dossier'].apply(make_clickable)

# Render the table with clickable links
st.markdown(
    """
    <style>
    .link-symbol {
        text-decoration: none;
        display: inline-block;
        text-align: center;
    }
    </style>
    """, 
    unsafe_allow_html=True
)
st.markdown(filtered_data.to_html(escape=False, index=False, justify='left'), unsafe_allow_html=True)
