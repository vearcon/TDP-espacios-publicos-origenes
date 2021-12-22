#!/usr/bin/python3
'''
Sacando data del link 46
Sacando data del link 47
Guardando...
Traceback (most recent call last):
  File "Desktop/scrap_meli.py", line 221, in <module>
    scrap(url, filepath)
  File "Desktop/scrap_meli.py", line 198, in scrap
    save_data( data, filename ) #un csv vacío da siz
  File "Desktop/scrap_meli.py", line 164, in save_data
    existing_file = name in os.listdir(dirpath)
NameError: name 'name' is not defined

'''


import os, sys
import time
from numpy.random import random

import re
import csv
import json
import requests
from bs4 import BeautifulSoup as bs

#####
#       UTILS
#####

def parse_url( url:str ):
    '''
    Dado un url devuelve objeto parseado de BeautifulSoup
    '''
    try:
        response = requests.get( url )
    except:
        print('***Error en conexión a', url)
        return None
        
    if response.status_code != 200:
        print('***Status code',response.status_code,'\tError en request', url)
        return None
    
    return bs( response.content, features="lxml" )



def get_links(url_search:str) -> list:
    '''
    Devuelve lista con todos los links a publicaciones de alquileres, dada una
    url de búsqueda con el formato que especifica numero de página
    '''
    urls = []

    soup = parse_url( url_search )
    if not soup: return
    
    tags = soup.find_all( name='a', 
                          attrs={'class':'ui-search-result__content ui-search-link'} )

    urls += [ t['href'] for t in tags ]

#    print(f'Se extrajeron {len(urls)} links')
    return urls



def find_pub_date(url: str):
    '''
    Dado el URL de una publicación activa de MeLi, devuelve la fecha de publicación utilizando la API.
    '''  
    URL_API = 'https://api.mercadolibre.com/items/'
    PATTERN = "MLA-\d+"
    pub_id = re.findall( re.compile( PATTERN ), url )[0]
    pub_id = pub_id.replace('-','')

    try:
        response = requests.get( URL_API + pub_id )
    except:
        print('Conexión a API malió sal, reintentando...')
        return None
    
    pub_json = response.json()
    date = pub_json['start_time']
    return date



def get_data(urls:list) -> list:
    '''
    Devuelve lista de diccionarion con datos del precio, superficie, ubicación...
    Dada una lista de links con publicaciones de inmuebles de mercadolibre,
    '''
    data_list = []
 
    for i,url in enumerate(urls):

        response = requests.get(url)
        
        soup = parse_url( url )
        if not soup:    continue

        pub_finalizada = soup.find(name='div', attrs={'class':'ui-pdp-container__row ui-pdp-container__row--item-status-message'})
        if pub_finalizada:  
            print('Link',i, ' Publicación Finalizada', url)
            continue        
##### EMPIEZA LA EXTRACCIÓN DE DATOS #####
        d_data = {}
####### Estos los saco de scrapear el html de la publicación                
######### ALGUNOS DATOS
        to_extract = {'sp_tot':     'Superficie total', 
                      'sp_cub':     'Superficie cubierta', 
                      'nu_ambs':    'Ambientes', 
                      'nu_dorms':   'Dormitorios', 
                      'pr_exp':     'Expensas'}
        tags_table = soup.find_all(name='tr',attrs={'class':'andes-table__row'})

        for key, title in to_extract.items():
            d_data[key] = None
            for tag in tags_table:
                text = tag.text
                if text.startswith(title):
                   value = text.replace(title,'').split()[0]
                   value = value.split('.')[0]
                   d_data[key] = int(value)
######### PRECIO
        tag_price = soup.find(name='span', attrs={'class':'price-tag-fraction'})
        d_data['pr_valor'] = int( tag_price.text.replace('.','') )

        tag_currency = soup.find(name='span',attrs={'class':'price-tag-symbol'})
        d_data['pr_moneda'] = tag_currency.text 

######### UBICACION
        tag_address = soup.find_all(name='p', 
                                    attrs={'class':'ui-pdp-color--BLACK ui-pdp-size--SMALL ui-pdp-family--REGULAR ui-pdp-media__title'})[-1]
        d_data['ub_calle'] = tag_address.text.replace(', Capital Federal, Capital Federal', '')
        
        tags_script = soup.find_all(name='script')
        pattern = re.compile( '"location":\{(.*?)\}' )
        locations = re.findall( pattern, tags_script[-1].text )
        locations = json.loads( '{'+locations[0]+'}' )           
        try:
            d_data['ub_lat'] = locations['latitude']
            d_data['ub_lon'] = locations['longitude']
        except:
            d_data['ub_lat'] = None
            d_data['ub_lon'] = None
            
######### FECHA PPUBLICACION --- Esto lo obtengo usando la API
        d_data['fe_pub'] = find_pub_date( url )      
        
######### URL
        d_data['url'] = url


        data_list.append(d_data)        
        time.sleep(random())
    return data_list
    


def save_data(dicts:list, filepath) -> None:

    dirpath = filepath[:filepath.rfind('/')]
    filename = filepath[filepath.rfind('/')+1:]

    existing_file = filename in os.listdir(dirpath)
    if existing_file:   
        mode='a'
    else:               
        mode='x' 
        print(f'No se encontró {filepath}, se creará a continuación.')
    
    with open(filepath, mode) as f:
        writer = csv.DictWriter(f, fieldnames=dicts[0].keys())

        if os.path.getsize(filepath)==0:
            writer.writeheader()
        
        for i, d in enumerate(dicts):
            writer.writerow( d )



#####
#       MAIN
#####

def scrap(url, filename, ni=0, nf=1000):

    for n in range(ni,nf):
        print(f'\tPágina {n}')
        url_page = url + str( n*48+1 )

        print(f'\t\tSacando links')
        links, last_page = get_links(url_page)
        
        if len(links)==0:
            print('Se alcanzó la última página.')
            break
        
        print(f'\t\tSacando data')  
        data = get_data(links)  #TARDA 6' POR PÁGINA!!!
        
        print(f'\t\tGuardando data')
        save_data( data, filename ) 


if __name__=='__main__':

    TODAY = time.strftime( "%Y-%m-%d", time.localtime() )
    DIRECTORY = sys.argv[1]

    URL_SEARCH_PHS  = 'https://inmuebles.mercadolibre.com.ar/ph/alquiler/capital-federal/_Desde_'
    URL_SEARCH_CASAS = 'https://inmuebles.mercadolibre.com.ar/casas/alquiler/capital-federal/_Desde_'
    URL_SEARCH_DEPTOS = 'https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/_Desde_'
    
   
    search = {'phs': URL_SEARCH_PHS,
              'casas': URL_SEARCH_CASAS,
              'deptos': URL_SEARCH_DEPTOS }


    for tipo, url in search.items():
        filepath = DIRECTORY + '_'.join([TODAY,tipo,'meli.csv'])
        print(f'Escrapeando {tipo}.\tLos datos se guardarán en {filepath}')
        scrap(url, filepath)
        
    print('Todo OK :)')
