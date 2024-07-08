import sys
import os
import base64
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'utils')))

import streamlit as st
from utils.db_utils import load_ingredient_list, find_ingredient_id_and_extract_link, update_search_history
from utils.findvalue import search_and_update_ingredient

# Imposta il layout di Streamlit
st.set_page_config(layout="wide")

# Percorso all'immagine
image_path = os.path.join('app', 'static', 'LOGOTOXAPP.png')

# Carica e visualizza l'immagine centrata
def get_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

image_base64 = get_image_base64(image_path)

# CSS per centrare l'immagine
st.markdown(
    f"""
    <style>
    .center-image {{
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 0;
        margin-bottom: 0;
    }}
    .center-image img {{
        width: 350px;  /* Ridimensiona l'immagine */
    }}
    .center-box {{
        display: flex;
        justify-content: center;
        align-items: center;
        width: 50%;
        margin: auto;
        padding: 0 20px; /* Adds spacing to the sides */
    }}
    .search-box {{
        text-align: center;
        font-size: 24px;
        margin-top: 20px;
        margin-bottom: 20px;
    }}
    .search-result {{
        width: 100%;
        font-size: 28px;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 20px;
    }}
    .result-links, .result-buttons {{
        width: 100%;
        font-size: 18px;
        margin-top: 10px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-evenly;
        gap: 120px; /* Adds spacing between buttons */
    }}
    .result-buttons a {{
        flex: 1;
        display: flex;
        justify-content: center;
        text-decoration: none; /* Removes the underline from links */
    }}
    .result-buttons a button {{
        width: 100%;
        padding: 10px 80px;
        font-size: 16px;
        cursor: pointer;
        background-color: white;
        color: black;
        border: 2px solid #ff0000;
        border-radius: 5px;
        flex: 1;
    }}
    .result-buttons a button:hover {{
        background-color: #ff0000;
        color: white;
    }}
    .cir-results, .pubchem-results {{
        width: 100%;
        font-size: 20px;
        margin-top: 10px;
        margin-bottom: 10px;
    }}
    .update-form {{
        width: 50%;
        margin: auto;
        font-size: 18px;
        margin-top: 20px;
        margin-bottom: 20px;
    }}
    .divider {{
        border-top: 2px solid #ccc;
        margin: 20px 0;
    }}
    </style>
    <div class="center-image">
        <img src="data:image/png;base64,{image_base64}" alt="Logo">
    </div>
    """,
    unsafe_allow_html=True
)



ingredient_list = load_ingredient_list()

# Centrare la casella di ricerca
st.markdown("<div class='center-box'><h3>Search for an ingredient</h3></div>", unsafe_allow_html=True)
st.markdown("<div class='center-box'>", unsafe_allow_html=True)
ingredient_name = st.selectbox("Select an ingredient", ingredient_list, label_visibility='collapsed', key="ingredient_selectbox", index=0)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)


# Mostrare il risultato della ricerca
st.markdown('<div class="full-width search-result">', unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>Search Result</h2>", unsafe_allow_html=True)

# Aggiungere un pulsante per cercare i valori online
if st.button('Search Values Online'):
    with st.spinner('Searching values...'):
        result = search_and_update_ingredient(ingredient_name)
        if result:
            st.success(f"Values for {ingredient_name} have been updated.")
        else:
            st.error(f"Could not find values for {ingredient_name} online.")
            
if ingredient_name:
    find_ingredient_id_and_extract_link(ingredient_name)
st.markdown('</div>', unsafe_allow_html=True)

update_search_history(ingredient_name)

