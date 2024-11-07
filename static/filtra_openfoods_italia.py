import pandas as pd

input_file = '/home/mauro/Desktop/Genefood/static/en.openfoodfacts.org.products.tsv'
output_file = 'en.openfoodfacts.org.products_ITALY.tsv'

with open(output_file, 'w') as outfile:
    # Read the input file in chunks
    chunk_size = 100000  # You can adjust the chunk size based on your memory capacity
    for chunk in pd.read_csv(input_file, sep='\t', chunksize=chunk_size, low_memory=False, on_bad_lines='skip'):
        # Filter the chunk
        filtered_chunk = chunk[chunk['countries_en'] == 'Italy']
        # Write the filtered chunk to the output file
        filtered_chunk.to_csv(outfile, sep='\t', index=False, header=outfile.tell()==0)

print(f"Filtered data saved to {output_file}")
