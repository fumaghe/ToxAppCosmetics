import streamlit as st
import pandas as pd
import re
from app.utils.db_utils import update_database

def dataset_page():
    csv_file_path = 'app/data/output_table.csv'

    col1, col2 = st.columns([5, 5])

    with col1:
        st.markdown("<h1>Dataset</h1>", unsafe_allow_html=True)
        
        data = pd.read_csv(csv_file_path)
        data = data.rename(columns={'pcpc_ingredientname': 'Ingredient', 'link': 'Website'})

        st.markdown("<h2>Select an ingredient</h2>", unsafe_allow_html=True)
        ingredient_name = st.selectbox("", data['Ingredient'].tolist())
        
        selected_ingredient = data[data['Ingredient'] == ingredient_name]
        if not selected_ingredient.empty:
            website_link = selected_ingredient['Website'].values[0]
            st.markdown(f"[Link to selected ingredient]({website_link})")

    if st.button("Update Database"):
        update_database()
    st.markdown("<p>Click to update the database. This operation may take a few seconds.</p>", unsafe_allow_html=True)

    alphabet = ['1'] + list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    selected_letter = st.radio('', alphabet, horizontal=True)

    if selected_letter == '1':
        filtered_data = data[data['Ingredient'].apply(lambda x: re.match(r'^\d', x) is not None)]
    else:
        filtered_data = data[data['Ingredient'].str.startswith(selected_letter, na=False)]

    st.table(filtered_data[['Ingredient', 'Website']])
