import sqlite3
import json
import streamlit as st
from app.utils.web_utils import get_pubchem_cid, extract_first_status_link

def get_db_connection():
    conn = sqlite3.connect('app/data/ingredients.db')
    conn.row_factory = sqlite3.Row
    return conn

def load_ingredient_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pcpc_ingredientname FROM ingredients")
    ingredients = cursor.fetchall()
    conn.close()
    return [ingredient["pcpc_ingredientname"] for ingredient in ingredients]

def update_database():
    st.success("Database updated successfully!")

def search_ingredient(ingredient_name_or_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT pcpc_ingredientid AS id, pcpc_ingredientname AS name, NOAEL_CIR, LD50_CIR, LD50_PubChem
    FROM ingredients
    WHERE pcpc_ingredientid = ? OR pcpc_ingredientname = ?
    """
    cursor.execute(query, (ingredient_name_or_id, ingredient_name_or_id))
    result = cursor.fetchone()
    conn.close()
    return result

def find_ingredient_id_and_extract_link(ingredient_name):
    ingredient = search_ingredient(ingredient_name)
    if ingredient:
        ingredient_id = ingredient["id"]
        st.markdown(f"<h3 style='text-align: left; font-size: 20px;'>Ingredient name: {ingredient['name']}</h3>", unsafe_allow_html=True)

        # Retrieve and display the CIR PDF link
        cir_link = extract_first_status_link(ingredient_id)
        if cir_link:
            st.markdown(f"[CIR Report PDF]({cir_link})")

        # Retrieve and display the PubChem link
        cid = get_pubchem_cid(ingredient['name'])
        if cid:
            pubchem_link = f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"
            st.markdown(f"[PubChem Page]({pubchem_link})")

        col1, col2, col3 = st.columns([4, 0.5, 4])
        
        with col1:
            st.markdown("### CIR Results")
            noael_cir = json.loads(ingredient['NOAEL_CIR'])
            ld50_cir = json.loads(ingredient['LD50_CIR'])

            if noael_cir:
                st.markdown("**NOAEL Values:**")
                for value, context in noael_cir:
                    st.markdown(f"- {value} mg/kg")
                    with st.expander("Context"):
                        st.write(context)
            else:
                st.write("No NOAEL values found in CIR.")

            if ld50_cir:
                st.markdown("**LD50 Values:**")
                for value, context in ld50_cir:
                    st.markdown(f"- {value} mg/kg")
                    with st.expander("Context"):
                        st.write(context)
            else:
                st.write("No LD50 values found in CIR.")

        with col3:
            st.markdown("### PubChem Results")
            ld50_pubchem = json.loads(ingredient['LD50_PubChem'])

            if ld50_pubchem:
                st.markdown("**LD50 Values:**")
                for value, context in ld50_pubchem:
                    st.markdown(f"- {value} mg/kg")
                    with st.expander("Context"):
                        st.write(context)
            else:
                st.write("No LD50 values found in PubChem.")

    else:
        st.write(f"Ingredient '{ingredient_name}' not found in the database.")

def update_search_history(ingredient_name):
    with open('app/data/search_history.txt', 'a') as file:
        file.write(f'{ingredient_name}\n')
