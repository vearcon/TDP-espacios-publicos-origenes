#!/usr/bin/python3

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
    n_attempts=5
    for _ in range(n_attempts):    
        try:
            response = requests.get( url )
            
            if response.status_code != 200:
                print('***Error en request. Status code',response.status_code, url)
                continue
            
            return bs( response.content, features="lxml" )
            
        except:
            print('***Error en conexión a', url)
                    
    return None



def get_links(url_search:str) -> list:
    '''
    Devuelve lista con todos los links a publicaciones de alquileres, dada una
    url de búsqueda con el formato que especifica numero de página
    '''
    urls = []

    soup = parse_url( url_search )
    if not soup: 
        return []
    
    tags = soup.find_all( name='a', 
                          attrs={'class':'ui-search-result__content ui-search-link'} )

    urls += [ t['href'] for t in tags ]
  
#    print(f'Se extrajeron {len(urls)} links')
    return urls



def get_data(urls:list) -> list:
    '''
    Devuelve lista de diccionarion con datos del precio, superficie, ubicación...
    Dada una lista de links con publicaciones de inmuebles de mercadolibre,
    '''
    data_list = []
    URL_API = 'https://api.mercadolibre.com/items/'
    PATTERN = "MLA-\d+"

    for i,url in enumerate(urls):
        d_data = {}

        pub_id = re.findall( re.compile( PATTERN ), url )[0]
        pub_id = pub_id.replace('-','')
        try:
            response = requests.get( URL_API + pub_id )
        except:
            print('***Conexión a API malió sal, reintentando...')
            return None
            
        if response.status_code != 200:
            print('***Request malio sal', response.status_code, url)
        pub_json = response.json() 

        to_extract = {'sp_tot':     'attributes.Superficie total', 
                      'sp_cub':     'attributes.Superficie cubierta', 
                      'nu_ambs':    'attributes.Ambientes', 
                      'nu_dorms':   'attributes.Dormitorios', 
                      'pr_exp':     'attributes.Expensas',
                      'pr_valor':   'price',
                      'pr_moneda':  'currency_id',
                      'fe_pub':     'start_time',
                      'ub_calle':   'location.address_line'}


        for key, value in to_extract.items():
            
            d_data[key] = None          #Inicializo
            
            try:                
                if value.startswith('attributes'):
                    attrs_list = pub_json['attributes']
                    attr = value.split('.')[1]
                    for d in attrs_list:
                         if d['name'] == attr:
                            d_data[key] = d['value_name']
                
                elif value.startswith('location'):
                    d_data[key] = pub_json[value.split('.')[0]][value.split('.')[1]]
                
                else:
                    d_data[key] = pub_json[value]
                    
            except Exception as e:
                print('***No se encontró valor de: ', value, i, url)
                    
### find lat, lon
        response = requests.get(url)
        try:
            pattern = re.compile( '"location":\{(.*?)\}' )
            locations = re.findall( pattern, str(response.content))
            
            locations = json.loads( '{'+locations[0]+'}' )           
            
            d_data['ub_lat'] = locations['latitude']
            d_data['ub_lon'] = locations['longitude']
        except:
            d_data['ub_lat'] = None
            d_data['ub_lon'] = None
            print('***No se encontró lat/lon: ',i, url)
                
    
        d_data['url'] = re.split( '(.*MLA-\d*)', url)[1] # para no guardar el url entero que contiene una descripcion de la publicacion

        data_list.append(d_data)
        
#        print(i, d_data)

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
        url_page = url + str(n*48)

        print(f'\t\tSacando links')
        links = get_links(url_page)

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
        
    print('Todo OK :D')
