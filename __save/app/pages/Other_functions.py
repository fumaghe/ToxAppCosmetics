import streamlit as st
import pandas as pd
import sqlite3
import os
from utils.findpdf import search_ingredients
from utils.findfromfoto import process_ingredients_from_csv
from utils.db_utils import load_ingredient_list

# Configura il layout di Streamlit
st.set_page_config(layout="wide")

# CSS per la stilizzazione
st.markdown(
    """
    <style>
    .center-title {
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 50px;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .center-box {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 50%;
        margin: auto;
        padding: 0 20px; /* Adds spacing to the sides */
    }
    .search-box {
        text-align: center;
        font-size: 24px;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .search-result {
        width: 100%;
        font-size: 28px;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .result-buttons {
        width: 100%;
        font-size: 18px;
        margin-top: 10px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-evenly;
    }
    .stProgress > div > div > div > div {
        background-color: red;
    }
    </style>
    """, unsafe_allow_html=True
)

# Centrare il titolo
st.markdown('<div class="center-title">Other Functions</div>', unsafe_allow_html=True)

# Stato per l'interruzione
if 'stop_process' not in st.session_state:
    st.session_state.stop_process = False

def stop_processing():
    st.session_state.stop_process = True

# Sezione per FindPDF
st.markdown("<h2>Find PDF</h2>", unsafe_allow_html=True)

num_ingredients_pdf = st.number_input("Number of ingredients to search", min_value=1, value=10, step=1)
start_index_pdf = st.number_input("Starting index", min_value=0, value=0, step=1)

if st.button('Search PDFs'):
    st.session_state.stop_process = False
    with st.spinner('Searching PDFs...'):
        search_ingredients(start_index_pdf, start_index_pdf + num_ingredients_pdf, st.session_state.stop_process)
    if st.session_state.stop_process:
        st.warning('PDF search interrupted.')
    else:
        st.success('PDF search completed.')

if st.button('Stop PDF Search'):
    stop_processing()

# Sezione per FindFromFoto
st.markdown("<h2>Find from Foto</h2>", unsafe_allow_html=True)

ingredients_df = pd.read_csv('app/data/Ingredients_with_missing_values.csv')
ingredients_list = ingredients_df['pcpc_ingredientname'].tolist()
selected_ingredients = st.multiselect("Select ingredients to search", ingredients_list)

if st.button('Search from Foto'):
    st.session_state.stop_process = False
    with st.spinner('Searching from Foto...'):
        process_ingredients_from_csv(selected_ingredients, st.session_state.stop_process)
    if st.session_state.stop_process:
        st.warning('Foto search interrupted.')
    else:
        st.success('Foto search completed.')

if st.button('Stop Foto Search'):
    stop_processing()

# Sezione per il download del database
st.markdown("<h2>Download Database</h2>", unsafe_allow_html=True)

if st.button('Download Database'):
    st.session_state.stop_process = False
    with st.spinner('Preparing download...'):
        db_path = 'app/data/ingredients.db'
        conn = sqlite3.connect(db_path)
        conn.close()
        with open(db_path, 'rb') as f:
            st.download_button(label="Download ingredients.db", data=f, file_name="ingredients.db", mime='application/octet-stream')
    if st.session_state.stop_process:
        st.warning('Database download interrupted.')
    else:
        st.success('Database download completed.')

if st.button('Stop Database Download'):
    stop_processing()
