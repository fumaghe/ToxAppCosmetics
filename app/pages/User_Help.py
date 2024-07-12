import streamlit as st
import pandas as pd
import os
from streamlit_star_rating import st_star_rating

st.set_page_config(layout="wide")


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
    .star-rating-label {
        font-family: 'League Spartan', sans-serif;
        font-size: 14px;
    }
    .st-star-rating .star {
        color: red !important;
        font-size: 20px !important;
    }
    .hidden-label {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def save_message(name, page, details, file_path='user_messages.csv'):
    new_message = pd.DataFrame({
        'Name': [name],
        'Page': [page],
        'Details': [details]
    })
    
    if os.path.exists(file_path):
        messages_df = pd.read_csv(file_path)
        messages_df = pd.concat([messages_df, new_message], ignore_index=True)
    else:
        messages_df = new_message

    messages_df.to_csv(file_path, index=False)

def save_review(name, rating, review, file_path='reviews.csv'):
    new_review = pd.DataFrame({
        'Name': [name],
        'Rating': [rating],
        'Review': [review]
    })
    
    if os.path.exists(file_path):
        reviews_df = pd.read_csv(file_path)
        reviews_df = pd.concat([reviews_df, new_review], ignore_index=True)
    else:
        reviews_df = new_review

    reviews_df.to_csv(file_path, index=False)

st.markdown("<h1 style='text-align: center;'>Help/Contacts</h1>", unsafe_allow_html=True)

st.markdown("If you have any suggestions or issues with any page, please contact me at [andrea.fumagalli@itsrizzoli.it](mailto:andrea.fumagalli@itsrizzoli.it).")

user_name = st.text_input("Your Name")

page_options = ["Home", "Certified Cosmetics", "Create Cosmetic", "Dataset", "Ingredient Information", "Other Functions", "Stats"]
selected_page = st.selectbox("Select the page you are having issues with", page_options)

problem_details = st.text_area("Describe the issue you are experiencing")

if st.button("Send Message"):
    if user_name and selected_page and problem_details:
        save_message(user_name, selected_page, problem_details)
        st.success("Message saved successfully!")
    else:
        st.warning("Please enter your name, select a page, and describe the issue.")

st.markdown("<hr>", unsafe_allow_html=True)

st.markdown("<h4>Submit a Review</h4>", unsafe_allow_html=True)

reviewer_name = st.text_input("Your Name (for review)")

rating = st_star_rating(label='Rate us (1 to 5 stars)', maxValue=5, defaultValue=5, key='star_rating')

review_message = st.text_area("Your Review (optional)")

if st.button("Submit Review"):
    if reviewer_name and rating:
        save_review(reviewer_name, rating, review_message)
        st.success("Review submitted successfully!")
    else:
        st.warning("Please enter your name and rate us.")

st.markdown("<hr>", unsafe_allow_html=True)
