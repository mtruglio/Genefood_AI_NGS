#!/home/utente/miniconda3/envs/genefood/bin/python
from flask import Flask, flash, session, render_template, request, redirect, url_for, send_file, jsonify
from webargs.flaskparser import abort, parser
from flask_session import Session
import pandas as pd
import io
import os
from pprint import pprint
from scripts.xlsxreader import build_scores_dicts, read_query, get_testi_auto
from scripts.scores_calculator import calc_scores
from scripts.scores_calculator import rules as base_rules
from scripts.scores_calculator import calculate_level
from scripts.scores_calculator_categorized import calc_scores_categorized
from scripts.assemble_report import assemble_report
from pprint import pprint
import werkzeug
from utils import errors
from utils.errors import ValidationError as ValidationError
import json
from scripts.docx_to_pdf import convert_to, joinpdf, merge_docx
from scripts.assemble_report import fill_template_from_dict
import zipfile
from io import BytesIO
debug = 'on'

app = Flask(__name__)
# app.config.from_object("config.ProductionConfig")
app.config.from_object("config.DevelopmentConfig")
app.register_error_handler(ValidationError, errors.handle_400_errors)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['JSON_AS_ASCII'] = False
app.jinja_env.policies['json.dumps_kwargs'] = {'ensure_ascii': False}
Session(app)
scores_peso, scores_t2d, scores_cardio, scores_mamma, notes_mamma, scores_plus, notes_plus, scores_vita, notes_vita, \
    scores_sport, notes_sport, scores_ageing, notes_ageing, scores_junior_intoll, notes_junior_intoll, scores_junior_frag, notes_junior_frag, \
    scores_junior_met, notes_junior_met, scores_junior_carie, notes_junior_carie = build_scores_dicts('static/GENEFOOD_variants_list.xlsx')

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
                    uploaded_file = request.files['input_file']
                    options = request.form.getlist('optcheck')
                    session['json_results'] = {}
                    session['reports'] = {}
                    
                    if uploaded_file.filename != '':
                            all_results = read_query(uploaded_file, options)
                            all_errors = []
                            print("ALL RESULTS")
                            print(all_results)
                            # input("FERMO")
                            # Decomposing Junior results into three different categories
                            
                            for r in all_results: 
                                if debug=='on':
                                    print(all_results[r][1])
                                    
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
                            
                            if debug=='on':
                                print("ALL RESULTS:")
                                print(all_results)
                            return redirect(url_for('results'))
                        
    return render_template('index.html')

@app.route('/results', methods=['GET', 'POST'])
def results():
    results = session.get('reports', None)
    testi = {}

    # Sorting results, which is now in alphabetical order for some reason
    sorted_results = {}
    for a in ['Base','Plus','Vita','Sport','Ageing','Mamma','Junior_intolleranze','Junior_fragilita','Junior_sindrome_met','Junior_carie']:
        if a in results:
            sorted_results[a] = results[a]



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
                    if (a == "Plus" or a== "Junior intolleranze") and sorted_results[a][2][r]['Glutine']!='No':
                        testo_lungo = testo_breve.replace("AL GLUTINE", "AL GLUTINE ({})".format(sorted_results[a][1][r]['Glutine']))
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
    return render_template('results.html', results=sorted_results, testi=testi)

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
    raw_results = session.get('json_results', None)
    # print(raw_results)
    print("Assembling report for ", analysis_type, patient_id)  
    name = reports[analysis_type][0][patient_id]['name']
    cf = reports[analysis_type][0][patient_id]['cf']
    email = reports[analysis_type][0][patient_id]['email']
    session['patient_data'] = session.get('patient_data', {})

    ai_response_dict, template_indicazioni, name, patient_id, analysis_type, committent = assemble_report(patient_id=patient_id, analysis_type=analysis_type, raw_results=raw_results, \
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
    'committent': committent
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
    patient_id = request.args.get('patient_id')
    print("################# EDIT AI RESPONSE #################")
    print(patient_id)
    # print(session.get('patient_data', {}))
    patient_data = session.get('patient_data', {})
    
    if patient_id and patient_id in patient_data:
        ai_response = patient_data[patient_id].get('ai_response_dict', {})
        name = patient_data[patient_id].get('name', '')
        cf = patient_data[patient_id].get('cf', '')
        email = patient_data[patient_id].get('email', '')
        analysis_type = patient_data[patient_id].get('analysis_type', '')
        committent = patient_data[patient_id].get('committent', '')
        template_indicazioni = patient_data[patient_id].get('template_indicazioni', '')
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
    
    # For GET request, prepare the form
    if request.method == 'GET':
        if 'raccomandazioni' in ai_response:
            json_string = json.dumps(ai_response['raccomandazioni'], indent=2, ensure_ascii=False)
            ai_response['raccomandazioni'] = json_string
            
        print("NAME", name)
        print("PATIENT ID", patient_id)
        print("ANALYSIS TYPE", analysis_type)
        print("COMMITTENT", committent)
        return render_template('ai_response_edit.html', ai_response=ai_response, 
                               name=name, patient_id=patient_id, analysis_type=analysis_type, 
                               committent=committent, template_indicazioni=template_indicazioni)
    
    # For POST request, process the form submission
    elif request.method == 'POST':
        # Get the form data
        updated_response = request.form.to_dict()
        
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
                "CF": cf
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

