import requests

query_string = "par"  
url1 = "https://cir-reports.cir-safety.org/FetchCIRReports?" + query_string
response1 = requests.get(url1)
data1 = response1.json()
records = data1.get('results', [])
more_records = data1.get('morerecords', False)

# Se ci sono più record disponibili, richiedi i dati aggiuntivi
if more_records:
    page = 2
    while more_records:
        url_next_page = "https://cir-reports.cir-safety.org/FetchCIRReports?" + query_string + f"&part2=true&page={page}"
        response_next_page = requests.get(url_next_page)
        data_next_page = response_next_page.json()
        records += data_next_page.get('results', [])
        more_records = data_next_page.get('morerecords', False)
        page += 1

# Path per il file di output
output_htmlcompleto = r"C:\Users\AndreaFumagalli\OneDrive - ITS Angelo Rizzoli\Desktop\Project Work\JSON DATASET1.0.txt"

# Salva i risultati in un file di testo
with open(output_htmlcompleto, 'w', encoding='utf-8') as file:
    for record in records:
        lowercase_record = {key.lower(): value.lower() if isinstance(value, str) else value for key, value in record.items()}
        file.write(str(lowercase_record) + '\n')

print(f"I dati sono stati salvati con successo in {output_htmlcompleto}")

