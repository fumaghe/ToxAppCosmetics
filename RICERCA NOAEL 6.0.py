import requests
from bs4 import BeautifulSoup
import re
from collections import Counter
import PyPDF2
import io

def extract_status_links(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        tbody = soup.find('tbody')
        if not tbody:
            print(f"No tbody found in {url}")
            return []

        status_links = []

        for row in tbody.find_all('tr')[1:]:
            link = row.find('a')['href']
            if "view-attachment" in link:
                full_status_link = "https://cir-reports.cir-safety.org/" + link.replace("../", "")
                status_links.append(full_status_link)

        return status_links

    except requests.RequestException as e:
        print(f"Error accessing {url}: {e}")
    except (IndexError, TypeError) as e:
        print(f"Error parsing the page: {e}")
        return []

def extract_text_from_pdf(pdf_content):
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
    text = ""
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text += page.extract_text() or ""
    return text

def find_noael_or_ld50s_values(text):
    noael_pattern = r'NOAEL\s*[:/]?'
    ld50s_pattern = r'LD50\s*[:/]?'
    
    def find_values(pattern):
        matches = re.finditer(pattern, text, re.IGNORECASE)
        values = []
        for match in matches:
            start_index = match.end()
            words = text[start_index:start_index+100].split()[:20]  # Extracting next 20 words
            for word in words:
                if re.match(r'\d+(\.\d+)?', word):  # Checking if the word is a number
                    values.append(word)
                    break
        return values
    
    noael_values = find_values(noael_pattern)
    if noael_values:
        return "NOAEL", noael_values
    else:
        ld50s_values = find_values(ld50s_pattern)
        if ld50s_values:
            return "LD50s", ld50s_values
    return None, []

def find_most_common_value(values):
    if not values:
        return None
    count = Counter(values)
    most_common_count = count.most_common(1)[0][1]
    most_common_values = [value for value, freq in count.items() if freq == most_common_count]
    return most_common_values, most_common_count

def find_ingredient_id_and_extract_link(ingredient_name, data_file_path, noael_file_path):
    with open(data_file_path, 'r', encoding='utf-8') as file:
        ingredients = []
        for line in file:
            data = eval(line.strip())
            search_name = ingredient_name.lower()
            if (search_name in data['pcpc_ingredientname'].lower() or
                search_name in data['pcpc_ciringredientname'].lower()):
                ingredients.append((data['pcpc_ingredientname'], data['pcpc_ingredientid']))

    with open(noael_file_path, 'a+', encoding='utf-8') as noael_file:
        noael_file.seek(0)
        existing_entries = noael_file.readlines()
        existing_data = {line.split(':')[0]: line.split(':')[1].strip() for line in existing_entries}

    if ingredients:
        for ingredient_name, ingredient_id in set(ingredients):
            if ingredient_id in existing_data:
                print(f"Ingredient name: {ingredient_name}")
                print(f"Existing Value: {existing_data[ingredient_id]}")
                continue

            url = f"https://cir-reports.cir-safety.org/cir-ingredient-status-report/?id={ingredient_id}"
            status_links = extract_status_links(url)
            for status_link in status_links:
                try:
                    response = requests.get(status_link)
                    response.raise_for_status()

                    pdf_text = extract_text_from_pdf(response.content)
                    value_type, values = find_noael_or_ld50s_values(pdf_text)
                    
                    if values:
                        most_common_values, most_common_count = find_most_common_value(values)
                        if most_common_values:
                            print(f"Ingredient name: {ingredient_name}")
                            for value in most_common_values:
                                print(f"{value_type} value: {value} mg/kg")
                                noael_file.write(f"{ingredient_id}:{value_type} {value}\n")
                        break
                except requests.RequestException as e:
                    print(f"Error accessing attachment {status_link}: {e}")
                except Exception as e:
                    print(f"Error reading PDF {status_link}: {e}")
    else:
        print(f"Ingredient containing '{ingredient_name}' not found in the data file.")

# Example usage
ingredient_name = "Acacia Catechu Gum"
data_file_path = "C:/Users/AndreaFumagalli/OneDrive - ITS Angelo Rizzoli/Documenti/GitHub/ProjectWork/DATASET.txt"
noael_file_path = "C:/Users/AndreaFumagalli/OneDrive - ITS Angelo Rizzoli/Documenti/GitHub/ProjectWork/NOAELVALUES.txt"

find_ingredient_id_and_extract_link(ingredient_name, data_file_path, noael_file_path)