import os
import ast

# Function to move specified foods from "PSEUDO-CEREALI" to "CEREALI"
def move_foods(data, filename):
    foods_to_move = ["patate", "tapioca", "manioca"]
    subkeys = ["Consigliati", "Tollerati", "Sconsigliati"]

    moved_items = []

    for subkey in subkeys:
        if "PSEUDO-CEREALI" in data["Carboidrati"][subkey] and "CEREALI" in data["Carboidrati"][subkey]:
            pseudo_cereali_items = data["Carboidrati"][subkey]["PSEUDO-CEREALI"].get("items", "")
            cereali_items = data["Carboidrati"][subkey]["CEREALI"].get("items", "")

            # Split and clean the items in PSEUDO-CEREALI
            pseudo_list = [item.strip().lower() for item in pseudo_cereali_items.split(",") if item.strip()]
            new_pseudo_list = []
            moved_foods = []

            # Check if the foods to move exist in PSEUDO-CEREALI
            for food in pseudo_list:
                if food in foods_to_move:
                    moved_foods.append(food)
                else:
                    new_pseudo_list.append(food)
            
            # If any food was moved, update the items in PSEUDO-CEREALI and CEREALI
            if moved_foods:
                # Update PSEUDO-CEREALI items (remove moved foods)
                data["Carboidrati"][subkey]["PSEUDO-CEREALI"]["items"] = ", ".join(new_pseudo_list)

                # Update CEREALI items (add moved foods)
                cereali_list = [item.strip() for item in cereali_items.split(",") if item.strip()]
                cereali_list.extend(moved_foods)
                data["Carboidrati"][subkey]["CEREALI"]["items"] = ", ".join(cereali_list)

                moved_items.extend(moved_foods)

    # If any items were moved, log the result
    if moved_items:
        print(f"Moved items from 'PSEUDO-CEREALI' to 'CEREALI' in {filename}: {', '.join(moved_items)}")
    else:
        print(f"No items to move in {filename}.")

# Iterate through files in a directory and process each one
def process_directory(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            filepath = os.path.join(directory, filename)
            try:
                # Read and evaluate the content of the file as a Python dictionary
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                    # Try to safely evaluate the text as a Python dictionary
                    try:
                        data = ast.literal_eval(content)

                        # Check and move foods from PSEUDO-CEREALI to CEREALI
                        if "Carboidrati" in data:
                            move_foods(data, filename)

                            # Save the modified data back to the file (or a new file if you prefer)
                            with open(filepath, 'w', encoding='utf-8') as file_out:
                                file_out.write(str(data))

                    except (ValueError, SyntaxError) as e:
                        print(f"Error evaluating {filename}: {str(e)}")
            except Exception as e:
                print(f"Error reading {filename}: {str(e)}")

# Replace 'your_directory' with the path to the directory containing your .txt files
process_directory('./')
