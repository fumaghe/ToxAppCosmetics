import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import json
from app.utils.db_utils import load_ingredient_list, search_ingredient, load_company_list, create_cosmetics_table

create_cosmetics_table()

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=League+Spartan:wght@400;700&display=swap');
    
    * {
        font-family: 'League Spartan', sans-serif;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'League Spartan', sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<h1 style='text-align: center; font-size: 50px;'>Create Cosmetic</h1>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    cosmetic_name = st.text_input("Cosmetic Name")
    
    company_name = st.text_input("Company Name")

    if "ingredients" not in st.session_state:
        st.session_state.ingredients = []

    selected_ingredient = st.selectbox("Select Ingredient to Add", load_ingredient_list(), key="selected_ingredient")
    
    if st.button("Add Ingredient"):
        ingredient_data = search_ingredient(selected_ingredient)
        if ingredient_data and ingredient_data['value_updated']:
            display_name = f"{selected_ingredient} - {ingredient_data['value_updated']}"
        else:
            display_name = selected_ingredient
        
        st.session_state.ingredients.append(display_name)

    toxicity_status = st.radio("Is the cosmetic toxic?", ("Yes", "No"))

    if st.button("Save Cosmetic"):
        new_cosmetic = {
            "Cosmetic Name": cosmetic_name,
            "Company Name": company_name,
            "Ingredients": st.session_state.ingredients,
            "Toxic": toxicity_status
        }
        if os.path.exists("app/data/cosmetics.json"):
            try:
                with open("app/data/cosmetics.json", 'r', encoding='utf-8') as file:
                    cosmetics_data = json.load(file)
            except json.JSONDecodeError:
                cosmetics_data = []
        else:
            cosmetics_data = []

        existing_names = [cosmetic['Cosmetic Name'] for cosmetic in cosmetics_data]
        if cosmetic_name in existing_names:
            st.error("Name already exists, please try a different name.")
        else:
            cosmetics_data.append(new_cosmetic)

            with open("app/data/cosmetics.json", 'w', encoding='utf-8') as file:
                json.dump(cosmetics_data, file, indent=4)

            st.session_state.ingredients = []
            st.experimental_rerun()

with col2:
    st.markdown(f"<h3>Cosmetic: {cosmetic_name}</h3>", unsafe_allow_html=True)
    st.markdown(f"<h4>Company: {company_name}</h4>", unsafe_allow_html=True)
    st.markdown("##### Ingredients Added:")
    for ingredient in st.session_state.ingredients:
        st.markdown(f"- {ingredient}")
    st.markdown(f"##### Toxic: {toxicity_status}")

st.markdown("<hr>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.markdown("<h5>Delete Cosmetic</h5>", unsafe_allow_html=True)
    if os.path.exists("app/data/cosmetics.json"):
        try:
            with open("app/data/cosmetics.json", 'r', encoding='utf-8') as file:
                cosmetics_data = json.load(file)
        except json.JSONDecodeError:
            cosmetics_data = []
        
        if cosmetics_data:
            cosmetic_names = [cosmetic["Cosmetic Name"] for cosmetic in cosmetics_data]
            selected_cosmetic = st.selectbox("Select Cosmetic to Delete", cosmetic_names)
            
            if st.button("Delete Cosmetic"):
                cosmetics_data = [cosmetic for cosmetic in cosmetics_data if cosmetic["Cosmetic Name"] != selected_cosmetic]
                with open("app/data/cosmetics.json", 'w', encoding='utf-8') as file:
                    json.dump(cosmetics_data, file, indent=4)
                st.success("Cosmetic deleted successfully.")
                st.experimental_rerun()

    st.markdown("<h5>Delete Ingredient from Cosmetic</h5>", unsafe_allow_html=True)
    if os.path.exists("app/data/cosmetics.json"):
        try:
            with open("app/data/cosmetics.json", 'r', encoding='utf-8') as file:
                cosmetics_data = json.load(file)
        except json.JSONDecodeError:
            cosmetics_data = []

        if cosmetics_data:
            selected_cosmetic = st.selectbox("Select Cosmetic", [cosmetic["Cosmetic Name"] for cosmetic in cosmetics_data], key="delete_ingredient_cosmetic")
            ingredients_to_delete = [cosmetic for cosmetic in cosmetics_data if cosmetic["Cosmetic Name"] == selected_cosmetic][0].get("Ingredients", [])
            selected_ingredient_to_delete = st.selectbox("Select Ingredient to Delete", ingredients_to_delete)
            
            if st.button("Delete Ingredient"):
                for cosmetic in cosmetics_data:
                    if cosmetic["Cosmetic Name"] == selected_cosmetic:
                        cosmetic["Ingredients"] = [ing for ing in cosmetic["Ingredients"] if ing != selected_ingredient_to_delete]
                        break
                with open("app/data/cosmetics.json", 'w', encoding='utf-8') as file:
                    json.dump(cosmetics_data, file, indent=4)
                st.success("Ingredient deleted successfully.")
                st.experimental_rerun()