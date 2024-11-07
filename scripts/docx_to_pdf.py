import sys
import subprocess
import re
from PyPDF2 import PdfFileMerger, PdfFileReader
import os
from docx import Document
from docxcompose.composer import Composer

def merge_docx(docx_paths, output_path):
    """
    Merges a list of DOCX files into a single DOCX file.

    Args:
        docx_paths (list): List of paths to DOCX files to be merged.
        output_path (str): Path where the merged DOCX will be saved.

    Returns:
        str: Path to the merged DOCX document.
    """
    if not docx_paths:
        raise ValueError("The list of docx paths is empty.")
    
    # Create a master document as a starting point
    master_doc = Document(docx_paths[0])
    
    composer = Composer(master_doc)

    # Append each document to the master document
    for docx_path in docx_paths[1:]:
        doc = Document(docx_path)
        composer.append(doc)
    
    # Save the merged document
    composer.save(output_path)

    return output_path

def convert_to(folder, source, timeout=None): #folder is the path where the pdf will be saved
    args = [libreoffice_exec(), '--headless', '--convert-to', 'pdf', '--outdir', folder, source]

    process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    # filename = re.search('-> (.*?) using filter', process.stdout.decode())

    # return filename.group(1)


def libreoffice_exec():
    # TODO: Provide support for more platforms
    if sys.platform == 'linux':
        return '/usr/bin/soffice'
    return 'libreoffice'

def joinpdf(files, out):
    # Open the files that have to be merged one by one
 
    # Call the PdfFileMerger
    mergedObject = PdfFileMerger()
    
    # I had 116 files in the folder that had to be merged into a single document
    # Loop through all of them and append their pages
    for f in files:
        if os.path.exists(f):
            mergedObject.append(PdfFileReader(f, 'rb'))
    
    # Write all the files into a file which is named as shown below
    mergedObject.write(out)

# convert_to('/home/mauro/Desktop/butta/', '/home/mauro/Desktop/butta/Filled_Indicazioni_alimentari.docx')
# merge_docx(['/home/mauro/GoogleDrive/Work/Altamedica/Genefood/ARCHIVIO/FAZIO CINZIA_24246361_Vita_result.docx', '/home/mauro/Desktop/butta/Filled_Indicazioni_alimentari.docx'], '/home/mauro/Desktop/butta/merged.docx')