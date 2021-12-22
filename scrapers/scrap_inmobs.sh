#!/bin/bash

path/to/scraper1.py $1
path/to/scraper2.py $1
path/to/scraper3.py $1

# path/to/scraper.py son los scripts de python que scrapean las páginas web
# no necesitan tener el "python" delante porque: 1.la primera linea de cada script
# ya se lo indica a bash diciendo "#!/usr/bin/python3"; 2.Los scripts tienen permiso
# de ejecución, esto se otorga desde la teminal haciendo
# 	chmod +x path/to/script.py
# Lo mismo se aplica para este script de bash.

# $1 es el valor del primer parámetro con el que se ejecuta este escript de bash
# que acá indica el directorio donde queremos guardar los csv que cree/edite cada scraper.
# Entonces para ejecutar este script de bash hay que poner en la consola (en crontab en nuestro caso):
# 	scrap_inmobs.sh directory/where/to/save/all/raw/csvs/

# O si queremos guardar el csv de cada página en un directorio separado,
# este script de bash debería ser:
#	path/to/scraper1.py $1
#	path/to/scraper2.py $2
#	path/to/scraper3.py $3
# Y se ejecutaria en la consola como:
#	scrap_inmobs.sh directory/where/to/save/raw/csvs1 directory/where/to/save/raw/csvs2 directory/where/to/save/raw/csvs3
