import sqlite3
import json

def mostra_primi_due_ingredienti():
    # Connetti al database
    conn = sqlite3.connect('ingredients.db')
    cursor = conn.cursor()

    # Esegui una query per ottenere i dati degli ingredienti
    cursor.execute("SELECT pcpc_ingredientid, pcpc_ingredientname, NOAEL_CIR, LD50_CIR, LD50_PubChem, echa_value, echa_dossier FROM ingredients LIMIT 2")
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
        print(f"ECHA Value: {json.loads(row[5]) if row[5] else 'N/A'}")
        print(f"ECHA Dossier: {row[6] if row[6] else 'N/A'}")
        print("-" * 40)

# Chiama la funzione per mostrare i dati
mostra_primi_due_ingredienti()
