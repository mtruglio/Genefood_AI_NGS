from openpyxl import load_workbook
import pandas as pd
from pprint import pprint

from utils.errors import ValidationError as ValidationError

def check_missing_data(datadict, foglio, legend):
    # print("Check foglio", foglio)
    # print(datadict)
    lengths=[]
    for d in datadict:
        lengths.append(len(d))
    
    lengths_unique = set(lengths)
    if len(lengths_unique) != 1:
        real_length = max(lengths_unique)
        patients_missing_data = []
        for i in range(0, len(lengths)):
            if lengths[i]!=real_length:
                patients_missing_data.append(str(legend[i]))
        return "Errore: Mancano uno o piu' dati nel campo {0} sul foglio {1} ".format(','.join(set(patients_missing_data)),foglio)
    else:
        return
        
def check_wrong_data(paziente, foglio):
    # print("Check foglio", foglio)
    # print(datadict)

    return "Errore: Il codice di accettazione non e' corretto (deve essere 8 cifre). Paziente {0}, foglio {1}".format(paziente, foglio)


def calc_weights_dict(df):
    weights_dict = {}
    for i, row in df.iterrows():
        gene = row["GENE"].strip()
        snp = row["SNP"].strip()
        genotype = row["GEN"].strip()
        weight = float(row["PESO"])
        if gene not in weights_dict:
            weights_dict[gene] = {}
            if '/' in gene:
                for g in gene.split('/'):
                    weights_dict[g] = {}
        if snp not in weights_dict[gene]:
            weights_dict[gene][snp] = {}
        if genotype not in weights_dict[gene][snp]:
            weights_dict[gene][snp][genotype] = weight
        else:
            print("error", gene, snp, genotype), "already present"
    
    #pprint(weights_dict)
    return weights_dict

def get_notes_dict(df):
    notes_dict ={}
    for i, row in df.iterrows():
        gene = row["GENE"].strip()
        snp = row["SNP"].strip()
        genesplit = row["GENE"].strip().split('/')
        snpsplit = row["SNP"].strip().split('/')
        
        genotype = row["GEN"].strip()
        note = row["NOTE"]
        if gene not in notes_dict:
            notes_dict[gene] = {}
        
        # Adding slashed genes and snps as they are
        if snp not in notes_dict[gene]:
                notes_dict[gene][snp] = {}
        snp_notes=[]
        for n in note.split('+'):
            snp_notes.append(n.rstrip().lstrip())
        notes_dict[gene][snp] = snp_notes

        # Also adding each gene and snp in slashes        
        for g in genesplit:
            if g not in notes_dict:
                notes_dict[g]={}
            for s in snpsplit:
                if s not in notes_dict[g]:
                    notes_dict[g][s] = {}
                snp_notes = []
                for n in note.split('+'):
                    snp_notes.append(n.rstrip().lstrip())
                notes_dict[g][s] = snp_notes
        
    return notes_dict

def get_testi_auto(testi_auto_file):
     filein = testi_auto_file
     testi = pd.read_excel(filein)
     testi_dict = testi.set_index(testi.columns[0]).T.to_dict('list')
     return testi_dict

def cleansheet(sheet):
    for i, row in sheet.iterrows():
        if pd.isnull(row["GEN"]) or pd.isnull(row["GENE"]):
            sheet.drop(i, inplace=True)
    return sheet

# def cleanquery(sheet):


def build_scores_dicts(variants_list_file):
    filein = variants_list_file

    peso = pd.read_excel(filein, sheet_name='RIS AUMENTO DI PESO')
    peso = cleansheet(peso)

    #print(peso)
    scores_peso = calc_weights_dict(peso)


    t2d = pd.read_excel(filein, sheet_name='RIS T2D')
    t2d = cleansheet(t2d)
    #print(t2d)
    scores_t2d = calc_weights_dict(t2d)


    cardio = pd.read_excel(filein, sheet_name='RISC PATOLOGIE CARDIOVASCOLARI')
    cardio = cleansheet(cardio)
    #print(cardio)
    scores_cardio = calc_weights_dict(cardio)
    
    mamma = pd.read_excel(filein, sheet_name='RIS MAMMA')
    mamma = cleansheet(mamma)
    scores_mamma = calc_weights_dict(mamma)
    notes_mamma = get_notes_dict(mamma)
    # print(notes_mamma)


    plus = pd.read_excel(filein, sheet_name='RIS PLUS')
    plus = cleansheet(plus)
    scores_plus = calc_weights_dict(plus)
    notes_plus = get_notes_dict(plus)
    # print(notes_plus)


    vita = pd.read_excel(filein, sheet_name='RIS VITA')
    vita = cleansheet(vita)
    scores_vita = calc_weights_dict(vita)
    notes_vita = get_notes_dict(vita)
    # print(notes_vita)
    # print(scores_vita)

    sport = pd.read_excel(filein, sheet_name='RIS SPORT')
    sport = cleansheet(sport)
    scores_sport = calc_weights_dict(sport)
    notes_sport = get_notes_dict(sport)
    # print(scores_sport)
    # print(notes_sport)

    aging = pd.read_excel(filein, sheet_name='RIS AGEING')
    aging = cleansheet(aging)
    scores_aging = calc_weights_dict(aging)
    notes_aging = get_notes_dict(aging)
    # print(notes_aging)

    junior_intoll = pd.read_excel(filein, sheet_name='RIS JUNIOR_INTOLL')
    junior_intoll = cleansheet(junior_intoll)
    scores_junior_intoll = calc_weights_dict(junior_intoll)
    notes_junior_intoll = get_notes_dict(junior_intoll)
    # print(scores_junior_intoll)
    # print(notes_junior_intoll)

    junior_frag = pd.read_excel(filein, sheet_name='RIS JUNIOR_FRAG')
    junior_frag = cleansheet(junior_frag)
    scores_junior_frag = calc_weights_dict(junior_frag)
    notes_junior_frag = get_notes_dict(junior_frag)
    # print(scores_junior_frag)
    # print(notes_junior_frag)

    junior_met = pd.read_excel(filein, sheet_name='RIS JUNIOR_MET')
    junior_met = cleansheet(junior_met)
    scores_junior_met = calc_weights_dict(junior_met)
    notes_junior_met = get_notes_dict(junior_met)
    # print(scores_junior_met)
    # print(notes_junior_met)

    junior_carie = pd.read_excel(filein, sheet_name='RIS JUNIOR_CARIE')
    junior_carie = cleansheet(junior_carie)
    scores_junior_carie = calc_weights_dict(junior_carie)
    notes_junior_carie = get_notes_dict(junior_carie)
    # print(scores_junior_carie)
    # print(notes_junior_carie)


    return scores_peso, scores_t2d, scores_cardio, scores_mamma, notes_mamma, scores_plus, \
        notes_plus, scores_vita, notes_vita, scores_sport, notes_sport, scores_aging, notes_aging, \
        scores_junior_intoll, notes_junior_intoll, scores_junior_frag, notes_junior_frag, \
        scores_junior_met, notes_junior_met, scores_junior_carie, notes_junior_carie

def read_query(filein, packages):
    #Add "Condizioni" to the 'packages' list
    if "Junior" in packages:
        packages.append("Junior_sindrome_met")
        packages.append("Junior_intolleranze")
        packages.append("Junior_carie")
        packages.append("Junior_fragilita")
        packages.remove("Junior")

        
    packages.append("Condizioni")

    # Packages is an array containing one or more from ['Base', 'Plus', 'Vita', 'Sport', 'Ageing', 'Mamma']
    all_results = {}
    errors = []
    
    for p in packages:

        wb = load_workbook(filename = filein)
        parsed_sheet = wb['Foglio '+p]
        # print("MAX COL",parsed_sheet.max_column)
        rows_iter = parsed_sheet.iter_rows(min_col = 1, min_row = 3, max_col = parsed_sheet.max_column+10, max_row = 11)
        # if p=='Vita':
        #     for row in rows_iter:
        #         for cell in list(row):

        #             print(cell.value())
        #     input("VITA wait")
        pazienti = [[cell.value for cell in list(row)[5:] if cell.value!=None] for row in rows_iter]
  


        
        # re initialize iterator
        rows_iter = parsed_sheet.iter_rows(min_col = 1, min_row = 3, max_col = parsed_sheet.max_column+10, max_row = 11)
        legend = []
        for row in rows_iter:
            # print(row)
            if list(row)[4].value!=None:
                legend.append(list(row)[4].value)

        error = check_missing_data(pazienti, p, legend)
        if error: # in case something is missing   
            errors.append(error)
            continue #do not proceed further with the sheet
        
        pazienti_dict = {}
        
        for i in range(0, len(pazienti[0])):

            patient_code = str(pazienti[0][i])
            patient_id = str(pazienti[1][i])
            patient_name = pazienti[2][i]
            patient_weight = pazienti[3][i]
            patient_height = pazienti[4][i]
            patient_lim = pazienti[6][i].lower()
            patient_dob = pazienti[7][i]
            patient_committent = pazienti[8][i]

            if len(patient_code) != 8:
                error = check_wrong_data(patient_name, p)
            if error: # in case something is missing   
                errors.append(error)
            
            
            if p=='Mamma':
                patient_gest = pazienti[5][i]
                pazienti_dict[patient_code] = {'code':patient_code, 'id':patient_id, 'name':patient_name, 'peso':patient_weight, 'altezza':patient_height, 'gestazione':patient_gest, 'lim':patient_lim, 'DOB':patient_dob, 'committent': patient_committent} 
            else:
                patient_sex = pazienti[5][i]
                pazienti_dict[patient_code] = {'code':patient_code, 'id':patient_id, 'name':patient_name, 'peso':patient_weight, 'altezza':patient_height, 'sesso':patient_sex, 'lim':patient_lim, 'DOB':patient_dob, 'committent': patient_committent} 
        
        if p!='Condizioni':
            sheet =  pd.read_excel(filein, sheet_name='Foglio '+p, skiprows=11, index_col=0, names=["Gene", "SNP", "WT", "alt"]+list(pazienti_dict.keys()))
        else:
            sheet =  pd.read_excel(filein, sheet_name='Foglio '+p, skiprows=10, nrows=1)
            sheet = sheet.iloc[:, 5:]
            names=list(pazienti_dict.keys())
            sheet.columns = names
            sheet = sheet.fillna(' ')

        all_results[p] = (sheet, pazienti_dict)
        print("THIS IS ALLRESULTS FROMM XLSXREADER for", p)
        # print(pazienti_dict)
        print(all_results[p])
    if errors:
        raise ValidationError(';'.join(errors))
    return all_results
