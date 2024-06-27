import requests
from bs4 import BeautifulSoup
import csv
import ast

# Leggi il file DATASET.txt e ottieni la lista degli ingredienti
with open('/workspaces/codespaces-blank/DATASET.txt', 'r') as file:
    lines = file.readlines()
    ingredienti = [ast.literal_eval(line.strip()) for line in lines]

# Base URL del sito
base_url = "https://cosmileeurope.eu/it/inci/"

# Apri il file CSV per scrivere i risultati
with open('ingredienti_info.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Ingrediente', 'Contenuto']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for ingrediente in ingredienti:
        ingredient_name = ingrediente['pcpc_ingredientname']
        ingredient_id = ingrediente['pcpc_ingredientid']
        try:
            # Costruisci l'URL della pagina dell'ingrediente
            ingredient_url = f"{base_url}{ingredient_id}"
            response = requests.get(ingredient_url)
            response.raise_for_status()

            # Analizza il contenuto della pagina dell'ingrediente
            soup = BeautifulSoup(response.content, 'html.parser')
            content = soup.get_text()

            # Scrivi il contenuto nel file CSV
            writer.writerow({'Ingrediente': ingredient_name, 'Contenuto': content})
        except requests.RequestException as e:
            # Gestisci eventuali errori di rete o richieste
            writer.writerow({'Ingrediente': ingredient_name, 'Contenuto': 'Ingredient not found'})
            print(f"Errore nella richiesta per l'ingrediente {ingredient_name}: {e}")

print("Processo completato.")