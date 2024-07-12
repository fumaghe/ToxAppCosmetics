import sqlite3
import json
import streamlit as st
from utils.web_utils import find_missing_values

def get_db_connection():
    conn = sqlite3.connect('app/data/ingredients.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_cosmetics_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cosmetics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cosmetic_name TEXT NOT NULL,
        company_name TEXT NOT NULL,
        ingredients TEXT NOT NULL,
        toxic TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def search_ingredient(ingredient_name_or_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT 
        pcpc_ingredientid AS id, 
        pcpc_ingredientname AS name, 
        NOAEL_CIR, 
        LD50_CIR, 
        LD50_PubChem, 
        echa_value,
        echa_dossier,
        EFSA_value,
        value_updated, 
        cir_page, 
        cir_pdf, 
        pubchem_page
    FROM ingredients
    WHERE pcpc_ingredientid = ? OR pcpc_ingredientname = ?
    """
    cursor.execute(query, (ingredient_name_or_id, ingredient_name_or_id))
    result = cursor.fetchone()
    conn.close()
    return result

def update_ingredient_value_in_db(ingredient_id, value_updated):
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

def remove_updated_value(ingredient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    UPDATE ingredients
    SET value_updated = NULL
    WHERE pcpc_ingredientid = ?
    """
    cursor.execute(query, (ingredient_id,))
    conn.commit()
    conn.close()

def load_ingredient_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pcpc_ingredientname FROM ingredients")
    ingredients = cursor.fetchall()
    conn.close()
    return [ingredient["pcpc_ingredientname"] for ingredient in ingredients]

def load_company_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DISTINCT company_name FROM cosmetics")
        companies = cursor.fetchall()
        return [company["company_name"] for company in companies]
    except sqlite3.OperationalError:
        return []

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

        st.markdown(f"<h3 style='text-align: left; font-size: 25px;'>Ingredient name: {ingredient['name']}</h3>", unsafe_allow_html=True)

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

        col1, col2, col3 = st.columns([4, 1, 4])
        
        with col1:
            st.markdown("<div class='cir-results'><h3>CIR Results</h3></div>", unsafe_allow_html=True)
            noael_cir = json.loads(ingredient['NOAEL_CIR'])
            ld50_cir = json.loads(ingredient['LD50_CIR'])

            if noael_cir:
                st.markdown("**NOAEL Values:**")
                for idx, (value, context) in enumerate(noael_cir):
                    st.markdown(f"- {value} mg/kg")
                    with st.expander("Context"):
                        st.write(context)
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
                        st.write(context)
                    if st.button("Valore corretto", key=f"ld50_button_{ingredient_id}_{idx}"):
                        update_ingredient_value_in_db(ingredient_id, value)
                        st.success(f"Value for {ingredient['name']} updated successfully to {value}.")
                        st.experimental_rerun()
            else:
                st.write("No LD50 values found in CIR.")

        with col3:
            st.markdown("<div class='pubchem-results'><h3>PubChem Results</h3></div>", unsafe_allow_html=True)
            ld50_pubchem = json.loads(ingredient['LD50_PubChem'])

            if ld50_pubchem:
                st.markdown("**LD50 Values:**")
                for idx, (value, context) in enumerate(ld50_pubchem):
                    st.markdown(f"- {value} mg/kg")
                    with st.expander("Context"):
                        st.write(context)
                    if st.button("Valore corretto", key=f"pubchem_ld50_button_{ingredient_id}_{idx}"):
                        update_ingredient_value_in_db(ingredient_id, value)
                        st.success(f"Value for {ingredient['name']} updated successfully to {value}.")
                        st.experimental_rerun()
            else:
                st.write("No LD50 values found in PubChem.")

        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2: 
            st.markdown("<div class='update-form'>", unsafe_allow_html=True)
            with st.form(key=f"update_form_{ingredient_id}"):
                st.markdown(f"**Update value for {ingredient['name']}**")
                new_value = st.text_input("Enter new value", key=f"new_value_{ingredient_id}")
                submit_button = st.form_submit_button(label="Submit")

                if submit_button and new_value:
                    update_ingredient_value_in_db(ingredient_id, new_value)
                    st.success(f"Value for {ingredient['name']} updated successfully.")
                    st.experimental_rerun()
            st.markdown("</div>", unsafe_allow_html=True)

            if value_updated:
                if st.button("Remove Updated Value"):
                    remove_updated_value(ingredient_id)
                    st.success(f"Value for {ingredient['name']} removed successfully.")
                    st.experimental_rerun()
    else:
        st.write(f"Ingredient '{ingredient_name}' not found in the database.")
        result, source = find_missing_values(ingredient_name)
        if result:
            st.markdown(f"**Found {source} Value:** {result}")
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

def update_database():
    st.success("Database updated successfully!")
