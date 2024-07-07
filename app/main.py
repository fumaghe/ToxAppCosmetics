import streamlit as st
from app.pages import main_page, toxicity_calculator_page, certified_cosmetics_page, dataset_page

# Sidebar menu
st.sidebar.title("Menu")
page = st.sidebar.radio("Navigation", ("Home", "Toxicity Calculator", "Certified Cosmetics", "Dataset"))

if page == "Home":
    main_page.show()
elif page == "Toxicity Calculator":
    toxicity_calculator_page.show()
elif page == "Certified Cosmetics":
    certified_cosmetics_page.show()
elif page == "Dataset":
    dataset_page.show()
