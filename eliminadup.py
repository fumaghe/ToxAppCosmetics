import pandas as pd

# Carica il file CSV
matched_file_path = 'matched_ingredients.csv'
matched_df = pd.read_csv(matched_file_path)

# Verifica i nomi delle colonne
print(matched_df.columns)

# Funzione per mantenere la riga più recente basata su 'Type' e 'Context' per ogni 'Ingredient'
def keep_most_recent(matched_df):
    # Estrai l'anno e i dettagli del contesto da 'Context'
    matched_df[['Year', 'Context_Detail']] = matched_df['Context'].str.extract(r'(\d{4})\s*(.*)', expand=True)
    
    # Converte 'Year' in intero
    matched_df['Year'] = matched_df['Year'].astype(int)
    
    # Ordina il dataframe per 'Ingredient', 'Type', 'Context_Detail' e 'Year'
    matched_df = matched_df.sort_values(by=['Ingredient', 'Type', 'Context_Detail', 'Year'], ascending=[True, True, True, False])
    
    # Elimina i duplicati mantenendo l'anno più recente
    cleaned_df = matched_df.drop_duplicates(subset=['Ingredient', 'Type', 'Context_Detail'], keep='first')
    
    # Elimina le colonne temporanee utilizzate per l'elaborazione
    cleaned_df = cleaned_df.drop(columns=['Year', 'Context_Detail'])
    
    return cleaned_df

# Applica la funzione per mantenere le voci più recenti
cleaned_df = keep_most_recent(matched_df)

# Visualizza il dataframe pulito
print(cleaned_df.head())

# Salva il dataframe pulito in un nuovo file CSV
cleaned_file_path = 'most_recent_matched_ingredients.csv'
cleaned_df.to_csv(cleaned_file_path, index=False)

print(f"Cleaned data saved to {cleaned_file_path}")
