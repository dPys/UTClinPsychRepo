#!/usr/bin/env python
import pandas as pd
from pandas.io.stata import StataWriter
import sys
import re
import numpy as np
from pyzipcode import ZipCodeDatabase
from uszipcode import ZipcodeSearchEngine
import urllib2
import urllib3
import xlrd
import time
from __future__ import division
import ast
from geopy.distance import vincenty
try:
    from bs4 import BeautifulSoup
except ImportError:
    from BeautifulSoup import BeautifulSoup
from rpy2.robjects import pandas2ri
pandas2ri.activate()
from rpy2.robjects import r

####RUN OPTIONS####
USCENSUS = 1
PSYCHTODAY = 1
MOVING = 1
###################

df = pd.read_stata('/Users/PSYC-dap3463/Desktop/ZNA_FINAL/zipcodes_raw.dta', preserve_dtypes=True)
df['ppt_id']=df['ppt_id'].astype('int')
df.rename(columns={'ppt_id': 'ID'}, inplace=True)

df_ref = pd.read_csv('/Users/PSYC-dap3463/Desktop/ZNA_FINAL/zip_code_database.csv',na_values="0")
df_ref['zip'] = df_ref['zip'].astype(str).str.zfill(5)

df['zip_corr'] = np.random.randn(len(df['ID']))
df['zip_type'] = np.random.randn(len(df['ID']))
df['PObox_mapping_dist'] = np.random.randn(len(df['ID']))

for ID in df['ID']:
    try:
        PObox_mapping_dist
    except NameError:
        pass
    else:
        del(PObox_mapping_dist)

    ZIPCODE=df[(df['ID'] == ID)].zip.values[0]
    if ZIPCODE == 'nan' or ZIPCODE == "":
        print("No zipcode provided...")
        continue

    search = ZipcodeSearchEngine()
    zipcode = search.by_zipcode(ZIPCODE)

    ##Get latitude and longitude
    lat_O = zipcode.Longitude
    long_O = zipcode.Latitude

    ##Extract ID index
    ID_index=df[(df['ID'] == ID)].index.values[0]

    zip_type = df_ref['type'][df_ref.loc[df_ref['zip'] == ZIPCODE].index[0]]
    print(str(ZIPCODE) + ' for ' + str(ID) + ' is ' + zip_type)
    #print(str(ZIPCODE) + ' for ' + str(ID) + ' is ' + zip_type)

    if zip_type == 'PO BOX':
        search = ZipcodeSearchEngine()
        zipcode = search.by_zipcode(ZIPCODE)
        if zipcode.LandArea <= 5:
            max_rad=20
        else:
            max_rad=40

        zcdb = ZipCodeDatabase()
        for j in range(1,max_rad):
          surr_zips = [x.encode('ascii') for x in [z.zip for z in zcdb.get_zipcodes_around_radius(ZIPCODE, j)]]
          if ZIPCODE in surr_zips:
              surr_zips.remove(ZIPCODE)
          if len(surr_zips) > 20:
              break

        cand_df = df_ref[df_ref['zip'].isin(surr_zips)]['zip'].values.tolist()

        first_pass=[]
        for i in cand_df:
            zip_type_2 = df_ref['type'][df_ref.loc[df_ref['zip'] == i].index[0]]
            if zip_type_2 == 'PO BOX':
                print(str(i) + ' is also a PO Box. Still checking...')
                continue
            else:
                search = ZipcodeSearchEngine()
                zipcode = search.by_zipcode(i)
                if zipcode.Population is None:
                    print('Missing population stats for ' + str(i) + '. Still checking...')
                    continue
                else:
                    if zipcode.Wealthy is None:
                        print('Missing Annual Income stats for ' + str(i) + '. Still checking...')
                        continue
                    else:
                        first_pass.append(i)

        candidates=[]
        for i in first_pass:
            search = ZipcodeSearchEngine()
            zipcode = search.by_zipcode(i)
            print('Estimating vincenty distance for ' + str(i) + '...')
            lat_M = zipcode.Latitude
            long_M = zipcode.Longitude
            ZIP_ORIG = (lat_O, long_O)
            ZIP_MAPPED = (lat_M, long_M)
            a=vincenty(ZIP_ORIG, ZIP_MAPPED).miles
            candidates.append(a)

        ix_smallest_dist=candidates.index(min(candidates))
        ZIPCODE=first_pass[ix_smallest_dist]
        PObox_mapping_dist=candidates[ix_smallest_dist]
        print('Using surrogate residential zipcode ' + str(ZIPCODE) + ' within ' + str(j) + ' mile radius...\n')
        print('Distance is: ' + str(PObox_mapping_dist) + '\n')
    #search = ZipcodeSearchEngine()
    #zipcode = search.by_zipcode(ZIPCODE)
    #if zipcode.Longitude > -70 or zipcode.Longitude is None:
        #print("WARNING! Unrealistic Latitude/Longitude found for this zipcode...")
        #continue
    zip_corr_ix=df[(df['ID'] == ID)].columns.get_loc('zip_corr')
    df.ix[ID_index,zip_corr_ix]=ZIPCODE

    zip_type_ix=df[(df['ID'] == ID)].columns.get_loc('zip_type')
    df.ix[ID_index,zip_type_ix]=zip_type

    try:
        PObox_mapping_dist
    except NameError:
        PObox_mapping_dist=0

    PObox_mapping_dist_ix=df[(df['ID'] == ID)].columns.get_loc('PObox_mapping_dist')
    df.ix[ID_index,PObox_mapping_dist_ix]=PObox_mapping_dist
##########################################################
##CENSUS STATISTICS##
##########################################################
if USCENSUS == 1:
    df['Zipcode_land_area'] = np.random.randn(len(df['ID']))
    df['Zipcode_pop_density'] = np.random.randn(len(df['ID']))
    df['Zipcode_pop_total'] = np.random.randn(len(df['ID']))
    df['Zipcode_avg_ann_income'] = np.random.randn(len(df['ID']))
    df['Zipcode_Longitude'] = np.random.randn(len(df['ID']))
    df['Zipcode_Latitude'] = np.random.randn(len(df['ID']))
    missing_data=[]

    for ID in df['ID']:
        ZIPCODE=df[(df['ID'] == ID)].zip_corr.values[0]
        if ZIPCODE == 'nan' or ZIPCODE == "":
            continue

        ##Extract ID index
        ID_index=df[(df['ID'] == ID)].index.values[0]

        search = ZipcodeSearchEngine()
        zipcode = search.by_zipcode(ZIPCODE)

        print(str(ZIPCODE))

        ##Extract total population
        pop_population_total=zipcode.Population
        print('Total population is: ' + str(pop_population_total))
        pop_total_ix = df[(df['ID'] == ID)].columns.get_loc('Zipcode_pop_total')
        df.ix[ID_index,pop_total_ix]=pop_population_total

        ##Extract Land Area
        land_area=zipcode.LandArea
        print('Land Area is: ' + str(land_area))
        land_area_ix = df[(df['ID'] == ID)].columns.get_loc('Zipcode_land_area')
        df.ix[ID_index,land_area_ix]=land_area

        ##Extract population density
        pop_density=zipcode.Density
        print('Population density is: ' + str(pop_density))
        pop_density_ix = df[(df['ID'] == ID)].columns.get_loc('Zipcode_pop_density')
        df.ix[ID_index,pop_density_ix]=pop_density

        ##Extract total annual income
        pop_avg_ann_income=zipcode.Wealthy
        print('Average Annual Income is: ' + str(pop_avg_ann_income))
        avg_ann_income_at_zipcode_ix=df[(df['ID'] == ID)].columns.get_loc('Zipcode_avg_ann_income')
        df.ix[ID_index,avg_ann_income_at_zipcode_ix]=pop_avg_ann_income

        ##Extract Longitude
        longitude=zipcode.Longitude
        print('Longitude is: ' + str(longitude))
        Zipcode_Longitude_ix=df[(df['ID'] == ID)].columns.get_loc('Zipcode_Longitude')
        df.ix[ID_index,Zipcode_Longitude_ix]=longitude

        ##Extract Longitude
        latitude=zipcode.Latitude
        print('Longitude is: ' + str(latitude))
        Zipcode_Latitude_ix=df[(df['ID'] == ID)].columns.get_loc('Zipcode_Latitude')
        df.ix[ID_index,Zipcode_Latitude_ix]=latitude

        print("\n")

############################################################
##PULL ACCESS TO MENTAL HEALTHCARE VIA PSYCHOLOGYTODAY
if PSYCHTODAY == 1:
    print("\n\nScraping psychologytoday for access to mental healthcare metrics...\n\n")
    df['Zipcode_Mental_Healthcare_Profs'] = np.random.randn(len(df['ID']))
    #####OPTIONS#####
    dist=15
    #################

    for ID in df['ID']:
        ZIPCODE=df[(df['ID'] == ID)].zip_corr.values[0]
        if ZIPCODE == 'nan' or ZIPCODE == "":
            continue
        ##Extract ID index
        ID_index=df[(df['ID'] == ID)].index.values[0]

        ##Crawl psychologytoday html to get number of unique mphone numbers of mental healthcare professionals in a search by zipcode
        #psychtoday_url=str('https://therapists.psychologytoday.com/rms/zip/' + str(ZIPCODE) + '.html')
        psychtoday_url=str('https://therapists.psychologytoday.com/rms/prof_results.php?sid=1474246095.6256_25374&zipcode=' + str(ZIPCODE) + '&zipdist=' + str(dist) + '&spec=2')
        time.sleep(2)
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        response = opener.open(psychtoday_url)
        html_contents = response.read()
        soup = BeautifulSoup(html_contents, "lxml")

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
            num_mental_health_profs_ix=df[(df['ID'] == ID)].columns.get_loc('Zipcode_Mental_Healthcare_Profs')
            df.ix[ID_index,num_mental_health_profs_ix]=num_mental_health_facilities
            print('\n\n')
            continue
        else:
            print('Multiple pages of output. Parsing...')

        ##Start counter
        count=0

        for i in z:
            time.sleep(1)
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
        value_ix=df[(df['ID'] == ID)].columns.get_loc('Zipcode_Mental_Healthcare_Profs')
        df.ix[ID_index,value_ix]=count
        print('\n\n')

##############################
##Moving.com metrics
##############################
if MOVING == 1:
    print("\n\nScraping moving.com for multiple metrics...\n\n")
    df_list=pd.read_csv('/Users/PSYC-dap3463/Desktop/ZNA_FINAL/zipcode_factor_list.csv',na_values="0")
    url_before_zip='http://www.moving.com/real-estate/city-profile/results.asp?Zip='

    for i in df_list['Title']:
        factor=df_list[(df_list['Title'] == i)].Factor.values[0]
        title=str(i)
        Run=df_list[(df_list['Title'] == i)].Collect.values[0]
        if Run == 2:
            continue
        print('Scraping for ' + str(i) + '...')
        df[factor] = np.random.randn(len(df['ID']))

        for ID in df['ID']:
          ZIPCODE=df[(df['ID'] == ID)].zip_corr.values[0]
          if ZIPCODE == 'nan' or ZIPCODE == "":
              continue
          ##Extract ID index
          ID_index=df[(df['ID'] == ID)].index.values[0]
          try:
              ##Crawl
              ##Clear cache
              urllib3.getproxies = lambda x = None: {}
              url=str(url_before_zip + str(ZIPCODE))
              time.sleep(1)
              http = urllib3.PoolManager()
              response = http.request('GET', url)
              html_contents = response.data

              ##Get line in html
              str_hint='title="' + title + '"'
              LINES=html_contents.splitlines()
              #del matching_lines
              for index, line in enumerate(LINES):
                  if str_hint in line:
                      matching_lines=line
                      if 'this.href, this.target, 300,\'sb\'' in matching_lines:
                          matching_lines=LINES[index+1]

              ##get str_pat_after_val
              str_pat_after_val=str(matching_lines.rsplit(str_hint)).strip('[""]')[1:5]
              regex = re.compile(str_pat_after_val)
              match_str_after=regex.findall(matching_lines)
              spliced_after=matching_lines.split(match_str_after[0], 1)[1]
              value=re.findall(r'\d+[\,\.]?\d*', spliced_after)[-1]
              print(factor + ' at zip: ' + str(ZIPCODE) + ' for subject ' + str(ID) + ' is ' + str(value))
              value_ix=df[(df['ID'] == ID)].columns.get_loc(factor)
              df.ix[ID_index,value_ix]=value
              print('\n\n')
          except:
              value=""
              continue

##Run variance, correlation, missingness checks
##Remove any duplicate columns
if (dups_cols == 1):
    dup_cols_list=df.columns.tolist()
    dups = [x for x in dup_cols_list if dup_cols_list.count(x) > 1]
    for i in dups:
	print('Removing redudant variable ' + str(i) + ' from dataframe...')
    df=df.drop_duplicates()
    print("\n")

###########################Data Integrity Check####################################
dups_rows = 0 #check for and remove duplicate rows/ID's (1=ON, 0=OFF)
dups_cols = 0 #check for and remove duplicate cols/variables (1=ON, 0=OFF)
check_var = 1 #check for and remove variables with low variance (1=ON, 0=OFF)
check_missingness = 1 #check for and remove variables with missing data according to missing_thresh (1=ON, 0=OFF)
check_cors = 1 #check for and remove variables with high correlation according to cor_strength (1=ON, 0=OFF)
var_threshold = 0.1 #variance threshold for rejecting variables
missing_thresh = 0.1 #missingness threshold for percentage of NA's detected to reject variable
cor_strength = 0.95 #correlation strength threshold to reject variables on the basis of high collinearity
###################################################################################

##Run variance check
print('\n')
if (check_var == 1):
    ##Remove variables with low variance
    for i in range(0,len(df.std()[df.std() < var_threshold].index[:])):
        print('Removing ' + str(df.std()[df.std() < var_threshold].index[i].encode('ascii')) +' for low variance ...')

    df.drop(df.std()[df.std() < var_threshold].index.values, axis=1, inplace=True)

##Return column names for those variables that have too many NAs
if (check_missingness == 1):
    nas_list=[]
    missing_thresh_perc=100*(missing_thresh)
    for column in df:
        if (column == 'Ann_income_weighted_by_avg_at_zip'):
            continue
        if (column == 'income'):
            continue
        thresh=(df[column].isnull().sum())/len(df)
        if thresh > missing_thresh:
            nas_list.append(df[column].name.encode('ascii'))
            print('Removing ' + str(df[column].name.encode('ascii')) + ' due to ' + str(round(100*(df[column].isnull().sum())/len(df),1)) + '% missing data...')

##Remove variables that have too many NAs
if (check_missingness == 1):
    for i in range(len(nas_list)):

        ##Delete those variables with high correlations
        df.drop(nas_list[i], axis=1, inplace=True)

##Return names of correlated variables
if (check_cors == 1):
    cor=df.corr(method='pearson')
    cor.loc[:,:]= np.tril(cor, k=-1)
    cor=cor.stack()
    high_cor=cor[cor > cor_strength]
    cors=high_cor.index.unique()
    corvars=[[s.encode('ascii') for s in list] for list in cors]

##If significantly correlated variables detected, identify the unique set and remove them
if (check_cors == 1):
    if len(corvars) !=0:

        ##Clean up string formatting of correlated variables
        corvars_bad=ast.literal_eval(str(corvars).replace('[','').replace(']',''))

        ##Remove duplicate strings in list
        unique=[];
        [unique.append(item) for item in corvars_bad if item not in unique];
        corvars_bad=unique;

        ##Remove each correlated variable
        for i in range(len(corvars_bad)):
          df.drop(corvars_bad[i], axis=1, inplace=True)
          print('Removing ' + str(corvars_bad[i]) + ' due to correlation...')
          print("\n")

##csv
df.to_csv('/Users/PSYC-dap3463/Desktop/ZNA_FINAL/ZIPCODES_SCRAPE_ALL.csv')
####Save df as .Rdata dataframe using rpy2.
##r_dataframe = pandas2ri.py2ri(df)
##r.assign("ZIP_R", r_dataframe)
##r("df_2 <- ZIP_R[,-which(sapply(ZIP_R, class) == 'factor')]")
##r("df <- as.data.frame( df_2[,4:num_cols], drop=false)")
##r("save(df, file='/Users/PSYC-dap3463/Desktop/ZNA_FINAL/ZIPCODES_SCRAPE_ALL.Rdata')")
#r("df_1 <- as.data.frame( ZIP_R[,1:2], drop=false)")
#r("df_2 <- ZIP_R[,-which(sapply(ZIP_R, class) == 'factor')]")
#r("num_cols <- NCOL(df_2)")
#r("df_2 <- as.data.frame( df_2[,4:num_cols], drop=false)")
#r("library(dplyr);join(df_1, df_2, type = 'right')")
