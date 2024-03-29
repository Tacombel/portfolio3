# python3

# para que descargue pasar como argumento el activo_id
# este modulo no actualiza la base de datos, solo descarga

import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from lxml import html
import sys
import datetime
import requests
from requests.exceptions import ConnectionError
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError
import json
import os
from config import Config
from time import sleep

path = 'data/app.db'
scriptdir = os.path.dirname(__file__)
db_path = Config.DB_PATH

SECRET_KEY = os.environ.get('AM_I_IN_A_DOCKER_CONTAINER', False)

def descargar_pagina(url):
    # This section is here to get the response code, as Selenium does not provide it.
    session = requests.Session()
    try:
        response = session.get(url, timeout=30)
        print(f'Response: {response.status_code}')
    except ConnectionError as error:
        print('Error getting response: ', error)
        return None
    ##

    options = webdriver.FirefoxOptions()
    options.add_argument('headless')
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    try:
        # This is to be able to test the script without building the container. Run the stack portfolio3_sin_nginx.
        if SECRET_KEY:
            with webdriver.Remote(
                command_executor='http://selenium-firefox:4444/wd/hub',
                options=options) as driver:
                driver.get(url)
                tree = html.fromstring(driver.page_source)
                return tree, response.status_code
        else:
            print('Usando selenium fuera de la red de Nginx. Lanza el contenedor selenium-firefox')
            with webdriver.Remote(
                command_executor='http://localhost:4444/wd/hub',
                options=options) as driver:
                driver.get(url)
                tree = html.fromstring(driver.page_source)
                return tree, response.status_code
    except TimeoutException as error:
        print('Timeout: ', error)
        return None, response.status_code
    except WebDriverException as error:
        print('Webdriver: ', error)
        return None, response.status_code

def variantes(e, tree):
    VL_old = False
    # www.morningstar.es
    if e == 0:
        date_xpath = '//*[@id="overviewQuickstatsDiv"]/table/tbody/tr[2]/td[1]/span/text()'
        vl_xpath = '//*[@id="overviewQuickstatsDiv"]/table/tbody/tr[2]/td[3]/text()'
        date = tree.xpath(date_xpath)
        VL = tree.xpath(vl_xpath)
        if len(date) == 0 or len(VL) == 0:
            data = ['No data']
            return data
        date, VL = date[0], VL[0]
        day = int(date[0:2])
        month = int(date[3:5])
        year = int(date[6:])
        date = datetime.date(year, month, day)
        VL = VL[4:]
        VL = VL.replace(",", ".")

    # es.investing.com tipo II
    if e == 6:
        date_xpath =     '/html/body/div[1]/div/div/div/div[2]/main/div/div[4]/div/div[1]/div/div[3]/div/table/tbody/tr[1]/td[1]/time/text()'
        vl_xpath =       '/html/body/div[1]/div/div/div/div[2]/main/div/div[4]/div/div[1]/div/div[3]/div/table/tbody/tr[1]/td[2]/text()'
        date_xpath_old = '/html/body/div[1]/div/div/div/div[2]/main/div/div[4]/div/div[1]/div/div[3]/div/table/tbody/tr[2]/td[1]/time/text()'
        vl_xpath_old =   '/html/body/div[1]/div/div/div/div[2]/main/div/div[4]/div/div[1]/div/div[3]/div/table/tbody/tr[2]/td[2]/text()'
        try:
            n = 1
            date = tree.xpath(date_xpath)
            VL = tree.xpath(vl_xpath)
            date_old = tree.xpath(date_xpath_old)
            VL_old = tree.xpath(vl_xpath_old)
            date, VL, date_old, VL_old = date[0], VL[0], date_old[0], VL_old[0]
            day = int(date[0:2])
            month = int(date[3:5])
            year = int(date[6:])
            date = datetime.date(year, month, day)
            VL = VL.replace(",", ".")
            day_old = int(date_old[0:2])
            month_old = int(date_old[3:5])
            year_old = int(date_old[6:])
            date_old = datetime.date(year_old, month_old, day_old)
            VL_old = VL_old.replace(",", ".")
        except AttributeError as e:
            print(f'AtributeError: {e}', flush=True)
            data = ['No data']
            return data
        except IndexError as e:
            print(f'IndexError: {e}', flush=True)
            data = ['No data']
            return data
        
# es.investing.com tipo I
    if e == 1:
        date_xpath = '//*[@id="curr_table"]/tbody/tr[1]/td[1]/text()'
        vl_xpath = '//*[@id="curr_table"]/tbody/tr[1]/td[2]/text()'
        date_xpath_old = '//*[@id="curr_table"]/tbody/tr[2]/td[1]/text()'
        vl_xpath_old = '//*[@id="curr_table"]/tbody/tr[2]/td[2]/text()'
        try:
            n = 1
            date = tree.xpath(date_xpath)
            VL = tree.xpath(vl_xpath)
            date_old = tree.xpath(date_xpath_old)
            VL_old = tree.xpath(vl_xpath_old)
            date, VL, date_old, VL_old = date[0], VL[0], date_old[0], VL_old[0]
            day = int(date[0:2])
            month = int(date[3:5])
            year = int(date[6:])
            date = datetime.date(year, month, day)
            VL = VL.replace(",", ".")
            day_old = int(date_old[0:2])
            month_old = int(date_old[3:5])
            year_old = int(date_old[6:])
            date_old = datetime.date(year_old, month_old, day_old)
            VL_old = VL_old.replace(",", ".")
        except AttributeError as e:
            print(f'AtributeError: {e}', flush=True)
            data = ['No data']
            return data
        except IndexError as e:
            print(f'IndexError: {e}', flush=True)
            data = ['No data']
            return data



    # portal4.lacaixa.es
    # No funciona y no esta probado con los últimos cambios
    if e == 2:
        date_xpath = '//*[@id="tabla_datos_generales"]/tbody/tr[4]/th/text()'
        vl_xpath = '//*[@id="tabla_datos_generales"]/tbody/tr[4]/td/text()'
        date = tree.xpath(date_xpath)
        VL = tree.xpath(vl_xpath)
        date, VL = date[0], VL[0]
        if len(date) == 0 or len(VL) == 0:
            data = ['No data']
            return data
        date = date[42:52]
        day = int(date[0:2])
        month = int(date[3:5])
        year = int(date[6:])
        date = datetime.date(year, month, day)
        VL = VL.split()[0]
        VL = VL.replace(",", ".")

    # www.quefondos.com
    if e == 3:
        date_xpath = '//*[@id="col3_content"]/div/div[4]/p[3]/span[2]/text()'
        vl_xpath = '//*[@id="col3_content"]/div/div[4]/p[1]/span[2]/text()'
        date = tree.xpath(date_xpath)
        VL = tree.xpath(vl_xpath)
        if len(date) == 0 or len(VL) == 0:
            data = ['No data']
            return data
        date, VL = date[0], VL[0]
        day = int(date[0:2])
        month = int(date[3:5])
        year = int(date[6:])
        date = datetime.date(year, month, day)
        VL = VL.split()[0]
        VL = VL.replace(",", ".")
    # www.bolsademadrid.es
    if e == 4:
        date_xpath = '//*[@id="ctl00_Contenido_tblPrecios"]/tbody/tr[2]/td[1]/text()'
        vl_xpath = '//*[@id="ctl00_Contenido_tblPrecios"]/tbody/tr[2]/td[6]/text()'
        date_xpath_old = '//*[@id="ctl00_Contenido_tblPrecios"]/tbody/tr[3]/td[1]/text()'
        vl_xpath_old = '//*[@id="ctl00_Contenido_tblPrecios"]/tbody/tr[3]/td[6]/text()'
        date = tree.xpath(date_xpath)
        VL = tree.xpath(vl_xpath)
        date_old = tree.xpath(date_xpath_old)
        VL_old = tree.xpath(vl_xpath_old)
        if len(date) == 0 or len(VL) == 0 or len(date_old) == 0 or len(VL_old) == 0 or VL[0] == '-' or VL_old[0] == '-':
            data = ['No data']
            return data
        date, VL, date_old, VL_old = date[0], VL[0], date_old[0], VL_old[0]
        day = int(date[0:2])
        month = int(date[3:5])
        year = int(date[6:])
        date = datetime.date(year, month, day)
        VL = VL.replace(",", ".")
        day_old = int(date_old[0:2])
        month_old = int(date_old[3:5])
        year_old = int(date_old[6:])
        date_old = datetime.date(year_old, month_old, day_old)
        VL_old = VL_old.replace(",", ".")

    if not VL_old:
        data = [date, VL]
    else:
        data = [date, VL, date_old, VL_old]

    return data

def variantes_API(e):
    if e == 5:
        # descargamos el precio del SCP en dolares desde Coinbase
        # la url falla así que he tenido que moverme a coingecko
        # url = 'https://api.coinbase.com/v2/exchange-rates?currency=SCP'
        # Este endpoint tambien sirve y es mucho mas simple https://api.coingecko.com/api/v3/simple/price?ids=siaprime-coin&vs_currencies=usd
        url = 'https://api.coingecko.com/api/v3/coins/siaprime-coin'
        req = Request(url)
        try:
            response = urlopen(req)
        except URLError as e:
            if hasattr(e, 'reason'):
                print('We failed to reach a server.', flush=True)
                print('Reason: ', e.reason, flush=True)
            elif hasattr(e, 'code'):
                print('The server couldn\'t fulfill the request.', flush=True)
                print('Error code: ', e.code, flush=True)
            return ['No data']
        data = json.loads(response.read())
        # Estos loggins son los de Coinbase, que no funciona
        # logging.info(f"$/SCP: {data['data']['rates']['USD']}")
        # logging.info(f"EUR/SCP: {data['data']['rates']['EUR']}")
        logging.info(f"$/SCP: {data['market_data']['current_price']['usd']}")
        now = datetime.datetime.now()
        return [datetime.date(now.year, now.month, now.day), data['market_data']['current_price']['usd'], 200, 39]


def scrape(activo_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM activo WHERE id =?", (str(activo_id),))
    e = c.fetchone()
    if len(e[4]) == 0:
        data = ['Error', 'No hay url', activo_id]
        logging.info('%s %s %s', str(data[0]), str(data[1]), str(data[2]))
        return data
    if e[4] == 'API':
        print(f'{datetime.datetime.now()}')
        print(f'> Scraping activo: {activo_id}', flush=True)
        return variantes_API(e[3])
    else:
        print(f'{datetime.datetime.now()}')
        print('> Scraping activo: ', activo_id, e[4], flush=True)
        tree, status_code = descargar_pagina(e[4])
        logging.info('Status code: %s', str(status_code))
        if status_code == 404:
            data = ['Error', 'La página no existe. Status_code: 404', activo_id]
            logging.info('%s %s %s', str(data[0]), str(data[1]), str(data[2]))
            return data
        data = variantes(e[3], tree)

        # Para detectar que esta descargando
        # logging.info('Activo: %s Data: %s', str(e[3]), str(data))
        print('Activo: ', activo_id, 'Tipo: ', e[3], 'Data: ', data, flush=True)

        if len(data) > 1:
            if '-' in data[1]:
                data = ['Error', 'VL es un -. Status_code:' + str(status_code), activo_id]
                logging.info('%s %s %s', str(data[0]), str(data[1]), str(data[2]))
                return data
        if len(data) == 4:
            logging.info('%s %s %s %s', str(data[0]), str(data[1]), str(data[2]), str(data[3]))
        elif len(data) == 2:
            logging.info('%s %s', str(data[0]), str(data[1]))
        elif len(data) == 1:
            logging.info('%s', data[0])

        if data:
            data.append(status_code)
            data.append(activo_id)
        else:
            data = ['Error', 'data no se ha creado. Status_code: ' + status_code, activo_id]
            logging.info('%s %s %s', str(data[0]), str(data[1]), str(data[2]))
        return data

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for index, e in enumerate(sys.argv):
        if index == 0:
            continue
        print(f'Esto es lo que enviamos: {scrape(e)}')
