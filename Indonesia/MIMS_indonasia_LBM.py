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
def extract_dos_con_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,format_org,std_format,format_match):
    std_mat=std_mat.strip()
    if(len(d)==0 and len(con)==0 ):
        dosage_match = re.findall('[^\w](\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\d*\.?\d*\s?mL)[^\w]'," "+mat+ " ", re.DOTALL)
        regex_to_match_mL=re.findall('\d*\.?\d*\s?mL',mat, re.DOTALL)
        con_match = re.findall('\d+\.?\d*\s?%',mat, re.DOTALL)
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
    format_match=re.findall('\ssugar-coated caplet\s|\sForte dry syr\s|\sPaed tab\s|\ssoln for inj\s|\sForte FC caplet\s|\sforte cap\s|\spaed drops\s|\spowd for oral liqd\s|\s powd for oral soln\s|\smouthwash\s|\srectal oint\s|\srectal cream\s|\sDaily Facial Moisturizer\s|\sInjection\s|\sForte gel\s|\sdose inhaler\s|\sdose vaccine\s|\sforte dry syr\s|\sForte dry syr\s|\sForte syr\s|\sforte syr\s|\sdry syr\s|\sinfant drops\s|\soral drops\s|\sOral drops\s|\soral liqd\s|\soral gel\s|\ssoftgel\s|\seye gel\s|\sEye Drops\s|\seye drops\s|\sEye Ointment\s|\stab Dry\s|\seffervescent tab\s|\sEffervescent tab\s|\schewtab\s|\sactive tab\s|\scaptab\s|\sDispersible tab\s|\sXR-FC tab\s|\sPlus tab\s|\ssugar-coated tab\s|\sFC tab\s|\schewable tab\s|\sforte tab\s|\sForte tab\s|\sLutevision Extra tab\s|\sAdult tab\s|\sadult tab\s|\smite tab\s|\sfilm-coated tab\s|\ssoftcap\s|\sForte dry susp\s|\sForte oral susp\s|\soral soln\s|\ssoft cap\s|\sForte susp\s|\spaed susp\s|\sforte liqd\s|\sForte cap\s|\sForte caplet\s|\sforte caplet\s|\sfilm-coated caplet\s|\sFC caplet\s|\sdose: Powd for inj\s|\soral susp\s|\ssachet\s|\sSachet\s|\scaplet\s|\sCaplet\s|\stab\s|\sTab\s|\scap\s|\sCap\s|\ssyrup\s|\ssyr\s|\sSyr\s|\sdrops\s|\ssusp\s|\sliqd\s|\spowd\s|\sdrag\s|\sbottle\s|\sForte\s|\sinj\s|\scream\s|\sCream\s|\soint\s|\smouthspray\s|\stoothpaste\s|\sshampoo\s|\sDiskus\s|\sgel\s|\sSerum\s|\slotion\s|\sLotion\s|\sdose\s|\ssoln\s|\sspray\s',mat, re.DOTALL)
    if(len(format_match)!=0 and len(format_org)==0):
        format_org=format_match[0].strip()
        std_format=search(format_org) 
    dosage_match_in_mat = re.findall('[^\w](\d+\.?\d*\/?\d*\.?\d*\s?u\/?mL\s?\+?\s?\d*\.?\d*\s?mcg\/?mL|\d+\.?\d*\/?\d*\.?\d*\s?u\/?mL|\d+\.?\d*\/?\d*\.?\d*\s?g\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\d*\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?dose|\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\sg\s|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\smL\s|\d+\.?\d*\s?mg(?:\/\d+\.?\d*\s?mg)*|\d+\.?\d*\/?\-?\d*\.?\d*\s?\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U)[^\w]'," " +std_mat+ " ", re.DOTALL)
    con_match_in_mat = re.findall('\d+\.?\d*\s?%',mat, re.DOTALL)
    if(len(dosage_match_in_mat)==0 and len(con_match_in_mat)==0):
        std_mat=std_mat.strip()
        current_mat=std_mat
        current_std_mat=std_mat
    elif(len(dosage_match_in_mat)!=0 and len(con_match_in_mat)!=0):
        std_mat=std_mat.strip()
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
        current_mat=std_mat
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
        current_mat=std_mat
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
        std_mat=std_mat.replace(format_match[0].strip(),'')
        current_std_mat=std_mat
    if(std_mat.startswith('Per ')):
        std_mat=std_mat.replace('Per ','')
        current_std_mat=std_mat
    return d,con,current_mat,current_std_mat,format_org,std_format
with open('MIMS Indonasia NEW.csv','w') as file:
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
        materials=[]
        formater=[]
        concentration=[]
        format_original=[]
        l=[]
        activeIngredientsList=[]
        std_material=[]
        mimsClass=[]
        amount=[]
        print("file name:",file)
        for item in data:
            material_match=''
            d=''
            con=''
            dosage_match=''
            con_match=''
            dosage_match_in_mat=''
            con_match_in_mat=''
            format_match=''
            replaced_mat=''
            format_org=''
            std_format=''
            current_mat=''
            current_std_mat=''
            drug=''
            org_form=''
            std_uom=''
            std_amount=''
            drug_name=[]
            dos_match_from_form=''
            match_found=set()
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
                    string=-1
#                             for listItem in activeIngredients:
                    activeIngredientsList=activeIngredients
                    if(activeIngredients[0].startswith('Per ')):
                        per='Per '
                        activeIngredientsList =  [per+e for e in activeIngredients[0].split(per) if e]
                        print("actIng : ",len(activeIngredients))
                    for entry in activeIngredientsList:
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
                        # if(entry[len(entry)-1]=='.'):
                        #     entry=entry[:len(entry)-1]
                        std_mat=entry
                        mat=entry
                        d,con,current_mat,current_std_mat,format_org,std_format=extract_dos_con_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,format_org,std_format,format_match)
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
                        concentration.append('')
                        dosage.append('')
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
                for product in products:
                    packaging= product['packaging']
                    org_form= product['form']
                    form=org_form
                    replaced=packaging.replace('&#39;s','')
                    decode_x=replaced.replace('&#215;','x')
                    l=decode_x.split(';')
                    material_match=''
                    for i in l:
                        i=i.replace(',','')
                        i=i.replace(';','')
                        print("i value:------------------------------------------------------------------------------------------------",i)
                        index=i.find('Rp')
                        raw_amount=i[index+2:]
                        l_index=raw_amount.find('/')
                        if(index!=-1):
                            std_uom=i[:index-2]
                            std_amount=raw_amount[:l_index]
                            std_uom=remove_substring_in_brackets(std_uom)
                            print("amount",std_amount)
                        else:
                            std_amount=''
                            std_uom=remove_substring_in_brackets(i)
                        i=i.strip()
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
                            dos_match_from_form = re.findall('\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?spray|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?puff|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?actuation|\d+\.?\d*\/?\d*\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?dose|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?metered spray|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\/?\-?\d*\.?\d*\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\d+\s?DHA',org_form, re.DOTALL)
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
                                    d=''
                                    material_match=con
                                elif(form.find('%')==-1):
                                    print("dosage from form:",form[m.start():])
                                    d=form[m.start():]
                                    material_match=d
                                    con=''
                                format_org=form[:m.start()]
                            else:
                                format_org=form
                                d=''
                                con=''
                        std_format=search(format_org)
                        if(std_format==None):
                            std_format=''
                        if(len(activeIngredients)!=0):
                                string=-1
                                activeIngredientsList=activeIngredients
                                if(activeIngredients[0].startswith('Per ')):
                                    per='Per '
                                    activeIngredientsList =  [per+e for e in activeIngredients[0].split(per) if e]
                                for entry in activeIngredientsList:
                                            entry=entry.replace('&amp;','&')
                                            entry=entry.replace(',','')
                                            entry=entry.replace(';','')
                                            entry=entry.strip()
                                            entry=entry.strip('.')
                                            # print("entry : ",entry,"form",format_org,"drugName:",current_drug)
                                            if(entry.startswith('Per ')):
                                                print("write regex to match pattern for material")
                                                # if(string==-1 and len(format_org)!=0):
                                                #     if(current_drug in activeIngredients[0]):
                                                #         print("search by drugName")
                                                #         if(entry.find(current_drug)!=-1):
                                                #             print("match drugName :",current_drug)
                                                #             pattern = re.compile(re.escape(format_org), re.IGNORECASE)
                                                #             match = pattern.search(entry)
                                                #             if(match):
                                                #                 print("match format with ignore case",format_org)
                                                #                 string=match.start()
                                                #             # string=entry.find(current_drug)
                                                #     else:
                                                #         if(string==-1):
                                                #             pattern = re.compile(re.escape(format_org), re.IGNORECASE)
                                                #             match = pattern.search(entry)
                                                #             if(match):
                                                #                 print("match format with ignore case",format_org)
                                                #                 string=match.start()
                                                #             if(string==-1):
                                                #                 if(len(material_match)!=0):
                                                #                     print("dos or con match")
                                                #                     string=entry.find(material_match)
                                                #                 if(string==-1):
                                                #                     match_res=''
                                                #                     match_pattern= re.findall('\d+\.?\d*',format_org,re.DOTALL)
                                                #                     if(len(match_pattern)!=0):
                                                #                         print("match digits from dosage or con",match_pattern)
                                                #                         result=''
                                                #                         for match in match_pattern:
                                                #                             if(match.find('/')==-1):
                                                #                                 match_res+=match+"/"
                                                #                         match_res=match_res[:-1]
                                                #                         string=entry.find(match_res)
                                            # else:
                                            #     if(len(form)!=0):
                                            #         string=entry.find(form)
                                            print("string value",string)
                                            if(string!=-1 and string!=0):
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
                                                amount.append(std_amount)
                                                mat=entry
                                                std_mat=entry
                                                d,con,current_mat,current_std_mat,format_org,std_format=extract_dos_con_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,format_org,std_format,format_match)
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
                                                match_found.add(entry)
                                                break;
                                # if(string==-1):
                                #         print("dos or conc is not extercted from mat",len(d),len(con),len(dosage_match),len(con_match))
                                #         if(activeIngredients[0].startswith('Per ')):
                                #             per='Per'
                                #             activeIngredientsList =  [per+e for e in activeIngredients[0].split(per) if e]
                                #         for entry in activeIngredientsList:
                                #             entry=entry.replace(',','')
                                #             entry=entry.replace(';','')
                                #             entry=entry.replace('&amp;','&')
                                #             entry=entry.strip()
                                #             entry=entry.strip('.')
                                #             if(entry not in match_found):
                                #                 print("exact match not found for material",entry)
                                #                 if(len(format_org)!=-1):
                                #                     pattern = r'\b(?:' + '|'.join(re.escape(word) for word in format_org.split()) + r')\b'
                                #                     match = re.search(pattern, entry, re.IGNORECASE)
                                #                     if(match):
                                #                       string = match.start()
                                #                 if(string!=-1):
                                #                     print("partial match found",entry,"format",format_org)
                                #                     brand.append(drugName)        
                                #                     manufacturer.append(manf)
                                #                     cimsClass.append(cims_class)
                                #                     mimsClass.append(mims_class)
                                #                     if(len(atc_code)!=0):
                                #                         atcCode.append(atc_code)
                                #                     elif(len(atc_code)==0):
                                #                         atcCode.append('')
                                #                     if(len(atc)!=0):
                                #                         atc=atc.strip('.')
                                #                         atcDetail.append(atc)
                                #                     elif(len(atc)==0):
                                #                         atcDetail.append('')
                                #                     std_uom=std_uom.strip()
                                #                     uom.append(std_uom)
                                #                     amount.append(std_amount)
                                #                     format_original.append(format_org)
                                #                     formater.append(std_format)
                                #                     mat=entry
                                #                     std_mat=entry
                                #                     print("Current entry : ",mat)
                                #                     d,con,current_mat,current_std_mat=extract_dos_con_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat)
                                #                     dosage.append(d)
                                #                     concentration.append(con)
                                #                     material.append(current_mat)
                                #                     std_material.append(current_std_mat)
                                #                     match_found.add(entry)
                                #                     break;
                                #                 else:
                                #                     pass
                                #             else:
                                #                 pass
                                if(string==-1):
                                    # if(products.index(product) == len(products)-1) :   
                                        if(activeIngredients[0].startswith('Per ')):
                                            per='Per '
                                            activeIngredientsList =  [per+e for e in activeIngredients[0].split(per) if e]
                                        for entry in activeIngredientsList:
                                            entry=entry.replace(',','')
                                            entry=entry.replace(';','')
                                            entry=entry.replace('&amp;','&')
                                            entry=entry.strip()
                                            entry=entry.strip('.')
                                            # if(entry not in match_found):
                                            #         print("partial match also not found for material",entry)
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
                                            amount.append(std_amount)
                                            mat=entry
                                            std_mat=entry
                                            print("Current entry : ",mat)
                                            d,con,current_mat,current_std_mat,format_org,std_format=extract_dos_con_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,format_org,std_format,format_match)
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
                                            match_found.add(entry)
                                            #         break;
                                            # else:
                                            #     print("material already matched",entry)
                                            #     pass 
                                    # else:
                                    #     pass         
                        elif(len(activeIngredients)==0):
                            print("activeIngredients is empty")
                            if(drugClassification=='Generic'):
                                current_mat=drugName
                                current_std_mat=drugName
                            material.append(current_mat)
                            d=d.replace(',','')
                            d=d.replace(' ','')
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
                            amount.append(std_amount)
                            format_original.append(format_org)
                            formater.append(std_format)
    print(brand,manufacturer,cimsClass,material,std_material,format_original,formater,concentration,dosage,uom,atcCode,atcDetail,amount,mimsClass,match_found)
    file = open('MIMS Indonasia NEW.csv', 'a', newline ='')
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