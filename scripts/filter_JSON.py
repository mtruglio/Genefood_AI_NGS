import json
from itertools import combinations
import random

def filter_records_smart(input_file, substrings):
    # Load the JSON data from the file
    print(substrings)
    with open(input_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Create the strict search string
    strict_search_string = '+'.join(substrings)

    # Define the filtering functions
    def contains_strict_string(id_paziente, strict_search_string):
        return strict_search_string in id_paziente

    def contains_substrings(id_paziente, substrings):
        return all(substring in id_paziente for substring in substrings)

    # Attempt strict search first
    filtered_data = [record for record in data if contains_strict_string(record['id_paziente'], strict_search_string)]
    # If no matches found, gradually relax the search criteria
    if not filtered_data:
        for r in range(len(substrings)-1, 0, -1):
            print("iteration", r)
            combs = combinations(substrings, r)

            for comb in combs:
                # print(comb)
                filtered_data.extend([record for record in data if contains_substrings(record['id_paziente'], comb)])
            #     if filtered_data:
            #         break
            if filtered_data != []:
                # print(filtered_data)
                print("JSON filtrato.")
                break
    if "Vegano" in substrings:
        filtered_data.extend([record for record in data if contains_strict_string(record['id_paziente'], "Vegano")])
    if "Vegetariano" in substrings:
        filtered_data.extend([record for record in data if contains_strict_string(record['id_paziente'], "Vegetariano")])
    
    return filtered_data

def gather_data(input_file_path, input_file_path2, primary_substrings, secondary_substrings, output_file_path):
    print('gather_data')
    print(primary_substrings)
    print(secondary_substrings)

    filtered_primary = filter_records_smart(input_file_path, primary_substrings)

    filtered_secondary = []
    if secondary_substrings:
        filtered_secondary = filter_records_smart(input_file_path2, secondary_substrings)
    filtered_data = filtered_primary + filtered_secondary
    with open(output_file_path, 'w', encoding='utf-8') as file:
        json.dump(filtered_data, file, indent=4, ensure_ascii=False)
    
    if len(json.dumps(filtered_data, ensure_ascii=False).encode('utf-8')) > 500 * 1024:
        print("Removing half of the records")
        filtered_data = random.sample(filtered_data, len(filtered_data)//3)
        with open(output_file_path, 'w', encoding='utf-8') as file:
            json.dump(filtered_data, file, indent=4, ensure_ascii=False)
    
# # Define the list of substrings to look for
# substrings_to_look_for = ['T2D_Lieve', 'Cardio_Lieve', 'Peso_NonEvidente']
# secondary_substrings = ['Sens.Alcol_True', 'Fruttosio_True', 'Caffeina_Lento', 'FerroBasso_True']
# # File paths
# input_file_path = 'consolidated_data_italian_with_subcategories.json'
# input_file_path2 = 'consolidated_data_italian_with_subcategories_special.json'

# output_file_path = 'filtered_data.json'
# # Run the filtering function
# filtered_primary = filter_records_smart(input_file_path, substrings_to_look_for)
# filtered_secondary = filter_records_smart(input_file_path2, secondary_substrings)

# #write both filtered data to a single JSON file
# filtered_data = filtered_primary + filtered_secondary
# with open(output_file_path, 'w', encoding='utf-8') as file:
#     json.dump(filtered_data, file, indent=4, ensure_ascii=False)


    

