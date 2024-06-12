from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup

# CHROME DRIVER
chromedriver_path = r'C:\Users\AndreaFumagalli\OneDrive - ITS Angelo Rizzoli\Desktop\chromedriver.exe'

chrome_options = Options()
chrome_options.add_argument("--headless")

driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)

try:
    driver.get('https://cir-reports.cir-safety.org/')
    time.sleep(10)
    driver.find_element(By.ID, "searchButton").click()
    time.sleep(10)

    # HTML
    html = driver.page_source
finally:
    driver.quit()

# Utilizza BeautifulSoup per analizzare l'HTML
soup = BeautifulSoup(html, 'html.parser')

# Salva l'HTML in una variabile
script_html = soup.prettify()

# Estrai i dati dall'HTML
extracted_data = [
    (
        row.find_all('td')[0].find('a').text.strip() if row.find_all('td')[0].find('a') else '',
        row.find_all('td')[1].text.strip() if len(row.find_all('td')) > 1 else '',
        "https://cir-reports.cir-safety.org" + row.find_all('td')[0].find('a')['href'] if row.find_all('td')[0].find('a') else ''
    )
    for row in soup.find_all('tr')[1:] if len(row.find_all('td')) >= 2
]

# Converte i dati estratti in una stringa
extracted_data_str = "Ingredient Name as Used\tINCI Name\tIndirizzo:\n" + "\n".join(
    f"{data[0]}\t{data[1]}\t{data[2]}" for data in extracted_data
)

# Path to save the complete HTML and extracted data
output_htmlcompleto = r"C:\Users\AndreaFumagalli\OneDrive - ITS Angelo Rizzoli\Desktop\DatasetCompleto.txt"

# Salva l'HTML completo e i dati estratti nel file
with open(output_htmlcompleto, 'w', encoding='utf-8') as file:
    file.write(extracted_data_str)

print(f"HTML completo e dati estratti salvati con successo in {output_htmlcompleto}")