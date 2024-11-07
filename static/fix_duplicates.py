import json
import re

# Funzione per trovare duplicati tra Consigliati, Tollerati, Sconsigliati in FRUTTA
def find_fruit_duplicates(data):
    duplicates = []
    
    for entry in data:
        for key, categories in entry.items():
            for category in categories:
                # Verifica se esiste la categoria Carboidrati
                if "Carboidrati" in category:
                    carboidrati = category["Carboidrati"]
                    
                    # Inizializza set per raccogliere gli elementi di ogni sezione
                    fruit_items = {"Consigliati": set(), "Tollerati": set(), "Sconsigliati": set()}
                    
                    # Itera su tutte le sezioni: Consigliati, Tollerati, Sconsigliati
                    for section in ["Consigliati", "Tollerati", "Sconsigliati"]:
                        if section in carboidrati and "FRUTTA" in carboidrati[section]:
                            # Ottieni l'elenco di items in FRUTTA
                            fruit_items_section = carboidrati[section]["FRUTTA"].get("items", "")
                            # Dividi per ", " e aggiungi ogni elemento al set della rispettiva sezione
                            fruit_items[section] = set(fruit_items_section.split(", "))
                    
                    # Confronto per duplicati tra le sezioni
                    for section1 in ["Consigliati", "Tollerati", "Sconsigliati"]:
                        for section2 in ["Consigliati", "Tollerati", "Sconsigliati"]:
                            if section1 != section2:
                                # Crea insiemi lowercased per confronto case-insensitive
                                items_section1_lower = {item.lower() for item in fruit_items[section1]}
                                items_section2_lower = {item.lower() for item in fruit_items[section2]}
                                
                                # Trova duplicati
                                duplicates_in_both = items_section1_lower.intersection(items_section2_lower)
                                
                                # Se troviamo duplicati, li aggiungiamo alla lista
                                if duplicates_in_both:
                                    duplicates.append((key, section1, section2, duplicates_in_both))
    
    return duplicates

# Carica il file JSON
with open('consolidated_data_italian_with_subcategories_enriched_corrected_v10.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Trova duplicati nella frutta tra Consigliati, Tollerati, Sconsigliati
fruit_duplicates = find_fruit_duplicates(data)

# Stampa i duplicati trovati
if fruit_duplicates:
    for key, section1, section2, dupes in fruit_duplicates:
        print(f"In {key}, ci sono duplicati tra {section1} e {section2}: {', '.join(dupes)}")
else:
    print("Nessun duplicato trovato tra Consigliati, Tollerati, Sconsigliati in FRUTTA.")
