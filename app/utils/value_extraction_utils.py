import re
from collections import Counter
import streamlit as st

def find_values(text, term):
    pattern = fr'{term}\s*[:/]?'
    if term == "LD50":
        pattern = fr'LD\s*[\n]*50\s*[:/]?'  # Gestisce i newline tra LD e 50
    
    matches = re.finditer(pattern, text, re.IGNORECASE)
    values = []
    for match in matches:
        start_index = match.end()
        words = text[start_index:start_index+100].split()[:20]  # Estrae 20 parole dopo il match
        for word in words:
            if re.match(r'\d+(\.\d+)?', word):  # Trova il valore numerico
                values.append((word, start_index))  # Aggiunge il valore e l'indice di inizio
                break
    return values

def display_values(common_values, pdf_text):
    if not common_values:
        st.write("No values found.")
        return

    for value, occurrences in common_values:
        with st.expander(f"Value: {value} mg/kg"):
            for i, (_, start_index) in enumerate(occurrences, 1):
                text_before = pdf_text[:start_index].split()[-20:]
                text_after = pdf_text[start_index:].split()[:20]
                surrounding_text = ' '.join(text_before + [f"<span style='color:red; font-weight:bold;'>{value}</span>"] + text_after)
                st.write(f"Occurrence {i}:")
                st.markdown(f"...{surrounding_text}...", unsafe_allow_html=True)

def find_most_common_values(values):
    if not values:
        return []
    count = Counter([v for v, _ in values])
    most_common = count.most_common(3)  # Ottiene i 3 più comuni
    common_values = []
    for value, _ in most_common:
        occurrences = [(v, idx) for v, idx in values if v == value]
        contexts = [(value, idx) for value, idx in occurrences]
        common_values.append((value, contexts))
    return common_values
