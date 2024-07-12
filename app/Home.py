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

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=League+Spartan:wght@400;700&display=swap');
    
    * {{
        font-family: 'League Spartan', sans-serif;
    }}
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'League Spartan', sans-serif;
    }}
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
        gap: 20px; /* Adds spacing between buttons */
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
        background-color: transparent;
        border: 2px solid #ff0000;
        border-radius: 5px;
        flex: 1;
    }}
    .result-buttons a button.light-theme {{
        color: black;
    }}
    .result-buttons a button.dark-theme {{
        color: white;
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
    .strikethrough {{
        text-decoration: line-through;
    }}
    </style>
    <div class="center-image">
        <img src="data:image/png;base64,{image_base64}" alt="Logo">
    </div>
    """,
    unsafe_allow_html=True
)

ingredient_list = load_ingredient_list()
st.markdown("<div class='center-box'><h3>Search for an ingredient</h3></div>", unsafe_allow_html=True)  
col1, col2, col3 = st.columns([1, 2, 1])
# Centrare la casella di ricerca
with col2:    
    st.markdown("<div class='center-box'>", unsafe_allow_html=True)
    ingredient_name = st.selectbox("Select an ingredient", ingredient_list, label_visibility='collapsed', key="ingredient_selectbox", index=0)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# Mostrare il risultato della ricerca
st.markdown('<div class="full-width search-result">', unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>Search Result</h2>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1.9, 2, 1])

with col2:
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
        echa_dossier = ingredient["echa_dossier"]
        
        def check_link(link):
            return link and link != "#"

        # Display the links as buttons
        st.markdown(
            f"""
            <div class='result-buttons'>
            <a href='{cir_page if check_link(cir_page) else "#"}' target='_blank' onclick="if('{cir_page}' === '#'){{event.preventDefault(); showError();}}"><button class='{"strikethrough" if not check_link(cir_page) else ""}'>CIR</button></a>
            <a href='{cir_pdf if check_link(cir_pdf) else "#"}' target='_blank' onclick="if('{cir_pdf}' === '#'){{event.preventDefault(); showError();}}"><button class='{"strikethrough" if not check_link(cir_pdf) else ""}'>PDF</button></a>
            <a href='{pubchem_page if check_link(pubchem_page) else "#"}' target='_blank' onclick="if('{pubchem_page}' === '#'){{event.preventDefault(); showError();}}"><button class='{"strikethrough" if not check_link(pubchem_page) else ""}'>PubChem</button></a>
            <a href='{echa_dossier if check_link(echa_dossier) else "#"}' target='_blank' onclick="if('{echa_dossier}' === '#'){{event.preventDefault(); showError();}}"><button class='{"strikethrough" if not check_link(echa_dossier) else ""}'>ECHA</button></a>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Mostra un messaggio di errore se il link non esiste e viene cliccato
        st.markdown(
            """
            <script>
            function showError() {
                let div = document.createElement('div');
                div.innerHTML = "Link not found";
                div.style.position = 'fixed';
                div.style.bottom = '10px';
                div.style.right = '10px';
                div.style.backgroundColor = 'red';
                div.style.color = 'white';
                div.style.padding = '10px';
                div.style.borderRadius = '5px';
                document.body.appendChild(div);
                setTimeout(() => div.remove(), 3000);
            }

            // Detect the Streamlit theme
            function applyTheme() {
                const bodyStyles = window.getComputedStyle(document.body);
                const theme = bodyStyles.getPropertyValue('--primary-background-color') === 'rgb(0, 0, 0)' ? 'dark' : 'light';
                const buttons = document.querySelectorAll('.result-buttons button');
                buttons.forEach(button => {
                    button.classList.add(theme === 'dark' ? 'dark-theme' : 'light-theme');
                });
            }

            // Apply theme on load
            document.addEventListener('DOMContentLoaded', applyTheme);
            </script>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<hr>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
            
        with col1:    
            # Aggiungere il selezionatore per la fonte dei dati
            source = st.selectbox("Select data source", ["CIR", "PubChem", "ECHA", "EFSA"], key="source_selectbox")
        
        with col2:
            # Aggiungere il selezionatore per il tipo di esposizione
            exposure_type = st.selectbox("Select exposure type", ["Oral", "Inhalate", "Dermal"], key="exposure_type_selectbox")

        st.markdown("<hr>", unsafe_allow_html=True)
        
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

        # Funzione per raggruppare i contesti con lo stesso valore
        def group_contexts(values_with_contexts):
            grouped = {}
            for value, context in values_with_contexts:
                if value in grouped:
                    grouped[value].append(context)
                else:
                    grouped[value] = [context]
            return grouped

        # Funzione per filtrare i contesti in base al tipo di esposizione
        def filter_by_exposure_type(values_with_contexts, exposure_type):
            keywords = {
                "Oral": ["oral"],
                "Inhalate": ["inhalate", "inhal", "inha"],
                "Dermal": ["dermal", "derm"]
            }
            filtered_values = []
            for value, context in values_with_contexts:
                if isinstance(context, list):
                    context = " ".join(context)
                for keyword in keywords[exposure_type]:
                    if keyword in context.lower():
                        filtered_values.append(value)
                        break
            return list(set(filtered_values))  # Rimuove i duplicati

        # Mostrare i valori in base alla fonte selezionata
        if source == "CIR":
            st.markdown("<div class='results'><h3>CIR Results</h3></div>", unsafe_allow_html=True)
            noael_cir = json.loads(ingredient['NOAEL_CIR'])
            ld50_cir = json.loads(ingredient['LD50_CIR'])

            # Filtrare e mostrare i valori in base al tipo di esposizione
            filtered_noael = filter_by_exposure_type(noael_cir, exposure_type)
            filtered_ld50 = filter_by_exposure_type(ld50_cir, exposure_type)
            
            if filtered_noael or filtered_ld50:
                st.markdown(f"<div class='results'><h4>{exposure_type} Values</h4></div>", unsafe_allow_html=True)
                if filtered_noael:
                    st.markdown("**NOAEL Values:** " + " - ".join(map(str, filtered_noael)))
                if filtered_ld50:
                    st.markdown("**LD50 Values:** " + " - ".join(map(str, filtered_ld50)))
            else:
                st.write("No values found for the selected exposure type.")
            
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**NOAEL Values:**")
                grouped_noael = group_contexts(noael_cir)
                for value, contexts in grouped_noael.items():
                    st.markdown(f"- {value} mg/kg")
                    with st.expander("Context"):
                        st.write("\n\n".join(map(str, contexts)))
                    if st.button("Verified Value", key=f"noael_button_{ingredient_id}_{value}"):
                        update_ingredient_value_in_db(ingredient_id, value)
                        st.success(f"Value for {ingredient['name']} updated successfully to {value}.")
                        st.experimental_rerun()

            with col2:
                st.markdown("**LD50 Values:**")
                grouped_ld50 = group_contexts(ld50_cir)
                for value, contexts in grouped_ld50.items():
                    st.markdown(f"- {value} mg/kg")
                    with st.expander("Context"):
                        st.write("\n\n".join(map(str, contexts)))
                    if st.button("Valore corretto", key=f"ld50_button_{ingredient_id}_{value}"):
                        update_ingredient_value_in_db(ingredient_id, value)
                        st.success(f"Value for {ingredient['name']} updated successfully to {value}.")
                        st.experimental_rerun()

        elif source == "PubChem":
            st.markdown("<div class='results'><h3>PubChem Results</h3></div>", unsafe_allow_html=True)
            ld50_pubchem = json.loads(ingredient['LD50_PubChem'])

            # Filtrare e mostrare i valori in base al tipo di esposizione
            filtered_ld50 = filter_by_exposure_type(ld50_pubchem, exposure_type)
            
            if filtered_ld50:
                st.markdown(f"<div class='results'><h4>{exposure_type} Values</h4></div>", unsafe_allow_html=True)
                st.markdown("**LD50 Values:** " + " - ".join(map(str, filtered_ld50)))
            else:
                st.write("No values found for the selected exposure type.")

            st.markdown("**LD50 Values:**")
            grouped_ld50_pubchem = group_contexts(ld50_pubchem)
            for value, contexts in grouped_ld50_pubchem.items():
                st.markdown(f"- {value} mg/kg")
                with st.expander("Context"):
                    st.write("\n\n".join(map(str, contexts)))
                if st.button("Valore corretto", key=f"pubchem_ld50_button_{ingredient_id}_{value}"):
                    update_ingredient_value_in_db(ingredient_id, value)
                    st.success(f"Value for {ingredient['name']} updated successfully to {value}.")
                    st.experimental_rerun()

        elif source == "ECHA":
            st.markdown("<div class='results'><h3>ECHA Results</h3></div>", unsafe_allow_html=True)
            echa_value_raw = ingredient['echa_value']
            echa_value = None
            if echa_value_raw and echa_value_raw != "[]":
                try:
                    echa_value = json.loads(echa_value_raw)
                except json.JSONDecodeError:
                    st.error("Failed to decode ECHA value. Please check the data format.")

            if echa_value:
                # Filtrare e mostrare i valori in base al tipo di esposizione
                filtered_echa = filter_by_exposure_type(echa_value, exposure_type)
                
                if filtered_echa:
                    st.markdown(f"<div class='results'><h4>{exposure_type} Values</h4></div>", unsafe_allow_html=True)
                    st.markdown("**ECHA Values:** " + " - ".join(map(str, filtered_echa)))
                else:
                    st.write("No values found for the selected exposure type.")

                st.markdown("**ECHA Values:**")
                grouped_echa = group_contexts(echa_value)
                for value, contexts in grouped_echa.items():
                    st.markdown(f"- {value}")
                    with st.expander("Context"):
                        st.write("\n\n".join(map(str, contexts)))
                    if st.button("Valore corretto", key=f"echa_value_button_{ingredient_id}_{value}"):
                        update_ingredient_value_in_db(ingredient_id, value)
                        st.success(f"Value for {ingredient['name']} updated successfully to {value}.")
                        st.experimental_rerun()
            else:
                st.write("No ECHA values found.")

        elif source == "EFSA":
            st.markdown("<div class='results'><h3>EFSA Results</h3></div>", unsafe_allow_html=True)
            efsa_value_raw = ingredient['EFSA_value']
            efsa_value = None
            if efsa_value_raw and efsa_value_raw != "[]":
                try:
                    efsa_value = json.loads(efsa_value_raw)
                except json.JSONDecodeError:
                    st.error("Failed to decode EFSA value. Please check the data format.")

            if efsa_value:
                # Filtrare e mostrare i valori in base al tipo di esposizione
                filtered_efsa = filter_by_exposure_type(efsa_value, exposure_type)
                
                if filtered_efsa:
                    st.markdown(f"<div class='results'><h4>{exposure_type} Values</h4></div>", unsafe_allow_html=True)
                    st.markdown("**EFSA Values:** " + " - ".join(map(str, filtered_efsa)))
                else:
                    st.write("No values found for the selected exposure type.")

                st.markdown("**EFSA Values:**")
                grouped_efsa = group_contexts(efsa_value)
                for value, contexts in grouped_efsa.items():
                    st.markdown(f"- {value}")
                    with st.expander("Context"):
                        st.write("\n\n".join(map(str, contexts)))
                    if st.button("Valore corretto", key=f"efsa_value_button_{ingredient_id}_{value}"):
                        update_ingredient_value_in_db(ingredient_id, value)
                        st.success(f"Value for {ingredient['name']} updated successfully to {value}.")
                        st.experimental_rerun()
            else:
                st.write("No EFSA values found.")

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
                update_ingredient_value_in_db(ingredient_id, new_value)
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


