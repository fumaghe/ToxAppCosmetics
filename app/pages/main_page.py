import streamlit as st
from app.utils.db_utils import load_ingredient_list, find_ingredient_id_and_extract_link, update_search_history

def main_page():
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        st.image("app/static/Toxic.png", use_column_width=True)
        
    ingredient_list = load_ingredient_list()

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h3 style='text-align: center;'>Search for an ingredient</h3>", unsafe_allow_html=True)
        ingredient_name = st.selectbox("", ingredient_list)
    
    st.markdown("<hr>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([0.2, 13, 0.2])

    with col2:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h2>Search Result</h2>", unsafe_allow_html=True)
        if ingredient_name:
            find_ingredient_id_and_extract_link(ingredient_name)

    col1, col2, col3 = st.columns([8, 4, 8])
    with col2:
        update_search_history(ingredient_name)
        st.markdown("</div>", unsafe_allow_html=True)
