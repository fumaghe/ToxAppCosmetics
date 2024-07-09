import sys
import os
import base64
import json
import streamlit as st
from utils.db_utils import load_ingredient_list, update_search_history, search_ingredient, get_db_connection, update_ingredient_value_in_db
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
    .results {{
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
    ingredient = search_ingredient(ingredient_name)
    if ingredient:
        ingredient_id = ingredient["id"]
        cir_page = ingredient["cir_page"]
        cir_pdf = ingredient["cir_pdf"]
        pubchem_page = ingredient["pubchem_page"]
        
        # Display the links as buttons
        st.markdown(
            f"""
            <div class='result-buttons'>
            <a href='{cir_page}' target='_blank'><button>CIR</button></a>
            <a href='{cir_pdf}' target='_blank'><button>PDF</button></a>
            <a href='{pubchem_page}' target='_blank'><button>PubChem</button></a>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Aggiungere il selezionatore per la fonte dei dati
        source = st.selectbox("Select data source", ["CIR", "PubChem", "ECHA"], key="source_selectbox")


        value_updated = ingredient['value_updated']
        if value_updated:
            st.markdown(
                f"""
                <div style="color: red; font-size: 20px;">
                User Updated Values
                - {value_updated}
                </div>
                """, 
                unsafe_allow_html=True
            )

        # Mostrare i valori in base alla fonte selezionata
        if source == "CIR":
            st.markdown("<div class='results'><h3>CIR Results</h3></div>", unsafe_allow_html=True)
            noael_cir = json.loads(ingredient['NOAEL_CIR'])
            ld50_cir = json.loads(ingredient['LD50_CIR'])

            if noael_cir:
                st.markdown("**NOAEL Values:**")
                for idx, (value, context) in enumerate(noael_cir):
                    st.markdown(f"- {value} mg/kg")
                    with st.expander("Context"):
                        st.write(f"{context}")
                    if st.button("Verified Value", key=f"noael_button_{ingredient_id}_{idx}"):
                        update_ingredient_value_in_db(ingredient_id, value)
                        st.success(f"Value for {ingredient['name']} updated successfully to {value}.")
                        st.experimental_rerun()
            else:
                st.write("No NOAEL values found in CIR.")

            if ld50_cir:
                st.markdown("**LD50 Values:**")
                for idx, (value, context) in enumerate(ld50_cir):
                    st.markdown(f"- {value} mg/kg")
                    with st.expander("Context"):
                        st.write(f"{context}")
                    if st.button("Valore corretto", key=f"ld50_button_{ingredient_id}_{idx}"):
                        update_ingredient_value_in_db(ingredient_id, value)
                        st.success(f"Value for {ingredient['name']} updated successfully to {value}.")
                        st.experimental_rerun()
            else:
                st.write("No LD50 values found in CIR.")

        elif source == "PubChem":
            st.markdown("<div class='results'><h3>PubChem Results</h3></div>", unsafe_allow_html=True)
            ld50_pubchem = json.loads(ingredient['LD50_PubChem'])

            if ld50_pubchem:
                st.markdown("**LD50 Values:**")
                for idx, (value, context) in enumerate(ld50_pubchem):
                    st.markdown(f"- {value} mg/kg")
                    with st.expander("Context"):
                        st.write(f"{context}")
                    if st.button("Valore corretto", key=f"pubchem_ld50_button_{ingredient_id}_{idx}"):
                        update_ingredient_value_in_db(ingredient_id, value)
                        st.success(f"Value for {ingredient['name']} updated successfully to {value}.")
                        st.experimental_rerun()
            else:
                st.write("No LD50 values found in PubChem.")

        elif source == "ECHA":
            st.markdown("<div class='results'><h3>ECHA Results</h3></div>", unsafe_allow_html=True)
            echa_value = json.loads(ingredient['echa_value'])

            if echa_value != "[]":
                st.markdown("**ECHA Values:**")
                for idx, (value, context) in enumerate(echa_value):
                    st.markdown(f"- {value}")
                    with st.expander("Context"):
                        st.write(f"{context}")
                    if st.button("Valore corretto", key=f"echa_value_button_{ingredient_id}_{idx}"):
                        update_ingredient_value_in_db(ingredient_id, value)
                        st.success(f"Value for {ingredient['name']} updated successfully to {value}.")
                        st.experimental_rerun()
            else:
                st.write("No ECHA values found.")
    else:
        st.write("No ingredient selected.")

    st.markdown("<hr>", unsafe_allow_html=True)

    # Adattare la sezione dell'aggiornamento del valore
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='update-form'>", unsafe_allow_html=True)
        with st.form(key=f"update_form_{ingredient_name}"):
            st.markdown(f"**Update value for {ingredient_name}**")
            new_value = st.text_input("Enter new value", key=f"new_value_{ingredient_name}")
            submit_button = st.form_submit_button(label="Submit")

            if submit_button and new_value:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO ingredients (pcpc_ingredientid, pcpc_ingredientname, value_updated)
                VALUES (?, ?, ?)
                """, (ingredient_name, ingredient_name, new_value))
                conn.commit()
                conn.close()
                st.success(f"Value for {ingredient_name} updated successfully.")
                st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Aggiungere il pulsante per rimuovere il value_updated
    if value_updated:
        with col2:
            if st.button("Remove updated value"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                UPDATE ingredients
                SET value_updated = NULL
                WHERE pcpc_ingredientid = ?
                """, (ingredient_id,))
                conn.commit()
                conn.close()
                st.success(f"Updated value for {ingredient_name} has been removed.")
                st.experimental_rerun()
else:
    st.write("No ingredient selected.")
