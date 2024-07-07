import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import json
import os
from app.utils.db_utils import load_ingredient_list

st.markdown("<h1>Toxicity Calculator</h1>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    cosmetic_name = st.text_input("Cosmetic Name")
    
    if "ingredients" not in st.session_state:
        st.session_state.ingredients = []

    selected_ingredient = st.selectbox("Select Ingredient to Add", load_ingredient_list(), key="selected_ingredient")
    
    if st.button("Add Ingredient"):
        st.session_state.ingredients.append(selected_ingredient)

    toxicity_status = st.radio("Is the cosmetic toxic?", ("Yes", "No"))

    if st.button("Save Cosmetic"):
        new_cosmetic = {
            "Cosmetic Name": cosmetic_name,
            "Ingredients": st.session_state.ingredients,
            "Toxic": toxicity_status
        }
        if os.path.exists("app/data/cosmetics.json"):
            with open("app/data/cosmetics.json", 'r', encoding='utf-8') as file:
                cosmetics_data = json.load(file)
        else:
            cosmetics_data = []

        cosmetics_data.append(new_cosmetic)

        with open("app/data/cosmetics.json", 'w', encoding='utf-8') as file:
            json.dump(cosmetics_data, file, indent=4)

        st.session_state.ingredients = []
        st.experimental_rerun()

with col2:
    st.markdown(f"<h3>Cosmetic: {cosmetic_name}</h3>", unsafe_allow_html=True)
    st.markdown("### Ingredients Added:")
    for ingredient in st.session_state.ingredients:
        st.markdown(f"- {ingredient}")
    st.markdown(f"### Toxic: {toxicity_status}")

st.markdown("<hr>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    # Delete Cosmetic Section
    st.markdown("<h3>Delete Cosmetic</h3>", unsafe_allow_html=True)
    if os.path.exists("app/data/cosmetics.json"):
        with open("app/data/cosmetics.json", 'r', encoding='utf-8') as file:
            cosmetics_data = json.load(file)
        
        cosmetic_names = [cosmetic["Cosmetic Name"] for cosmetic in cosmetics_data]
        selected_cosmetic = st.selectbox("Select Cosmetic to Delete", cosmetic_names)
        
        if st.button("Delete Cosmetic"):
            cosmetics_data = [cosmetic for cosmetic in cosmetics_data if cosmetic["Cosmetic Name"] != selected_cosmetic]
            with open("app/data/cosmetics.json", 'w', encoding='utf-8') as file:
                json.dump(cosmetics_data, file, indent=4)
            st.success("Cosmetic deleted successfully.")
            st.experimental_rerun()

    st.markdown("<h3>Delete Ingredient from Cosmetic</h3>", unsafe_allow_html=True)
    if os.path.exists("app/data/cosmetics.json"):
        with open("app/data/cosmetics.json", 'r', encoding='utf-8') as file:
            cosmetics_data = json.load(file)
        
        selected_cosmetic = st.selectbox("Select Cosmetic", cosmetic_names, key="delete_ingredient_cosmetic")
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
