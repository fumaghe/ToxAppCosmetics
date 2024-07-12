import sqlite3

def check_db_overview(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Totale ingredienti
    cursor.execute("SELECT COUNT(*) FROM ingredients")
    total_ingredients = cursor.fetchone()[0]

    # Controlla quanti ingredienti hanno un valore per ciascuna colonna
    columns = ["NOAEL_CIR", "LD50_CIR", "LD50_PubChem", "echa_value", "echa_dossier", "EFSA_value"]
    overview = {col: 0 for col in columns}
    for col in columns:
        cursor.execute(f"SELECT COUNT(*) FROM ingredients WHERE {col} IS NOT NULL AND {col} != '[]'")
        overview[col] = cursor.fetchone()[0]

    # Controlla quanti ingredienti hanno 0, 1, 2, 3, ... valori
    cursor.execute("""
        SELECT 
            (CASE 
                WHEN NOAEL_CIR IS NOT NULL AND NOAEL_CIR != '[]' THEN 1 ELSE 0 END) +
            (CASE 
                WHEN LD50_CIR IS NOT NULL AND LD50_CIR != '[]' THEN 1 ELSE 0 END) +
            (CASE 
                WHEN LD50_PubChem IS NOT NULL AND LD50_PubChem != '[]' THEN 1 ELSE 0 END) +
            (CASE 
                WHEN echa_value IS NOT NULL AND echa_value != '[]' THEN 1 ELSE 0 END) +
            (CASE 
                WHEN echa_dossier IS NOT NULL AND echa_dossier != '[]' THEN 1 ELSE 0 END) +
            (CASE 
                WHEN EFSA_value IS NOT NULL AND EFSA_value != '[]' THEN 1 ELSE 0 END) 
        AS num_values
        FROM ingredients
    """)
    values_count = cursor.fetchall()
    count_distribution = {i: 0 for i in range(0, 7)}
    zero_values = 0
    at_least_one_value = 0

    for count in values_count:
        count_distribution[count[0]] += 1
        if count[0] == 0:
            zero_values += 1
        else:
            at_least_one_value += 1

    conn.close()

    print(f"Total ingredients: {total_ingredients}")
    for col, count in overview.items():
        print(f"Ingredients with {col} values: {count}")
    for num_values, count in count_distribution.items():
        print(f"Ingredients with {num_values} values: {count}")
    print(f"Ingredients with zero values: {zero_values}")
    print(f"Ingredients with at least one value: {at_least_one_value}")

# Path to the database
db_path = 'ingredients.db'

# Running the check
check_db_overview(db_path)
