#!/home/utente/miniconda3/envs/genefood/bin/python
from flask import Flask, flash, session, render_template, request, redirect, url_for, send_file, jsonify
from webargs.flaskparser import abort, parser
from flask_session import Session
import pandas as pd
import io
import os
from pprint import pprint
from scripts.xlsxreader import build_scores_dicts, read_query, read_NGS_results_from_file, get_testi_auto
from scripts.scores_calculator import calc_scores
from scripts.scores_calculator import rules as base_rules
from scripts.scores_calculator import calculate_level
from scripts.scores_calculator_categorized import calc_scores_categorized
from scripts.assemble_report import assemble_report
from pprint import pprint
import werkzeug
from utils import errors
from utils import utilities
from utils.errors import ValidationError as ValidationError
import json
import subprocess
from scripts.docx_to_pdf import convert_to, joinpdf, merge_docx
from scripts.assemble_report import fill_template_from_dict
import zipfile
from io import BytesIO
import pickle
from pathlib import Path
debug = 'on'

app = Flask(__name__)
app.config.from_object("config.ProductionConfig")
# app.config.from_object("config.DevelopmentConfig")
app.register_error_handler(ValidationError, errors.handle_400_errors)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['JSON_AS_ASCII'] = False
app.jinja_env.policies['json.dumps_kwargs'] = {'ensure_ascii': False}
Session(app)
scores_peso, scores_t2d, scores_cardio, scores_mamma, notes_mamma, scores_plus, notes_plus, scores_vita, notes_vita, \
    scores_sport, notes_sport, scores_ageing, notes_ageing, scores_junior_intoll, notes_junior_intoll, scores_junior_frag, notes_junior_frag, \
    scores_junior_met, notes_junior_met, scores_junior_carie, notes_junior_carie = build_scores_dicts('static/GENEFOOD_variants_list.xlsx')

# Build mapping of option -> gene -> rsID -> (ref, alt)
ref_alt_file = 'static/GENEFOOD_variants_ref_alt.xlsx'
variants_ref_alt = {}
ref_alt_sheets = pd.read_excel(ref_alt_file, sheet_name=None)
for sheet_name, sheet_df in ref_alt_sheets.items():
    option_name = sheet_name.replace('Foglio', '').strip() or sheet_name
    option_variants = {}
    for _, row in sheet_df.iterrows():
        gene = row.get('gene')
        rs_id = row.get('rs_id')
        wt = row.get('wt')
        alt = row.get('alt')
        if pd.isna(gene) or pd.isna(rs_id) or pd.isna(wt) or pd.isna(alt):
            continue
        gene_key = str(gene).strip()
        rsid_key = str(rs_id).strip()
        wt_val = str(wt).strip()
        alt_val = str(alt).strip()
        option_variants.setdefault(gene_key, {})[rsid_key] = (wt_val, alt_val)
    variants_ref_alt[option_name] = option_variants

print("VARIANTS REF ALT:")
print(variants_ref_alt)
# put all these scores and notes into a dictionary for easier passing around
all_scores_notes = {
    'scores_peso': scores_peso,
    'scores_t2d': scores_t2d,
    'scores_cardio': scores_cardio,
    'scores_mamma': scores_mamma,
    'notes_mamma': notes_mamma,
    'scores_plus': scores_plus,
    'notes_plus': notes_plus,
    'scores_vita': scores_vita,
    'notes_vita': notes_vita,
    'scores_sport': scores_sport,
    'notes_sport': notes_sport,
    'scores_ageing': scores_ageing,
    'notes_ageing': notes_ageing,
    'scores_junior_intoll': scores_junior_intoll,
    'notes_junior_intoll': notes_junior_intoll,
    'scores_junior_frag': scores_junior_frag,
    'notes_junior_frag': notes_junior_frag,
    'scores_junior_met': scores_junior_met,
    'notes_junior_met': notes_junior_met,
    'scores_junior_carie': scores_junior_carie,
    'notes_junior_carie': notes_junior_carie
}


@parser.error_handler
def handle_request_parsing_error(err, req, schema, *, error_status_code, 
                                    error_headers):
    """webargs error handler that uses Flask-RESTful's abort function to                 
    return a JSON error response to the client.
    """
    abort(error_status_code, errors=err.messages)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.form.get("Submit_file"):
                    metadata_file = request.files['metadata_file']
                    variants_file = request.files['variants_file']
                    print("files received:", metadata_file, variants_file)
                    options = request.form.getlist('optcheck')
                    selected_options = list(options)
                    print("Selected options:", selected_options)
                    session['json_results'] = {}
                    session['reports'] = {}
                    session['warning_dicts'] = {'not_found': {}, 'no_call': {}, 'mismatch': {}}
                    session['not_found'] = {}
                    session['no_call'] = {}
                    session['mismatch'] = {}
                    
                    if metadata_file.filename != '' and variants_file.filename != '':
                            metadata = read_query(metadata_file)
                            print("METADATA:")
                            pprint(metadata)


                            ngs_variants_df = read_NGS_results_from_file(variants_file, options, all_scores_notes)
                            print("NGS VARIANTS DF:")
                            print(ngs_variants_df)
                            all_errors = []
                            print("ALL RESULTS")
                            print(metadata)
                            print(ngs_variants_df)
                            print("CHECKING PATIENTS IN METADATA AGAINST NGS RESULTS...")
                            print(metadata.keys())
                            print(ngs_variants_df.index)
                            # Validate that all patients in metadata exist in the NGS variants file
                            missing_patients = [pid for pid in metadata.keys() if pid not in ngs_variants_df.index]
                            print("Missing patients:", missing_patients)

                            if missing_patients:
                                error_message = (
                                    "Errore: I seguenti pazienti sono presenti nei metadati ma assenti "
                                    f"nei risultati NGS: {', '.join(missing_patients)}"
                                )
                                raise ValidationError(error_message)


                            # selected_scores_notes is just a subset of variants_ref_alt which keeps only the options selected
                            selected_variants_definition = utilities.subset_top_keys_safe(variants_ref_alt, selected_options, strict=False)
                            
                            # Build per-patient lookup to speed gene/rsID searches
                            patient_variant_lookup = {}
                            if isinstance(ngs_variants_df, pd.DataFrame):
                                for patient in ngs_variants_df.index.unique():
                                    patient_df = ngs_variants_df.loc[[patient]]
                                    patient_variant_lookup[str(patient)] = {
                                        (str(row["Gene"]).strip(), str(row["rsID"]).strip()): row
                                        for _, row in patient_df.iterrows()
                                    }

                            no_call_list = []
                            genes_not_found = []
                            allele_mismatch_warnings = []
                            not_found_dict = {}
                            no_call_dict = {}
                            mismatch_dict = {}
                            selected_variants_dfs = {}

                            def _add_warning_entry(warning_dict, option_label, patient_label, gene_key, rsid_key):
                                option_bucket = warning_dict.setdefault(option_label, {})
                                warning_value = f"{str(gene_key).strip()}({str(rsid_key).strip()})"
                                existing = option_bucket.get(patient_label)
                                if existing:
                                    existing_values = [item.strip() for item in existing.split(",") if item.strip()]
                                    if warning_value not in existing_values:
                                        option_bucket[patient_label] = f"{existing}, {warning_value}"
                                else:
                                    option_bucket[patient_label] = warning_value

                            def _allelic_call(row, patient_data, option_label, patient_label):
                                """Return genotype plus warning messages for the caller to collect."""
                                gene_key = str(row.Gene).strip()
                                rsid_key = str(row.SNP).strip()
                                wt_val = str(row.WT).strip()
                                alt_val = str(row.alt).strip()
                                gene_not_found_msg = None
                                no_call_msg = None
                                mismatch_msg = None
                                record = patient_data.get((gene_key, rsid_key))
                                if record is None:
                                    genotype = wt_val + wt_val
                                    gene_not_found_msg = f"{option_label} | {patient_label} | {gene_key} {rsid_key} not found"
                                    return genotype, no_call_msg, gene_not_found_msg, mismatch_msg

                                ref_val = str(record["Ref"]).strip()
                                var_val = str(record["Variant"]).strip()
                                if ref_val != wt_val or var_val != alt_val:
                                    # let's try to reverse complement both and see if that matches
                                    # if utilities.reverse_complement(ref_val) == wt_val and utilities.reverse_complement(var_val) == alt_val:
                                        #
                                    mismatch_msg = f"{option_label} | {patient_label} | {gene_key} {rsid_key} Ref/Alt {ref_val}/{var_val} expected {wt_val}/{alt_val}"


                                call_value = str(record["Allele Call"]).strip().lower()
                                if call_value == "absent":
                                    genotype = wt_val + wt_val
                                elif call_value == "homozygous":
                                    genotype = alt_val + alt_val
                                elif call_value == "heterozygous":
                                    genotype = wt_val + alt_val
                                elif call_value == "no call":
                                    genotype = wt_val + wt_val
                                    no_call_msg = f"{option_label} | {patient_label} | {gene_key} {rsid_key} marked No Call"
                                else:
                                    genotype = ''
                                return genotype, no_call_msg, gene_not_found_msg, mismatch_msg


                            patient_ids = list(patient_variant_lookup.keys())

                            def _keep_patient_columns(df):
                                keep_cols = [
                                    col for col in df.columns
                                    if col in ('Gene', 'SNP', 'WT', 'alt') or col in metadata.keys()
                                ]
                                return df.loc[:, keep_cols]

                            # If any selected definition is already tabular, keep only valid patient columns.
                            if isinstance(selected_variants_definition, dict):
                                selected_variants_definition = {
                                    key: _keep_patient_columns(value) if isinstance(value, pd.DataFrame) else value
                                    for key, value in selected_variants_definition.items()
                                }

                            for option_name, genes in selected_variants_definition.items():
                                rows = []
                                for gene_name, rs_map in genes.items():
                                    for rsid, (wt, alt) in rs_map.items():
                                        rows.append({'Gene': gene_name, 'SNP': rsid, 'WT': wt, 'alt': alt})
                                option_df = pd.DataFrame(rows, columns=['Gene', 'SNP', 'WT', 'alt'])

                                for patient_id in patient_ids:
                                    pdata = patient_variant_lookup.get(patient_id, {})
                                    genotypes = []
                                    for row in option_df.itertuples(index=False):
                                        genotype, no_call_msg, gene_not_found_msg, mismatch_msg = _allelic_call(
                                            row, pdata, option_name, patient_id
                                        )
                                        if no_call_msg:
                                            no_call_list.append(no_call_msg)
                                            _add_warning_entry(no_call_dict, option_name, patient_id, row.Gene, row.SNP)
                                        if gene_not_found_msg:
                                            genes_not_found.append(gene_not_found_msg)
                                            _add_warning_entry(not_found_dict, option_name, patient_id, row.Gene, row.SNP)
                                        if mismatch_msg:
                                            allele_mismatch_warnings.append(mismatch_msg)
                                            _add_warning_entry(mismatch_dict, option_name, patient_id, row.Gene, row.SNP)
                                        genotypes.append(genotype)
                                    option_df[patient_id] = genotypes

                                option_df = _keep_patient_columns(option_df)
                                selected_variants_dfs[option_name] = (option_df, metadata)


                            print(selected_variants_definition)
                            print("SELECTED VARIANTS DFs:")
                            pprint(selected_variants_dfs)
                            #print alll warnings collected
                            if no_call_list:
                                print("No Call Warnings:")
                                for msg in no_call_list:
                                    print(msg)
                            if genes_not_found:
                                print("Genes Not Found Warnings:")
                                for msg in genes_not_found:
                                    print(msg)
                            if allele_mismatch_warnings:
                                print("Allele Mismatch Warnings:")
                                for msg in allele_mismatch_warnings:
                                    print(msg)
                            print("Warnings by dictionary:")
                            pprint({
                                'not_found': not_found_dict,
                                'no_call': no_call_dict,
                                'mismatch': mismatch_dict
                            })

                            # input("FERMO")
                            # Decomposing Junior results into three different categories
                            all_results = selected_variants_dfs.copy()
                            for r in all_results: 
                                # if debug=='on':
                                #     print(all_results[r][1])
                                    
                                if r == 'Base':
                                    final_scores, final_levels, errors = calc_scores(r, all_results[r], [('Peso',scores_peso), ('T2D',scores_t2d), ('Cardio',scores_cardio)], debug=debug)
                                elif r== 'Mamma':
                                    final_scores, final_levels, errors = calc_scores_categorized(r, all_results[r], [('Mamma', scores_mamma, notes_mamma)], debug=debug)
                                    for paz in final_scores:
                                        final_levels[paz]['Low Vitamin B9'] = 'Vedi Vita'
                                        final_levels[paz]['Vitamin B12'] = 'Vedi Vita'
                                        final_levels[paz]['Vitamin D'] = 'Vedi Vita'
                                        final_scores[paz]['Low Vitamin B9'] = ''
                                        final_scores[paz]['Vitamin B12'] = ''
                                        final_scores[paz]['Vitamin D'] = ''

                                elif r== 'Plus':
                                    final_scores, final_levels, errors = calc_scores_categorized(r, all_results[r], [('Plus', scores_plus, notes_plus)], debug=debug)
                                elif r== 'Vita':
                                    final_scores, final_levels, errors = calc_scores_categorized(r, all_results[r], [('Vita', scores_vita, notes_vita)], debug=debug)
                                elif r== 'Sport':
                                    final_scores, final_levels, errors = calc_scores_categorized(r, all_results[r], [('Sport', scores_sport, notes_sport)], debug=debug)
                                elif r=='Junior_intolleranze':
                                    final_scores, final_levels, errors = calc_scores_categorized(r, all_results[r], [('Junior_intolleranze', scores_junior_intoll, notes_junior_intoll)], debug=debug)
                                elif r=='Junior_fragilita':
                                    final_scores, final_levels, errors = calc_scores_categorized(r, all_results[r], [('Junior_fragilita', scores_junior_frag, notes_junior_frag)], debug=debug)
                                elif r=='Junior_carie':
                                    final_scores, final_levels, errors = calc_scores_categorized(r, all_results[r], [('Junior_carie', scores_junior_carie, notes_junior_carie)], debug=debug)
                                elif r=='Junior_sindrome_met':
                                    final_scores, final_levels, errors = calc_scores_categorized(r, all_results[r], [('Junior_sindrome_met', scores_junior_met, notes_junior_met)], debug=debug)
                                elif r== 'Ageing':
                                    final_scores, final_levels, errors = calc_scores_categorized(r, all_results[r], [('Ageing', scores_ageing, notes_ageing)], debug=debug)
                                    for paz in final_scores:
                                        if debug=='on':
                                            print('Rischio Cardio is', final_scores[paz]['Rischio Cardio'], final_levels[paz]['Rischio Cardio'])
                                            print(' che si somma a', session['reports']['Base'][1][paz]['Cardio'], session['reports']['Base'][2][paz]['Cardio'])
                                        
                                        new_cardio_score = session['reports']['Base'][1][paz]['Cardio']+final_scores[paz]['Rischio Cardio']
                                        new_cardio_level = calculate_level('Cardio', new_cardio_score, base_rules)
                                        session['reports']['Base'][1][paz]['Cardio'] = new_cardio_score
                                        session['reports']['Base'][2][paz]['Cardio'] = new_cardio_level
                                        final_levels[paz]['Rischio Cardio'] = 'Vedi Cardio Base'
                                        if debug=='on':
                                            print('new Cardio score is', new_cardio_score)
                                            print('new Cardio level is', new_cardio_level)
                                            
                                            print('Rischio T2D is', final_scores[paz]['Diabete e ipercolesterolemia'], final_levels[paz]['Diabete e ipercolesterolemia'])
                                            print(' che si somma a', session['reports']['Base'][1][paz]['T2D'], session['reports']['Base'][2][paz]['T2D'])
                                        new_t2d_score = session['reports']['Base'][1][paz]['T2D']+final_scores[paz]['Diabete e ipercolesterolemia']
                                        new_t2d_level = calculate_level('T2D', new_t2d_score, base_rules)
                                        session['reports']['Base'][1][paz]['T2D'] = new_t2d_score
                                        session['reports']['Base'][2][paz]['T2D'] = new_t2d_level
                                        final_levels[paz]['Diabete e ipercolesterolemia'] = 'Vedi T2D Base'
                                        if debug=='on':
                                            print('new T2D score is', new_t2d_score)
                                            print('new T2D level is', new_t2d_level)                                       

                                if errors:
                                    all_errors.extend(errors)
                                    

                                session['reports'][r] = (all_results[r][1], final_scores, final_levels)
                                session['json_results'][r] = [all_results[r][0].to_dict(), all_results[r][1]]
                                
                            if all_errors:
                                raise ValidationError(';'.join(set(all_errors)))

                            session['warning_dicts'] = {
                                'not_found': not_found_dict,
                                'no_call': no_call_dict,
                                'mismatch': mismatch_dict
                            }
                            session['not_found'] = not_found_dict
                            session['no_call'] = no_call_dict
                            session['mismatch'] = mismatch_dict
                            
                            if debug=='on':
                                print("ALL RESULTS:")
                                print(all_results)
                            return redirect(url_for('results'))
                        
    return render_template('index.html')

@app.route('/results', methods=['GET', 'POST'])
def results():
    results = session.get('reports', None)
    testi = {}
    not_found = session.get('not_found', {})
    no_call = session.get('no_call', {})
    mismatch = session.get('mismatch', {})
    warning_dicts = session.get('warning_dicts', {'not_found': {}, 'no_call': {}, 'mismatch': {}})

    # Sorting results, which is now in alphabetical order for some reason
    sorted_results = {}
    for a in ['Base','Plus','Vita','Sport','Ageing','Mamma','Junior_intolleranze','Junior_fragilita','Junior_sindrome_met','Junior_carie']:
        if a in results:
            sorted_results[a] = results[a]


    print("Sorted results:")
    pprint(sorted_results)
    # Adding a new dictionary for short texts and long texts
    for a in ['Base','Plus','Vita','Sport','Ageing','Mamma','Junior_intolleranze','Junior_fragilita','Junior_sindrome_met','Junior_carie']:
        if a not in testi and a in sorted_results:
            testi[a] = {}
            # if a == 'Mamma':
            #     for r in sorted_results[a][2].keys():
            #         testi[a][r] = {"testo_breve":'', "testo_lungo":''}
            #     continue


            for r in sorted_results[a][2].keys():
                print("Patient ", r, "Test", a)
                print(sorted_results[a][2][r].values())
                testo_breve = 'PREDISPOSIZIONE GENETICA '
                for i in sorted_results[a][2][r]:
                    key = i+'|'+str(sorted_results[a][2][r][i])
                    if key in testi_auto and str(sorted_results[a][2][r][i])!='No':
                        testo_breve += testi_auto[key][0]+', ' 
                testo_breve = testo_breve.rstrip(', ')
                last_comma_index = testo_breve.rfind(", ")
                if last_comma_index != -1:
                    testo_breve = testo_breve[:last_comma_index] + " E" + testo_breve[last_comma_index + 1:]

                if a != "Vita" and a != "Mamma":
                    if (a == "Plus" or a== "Junior intolleranze") and sorted_results[a][0][r]['glutine']!='Normale':
                        testo_lungo = testo_breve.replace("AL GLUTINE", "AL GLUTINE ({})".format(sorted_results[a][0][r]['glutine']))
                    else:
                        testo_lungo = testo_breve

                else:
                    print("ANALYSING", a)
                    testo_lungo = testo_breve+'. Si consiglia di controllare '
                    for i in sorted_results[a][2][r]:
                        key = i+'|'+str(sorted_results[a][2][r][i])
                        if key in testi_auto:
                            testo_lungo += testi_auto[key][1]+', '
                    testo_lungo = testo_lungo.rstrip(', ')
                    last_comma_index = testo_lungo.rfind(", ")
                    if last_comma_index != -1:
                        testo_lungo = testo_lungo[:last_comma_index] + ", e" + testo_lungo[last_comma_index + 1:]
                    # print("LUNGO IN", a,":",testo_lungo)
                    # print("CORTO IN", a,":",testo_breve)

                testi[a][r] = {"testo_breve":testo_breve, "testo_lungo":testo_lungo+'.'}

                if a == "Mamma" and sorted_results[a][2][r]:
                    # print("CHECK")
                    # print(sorted_results[a][2][r])
                    # print("TESTI IN MAMMA")
                    # print(testi)

                    testi["Vita"][r]["testo_breve"] = testi["Vita"][r]["testo_breve"] + ". "+testi["Mamma"][r]["testo_breve"]
                    testi["Vita"][r]["testo_lungo"] = testi["Vita"][r]["testo_lungo"] + ". "+testi["Mamma"][r]["testo_lungo"]

                if testo_breve == "PREDISPOSIZIONE GENETICA" and a not in ["Junior_intolleranze", "Junior_fragilita", "Junior_sindrome_met", "Junior_carie"]:
                    testi[a][r] = {"testo_breve":"NON SI EVIDENZIANO PREDISPOSIZIONI GENETICHE", "testo_lungo":"NON SI EVIDENZIANO PREDISPOSIZIONI GENETICHE."}
                elif testo_breve == "PREDISPOSIZIONE GENETICA" and a in ["Junior_intolleranze", "Junior_fragilita", "Junior_sindrome_met", "Junior_carie"]:
                    testi[a][r] = {"testo_breve":f"{a}:NON SI EVIDENZIA PREDISPOSIZIONE GENETICA", "testo_lungo":"NON SI EVIDENZIA PREDISPOSIZIONE GENETICA."}
                    
    print(sorted_results)
    print(testi)
    if debug=='on':
        # print("########### RESULTS #################")
        # print(results)
        # for r in results:
        #     print(r)
            
        print("########### SORTED RESULTS #################")
        pprint(sorted_results)

        print("########### JUST RESPONSES #################")
        for r in sorted_results:
            print("### {} ###".format(r))
            pprint(sorted_results[r][2])   
        print("##### Testi:")
        pprint(testi)
    return render_template(
        'results.html',
        results=sorted_results,
        testi=testi,
        warning_dicts=warning_dicts,
        not_found=not_found,
        no_call=no_call,
        mismatch=mismatch
    )

@app.route('/report_process/<analysis_type>/<patient_id>', methods=['GET', 'POST'])
def report_process(analysis_type, patient_id):
    print("ANALISI TIPO", analysis_type)
    clicked_button = request.form["btn"]
    print(clicked_button)
    testo_intolleranzelong = ''
    testo_metabolismolong = ''
    testo_intolleranzeshort = ''
    testo_metabolismoshort = ''
    testo_sportshort = ''
    testo_sportlong = ''
    testo_ageingshort = ''
    testo_ageinglong = ''
    testo_juniormet_long = ''
    testo_juniormet_short = ''
    testo_juniorcarie_long = ''
    testo_juniorcarie_short = ''
    testo_juniorintoll_long = ''
    testo_juniorintoll_short = ''
    testo_juniorfrag_long = ''
    testo_juniorfrag_short = ''

    if analysis_type in ["Plus", "Vita", "Sport", "Ageing", "Mamma"]:
        testo_intolleranzeshort = request.form['intolleranzeshort_{0}_{1}'.format(analysis_type, patient_id)]
        testo_intolleranzelong = request.form['intolleranzelong_{0}_{1}'.format(analysis_type, patient_id)]
    if analysis_type in ["Vita", "Sport", "Ageing", "Mamma"]:
        testo_metabolismoshort = request.form['metabolismoshort_{0}_{1}'.format(analysis_type, patient_id)]
        testo_metabolismolong = request.form['metabolismolong_{0}_{1}'.format(analysis_type, patient_id)]
    if analysis_type in ["Sport", "Ageing"]:
        testo_sportshort = request.form['sportshort_{0}_{1}'.format(analysis_type, patient_id)]
        testo_sportlong = request.form['sportlong_{0}_{1}'.format(analysis_type, patient_id)]
    if analysis_type == "Ageing":
        testo_ageingshort = request.form['ageingshort_{0}_{1}'.format(analysis_type, patient_id)]
        testo_ageinglong = request.form['ageinglong_{0}_{1}'.format(analysis_type, patient_id)]
    if analysis_type == "Junior_carie": # QUI RICHIEDIAMO I FORM, MA BISOGNA VEDERE QUALI FORM PRODURRE PER JUNIOR E SE POSSIAMO SFRUTTARE I FORM DI PLUS E DI VITA
        testo_juniormet_short = request.form['juniormetshort_{0}_{1}'.format(analysis_type, patient_id)]
        testo_juniormet_long = request.form['juniormetlong_{0}_{1}'.format(analysis_type, patient_id)]
        testo_juniorintoll_long = request.form['juniorintlong_{0}_{1}'.format(analysis_type, patient_id)]
        testo_juniorintoll_short = request.form['juniorintshort_{0}_{1}'.format(analysis_type, patient_id)]
        testo_juniorfrag_long = request.form['juniorfraglong_{0}_{1}'.format(analysis_type, patient_id)]
        testo_juniorfrag_short = request.form['juniorfragshort_{0}_{1}'.format(analysis_type, patient_id)]
        testo_juniorcarie_long = request.form['juniorcarielong_{0}_{1}'.format(analysis_type, patient_id)]
        testo_juniorcarie_short = request.form['juniorcarieshort_{0}_{1}'.format(analysis_type, patient_id)]
        

    
    # print(patient_id)
    # print(analysis_type)
    reports = session.get('reports', None)
    print("REPORTS IN SESSION:")
    print(reports)
    raw_results = session.get('json_results', None)
    # print(raw_results)
    print("Assembling report for ", analysis_type, patient_id)  
    name = reports[analysis_type][0][patient_id]['name']
    cf = reports[analysis_type][0][patient_id]['cf']
    email = reports[analysis_type][0][patient_id]['email']
    session['patient_data'] = session.get('patient_data', {})
    ai_response_dict, template_indicazioni, name, patient_id, analysis_type, committent, base_conditions, other_conditions = assemble_report(patient_id=patient_id, analysis_type=analysis_type, raw_results=raw_results, \
        reports=reports, scores_peso=scores_peso, scores_t2d=scores_t2d, scores_cardio=scores_cardio, \
        scores_mamma=scores_mamma, notes_mamma=notes_mamma, scores_plus=scores_plus, notes_plus=notes_plus, \
        scores_vita=scores_vita, notes_vita=notes_vita, scores_sport=scores_sport, notes_sport=notes_sport, \
        scores_ageing=scores_ageing, notes_ageing=notes_ageing, scores_junior_carie=scores_junior_carie, \
            notes_junior_carie=notes_junior_carie, scores_junior_frag=scores_junior_frag, notes_junior_frag=notes_junior_frag, \
            scores_junior_met=scores_junior_met, notes_junior_met=notes_junior_met, scores_junior_intoll=scores_junior_intoll, \
            notes_junior_intoll=notes_junior_intoll,
        testi=(testo_intolleranzeshort,testo_intolleranzelong, testo_metabolismoshort, testo_metabolismolong, testo_sportshort, \
        testo_sportlong, testo_ageingshort, testo_ageinglong, testo_juniormet_short, testo_juniormet_long, testo_juniorintoll_short, \
        testo_juniorintoll_long, testo_juniorfrag_short, testo_juniorfrag_long, testo_juniorcarie_short, testo_juniorcarie_long), \
        button=clicked_button, debug=debug)
    
    session['patient_data'][patient_id] = {
    'name': name,
    'cf': cf,
    'email': email,
    'ai_response_dict': ai_response_dict,
    'template_indicazioni': template_indicazioni,
    'analysis_type': analysis_type,
    'committent': committent,
    'base_conditions': base_conditions,
    }
    if clicked_button == "Download Word":
        # return send_file('ARCHIVIO/{0}_{1}_{2}_result.docx'.format(name, patient_id, analysis_type), as_attachment=True)
        return jsonify(success=True, patient_id=patient_id)

    elif clicked_button == "Download PDF":
        return send_file('ARCHIVIO/{0}_{1}_{2}.pdf'.format(name, patient_id, analysis_type), as_attachment=True)
    elif clicked_button == "Invia ad Astrolabio":
        print("entrato in astrolabio")
        return ('', 204)
    
@app.route('/edit_ai_response', methods=['GET', 'POST'])
def edit_ai_response():
    with Path("static/profile2id.pkl").open("rb") as f:
        profile2id = pickle.load(f)
    patient_id = request.args.get('patient_id')
    print("################# EDIT AI RESPONSE #################")
    print(patient_id)
    # print(session.get('patient_data', {}))
    patient_data = session.get('patient_data', {})
    # print(patient_data)
    sensitivities = []
    if patient_id and patient_id in patient_data:
        patient_summary = patient_data[patient_id]['ai_response_dict'].get('id_paziente', '')
        patient_conditions = patient_data[patient_id]['ai_response_dict'].get('condizioni', [])

        cereali_sensitive = ''
        latticini_sensitive = ''
        glutine_found = (any(('glutine' in condition.lower() or 'Glutine' in condition) 
                        for condition in patient_conditions if condition) or
                        'Glut' in patient_summary)
        if glutine_found:
            cereali_sensitive = "Grano, frumento, farina 00, farina 0, farina integrale, semola, farro, kamut, orzo, malto d'orzo, estratto di malto, segale, avena, triticale, amido di frumento, crusca di frumento, pangrattato, glutine"

        lattosio_found = (any(('lattosio' in condition.lower() or 'Lattosio' in condition) 
                        for condition in patient_conditions if condition) or
                        'Latt' in patient_summary)
        if lattosio_found:
            latticini_sensitive = "Latte intero, latte scremato, latte in polvere o concentrato, panna fresca, panna da cucina, panna montata, panna in polvere, burro, burro chiarificato, yogurt, crema di latte, siero di latte, latticello, lattosio, siero di latte, proteine del siero di latte, caseina, caseinato di calcio"
        
        fruttosio_found = (any(('fruttosio' in condition.lower() or 'Fruttosio' in condition) 
                        for condition in patient_conditions if condition) or
                        'Fruttosio' in patient_summary)
        if fruttosio_found:
            sensitivities.append(3)

        # Check if raccomandazioni is a string and convert it to dict if necessary
        if 'raccomandazioni' in patient_data[patient_id]['ai_response_dict']:
            if isinstance(patient_data[patient_id]['ai_response_dict']['raccomandazioni'], str):
                try:
                    patient_data[patient_id]['ai_response_dict']['raccomandazioni'] = json.loads(
                        patient_data[patient_id]['ai_response_dict']['raccomandazioni']
                    )
                except json.JSONDecodeError as e:
                    print(f"Could not parse raccomandazioni string as JSON: {e}")
        
        # Now update the values if raccomandazioni is a dictionary
        if isinstance(patient_data[patient_id]['ai_response_dict'].get('raccomandazioni'), dict):
            # Update for lattosio
            if lattosio_found:
                sensitivities.append(1)
                # Ensure the path exists
                if 'Proteine' in patient_data[patient_id]['ai_response_dict']['raccomandazioni']:
                    if 'Sensibili' not in patient_data[patient_id]['ai_response_dict']['raccomandazioni']['Proteine']:
                        patient_data[patient_id]['ai_response_dict']['raccomandazioni']['Proteine']['Sensibili'] = {}
                    if 'LATTICINI' not in patient_data[patient_id]['ai_response_dict']['raccomandazioni']['Proteine']['Sensibili']:
                        patient_data[patient_id]['ai_response_dict']['raccomandazioni']['Proteine']['Sensibili']['LATTICINI'] = {}
                    
                    # Set the items
                    patient_data[patient_id]['ai_response_dict']['raccomandazioni']['Proteine']['Sensibili']['LATTICINI']['items'] = latticini_sensitive
            
            # Update for glutine
            if glutine_found:
                sensitivities.append(2)
                # Ensure the path exists
                if 'Carboidrati' in patient_data[patient_id]['ai_response_dict']['raccomandazioni']:
                    if 'Sensibili' not in patient_data[patient_id]['ai_response_dict']['raccomandazioni']['Carboidrati']:
                        patient_data[patient_id]['ai_response_dict']['raccomandazioni']['Carboidrati']['Sensibili'] = {}
                    if 'CEREALI' not in patient_data[patient_id]['ai_response_dict']['raccomandazioni']['Carboidrati']['Sensibili']:
                        patient_data[patient_id]['ai_response_dict']['raccomandazioni']['Carboidrati']['Sensibili']['CEREALI'] = {}
                    
                    # Set the items
                    patient_data[patient_id]['ai_response_dict']['raccomandazioni']['Carboidrati']['Sensibili']['CEREALI']['items'] = cereali_sensitive
                    
        ai_response = patient_data[patient_id].get('ai_response_dict', {})
        name = patient_data[patient_id].get('name', '')
        cf = patient_data[patient_id].get('cf', '')
        email = patient_data[patient_id].get('email', '')
        analysis_type = patient_data[patient_id].get('analysis_type', '')
        committent = patient_data[patient_id].get('committent', '')
        template_indicazioni = patient_data[patient_id].get('template_indicazioni', '')
        base_conditions = '+'.join(patient_data[patient_id].get('base_conditions', []))
    else:
        # Fallback to original session variables if patient data not found
        ai_response = session.get('ai_response_dict', {})
        name = session.get('name', '')
        cf = session.get('cf', '')
        email = session.get('email', '')
        patient_id = session.get('patient_id', '')
        analysis_type = session.get('analysis_type', '')
        committent = session.get('committent', '')
        template_indicazioni = session.get('template_indicazioni', '')
    print("BASE CONDITIONS", base_conditions)
    print("Profile n.", profile2id.get(base_conditions, 'not found'))
    print("SENSITIVITIES", sorted(sensitivities))
    # For GET request, prepare the form
    if request.method == 'GET':
        if 'raccomandazioni' in ai_response:
            json_string = json.dumps(ai_response['raccomandazioni'], indent=2, ensure_ascii=False)
            ai_response['raccomandazioni'] = json_string
            
        print("NAME", name)
        print("PATIENT ID", patient_id)
        print("ANALYSIS TYPE", analysis_type)
        print("COMMITTENT", committent)
        # print("RACCOMANDAZIONI", ai_response['raccomandazioni'])
        return render_template('ai_response_edit.html', ai_response=ai_response, 
                               name=name, patient_id=patient_id, analysis_type=analysis_type, 
                               committent=committent, template_indicazioni=template_indicazioni)
    
    # For POST request, process the form submission
    elif request.method == 'POST':
        # Get the form data
        updated_response = request.form.to_dict()
        # print("############# GOT HERE ##############")
        # Get the original AI response dictionary to preserve all fields
        original_ai_response = patient_data[patient_id]['ai_response_dict'].copy()
        
        # Update the name and patient_id if they were changed in the form
        if 'name' in updated_response:
            original_ai_response['name'] = updated_response['name']
            patient_data[patient_id]['name'] = updated_response['name']
            name = updated_response['name']
        
        if 'patient_id' in updated_response and updated_response['patient_id'] != patient_id:
            # Handle potential patient_id change carefully
            new_patient_id = updated_response['patient_id']
            print(f"Note: Patient ID was changed from {patient_id} to {new_patient_id} but the original reference is maintained")
        
        # Convert the raccomandazioni string back to a dictionary
        raccomandazioni_dict = {}
        if 'raccomandazioni' in updated_response:
            try:
                raccomandazioni_dict = json.loads(updated_response['raccomandazioni'])
                # Update only the raccomandazioni field in the original dictionary
                original_ai_response['raccomandazioni'] = raccomandazioni_dict
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                print("Error parsing JSON in recommendations")
                # Keep the original raccomandazioni if parsing fails
        
        if 'diagnosi' in updated_response:
            original_ai_response['Diagnosi'] = updated_response['diagnosi']

        # Update other fields that might have been modified in the form
        for key in updated_response:
            if key not in ['name', 'patient_id', 'raccomandazioni', 'Diagnosi']:
                original_ai_response[key] = updated_response[key]

        
        # Update the stored patient data with the modified original dictionary
        patient_data[patient_id]['ai_response_dict'] = original_ai_response
        
        # Get the necessary variables for fill_template_from_dict
        analysis_type = patient_data[patient_id].get('analysis_type', '')
        committent = patient_data[patient_id].get('committent', '')
        template_indicazioni = patient_data[patient_id].get('template_indicazioni', '')
        
        try:

            output_file = './ARCHIVIO/{0}_{1}_{2}_indicazioni.docx'.format(name, patient_id, analysis_type)
            fill_template_from_dict(template_indicazioni, original_ai_response, output_file, committent, analysis_type)
            final_docx = './ARCHIVIO/{0}_{1}_{2}_result.docx'.format(name, patient_id, analysis_type)
            merge_docx(['./ARCHIVIO/{0}_{1}_{2}_genetics.docx'.format(name, patient_id, analysis_type), 
                        './ARCHIVIO/{0}_{1}_{2}_indicazioni.docx'.format(name, patient_id, analysis_type)], final_docx)
            
            # Create and save the JSON file with the specified structure
            json_file_path = './ARCHIVIO/{0}_{1}_{2}_result.json'.format(name, patient_id, analysis_type)
            json_data = {
                "Email": email,
                "CF": cf,
                "codProfilo": profile2id.get(base_conditions, 'not found'),
                "codSensibilita": sorted(sensitivities)
            }
            
            # Add the raccomandazioni content but remove specified keys
            if raccomandazioni_dict:
                # Create a copy to avoid modifying the original dictionary
                filtered_raccomandazioni = raccomandazioni_dict.copy()
                
                # Remove unwanted keys if they exist
                if "Verdure" in filtered_raccomandazioni:
                    filtered_raccomandazioni.pop("Verdure")
                if "Integratori" in filtered_raccomandazioni:
                    filtered_raccomandazioni.pop("Integratori")
                
                # Add the filtered dictionary to json_data
                json_data.update(filtered_raccomandazioni)

            # Write the JSON file
            with open(json_file_path, 'w', encoding='utf-8') as json_file:
                json.dump(json_data, json_file, indent=2, ensure_ascii=False)

            print(f"JSON file created: {json_file_path}")
            
            # Sending the JSON to the Genefood app backend
            URL = "https://jpoaxndblvkndhjccird.supabase.co/functions/v1/importUserData"
            TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impwb2F4bmRibHZrbmRoamNjaXJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDAzODYzNjksImV4cCI6MjA1NTk2MjM2OX0.yB21Rq6IIx50HXCMqHMv9GzAt3R2cySYptT0G5QxEz0'

            cmd = [
                "curl", "-sSL", "-X", "POST", URL,
                "-H", f"Authorization: Bearer {TOKEN}",
                "-H", "Content-Type: application/json",
                "--data-binary", f"@{json_file_path}",
            ]

            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("curl exit code:", result.returncode)
            print("stdout:", result.stdout)
            print("stderr:", result.stderr)
            # Create a zip file containing both the docx and json files

            # Create a BytesIO object to store the zip file
            memory_file = BytesIO()
            with zipfile.ZipFile(memory_file, 'w') as zf:
                # Add the docx file to the zip
                zf.write(final_docx, f"{name}_{patient_id}_{analysis_type}_result.docx")
                # Add the json file to the zip
                zf.write(json_file_path, f"{name}_{patient_id}_{analysis_type}_result.json")

            # Reset the file pointer to the beginning of the BytesIO object
            memory_file.seek(0)

            # Return the zip file as a download which will trigger the window close
            return send_file(
                memory_file,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f"{name}_{patient_id}_{analysis_type}_results.zip"
            )
            
        except Exception as e:
            print(f"Error generating report: {e}")
            # In case of error, return a message but don't close window
            return render_template('ai_response_edit.html', ai_response=original_ai_response, 
                                  name=name, patient_id=patient_id, analysis_type=analysis_type, 
                                  committent=committent, template_indicazioni=template_indicazioni,
                                  error_message=f"Error generating report: {str(e)}")
    
    return render_template('ai_response_edit.html', ai_response={}, 
                           name='', patient_id='', analysis_type='', 
                           committent='', template_indicazioni='')

if __name__ == '__main__':
    print("HELLO")
    scores_peso, scores_t2d, scores_cardio, scores_mamma, notes_mamma, scores_plus, notes_plus, scores_vita, notes_vita, \
    scores_sport, notes_sport, scores_ageing, notes_ageing, scores_junior_intoll, notes_junior_intoll, scores_junior_frag, notes_junior_frag, \
    scores_junior_met, notes_junior_met, scores_junior_carie, notes_junior_carie  = build_scores_dicts('static/GENEFOOD_variants_list.xlsx')
    testi_auto = get_testi_auto('static/testi_auto_dict.xlsx')
    # for s in [scores_junior, notes_junior]:
    #     pprint(s)
    app.run()
