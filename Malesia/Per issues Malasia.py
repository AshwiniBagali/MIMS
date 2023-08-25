import csv
import json
import os
import pandas as pd
import re
from elasticsearch import Elasticsearch, helpers
def remove_substring_in_brackets(packaging):
    # Define the regex pattern to check for substrings within brackets
    pattern = r'\([^()]*\)'  # This pattern matches anything between '(' and ')'

    # Use the re.sub() function repeatedly to remove all occurrences of substrings within brackets
    while re.search(pattern, packaging):
        packaging = re.sub(pattern, '', packaging)

    return packaging
keywords_list = ['of', 'is', 'a', 'the', 'per', 'tab', 'syr', 'cap', 'fc', 'caplet', 'oral', 'susp', 'oral', 'inj', 'injection', 'soln', 'solution', 'dose', 'sugar-coated', 'forte', 'dry', 'paed', 'for', 'fC', 'drops', 'powd', 'liqd', 'mouthwash', 'rectal', 'oint', 'cream', 'daily', 'facial', 'moisturizer', 'gel', 'inhaler', 'vaccine', 'infant', 'softgel', 'eye', 'ointment', 'effervescent', 'chewtab', 'active', 'captab', 'dispersible', 'xr-fc', 'plus', 'chewable', 'dose:', 'extra', 'adult', 'mite', 'film-coated', 'softcap', 'soft', 'sachet', 'syrup', 'drag', 'bottle', 'mouthspray', 'toothpaste', 'shampoo', 'diskus', 'serum', 'lotion', 'spray']
def get_forms(products):
    forms_list=[]
    products = sorted(products, key=lambda x: len(x['form']), reverse=True)#Get products in descending order
    for product in products:
        forms_list.append(product['form'])
    return forms_list
def append_keywords_from_form_to_keywords_list(forms_list):#Append keywords from form to keywords to map and remove it form material
    local_keywords_list = keywords_list
    print("keywords list for current line item : ",local_keywords_list)
    for current_form in forms_list:
        current_form=current_form.lower().split()
        for word in current_form:
            if word not in local_keywords_list:
                local_keywords_list.append(word)
    return local_keywords_list
def get_sub_string_from_mat(activeIngredientsList,local_keywords_list): #Get starting substring from material to be mapped with form and then remove
        mat_to_map_form = []
        material_list = []
        for e,entry in enumerate(activeIngredientsList):
            entry=entry.replace('&amp;','&')
            entry=entry.replace(',','')
            entry=entry.replace(';','')
            entry=entry.strip()
            entry=entry.strip('.')
            raw_mat = ''
            dosage_match_in_mat = re.search('[^\w](\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg\/?dose|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg\/?actuation|\d+\.?\d*\/?\d*\.?\d*\s?u\/?mL\s?\+?\s?\d*\.?\d*\s?mcg\/?mL|\d+\.?\d*\/?\d*\.?\d*\s?mg\/?mL|\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg(?:\/\d+\.?\d*\s?mg)*|\d+\.?\d*\/?\-?\d*\.?\d*/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\sg\s|\smL\s|\sL\s|\samp\s|\spuff\s|\sdose\s|\skCal\s|\sbar\s)[^\w]'," "+entry+" ", re.DOTALL)
            con_match_in_mat = re.search('\d+\.?\d*\s?%',entry)# add first conc match or dosage match to keywords
            if(dosage_match_in_mat):
                    dosage_matches = dosage_match_in_mat.group(0).split()
                    for match in dosage_matches:
                        if(match.strip() not in local_keywords_list):
                            local_keywords_list.append(match.strip().lower())
            if(con_match_in_mat):
                    con_matches = con_match_in_mat.group(0).split()
                    for match in con_matches:
                        if(match not in local_keywords_list):
                            local_keywords_list.append(match.strip().lower())
            words_in_mat = entry.split()
            for i, word in enumerate(words_in_mat):
                if word.lower() in local_keywords_list:
                    raw_mat += word + ' '
                else:
                    break
#             raw_mat=raw_mat.strip()
            material_list.append(entry)
            mat_to_map_form.append(raw_mat)
            print("raw material to match form : ",raw_mat)
        return mat_to_map_form,material_list
def map_form_to_mat(forms_list,mat_to_map_form,material_list):#map form to material with highest count match
    list_of_dicts = []
    for i in range(len(mat_to_map_form)):
        dictionary = {
            "form": forms_list[i],
            "count": 0,
            "activeIngredient":material_list[i],
            "materialToMapForm":mat_to_map_form[i]
        }
        list_of_dicts.append(dictionary)
    for j,f in enumerate(forms_list):
        for k,a in enumerate(mat_to_map_form):
#             a=a.lower()
            count=0
            current_entry=list_of_dicts[k]
            words_in_form=f.lower().split()
            for word in words_in_form:
                if word in a.lower():
                    count=count+1
            if(current_entry['count']<count):
                current_entry['count']=count
                current_entry['form']=f
    list_of_dicts = sorted(list_of_dicts, key=lambda x: x['count'], reverse=True)#sort dictionary by highest count match
    not_found_index=0
    for l,item in enumerate(list_of_dicts):
        if(item['form'] in forms_list):
            forms_list.remove(item['form'])
        else:
            not_found_index=l
    if(len(forms_list)!=0):
        list_of_dicts[not_found_index]['form']=forms_list[0]
    list_of_dicts = sorted(list_of_dicts, key=lambda x: len(x['form']), reverse=True)#sort dictionary by form length
    print("mapped dictionary : ",list_of_dicts)
    return list_of_dicts
def get_matching_material(current_form,list_of_dicts):#get matching material for cuurent form
    matching_mat=''
    material_to_map_form=''
    for m in list_of_dicts :
        if m.get('form') == current_form:
            matching_mat=m.get('activeIngredient')
            material_to_map_form=m.get('materialToMapForm')
            break
    return matching_mat,material_to_map_form
def extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,material_to_map_form,format_org,std_format,format_match):
    std_mat=std_mat.strip()
    mat=mat.strip()
    if(len(d)==0 and len(con)==0 ):
        # dosage_match = re.findall('\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\d*\.?\d*\s?mL',mat, re.DOTALL)# Regex extracting 2 gummies as 2g
        dosage_match = re.findall('[^\w](\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\d*\.?\d*\s?mL)[^\w]'," "+mat+" ", re.DOTALL)
        con_match = re.findall('\d+\.?\d*\s?%',mat, re.DOTALL)
        regex_to_match_mL=re.findall('\d*\.?\d*\s?mL',mat, re.DOTALL)
        if(len(dosage_match)!=0 and len(con_match)!=0):
            if(len(regex_to_match_mL)!=0):
                per_dosage=''
                if(mat.startswith('Per '+regex_to_match_mL[0].strip())):
                    per_dosage=dosage_match.pop(0)
                    dosage_match.append(per_dosage)
            result=''
            for m in dosage_match:
                if(m.find('/')==-1):
                    result+=m+"/"
                    result=result.replace(' ','')
            d=result[:-1]
            d=d.strip('.')
            result=''
            for m in con_match:
                result+=m+"/"
                result=result.replace(' ','')
            con=result[:-1]
        elif(len(dosage_match)!=0):
            if(len(regex_to_match_mL)!=0):
                per_dosage=''
                if(mat.startswith('Per '+regex_to_match_mL[0].strip())):
                    per_dosage=dosage_match.pop(0)
                    dosage_match.append(per_dosage)
            result=''
            for m in dosage_match:
                if(m.find('/')==-1):
                    result+=m+"/"
                    result=result.replace(' ','')
            d=result[:-1]
            d=d.strip('.')
            con=''
        elif(len(con_match)!=0):
            result=''
            for m in con_match:
                result+=m+"/"
                result=result.replace(' ','')
            con=result[:-1]
            d=''
        elif(len(dosage_match)==0 and len(con_match)==0 and len(con)==0):
            d=''
            con=''
    if(len(d)==0 and len(con)==0):
        d=''
        con=''
    format_match = re.findall('\sunit dose vial\s|\spolyamp inj\s|\ssoluble insulin\s|\spowd for oral susp\s|\spowd for oral soln|\ssoftgel\s|\ssoln for inj\s|\sXR-FC tab\s|\smilk powd\s|\smoisturizing facial cleansing foam\s|\sintensive moisturizing cream\s|\srestorative hydration cream\s|\smoisturising bath & shampoo\s|\slight moisturising cream\s|\sdermarelief rescue cream\s|\smoisturizing body lotion\s|\smoisturising bath & wash\s|\sdaily facial moisturizer\s|\sgentle foaming cleanser\s|\smoisturising day cream\s|\srevitalising eye cream\s|\snourishing conditioner\s|\sultra hydrating lotion\s|\smoisturising body wash\s|\ssensitive light lotion\s|\snurturing night cream\s|\smoisturising cleanser\s|\sintensive moisturizer\s|\sintensive oint-cream\s|\soil free moisturiser\s|\sdermarelief cleanser\s|\srichenic urea cream\s|\shydrating body wash\s|\smoisturising lotion\s|\sdose: powd for inj\s|\spowd for inj\s|\smoisturising cream\s|\snourishing shampoo\s|\sdermarelief lotion\s|\smulti-action cream\s|\sprofessional serum\s|\smoisturising wash\s|\sintensive lotion\s|\sfoaming cleanser\s|\sbody moisturiser\s|\smedicated lotion\s|\sdaily face cream\s|\sdaily oral rinse\s|\sintensive cream\s|\ssoothing lotion\s|\sgentle cleanser\s|\ssting-free oint\s|\sfilm-coated tab\s|\ssoothing cream\s|\sgentle shampoo\s|\sdaily moisture\s|\scleansing gel\s|\scod liver oil\s|\srepair cream\s|\schewable tab\s|\sfoaming wash\s|\sultra lotion\s|\sdaily lotion\s|\snappy cream\s|\sskin lotion\s|\sgentle wash\s|\srectal oint\s|\smouth spray\s|\screamy wash\s|\smoisturizer\s|\shand cream\s|\srescue gel\s|\sfruit powd\s|\stoothpaste\s|\sinhalation\s|\scaring oil\s|\soral spray\s|\soral susp\s|\soral liqd\s|\smouthwash\s|\smouth gel\s|\soral soln\s|\sactuation\s|\scleanser\s|\ssunblock\s|\sbath oil\s|\sgranules\s|\sinsulin\s|\sshampoo\s|\sfc tab\s|\ssachet\s|\slotion\s|\stroche\s|\scream\s|\sdrops\s|\spowd\s|\ssusp\s|\sliqd\s|\swash\s|\ssupp\s|\sdose\s|\soint\s|\ssoln\s|\stab\s|\scap\s|\sinj\s|\sgel\s|\ssyr\s|\sgummies\s|\sgummy\s|\sturbuhaler\s|\saccuhaler\s|\sevohaler\s|\smdv\s|\svial\s',mat.lower(),re.DOTALL)
    if(len(format_match)!=0 and len(format_org)==0):
        format_org=format_match[0].strip()
        std_format=search(format_org)
    if(len(material_to_map_form)!=0): # Remove raw string from material
#         material_to_map_form = re.escape(material_to_map_form)#This ensures that any special characters are treated as literal characters in the regular expression pattern.
#         std_mat = re.sub(material_to_map_form,'',std_mat ,flags = re.IGNORECASE) #Ignore case while removing raw_string in material
        std_mat = std_mat.replace(material_to_map_form,'')
        print("Remove raw string from material :",std_mat,"raw material:",material_to_map_form)
    dosage_match_in_mat = re.findall('[^\w](\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg\/?dose|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg\/?actuation|\d+\.?\d*\/?\d*\.?\d*\s?u\/?mL\s?\+?\s?\d*\.?\d*\s?mcg\/?mL|\d+\.?\d*\/?\d*\.?\d*\s?mg\/?mL|\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg(?:\/\d+\.?\d*\s?mg)*|\d+\.?\d*\/?\-?\d*\.?\d*/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U)[^\w]'," "+std_mat+" ", re.DOTALL)
    con_match_in_mat = re.findall('\d+\.?\d*\s?%',mat, re.DOTALL)
    if(len(dosage_match_in_mat)==0 and len(con_match_in_mat)==0):
        current_mat=mat
        current_std_mat=std_mat
    elif(len(dosage_match_in_mat)!=0 and len(con_match_in_mat)!=0):
        current_mat=mat
        for dm in dosage_match_in_mat:
            dm=dm.strip()
            std_mat=std_mat.replace(dm,'',1)
            std_mat=std_mat.replace('  ',' ')
        for cm in con_match_in_mat:
            std_mat=std_mat.replace(cm,'',1)
            std_mat=std_mat.replace('  ',' ')
        # remove_raw_from_mat = r'^\d*\.?\d*\/?\d*\.?\d*\s?white tab|^\d*\.?\d*\/?\d*\.?\d*\s?blue tab|^\d*\.?\d*\/?\d*\.?\d*\s?large tab|^FC tab|^Forte tab|^forte tab|^tab|^\d*\.?\d*\/?\d*\.?\d*\s?kCal|^\d*\.?\d*\/?\d+\.?\d*\s?tab|^syr\/mL|^tab\/?\s?susp|^tab\/?\s?liqd|^tab\/?\s?syr|^tab\/?\s?drag|^forte caplet|^Forte caplet|^Forte cap|^FC caplet|^Forte dry syr|^forte syr|^forte liqd|^Forte oral susp|^\d*\.?\d*\/?\d*\.?\d*\s?cap\s*\d*\-?|^\d*\.?\d*\/?\d+\.?\d*\s?mL|^\d*\.?\d*\/?\d*\.?\d*\s?FC caplet|^\d*\.?\d*\/?\d*\.?\d*\s?FC Caplet|^\d*\.?\d*\/?\d*\.?\d*\s?brown tab|^caplet|^Caplet\/Effervescent tab?|^Caplet|^\d+\.?\d*\/?\d+\.?\d*\s?cap|^cap\/?|^Cap|^syr\/?mL|^caplet|^Forte dry susp|^inj|^insulin|^susp|^sachet|^Sachet|^syr|^DHA|^milk powd|^oint|^powd|^mL|^\d+\-?'
        # pat_match = re.findall(remove_raw_from_mat,std_mat)
        # if(len(pat_match)!=0):
        #     current_std_mat=std_mat.replace(pat_match[0],'')
        std_mat=std_mat.replace('w/w','')
        std_mat=std_mat.replace('w/v','')
        std_mat=std_mat.strip() 
        current_std_mat=std_mat
    elif(len(dosage_match_in_mat)!=0):
        current_mat=mat
        for dm in dosage_match_in_mat:
            dm=dm.strip()
            std_mat=std_mat.replace(dm,'',1)
            std_mat=std_mat.replace('  ',' ')
        # remove_raw_from_mat = r'^\d*\.?\d*\/?\d*\.?\d*\s?white tab|^\d*\.?\d*\/?\d*\.?\d*\s?blue tab|^\d*\.?\d*\/?\d*\.?\d*\s?large tab|^FC tab|^Forte tab|^forte tab|^tab|^\d*\.?\d*\/?\d*\.?\d*\s?kCal|^\d*\.?\d*\/?\d+\.?\d*\s?tab|^syr\/mL|^tab\/?\s?susp|^tab\/?\s?liqd|^tab\/?\s?syr|^tab\/?\s?drag|^forte caplet|^Forte caplet|^Forte cap|^FC caplet|^Forte dry syr|^forte syr|^forte liqd|^Forte oral susp|^\d*\.?\d*\/?\d*\.?\d*\s?cap\s*\d*\-?|^\d*\.?\d*\/?\d+\.?\d*\s?mL|^\d*\.?\d*\/?\d*\.?\d*\s?FC caplet|^\d*\.?\d*\/?\d*\.?\d*\s?FC Caplet|^\d*\.?\d*\/?\d*\.?\d*\s?brown tab|^caplet|^Caplet\/Effervescent tab?|^Caplet|^\d+\.?\d*\/?\d+\.?\d*\s?cap|^cap\/?|^Cap|^syr\/?mL|^caplet|^Forte dry susp|^inj|^insulin|^susp|^sachet|^Sachet|^syr|^DHA|^milk powd|^oint|^powd|^mL|^\d+\-?'
        # pat_match = re.findall(remove_raw_from_mat,std_mat)
        # if(len(pat_match)!=0):
        #     current_std_mat=std_mat.replace(pat_match[0],'')
        std_mat=std_mat.strip()
        current_std_mat=std_mat
    elif(len(con_match_in_mat)!=0):
        current_mat=mat
        for cm in con_match_in_mat:
            std_mat=std_mat.replace(cm,'')
            std_mat=std_mat.replace('  ',' ')
        # remove_raw_from_mat = r'^\d*\.?\d*\/?\d*\.?\d*\s?white tab|^\d*\.?\d*\/?\d*\.?\d*\s?blue tab|^\d*\.?\d*\/?\d*\.?\d*\s?large tab|^FC tab|^Forte tab|^forte tab|^tab|^\d*\.?\d*\/?\d*\.?\d*\s?kCal|^\d*\.?\d*\/?\d+\.?\d*\s?tab|^syr\/mL|^tab\/?\s?susp|^tab\/?\s?liqd|^tab\/?\s?syr|^tab\/?\s?drag|^forte caplet|^Forte caplet|^Forte cap|^FC caplet|^Forte dry syr|^forte syr|^forte liqd|^Forte oral susp|^\d*\.?\d*\/?\d*\.?\d*\s?cap\s*\d*\-?|^\d*\.?\d*\/?\d+\.?\d*\s?mL|^\d*\.?\d*\/?\d*\.?\d*\s?FC caplet|^\d*\.?\d*\/?\d*\.?\d*\s?FC Caplet|^\d*\.?\d*\/?\d*\.?\d*\s?brown tab|^caplet|^Caplet\/Effervescent tab?|^Caplet|^\d+\.?\d*\/?\d+\.?\d*\s?cap|^cap\/?|^Cap|^syr\/?mL|^caplet|^Forte dry susp|^inj|^insulin|^susp|^sachet|^Sachet|^syr|^DHA|^milk powd|^oint|^powd|^mL|^\d+\-?'
        # pat_match = re.findall(remove_raw_from_mat,std_mat)
        # if(len(pat_match)!=0):
        #     current_std_mat=std_mat.replace(pat_match[0],'')
        std_mat=std_mat.replace('w/w','')
        std_mat=std_mat.replace('w/v','')
        std_mat=std_mat.strip()
        current_std_mat=std_mat
    if(len(format_match)!=0):
        pattern = re.compile(re.escape(format_match[0].rstrip()), re.IGNORECASE)
        std_mat = pattern.sub('', std_mat)
        # std_mat=std_mat.replace(format_match[0].strip(),'')
        current_std_mat=std_mat
    return d,con,current_mat,current_std_mat,format_org,std_format
with open('MIMS Malaysia.csv','w') as file:
    writer = csv.writer(file)
    writer.writerow(["brand","manufacturer","cims_class","material","standard_material","format_original","standard_format","concentration","dosage","uom","atc_code","atc_detail","amount","mims_class"])
def read_text_file(file):  
    with open(file) as f:
        data= [json.loads(line) for line in f]    
        brand=[]    
        manufacturer=[]
        cimsClass=[]
        atcCode=[]
        atcDetail=[]
        material=[]
        dosage=[]
        uom=[]
        form=[]
        products=[]
        formater=[]
        concentration=[]
        format_original=[]
        l=[]
        activeIngredientsList=[]
        std_material=[]
        mimsClass=[]
        amount=[]
        for item in data:
            d=''
            con=''
            dosage_match=''
            con_match=''
            dosage_match_in_mat=''
            con_match_in_mat=''
            dos_match_from_form=''
            con_match_from_form=''
            format_match=''
            format_org=''
            std_format=''
            current_mat=''
            current_std_mat=''
            drug=''
            org_form=''
            std_uom=''
            drug_name=[]
            print("--------------------------------------------------------------------------------",item['drugName'])
            products= item['details']['products']
            activeIngredients=item['details']['activeIngredients']
            drugName=item['drugName']
            drugName=drugName.replace(',','')
            atc_code=item['details']['atcCode']
            atc=item['details']['atc']
            manf=item['details']['manufacturer']
            cims_class=item['details']['cimsClass']
            mims_class=item['details']['mimsClass']
            drugClassification=item['drugClassification']
            if(len(products)==0):
                if(len(activeIngredients)!=0):
                    activeIngredientsList=activeIngredients
                    if(activeIngredients[0].startswith('Per ')):
                        per='Per '
                        activeIngredientsList =  [per+e for e in activeIngredients[0].split(per) if e]
                        local_keywords_list = keywords_list
                        mat_to_map_form,material_list = get_sub_string_from_mat(activeIngredientsList, local_keywords_list)
                    else:
                            mat_to_map_form = ['']
                    for i,entry in enumerate(activeIngredientsList):
                            brand.append(drugName)        
                            manufacturer.append(manf)
                            cimsClass.append(cims_class)
                            mimsClass.append(mims_class)
                            if(len(atc_code)!=0):
                                atcCode.append(atc_code)
                            elif(len(atc_code)==0):
                                atcCode.append('')
                            if(len(atc)!=0):
                                atc=atc.replace(';','')
                                atc=atc.replace(',','')
                                atc=atc.replace('  ',' ')
                                atc=atc.strip('.')
                                atcDetail.append(atc)
                            elif(len(atc)==0):
                                atcDetail.append('')
                            uom.append('')
                            amount.append('')
                            d=''
                            con=''
                            format_org=''
                            std_format=''
                            entry=entry.replace(',','')
                            entry=entry.replace(';','')
                            entry=entry.replace('&amp;','&')
                            entry=entry.strip()
                            entry=entry.strip('.')
                            std_mat=entry
                            mat=entry
                            d,con,current_mat,current_std_mat,format_org,std_format=extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,mat_to_map_form[i],format_org,std_format,format_match)
                            format_original.append(format_org)
                            formater.append(std_format)
                            dosage.append(d)
                            concentration.append(con)
                            material.append(current_mat)
                            std_material.append(current_std_mat)
                elif(len(activeIngredients)==0):
                        concentration.append('')
                        dosage.append('')
                        if(drugClassification=='Generic'):
                                #If drugClassification is generic and activeIngredients is empty then drugName becomes activeIngredient for that drug
                                current_mat=drugName
                                current_std_mat=drugName
                        material.append(current_mat)
                        std_material.append(current_std_mat)
                        brand.append(drugName)        
                        manufacturer.append(manf)
                        cimsClass.append(cims_class)
                        mimsClass.append(mims_class)
                        
                        if(len(atc_code)!=0):
                            atcCode.append(atc_code)
                        elif(len(atc_code)==0):
                            atcCode.append('')
                        
                        std_atc=atc.replace(';','')
                        standard_atc=std_atc.replace(',','')
                        standard_atc=standard_atc.replace('  ',' ')
                        if(len(atc)!=0):
                            atc=atc.replace(';','')
                            atc=atc.replace(',','')
                            atc=atc.replace('  ',' ')
                            atc=atc.strip('.')
                            atcDetail.append(atc)
                        elif(len(atc)==0):
                            atcDetail.append('')
                        format_original.append('')
                        formater.append('')
                        uom.append('')
                        amount.append('')
                        d=''
                        con=''
                        format_org=''
                        std_format=''
            elif(len(products)!=0): 
                forms_list = get_forms(products)
                local_keywords_list = append_keywords_from_form_to_keywords_list(forms_list)
                if( len(activeIngredients)!=0):
                    if(activeIngredients[0].startswith('Per ')):
                        per='Per '
                        activeIngredientsList =  [per+e for e in activeIngredients[0].split(per) if e]
                        mat_to_map_form,material_list = get_sub_string_from_mat(activeIngredientsList,local_keywords_list)
                        if(len(material_list) != len(forms_list)):
                                print("drugname : ",drugName,"material list : ",material_list,"forms list : ",forms_list)
                                continue
                        list_of_dicts = map_form_to_mat(forms_list,mat_to_map_form,material_list)
                for product in products:
                    packaging= product['packaging']
                    std_packaging=remove_substring_in_brackets(packaging)
                    print("std_pacaking",std_packaging)
                    org_form= product['form']
                    # form=org_form
                    replaced=std_packaging.replace('&#39;s','')
                    decode_x=replaced.replace('&#215;','x')
                    l=decode_x.split(';')
                    for i in l:
                        i=i.replace(',','')
                        i=i.replace(';','')
                        std_uom=remove_substring_in_brackets(i)
                        std_uom=std_uom.strip()
                        print("uom",std_uom)
                        # if(drugName.find('/')!=-1):
                        #     drug_name=drugName.split('/')
                        #     drug_match_in_form=''
                        #     for drug in drug_name:
                        #             if(org_form.find(drug)!=-1):
                        #                 drug_match_in_form=form[:len(drug)]
                        #                 current_drug=drug
                        #     form=form.replace(drug_match_in_form,'')
                        # else:
                        #     current_drug=drugName
                        org_form=org_form.replace(';','')
                        org_form=org_form.replace(',','')
                        form=org_form
                        pattern = re.compile(re.escape(drugName), re.IGNORECASE)
                        form = pattern.sub('', form)
                        form=form.strip()
                        print("form after removing drugName:",form)
                        if form and form[0].isdigit():
                            dos_match_from_form = re.findall('\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?spray|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?actuation|\d+\.?\d*\/?\d*\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?dose|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?metered spray|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\/?\-?\d*\.?\d*\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\d+\s?DHA',org_form, re.DOTALL)
                            con_match_from_form= re.findall('\d+\.?\d*\s?%',org_form, re.DOTALL)
                            if(len(dos_match_from_form)!=0 and len(con_match_from_form)!=0):
                                result=''
                                for m in dos_match_from_form:
                                    if(m.find('/')==-1):
                                        result+=m+"/"
                                    else:
                                        result=m
                                d=result.strip('/')
                                result=''
                                for m in con_match_from_form:
                                    if(m.find('/')==-1):
                                        result+=m+"/"
                                    else:
                                        result=m
                                con=result.strip('/')
                                form=form.replace(con,'')
                                form=form.replace('w/w','')
                                form=form.replace('w/v','')
                                form=form.replace(d,'')
                                form=form.replace(con,'')
                                format_org=form
                            elif(len(dos_match_from_form)!=0):
                                con=''
                                result=''
                                for m in dos_match_from_form:
                                    if(m.find('/')==-1):
                                        result+=m+"/"
                                    else:
                                        result=m
                                d=result.strip('/')
                                format_org=form.replace(d,'')
                            elif(len(con_match_from_form)!=0):
                                d=''
                                result=''
                                for m in con_match_from_form:
                                    if(m.find('/')==-1):
                                        result+=m+"/"
                                    else:
                                        result=m
                                con=result.strip('/')
                                form=form.replace(con,'')
                                form=form.replace('w/w','')
                                form=form.replace('w/v','')
                                format_org=form
                            else:
                                d=''
                                con=''
                                remove_raw_num=re.findall(r"\d+",form)
                                if(remove_raw_num):
                                    for n in remove_raw_num:
                                        form=form.replace(n,'')
                                format_org=form
                        else:
                            m=re.search(r"\d",form)
                            if(m):
                                if(form.find('%')!=-1):
                                    end_index=form.find('%')
                                    con=form[m.start():end_index+1]
                                    # con=con.replace(' ','')
                                    d=''
                                    # material_match=con
                                elif(form.find('%')==-1):
                                    d=form[m.start():]
                                    # material_match=d
                                    # d=d.replace(' ','')
                                    # d=d.replace(',','')
                                    con=''
                                format_org=form[:m.start()]
                            else:
                                format_org=form
                                d=''
                                con=''
                        format_org=format_org.strip()
                        std_format=search(format_org)
                        if(std_format==None):
                            std_format=''
                        if(len(activeIngredients)!=0):
                                activeIngredientsList=activeIngredients
                                if(activeIngredients[0].startswith('Per ')):
                                    per='Per '
                                    activeIngredientsList =  [per+e for e in activeIngredients[0].split(per) if e]
                                    for entry in activeIngredientsList:
                                            matched_material,material_to_map_form = get_matching_material(org_form,list_of_dicts)
                                            print("matched_material :",matched_material,"material to map form : " ,material_to_map_form)
                                            brand.append(drugName)        
                                            manufacturer.append(manf)
                                            cimsClass.append(cims_class)
                                            mimsClass.append(mims_class)
                                            if(len(atc_code)!=0):
                                                atcCode.append(atc_code)
                                            elif(len(atc_code)==0):
                                                atcCode.append('')
                                            if(len(atc)!=0):
                                                atc=atc.replace(';','')
                                                atc=atc.replace(',','')
                                                atc=atc.replace('  ',' ')
                                                atc=atc.strip('.')
                                                atcDetail.append(atc)
                                            elif(len(atc)==0):
                                                atcDetail.append('')
                                            std_uom=std_uom.strip()
                                            uom.append(std_uom)
                                            amount.append('')
                                            mat=matched_material
                                            std_mat=matched_material
                                            d,con,current_mat,current_std_mat,format_org,std_format = extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,material_to_map_form,format_org,std_format,format_match)
                                            d=d.replace(' ','')
                                            d=d.replace(',','')
                                            con=con.replace(' ','')
                                            con=con.replace(',','')
                                            dosage.append(d)
                                            concentration.append(con)
                                            format_original.append(format_org)
                                            formater.append(std_format)
                                            current_mat = current_mat.replace(',','')
                                            material.append(current_mat)
                                            std_material.append(current_std_mat)
                                            break;
                                else:
                                    for entry in activeIngredientsList:
                                            entry=entry.replace(',','')
                                            entry=entry.replace(';','')
                                            entry=entry.replace('&amp;','&')
                                            entry=entry.strip()
                                            entry=entry.strip('.')
                                            brand.append(drugName)        
                                            manufacturer.append(manf)
                                            cimsClass.append(cims_class)
                                            mimsClass.append(mims_class)
                                            if(len(atc_code)!=0):
                                                atcCode.append(atc_code)
                                            elif(len(atc_code)==0):
                                                atcCode.append('')
                                            if(len(atc)!=0):
                                                atc=atc.replace(';','')
                                                atc=atc.replace(',','')
                                                atc=atc.replace('  ',' ')
                                                atc=atc.strip('.')
                                                atcDetail.append(atc)
                                            elif(len(atc)==0):
                                                atcDetail.append('')
                                            std_uom=std_uom.strip()
                                            uom.append(std_uom)
                                            amount.append('')
                                            mat=entry
                                            std_mat=entry
                                            d,con,current_mat,current_std_mat,format_org,std_format = extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,"",format_org,std_format,format_match)
                                            d=d.replace(' ','')
                                            d=d.replace(',','')
                                            con=con.replace(' ','')
                                            con=con.replace(',','')
                                            dosage.append(d)
                                            concentration.append(con)
                                            format_original.append(format_org)
                                            formater.append(std_format)
                                            material.append(current_mat)
                                            std_material.append(current_std_mat)    
                        elif(len(activeIngredients)==0):
                            if(drugClassification=='Generic'):
                                current_mat=drugName
                                current_std_mat=drugName
                            material.append(current_mat)
                            d=d.replace(' ','')
                            d=d.replace(',','')
                            con=con.replace(' ','')
                            con=con.replace(',','')
                            dosage.append(d)
                            concentration.append(con)
                            std_material.append(current_std_mat)
                            brand.append(drugName)        
                            manufacturer.append(manf)
                            cimsClass.append(cims_class)
                            mimsClass.append(mims_class)
                            if(len(atc_code)!=0):
                                atcCode.append(atc_code)
                            elif(len(atc_code)==0):
                                atcCode.append('')
                            if(len(atc)!=0):
                                atc=atc.replace(';','')
                                atc=atc.replace(',','')
                                atc=atc.replace('  ',' ')
                                atc=atc.strip('.')
                                atcDetail.append(atc)
                            elif(len(atc)==0):
                                atcDetail.append('')
                            std_uom=std_uom.strip()
                            uom.append(std_uom)
                            amount.append('')
                            format_original.append(format_org)
                            formater.append(std_format)
    print(brand,manufacturer,cimsClass,material,std_material,format_original,formater,concentration,dosage,uom,atcCode,atcDetail,amount,mimsClass)
    file = open('MIMS Malaysia.csv', 'a', newline ='')
    with file:
        write = csv.writer(file)
        write.writerows(zip(brand,manufacturer,cimsClass,material,std_material,format_original,formater,concentration,dosage,uom,atcCode,atcDetail,amount,mimsClass))      
def search(form):
        es = Elasticsearch("http://admin:admin@localhost:9200/", ca_certs=False, verify_certs=False)
        query = {
	       "query": {
	       "multi_match" : {
	       "query":  form,
	       "type":       "most_fields",
	       "fields": ["format"],
	       "fuzziness": "AUTO"
	       }
	      }
	     }
        resp = es.search(index="format_index", body=query)
        if len(resp['hits']['hits']) != 0:
            doc = resp['hits']['hits'][0]
            standard_format=doc['_source']['format']
            return standard_format
for file in os.listdir():
    if file.endswith(".jsonl"):
        read_text_file(file)