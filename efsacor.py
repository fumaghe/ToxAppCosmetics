import sqlite3
import pandas as pd
import re

# Carica il file CSV
efsadb_file_path = 'EFSADB.csv'
efsadb_df = pd.read_csv(efsadb_file_path, on_bad_lines='skip')

# Connetti al database SQLite
db_file_path = 'ingredients.db'
conn = sqlite3.connect(db_file_path)
cursor = conn.cursor()

# Carica la tabella ingredients
cursor.execute("SELECT * FROM ingredients")
ingredients_data = cursor.fetchall()
columns = [description[0] for description in cursor.description]
ingredients_df = pd.DataFrame(ingredients_data, columns=columns)

# Chiudi la connessione al database
conn.close()

# Funzione per trovare corrispondenze e creare il nuovo CSV
def find_matches_and_create_csv(ingredients_df, efsadb_df):
    matched_rows = []

    for name in ingredients_df['pcpc_ingredientname']:
        print(f"Cercando: {name}")
        parts = name.split()
        found = False

        while parts and not found:
            partial_name = ' '.join(parts)
            escaped_partial_name = re.escape(partial_name)
            try:
                matches = efsadb_df[efsadb_df['Substance'].str.contains(escaped_partial_name, case=False, na=False)]
                if not matches.empty:
                    matches = matches.copy()
                    matches['Ingredient'] = name
                    matched_rows.append(matches)
                    found = True
                else:
                    parts.pop()  # Rimuovi l'ultima parola e riprova
            except re.error:
                parts.pop()  # Rimuovi l'ultima parola e riprova in caso di errore di regex

    if matched_rows:
        result_df = pd.concat(matched_rows)
        result_df.to_csv('matched_ingredients.csv', index=False)

# Esegui la funzione
find_matches_and_create_csv(ingredients_df, efsadb_df)
