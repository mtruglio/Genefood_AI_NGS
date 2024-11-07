import json
import os

# Define paths
json_path = 'consolidated_data_italian_with_subcategories.json'
txt_folder_path = 'enriched_files'  # Replace with the actual path to the folder containing txt files

# Load the main JSON data
with open(json_path, 'r', encoding='utf-8') as json_file:
    json_data = json.load(json_file)

# Iterate over all txt files in the specified folder
for txt_filename in os.listdir(txt_folder_path):
    if txt_filename.endswith('.txt'):
        # Extract patient ID from the filename
        patient_id = txt_filename.replace('.txt', '')

        # Load the dictionary from the txt file
        with open(os.path.join(txt_folder_path, txt_filename), 'r', encoding='utf-8') as dict_file:
            update_data = eval(dict_file.read())  # Caution with eval; ensure txt file contents are trusted

        # Match and update the corresponding patient record in JSON
        for record in json_data:
            if record["id_paziente"] == patient_id:
                # Preserve the current "Verdure" value
                verdure_data = record["raccomandazioni"].get("Verdure")

                # Update 'raccomandazioni' with new data from the txt file, keeping 'Verdure' unchanged
                record["raccomandazioni"] = update_data
                if verdure_data:
                    record["raccomandazioni"]["Verdure"] = verdure_data

                break  # Stop loop once the correct record is found and updated

# Save the updated JSON data back to file
with open(json_path, 'w', encoding='utf-8') as json_file:
    json.dump(json_data, json_file, ensure_ascii=False, indent=4)
