import sqlite3
import json
import streamlit as st
from utils.web_utils import find_missing_values

def get_db_connection():
    conn = sqlite3.connect('app/data/ingredients.db')
    conn.row_factory = sqlite3.Row
    return conn

def search_ingredient(ingredient_name_or_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT pcpc_ingredientid AS id, pcpc_ingredientname AS name, NOAEL_CIR, LD50_CIR, LD50_PubChem, value_updated, cir_page, cir_pdf, pubchem_page
    FROM ingredients
    WHERE pcpc_ingredientid = ? OR pcpc_ingredientname = ?
    """
    cursor.execute(query, (ingredient_name_or_id, ingredient_name_or_id))
    result = cursor.fetchone()
    conn.close()
    return result

def update_ingredient_in_db(ingredient_id, value_updated):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    UPDATE ingredients
    SET value_updated = ?
    WHERE pcpc_ingredientid = ?
    """
    cursor.execute(query, (value_updated, ingredient_id))
    conn.commit()
    conn.close()

def load_ingredient_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pcpc_ingredientname FROM ingredients")
    ingredients = cursor.fetchall()
    conn.close()
    return [ingredient["pcpc_ingredientname"] for ingredient in ingredients]

def update_search_history(search_term):
    with open("app/data/search_history.txt", "a", encoding="utf-8") as file:
        file.write(f"{search_term}\n")

def find_ingredient_id_and_extract_link(ingredient_name):
    ingredient = search_ingredient(ingredient_name)
    if ingredient:
        ingredient_id = ingredient["id"]
        cir_page = ingredient["cir_page"]
        cir_pdf = ingredient["cir_pdf"]
        pubchem_page = ingredient["pubchem_page"]

        st.markdown(f"<h3 style='text-align: left; font-size: 20px;'>Ingredient name: {ingredient['name']}</h3>", unsafe_allow_html=True)

        # Display the links in a rounded-corner box
        st.markdown(
            f"""
            <div style='border: 2px solid #ccc; border-radius: 15px; padding: 10px;'>
                <h4>Links</h4>
                <p>Link sito CIR: <a href='{cir_page}' target='_blank'>clicca</a></p>
                <p>Link pdf CIR: <a href='{cir_pdf}' target='_blank'>clicca</a></p>
                <p>Link sito PubChem: <a href='{pubchem_page}' target='_blank'>clicca</a></p>
            </div>
            """,
            unsafe_allow_html=True
        )

        value_updated = ingredient['value_updated']
        if value_updated:
            st.markdown("### User Updated Values")
            st.markdown(f"- {value_updated}")

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

        # Form to update the value
        with st.form(key=f"update_form_{ingredient_id}"):
            st.markdown(f"**Update value for {ingredient['name']}**")
            new_value = st.text_input("Enter new value", key=f"new_value_{ingredient_id}")
            submit_button = st.form_submit_button(label="Submit")

            if submit_button and new_value:
                update_ingredient_in_db(ingredient_id, new_value)
                st.success(f"Value for {ingredient['name']} updated successfully.")
                st.experimental_rerun()
    else:
        st.write(f"Ingredient '{ingredient_name}' not found in the database.")
        # Perform online search if the ingredient is not found in the database
        result, source = find_missing_values(ingredient_name)
        if result:
            st.markdown(f"**Found {source} Value:** {result}")
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

def update_database():
    # Add your database update logic here
    st.success("Database updated successfully!")
