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
keywords_list = ['of', 'is', 'a', 'the', 'per', 'tab', 'syr', 'cap', 'fc', 'caplet', 'oral', 'susp', 'oral', 'inj', 'injection', 'soln', 'solution', 'dose', 'sugar-coated', 'forte', 'dry', 'paed', 'for', 'fC', 'drops', 'powd', 'liqd', 'mouthwash', 'rectal', 'oint', 'cream', 'daily', 'facial', 'moisturizer', 'gel', 'inhaler', 'vaccine', 'infant', 'softgel', 'eye', 'ointment', 'effervescent', 'chewtab', 'active', 'captab', 'dispersible', 'xr-fc', 'plus', 'chewable', 'dose:', 'extra', 'adult', 'mite', 'film-coated', 'softcap', 'soft', 'sachet', 'syrup', 'drag', 'bottle', 'mouthspray', 'toothpaste', 'shampoo', 'diskus', 'serum', 'lotion', 'spray']
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
    return local_keywords_list
def split_material(activeIngredients,drug_name):
    string = activeIngredients[0]
    pattern = r'\.\s*<strong>\s*([A-Za-z]+)|\,\s*<strong>\s*per|\.\s*<em>\s*per|\.\s*<em>\s*({})'.format('|'.join((drug.split()[0]) for drug in drug_name))
    indices = [0]+[m.start()+1 for m in re.finditer(pattern, string,re.IGNORECASE)] + [None]#appending first and last items to list
    active_ingredients_list = [string[indices[i]:indices[i+1]] for i in range(len(indices)-1)]   
    # active_ingredients_list.append(parts)
    return active_ingredients_list
def get_material(activeIngredients,drugName):#
    string_in_bold = []
    # cleaned_active_ingredients = []
    active_ingredients = []
    # activeIngredientsList = activeIngredients
    # find_string_to_split = re.findall(r'\.\s*<strong>', activeIngredients[0])
    # if(find_string_to_split):
    #     # Split the string using the matches
    #     split_active_ingredients = re.split(r'\.\s*<strong>', activeIngredients[0])
    #     # Combine the split parts with the matches to get the desired result
    #     activeIngredientsList = [split_active_ingredients[0]] + [match + split for match, split in zip(find_string_to_split, split_active_ingredients[1:])]
        
    if(len(activeIngredients)!= 0):
        for item in activeIngredients:
            item = item.replace('&amp;','&')
            item = item.replace(',','')
            item = item.replace(';','')
            item = item.replace('<sup>','^')
            item = item.replace('</sup>','')
            item = item.replace('<sub>','')
            item = item.replace('</sub>','')
            item = item.replace('<em>','')
            item = item.replace('</em>','')
            item = item.replace('  ',' ')
            bold_words = re.findall(r'\.?\s*<strong>(.*?)</strong>', item)
            item = item.strip('.')
            item = item.replace('<strong>','')
            item = item.replace('</strong>','')
            item = item.replace('  ',' ')
            item = item.strip()
            item = item.strip('.')
            if(len(bold_words)!=0):
                pattern = r'\b(?:Caplet/Effervescent tab|cream/oint|tab/drag|packet/capsule|eye drops/ear drops|tablet/package|packet/tablet|tablet/capsule|solution/per tablet|tab/\d+\s*mL|oint/powd|cap/\d+\s*mL|caplet/\d+\s*mL|/{}|{}/)\b'.format(re.escape(drugName), re.escape(drugName))
                matches = re.findall(pattern, bold_words[0], re.IGNORECASE)
                if(matches):  
                    split_bold = bold_words[0].split('/')
                    append_index = item.find(split_bold[-1])
                    for i,word in enumerate(split_bold):
                        cleaned_item = word + " " +item[append_index+len(split_bold[-1]):]
                        cleaned_item = re.sub(r'\s+', ' ', cleaned_item)
                        active_ingredients.append(cleaned_item.strip())
                        string_in_bold.append(word.strip())
                else:
                    string_in_bold.append(bold_words[0].strip())
                    active_ingredients.append(item)
            else:
                string_in_bold.append('')
                active_ingredients.append(item)
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
            dosage_match_in_mat = re.search('[^\w](\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg\/?dose|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg\/?actuation|\d+\.?\d*\/?\d*\.?\d*\s?u\/?mL\s?\+?\s?\d*\.?\d*\s?mcg\/?mL|\d+\.?\d*\/?\d*\.?\d*\s?mg\/?mL|\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg(?:\/\d+\.?\d*\s?mg)*|\d+\.?\d*\/?\-?\d*\.?\d*/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\sg\s|\smL\s|\sL\s|\samp\s|\sdose\s|\skCal\s|\sbar\s)[^\w]'," "+entry+" ", re.DOTALL)
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
                # print("match form :",max_index,"activeIngredient :",row["index"],list_of_dicts[row["index"]]["materialToMapForm"], forms_list[max_index])
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
    rows =[]
    for j,f in enumerate(drug_name):
        row = {
                "index": j,
                "values":[]
            }
        # current_entry=list_of_dicts[j]
        for k,a in enumerate(list_of_dicts):
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
def extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,material_to_map,format_org,std_format,format_match):
    std_mat=std_mat.strip()
    mat=mat.strip()
    if(len(d)==0 and len(con)==0 ):
        # dosage_match = re.findall('\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\d*\.?\d*\s?mL',mat, re.DOTALL)# Regex extracting 2 gummies as 2g
        dosage_match = re.findall('[^\w](\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\s?mg|\d*\.?\d*\s?mL|\d+\.?\d*\s?mcg)[^\w]'," "+mat+" ", re.DOTALL)
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
                else:
                    result+=m
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
                if(mat.startswith('Per '+regex_to_match_mL[0].strip())):
                    per_dosage=dosage_match.pop(0)
                    dosage_match.append(per_dosage)
            result=''
            for m in dosage_match:
                if(m.find('/')==-1):
                    result+=m+"/"
                    result=result.replace(' ','')
                else:
                    result+=m
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
    format_match = re.findall('\sexpectorant\s|\sCream & Intensive Cream\s|\sUltrafresh Stretch Mark\s|\sUltrafresh Shower Gel\s|\sIntifresh Hygiene Mist\s|Protect Hand Cream\s|Protect Hand Cream\s|\sunit dose vial\s|\spolyamp inj\s|\ssoluble insulin\s|\spowd for oral susp\s|\spowd for oral soln|\ssoftgel\s|\ssoln for inj\s|\sXR-FC tab\s|\smilk powd\s|\smoisturizing facial cleansing foam\s|\sintensive moisturizing cream\s|\srestorative hydration cream\s|\smoisturising bath & shampoo\s|\slight moisturising cream\s|\sdermarelief rescue cream\s|\smoisturizing body lotion\s|\smoisturising bath & wash\s|\sMoisturising Wash & Shampoo\s|\s Wash & Shampoo\s|\sdaily facial moisturizer\s|\sgentle foaming cleanser\s|\smoisturising day cream\s|\srevitalising eye cream\s|\snourishing conditioner\s|\sultra hydrating lotion\s|\smoisturising body wash\s|\ssensitive light lotion\s|\snurturing night cream\s|\smoisturising cleanser\s|\sintensive moisturizer\s|\sintensive oint-cream\s|\soil free moisturiser\s|\sdermarelief cleanser\s|\srichenic urea cream\s|\shydrating body wash\s|\smoisturising lotion\s|\sdose: powd for inj\s|\spowd for inj\s|moisturising cream\s|\snourishing shampoo\s|\sdermarelief lotion\s|\smulti-action cream\s|\sprofessional serum\s|\smoisturising wash\s|\sintensive lotion\s|\sfoaming cleanser\s|\sbody moisturiser\s|\smedicated lotion\s|\sdaily face cream\s|\sdaily oral rinse\s|\sintensive cream\s|\ssoothing lotion\s|\sgentle cleanser\s|\ssting-free oint\s|\sfilm-coated tab\s|\ssoothing cream\s|\sgentle shampoo\s|\sdaily moisture\s|\scleansing gel\s|\scod liver oil\s|\srepair cream\s|\schewable tab\s|\sfoaming wash\s|\sultra lotion\s|\sdaily lotion\s|\snappy cream\s|\sskin lotion\s|\sBody Lotion\s|\sgentle wash\s|\srectal oint\s|\smouth spray\s|\screamy wash\s|\smoisturizer\s|\shand cream\s|\srescue gel\s|\sfruit powd\s|\stoothpaste\s|\sinhalation\s|\scaring oil\s|\soral spray\s|\soral susp\s|\soral liqd\s|\smouthwash\s|\smouth gel\s|\soral soln\s|\sactuation\s|\scleanser\s|\ssunblock\s|\sbath oil\s|\sgranules\s|\sinsulin\s|\sshampoo\s|\sfc tab\s|\ssachet\s|\slotion\s|\stroche\s|\scream\s|\sdrops\s|\spowd\s|\ssusp\s|\sliqd\s|\swash\s|\ssupp\s|\soint\s|\ssoln\s|\stab\s|\scap\s|\sinj\s|\sgel\s|\ssyr\s|\sgummies\s|\sgummy\s|\sturbuhaler\s|\saccuhaler\s|\sevohaler\s|\smdv\s|\svial\s|\sSpray\s'," "+material_to_map+" ",re.IGNORECASE)
    if(len(format_match)!=0 and len(format_org)==0):
        format_org=format_match[0].strip()
        std_format=search(format_org)
    if(len(material_to_map)!=0): # Remove raw string from material
#         material_to_map = re.escape(material_to_map_form)#This ensures that any special characters are treated as literal characters in the regular expression pattern.
#         std_mat = re.sub(material_to_map,'',std_mat ,flags = re.IGNORECASE) #Ignore case while removing raw_string in material
        std_mat = std_mat.replace(material_to_map,'')
        std_mat = std_mat.strip()
    dosage_match_in_mat = re.findall('[^\w](\d+\.?\d*\s?mosm\/?\d*\.?\d*\s?L|\d+\.?\d*\/?\-?\d*\.?\d*\s?mOsm\/?\d*\.?\d*\s?L|\d+\.?\d*\s?mOsmol\/?\d*\s?L|\d+\.?\d*\s?mOsmol\/?\d*\s?kg|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg\/?dose|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg\/?actuation|\d+\.?\d*\/?\d*\.?\d*\s?u\/?mL\s?\+?\s?\d*\.?\d*\s?mcg\/?mL|\d+\.?\d*\/?\d*\.?\d*\s?mg\/?mL|\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg(?:\/\d+\.?\d*\s?mg)*|\d+\.?\d*\/?\-?\d*\.?\d*/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?mmol)[^\w]'," "+std_mat+" ", re.DOTALL)
    con_match_in_mat = re.findall('\d+\.?\d*\s?%',mat, re.DOTALL)
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
        std_mat=std_mat.replace('w/w','')
        std_mat=std_mat.replace('w/v','')
        std_mat=std_mat.strip('/')
        std_mat=std_mat.strip('&')
        std_mat=std_mat.replace(' / ',' ')
        std_mat=std_mat.replace(' . ',' ')
        std_mat=std_mat.replace('()',' ')
        std_mat=std_mat.strip('or')
        std_mat=re.sub(r'\s+', ' ', std_mat)
        std_mat=std_mat.strip() 
        current_std_mat=std_mat
    elif(len(dosage_match_in_mat)!=0):
        current_mat=mat
        for dm in dosage_match_in_mat:
            dm=dm.strip()
            std_mat=std_mat.replace(dm,'',1)
        std_mat=std_mat.strip('/')
        std_mat=std_mat.strip('&')
        std_mat=std_mat.replace(' / ',' ')
        std_mat=std_mat.replace('()',' ')
        std_mat=std_mat.replace(' . ',' ')
        std_mat=std_mat.strip('or')
        std_mat=re.sub(r'\s+', ' ', std_mat)
        std_mat=std_mat.strip()
        current_std_mat=std_mat
    elif(len(con_match_in_mat)!=0):
        current_mat=mat
        for cm in con_match_in_mat:
            std_mat=std_mat.replace(cm,'',1)
        std_mat=std_mat.replace('w/w','')
        std_mat=std_mat.replace('w/v','')
        std_mat=std_mat.strip('/')
        std_mat=std_mat.strip('&')
        std_mat=std_mat.replace(' / ',' ')
        std_mat=std_mat.replace('()',' ')
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
        dos,c,current_mat,current_std_mat,format_org,std_format = extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,mat_to_map_list[e],format_org,std_format,format_match)
        dos = dos.replace(' ','')
        dos = dos.replace(',','')
        c = c.replace(' ','')
        c = c.replace(',','')
        csv_headers.dosage.append(dos)
        csv_headers.concentration.append(c)
        csv_headers.format_original.append(format_org)
        csv_headers.formater.append(std_format)
        csv_headers.material.append(current_mat)
        csv_headers.std_material.append(current_std_mat)
def process_drug_name(drugName):
    parts = drugName.split('/')
    first_word = parts[0].split()[0]
    drug_name = []
    if first_word in parts[1]:
        for part in parts:
            drug_name.append(part)
    else:
        drug_name.append(drugName)
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
            # print (f"new combination of UOM found ignoring now: index : {index}  {uom} \n")
            if "new_combination" in map1.keys():
                map1["new_combination"] += 1
            else :
                map1["new_combination"] = 1


        first_element = split[0]
        is_only_digits = 1;
        for elem in split:
            if re.search( r'^\d+(\.\d+)?$', elem): 
                elem = int(elem)
                # if not isinstance(elem, str):
                    # print(elem)
                if elem and elem > 0 :
                    quantity *= elem
                    print("quantity:",quantity)
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
with open('MIMS Malaysia.csv','w') as file:
    writer = csv.writer(file)
    writer.writerow(["brand","manufacturer","cims_class","material","standard_material","format_original","standard_format","concentration","dosage","uom","uom_dosage","uom_quantity","unit_price","total_amount","atc_code","atc_detail","mdc_code","sub_format","locale","mims_class"])
with open('Malaysia.csv','w') as f:
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
            dos_match_from_packaging=''
            con_match_from_packaging=''
            format_match=''
            format_org=''
            std_format=''
            current_mat=''
            current_std_mat=''
            drug=''
            org_form=''
            std_uom=''
            std_amount=''
            drug_name=[]
            activeIngredientsList=[]
            is_length_to_map_equal = True
            print("--------------------------------------------------------------------------------",item['drugName'])
            products= item['details']['products']
            activeIngredients=item['details']['activeIngredients']
            drugName=item['drugName']
            drugName = drugName.replace(',','')
            drugName = drugName.replace('&amp;','&')
            drugName = drugName.replace('<sub>','')
            drugName = drugName.replace('</sub>','')
            drugName = drugName.replace('<em>','')
            drugName = drugName.replace('</em>','')
            drugName = drugName.replace('&quot;','"')
            atc_code_list=item['details']['atcCode']
            atc_list=item['details']['atc']
            manf=item['details']['manufacturer']
            cims_class=item['details']['cimsClass']
            mims_class=item['details']['mimsClass']
            drugClassification=item['drugClassification']
            individual_words = []
            if(drugName.find('/')!=-1):
                drug_name = process_drug_name(drugName)
            else:
                drug_name.append(drugName)
            individual_words = [word for item in drug_name for word in item.split() if not all(char.isdigit() for char in word)]
            if(len(activeIngredients)!=0):
                active_ingredients_list = split_material(activeIngredients,drug_name)
                mat_to_map_list,material_list = get_material(active_ingredients_list,drug_name[0])
            else:
                material_list = ''
            if(len(products)==0):
                for drug in drug_name:
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
                            print("is length equal for mapping : ",is_length_to_map_equal)
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
                                format_org = ''
                                std_format = ''
                                std_mat = matched_material
                                mat = matched_material
                                dos = ""
                                c = ""
                                dos,c,current_mat,current_std_mat,format_org,std_format = extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,material_to_map,format_org,std_format,format_match)
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
                                print("length not equal for mapping :",material_list,drug_name)
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
                                        format_org = ''
                                        std_format = ''
                                        std_mat = entry
                                        mat = entry
                                        dos = ""
                                        c = ""
                                        dos,c,current_mat,current_std_mat,format_org,std_format = extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,mat_to_map_list[e],format_org,std_format,format_match)
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
                            concentration.append('')
                            dosage.append('')
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
                            uom_dosage_list.append('')
                            uom_quantity_list.append(1)
                            unit_price_list.append('')
                            if(len(atc_code_list)!=0):
                                atc_code = atc_code_list[0]
                                atcCode.append(atc_code)
                            elif(len(atc_code_list)==0):
                                atcCode.append('')
                            if(len(atc_list)!=0):
                                atc=atc_list[0]
                                atc=atc.replace(';','')
                                atc=atc.replace(',','')
                                atc=atc.replace('  ',' ')
                                atc=atc.strip('.')
                                atcDetail.append(atc)
                            elif(len(atc_list)==0):
                                atcDetail.append('')
                            format_original.append('')
                            formater.append('')
                            uom.append('')
                            d=''
                            con=''
                            format_org=''
                            std_format=''
            elif(len(products)!=0):
                forms_list = get_forms(products)
                local_keywords_list = append_keywords_from_form_to_keywords_list(forms_list,drug_name)
                if(len(material_list)!=0):
                    if((len(material_list) != len(forms_list) and len(material_list)>1) or ((len(drug_name) != len(forms_list) and len(drug_name)>1)) or ((len(drug_name) != len(material_list) and len(drug_name)>1) and len(material_list)>1)):
                            print("drugname : ",drug_name,"material list : ",material_list,"forms list : ",forms_list)
                            is_length_to_map_equal = False
                    else:
                        if(len(material_list)>1):#map form to material in case of single or multiple drugNames
                            list_of_dicts = map_form_to_mat(forms_list,mat_to_map_list,material_list,drug_name)
                        if(len(drug_name)>1 and len(material_list)<=1):#map drugName to form in case of single material
                            list_of_dicts = map_drug_name_to_form(drug_name,forms_list,mat_to_map_list,material_list)
                for drug in drug_name:
                    for product in products:
                        packaging= product['packaging']
                        std_packaging=remove_substring_in_brackets(packaging)
                        org_form= product['form']
                        # form=org_form
                        replaced=std_packaging.replace('&#39;s','')
                        decode_x=replaced.replace('&#215;','x')
                        l=decode_x.split(';')
                        for i in l:
                            i=i.replace(',','')
                            i=i.replace(';','')
                            std_uom=remove_substring_in_brackets(i)
                            std_uom=std_uom.replace("'s",'')
                            std_uom=std_uom.strip()
                            print("amount:",std_amount)
                            if(std_amount):
                                std_amount = float(std_amount)
                            std_uom = std_uom.replace(' ','')
                            uom_dosage,quantity,unit_price,std_uom = get_uom_details(std_amount,std_uom)
                            org_form=org_form.replace(';','')
                            org_form=org_form.replace(',','')
                            form=org_form
                            for d in individual_words:
                                pattern = re.compile(re.escape(d), re.IGNORECASE)
                                form = pattern.sub('', form,1)
                            print("form:",form)
#                             if(len(drug_name)>1):
#                                 drug_match_in_form=''
#                                 for d in drug_name:
#                                         if(org_form.find(d)!=-1):
#                                             drug_match_in_form=form[:len(d)]
# #                                             current_drug=d
#                                 print("form to be replaced : ",drug_match_in_form)
#                                 form=form.replace(drug_match_in_form,'')
#                             else:
#                                 # current_drug=drugName
#                                 pattern = re.compile(re.escape(drug), re.IGNORECASE)
#                                 form = pattern.sub('', form)
                            form=form.strip()
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
                                        form=form.replace(m,'')
                                    d=result.strip('/')
                                    result=''
                                    for m in con_match_from_form:
                                        if(m.find('/')==-1):
                                            result+=m+"/"
                                        else:
                                            result=m
                                        form=form.replace(m,'')
                                    con=result.strip('/')
                                    form=form.replace('w/w','')
                                    form=form.replace('w/v','')
                                    format_org=form
                                elif(len(dos_match_from_form)!=0):
                                    con=''
                                    result=''
                                    for m in dos_match_from_form:
                                        if(m.find('/')==-1):
                                            result+=m+"/"
                                        else:
                                            result=m
                                        form=form.replace(m,'')
                                    d=result.strip('/')
                                elif(len(con_match_from_form)!=0):
                                    d=''
                                    result=''
                                    for m in con_match_from_form:
                                        if(m.find('/')==-1):
                                            result+=m+"/"
                                        else:
                                            result=m
                                        form=form.replace(m,'')
                                    con=result.strip('/')
                                    form=form.replace('w/w','')
                                    form=form.replace('w/v','')
                                    format_org=form
                                else:
                                    d=''
                                    con=''
                                    remove_raw_num=re.findall(r"\d+\/?\d*|\d+\.?\d*",form)#Remove raw numbers from form
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
                            format_org = format_org.replace('/','')
                            remove_raw_num=re.findall(r"\d+\/?\d*|\d+\.?\d*",format_org)#Remove raw numbers from form
                            if(remove_raw_num):
                                for n in remove_raw_num:
                                    format_org=format_org.replace(n,'')
                            format_org = format_org.strip()
                            print("cleaned form:",format_org)
                            format_org=format_org.strip()
                            std_format=search(format_org)
                            if(std_format==None):
                                std_format=''
                            d = re.sub(r'(\d+\.?\d*)\s*/\s*(\d+\.?\d*)\s*([A-Za-z]+)', r'\1\3/\2\3', d)
                            print("is length equal for mapping : ",is_length_to_map_equal)
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
                                            dos = dos.replace(' ','')
                                            dos = dos.replace(',','')
                                            c = c.replace(' ','')
                                            c = c.replace(',','')
                                            dosage.append(dos)
                                            concentration.append(c)
                                            format_original.append(format_org)
                                            formater.append(std_format)
                                            current_mat = current_mat.replace(',','')
                                            material.append(current_mat)
                                            std_material.append(current_std_mat)
                                        elif(is_length_to_map_equal == False):
                                            print("length not equal for mapping when form is present:",material_list,drug_name)
                                            add_manual(csv_headers,drug,manf,cims_class,mims_class,atc_code_list,atc_list,std_uom,std_amount,d,con,format_org,std_format,material_list,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,mat_to_map_list,format_match,uom_dosage,quantity,unit_price)
                                        else:
                                            pass;
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
                                            atc = atc_list[0]
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
                                    atc = atc_list[0]
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
    file = open('MIMS Malaysia.csv', 'a', newline ='')
    with file:
        write = csv.writer(file)
        write.writerows(zip(csv_headers.brand,csv_headers.manufacturer,csv_headers.cimsClass,csv_headers.material,csv_headers.std_material,csv_headers.format_original,csv_headers.formater,csv_headers.concentration,csv_headers.dosage,csv_headers.uom,csv_headers.uom_dosage_list,csv_headers.uom_quantity_list,csv_headers.unit_price_list,csv_headers.amount,csv_headers.atcCode,csv_headers.atcDetail,[""]* len(csv_headers.brand),[""]* len(csv_headers.brand),["en_MY"]* len(csv_headers.brand),csv_headers.mimsClass))
    f = open('Malaysia.csv', 'a', newline ='')
    with f:
        write = csv.writer(f)
        write.writerows(zip(brand,manufacturer,cimsClass,material,std_material,format_original,formater,concentration,dosage,uom,uom_dosage_list,uom_quantity_list,unit_price_list,amount,atcCode,atcDetail,[""]* len(brand),[""]* len(brand),["en_MY"]* len(brand),mimsClass))      
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