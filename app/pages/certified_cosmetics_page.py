import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import json
import os

def certified_cosmetics_page():
    st.markdown("<h1>Certified Cosmetics</h1>", unsafe_allow_html=True)
    
    if os.path.exists("app/data/cosmetics.json"):
        with open("app/data/cosmetics.json", 'r', encoding='utf-8') as file:
            cosmetics_data = json.load(file)
        
        if cosmetics_data:
            cosmetic_names = [cosmetic["Cosmetic Name"] for cosmetic in cosmetics_data]
            selected_cosmetic_name = st.selectbox("Select a Cosmetic", cosmetic_names)
            
            if selected_cosmetic_name:
                selected_cosmetic = next((cosmetic for cosmetic in cosmetics_data if cosmetic["Cosmetic Name"] == selected_cosmetic_name), None)
                
                if selected_cosmetic:
                    st.markdown(f"### Cosmetic Name: {selected_cosmetic['Cosmetic Name']}")
                    st.markdown("### Ingredients:")
                    for ingredient in selected_cosmetic["Ingredients"]:
                        st.markdown(f"- {ingredient}")
                    
                    toxicity_status = selected_cosmetic['Toxic']
                    if toxicity_status == "Yes":
                        st.markdown(f"<div style='color: red;'><strong>Toxic: {toxicity_status}</strong></div>", unsafe_allow_html=True)
                        st.error("This cosmetic is toxic!")
                    else:
                        st.markdown(f"<div style='color: green;'><strong>Toxic: {toxicity_status} 👍</strong></div>", unsafe_allow_html=True)
                        st.success("This cosmetic is not toxic!")
        else:
            st.write("No certified cosmetics found.")
    else:
        st.write("No certified cosmetics found.")
