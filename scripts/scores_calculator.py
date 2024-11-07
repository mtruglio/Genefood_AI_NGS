import itertools
rules = {
    'Peso':{
        'alto':[20,999],
        'medio':[15,19],
        'lieve':[10,14],
        'non evidente':[-1,9]
    },
    'T2D': {
        'alto': [20, 999],
        'medio': [15, 19],
        'lieve': [7, 14],
        'non evidente': [-1, 6]
    },
    'Cardio': {
        'alto': [22, 999],
        'medio': [17, 21],
        'lieve': [12, 16],
        'non evidente': [-5, 11]
    }
}

def calculate_level(category, score_to_label, scoring_rules):
    for level in scoring_rules[category]:
        low = scoring_rules[category][level][0]
        hi = scoring_rules[category][level][1]
        if int(score_to_label) >= low and int(score_to_label)<= hi:
            final_level = level
    return final_level
        
def calc_scores(test_type, results, scores_tuples, debug='off'):
    if debug == 'on':
        print(results)
        print(test_type)

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
                raise("Error! Duplicate SNP code "+row["SNP"])
            pz_snps[pz][row["SNP"].strip()] = row[pz].strip()
    if debug == 'on':
        print(pz_snps)

    final_scores = {}
    final_levels = {}
    errors=[]
    for pz in pz_snps:
        if test_type == 'Base':
            final_scores[pz] = {'Cardio':0, 'Peso':0, 'T2D':0, }
            final_levels[pz] = { 'Cardio':'', 'Peso':'', 'T2D':'',}
            
        for scoring in scores_tuples:
            if debug == 'on':
                print('\n\n################# {} #################'.format(scoring[0]))
            scoring_dict = scoring[1]
            for gene in scoring_dict:

                if debug == 'on':
                    print("#### GENE: {} ########".format(gene))

                for snp in scoring_dict[gene]:
                    if '/' not in snp:
                        if snp in pz_snps[pz]:

                            if debug == 'on':
                                print(snp, "found in", pz)

                            if pz_snps[pz][snp] == 'NO':
                                final_scores[pz][scoring[0]]+=0
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
                                    final_scores[pz][scoring[0]]+=score
                    else:
                        snp0 = snp.split('/')[0]
                        snp1 = snp.split('/')[1]

                        if (snp0 in pz_snps[pz]) and (snp1 in pz_snps[pz]):

                            if debug == 'on':
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
                                    final_scores[pz][scoring[0]]+=score
                            else:
                                final_scores[pz][scoring[0]]+=0


            # Calculating risk levels

            #print("Find level for", scoring[0], final_scores[pz][scoring[0]])
            score_to_label = final_scores[pz][scoring[0]]
            final_levels[pz][scoring[0]] = calculate_level(scoring[0], score_to_label, rules)

            #print(rules[scoring[0]])

            #input()    
        #input()
    if debug == 'on':
        print(final_scores)
        print(final_levels)
    return(final_scores, final_levels, errors)

