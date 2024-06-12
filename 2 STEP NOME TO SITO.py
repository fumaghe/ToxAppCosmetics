# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 17:18:59 2024

@author: AndreaFumagalli
"""


import webbrowser

def find_ingredient_id(ingredient_name, data_file_path):

  with open(data_file_path, 'r', encoding='utf-8') as file:
    for line in file:

      data = eval(line.strip())

      if data['pcpc_ingredientname'] == ingredient_name or data['pcpc_ciringredientname'] == ingredient_name:
        return data['pcpc_ingredientid']

  return None 

# Example usage
ingredient_name_to_find = "Apricot Kernel Oil Propylene Glycol Esters"  # Replace with the actual ingredient name
data_file_path = "C:\Users\AndreaFumagalli\OneDrive - ITS Angelo Rizzoli\Documenti\GitHub\ProjectWork\DATASET.txt"  # Replace with your actual file path (ensure backslashes are escaped)

ingredient_id = find_ingredient_id(ingredient_name_to_find, data_file_path)

if ingredient_id:
  report_url = f"https://cir-reports.cir-safety.org/cir-ingredient-status-report/?id={ingredient_id}"
  print(f"Ingredient ID for '{ingredient_name_to_find}': {ingredient_id}")
  print(f"Opening CIR report: {report_url}")
  webbrowser.open(report_url)  # Opens the report in the system's default web browser
else:
  print(f"Ingredient '{ingredient_name_to_find}' not found in the data file.")

