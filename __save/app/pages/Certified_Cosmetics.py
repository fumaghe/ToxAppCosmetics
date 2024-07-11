import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import json

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

st.markdown("<h1 style='text-align: center; font-size: 50px;'>Certified Cosmetics</h1>", unsafe_allow_html=True)

# Search bars for filtering
cosmetic_name_search = st.text_input("Search by Cosmetic Name")
company_name_search = st.text_input("Search by Company Name")

if st.button("Clear Filters"):
    cosmetic_name_search = ""
    company_name_search = ""

st.markdown("<hr>", unsafe_allow_html=True)
if os.path.exists("app/data/cosmetics.json"):
    try:
        with open("app/data/cosmetics.json", 'r', encoding='utf-8') as file:
            cosmetics_data = json.load(file)
    except json.JSONDecodeError:
        st.error("Error loading cosmetics data. The file might be empty or corrupted.")
        cosmetics_data = []

    if cosmetics_data:
        # Apply filters
        if cosmetic_name_search:
            cosmetics_data = [cosmetic for cosmetic in cosmetics_data if cosmetic_name_search.lower() in cosmetic['Cosmetic Name'].lower()]
        if company_name_search:
            cosmetics_data = [cosmetic for cosmetic in cosmetics_data if company_name_search.lower() in cosmetic['Company Name'].lower()]

        cosmetics_data.reverse()

        for index, cosmetic in enumerate(cosmetics_data):
            company_name = cosmetic.get('Company Name', 'Unknown')
            st.markdown(
                f"""
                <div style='margin-bottom: 10px;'>
                    <h2 font-size: 27px;'>Cosmetic Name: {cosmetic['Cosmetic Name']}</h2>
                    <h4 font-size: 22px;'>Company Name: {company_name}</h4>
                """, unsafe_allow_html=True
            )

            for ingredient in cosmetic["Ingredients"]:
                st.markdown(f"<li font-size: 18px;'>{ingredient}</li>", unsafe_allow_html=True)
            
            st.markdown("</ul>", unsafe_allow_html=True)

            toxicity_status = cosmetic['Toxic']
            if toxicity_status == "Yes":
                st.markdown(
                    f"<div style='color: red; font-size: 20px;'><strong>Toxic: {toxicity_status}</strong></div>", 
                    unsafe_allow_html=True
                )
                st.error("This cosmetic is toxic!")
            else:
                st.markdown(
                    f"<div style='color: green; font-size: 20px;'><strong>Toxic: {toxicity_status}</strong></div>", 
                    unsafe_allow_html=True
                )
                st.success("This cosmetic is not toxic!")
            if st.button(f"Delete {cosmetic['Cosmetic Name']}", key=f"delete_{cosmetic['Cosmetic Name']}_{index}"):
                cosmetics_data = [c for c in cosmetics_data if c["Cosmetic Name"] != cosmetic["Cosmetic Name"]]
                with open("app/data/cosmetics.json", 'w', encoding='utf-8') as file:
                    json.dump(cosmetics_data, file, indent=4)
                st.success(f"Deleted {cosmetic['Cosmetic Name']}")
                st.experimental_rerun()
            st.markdown("<hr>", unsafe_allow_html=True)

        if st.button("Delete All Cosmetics"):
            cosmetics_data = []
            with open("app/data/cosmetics.json", 'w', encoding='utf-8') as file:
                json.dump(cosmetics_data, file, indent=4)
            st.success("Deleted all cosmetics")
            st.experimental_rerun()
    else:
        st.write("No certified cosmetics found.")
else:
    st.write("No certified cosmetics found.")
