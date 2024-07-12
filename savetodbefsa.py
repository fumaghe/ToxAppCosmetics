import pandas as pd
import sqlite3
import json
import re

# Carica il file CSV
csv_file_path = 'DBEFSALAST.csv'
efsadb_df = pd.read_csv(csv_file_path)

# Connetti al database SQLite
db_file_path = 'ingredients.db'
conn = sqlite3.connect(db_file_path)
cursor = conn.cursor()

# Carica la tabella ingredients
ingredients_df = pd.read_sql_query("SELECT * FROM ingredients", conn)

# Verifica se la colonna EFSA_value esiste già
cursor.execute("PRAGMA table_info(ingredients)")
columns = [info[1] for info in cursor.fetchall()]
if 'EFSA_value' not in columns:
    cursor.execute("ALTER TABLE ingredients ADD COLUMN EFSA_value TEXT")

# Funzione per aggiornare il database con i valori EFSA
def update_efsa_values(ingredients_df, efsadb_df):
    for index, row in ingredients_df.iterrows():
        ingredient_name = row['pcpc_ingredientname']
        print(f"Cercando: {ingredient_name}")
        escaped_ingredient_name = re.escape(ingredient_name)
        matches = efsadb_df[efsadb_df['Ingredient'].str.contains(escaped_ingredient_name, case=False, na=False)]
        
        if not matches.empty:
            efsa_values = []
            for _, match_row in matches.iterrows():
                value = match_row['Valore']
                context = match_row['Context']
                efsa_values.append([value, [f"Type: {match_row['Type']}, Context: {context}"]])
            
            efsa_values_json = json.dumps(efsa_values)
            cursor.execute("UPDATE ingredients SET EFSA_value = ? WHERE pcpc_ingredientname = ?", (efsa_values_json, ingredient_name))
            print(f"Salvato: {ingredient_name} con EFSA_value: {efsa_values_json}")
    
    conn.commit()

# Applica la funzione per aggiornare i valori EFSA nel database
update_efsa_values(ingredients_df, efsadb_df)

# Chiudi la connessione al database
conn.close()

print("Database aggiornato con i valori EFSA.")
