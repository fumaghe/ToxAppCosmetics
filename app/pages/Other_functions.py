import streamlit as st
import pandas as pd
import sqlite3
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from io import BytesIO
from utils.findpdf import search_ingredients
from utils.findfromfoto import process_ingredients_from_csv
from utils.db_utils import load_ingredient_list

# Configura il layout di Streamlit
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
    </style>
    """,
    unsafe_allow_html=True
)

# CSS per la stilizzazione
st.markdown(
    """
    <style>
    .center-title {
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 50px;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .center-box {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 50%;
        margin: auto;
        padding: 0 20px; /* Adds spacing to the sides */
    }
    .search-box {
        text-align: center;
        font-size: 24px;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .search-result {
        width: 100%;
        font-size: 28px;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .result-buttons {
        width: 100%;
        font-size: 18px;
        margin-top: 10px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-evenly;
    }
    .stProgress > div > div > div > div {
        background-color: red;
    }
    </style>
    """, unsafe_allow_html=True
)

# Centrare il titolo
st.markdown("<h1 style='text-align: center; font-size: 50px;'>Other Functions</h1>", unsafe_allow_html=True)

# Stato per l'interruzione
if 'stop_process' not in st.session_state:
    st.session_state.stop_process = False

def stop_processing():
    st.session_state.stop_process = True

# Sezione per FindFromFoto
st.markdown("<h4>Find from Foto</h4>", unsafe_allow_html=True)

ingredients_df = pd.read_csv('app/data/Ingredients_with_missing_values.csv')
ingredients_list = ingredients_df['pcpc_ingredientname'].tolist()
selected_ingredients = st.multiselect("Select ingredients to search", ingredients_list)

if st.button('Search from Foto'):
    st.session_state.stop_process = False
    with st.spinner('Searching from Foto...'):
        process_ingredients_from_csv(selected_ingredients, st.session_state.stop_process)
    if st.session_state.stop_process:
        st.warning('Foto search interrupted.')
    else:
        st.success('Foto search completed.')

if st.button('Stop Foto Search'):
    stop_processing()

st.markdown("<hr>", unsafe_allow_html=True)

# Sezione per il download del database
st.markdown("<h4>Download Database</h4>", unsafe_allow_html=True)

if st.button('Download Database'):
    st.session_state.stop_process = False
    with st.spinner('Preparing download...'):
        db_path = 'app/data/ingredients.db'
        conn = sqlite3.connect(db_path)
        conn.close()
        with open(db_path, 'rb') as f:
            st.download_button(label="Download ingredients.db", data=f, file_name="ingredients.db", mime='application/octet-stream')
    if st.session_state.stop_process:
        st.warning('Database download interrupted.')
    else:
        st.success('Database download completed.')

if st.button('Stop Database Download'):
    stop_processing()

st.markdown("<hr>", unsafe_allow_html=True)

# Sezione per creare e scaricare un file dalle colonne selezionate
st.markdown("<h4>Create and Download File</h4>", unsafe_allow_html=True)

# Elenco delle colonne disponibili, inclusa EFSA_value
columns = [
    'pcpc_ingredientid', 
    'pcpc_ingredientname', 
    'NOAEL_CIR', 
    'LD50_CIR', 
    'LD50_PubChem', 
    'value_updated', 
    'cir_page', 
    'cir_pdf', 
    'pubchem_page', 
    'echa_value', 
    'echa_dossier', 
    'EFSA_value'  # Aggiungi la colonna EFSA_value
]

# Selettore di colonne
selected_columns = st.multiselect("Select columns to include in the file", columns, key="columns_multiselect")

# Selettore di ingredienti condizionato
if 'pcpc_ingredientname' in selected_columns:
    ingredient_options = load_ingredient_list()
    selected_specific_ingredients = st.multiselect("Select specific ingredients (optional)", ingredient_options, key="ingredients_multiselect")

# Selettore di formato file
file_format = st.selectbox("Select file format", ["CSV", "TXT", "JSON", "PDF"], key="file_format_select")

def extract_values(data):
    try:
        data_list = eval(data)
        if isinstance(data_list, list):
            return ', '.join([item[0] for item in data_list if isinstance(item, list)])
    except:
        return data
    return data

def create_pdf(df):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 40  # Margine per il testo

    # Aggiungi font League Spartan
    font_path = os.path.join(os.path.dirname(__file__), '..', 'static/fonts', 'LeagueSpartan-Regular.ttf')
    bold_font_path = os.path.join(os.path.dirname(__file__), '..', 'static/fonts', 'LeagueSpartan-Bold.ttf')
    pdfmetrics.registerFont(TTFont('LeagueSpartan', font_path))
    pdfmetrics.registerFont(TTFont('LeagueSpartan-Bold', bold_font_path))
    c.setFont("LeagueSpartan", 10)
    
    # Aggiungi logo
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'LOGOTOXAPP.png')
    if os.path.exists(logo_path):
        c.drawImage(logo_path, margin, height - margin - 50, width=50, preserveAspectRatio=True, mask='auto')
    
    # Aggiungi titolo centrato
    c.setFont("LeagueSpartan-Bold", 36)
    c.drawCentredString(width / 2.0, height - margin - 50, "ToxApp PDF")
    c.setFont("LeagueSpartan", 10)
    
    y = height - margin - 100
    
    for index, row in df.iterrows():
        ingredient_name = row['pcpc_ingredientname']
        c.setFillColor(colors.red)
        c.setFont("LeagueSpartan-Bold", 12)
        c.drawString(margin, y, ingredient_name)
        c.setFillColor(colors.black)
        c.setFont("LeagueSpartan", 10)
        y -= 15
        
        for col in df.columns:
            if col == 'pcpc_ingredientname':
                continue
            c.setFont("LeagueSpartan-Bold", 10)
            text = f"{col}:"
            c.drawString(margin, y, text)
            c.setFont("LeagueSpartan", 10)
            text = extract_values(row[col])
            lines = simpleSplit(text, "LeagueSpartan", 10, width - 2*margin - 50)  # Divide il testo in righe
            for line in lines:
                c.drawString(margin + 100, y, line)  # Aggiungi più margine a sinistra
                y -= 15
                if y < margin:
                    c.showPage()
                    if os.path.exists(logo_path):
                        c.drawImage(logo_path, margin, height - margin - 50, width=50, preserveAspectRatio=True, mask='auto')
                    c.setFont("LeagueSpartan-Bold", 36)
                    c.drawCentredString(width / 2.0, height - margin - 50, "ToxApp PDF")
                    c.setFont("LeagueSpartan", 10)
                    y = height - margin - 100
            y -= 15  # Spazio tra i campi
        c.line(margin, y, width - margin, y)  # Aggiungi linea di separazione
        y -= 15
        if y < margin:
            c.showPage()
            if os.path.exists(logo_path):
                c.drawImage(logo_path, margin, height - margin - 50, width=50, preserveAspectRatio=True, mask='auto')
            c.setFont("LeagueSpartan-Bold", 36)
            c.drawCentredString(width / 2.0, height - margin - 50, "ToxApp PDF")
            c.setFont("LeagueSpartan", 10)
            y = height - margin - 100
    
    c.save()
    buffer.seek(0)
    return buffer

if st.button('Create File'):
    if selected_columns:
        with st.spinner('Creating file...'):
            # Connettersi al database e recuperare i dati
            conn = sqlite3.connect('app/data/ingredients.db')
            if 'pcpc_ingredientname' in selected_columns and selected_specific_ingredients:
                placeholders = ', '.join('?' for _ in selected_specific_ingredients)
                query = f"SELECT {', '.join(selected_columns)} FROM ingredients WHERE pcpc_ingredientname IN ({placeholders})"
                df = pd.read_sql_query(query, conn, params=selected_specific_ingredients)
            else:
                query = f"SELECT {', '.join(selected_columns)} FROM ingredients"
                df = pd.read_sql_query(query, conn)
            conn.close()

            # Estrai solo i valori numerici dai dati strutturati
            for col in selected_columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].apply(extract_values)

            if file_format == "CSV":
                # Creare il file CSV
                file_data = df.to_csv(index=False, encoding='utf-8-sig')
                mime = 'text/csv'
                file_name = "ingredients.csv"
            elif file_format == "TXT":
                # Creare il file TXT
                file_data = df.to_csv(index=False, sep='\t', encoding='utf-8-sig')
                mime = 'text/plain'
                file_name = "ingredients.txt"
            elif file_format == "JSON":
                # Creare il file JSON
                file_data = df.to_json(orient='records')
                mime = 'application/json'
                file_name = "ingredients.json"
            elif file_format == "PDF":
                # Creare il file PDF
                pdf = create_pdf(df)
                file_data = pdf.getvalue()
                mime = 'application/pdf'
                file_name = "ingredients.pdf"
            
            # Pulsante per scaricare il file
            st.download_button(label=f"Download {file_format}", data=file_data, file_name=file_name, mime=mime)
        st.success(f'{file_format} created successfully.')
    else:
        st.warning('Please select at least one column.')

st.markdown("<hr>", unsafe_allow_html=True)

# Sezione per FindPDF
st.markdown("<h4>Find PDF</h4>", unsafe_allow_html=True)

num_ingredients_pdf = st.number_input("Number of ingredients to search", min_value=1, value=10, step=1, key="num_ingredients_pdf")
start_index_pdf = st.number_input("Starting index", min_value=0, value=0, step=1, key="start_index_pdf")

if st.button('Search PDFs', key="search_pdfs_button"):
    st.session_state.stop_process = False
    with st.spinner('Searching PDFs...'):
        search_ingredients(start_index_pdf, start_index_pdf + num_ingredients_pdf, st.session_state.stop_process)
    if st.session_state.stop_process:
        st.warning('PDF search interrupted.')
    else:
        st.success('PDF search completed.')

if st.button('Stop PDF Search', key="stop_pdf_search_button"):
    stop_processing()
