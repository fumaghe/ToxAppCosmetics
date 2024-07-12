import sqlite3

def sostituisci_none_con_array_vuoto():
    # Connetti al database
    conn = sqlite3.connect('ingredients.db')
    cursor = conn.cursor()

    # Esegui una query per ottenere gli ingredienti con EFSA_value uguale a None
    cursor.execute("SELECT pcpc_ingredientname FROM ingredients WHERE EFSA_value IS NULL")
    rows = cursor.fetchall()

    # Sostituisci None con '[]'
    for row in rows:
        ingredient_name = row[0]
        cursor.execute("UPDATE ingredients SET EFSA_value = '[]' WHERE pcpc_ingredientname = ?", (ingredient_name,))

    # Conferma le modifiche
    conn.commit()
    conn.close()

    print(f"Sostituiti i valori None con '[]' per {len(rows)} ingredienti")

# Esegui la funzione di sostituzione
sostituisci_none_con_array_vuoto()
