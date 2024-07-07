import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from app.pages.main_page import main_page
from app.pages.toxicity_calculator_page import toxicity_calculator_page
from app.pages.certified_cosmetics_page import certified_cosmetics_page
from app.pages.dataset_page import dataset_page

# Set the page configuration
st.set_page_config(layout="wide", page_title="CosmeticToxicity", page_icon="🧴")

# Custom CSS for styling
with open("app/static/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Sidebar menu
st.sidebar.title("Menu")
page = st.sidebar.radio("Navigation", ("Home", "Toxicity Calculator", "Certified Cosmetics", "Dataset"))

if page == "Home":
    main_page()
elif page == "Toxicity Calculator":
    toxicity_calculator_page()
elif page == "Certified Cosmetics":
    certified_cosmetics_page()
elif page == "Dataset":
    dataset_page()
