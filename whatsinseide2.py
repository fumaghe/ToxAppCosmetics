import sqlite3
import json

# Connetti al database
conn = sqlite3.connect('ingredients.db')
cursor = conn.cursor()

# Esegui una query per ottenere i dati degli ingredienti
cursor.execute("SELECT pcpc_ingredientid, pcpc_ingredientname, NOAEL_CIR, LD50_CIR, LD50_PubChem FROM ingredients LIMIT 1")
rows = cursor.fetchall()

# Chiudi la connessione al database
conn.close()

# Stampa i dati in un formato leggibile
for row in rows:
    print(f"Ingredient ID: {row[0]}")
    print(f"Ingredient Name: {row[1]}")
    print(f"NOAEL_CIR: {json.loads(row[2]) if row[2] else 'N/A'}")
    print(f"LD50_CIR: {json.loads(row[3]) if row[3] else 'N/A'}")
    print(f"LD50_PubChem: {json.loads(row[4]) if row[4] else 'N/A'}")
    print("-" * 40)
