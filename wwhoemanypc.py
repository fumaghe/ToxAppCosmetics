import sqlite3

def check_ld50_pubchem_values(db_path, num_ingredients):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT LD50_PubChem FROM ingredients LIMIT ?", (num_ingredients,))
    ingredients = cursor.fetchall()
    conn.close()

    total_ingredients = len(ingredients)
    with_values = sum(1 for ingredient in ingredients if ingredient[0] not in [None, '[]'])

    print(f"Total ingredients checked: {total_ingredients}")
    print(f"Ingredients with LD50_PubChem values: {with_values}")
    print(f"Ingredients without LD50_PubChem values: {total_ingredients - with_values}")

# Path to the database
db_path = 'ingredients.db'

# Number of ingredients to check
num_ingredients_to_check = 6056

# Running the check
check_ld50_pubchem_values(db_path, num_ingredients_to_check)
