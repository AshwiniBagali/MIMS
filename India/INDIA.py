import json
import csv
import os
import re
import pandas as pd
from elasticsearch import Elasticsearch, helpers
with open('MMA_INDIA.csv','w') as file:
    writer = csv.writer(file)
    writer.writerow(["brand","manufacturer","cimsClass","material","standard_material","format_original","format","concentration","dosage","uom","atcCode","amount","atcDetail"])
def read_text_file(file): 
    print("filename----------------------------------------------------------------------- : ",file)
    with open(file) as f:
        data= [json.loads(line) for line in f]
        standard_format=''
        brand=[]
        manufacturer=[]
        cimsClass=[]
        atcCode=[]
        atcDetail=[]
        material=[]
        dosage=[]
        uom=[]
        amount=[]
        form=[]
        products=[]
        materials=[]
        formater=[]
        concentration=[]
        format_original=[]
        search_format=[]
        l=[]
        d=''
        con=''
        std_material=[]
        dosage_match=[]
        con_match=[]
        for item in data:
            products= item['details']['products']
            activeIngredients=item['details']['activeIngredients']
            for product in products:
                packaging= product['packaging']
                form= product['form']
                replaced=packaging.replace('&#39;s','')
                l=replaced.split(';')
                for i in l:
                    drugName=item['drugName']
                    drugName=drugName.replace(',','')
                    brand.append(drugName)
                    form=form.replace(item['drugName'],'')
                    form=form.strip()
                    format_original.append(form)
                    std_format=search(form)
                    formater.append(std_format)
                    manf=item['details']['manufacturer']
                    manf=manf.replace(',','')
                    manufacturer.append(manf)

                    cims=item['details']['cimsClass']
                    cims=cims.replace(',','')
                    cimsClass.append(cims)
                    
                    if(len(item['details']['atcCode'])!=0):
                        atcCode.append(item['details']['atcCode'])
                        atc=item['details']['atc']
                        std_atc=atc.replace(';','')
                        standard_atc=std_atc.replace(',','')
                        if(len(standard_atc)!=0):
                            if(standard_atc[len(standard_atc)-1]=='.'):
                                atcDetail.append(standard_atc[:len(standard_atc)-1])
                            else:
                                atcDetail.append(standard_atc)
                    else:
                        atcCode.append('')
                        atcDetail.append('') 
                    index=i.find('(')
                    if(index!=-1):
                        string=i[:index-1]
                        s=i.find('x')
                        x_first_occ=i[s+1:]
                        l_index=i.find('INR')
                        if(s!=-1):
                            per=i.find('%')
                            x_second_occ=x_first_occ.find('x')  
                            if(per!=-1):
                                con=i[:per+1]
                                con=con.replace(' ','')
                                concentration.append(con)
                                uom.append(i[s+2:index-1])
                                d=''
                                dosage.append('')
                                amt=i[index+1:l_index-1]
                                amt=amt.replace(',','')
                                amount.append(amt)
                            elif(per==-1):
                                con=''
                                concentration.append('')
                                if(x_second_occ!=-1):
                                    index=x_first_occ.find('(')
                                    l_index=x_first_occ.find('INR')
                                    uom.append(x_first_occ[x_second_occ+2:index]) 
                                    d=i[:s]
                                    d=d.replace(' ','')
                                    dosage.append(d)
                                    amt=x_first_occ[index+1:l_index-1]
                                    amt=amt.replace(',','')
                                    amount.append(amt)
                                elif(x_second_occ==-1):
                                    d=i[:s]
                                    d=d.replace(' ','')
                                    dosage.append(d)
                                    uom.append(i[s+2:index-1])
                                    amt=i[index+1:l_index-1]
                                    amt=amt.replace(',','')
                                    amount.append(amt)
                        else:
                            uom.append(string)
                            d=''
                            con=''
#                             dosage.append('')
#                             concentration.append('')
                            amt=i[index+1:l_index-1]
                            amt=amt.replace(',','')
                            amount.append(amt)
                    elif(index==-1):
                        s=i.find('x')
                        if(s!=-1):
                            per=i.find('%')
                            if(per!=-1):
                                con=i[:per+1]
                                con=con.replace(' ','')
                                concentration.append(con)
                                uom.append(i[s+2:])
                                d=''
                                dosage.append('')
                            elif(per==-1):
                                uom.append(i[s+2:])
                                d=i[:s]
                                d=d.replace(' ','')
                                dosage.append(d)
                                con=''
                                concentration.append('')
                        else:
                            uom.append(i)
                            d=''
                            con=''
                        #dosage.append('')
                        #concentration.append('')
                        amount.append('')
                    if(len(activeIngredients)!=0):    
                        for entry in activeIngredients:
                            string=entry.find(form)
                            entry=entry.replace(',','')
                            if(string!=-1):
                                find_index=entry.find(':')
                                mat=entry[find_index+2:-1]
                                if(len(d)==0 and form!="kit"):
                                            dosage_match = re.findall('\d+\.?\d*\s?g|\d+\.?\d*\s?mg|\d+\.?\d*\s?mcg|\d+\.?\d+\s?IU|\d+\.?\d*\s?mL|\d+\.?\d*\s?ml',mat, re.DOTALL)
                                            con_match = re.findall('\d+\.?\d*\s?%',mat, re.DOTALL)
                                            print("Match : ",len(dosage_match),len(con_match))
                                            if(len(dosage_match)!=0 and len(con_match)!=0):
                                                result=''
                                                for m in dosage_match:
                                                    result+=m+"/"
                                                    result=result.replace(' ','')
                                                #print("Current entry : ",mat)
                                                dosage.append(result[:-1])
                                                result=''
                                                for m in con_match:
                                                    result+=m+"/"
                                                    result=result.replace(' ','')
                                                concentration.append(result[:-1])
                                                #concentration.append('')
                                                print("Dosage and con success",result[:-1])
                                            elif(len(dosage_match)!=0):
                                                result=''
                                                for m in dosage_match:
                                                    result+=m+"/"
                                                    result=result.replace(' ','')
                                                dosage.append(result[:-1])
                                                concentration.append('')
                                                print("Dosage success",result[:-1]) 
                                            elif(len(con_match)!=0):
                                                result=''
                                                for m in con_match:
                                                    result+=m+"/"
                                                    result=result.replace(' ','')
                                                concentration.append(result[:-1])
                                                dosage.append('')
                                                print("Concentration success",result[:-1])    
                                            elif(len(dosage_match)==0 and len(con_match)==0 and len(con)==0):
                                                print("Dosage is not at all present",entry)
                                                concentration.append('')
                                                dosage.append('')
#                                 break;                
                                if(len(d)==0 and form=="kit"):
                                    dosage.append('')
                                    concentration.append('')
                                if(len(dosage_match)==0 and len(con_match)==0):
                                        print("dosage and con match not found : ",mat)
#                                         material.append(mat)
                                        if(mat[len(mat)-1]=='/'):
                                            mat=mat[:len(mat)-1]
                                        mat=mat.strip()
                                        std_material.append(mat)
                                elif(len(dosage_match)!=0 and len(con_match)!=0):
                                        print("dosage and con match found : ",dosage_match,con_match,mat)
#                                         material.append(mat)
                                        for dm in dosage_match:
                                            print("current dosage match : ",dm)
                                            mat=mat.replace(dm,'')
                                            mat=mat.replace('  ',' ')
                                            print("replaced entry : ",mat)
                                        for cm in con_match:
                                            print("current con match : ",cm)
                                            mat=mat.replace(cm,'')
                                            mat=mat.replace('  ',' ')
                                            #mat= re.sub(r'[^a-zA-Z/ ]', '', mat)
                                            print("replaced entry : ",mat)
                                        if(re.search(r"\d",mat)!=0):
                                            print("removing numbers")
                                            mat= re.sub(r'[^a-zA-Z/ ]', '', mat)
                                            mat=mat.replace('  ',' ')
                                        if(mat[len(mat)-1]=='/'):
                                            mat=mat[:len(mat)-1]
                                        mat=mat.strip()    
                                        std_material.append(mat)        
                                elif(len(dosage_match)!=0):
                                        print("dosage match found : ",dosage_match,mat)
#                                         material.append(mat)
                                        for dm in dosage_match:
                                            print("current dosage match : ",dm)
                                            mat=mat.replace(dm,'')
                                            mat=mat.replace('  ',' ')
                                            #mat= re.sub(r'[^a-zA-Z/ ]', '', mat)
                                            print("replaced entry : ",mat)
                                        if(re.search(r"\d",mat)!=0):
                                            print("removing numbers")
                                            mat= re.sub(r'[^a-zA-Z/ ]', '', mat)
                                            mat=mat.replace('  ',' ')
                                        if(mat[len(mat)-1]=='/'):
                                            mat=mat[:len(mat)-1]
                                        mat=mat.strip()
                                        std_material.append(mat)
                                elif(len(con_match)!=0):
                                        print("concentration match found : ",con_match,mat)
#                                         material.append(mat)
                                        for cm in con_match:
                                            print("current con match : ",cm)
                                            mat=mat.replace(cm,'')
                                            mat=mat.replace('  ',' ')
                                            print("replaced entry : ",mat)
                                        if(re.search(r"\d",mat)!=0):
                                            print("removing numbers")
                                            mat= re.sub(r'[^a-zA-Z/ ]', '', mat)
                                            mat=mat.replace('  ',' ')
                                        if(mat[len(mat)-1]=='/'):
                                            mat=mat[:len(mat)-1]
                                        mat=mat.strip()
                                        std_material.append(mat)
                                if(entry[len(entry)-1]=='.'):
                                    print("Material : ",entry[find_index+1:len(entry)-1])
                                    mat=entry[find_index+1:len(entry)-1]
                                    mat=mat.strip()
                                    material.append(mat)
                                elif(entry[len(entry)-1]!='.'):
                                    print("Material : ",entry[find_index+1:])
                                    mat=entry[find_index+1:]
                                    mat=mat.strip()
                                    material.append(mat) 
                                break;
                        if(string==-1):
                            for entry in activeIngredients:
                                entry=entry.replace(',','')
                                if(len(d)==0 and len(con)==0):
                                    print("dosage is not at all present",entry)
                                    dosage.append('')
                                    concentration.append('')
                                if(entry[len(entry)-1]=='.'):
                                    print("Material : ",entry[:len(entry)-1])
                                    mat=entry[:len(entry)-1]
                                    mat=mat.strip()
                                    material.append(mat)
                                elif(entry[len(entry)-1]!='.'):
                                    print("Material : ",entry)
                                    mat=entry
                                    mat=mat.strip()
                                    material.append(mat) 
                                print("current material : ",mat)
                                if(len(dosage_match)==0 and len(con_match)==0):
                                        print("dosage and con match not found : ",mat)
#                                         material.append(mat)
                                        if(mat[len(mat)-1]=='/'):
                                            mat=mat[:len(mat)-1]
                                        mat=mat.strip()
                                        std_material.append(mat)
                                elif(len(dosage_match)!=0 and len(con_match)!=0):
                                        print("dosage and con match found : ",dosage_match,con_match,mat)
#                                         material.append(mat)
                                        for dm in dosage_match:
                                            print("current dosage match : ",dm)
                                            mat=mat.replace(dm,'')
                                            mat=mat.replace('  ',' ')
                                            print("replaced entry : ",mat)
                                        for cm in con_match:
                                            print("current con match : ",cm)
                                            mat=mat.replace(cm,'')
                                            mat=mat.replace('  ',' ')
                                            #mat= re.sub(r'[^a-zA-Z/ ]', '', mat)
                                            print("replaced entry : ",mat)
                                        if(re.search(r"\d",mat)!=0):
                                            print("removing numbers")
                                            mat= re.sub(r'[^a-zA-Z/ ]', '', mat)
                                            mat=mat.replace('  ',' ')
                                        if(mat[len(mat)-1]=='/'):
                                            mat=mat[:len(mat)-1]
                                        mat=mat.strip()    
                                        std_material.append(mat)        
                                elif(len(dosage_match)!=0):
                                        print("dosage match found : ",dosage_match,mat)
#                                         material.append(mat)
                                        for dm in dosage_match:
                                            print("current dosage match : ",dm)
                                            mat=mat.replace(dm,'')
                                            mat=mat.replace('  ',' ')
                                            #mat= re.sub(r'[^a-zA-Z/ ]', '', mat)
                                            print("replaced entry : ",mat)
                                        if(re.search(r"\d",mat)!=0):
                                            print("removing numbers")
                                            mat= re.sub(r'[^a-zA-Z/ ]', '', mat)
                                            mat=mat.replace('  ',' ')
                                        if(mat[len(mat)-1]=='/'):
                                            mat=mat[:len(mat)-1]
                                        mat=mat.strip()
                                        std_material.append(mat)
                                elif(len(con_match)!=0):
                                        print("concentration match found : ",con_match,mat)
#                                         material.append(mat)
                                        for cm in con_match:
                                            print("current con match : ",cm)
                                            mat=mat.replace(cm,'')
                                            mat=mat.replace('  ',' ')
                                            print("replaced entry : ",mat)
                                        if(re.search(r"\d",mat)!=0):
                                            print("removing numbers")
                                            mat= re.sub(r'[^a-zA-Z/ ]', '', mat)
                                            mat=mat.replace('  ',' ')
                                        if(mat[len(mat)-1]=='/'):
                                            mat=mat[:len(mat)-1]
                                        mat=mat.strip()
                                        std_material.append(mat)
                    elif(len(activeIngredients)==0):
                        material.append('')
                        std_material.append('')
                        if(len(d)==0):
                            dosage.append('')
                        if(len(con)==0 and len(d)==0): 
                            concentration.append('')
#                         amount.append('')
#                         uom.append(i)
#                     if(len(d)!=0):
#                         print("Dosage not present",material[i])
#                         pattern = '\d+\.?\d*\s?g|\d+\.?\d*\s?mg|\d+\.?\d*\s?mcg|\d+\.?\d+\s?IU|\d+\.?\d*\s?mL|\d+\.?\d*\s?ml'
#                         test_string = material
#                         result = re.match(pattern, test_string)
#                         if result:
#                              print("Search successful.")
#                         else:
#                              print("Search unsuccessful.")	
    file = open('MMA_INDIA.csv', 'a', newline ='')
    with file:
        write = csv.writer(file)
        write.writerows(zip(brand,manufacturer,cimsClass,material,std_material,format_original,formater,concentration,dosage,uom,atcCode,amount,atcDetail))      
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
    