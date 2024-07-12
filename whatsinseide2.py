import sqlite3
import json

def mostra_primi_due_ingredienti():
    # Connetti al database
    conn = sqlite3.connect('ingredients.db')
    cursor = conn.cursor()

    # Esegui una query per ottenere i dati degli ingredienti
    cursor.execute("SELECT pcpc_ingredientid, pcpc_ingredientname, NOAEL_CIR, LD50_CIR, LD50_PubChem, echa_value, echa_dossier, EFSA_value FROM ingredients LIMIT 2")
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
        print(f"ECHA Dossier: {row[6]}")
        print(f"EFSA Value: {json.loads(row[7]) if row[7] else 'N/A'}")
        print("-" * 40)

def conta_ingredienti_con_valore_efsa():
    # Connetti al database
    conn = sqlite3.connect('ingredients.db')
    cursor = conn.cursor()

    # Esegui una query per contare gli ingredienti con un valore EFSA_value
    cursor.execute("SELECT COUNT(*) FROM ingredients WHERE EFSA_value IS NOT NULL AND EFSA_value != '[]'")
    count = cursor.fetchone()[0]

    # Chiudi la connessione al database
    conn.close()

    print(f"Numero di ingredienti con un valore EFSA_value: {count}")

# Chiama le funzioni
mostra_primi_due_ingredienti()
conta_ingredienti_con_valore_efsa()
