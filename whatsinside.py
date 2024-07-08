import sqlite3

def verify_ingredients():
    conn = sqlite3.connect('ingredients.db')
    cursor = conn.cursor()
    cursor.execute("SELECT pcpc_ingredientid, pcpc_ingredientname, cir_page, cir_pdf, pubchem_page FROM ingredients LIMIT 41")
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        print(f"Ingredient ID: {row[0]}")
        print(f"Ingredient Name: {row[1]}")
        print(f"CIR Page: {row[2]}")
        print(f"CIR PDF: {row[3]}")
        print(f"PubChem Page: {row[4]}")
        print("-" * 40)

verify_ingredients()
