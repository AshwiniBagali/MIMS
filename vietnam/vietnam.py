import csv
import json
import os
import pandas as pd
import re
from elasticsearch import Elasticsearch, helpers
import copy 
map1 = {}
def remove_substring_in_brackets(packaging):
    # Define the regex pattern to check for substrings within brackets
    pattern = r'\([^()]*\)'  # This pattern matches anything between '(' and ')'

    # Use the re.sub() function repeatedly to remove all occurrences of substrings within brackets
    while re.search(pattern, packaging):
        packaging = re.sub(pattern, '', packaging)

    return packaging
keywords_list = ['of', 'is', 'a', 'the', 'per', 'tab', 'syr', 'cap', 'fc', 'caplet', 'oral', 'susp', 'oral', 'inj', 'injection', 'soln', 'solution', 'sugar-coated', 'forte', 'dry', 'paed', 'for', 'fC', 'drops', 'powd', 'liqd', 'mouthwash', 'rectal', 'oint', 'cream', 'daily', 'facial', 'moisturizer', 'gel', 'inhaler', 'vaccine', 'infant', 'softgel', 'eye', 'ointment', 'effervescent', 'chewtab', 'active', 'captab', 'dispersible', 'xr-fc', 'plus', 'chewable', 'extra', 'adult', 'mite', 'film-coated', 'softcap', 'soft', 'sachet', 'syrup', 'drag', 'bottle', 'mouthspray', 'toothpaste', 'shampoo', 'diskus', 'serum', 'lotion', 'spray']
def get_forms(products):
    forms_list=[]
    products = sorted(products, key=lambda x: len(x['form']), reverse=True)#Get products in descending order
    for product in products:
        cleaned_form = product['form']
        cleaned_form = cleaned_form.replace(',','')
        forms_list.append(cleaned_form)
    return forms_list
def append_keywords_from_form_to_keywords_list(forms_list,drug_name): #Append keywords from form to keywords to map and remove it form material
    local_keywords_list = copy.deepcopy(keywords_list)
    
    for current_form in forms_list:
        current_form=current_form.split()
        for word in current_form:
            if word.lower() not in local_keywords_list:
                local_keywords_list.append(word.lower())
    for current_drug in drug_name:
        current_drug=current_drug.split()
        for word in current_drug:
            if word.lower() not in local_keywords_list:
                local_keywords_list.append(word.lower())
    print("keywords list for current line item : ",local_keywords_list)
    return local_keywords_list
def split_material(activeIngredients,drug_name):
    string = activeIngredients[0]
    pattern = r'(\.\s*<strong>\s*([A-Za-z]+)|\s*<strong>\s*\.\s*([A-Za-z]+)|\,\s*<strong>\s*per|\,\s*<strong>\s*Each|\.\s*<em>\s*per|\.\s*<em>\s*({})|\s*<em>\s*\.\s*({}))'.format('|'.join((drug.split()[0]) for drug in drug_name), '|'.join((drug.split()[0]) for drug in drug_name))
    indices = [0]+[m.start()+1 for m in re.finditer(pattern, string,re.IGNORECASE)] + [None]#appending first and last items to list
    active_ingredients_list = [string[indices[i]:indices[i+1]] for i in range(len(indices)-1)]  
    return active_ingredients_list
def check_string(input_string,find_index):
    # Check if ':' exists in the string
    if find_index != -1:
        # Extract substrings before and after ':'
        before_colon = input_string[:find_index]
        after_colon = input_string[find_index + 1:]

        # Check if both substrings contain digits
        if not (before_colon.isdigit() and after_colon.isdigit()):
            return True  # String contains ':' but doesn't have digit:digit format
    return False  # String doesn't contain ':' or contains digit:digit format
def material_clean_up(item):
    item = item.strip('.')
    item = item.replace('&amp;','&')
    # item = item.replace(',','')
    item = item.replace(';','')
    item = item.replace('<sup>','^')
    item = item.replace('<sup >','^')
    item = item.replace('< sup>','^')
    item = item.replace('</sup>','')
    item = item.replace('</ sup>','')
    item = item.replace('</sup >','')
    item = item.replace('< /sup>','')
    item = item.replace('<sub>','')
    item = item.replace('< sub>','')
    item = item.replace('<sub >','')
    item = item.replace('</ sub>','')
    item = item.replace('</sub >','')
    item = item.replace('</sub>','')
    item = item.replace('< /sub>','')
    item = item.replace('<em>','') 
    item = item.replace('<em >','')
    item = item.replace('< em>','') 
    item = item.replace('</em>','')
    item = item.replace('</em >','')
    item = item.replace('</ em>','')
    item = item.replace('< /em>','')
    item = item.replace('<strong>','')
    item = item.replace('</strong>','')
    item = item.replace('\u200b','')
    item = item.strip()
    item = item.strip('.')
    item = item.strip()
    return item
def get_material(activeIngredients,drugName):#
    string_in_bold = []
    # cleaned_active_ingredients = []
    active_ingredients = []
    cleaned_string_in_bold = ''
    # activeIngredientsList = activeIngredients
    # find_string_to_split = re.findall(r'\.\s*<strong>', activeIngredients[0])
    # if(find_string_to_split):
    #     # Split the string using the matches
    #     split_active_ingredients = re.split(r'\.\s*<strong>', activeIngredients[0])
    #     # Combine the split parts with the matches to get the desired result
    #     activeIngredientsList = [split_active_ingredients[0]] + [match + split for match, split in zip(find_string_to_split, split_active_ingredients[1:])]
    if(len(activeIngredients)!= 0):
        for item in activeIngredients:
            bold_words = re.findall(r'\.?\s*<strong>(.*?)</strong>', item)
            # bold_words = re.findall(r'(.*?(:\s?</(?:strong|em)>|</(?:strong|em)>\s?\(.*?\)\s?:|</(?:strong|em)>\s?:|</(?:strong)>\s?))', item,re.DOTALL)
            # find_index = item.find('</strong>')
            # regex = re.search('\d+:\d+',item,re.DOTALL)
            # if(len(bold_words)!=0):
            #    bold_words = material_clean_up(bold_words[0][0])
            item = material_clean_up(item)
            find_index = item.find(':')
            raw_material = ''
            if(find_index!=-1):
                raw_material = item[:find_index]
            # if(len(bold_words)!=0):
            #     string_in_bold.append(bold_words[0])
            #     # cleaned_active_ingredients.append(re.sub(r'\.?\s*<strong>.*?</strong>', '', item))
            #     item = item.replace('<strong>','')
            #     item = item.replace('</strong>','')
            # else:
            #     string_in_bold.append('')
            # active_ingredients.append(item)
                print(raw_material,drugName[0].lower())
                if(raw_material.lower().find('each ')!=-1 or raw_material.lower().find('per ')!=-1 or raw_material.lower().find(drugName[0].lower())!=-1 or raw_material.lower().find('cream')or raw_material.lower().find('ointment')):
                    print("bold:",raw_material)
                    cleaned_string_in_bold = raw_material.strip()
                    cleaned_string_in_bold = cleaned_string_in_bold.strip('.')
                    cleaned_string_in_bold = cleaned_string_in_bold.strip(':')
                    cleaned_string_in_bold = cleaned_string_in_bold.strip()
                    pattern = r'\b(?:Caplet/Effervescent tab|cream/oint|tab/drag|packet/capsule|eye drops/ear drops|tablet/package|packet/tablet|tablet/capsule|solution/per tablet|tab/\d+\s*mL|oint/powd|cap/\d+\s*mL|caplet/\d+\s*mL|/{}|{}/)\b'.format(re.escape(drugName), re.escape(drugName))
                    matches = re.findall(pattern, cleaned_string_in_bold, re.IGNORECASE)
                    if(matches):  
                        split_bold = cleaned_string_in_bold.split('/')
                        append_index = item.find(split_bold[-1])
                        for i,word in enumerate(split_bold):
                            cleaned_item = word + " " +item[append_index+len(split_bold[-1]):]
                            cleaned_item = re.sub(r'\s+', ' ', cleaned_item)
                            active_ingredients.append(cleaned_item.strip())
                            string_in_bold.append(word.strip())
                    else:
                        string_in_bold.append(cleaned_string_in_bold)
                        active_ingredients.append(item)
                else:
                    string_in_bold.append('')
                    active_ingredients.append(item)
            elif(len(bold_words)!=0):
                cleaned_string_in_bold = bold_words[0].strip()
                cleaned_string_in_bold = cleaned_string_in_bold.strip(';')
                cleaned_string_in_bold = cleaned_string_in_bold.strip(':')
                string_in_bold.append(cleaned_string_in_bold)
                active_ingredients.append(item)
            else:
                string_in_bold.append('')
                active_ingredients.append(item)
            print("string in bold:",string_in_bold)
    return string_in_bold,active_ingredients
def get_sub_string_from_mat(activeIngredientsList,local_keywords_list): #Get starting substring from material to be mapped with form and then remove
        mat_to_map_list = []
        material_list = []
        for e,entry in enumerate(activeIngredientsList):
            entry=entry.replace('&amp;','&')
            entry=entry.replace(',','')
            entry=entry.replace(';','')
            entry=entry.strip()
            entry=entry.strip('.')
            raw_mat = ''
            dosage_match_in_mat = re.search('[^\w](\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg\/?dose|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg\/?actuation|\d+\.?\d*\/?\d*\.?\d*\s?u\/?mL\s?\+?\s?\d*\.?\d*\s?mcg\/?mL|\d+\.?\d*\/?\d*\.?\d*\s?mg\/?mL|\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg(?:\/\d+\.?\d*\s?mg)*|\d+\.?\d*\/?\-?\d*\.?\d*/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\sg\s|\smL\s|\sL\s|\samp\s|\spuff\s|\skCal\s|\sbar\s)[^\w]'," "+entry+" ", re.DOTALL)
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
            mat_to_map_list.append(raw_mat)
        return mat_to_map_list,material_list
def isRowUnique(row,element):#check if row with highest count is unique
    c = 0
    for i in range(len(row)):
        if (row[i] == element):
            c += 1
            if c > 1:
                return False
    return True

def clearForms(rows,index):#Remove mapped form
    for j , row in enumerate(rows):
        for i, item in enumerate(row["values"]):
            if(i==index):
                rows[j]["values"][i] = -1
    return rows
    
def map_form_to_mat(forms_list,mat_to_map_form,material_list,drug_name):#map form to material with highest count match
    list_of_dicts = []
    for i in range(len(mat_to_map_form)):
        dictionary = {
            "form": forms_list[i],
            "count": 0,
            "activeIngredient":material_list[i],
            "materialToMapForm":mat_to_map_form[i],
            "drugName":""
        }
        list_of_dicts.append(dictionary)
        # arr = [[0]*len(forms_list)]*len(mat_to_map_form)
    rows =[]
    for j,f in enumerate(mat_to_map_form):
        f = re.sub(r'(\d) (\D)', r'\1\2', f) #Remove space for mapping
        row = {
                "index": j,
                "values":[]
            }
        # current_entry=list_of_dicts[j]
        for k,a in enumerate(forms_list):
#             a=a.lower()
            # a = re.sub(r'(\d) (\D)', r'\1\2', a) #Remove space for mapping
            count=0
            words_in_form=a.split()
            for word in words_in_form:
                if word.lower() in f.lower():
                    count=count+1
            row["values"].append(count)
            # if(current_entry['count']<count):
            #     current_entry['count']=count
                #current_entry['form']=f
        rows.append(row)
    while len(rows) != 0:
        for row in rows:
            max_element = 0
            max_index = 0
            for i , item in enumerate(row["values"]):
                if max_element <= item:
                    max_element = item
                    max_index = i
            if(isRowUnique(row["values"],max_element)):
                list_of_dicts[row["index"]]["form"] = forms_list[max_index]
                rows.remove(row)
                rows = clearForms(rows,max_index) 
    #     list_of_dicts = sorted(list_of_dicts, key=lambda x: x['count'], reverse=True)#sort dictionary by highest count match
#     not_found_index=0
#     for l,item in enumerate(list_of_dicts):
#         if(item['form'] in forms_list):
#             forms_list.remove(item['form'])
#         else:
#             not_found_index=l
#     if(len(forms_list)!=0):
#         list_of_dicts[not_found_index]['form']=forms_list[0] 
    list_of_dicts = sorted(list_of_dicts, key=lambda x: len(x['form']), reverse=True)#sort dictionary by form length
    if(len(drug_name)>1):
        list_of_dicts = map_drug_name_to_mat_and_form(list_of_dicts,drug_name)
    return list_of_dicts

def map_drug_name_to_mat_and_form(list_of_dicts,drug_name):#map drugName to material and form with highest count match   
    # for c in list_of_dicts:
    #     c['count'] = 0 
    # for j,d in enumerate(drug_name):
    #     for k, current_entry in enumerate(list_of_dicts):
    #         count=0
    #         words_in_drug_name= d.split()
    #         for word in words_in_drug_name:
    #             if word.lower() in current_entry["form"].lower():
    #                 count=count+1
    #         if(current_entry['count']<count):
    #             current_entry['count']=count
    #             current_entry['drugName']= d
    # not_found_index=0
    # list_of_dicts = sorted(list_of_dicts, key=lambda x: x['count'], reverse=True)#sort dictionary by highest count match
    # for l,item in enumerate(list_of_dicts):
    #     if(item['drugName'] in drug_name):
    #         drug_name.remove(item['drugName'])
    #     else:
    #         not_found_index=l
    # if(len(drug_name)!=0):
    #     list_of_dicts[not_found_index]['drugName']=drug_name[0]
    # list_of_dicts = sorted(list_of_dicts, key=lambda x: len(x['drugName']), reverse=True)#sort dictionary by drugName length
    # return list_of_dicts
    rows =[]
    for j,a in enumerate(list_of_dicts):
        row= {
                "index": j,
                "values":[]
            }
        # current_entry=list_of_dicts[j]
        for k,f in enumerate(drug_name):
#             a=a.lower()
            count=0
            words_in_form=a["form"].split()
            for word in words_in_form:
                if word.lower() in f.lower():
                    count=count+1
            row["values"].append(count)
            # if(current_entry['count']<count):
            #     current_entry['count']=count
                #current_entry['form']=f
        rows.append(row)
    while len(rows) != 0:
        for row in rows:
            max_element = 0
            max_index = 0
            for i , item in enumerate(row["values"]):
                if max_element <= item:
                    max_element = item
                    max_index = i
            if(isRowUnique(row["values"],max_element)):
                list_of_dicts[row["index"]]["drugName"] = drug_name[max_index]
                rows.remove(row)
                rows = clearForms(rows,max_index)
    list_of_dicts = sorted(list_of_dicts, key=lambda x: len(x['drugName']), reverse=True)
    return list_of_dicts
def map_drug_name_to_mat(drug_name_list,mat_to_map_drug,material_list):#map drugName to material with highest count match
    list_of_dicts = []
    for i in range(len(mat_to_map_drug)):
        dictionary = {
            "drugName": drug_name_list[i],
            "count": 0,
            "activeIngredient":material_list[i],
            "materialToMapDrug":mat_to_map_drug[i]
        }
        list_of_dicts.append(dictionary)
#     for j,d in enumerate(drug_name_list):
#         for k,a in enumerate(mat_to_map_drug):
# #             a=a.lower()
#             count=0
#             current_entry=list_of_dicts[k]
#             words_in_drug_name=d.split()
#             for word in words_in_drug_name:
#                 if word.lower() in a.lower():
#                     count=count+1
#             if(current_entry['count']<count):
#                 current_entry['count']=count
#                 current_entry['drugName']=d
    # list_of_dicts = sorted(list_of_dicts, key=lambda x: x['count'], reverse=True)#sort dictionary by highest count match
    # not_found_index=0
    # for l,item in enumerate(list_of_dicts):
    #     if(item['drugName'] in drug_name_list):
    #         drug_name_list.remove(item['drugName'])
    #     else:
    #         not_found_index=l
    # if(len(drug_name_list)!=0):
    #     list_of_dicts[not_found_index]['drugName']=drug_name_list[0]
    rows =[]
    for j,f in enumerate(drug_name_list):
        row = {
                "index": j,
                "values":[]
            }
        for k,a in enumerate(mat_to_map_drug):
#             a=a.lower()
            count=0
            words_in_form=a.split()
            for word in words_in_form:
                if word.lower() in f.lower():
                    count=count+1
            row["values"].append(count)
            # if(current_entry['count']<count):
            #     current_entry['count']=count
                #current_entry['form']=f
        rows.append(row)
    while len(rows) != 0:
        for row in rows:
            max_element = 0
            max_index = 0
            for i , item in enumerate(row["values"]):
                if max_element <= item:
                    max_element = item
                    max_index = i
            if(isRowUnique(row["values"],max_element)):
                list_of_dicts[row["index"]]["drugName"] = drug_name_list[max_index]
                rows.remove(row)
                rows = clearForms(rows,max_index)
    list_of_dicts = sorted(list_of_dicts, key=lambda x: len(x['drugName']), reverse=True)#sort dictionary by form length
    return list_of_dicts
def map_drug_name_to_form(drug_name_list,forms_list,mat_to_map_form,material_list):#map drugName to form with highest count match
    list_of_dicts = []
    for i in range(len(forms_list)):
        dictionary = {
            "drugName": drug_name_list[i],
            "count": 0,
            "form":forms_list[i],
            "activeIngredient":material_list[0],#No need to map material as it's only single material
            "materialToMapForm":mat_to_map_form[0]
        }
        list_of_dicts.append(dictionary)
    rows =[]
    for j,f in enumerate(drug_name_list):
        row = {
                "index": j,
                "values":[]
            }
        # current_entry=list_of_dicts[j]
        for k,a in enumerate(forms_list):
#             a=a.lower()
            count=0
            words_in_form=a.split()
            for word in words_in_form:
                if word.lower() in f.lower():
                    count=count+1
            row["values"].append(count)
            # if(current_entry['count']<count):
            #     current_entry['count']=count
                #current_entry['form']=f
        rows.append(row)
    while len(rows) != 0:
        for row in rows:
            max_element = 0
            max_index = 0
            for i , item in enumerate(row["values"]):
                if max_element <= item:
                    max_element = item
                    max_index = i
            if(isRowUnique(row["values"],max_element)):
                list_of_dicts[row["index"]]["form"] = forms_list[max_index]
                rows.remove(row)
                rows = clearForms(rows,max_index) 
    list_of_dicts = sorted(list_of_dicts, key=lambda x: len(x['form']), reverse=True)#sort dictionary by form length
    return list_of_dicts
def get_matching_material(current_form,current_drug,list_of_dicts):#get matching material for cuurent form
    matching_mat=''
    material_to_map=''
    for m in list_of_dicts :
        if(len(m.get('drugName'))!=0):#Get mapped material for drugName and form
            if m.get('form') == current_form and m.get('drugName') == current_drug:
                matching_mat = m.get('activeIngredient')
                material_to_map = m.get('materialToMapForm')
                break
        if(len(current_form) == 0):#Get mapped material for drugName
            if  m.get('drugName') == current_drug:
                matching_mat = m.get('activeIngredient')
                material_to_map = m.get('materialToMapDrug')
                break
        if(len(m.get('drugName'))==0):
            if m.get('form') == current_form:#Get mapped material for form
                matching_mat = m.get('activeIngredient')
                material_to_map = m.get('materialToMapForm')
                break
    return matching_mat,material_to_map
def get_dosage_from_packaging(dos_match_from_packaging,con_match_from_packaging,d,con,packaging):
    pattern = r'\([^()]*\)'
    dosage_in_packaging = re.search(pattern, packaging)
    if(dosage_in_packaging):
        dos_match_from_packaging = re.findall('\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?spray|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?puff|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?actuation|\d+\.?\d*\/?\d*\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?dose|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?metered spray|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\/?\-?\d*\.?\d*\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\d+\s?DHA',dosage_in_packaging.group(0), re.DOTALL)
        con_match_from_packaging= re.findall('\d+\.?\d*\s?%',dosage_in_packaging.group(0), re.DOTALL)
        if(len(dos_match_from_packaging)!=0):
            d = dos_match_from_packaging[0]
            con = ''
        elif(len(con_match_from_packaging) !=0):
            con = con_match_from_packaging
            d = ''
    return d,con
def extract_dos_con_from_drug(dos_match_from_drug,con_match_from_drug,dos,c,drug):
    dos_match_from_drug = re.findall('[^\w](\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mg|\d+\.?\d*\s?MG|\d+\.?\d*\s?g|\d+\.?\d*\s?IU)[^\w]'," "+drug+" ", re.DOTALL)
    con_match_from_drug = re.findall('\d+\.?\d*\s?%\/\d+\.?\d*\s?%|\d+\.?\d*\s?%',drug, re.DOTALL)
    if(len(dos_match_from_drug)!=0):
        dos = dos_match_from_drug[0]
    if(len(con_match_from_drug)!=0):
        c = con_match_from_drug[0]
    return dos,c
def extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,material_to_map,format_org,std_format,format_match):
    std_mat=std_mat.strip()
    mat=mat.strip()
    regex_to_match_comma_in_dos = re.findall(r'\d+\,\d+',mat,re.DOTALL)
    for match in regex_to_match_comma_in_dos:
        std_match = match.replace(',','')
        mat = mat.replace(match,std_match)
        std_mat = std_mat.replace(match,std_match)
    if(len(d)==0 and len(con)==0 ):
        temp_mat = mat
        remove_duplicate_dosage = re.findall('\d+\.?\d*\s?mg\/\-?\d*\.?\d*\s?mg\/\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?mg\/\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?mcg\/\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/\-?\d*\.?\d*\s?mg|\d+\.?\d*\/\-?\d*\.?\d*\s?mcg',material_to_map,re.DOTALL)
        if(len(remove_duplicate_dosage)!=0):
            temp_mat = temp_mat.replace(remove_duplicate_dosage[0],'')
        # dosage_match = re.findall('\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\d*\.?\d*\s?mL',mat, re.DOTALL)# Regex extracting 2 gummies as 2g
        dosage_match = re.findall('[^\w](\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?MIU)[^\w]'," "+temp_mat+" ", re.DOTALL)
        con_match = re.findall('\d+\.?\d*\s?%',temp_mat, re.DOTALL)
        regex_to_match_mL=re.findall('\d*\.?\d*\s?mL',temp_mat, re.DOTALL)
        if(len(dosage_match)!=0 and len(con_match)!=0):
            if(len(regex_to_match_mL)!=0):
                per_dosage=''
                if(temp_mat.startswith('Per '+regex_to_match_mL[0].strip()) or temp_mat.startswith('Each '+regex_to_match_mL[0].strip())):
                    per_dosage=dosage_match.pop(0)
                    dosage_match.append(per_dosage)
            result=''
            for m in dosage_match:
                if(m.find('/')==-1):
                    result+=m+"/"
                    result=result.replace(' ','')
                else:
                    result+=m
                    result+="/"
            result=result.replace("//","/")
            result=result.replace(' ','')
            result=result.strip('/')
            result=result.strip('.')
            d=result
            result=''
            for m in con_match:
                result+=m+"/"
                result=result.replace(' ','')
            con=result[:-1]
        elif(len(dosage_match)!=0):
            if(len(regex_to_match_mL)!=0):
                per_dosage=''
                if(temp_mat.startswith('Per '+regex_to_match_mL[0].strip())or temp_mat.startswith('Each '+regex_to_match_mL[0].strip())):
                    per_dosage=dosage_match.pop(0)
                    dosage_match.append(per_dosage)
            result=''
            for m in dosage_match:
                if(m.find('/')==-1):
                    result+=m+"/"
                    result=result.replace(' ','')
                else:
                    result+=m
                    result+="/"
            result=result.replace("//","/")
            result=result.replace(' ','')
            result=result.strip('/')
            result=result.strip('.')
            d=result
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
    format_match = re.findall('[^\w](mouth spray|cod liver oil|moisturising body wash|moisturising lotion|moisturising wash|moisturising bath & shampoo|soluble insulin|unit dose vial|Cream & Intensive Cream|suppositories|Enteric-Coated Microcapsules|Powdered Milk|powd for oral susp \(tutti-frutti flavour sachet\)|powd for inj \[vaccine \(inj\) \(pre-filled syringe\]|powd for soln for infusion \(single-use vial\)|soln for inj/infusion \(pre-filled syringe\)|vaccine \(inj\) \(vial & pre-filled syringe\)|vaccine susp for inj \(pre-filled syringe\)|vaccine \(oral\) \(pre-filled dosing tube\)|gastro-resistant \(enteric-coated\) tab|effervescent granules \(lemon flavour\)|DermaRel Lipid-Replenishing Cleanser|powd for conc for soln for infusion|vaccine \(inj\) \(pre-filled syringe\)|Moisturizing Facial Cleansing Foam|Total Care Less Intense mouthwash|susp for inj \(pre-filled syringe\)|soln for inj \(pre-filled syringe\)|oral susp \(tutti-frutti flavour\)|vaccine \(inj\) \(single-dose vial\)|inhalation soln \(unit-dose vial\)|powd for inj \(single-dose vial\)|DermaRel Ultra Hydrating Lotion|ultra hydrating lotion|granules for oral soln \(sachet\)|nebuliser soln \(unit-dose vial\)|concentrated soln for infusion|soln for inj \(pre-filled pen\)|powd for inj \(pre-filled pen\)|Childn granules for oral susp|Infant granules for oral susp|eye drops \(preservative-free\)|powd for inj \(Clickeasy vial\)|Hydrating cleansing bar soap|Intensive Moisturizing Cream|powd for inj/infusion \(vial\)|powd for oral soln \(sachet\)|soln for inj \(autoinjector\)|Restorative Hydration Cream|Moisturising Wash & Shampoo|Wash & Shampoo|Sugar-enteric-coated caplet|oral soln \(cherry flavour\)|powd for soln for infusion|conc for soln for infusion|Plus Cough Suppressant syr|Ped granules for oral soln|emulsion for inj/infusion|Intensive Hydrating Cream|pre-filled pen \(Solostar\)|oral soln \(grape flavour\)|serum topical application|powd for infusion \(vial\)|inj \(pre-filled syringe\)|FlexPen \(pre-filled pen\)|Light Moisturising Cream|soln for infusion \(vial\)|vaccine \(inj\) \(lyo vial\)|DermaRelief Rescue Cream|Single dose powd for inj|Moisturizing Body Lotion|soln for inj \(cartridge\)|Daily Facial Moisturizer|Moisturising Bath & Wash|susp for inj \(cartridge\)|Gentle Foaming Cleanser|Ultrafresh Stretch Mark|Hydrating liqd cleanser|bladder irrigation soln|powd for inj \(lyo vial\)|fast disintegrating tab|Adlt pre-filled syringe|Moisturising Day cream|Revitalising eye cream|Nourishing Conditioner|Intifresh Hygiene Mist|granules for oral soln|Sensitive Light lotion|granules for oral susp|powd for inj/infusion|soln for inj/infusion|powd for soln for inj|Nurturing Night cream|Moisturising Cleanser|Ultrafresh Shower Gel|effervescent granules|granule for oral soln|Intensive oint-cream|gastro-resistant tab|Total Care mouthwash|Oil Free Moisturiser|infusion conc \(vial\)|DermaRelief Cleanser|vaccine \(inj\) \(vial\)|minimicrospheres cap|gastro-resistant cap|modified-release tab|Plus Expectorant syr|Preparation Cleanser|micronized FC caplet|oral saline laxative|respiratory solution|Richenic urea cream|powd for inj \(vial\)|soln for inj \(vial\)|penfill \(cartridge\)|Cool Mint mouthwash|inhalation powd cap|Aqueous nasal spray|Hydrating Body Wash|DermaRel Spray & Go|topical application|susp for inj \(vial\)|orodispersible film|Forte topical spray|soln for inhalation|Active chewable tab|Chocolate oral liqd|inhalation liqd cap|liqd for inhalation|susp for inhalation|Sugar-coated caplet|Inhalation Solution|respirator solution|powd for oral susp|Polyamp Duofit inj|powd for oral soln|soln for inj \(amp\)|Protect Hand Cream|powd for oral liqd|Moisturising Cream|Nourishing Shampoo|powd for IM/IV inj|orodispersible tab|cleansing bar soap|DermaRelief Lotion|Intratracheal susp|Multivitamin gummy|Professional Serum|Multi-Action Cream|inj \(lyo\) for soln|IV/IM powd for inj|Childn nasal drops|Infant nasal drops|film-coated caplet|enteric-coated tab|pre-filled syringe|Prefilled syringe|soln for infusion|powd for infusion|transdermal spray|transdermal patch|granules for susp|effervescent powd|topical soln conc|oral lyophilisate|powd for oral use|Adult nasal drops|Kids chewable tab|Vanilla oral liqd|milk powd Vanilla|infant oral drops|Plus Chewable tab|Infusion solution|Intensive lotion|Foaming cleanser|oromucosal spray|sugar-coated tab|effervescent tab|Body Moisturiser|Hydrating lotion|Medicated Lotion|Daily Face cream|Daily Oral Rinse|lyo powd for inj|Derma Rash cream|vaccine susp inj|soft gelatin cap|viscous solution|ophthalmic drops|Intensive cream|Soothing lotion|dispersible tab|film-coated tab|inhalation powd|childn granules|Gentle Cleanser|Sting-Free Oint|inhalation soln|oromucosal liqd|respirator soln|liqd-filled cap|forte oral susp|inhalation liqd|intraocular inj|IV powd for inj|Transparent gel|transdermal gel|oromucosal soln|Chewable caplet|milk powd Honey|Expectorant syr|liqd inhalation|Saline Solution|oral Suspension|powder/solution|Soothing cream|pre-filled pen|oromucosal gel|adult granules|Gentle Shampoo|Relizema cream|vaccine \(oral\)|infusion \(amp\)|nebuliser soln|Daily Moisture|vaccine \(vial\)|ear drops soln|ophth emulsion|pre-filled inj|nebulizer soln|Forte dry susp|Aerofilm gauze|sublingual tab|Micellar Water|eye & ear drop|eye suspension|infusion conc|vaccine \(inj\)|topical spray|eye/ear drops|liqd cleanser|oral granules|cleansing gel|topical cream|inj iopamidol|infusion soln|forte dry syr|dry syr Forte|eye-ear drops|oral solution|soln for inj|chewable tab|Repair cream|powd for inj|infusion bag|topical soln|topical liqd|Forte FC tab|susp for inj|topical powd|rectal cream|Foaming Wash|Ultra lotion|Daily Lotion|Forte caplet|soluble film|dental paste|facial cream|eye ointment|nail lacquer|vaccine oral|nasal spray|topical gel|ophth drops|nasal drops|softgel cap|KwikPen inj|chewing gum|Nappy Cream|Skin Lotion|Gentle Wash|Polyamp inj|rectal oint|Body Lotion|expectorant|Creamy Wash|shower pack|intensive moisturizer|Moisturizer|transdermal|ophth strip|vaccine inj|IV infusion|Plus caplet|topical oil|Night Cream|Moisturiser|Conditioner|Thermometer|Liquid Soap|concentrate|intravenous|suppository|oral liquid|stain strip|oral drops|ophth soln|Childn syr|oral spray|inj \(vial\)|Skin cream|Start oint|coated tab|ophth susp|scalp soln|Hand Cream|Rescue Gel|ophth oint|Sugar-free|toothpaste|inhalation|spray powd|nasal wash|caring oil|combi pack|mouthspray|active tab|Forte drag|rectal gel|turbuhaler|Thermoscan|dental gel|irrigation|nasal drop|oral paste|suspension|wound wash|supplement|oral liqd|oral susp|oral soln|eye drops|actuation|Adult syr|inj \(amp\)|milk powder|milk powd|ear drops|Ear Drop|mouthwash|Adult cap|Regen pad|FC caplet|XR-FC tab|Mouth gel|forte syr|DHA gummy|accuhaler|oral powd|cough syr|sunscreen|body wash|Forte cap|depot inj|liqd soap|forte tab|paed susp|gauze-pad|vag ovule|flash tab|liqd wash|adult tab|rapihaler|Day Cream|Injection|Plus susp|Nebuliser|sanitiser|container|infusion|cleanser|Sunblock|vag wash|infusion|oral gel|granules|liniment|Bath Oil|inj conc|evohaler|Kids syr|Gold cap|eye susp|eye oint|pastille|respules|Disp tab|hard cap|mite tab|GITS tab|band-aid|soft cap|Plus tab|dressing|solostar|orapaste|filcotab|Lip Balm|Emulsion|Eyedrops|Eyedrop|Eye Drop|solution|catridge|ointment|tincture|spansule|Shampoo|vag gel|vegecap|softcap|linctus|vag tab|vaccine|pessary|vegicap|topical|gummies|nebules|Softgels|softgel|plaster|filmtab|implant|dry syr|minitab|eye gel|chewtab|inhaler|dry inj|emulgel|Essence|Capsules|capsule|handrub|Lozenges|lozenge|mixture|Bandage|aerosol|pellets|FC tab|lotion|elixir|sachet|\(vial\)|ER tab|gargle|SolTab|caplet|troche|XR tab|teabag|CR tab|IV inj|EC tab|FC cap|MR tab|OD tab|bottles||bottle|DR cap|FX tab|captab|diskus|IR tab|douche|Balsam|liquid|powder|system|Tablets|tablet|wafers|durule|cream|Spray|gummy|drops|Drop|enema|ovule|sheet|jelly|licap|Patch|paste|Creme|Serum|beads|paint|scrub|strip|syrup|tears|gauze|stick|powd|drag|Wash|susp|liqd|oint|supp|soap|vial|soln|oral|foam|balm|salt|swab|film|melt|pill|wipe|cap|inj|dispertab|tab|gel|syr|loz|MDI|DPI|pen|oil|Kit|Jel|gum|udv|IV|insulin|mdv|syringe|bag)[^\w]'," "+material_to_map+" ",re.IGNORECASE)
    if(len(format_match)!=0 and len(format_org)==0):
        format_org=format_match[0].strip()
        std_format=search(format_org)
    if(len(material_to_map)!=0): # Remove raw string from material
#         material_to_map = re.escape(material_to_map_form)#This ensures that any special characters are treated as literal characters in the regular expression pattern.
#         std_mat = re.sub(material_to_map,'',std_mat ,flags = re.IGNORECASE) #Ignore case while removing raw_string in material
        std_mat = std_mat.replace(material_to_map,'')
        std_mat = std_mat.strip()
        std_mat = std_mat.strip(":")
        std_mat = std_mat.strip()
        print("Removed raw string from material :",std_mat,"raw material:",material_to_map)
    dosage_match_in_mat = re.findall('[^\w](\d+\.?\d*\s?mg\/?\d*\.?\d*\s?IU|\d+\.?\d*\s?units\s?\/?\s?\d*\.?\d*\s?mL|\d+\.?\d*\s?mL\s?\/?\s?\d*\.?\d*\s?dose|\d+\.?\d*\s?IU\s?\/?\s?\d*\.?\d*\s?tube|\d+\.?\d*\s?mg\s?\/?\s?\d*\.?\d*\s?dose|\d+\.?\d*\s?IU\s?\/?\s?\d*\.?\d*\s?g|\d+\.?\d*\s?MIU\s?\/?\s?\d*\.?\d*\s?MIU|\d+\.?\d*\s?IU\s?\/?\d*\.?\d*\s?mg|\d+\.?\d*\s?mmol\s?\/?\d*\.?\d*\s?L|\d+\.?\d*\s?mOsm\/?\d*\.?\d*\s?kg|\d+\.?\d*\s?mg\s?\/?\d*\.?\d*\s?g|\d+\.?\d*\s?g\/?\d*\.?\d*\s?L|\d*\.?\d*\s?g\/?\d*\.?\d*\s?mL|\d+\.?\d*\s?mosm\/?\d*\.?\d*\s?L|\d+\.?\d*\/?\-?\d*\.?\d*\s?mOsm\/?\d*\.?\d*\s?L|\d+\.?\d*\s?mOsmol\/?\d*\s?L|\d+\.?\d*\s?mOsmol\/?\d*\s?kg|\d+\.?\d*\s?billion cells\/?\d+\s?mL|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg\/?dose|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg\/?actuation|\d+\.?\d*\/?\d*\.?\d*\s?u\/?mL\s?\+?\s?\d*\.?\d*\s?mcg\/?mL|\d+\.?\d*\/?\d*\.?\d*\s?mg\/?mL|\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg(?:\/\d+\.?\d*\s?mg)*|\d+\.?\d*\/?\-?\d*\.?\d*/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?mmol|\d+\.?\d*\/?\-?\d*\.?\d*\s?million cells|\d+\.?\d*\/?\-?\d*\.?\d*\s?billion cells|\d+\.?\d*\/?\-?\d*\.?\d*\s?CFU|\d+\.?\d*\/?\-?\d*\.?\d*\s?mOsm|\d+\.?\d*\/?\-?\d*\.?\d*\s?MIU)[^\w]'," "+std_mat+" ", re.DOTALL)
    con_match_in_mat = re.findall('\d+\.?\d*\s?%',std_mat, re.DOTALL)
    std_mat = std_mat.replace(',','')
    mat = mat.replace(',','')
    if(len(dosage_match_in_mat)==0 and len(con_match_in_mat)==0):
        current_mat=mat
        std_mat=re.sub(r'\s+', ' ', std_mat)
        current_std_mat=std_mat
    elif(len(dosage_match_in_mat)!=0 and len(con_match_in_mat)!=0):
        current_mat=mat
        for dm in dosage_match_in_mat:
            dm=dm.strip()
            std_mat=std_mat.replace(dm,'',1)
        for cm in con_match_in_mat:
            std_mat=std_mat.replace(cm,'',1)
        std_mat=std_mat.strip()
        std_mat=std_mat.replace('w/w','')
        std_mat=std_mat.replace('w/v','')
        std_mat=std_mat.strip('/')
        std_mat=std_mat.strip('&')
        std_mat=std_mat.replace(' / ',' ')
        std_mat=std_mat.replace('()',' ')
        std_mat=std_mat.replace('( )',' ')
        std_mat=std_mat.replace('(/ )',' ')
        std_mat=std_mat.replace('(/  )',' ')
        std_mat=std_mat.replace(' . ',' ')
        std_mat=std_mat.strip('or')
        std_mat=re.sub(r'\s+', ' ', std_mat)
        std_mat=std_mat.strip() 
        current_std_mat=std_mat
    elif(len(dosage_match_in_mat)!=0):
        current_mat=mat
        for dm in dosage_match_in_mat:
            dm=dm.strip()
            std_mat=std_mat.replace(dm,'',1)
        std_mat=std_mat.strip()
        std_mat=std_mat.strip('/')
        std_mat=std_mat.strip('&')
        std_mat=std_mat.replace(' / ',' ')
        std_mat=std_mat.replace('()',' ')
        std_mat=std_mat.replace('( )',' ')
        std_mat=std_mat.replace('(/ )',' ')
        std_mat=std_mat.replace('(/  )',' ')
        std_mat=std_mat.replace(' . ',' ')
        std_mat=std_mat.strip('or')
        std_mat=re.sub(r'\s+', ' ', std_mat)
        std_mat=std_mat.strip()
        current_std_mat=std_mat
    elif(len(con_match_in_mat)!=0):
        current_mat=mat
        for cm in con_match_in_mat:
            std_mat=std_mat.replace(cm,'',1)
        std_mat=std_mat.strip()
        std_mat=std_mat.replace('w/w','')
        std_mat=std_mat.replace('w/v','')
        std_mat=std_mat.strip('/')
        std_mat=std_mat.strip('&')
        std_mat=std_mat.replace(' / ',' ')
        std_mat=std_mat.replace('()',' ')
        std_mat=std_mat.replace('( )',' ')
        std_mat=std_mat.replace('(/ )',' ')
        std_mat=std_mat.replace('(/  )',' ')
        std_mat=std_mat.replace(' . ',' ')
        std_mat=std_mat.strip('or')
        std_mat=re.sub(r'\s+', ' ', std_mat)
        std_mat=std_mat.strip()
        current_std_mat=std_mat
    if(len(format_match)!=0):
        pattern = re.compile(re.escape(format_match[0].rstrip()), re.IGNORECASE)
        std_mat = pattern.sub('', std_mat)
        current_std_mat=std_mat
    return d,con,current_mat,current_std_mat,format_org,std_format
def add_manual(csv_headers,drug,manf,cims_class,mims_class,atc_code_list,atc_list,std_uom,std_amount,d,con,format_org,std_format,material_list,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,mat_to_map_list,format_match,uom_dosage,quantity,unit_price):
    for e,entry in enumerate(material_list):
        csv_headers.brand.append(drug)        
        csv_headers.manufacturer.append(manf)
        csv_headers.cimsClass.append(cims_class)
        csv_headers.mimsClass.append(mims_class)
        if(len(atc_code_list)!=0):
            atc_code = atc_code_list[0]
            csv_headers.atcCode.append(atc_code)
        elif(len(atc_code_list)==0):
            csv_headers.atcCode.append('')
        if(len(atc_list)!=0):
            atc=atc_list[0]
            atc=atc.replace('\u200b','')
            atc=atc.replace(';','')
            atc=atc.replace(',','')
            atc=atc.replace('  ',' ')
            atc=atc.strip('.')
            csv_headers.atcDetail.append(atc)
        elif(len(atc_list)==0):
            csv_headers.atcDetail.append('')
        std_uom = std_uom.strip()
        csv_headers.uom.append(std_uom)
        csv_headers.uom_dosage_list.append(uom_dosage)
        csv_headers.uom_quantity_list.append(quantity)
        csv_headers.unit_price_list.append(unit_price)
        csv_headers.amount.append('')
        std_mat = entry
        mat = entry
        dos = ""
        c = ""
        current_format = ""
        dos,c,current_mat,current_std_mat,current_format,std_format = extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,mat_to_map_list[e],format_org,std_format,format_match)
        dos = dos.replace(' ','')
        dos = dos.replace(',','')
        c = c.replace(' ','')
        c = c.replace(',','')
        csv_headers.dosage.append(dos)
        csv_headers.concentration.append(c)
        csv_headers.format_original.append(current_format)
        csv_headers.formater.append(std_format)
        csv_headers.material.append(current_mat)
        csv_headers.std_material.append(current_std_mat)
def process_drug_name(drugName):
    parts = drugName.split('/')
    first_word = parts[0].split()[0]
    drug_name = []
    if all(first_word in part for part in parts):
        for part in parts:
            drug_name.append(part)
    return drug_name
def split_drug_name(drugName,products):
    drug_name = []
    parts = drugName.split('/')
    first_word = parts[0].split()[0]
    count_drug_name = drugName.count(first_word)
    if(len(products)!=0):
        forms_list = get_forms(products)
        if (count_drug_name==1 and all(word in forms_list for word in parts)):
            for part in parts:
                res = ''
                if(first_word not in part):
                    res = ' '.join(parts[0].split()[:-1]) +" "+ part
                else:
                    res = part
                drug_name.append(res)
    else:
        if (count_drug_name==1):
                for part in parts:
                    res = ''
                    if(first_word not in part):
                        res = ' '.join(parts[0].split()[:-1]) +" "+ part
                    else:
                        res = part
                    drug_name.append(res)
    return drug_name
def get_uom_details(std_amount,std_uom):
    unit_price = ''   
    quantity = 1
    uom_dosage = ''
    sub_split = []
    if 'x' in std_uom : 
        split =  std_uom.split('x');        
        if len(split) == 1 : 
            if "one" in map1.keys():
                map1["one"] = map1["one"] + 1
            else :
                map1["one"] = 1
        elif len(split) == 2 :
            if "two" in map1.keys():
                map1["two"] = map1["two"] + 1
            else :
                 map1["two"] = 1
        elif len(split) == 3:
            if "three" in map1.keys():
                map1["three"] = map1["three"] + 1
            else :
                map1["three"] = 1
        elif len(split) == 4:
            if "four" in map1.keys():
                map1["four"] = map1["four"] + 1
            else :
                map1["four"] = 1
        else:
            if "new_combination" in map1.keys():
                map1["new_combination"] += 1
            else :
                map1["new_combination"] = 1


        first_element = split[0]
        is_only_digits = 1;
        for elem in split:
            if re.search( r'^\d+(\.\d+)?$', elem): 
                elem = int(elem)
                if elem and elem > 0 :
                    quantity *= elem
            else:
                is_only_digits = 0;
                if uom_dosage == "":
                    uom_dosage += elem
                else: 
                    uom_dosage += 'x' + elem
        
        if is_only_digits:
            uom_dosage = first_element
        if std_amount and std_amount > 0 :
            unit_price = round(std_amount / quantity,2)
    else:
        if std_uom == "":
            if "empty" in map1.keys():
                map1["empty"] += 1
            else :
                map1["empty"] = 1
        elif re.search( r'^\d+$',std_uom) :
            if "one" in map1.keys():
                map1["one"] += 1
            else :
                map1["one"] = 1
        else: 
            sub_split = re.findall(r'(\d+)([a-z]+)', std_uom)
            if len(sub_split) > 0 :
                unit = sub_split[0][1]
                if "unit" in map1.keys():
                    if unit in map1["unit"].keys():                    
                        map1["unit"][unit] += 1
                    else:
                        map1["unit"][unit] = 1
                else :
                    map1["unit"] = {}
                    map1["unit"][unit] = 1

            else:
                # print (f"unknown format of UOM found ignoring now:{index} {uom}");
                if "unknown" in map1.keys():
                    map1["unknown"] += 1
                else :
                    map1["unknown"] = 1
                std_uom = "";
         
        uom_dosage = std_uom
        if re.search( r'^\d+(\.\d+)?$', std_uom): 
            quantity = float(std_uom)
            if std_amount and std_amount > 0 :
                unit_price = round(std_amount / quantity,2)
        else:
            quantity = 1
            unit_price = std_amount
    return uom_dosage,quantity,unit_price,std_uom
with open('MIMS Vietnam.csv','w') as file:
    writer = csv.writer(file)
    writer.writerow(["brand","manufacturer","cims_class","material","standard_material","format_original","standard_format","concentration","dosage","uom","uom_dosage","uom_quantity","unit_price","total_amount","atc_code","atc_detail","mdc_code","sub_format","locale","mims_class"])
with open('Vietnam.csv','w') as f:
    writer = csv.writer(f)
    writer.writerow(["brand","manufacturer","cims_class","material","standard_material","format_original","standard_format","concentration","dosage","uom","uom_dosage","uom_quantity","unit_price","total_amount","atc_code","atc_detail","mdc_code","sub_format","locale","mims_class"])
class CsvHeaders:
    def reset_to_initial_values(self):
        self.brand=[]    
        self.manufacturer=[]
        self.cimsClass=[]
        self.atcCode=[]
        self.atcDetail=[]
        self.material=[]
        self.dosage=[]
        self.uom=[]
        self.form=[]
        self.products=[]
        self.formater=[]
        self.concentration=[]
        self.format_original=[]
        self.l=[]
        self.std_material=[]
        self.mimsClass=[]
        self.amount=[]
        self.uom_dosage_list=[]
        self.uom_quantity_list=[]
        self.unit_price_list=[]
def read_text_file(file):  
    with open(file) as f:
        csv_headers = CsvHeaders()
        csv_headers.reset_to_initial_values()
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
        std_material=[]
        mimsClass=[]
        amount=[]
        uom_dosage_list=[]
        uom_quantity_list=[]
        unit_price_list=[]
        for item in data:
            d=''
            con=''
            dosage_match=''
            con_match=''
            dosage_match_in_mat=''
            con_match_in_mat=''
            dos_match_from_form=''
            con_match_from_form=''
            dos_match_from_drug = ''
            con_match_from_drug = ''
            format_match=''
            format_org=''
            std_format=''
            current_mat=''
            current_std_mat=''
            drug=''
            org_form=''
            std_uom=''
            format_match_from_form=[]
            drug_name=[]
            std_amount=''
            is_length_to_map_equal = True
            print("--------------------------------------------------------------------------------",item['drugName'])
            products = item['details']['products']
            activeIngredients = item['details']['activeIngredients']
            drugName = item['drugName']
            drugName = drugName.replace(',','')
            drugName = drugName.replace('&amp;','&')
            drugName = drugName.replace('<sub>','')
            drugName = drugName.replace('</sub>','')
            drugName = drugName.replace('<em>','')
            drugName = drugName.replace('</em>','')
            drugName = drugName.replace('&quot;','"')
            drugName = drugName.replace('\u200b','')
            atc_code_list = item['details']['atcCode']
            atc_list = item['details']['atc']
            manf = item['details']['manufacturer']
            cims_class = item['details']['cimsClass']
            mims_class = item['details']['mimsClass']
            drugClassification = item['drugClassification']
            if(drugName.find('/')!=-1):
                drug_name = process_drug_name(drugName)
            if(len(drug_name)<=1):
                regex_for_split = re.findall(r'\d+\.?\d*/\d+\.?\d*$',drugName,re.DOTALL)
                if(regex_for_split):
                    drug_name = split_drug_name(drugName,products)
            if(len(drug_name)<=1):
                drug_name.append(drugName)
            if(len(activeIngredients)!=0):
                active_ingredients_list = split_material(activeIngredients,drug_name)
                mat_to_map_list,material_list = get_material(active_ingredients_list,drug_name[0])
            else:
                material_list = ''
            if(len(products)==0):
                for drug in drug_name:
                    format_match_from_form = re.findall('[^\w](mouth spray|cod liver oil|moisturising body wash|moisturising lotion|moisturising wash|moisturising bath & shampoo|soluble insulin|unit dose vial|Cream & Intensive Cream|suppositories|Enteric-Coated Microcapsules|Powdered Milk|powd for oral susp \(tutti-frutti flavour sachet\)|powd for inj \[vaccine \(inj\) \(pre-filled syringe\]|powd for soln for infusion \(single-use vial\)|soln for inj/infusion \(pre-filled syringe\)|vaccine \(inj\) \(vial & pre-filled syringe\)|vaccine susp for inj \(pre-filled syringe\)|vaccine \(oral\) \(pre-filled dosing tube\)|gastro-resistant \(enteric-coated\) tab|effervescent granules \(lemon flavour\)|DermaRel Lipid-Replenishing Cleanser|powd for conc for soln for infusion|vaccine \(inj\) \(pre-filled syringe\)|Moisturizing Facial Cleansing Foam|Total Care Less Intense mouthwash|susp for inj \(pre-filled syringe\)|soln for inj \(pre-filled syringe\)|oral susp \(tutti-frutti flavour\)|vaccine \(inj\) \(single-dose vial\)|inhalation soln \(unit-dose vial\)|powd for inj \(single-dose vial\)|DermaRel Ultra Hydrating Lotion|ultra hydrating lotion|granules for oral soln \(sachet\)|nebuliser soln \(unit-dose vial\)|concentrated soln for infusion|soln for inj \(pre-filled pen\)|powd for inj \(pre-filled pen\)|Childn granules for oral susp|Infant granules for oral susp|eye drops \(preservative-free\)|powd for inj \(Clickeasy vial\)|Hydrating cleansing bar soap|Intensive Moisturizing Cream|powd for inj/infusion \(vial\)|powd for oral soln \(sachet\)|soln for inj \(autoinjector\)|Restorative Hydration Cream|Moisturising Wash & Shampoo|Wash & Shampoo|Sugar-enteric-coated caplet|oral soln \(cherry flavour\)|powd for soln for infusion|conc for soln for infusion|Plus Cough Suppressant syr|Ped granules for oral soln|emulsion for inj/infusion|Intensive Hydrating Cream|pre-filled pen \(Solostar\)|oral soln \(grape flavour\)|serum topical application|powd for infusion \(vial\)|inj \(pre-filled syringe\)|FlexPen \(pre-filled pen\)|Light Moisturising Cream|soln for infusion \(vial\)|vaccine \(inj\) \(lyo vial\)|DermaRelief Rescue Cream|Single dose powd for inj|Moisturizing Body Lotion|soln for inj \(cartridge\)|Daily Facial Moisturizer|Moisturising Bath & Wash|susp for inj \(cartridge\)|Gentle Foaming Cleanser|Ultrafresh Stretch Mark|Hydrating liqd cleanser|bladder irrigation soln|powd for inj \(lyo vial\)|fast disintegrating tab|Adlt pre-filled syringe|Moisturising Day cream|Revitalising eye cream|Nourishing Conditioner|Intifresh Hygiene Mist|granules for oral soln|Sensitive Light lotion|granules for oral susp|powd for inj/infusion|soln for inj/infusion|powd for soln for inj|Nurturing Night cream|Moisturising Cleanser|Ultrafresh Shower Gel|effervescent granules|granule for oral soln|Intensive oint-cream|gastro-resistant tab|Total Care mouthwash|Oil Free Moisturiser|infusion conc \(vial\)|DermaRelief Cleanser|vaccine \(inj\) \(vial\)|minimicrospheres cap|gastro-resistant cap|modified-release tab|Plus Expectorant syr|Preparation Cleanser|micronized FC caplet|oral saline laxative|respiratory solution|Richenic urea cream|powd for inj \(vial\)|soln for inj \(vial\)|penfill \(cartridge\)|Cool Mint mouthwash|inhalation powd cap|Aqueous nasal spray|Hydrating Body Wash|DermaRel Spray & Go|topical application|susp for inj \(vial\)|orodispersible film|Forte topical spray|soln for inhalation|Active chewable tab|Chocolate oral liqd|inhalation liqd cap|liqd for inhalation|susp for inhalation|Sugar-coated caplet|Inhalation Solution|respirator solution|powd for oral susp|Polyamp Duofit inj|powd for oral soln|soln for inj \(amp\)|Protect Hand Cream|powd for oral liqd|Moisturising Cream|Nourishing Shampoo|powd for IM/IV inj|orodispersible tab|cleansing bar soap|DermaRelief Lotion|Intratracheal susp|Multivitamin gummy|Professional Serum|Multi-Action Cream|inj \(lyo\) for soln|IV/IM powd for inj|Childn nasal drops|Infant nasal drops|film-coated caplet|enteric-coated tab|pre-filled syringe|Prefilled syringe|soln for infusion|powd for infusion|transdermal spray|transdermal patch|granules for susp|effervescent powd|topical soln conc|oral lyophilisate|powd for oral use|Adult nasal drops|Kids chewable tab|Vanilla oral liqd|milk powd Vanilla|infant oral drops|Plus Chewable tab|Infusion solution|Intensive lotion|Foaming cleanser|oromucosal spray|sugar-coated tab|effervescent tab|Body Moisturiser|Hydrating lotion|Medicated Lotion|Daily Face cream|Daily Oral Rinse|lyo powd for inj|Derma Rash cream|vaccine susp inj|soft gelatin cap|viscous solution|ophthalmic drops|Intensive cream|Soothing lotion|dispersible tab|film-coated tab|inhalation powd|childn granules|Gentle Cleanser|Sting-Free Oint|inhalation soln|oromucosal liqd|respirator soln|liqd-filled cap|forte oral susp|inhalation liqd|intraocular inj|IV powd for inj|Transparent gel|transdermal gel|oromucosal soln|Chewable caplet|milk powd Honey|Expectorant syr|liqd inhalation|Saline Solution|oral Suspension|powder/solution|Soothing cream|pre-filled pen|oromucosal gel|adult granules|Gentle Shampoo|Relizema cream|vaccine \(oral\)|infusion \(amp\)|nebuliser soln|Daily Moisture|vaccine \(vial\)|ear drops soln|ophth emulsion|pre-filled inj|nebulizer soln|Forte dry susp|Aerofilm gauze|sublingual tab|Micellar Water|eye & ear drop|eye suspension|infusion conc|vaccine \(inj\)|topical spray|eye/ear drops|liqd cleanser|oral granules|cleansing gel|topical cream|inj iopamidol|infusion soln|forte dry syr|dry syr Forte|eye-ear drops|oral solution|soln for inj|chewable tab|Repair cream|powd for inj|infusion bag|topical soln|topical liqd|Forte FC tab|susp for inj|topical powd|rectal cream|Foaming Wash|Ultra lotion|Daily Lotion|Forte caplet|soluble film|dental paste|facial cream|eye ointment|nail lacquer|vaccine oral|nasal spray|topical gel|ophth drops|nasal drops|softgel cap|KwikPen inj|chewing gum|Nappy Cream|Skin Lotion|Gentle Wash|Polyamp inj|rectal oint|Body Lotion|expectorant|Creamy Wash|shower pack|intensive moisturizer|Moisturizer|transdermal|ophth strip|vaccine inj|IV infusion|Plus caplet|topical oil|Night Cream|Moisturiser|Conditioner|Thermometer|Liquid Soap|concentrate|intravenous|suppository|oral liquid|stain strip|oral drops|ophth soln|Childn syr|oral spray|inj \(vial\)|Skin cream|Start oint|coated tab|ophth susp|scalp soln|Hand Cream|Rescue Gel|ophth oint|Sugar-free|toothpaste|inhalation|spray powd|nasal wash|caring oil|combi pack|mouthspray|active tab|Forte drag|rectal gel|turbuhaler|Thermoscan|dental gel|irrigation|nasal drop|oral paste|suspension|wound wash|supplement|oral liqd|oral susp|oral soln|eye drops|actuation|Adult syr|inj \(amp\)|milk powder|milk powd|ear drops|Ear Drop|mouthwash|Adult cap|Regen pad|FC caplet|XR-FC tab|Mouth gel|forte syr|DHA gummy|accuhaler|oral powd|cough syr|sunscreen|body wash|Forte cap|depot inj|liqd soap|forte tab|paed susp|gauze-pad|vag ovule|flash tab|liqd wash|adult tab|rapihaler|Day Cream|Injection|Plus susp|Nebuliser|sanitiser|container|infusion|cleanser|Sunblock|vag wash|infusion|oral gel|granules|liniment|Bath Oil|inj conc|evohaler|Kids syr|Gold cap|eye susp|eye oint|pastille|respules|Disp tab|hard cap|mite tab|GITS tab|band-aid|soft cap|Plus tab|dressing|solostar|orapaste|filcotab|Lip Balm|Emulsion|Eyedrops|Eyedrop|Eye Drop|solution|catridge|ointment|tincture|spansule|Shampoo|vag gel|vegecap|softcap|linctus|vag tab|vaccine|pessary|vegicap|topical|gummies|nebules|Softgels|softgel|plaster|filmtab|implant|dry syr|minitab|eye gel|chewtab|inhaler|dry inj|emulgel|Essence|Capsules|capsule|handrub|Lozenges|lozenge|mixture|Bandage|aerosol|pellets|FC tab|lotion|elixir|sachet|\(vial\)|ER tab|gargle|SolTab|caplet|troche|XR tab|teabag|CR tab|IV inj|EC tab|FC cap|MR tab|OD tab|bottles|bottle|DR cap|FX tab|captab|diskus|IR tab|douche|Balsam|liquid|powder|system|Tablets|tablet|wafers|durule|cream|Spray|gummy|drops|Drop|enema|ovule|sheet|jelly|licap|Patch|paste|Creme|Serum|beads|paint|scrub|strip|syrup|tears|gauze|stick|powd|drag|Wash|susp|liqd|oint|supp|soap|vial|soln|oral|foam|balm|salt|swab|film|melt|pill|wipe|cap|inj|dispertab|tab|gel|syr|loz|MDI|DPI|pen|oil|Kit|Jel|gum|udv|IV|insulin|mdv|syringe|bag)[^\w]'," "+drug+" ",re.IGNORECASE)
                    if(len(format_match_from_form)!=0):
                        format_org = format_match_from_form[0]
                    else:
                        format_org = ''
                    std_format=search(format_org)
                    if(std_format==None):
                        std_format=''
                    if(len(material_list)!=0):
                        local_keywords_list = append_keywords_from_form_to_keywords_list([],drug_name)
                        if(len(material_list) > 1 and len(drug_name) > 1):#map drugName to material
                            if(len(material_list) != len(drug_name)):
                                matched_material = ""
                                is_length_to_map_equal = False
                            else:
                                list_of_dicts = map_drug_name_to_mat(drug_name,mat_to_map_list,material_list)
                                # for i,entry in enumerate(activeIngredientsList):
                                matched_material,material_to_map = get_matching_material('',drug,list_of_dicts)
                            if(matched_material and is_length_to_map_equal == True):
                                brand.append(drug)        
                                manufacturer.append(manf)
                                cimsClass.append(cims_class)
                                mimsClass.append(mims_class)
                                if(len(atc_code_list)!=0):
                                    atc_code = atc_code_list[0]
                                    atcCode.append(atc_code)
                                elif(len(atc_code_list)==0):
                                    atcCode.append('')
                                if(len(atc_list)!=0):
                                    atc=atc_list[0]
                                    atc=atc.replace('\u200b','')
                                    atc=atc.replace(';','')
                                    atc=atc.replace(',','')
                                    atc=atc.replace('  ',' ')
                                    atc=atc.strip('.')
                                    atcDetail.append(atc)
                                elif(len(atc_list)==0):
                                    atcDetail.append('')
                                uom.append('')
                                uom_dosage_list.append('')
                                uom_quantity_list.append(1)
                                unit_price_list.append('')
                                amount.append('')
                                d = ''
                                con = ''
                                std_mat = matched_material
                                mat = matched_material
                                dos = ""
                                c = ""
                                dos,c,current_mat,current_std_mat,format_org,std_format = extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,material_to_map,format_org,std_format,format_match)
                                if(len(dos)==0 and len(c)==0):
                                    dos,c = extract_dos_con_from_drug(dos_match_from_drug,con_match_from_drug,dos,c,drug)
                                dos = dos.replace(' ','')
                                dos = dos.replace(',','')
                                c = c.replace(' ','')
                                c = c.replace(',','')
                                dosage.append(dos)
                                concentration.append(c)
                                format_original.append(format_org)
                                formater.append(std_format)
                                material.append(current_mat)
                                std_material.append(current_std_mat)
                            elif(is_length_to_map_equal == False):
                                add_manual(csv_headers,drug,manf,cims_class,mims_class,atc_code_list,atc_list,std_uom,std_amount,d,con,format_org,std_format,material_list,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,mat_to_map_list,format_match,'',1,'')
                            else:
                                pass
                        else:
                                    for e,entry in enumerate(material_list):
                                        brand.append(drug)        
                                        manufacturer.append(manf)
                                        cimsClass.append(cims_class)
                                        mimsClass.append(mims_class)
                                        if(len(atc_code_list)!=0):
                                            atc_code = atc_code_list[0]
                                            atcCode.append(atc_code)
                                        elif(len(atc_code_list)==0):
                                            atcCode.append('')
                                        if(len(atc_list)!=0):
                                            atc=atc_list[0]
                                            atc=atc.replace('\u200b','')
                                            atc=atc.replace(';','')
                                            atc=atc.replace(',','')
                                            atc=atc.replace('  ',' ')
                                            atc=atc.strip('.')
                                            atcDetail.append(atc)
                                        elif(len(atc_list)==0):
                                            atcDetail.append('')
                                        uom.append('')
                                        uom_dosage_list.append('')
                                        uom_quantity_list.append(1)
                                        unit_price_list.append('')
                                        amount.append('')
                                        d = ''
                                        con = ''
                                        std_mat = entry
                                        mat = entry
                                        dos = ""
                                        c = ""
                                        org_format = ""
                                        format_std = ""
                                        dos,c,current_mat,current_std_mat,org_format,format_std = extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,mat_to_map_list[e],format_org,std_format,format_match)
                                        if(len(dos)==0 and len(c)==0):
                                            dos,c = extract_dos_con_from_drug(dos_match_from_drug,con_match_from_drug,dos,c,drug)
                                        dos = dos.replace(' ','')
                                        dos = dos.replace(',','')
                                        c = c.replace(' ','')
                                        c = c.replace(',','')
                                        dosage.append(dos)
                                        concentration.append(c)
                                        format_original.append(org_format)
                                        formater.append(format_std)
                                        material.append(current_mat)
                                        std_material.append(current_std_mat)
                    elif(len(material_list)==0):
                            dos = ''
                            c = ''
                            if(len(dos)==0 and len(c)==0):
                                dos,c = extract_dos_con_from_drug(dos_match_from_drug,con_match_from_drug,dos,c,drug)
                            concentration.append(c)
                            dosage.append(dos)
                            if(drugClassification=='Generic'):
                                    #If drugClassification is generic and material_list is empty then drugName becomes activeIngredient for that drug
                                    current_mat = drug
                                    current_std_mat = drug
                                    drug = ''
                            material.append(current_mat)
                            std_material.append(current_std_mat)
                            brand.append(drug)        
                            manufacturer.append(manf)
                            cimsClass.append(cims_class)
                            mimsClass.append(mims_class)
                            if(len(atc_code_list)!=0):
                                atc_code = atc_code_list[0]
                                atcCode.append(atc_code)
                            elif(len(atc_code_list)==0):
                                atcCode.append('')
                            if(len(atc_list)!=0):
                                atc=atc_list[0]
                                atc=atc.replace('\u200b','')
                                atc=atc.replace(';','')
                                atc=atc.replace(',','')
                                atc=atc.replace('  ',' ')
                                atc=atc.strip('.')
                                atcDetail.append(atc)
                            elif(len(atc_list)==0):
                                atcDetail.append('')
                            uom.append('')
                            uom_dosage_list.append('')
                            uom_quantity_list.append(1)
                            unit_price_list.append('')
                            amount.append('')
                            d=''
                            con=''
                            format_original.append(format_org)
                            formater.append(std_format)
            elif(len(products)!=0):
                forms_list = get_forms(products)
                local_keywords_list = append_keywords_from_form_to_keywords_list(forms_list,drug_name)
                if(len(material_list)!=0):
                    if((len(material_list) != len(forms_list) and len(material_list)>1) or ((len(drug_name) != len(forms_list) and len(drug_name)>1)) or ((len(drug_name) != len(material_list) and len(drug_name)>1) and len(material_list)>1)):
                            is_length_to_map_equal = False
                    else:
                        if(len(material_list)>1):#map form to material in case of single or multiple drugNames
                            list_of_dicts = map_form_to_mat(forms_list,mat_to_map_list,material_list,drug_name)
                        if(len(drug_name)>1 and len(material_list)<=1):#map drugName to form in case of single material
                            list_of_dicts = map_drug_name_to_form(drug_name,forms_list,mat_to_map_list,material_list)
                for drug in drug_name:
                    for product in products:
                        packaging = product['packaging']
                        std_packaging = remove_substring_in_brackets(packaging)
                        org_form = product['form']
                        org_form = org_form.replace('\u200b','')
                        org_form = org_form.replace(',','')
                        # form = org_form
                        # form_without_drug_name = org_form
                        replaced=std_packaging.replace('&#39;s','')
                        decode_x=replaced.replace('&#215;','x')
                        l=decode_x.split(';')
                        for i in l:
                            i=i.replace(',','')
                            i=i.replace(';','')
                            std_uom=remove_substring_in_brackets(i)
                            std_uom=std_uom.replace("'s","")
                            std_uom=std_uom.strip()
                            if(std_amount):
                                std_amount = float(std_amount)
                            std_uom = std_uom.replace(' ','')
                            uom_dosage,quantity,unit_price,std_uom = get_uom_details(std_amount,std_uom)
                            format_match_from_form = re.findall('[^\w](mouth spray|cod liver oil|moisturising body wash|moisturising lotion|moisturising wash|moisturising bath & shampoo|soluble insulin|unit dose vial|Cream & Intensive Cream|suppositories|Enteric-Coated Microcapsules|Powdered Milk|powd for oral susp \(tutti-frutti flavour sachet\)|powd for inj \[vaccine \(inj\) \(pre-filled syringe\]|powd for soln for infusion \(single-use vial\)|soln for inj/infusion \(pre-filled syringe\)|vaccine \(inj\) \(vial & pre-filled syringe\)|vaccine susp for inj \(pre-filled syringe\)|vaccine \(oral\) \(pre-filled dosing tube\)|gastro-resistant \(enteric-coated\) tab|effervescent granules \(lemon flavour\)|DermaRel Lipid-Replenishing Cleanser|powd for conc for soln for infusion|vaccine \(inj\) \(pre-filled syringe\)|Moisturizing Facial Cleansing Foam|Total Care Less Intense mouthwash|susp for inj \(pre-filled syringe\)|soln for inj \(pre-filled syringe\)|oral susp \(tutti-frutti flavour\)|vaccine \(inj\) \(single-dose vial\)|inhalation soln \(unit-dose vial\)|powd for inj \(single-dose vial\)|DermaRel Ultra Hydrating Lotion|ultra hydrating lotion|granules for oral soln \(sachet\)|nebuliser soln \(unit-dose vial\)|concentrated soln for infusion|soln for inj \(pre-filled pen\)|powd for inj \(pre-filled pen\)|Childn granules for oral susp|Infant granules for oral susp|eye drops \(preservative-free\)|powd for inj \(Clickeasy vial\)|Hydrating cleansing bar soap|Intensive Moisturizing Cream|powd for inj/infusion \(vial\)|powd for oral soln \(sachet\)|soln for inj \(autoinjector\)|Restorative Hydration Cream|Moisturising Wash & Shampoo|Wash & Shampoo|Sugar-enteric-coated caplet|oral soln \(cherry flavour\)|powd for soln for infusion|conc for soln for infusion|Plus Cough Suppressant syr|Ped granules for oral soln|emulsion for inj/infusion|Intensive Hydrating Cream|pre-filled pen \(Solostar\)|oral soln \(grape flavour\)|serum topical application|powd for infusion \(vial\)|inj \(pre-filled syringe\)|FlexPen \(pre-filled pen\)|Light Moisturising Cream|soln for infusion \(vial\)|vaccine \(inj\) \(lyo vial\)|DermaRelief Rescue Cream|Single dose powd for inj|Moisturizing Body Lotion|soln for inj \(cartridge\)|Daily Facial Moisturizer|Moisturising Bath & Wash|susp for inj \(cartridge\)|Gentle Foaming Cleanser|Ultrafresh Stretch Mark|Hydrating liqd cleanser|bladder irrigation soln|powd for inj \(lyo vial\)|fast disintegrating tab|Adlt pre-filled syringe|Moisturising Day cream|Revitalising eye cream|Nourishing Conditioner|Intifresh Hygiene Mist|granules for oral soln|Sensitive Light lotion|granules for oral susp|powd for inj/infusion|soln for inj/infusion|powd for soln for inj|Nurturing Night cream|Moisturising Cleanser|Ultrafresh Shower Gel|effervescent granules|granule for oral soln|Intensive oint-cream|gastro-resistant tab|Total Care mouthwash|Oil Free Moisturiser|infusion conc \(vial\)|DermaRelief Cleanser|vaccine \(inj\) \(vial\)|minimicrospheres cap|gastro-resistant cap|modified-release tab|Plus Expectorant syr|Preparation Cleanser|micronized FC caplet|oral saline laxative|respiratory solution|Richenic urea cream|powd for inj \(vial\)|soln for inj \(vial\)|penfill \(cartridge\)|Cool Mint mouthwash|inhalation powd cap|Aqueous nasal spray|Hydrating Body Wash|DermaRel Spray & Go|topical application|susp for inj \(vial\)|orodispersible film|Forte topical spray|soln for inhalation|Active chewable tab|Chocolate oral liqd|inhalation liqd cap|liqd for inhalation|susp for inhalation|Sugar-coated caplet|Inhalation Solution|respirator solution|powd for oral susp|Polyamp Duofit inj|powd for oral soln|soln for inj \(amp\)|Protect Hand Cream|powd for oral liqd|Moisturising Cream|Nourishing Shampoo|powd for IM/IV inj|orodispersible tab|cleansing bar soap|DermaRelief Lotion|Intratracheal susp|Multivitamin gummy|Professional Serum|Multi-Action Cream|inj \(lyo\) for soln|IV/IM powd for inj|Childn nasal drops|Infant nasal drops|film-coated caplet|enteric-coated tab|pre-filled syringe|Prefilled syringe|soln for infusion|powd for infusion|transdermal spray|transdermal patch|granules for susp|effervescent powd|topical soln conc|oral lyophilisate|powd for oral use|Adult nasal drops|Kids chewable tab|Vanilla oral liqd|milk powd Vanilla|infant oral drops|Plus Chewable tab|Infusion solution|Intensive lotion|Foaming cleanser|oromucosal spray|sugar-coated tab|effervescent tab|Body Moisturiser|Hydrating lotion|Medicated Lotion|Daily Face cream|Daily Oral Rinse|lyo powd for inj|Derma Rash cream|vaccine susp inj|soft gelatin cap|viscous solution|ophthalmic drops|Intensive cream|Soothing lotion|dispersible tab|film-coated tab|inhalation powd|childn granules|Gentle Cleanser|Sting-Free Oint|inhalation soln|oromucosal liqd|respirator soln|liqd-filled cap|forte oral susp|inhalation liqd|intraocular inj|IV powd for inj|Transparent gel|transdermal gel|oromucosal soln|Chewable caplet|milk powd Honey|Expectorant syr|liqd inhalation|Saline Solution|oral Suspension|powder/solution|Soothing cream|pre-filled pen|oromucosal gel|adult granules|Gentle Shampoo|Relizema cream|vaccine \(oral\)|infusion \(amp\)|nebuliser soln|Daily Moisture|vaccine \(vial\)|ear drops soln|ophth emulsion|pre-filled inj|nebulizer soln|Forte dry susp|Aerofilm gauze|sublingual tab|Micellar Water|eye & ear drop|eye suspension|infusion conc|vaccine \(inj\)|topical spray|eye/ear drops|liqd cleanser|oral granules|cleansing gel|topical cream|inj iopamidol|infusion soln|forte dry syr|dry syr Forte|eye-ear drops|oral solution|soln for inj|chewable tab|Repair cream|powd for inj|infusion bag|topical soln|topical liqd|Forte FC tab|susp for inj|topical powd|rectal cream|Foaming Wash|Ultra lotion|Daily Lotion|Forte caplet|soluble film|dental paste|facial cream|eye ointment|nail lacquer|vaccine oral|nasal spray|topical gel|ophth drops|nasal drops|softgel cap|KwikPen inj|chewing gum|Nappy Cream|Skin Lotion|Gentle Wash|Polyamp inj|rectal oint|Body Lotion|expectorant|Creamy Wash|shower pack|intensive moisturizer|Moisturizer|transdermal|ophth strip|vaccine inj|IV infusion|Plus caplet|topical oil|Night Cream|Moisturiser|Conditioner|Thermometer|Liquid Soap|concentrate|intravenous|suppository|oral liquid|stain strip|oral drops|ophth soln|Childn syr|oral spray|inj \(vial\)|Skin cream|Start oint|coated tab|ophth susp|scalp soln|Hand Cream|Rescue Gel|ophth oint|Sugar-free|toothpaste|inhalation|spray powd|nasal wash|caring oil|combi pack|mouthspray|active tab|Forte drag|rectal gel|turbuhaler|Thermoscan|dental gel|irrigation|nasal drop|oral paste|suspension|wound wash|supplement|oral liqd|oral susp|oral soln|eye drops|actuation|Adult syr|inj \(amp\)|milk powder|milk powd|ear drops|Ear Drop|mouthwash|Adult cap|Regen pad|FC caplet|XR-FC tab|Mouth gel|forte syr|DHA gummy|accuhaler|oral powd|cough syr|sunscreen|body wash|Forte cap|depot inj|liqd soap|forte tab|paed susp|gauze-pad|vag ovule|flash tab|liqd wash|adult tab|rapihaler|Day Cream|Injection|Plus susp|Nebuliser|sanitiser|container|infusion|cleanser|Sunblock|vag wash|infusion|oral gel|granules|liniment|Bath Oil|inj conc|evohaler|Kids syr|Gold cap|eye susp|eye oint|pastille|respules|Disp tab|hard cap|mite tab|GITS tab|band-aid|soft cap|Plus tab|dressing|solostar|orapaste|filcotab|Lip Balm|Emulsion|Eyedrops|Eyedrop|Eye Drop|solution|catridge|ointment|tincture|spansule|Shampoo|vag gel|vegecap|softcap|linctus|vag tab|vaccine|pessary|vegicap|topical|gummies|nebules|Softgels|softgel|plaster|filmtab|implant|dry syr|minitab|eye gel|chewtab|inhaler|dry inj|emulgel|Essence|Capsules|capsule|handrub|Lozenges|lozenge|mixture|Bandage|aerosol|pellets|FC tab|lotion|elixir|sachet|\(vial\)|ER tab|gargle|SolTab|caplet|troche|XR tab|teabag|CR tab|IV inj|EC tab|FC cap|MR tab|OD tab|bottles|bottle|DR cap|FX tab|captab|diskus|IR tab|douche|Balsam|liquid|powder|system|Tablets|tablet|wafers|durule|cream|Spray|gummy|drops|Drop|enema|ovule|sheet|jelly|licap|Patch|paste|Creme|Serum|beads|paint|scrub|strip|syrup|tears|gauze|stick|powd|drag|Wash|susp|liqd|oint|supp|soap|vial|soln|oral|foam|balm|salt|swab|film|melt|pill|wipe|cap|inj|dispertab|tab|gel|syr|loz|MDI|DPI|pen|oil|Kit|Jel|gum|udv|IV|insulin|mdv|syringe|bag)[^\w]'," "+org_form+" ",re.IGNORECASE)
#                             if(len(drug_name)>1):
#                                 for d in drug_name:
#                                         d = d.lower()
#                                         # org_form = org_form.lower()
#                                         if(org_form.lower().find(d)!=-1):
#                                             drug_match_in_form=form[org_form.lower().find(d):org_form.find(d)+len(d)]
#                                             best_match=drug_match_in_form
# #                                             current_drug=d
#                                 form = form.replace(drug_match_in_form,'')
#                                 form_without_drug_name = form_without_drug_name.replace(drug_match_in_form,'')
#                             else:
#                                 if(org_form.find(drug)==-1):
#                                     original_form = org_form.split()
#                                     drug_names = drug.split()
#                                     for i in range(len(original_form)):
#                                         if(original_form[i] in drug_names):
#                                             form = form.replace(original_form[i],'')
#                                             form_without_drug_name = form_without_drug_name.replace(original_form[i],'')
#                                 else:
#                                     pattern = re.compile(re.escape(drug), re.IGNORECASE)
#                                     form = pattern.sub('', form)
#                                     form_without_drug_name = pattern.sub('', org_form)
                            if(org_form.find('%')!=-1):
                                dos_match_from_form = re.findall('[^\w](\d+\.?\d*\s?mg\/?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?\d*\.?\d*\s?ml|\d+\.?\d*\s?IU\/?\d*\.?\d*\s?mL|\d+\.?\d*\s?g\/?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\d*\.?\d*\s?dose|\d+\.?\d*\s?mcg\/?\d*\.?\d*\s?hour|\d+\.?\d*\s?mg\/?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\d*\.?\d*\s?g|\d+\.?\d*\s?units\/?\d*\.?\d*\s?mL|\d+\.?\d*\s?mg\/?\d*\.?\d*\s?g|\d+\.?\d*\s?mg\/?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg\/?\d*\.?\d*\s?mL|\d+\s*mg(?:\/?(?:\d*\s*mL)?)?|\d+\.?\d*\s?g|\d+\.?\d*?MIU|\d+\.?\d*\s?IU|\d+\.?\d*\s?U|\d+\.?\d*\s?mcg|\d+\.?\d*\s?mL|\d+\.?\d*\s?u|\d+\.?\d*\s?U)[^\w]'," "+org_form+" ", re.DOTALL)
                                con_match_from_form = re.findall('\d+\.?\d*\s?%',org_form, re.DOTALL)
                            else:
                                con_match_from_form = []
                                dos_match_from_form = re.findall('[^\w](\d+\.?\d*\s?mg\/?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?\d*\.?\d*\s?ml|\d+\.?\d*\s?IU\/?\d*\.?\d*\s?mL|\d+\.?\d*\s?g\/?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\d*\.?\d*\s?dose|\d+\.?\d*\s?mcg\/?\d*\.?\d*\s?hour|\d+\.?\d*\s?mg\/?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\d*\.?\d*\s?g|\d+\.?\d*\s?units\/?\d*\.?\d*\s?mL|\d+\.?\d*\s?mg\/?\d*\.?\d*\s?g|\d+\.?\d*\s?mg\/?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg\/?\d*\.?\d*\s?mL|\d+\.?\d*\s?mg(?:\/\d+\.?\d*\s?mg)*|\d+\.?\d*\s*MIU|\d+\.?\d*\s?MU\/?\d*\.?\d*\s?mL|\d+.?\d*\/?\d*.?\d*\/?\d*.?\d*\s*mg(?:\/?(?:\d*.?\d*\s*mL)?)?|\d+.?\d*\s*g(?:\/?(?:\d*.?\d*\s*mL)?)?(?:\/?(?:\d*.?\d*\s*L)?)?|\d+\.?\d*?MIU|\d+\s*IU(?:\/?(?:\d*.?\d*\s*mL)?)?|\d+\.?\d*\s?U\/?mL|\d+.?\d*\/?\d*\s*mcg(?:\/?(?:\d*.?\d*\s*mL)?)?|\d+\.?\d*\s?mL|\d+\.?\d*\s?U|\d+\.?\d*\s?u)[^\w]'," "+org_form+" ", re.DOTALL)
                            if(len(dos_match_from_form)!=0 and len(con_match_from_form)!=0):
                                result=''
                                for cm in con_match_from_form:
                                    result+=cm+"/"
                                    # form=form.replace(cm,'',1)
                                con=result[:-1]
                                result=''
                                for dm in dos_match_from_form:
                                    result+=dm+"/"
                                    # form=form.replace(dm,'',1)
                                d=result[:-1]
                            elif(len(dos_match_from_form)!=0):
                                result=''
                                for m in dos_match_from_form:
                                    result+=m+"/"
                                    # form=form.replace(m,'',1)
                                d=result[:-1]
                                con=''
                            elif(len(con_match_from_form)!=0):
                                result=''
                                for m in con_match_from_form:
                                    result+=m+"/"
                                    # form=form.replace(m,'',1)
                                con=result[:-1]
                                d=''
                            elif(len(dos_match_from_form)==0 and len(con_match_from_form)==0):
                                d=''
                                con=''
                            # form = form.replace('  ',' ')
                            # form = form.replace('w/w','')
                            # form = form.replace('w/v','')
                            # form = form.strip()
                            # format_org = form
                            if(len(format_match_from_form)!=0):
                                format_org = format_match_from_form[0]
                            else:
                                format_org = ''
                            std_format = search(format_org)
                            if(std_format==None):
                                std_format = ''
                            d = re.sub(r'(\d+\.?\d*)\s*/\s*(\d+\.?\d*)\s*([A-Za-z]+)', r'\1\3/\2\3', d)
                            if(len(material_list)!=0):
                                    if(len(material_list) > 1 or len(drug_name) > 1):
                                        matched_material = ""
                                        if(is_length_to_map_equal == True):
                                            matched_material,material_to_map = get_matching_material(org_form,drug,list_of_dicts)
                                        if(len(matched_material)!=0 and is_length_to_map_equal == True):
                                            brand.append(drug)        
                                            manufacturer.append(manf)
                                            cimsClass.append(cims_class)
                                            mimsClass.append(mims_class)
                                            if(len(atc_code_list)!=0):
                                                atc_code = atc_code_list[0]
                                                atcCode.append(atc_code)
                                            elif(len(atc_code_list)==0):
                                                atcCode.append('')
                                            if(len(atc_list)!=0):
                                                atc=atc_list[0]
                                                atc=atc.replace('\u200b','')
                                                atc=atc.replace(';','')
                                                atc=atc.replace(',','')
                                                atc=atc.replace('  ',' ')
                                                atc=atc.strip('.')
                                                atcDetail.append(atc)
                                            elif(len(atc_list)==0):
                                                atcDetail.append('')
                                            std_uom=std_uom.strip()
                                            uom.append(std_uom)
                                            uom_dosage_list.append(uom_dosage)
                                            uom_quantity_list.append(quantity)
                                            unit_price_list.append(unit_price)
                                            amount.append(std_amount)
                                            mat=matched_material
                                            std_mat=matched_material
                                            dos = ""
                                            c = ""
                                            dos,c,current_mat,current_std_mat,format_org,std_format = extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,material_to_map,format_org,std_format,format_match)
                                            if(len(dos)==0 and len(c)==0):
                                                dos,c = extract_dos_con_from_drug(dos_match_from_drug,con_match_from_drug,dos,c,drug)
                                            dos = dos.replace(' ','')
                                            dos = dos.replace(',','')
                                            c = c.replace(' ','')
                                            c = c.replace(',','')
                                            dosage.append(dos)
                                            concentration.append(c)
                                            format_original.append(format_org)
                                            formater.append(std_format)
                                            material.append(current_mat)
                                            std_material.append(current_std_mat)
                                        elif(is_length_to_map_equal == False):
                                            add_manual(csv_headers,drug,manf,cims_class,mims_class,atc_code_list,atc_list,std_uom,std_amount,d,con,format_org,std_format,material_list,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,mat_to_map_list,format_match,uom_dosage,quantity,unit_price)
                                        else:
                                            pass
                                    else:
                                        entry = material_list[0]
                                        brand.append(drug)        
                                        manufacturer.append(manf)
                                        cimsClass.append(cims_class)
                                        mimsClass.append(mims_class)
                                        if(len(atc_code_list)!=0):
                                            atc_code = atc_code_list[0]
                                            atcCode.append(atc_code)
                                        elif(len(atc_code_list)==0):
                                            atcCode.append('')
                                        if(len(atc_list)!=0):
                                            atc=atc_list[0]
                                            atc=atc.replace('\u200b','')
                                            atc=atc.replace(';','')
                                            atc=atc.replace(',','')
                                            atc=atc.replace('  ',' ')
                                            atc=atc.strip('.')
                                            atcDetail.append(atc)
                                        elif(len(atc_list)==0):
                                            atcDetail.append('')
                                        std_uom=std_uom.strip()
                                        uom.append(std_uom)
                                        uom_dosage_list.append(uom_dosage)
                                        uom_quantity_list.append(quantity)
                                        unit_price_list.append(unit_price)
                                        amount.append(std_amount)
                                        mat=entry
                                        std_mat=entry
                                        dos = ""
                                        c = ""
                                        dos,c,current_mat,current_std_mat,format_org,std_format = extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,mat_to_map_list[0],format_org,std_format,format_match)
                                        if(len(dos)==0 and len(c)==0):
                                            dos,c = extract_dos_con_from_drug(dos_match_from_drug,con_match_from_drug,dos,c,drug)
                                        dos = dos.replace(' ','')
                                        dos = dos.replace(',','')
                                        c = c.replace(' ','')
                                        c = c.replace(',','')
                                        dosage.append(dos)
                                        concentration.append(c)
                                        format_original.append(format_org)
                                        formater.append(std_format)
                                        material.append(current_mat)
                                        std_material.append(current_std_mat)    
                            elif(len(material_list)==0):
                                if(drugClassification=='Generic'):
                                    current_mat = drug
                                    current_std_mat = drug
                                    drug = ''
                                material.append(current_mat)
                                if(len(d)==0 and len(con)==0):
                                    dos,c = extract_dos_con_from_drug(dos_match_from_drug,con_match_from_drug,dos,c,drug)
                                d=d.replace(' ','')
                                d=d.replace(',','')
                                con=con.replace(' ','')
                                con=con.replace(',','')
                                dosage.append(d)
                                concentration.append(con)
                                std_material.append(current_std_mat)
                                brand.append(drug)        
                                manufacturer.append(manf)
                                cimsClass.append(cims_class)
                                mimsClass.append(mims_class)
                                if(len(atc_code_list)!=0):
                                    atc_code = atc_code_list[0]
                                    atcCode.append(atc_code)
                                elif(len(atc_code_list)==0):
                                    atcCode.append('')
                                if(len(atc_list)!=0):
                                    atc=atc_list[0]
                                    atc=atc.replace('\u200b','')
                                    atc=atc.replace(';','')
                                    atc=atc.replace(',','')
                                    atc=atc.replace('  ',' ')
                                    atc=atc.strip('.')
                                    atcDetail.append(atc)
                                elif(len(atc_list)==0):
                                    atcDetail.append('')
                                std_uom=std_uom.strip()
                                uom.append(std_uom)
                                uom_dosage_list.append(uom_dosage)
                                uom_quantity_list.append(quantity)
                                unit_price_list.append(unit_price)
                                amount.append(std_amount)
                                format_original.append(format_org)
                                formater.append(std_format)
    file = open('MIMS Vietnam.csv', 'a', newline ='')
    with file:
        write = csv.writer(file)
        write.writerows(zip(csv_headers.brand,csv_headers.manufacturer,csv_headers.cimsClass,csv_headers.material,csv_headers.std_material,csv_headers.format_original,csv_headers.formater,csv_headers.concentration,csv_headers.dosage,csv_headers.uom,csv_headers.uom_dosage_list,csv_headers.uom_quantity_list,csv_headers.unit_price_list,csv_headers.amount,csv_headers.atcCode,csv_headers.atcDetail,[""]* len(csv_headers.brand),[""]* len(csv_headers.brand),["vi_VN"]* len(csv_headers.brand),csv_headers.mimsClass))
    f = open('Vietnam.csv', 'a', newline ='')
    with f:
        write = csv.writer(f)
        write.writerows(zip(brand,manufacturer,cimsClass,material,std_material,format_original,formater,concentration,dosage,uom,uom_dosage_list,uom_quantity_list,unit_price_list,amount,atcCode,atcDetail,[""]* len(brand),[""]* len(brand),["vi_VN"]* len(brand),mimsClass))      
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
    if file.startswith("mims_"):
        read_text_file(file)