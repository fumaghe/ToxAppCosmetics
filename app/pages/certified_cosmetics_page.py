import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import json


st.markdown("<h1 style='text-align: center; font-size: 40px;'>Certified Cosmetics</h1>", unsafe_allow_html=True)

if os.path.exists("app/data/cosmetics.json"):
    with open("app/data/cosmetics.json", 'r', encoding='utf-8') as file:
        cosmetics_data = json.load(file)
    
    if cosmetics_data:
        # Invert the order to show the latest added cosmetics first
        cosmetics_data.reverse()

        for cosmetic in cosmetics_data:
            st.markdown(
                f"""
                <div style='margin-bottom: 10px;'>
                    <h2 style='color: #333; font-size: 27px;'>Cosmetic Name: {cosmetic['Cosmetic Name']}</h2>
                """, unsafe_allow_html=True
            )

            for ingredient in cosmetic["Ingredients"]:
                st.markdown(f"<li style='color: #555; font-size: 18px;'>{ingredient}</li>", unsafe_allow_html=True)
            
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
                    f"<div style='color: green; font-size: 20px;'><strong>Toxic: {toxicity_status} 👍</strong></div>", 
                    unsafe_allow_html=True
                )
                st.success("This cosmetic is not toxic!")
            if st.button(f"Delete {cosmetic['Cosmetic Name']}", key=f"delete_{cosmetic['Cosmetic Name']}"):
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
