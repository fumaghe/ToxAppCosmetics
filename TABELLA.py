import pandas as pd

# Path al file DATASET.txt
file_path = '/workspaces/codespaces-blank/DATASET.txt'

# Leggi il contenuto del file e convertilo in una lista di dizionari
data = []
with open(file_path, 'r') as file:
    for line in file:
        # Eval è utilizzato per valutare la stringa come un dizionario Python
        # Nota: eval può essere pericoloso se il contenuto del file non è affidabile
        data.append(eval(line.strip()))

# Crea una lista di dizionari con le colonne desiderate
table_data = []
for item in data:
    if 'pcpc_ingredientname' in item and 'pcpc_ingredientid' in item:
        table_data.append({
            'pcpc_ingredientname': item['pcpc_ingredientname'],
            'link': f"https://cir-reports.cir-safety.org/cir-ingredient-status-report/?id={item['pcpc_ingredientid']}"
        })

# Crea un DataFrame pandas dalla lista di dizionari
df = pd.DataFrame(table_data)

# Mostra la tabella
print(df)

# Salva la tabella in un file CSV (opzionale)
output_csv_path = '/workspaces/codespaces-blank/output_table.csv'
df.to_csv(output_csv_path, index=False)