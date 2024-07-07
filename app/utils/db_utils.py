import sqlite3
import json
import streamlit as st

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

def find_ingredient_id_and_extract_link(ingredient_name):
    ingredient = search_ingredient(ingredient_name)
    if ingredient:
        ingredient_id = ingredient["id"]
        st.markdown(f"<h3 style='text-align: left; font-size: 20px;'>Ingredient name: {ingredient['name']}</h3>", unsafe_allow_html=True)

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
