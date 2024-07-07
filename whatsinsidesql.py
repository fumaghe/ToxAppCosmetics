import sqlite3

# Percorso al database
db_path = 'ingredients.db'

# Connetti al database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Ottieni i nomi delle tabelle
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Per ogni tabella, ottieni le colonne
for table in tables:
    table_name = table[0]
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    print(f"Table: {table_name}")
    for column in columns:
        print(f"  Column: {column[1]} - Type: {column[2]}")

# Chiudi la connessione
conn.close()
