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
def extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,format_org,std_format,format_match):
    std_mat=std_mat.strip()
    if(len(d)==0 and len(con)==0 ):
        # dosage_match = re.findall('\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U|\d*\.?\d*\s?mL',mat, re.DOTALL)# Regex extracting 2 gummies as 2g
        dosage_match = re.findall('\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u[^\w]|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g[^\w]|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U[^\w]|\d*\.?\d*\s?mL',mat, re.DOTALL)
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
    format_match = re.findall('\ssoluble insulin\s|\spowd for oral susp\s|\spowd for oral soln|\ssoftgel\s|\ssoln for inj\s|\sXR-FC tab\s|\smilk powd\s|\smoisturizing facial cleansing foam\s|\sintensive moisturizing cream\s|\srestorative hydration cream\s|\smoisturising bath & shampoo\s|\slight moisturising cream\s|\sdermarelief rescue cream\s|\smoisturizing body lotion\s|\smoisturising bath & wash\s|\sdaily facial moisturizer\s|\sgentle foaming cleanser\s|\smoisturising day cream\s|\srevitalising eye cream\s|\snourishing conditioner\s|\sultra hydrating lotion\s|\smoisturising body wash\s|\ssensitive light lotion\s|\snurturing night cream\s|\smoisturising cleanser\s|\sintensive moisturizer\s|\sintensive oint-cream\s|\soil free moisturiser\s|\sdermarelief cleanser\s|\srichenic urea cream\s|\shydrating body wash\s|\smoisturising lotion\s|\sdose: powd for inj\s|\spowd for inj\s|\smoisturising cream\s|\snourishing shampoo\s|\sdermarelief lotion\s|\smulti-action cream\s|\sprofessional serum\s|\smoisturising wash\s|\sintensive lotion\s|\sfoaming cleanser\s|\sbody moisturiser\s|\smedicated lotion\s|\sdaily face cream\s|\sdaily oral rinse\s|\sintensive cream\s|\ssoothing lotion\s|\sgentle cleanser\s|\ssting-free oint\s|\sfilm-coated tab\s|\ssoothing cream\s|\sgentle shampoo\s|\sdaily moisture\s|\scleansing gel\s|\scod liver oil\s|\srepair cream\s|\schewable tab\s|\sfoaming wash\s|\sultra lotion\s|\sdaily lotion\s|\snappy cream\s|\sskin lotion\s|\sgentle wash\s|\srectal oint\s|\smouth spray\s|\screamy wash\s|\smoisturizer\s|\shand cream\s|\srescue gel\s|\sfruit powd\s|\stoothpaste\s|\sinhalation\s|\scaring oil\s|\soral spray\s|\soral susp\s|\soral liqd\s|\smouthwash\s|\smouth gel\s|\soral soln\s|\sactuation\s|\scleanser\s|\ssunblock\s|\sbath oil\s|\sgranules\s|\sinsulin\s|\sshampoo\s|\sfc tab\s|\ssachet\s|\slotion\s|\stroche\s|\scream\s|\sdrops\s|\spowd\s|\ssusp\s|\sliqd\s|\swash\s|\ssupp\s|\sdose\s|\soint\s|\ssoln\s|\stab\s|\scap\s|\sinj\s|\sgel\s|\ssyr\s|\sgummies\s|\sgummy\s|\sturbuhaler\s|\saccuhaler\s|\sevohaler\s',mat.lower(),re.DOTALL)
    if(len(format_match)!=0 and len(format_org)==0):
        format_org=format_match[0].strip()
        std_format=search(format_org)   
    dosage_match_in_mat = re.findall('\d+\.?\d*\s?mg\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg\/?dose|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg\/?actuation|\d+\.?\d*\/?\d*\.?\d*\s?u\/?mL\s?\+?\s?\d*\.?\d*\s?mcg\/?mL|\d+\.?\d*\/?\d*\.?\d*\s?mg\/?mL|\d+\.?\d*\s?u\/?\-?\d*\.?\d*\s?u|\d+\.?\d*\/?\-?\d*\.?\d*\s?u[^\w]|\d+\.?\d*\s?g\/?\-?\d*\.?\d*\s?g|\d+\.?\d*\/?\-?\d*\.?\d*\s?g[^\w]|\d+\.?\d*\s?mcg\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\/?\-?\d*\.?\d*\s?mcg|\d+\.?\d*\s?IU\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?IU\/?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?IU|\d+\.?\d*\s?mL\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?mL|\d+\.?\d*\/?\-?\d*\.?\d*\s?ml|\d+\.?\d*\s?mg(?:\/\d+\.?\d*\s?mg)*|\d+\.?\d*\/?\-?\d*\.?\d*/?\-?\d*\.?\d*\s?mg|\d+\.?\d*\s?iu\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\/?\-?\d*\.?\d*\s?iu|\d+\.?\d*\s?KIU\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\/?\-?\d*\.?\d*\s?KIU|\d+\.?\d*\s?U\/?\-?\d*\.?\d*\s?U|\d+\.?\d*\/?\-?\d*\.?\d*\s?U[^\w]|\sg\s|\smL\s',mat, re.DOTALL)
    con_match_in_mat = re.findall('\d+\.?\d*\s?%',mat, re.DOTALL)
    if(len(dosage_match_in_mat)==0 and len(con_match_in_mat)==0):
        std_mat=std_mat.strip()
        current_mat=std_mat
        current_std_mat=std_mat
    elif(len(dosage_match_in_mat)!=0 and len(con_match_in_mat)!=0):
        std_mat=std_mat.strip()
        current_mat=std_mat
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
        pattern = re.compile(re.escape(format_match[0].rstrip()), re.IGNORECASE)
        std_mat = pattern.sub('', std_mat)
        # std_mat=std_mat.replace(format_match[0].strip(),'')
        current_std_mat=std_mat
    if(std_mat.startswith('Per ')):
        std_mat=std_mat.replace('Per ','')
        std_mat=std_mat.strip()
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
            drug_name=[]
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
                    activeIngredientsList=activeIngredients
                    if(activeIngredients[0].startswith('Per ')):
                        per='Per '
                        activeIngredientsList =  [per+e for e in activeIngredients[0].split(per) if e]
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
                            std_mat=entry
                            mat=entry
                            d,con,current_mat,current_std_mat,format_org,std_format=extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,format_org,std_format,format_match)
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
                for product in products:
                    packaging= product['packaging']
                    std_packaging=remove_substring_in_brackets(packaging)
                    print("std_pacaking",std_packaging)
                    org_form= product['form']
                    # form=org_form
                    replaced=std_packaging.replace('&#39;s','')
                    decode_x=replaced.replace('&#215;','x')
                    l=decode_x.split(';')
                    material_match=''
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
                                                print("write regex to match materail and associate with it")
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
                                                d,con,current_mat,current_std_mat,format_org,std_format=extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,format_org,std_format,format_match)
                                                d=d.replace(' ','')
                                                d=d.replace(',','')
                                                con=con.replace(' ','')
                                                con=con.replace(',','')
                                                dosage.append(d)
                                                concentration.append(con)
                                                material.append(current_mat)
                                                std_material.append(current_std_mat)
                                                format_original.append(format_org)
                                                formater.append(std_format)
                                                match_found.add(entry)
                                                break;
                                # if(string==-1):
                                #         activeIngredientsList=activeIngredients
                                #         if(activeIngredients[0].startswith('Per ')):
                                #             per='Per'
                                #             activeIngredientsList =  [per+e for e in activeIngredients[0].split(per) if e]
                                #             for entry in activeIngredientsList:
                                #                 entry=entry.replace(',','')
                                #                 entry=entry.replace(';','')
                                #                 entry=entry.replace('&amp;','&')
                                #                 entry=entry.strip()
                                #                 entry=entry.strip('.')
                                #                 if(entry not in match_found):
                                #                     print("exact match not found for material",entry)
                                #                     if(len(format_org)!=-1):
                                #                         pattern = r'\b(?:' + '|'.join(re.escape(word) for word in format_org.split()) + r')\b'
                                #                         match = re.search(pattern, entry, re.IGNORECASE)
                                #                         if(match):
                                #                             string = match.start()
                                #                     if(string!=-1):
                                #                         print("partial match found",entry,"format",format_org)
                                #                         brand.append(drugName)        
                                #                         manufacturer.append(manf)
                                #                         cimsClass.append(cims_class)
                                #                         mimsClass.append(mims_class)
                                #                         if(len(atc_code)!=0):
                                #                             atcCode.append(atc_code)
                                #                         elif(len(atc_code)==0):
                                #                             atcCode.append('')
                                #                         if(len(atc)!=0):
                                #                             if(len(atc)!=0):
                                #                                 atc=atc.replace(';','')
                                #                                 atc=atc.replace(',','')
                                #                                 atc=atc.replace('  ',' ')
                                #                                 atc=atc.strip('.')
                                #                                 atcDetail.append(atc)
                                #                         elif(len(atc)==0):
                                #                             atcDetail.append('')
                                #                         std_uom=std_uom.strip()
                                #                         uom.append(std_uom)
                                #                         amount.append('')
                                #                         format_original.append(format_org)
                                #                         formater.append(std_format)
                                #                         mat=entry
                                #                         std_mat=entry
                                #                         print("Current entry : ",mat)
                                #                         d,con,current_mat,current_std_mat=extract_dos_con_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat)
                                #                         dosage.append(d)
                                #                         concentration.append(con)
                                #                         material.append(current_mat)
                                #                         std_material.append(current_std_mat)
                                #                         match_found.add(entry)
                                #                         break;
                                #                     else:
                                #                         pass
                                #                 else:
                                #                     pass
                                if(string==-1):
#                                     if(products.index(product) == len(products)-1) : 
                                        activeIngredientsList=activeIngredients
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
                                            amount.append('')
                                            mat=entry
                                            std_mat=entry
                                            print("Current entry : ",mat)
                                            d,con,current_mat,current_std_mat,format_org,std_format=extract_dos_con_format_from_mat(d,con,mat,std_mat,dosage_match,con_match,dosage_match_in_mat,con_match_in_mat,format_org,std_format,format_match)
                                            d=d.replace(' ','')
                                            d=d.replace(',','')
                                            con=con.replace(' ','')
                                            con=con.replace(',','')
                                            dosage.append(d)
                                            concentration.append(con)
                                            material.append(current_mat)
                                            std_material.append(current_std_mat)
                                            format_original.append(format_org)
                                            formater.append(std_format)
                                            match_found.add(entry)
                                            # break;
                                            # else:
                                            #     print("material already matched",entry)
                                            #     pass 
#                                     else:
#                                         pass         
                        elif(len(activeIngredients)==0):
                            print("activeIngredients is empty")
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
    print(brand,manufacturer,cimsClass,material,std_material,format_original,formater,concentration,dosage,uom,atcCode,atcDetail,amount,mimsClass,match_found)
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