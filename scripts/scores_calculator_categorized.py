import itertools
from pprint import pprint
rules = {
    'Mamma':{
        'Sodium':{'Low':[-999,-1], 'High':[6,999]},
        'Low Zinc' : [2, 999],
        'Low Vitamin B12':[1,1000], 
        'Low Vitamin B6':[2,1000], 
        'Low Vitamin D':[3,1000], 
        'Low Vitamin B9':[4,1000],
        'Low Potassium':[1, 999]},
    'Plus':{
        'Sens. Alcol' : [2, 999],
        'Fruttosio':[3,1000], 
        'Lattosio':[1,1000],  
        'Nichel':[1,1000], 
        'Caffeina':{'Lento':[-999,-1], 'Veloce':[1,999]},
        'Glutine':[1,1000]
    },
    'Vita':{
        'Ferro Basso':[2, 999], 
        'Emocromatosi': {'No':[-999,0], 'Lieve_predisp':[1,1], 'True':[2,999]},
        'Low Vitamin B9':[2,999], 
        'Low Vitamin D':[2,10000], 
        'Low Vitamin B12':[3,1000],
        'Low Vitamin A':[2,1000]},
    'Sport':{
        'Crampi-Debolezza Tendinea':[2,999],
        'Tendinopatie':[5,999],
        'Sport Resistenza-Potenza':{'Potenza':[2,999], 'Resistenza':[-1,1], 'Misto':[0,0] },
        'Danno muscolare':[2,999],
        'Osteoartrosi e fratture':[2,999]
    },
    'Ageing':{
        'Infiammazione Cronica':[1,999],
        'Invecchiamento Precoce':[1,999],
        'Calo att. antiossidante':[2,999],
        'Elast. Pelle':[1,999],
        'Idrat. Pelle':[1,999],
        'Funzioni cognitive': [2,999],
        'Diabete e ipercolesterolemia':[0,999],
        'Rischio Cardio':[0,999]
    },
    'Junior_intolleranze':{
        'Sens. Alcol' : [2, 999],
        'Fruttosio':[2,1000], 
        'Lattosio':[1,1000],  
        'Nichel':[2,1000], 
        'Caffeina':{'Lento':[-999,-1], 'Veloce':[1,999]},
        # 'Glutine':[1,1000],
    },
    'Junior_sindrome_met':{
        'Sindrome metabolica':{"No":[-999,9], "Lieve":[10,20], "Medio":[21,30], "Alto":[30,1000]},
    },
    'Junior_carie':{
        'Carie':{"No":[-999,4], "Lieve":[5,6], "Medio":[7,7], "Alto":[8,1000]},
    },
    'Junior_fragilita':{
        'Frag. Ossea':{"No":[-999,6], "Lieve":[7,7], "Medio":[8,11], "Alto":[12,1000]},
        # 'Frag. Ossea Pediatrica':[5,1000],
        # 'Low Vitamin D':[3,1000],
        # 'Fosforo Basso':[5,1000],
        # 'Calcio Alto':[5,1000],
        'Emocromatosi': {'No':[-999,0], 'Lieve_predisp':[1,2], 'True':[3,999]},
        'Ferro Basso':[2, 999],
    },
}


def calc_scores_categorized(test_type, results, scores_tuples, debug='on'):
    if debug == 'on':
        print('\n\n\n###################### RESULTS DF FOR {} ###########################'.format(test_type))
        pprint(results)
        print('###################### SCORES DF FOR {} ###########################'.format(test_type))
        pprint(scores_tuples)
        print("\n\n\n")
    # input()
        
    df = results[0]
    pz_dict = results[1]
    if debug == 'on':
        print(df)
        print(pz_dict)
    pz_snps = {}

    for pz in pz_dict:
        pz_snps[pz] = {}

    for i, row in df.iterrows():
        for pz in pz_dict:
            if row["SNP"] in pz_snps[pz]:
                print("Error! Duplicate SNP code "+row["SNP"])
                raise ValueError
            pz_snps[pz][row["SNP"].strip()] = row[pz].strip()
            
    if debug == 'on':
        print(pz_snps)

    final_scores = {}
    final_levels = {}
    errors=[]

    for pz in pz_snps:
        print("Calculating scores for patient", pz)
        print("patient dictionary:", pz_dict[pz])
        final_scores[pz] = {}
        final_levels[pz] = {}
        if test_type == 'Mamma':
            final_scores[pz] = {'Low Zinc':0, 'Sodium':0, 'Low Vitamin B12':0, 'Low Vitamin B6':0, 'Low Vitamin D':0, 'Low Vitamin B9':0, 'Low Potassium':0}
            final_levels[pz] = {'Low Zinc':'', 'Sodium':'', 'Low Vitamin B12':'', 'Low Vitamin B6':'', 'Low Vitamin D':'', 'Low Vitamin B9':'', 'Low Potassium':''}
        elif test_type == 'Plus':
            final_scores[pz] = {'Sens. Alcol' :0, 'Fruttosio':0, 'Lattosio':0, 'Nichel':0, 'Caffeina':0,'Glutine':0}
            final_levels[pz] = {'Sens. Alcol' :'', 'Fruttosio':'', 'Lattosio':'', 'Nichel':'', 'Caffeina':'','Glutine':''}
        elif test_type == 'Vita':
            final_scores[pz] = {'Ferro Basso':0, 'Emocromatosi':0, 'Low Vitamin B9':0, 'Low Vitamin D':0, 'Low Vitamin B12':0, 'Low Vitamin A':0}
            final_levels[pz] = {'Ferro Basso':'', 'Emocromatosi':'', 'Low Vitamin B9':'', 'Low Vitamin D':'', 'Low Vitamin B12':'', 'Low Vitamin A':''} 
        elif test_type == 'Sport':
            final_scores[pz] = {'Crampi-Debolezza Tendinea':0,'Tendinopatie':0,'Sport Resistenza-Potenza':0, 'Danno muscolare':0,'Osteoartrosi e fratture':0}
            final_levels[pz] = {'Crampi-Debolezza Tendinea':'','Tendinopatie':'','Sport Resistenza-Potenza':'', 'Danno muscolare':'','Osteoartrosi e fratture':''}
        elif test_type == 'Ageing':
            final_scores[pz] = {'Infiammazione Cronica':0,'Invecchiamento Precoce':0,'Calo att. antiossidante':0,'Elast. Pelle':0,'Idrat. Pelle':0, \
                        'Funzioni cognitive': 0, 'Diabete e ipercolesterolemia':0,'Rischio Cardio':0}
            final_levels[pz] = {'Infiammazione Cronica':'','Invecchiamento Precoce':'','Calo att. antiossidante':'','Elast. Pelle':'','Idrat. Pelle':'', \
                        'Funzioni cognitive': '', 'Diabete e ipercolesterolemia':'','Rischio Cardio':''}
        elif test_type == 'Junior_intolleranze':
            final_scores[pz] = {'Sens. Alcol' :0, 'Fruttosio':0, 'Lattosio':0, 'Caffeina':0, 'Glutine':0, 'Nichel':0 }
            final_levels[pz] = {'Sens. Alcol' :'', 'Fruttosio':'', 'Lattosio':'', 'Caffeina':'', 'Glutine':'', 'Nichel':'' }
        elif test_type == 'Junior_sindrome_met':
            final_scores[pz] = {'Sindrome metabolica':0}
            final_levels[pz] = {'Sindrome metabolica':''}
        elif test_type == 'Junior_carie':
            final_scores[pz] = {'Carie':0}
            final_levels[pz] = {'Carie':''}
        elif test_type == 'Junior_fragilita':
            final_scores[pz] = {'Frag. Ossea':0, 'Emocromatosi':0, 'Ferro Basso':0}
            final_levels[pz] = {'Frag. Ossea':'', 'Emocromatosi':'', 'Ferro Basso':''}
        for scoring in scores_tuples:
            if debug == 'on':
                print('\n\n################# {} #################'.format(scoring[0]))
            scoring_dict = scoring[1]
            notes_dict = scoring[2]
            for gene in scoring_dict:

                if debug == 'on':
                    print("#### GENE: {} ########".format(gene))

                for snp in scoring_dict[gene]:  # go through all the snps for the gene, and check patient's result for presence
                    if '/' not in snp:
                        if snp in pz_snps[pz]:
                            category = notes_dict[gene][snp]

                            if debug == 'on':
                                print('########## SNP ', snp, 'corresponds to ', category)    
                                print(snp, "found in", pz)



                            if pz_snps[pz][snp] == 'NO':
                                for c in category:
                                    final_scores[pz][c]+=0
                            else:
                                variant1 = pz_snps[pz][snp]
                                variant2 = pz_snps[pz][snp][::-1]
                                possible_variants = [variant1, variant2]
                                variant_found = False
                                for v in possible_variants:
                                    if v in scoring_dict[gene][snp]:
                                        score = scoring_dict[gene][snp][v]
                                        variant = v
                                        variant_found = True
                                if variant_found == False:
                                    errors.append("{0} non trovato tra i possibili genotipi per questo SNP. Paziente {3}, Foglio {4}, Gene {1}, SNP {2}".format(pz_snps[pz][snp], gene, snp, pz, test_type))
                                else:
                                    if debug == 'on':
                                        print("Variant", v, "Score:", score)
                                    for c in category:
                                        final_scores[pz][c]+=score
                                    
                    elif snp.count('/') ==1:
                        snp0 = snp.split('/')[0]
                        snp1 = snp.split('/')[1]

                        if (snp0 in pz_snps[pz]) and (snp1 in pz_snps[pz]):
                            category = notes_dict[gene][snp]
                            if debug == 'on':
                                print('########## SNP ', snp, 'corresponds to ', category)    
                                print(snp0+'/'+snp1, "found in", pz)

                            if (pz_snps[pz][snp0]!='NO' and pz_snps[pz][snp1]!='NO'):
                                snp0variants = [pz_snps[pz][snp0], pz_snps[pz][snp0][::-1]]
                                snp1variants = [pz_snps[pz][snp1], pz_snps[pz][snp1][::-1]]

                                product = list(itertools.product(snp0variants, snp1variants))
                                snpvariants = ['/'.join(t) for t in product]

                                variant_found = False
                                for v in snpvariants:
                                    if v in scoring_dict[gene][snp]:
                                        score = scoring_dict[gene][snp][v]
                                        variant_found = True
                                        break

                                if variant_found == False:
                                    print(pz_snps[pz])
                                    errors.append("{0} non trovato tra i possibili genotipi per questo SNP. Paziente {3}, Foglio {4}, Gene {1}, SNP {2}".format(' or '.join(set(snpvariants)), gene, snp, pz, test_type))
                                else:                                    
                                    if debug == 'on':
                                            print("Variant", v, "Score:", score)
                                    for c in category:
                                        final_scores[pz][c]+=score        
                            else:
                                for c in category:
                                    final_scores[pz][c]+=0   
                                
                    elif snp.count('/') ==2:
                        snp0 = snp.split('/')[0]
                        snp1 = snp.split('/')[1]
                        snp2 = snp.split('/')[2]

                        if (snp0 in pz_snps[pz]) and (snp1 in pz_snps[pz]) and (snp2 in pz_snps[pz]):
                            category = notes_dict[gene][snp]
                            if debug == 'on':
                                print('########## SNP ', snp, 'corresponds to ', category)    
                                print(snp0+'/'+snp1+'/'+snp2, "found in", pz)

                            if (pz_snps[pz][snp0]!='NO' and pz_snps[pz][snp1]!='NO') and pz_snps[pz][snp2]!='NO':
                                snp0variants = [pz_snps[pz][snp0], pz_snps[pz][snp0][::-1]]
                                snp1variants = [pz_snps[pz][snp1], pz_snps[pz][snp1][::-1]]
                                snp2variants = [pz_snps[pz][snp2], pz_snps[pz][snp2][::-1]]

                                product = list(itertools.product(snp0variants, snp1variants, snp2variants))
                                snpvariants = ['/'.join(t) for t in product]
                                variant_found = False
                                for v in snpvariants:
                                    if v in scoring_dict[gene][snp]:
                                        score = scoring_dict[gene][snp][v]
                                        variant_found = True
                                        break

                                if variant_found == False:
                                    print(pz_snps[pz])
                                    errors.append("{0} non trovato tra i possibili genotipi per questo SNP. Paziente {3}, Foglio {4}, Gene {1}, SNP {2}".format(' or '.join(set(snpvariants)), gene, snp, pz, test_type))
                                else:
                                    if debug == 'on':
                                        print("Variant", v, "Score:", score) 
                                    for c in category:
                                        final_scores[pz][c]+=score                                            
                            else:
                                for c in category:
                                    final_scores[pz][c]+=0  
            # Calculating risk levels

            #print("Find level for", scoring[0], final_scores[pz][scoring[0]])
            for category in final_levels[pz]:
                final_levels[pz][category] = 'No'
                if debug == 'on':
                    print("Scoring category", category)
                    print("Score is" ,final_scores[pz][category])
                    print("Rules are", rules[scoring[0]][category])
                score_to_label = final_scores[pz][category]

                if category == 'Glutine' and pz_dict[pz]['glutine'] != 'Normale':
                    final_levels[pz][category] = 'True'
                    final_scores[pz][category] = pz_dict[pz]['glutine']

                    continue

                if type(rules[scoring[0]][category]) == list:
                    low = rules[scoring[0]][category][0]
                    hi = rules[scoring[0]][category][1]
                    if int(score_to_label) >= low and int(score_to_label)<= hi:
                        final_levels[pz][category] = True
                elif type(rules[scoring[0]][category]) == dict:
                    for level in rules[scoring[0]][category]:
                        low = rules[scoring[0]][category][level][0]
                        hi = rules[scoring[0]][category][level][1]
                        if int(score_to_label) >= low and int(score_to_label)<= hi:
                            final_levels[pz][category] = level
                
            #print(rules[scoring[0]])

            #input()    
        #input()
    if debug == 'on':
        print(final_scores)
        print(final_levels)
    
    
    return(final_scores, final_levels, errors)

