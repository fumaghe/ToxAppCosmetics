import requests
from bs4 import BeautifulSoup
import re
import pdfplumber
import io
import re
import pdfminer.high_level

# Funzione per estrarre il primo link dello status report da una pagina URL
def extract_first_status_link(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        status_link = soup.find('table').find_all('tr')[1].find('a')['href']
        full_status_link = "https://cir-reports.cir-safety.org/" + status_link.replace("../", "")
        return full_status_link
    except requests.RequestException as e:
        print(f"Error accessing {url}: {e}")
    except (IndexError, TypeError) as e:
        print(f"Error parsing the page: {e}")

# Funzione per estrarre il testo da un PDF usando pdfplumber
def extract_text_from_pdf(pdf_content):
    with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

# Funzione per trovare i valori NOAEL nel testo
def find_noael_values(text):
    pattern = r'NOAEL\s*[:/]?'
    matches = re.finditer(pattern, text, re.IGNORECASE)
    values = []
    for match in matches:
        start_index = match.end()
        words = text[start_index:start_index+100].split()[:20]
        for word in words:
            if re.match(r'\d+(\.\d+)?', word):
                values.append(word)
                break
    return values

# Funzione per trovare i valori LD50 nel testo con espressione regolare migliorata
def find_ld50_values(text):
    pattern = r'LD\s*5[0O]\s*[:/]?|LD\s*₅\d\s*[:/]?|LD\s*5\d\s*[:/]?|LD\s*5[0O]\s*mg\/kg|LD\s*₅\d\s*mg\/kg|LD\s*5\d\s*mg\/kg|LD\s*5[0O]\s*mg/kg|LD\s*₅\d\s*mg/kg|LD\s*5\d\s*mg/kg'
    matches = re.finditer(pattern, text, re.IGNORECASE)
    values = []

    for match in matches:
        start_index = match.end()
        words = text[start_index:start_index+100].split()[:20]

        for word in words:
            if re.match(r'\d+(\.\d+)?', word):
                values.append(word)
                break

    return values

# Funzione per trovare il valore più comune in una lista di valori
def find_most_common_value(values):
    if not values:
        return None, 0
    count = Counter(values)
    most_common_value, most_common_count = count.most_common(1)[0]
    return most_common_value, most_common_count

# Funzione per scrivere i valori trovati nel file
def check_and_append_values(ingredient_id, most_common_value, other_values, value_type, file_path):
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(f"{ingredient_id}:most_common_{value_type}:{most_common_value}\n")
        if other_values:
            file.write(f"{ingredient_id}:other_{value_type}:{','.join(map(str, other_values))}\n")

# Funzione principale per trovare l'ID dell'ingrediente e estrarre i valori dal PDF
def find_ingredient_id_and_extract_link(ingredient_name, data_file_path, value_file_path):
    value_dict = {}
    with open(value_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if ':' in line:
                id_value_pair = line.strip().split(':')
                if len(id_value_pair) == 3:
                    id_key = id_value_pair[0]
                    if id_key not in value_dict:
                        value_dict[id_key] = {}
                    value_dict[id_key][id_value_pair[1]] = id_value_pair[2].split(',')

    with open(data_file_path, 'r', encoding='utf-8') as file:
        ingredients = []
        for line in file:
            data = eval(line.strip())
            search_name = ingredient_name.lower()
            if (search_name in data['pcpc_ingredientname'].lower() or
                search_name in data['pcpc_ciringredientname'].lower()):
                ingredients.append((data['pcpc_ingredientname'], data['pcpc_ingredientid']))

    if ingredients:
        for ingredient_name, ingredient_id in set(ingredients):
            if ingredient_id in value_dict:
                print(f"Ingredient name: {ingredient_name}")
                most_common_noael = value_dict[ingredient_id].get('most_common_NOAEL', ['N/A'])[0]
                other_noael_values = value_dict[ingredient_id].get('other_NOAEL', [])
                most_common_ld50 = value_dict[ingredient_id].get('most_common_LD50', ['N/A'])[0]
                other_ld50_values = value_dict[ingredient_id].get('other_LD50', [])
                
                print(f"Most common NOAEL: {most_common_noael} mg/kg")
                for value in other_noael_values:
                    print(f"Other NOAEL value: {value}")

                print(f"Most common LD50: {most_common_ld50} mg/kg")
                for value in other_ld50_values:
                    print(f"Other LD50 value: {value}")
            else:
                url = f"https://cir-reports.cir-safety.org/cir-ingredient-status-report/?id={ingredient_id}"
                status_link = extract_first_status_link(url)
                if status_link:
                    try:
                        response = requests.get(status_link)
                        response.raise_for_status()
                        
                        pdf_text = extract_text_from_pdf(response.content)
                        print(f"Extracted text from PDF:\n{pdf_text}\n")  # Debug: Print extracted text
                        
                        noael_values = find_noael_values(pdf_text)
                        most_common_noael, _ = find_most_common_value(noael_values)
                        
                        if noael_values:
                            other_noael_values = set(noael_values)
                            other_noael_values.discard(most_common_noael)
                            
                            print(f"Ingredient name: {ingredient_name}")
                            print(f"Most common NOAEL: {most_common_noael} mg/kg")
                            for value in other_noael_values:
                                print(f"Other NOAEL value: {value}")

                            check_and_append_values(ingredient_id, most_common_noael, list(other_noael_values), 'NOAEL', value_file_path)
                        else:
                            ld50_values = find_ld50_values(pdf_text)
                            most_common_ld50, _ = find_most_common_value(ld50_values)
                            
                            if ld50_values:
                                other_ld50_values = set(ld50_values)
                                other_ld50_values.discard(most_common_ld50)
                                
                                print(f"Ingredient name: {ingredient_name}")
                                print(f"Most common LD50: {most_common_ld50} mg/kg")
                                for value in other_ld50_values:
                                    print(f"Other LD50 value: {value}")

                                check_and_append_values(ingredient_id, most_common_ld50, list(other_ld50_values), 'LD50', value_file_path)
                            else:
                                print(f"Ingredient name: {ingredient_name}")
                                print("No NOAEL or LD50 values found.")
                    except requests.RequestException as e:
                        print(f"Error accessing attachment {status_link}: {e}")
                    except Exception as e:
                        print(f"Error reading PDF {status_link}: {e}")
    else:
        print(f"Ingredient containing '{ingredient_name}' not found in the data file.")

# Esempio di utilizzo
ingredient_name = "Simmondsia Chinensis (Jojoba) Seed Wax"
data_file_path = "C:/Users/AndreaFumagalli/OneDrive - ITS Angelo Rizzoli/Documenti/GitHub/ProjectWork/DATASET.txt"
value_file_path = "C:/Users/AndreaFumagalli/OneDrive - ITS Angelo Rizzoli/Documenti/GitHub/ProjectWork/NOAELVALUES.txt"

find_ingredient_id_and_extract_link(ingredient_name, data_file_path, value_file_path)