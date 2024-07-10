import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager


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
    .section-title {
        color: #333;
        font-size: 27px;
        margin-top: 40px;
    }
    .toxicity-yes {
        background-color: #ffcccc !important;
    }
    .toxicity-no {
        background-color: #ccffcc !important;
    }
    table.dataframe {
        width: auto;
        table-layout: fixed;
    }
    table.dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
    table.dataframe tbody tr th {
        vertical-align: top;
    }
    table.dataframe thead th {
        position: -webkit-sticky; /* for Safari */
        position: sticky;
        top: 0;
        background-color: #f1f1f1;
        z-index: 1;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<h1 style='text-align: center; font-size: 50px;'>Cosmetic Statistics</h1>", unsafe_allow_html=True)

if os.path.exists("app/data/cosmetics.json"):
    try:
        with open("app/data/cosmetics.json", 'r', encoding='utf-8') as file:
            cosmetics_data = json.load(file)
    except json.JSONDecodeError:
        st.error("Error loading cosmetics data. The file might be empty or corrupted.")
        cosmetics_data = []

    if cosmetics_data:
        df = pd.DataFrame(cosmetics_data)

        if 'Company Name' not in df.columns:
            st.error("The data does not contain the 'Company Name' field.")
        else:
            # Filter by toxicity
            st.markdown("<h2 class='section-title'>Filter by Toxicity</h2>", unsafe_allow_html=True)
            toxicity_filter = st.radio("Select Toxicity", ('All', 'Yes', 'No'))
            if toxicity_filter != 'All':
                df = df[df['Toxic'] == toxicity_filter]

            st.markdown("<h2 class='section-title'>Cosmetics Data</h2>", unsafe_allow_html=True)
            def color_toxicity(val):
                color = '#ffcccc' if val == 'Yes' else '#ccffcc'
                return f'background-color: {color}'

            styled_df = df.style.applymap(color_toxicity, subset=['Toxic']).set_properties(**{'text-align': 'left'})
            st.dataframe(styled_df)

            st.markdown("<h2 class='section-title'>Toxic vs Non-Toxic Cosmetics</h2>", unsafe_allow_html=True)
            toxicity_counts = df['Toxic'].value_counts().reset_index()
            toxicity_counts.columns = ['Toxic', 'Count']
            fig, ax = plt.subplots()
            colors = ['#ff6666', '#66ff66']
            bars = ax.bar(toxicity_counts['Toxic'], toxicity_counts['Count'], color=colors)
            for bar, color in zip(bars, colors):
                height = bar.get_height()
                text_color = '#ff9999' if color == '#ff6666' else '#99ff99'
                ax.annotate(f'{height}',
                            xy=(bar.get_x() + bar.get_width() / 2, 0),
                            ha='center', va='bottom', fontsize=50, color=text_color, weight='bold')
            st.pyplot(fig)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Most Common Ingredients")
                common_ingredients = df.explode('Ingredients')['Ingredients'].value_counts().reset_index()
                common_ingredients.columns = ['Ingredient Name', 'Count']
                st.dataframe(common_ingredients.head(10))

            with col2:
                st.markdown("### Cosmetics by Company")
                companies = df['Company Name'].value_counts().reset_index()
                companies.columns = ['Company Name', 'Number of Cosmetics']
                st.dataframe(companies)

            # Toxicity of Ingredients
            toxic_ingredients = df.explode('Ingredients')[['Ingredients', 'Toxic']]
            toxic_ingredients['Ingredient Name'] = toxic_ingredients['Ingredients'].str.split(' - ').str[0]
            ingredient_toxicity_counts = toxic_ingredients.groupby(['Ingredient Name', 'Toxic']).size().unstack().fillna(0)

            if 'No' in ingredient_toxicity_counts.columns and 'Yes' in ingredient_toxicity_counts.columns:
                st.markdown("<h2 class='section-title'>Least Toxic and Most Toxic Ingredients</h2>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### Least Toxic Ingredients")
                    least_toxic = ingredient_toxicity_counts[ingredient_toxicity_counts['No'] > 0].sort_values('No', ascending=False)
                    st.dataframe(least_toxic.head(10))

                with col2:
                    st.markdown("### Most Toxic Ingredients")
                    most_toxic = ingredient_toxicity_counts[ingredient_toxicity_counts['Yes'] > 0].sort_values('Yes', ascending=False)
                    st.dataframe(most_toxic.head(10))
            else:
                st.error("Not enough data to determine least toxic and most toxic ingredients.")

            st.markdown("<h2 class='section-title'>Filter by Company</h2>", unsafe_allow_html=True)
            selected_company = st.selectbox("Select Company", df['Company Name'].unique())
            filtered_data = df[df['Company Name'] == selected_company]
            st.dataframe(filtered_data)

            if st.button("Reload Data"):
                st.experimental_rerun()
    
    else:
        st.write("No cosmetic data available.")
else:
    st.write("No cosmetic data available.")
