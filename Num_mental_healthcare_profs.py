#!/usr/bin/env python
import pandas as pd
import numpy as np
import urllib2
import sys
import re
import xlrd
import time
try:
    from bs4 import BeautifulSoup
except ImportError:
    from BeautifulSoup import BeautifulSoup

###
factor_raw='Zipcode_Num_Mental_Healthcare_Profs'
dist=15
###
factor = factor_raw + '_' + str(dist) + 'mileradius'
#df = pd.read_csv('/Users/PSYC-dap3463/Desktop/zipcodes_raw.csv',na_values="")
xls = pd.ExcelFile('/Users/PSYC-dap3463/Desktop/zipcodes_raw.xls')
df = xls.parse('Sheet1')
df_ref = pd.read_csv('/Users/PSYC-dap3463/Documents/MDL_projects/Deprexis_python/ZNA/zip_code_database.csv',na_values="0")
df['zip']=df['zip'].astype('str').map(lambda x: x.rstrip('.0'))
df[factor] = np.random.randn(len(df['ID']))
df_ref['zip'] = df_ref['zip'].apply(str).apply(lambda x: x.zfill(5))

for ID in df['ID']:
    ZIPCODE=df[(df['ID'] == ID)].zip
    if ZIPCODE.values[0] == 'nan' or len(str(ZIPCODE)) == 0:
        continue
    #ZIPCODE=str(int(ZIPCODE.values[0])).zfill(5)
    ZIPCODE=str(int(ZIPCODE.values[0]))
    ##Extract ID index
    ID_index=df[(df['ID'] == ID)].index.values[0]
    #try:
        #zip_type=df_ref[(df_ref['zip'] == ZIPCODE)]['type'].values[0]
        #print('Zipcode for subject ' + str(ID) + ' is ' + str(ZIPCODE) + '\n' + 'Zipcode type is: ' + zip_type)
    #except:
        #print('NO ZIP FOUND FOR ' + str(ID) + '. Skipping ' + str(ID))
        #continue
    ##Crawl psychologytoday html to get number of unique mphone numbers of mental healthcare professionals in a search by zipcode
    #psychtoday_url=str('https://therapists.psychologytoday.com/rms/zip/' + str(ZIPCODE) + '.html')
    psychtoday_url=str('https://therapists.psychologytoday.com/rms/prof_results.php?sid=1474246095.6256_25374&zipcode=' + str(ZIPCODE) + '&zipdist=' + str(dist) + '&spec=2')
    time.sleep(2)
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    response = opener.open(psychtoday_url)
    html_contents = response.read()
    soup = BeautifulSoup(html_contents)

    y=[]

    for link in soup.find_all('a'):
        y.append(str(link.get('href')))

    z=[]
    sub='rec_next'
    for s in y:
        if sub.lower() in s.lower():
		    z.append(str(s))

    ##Ensure each subsequent page is a unique url
    z=list(set(z))

    ##Get number of contacts on first page
    if not z:
        num_mental_health_facilities=len(set(re.findall("[(][\d]{3}[)][ ]?[\d]{3}-[\d]{4}", html_contents)))
        print('Number of mental health care professionals within zipcode: ' + str(num_mental_health_facilities))
        num_mental_health_profs_ix=df[(df['ID'] == ID)].columns.get_loc(factor)
        df.ix[ID_index,num_mental_health_profs_ix]=num_mental_health_facilities
        print('\n\n')
        continue
    else:
        print('Multiple pages of output. Parsing...')

    ##Start counter
    count=0

    for i in z:
        time.sleep(2)
        psychtoday_url_page='https://therapists.psychologytoday.com' + i
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        try:
            response = opener.open(psychtoday_url_page)
        except urllib2.HTTPError, e:
            print("\n\n\nConnection Error!")
            continue
        html_contents = response.read()
        num_mental_health_facilities=len(set(re.findall("[(][\d]{3}[)][ ]?[\d]{3}-[\d]{4}", html_contents)))
        print('Crawling page ' + str(z.index(i)+int(1)) + "\n" + 'Found ' + str(num_mental_health_facilities) + ' healthcare professionals...' + "\n")
        count = count + num_mental_health_facilities

    print('Number of mental health care professionals within zipcode: ' + str(count))
    value_ix=df[(df['ID'] == ID)].columns.get_loc(factor)
    df.ix[ID_index,value_ix]=count
    print('\n\n')

save_loc='/Users/PSYC-dap3463/Desktop/zipcode_' + factor + str(dist) + '.csv'
df.to_csv(save_loc)
