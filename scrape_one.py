# python3

# para que descargue pasar como argumento el activo_id
# este modulo no actualiza la base de datos, solo descarga

import sqlite3
from selenium import webdriver
from lxml import html
import sys
import datetime
import platform
import requests
import os
import logging


def descargar_pagina(url):
    cwd = os.getcwd()
    # chromedriver para intel y chromedriver_ARM para raspberry
    if platform.system() == 'Windows':
        path = cwd + '\chromedriver\chromedriver.exe'
    else:
        path = cwd + '/chromedriver/chromedriver_ARM'
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    # This option is necessary to avoid an error when running as a service
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(chrome_options=options, executable_path=path)
    session = requests.Session()
    response = session.get(url)
    driver.get(url)
    tree = html.fromstring(driver.page_source)
    driver.quit()
    return tree, response.status_code


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

    # es.investing.com
    if e == 1:
        date_xpath = '//*[@id="curr_table"]/tbody/tr[1]/td[1]/text()'
        vl_xpath = '//*[@id="curr_table"]/tbody/tr[1]/td[2]/text()'
        date_xpath_old = '//*[@id="curr_table"]/tbody/tr[2]/td[1]/text()'
        vl_xpath_old = '//*[@id="curr_table"]/tbody/tr[2]/td[2]/text()'
        date = tree.xpath(date_xpath)
        VL = tree.xpath(vl_xpath)
        date_old = tree.xpath(date_xpath_old)
        VL_old = tree.xpath(vl_xpath_old)
        if len(date) == 0 or len(VL) == 0 or len(date_old) == 0 or len(VL_old) == 0:
            data = ['No data']
            return data'
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


def scrape(activo_id):
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute("SELECT * FROM activo WHERE id =?", (str(activo_id),))
    e = c.fetchone()
    if len(e[4]) == 0:
        data = ['Error', 'No hay url', activo_id]
        logging.info('%s %s %s', str(data[0]), str(data[1]), str(data[2]))
        return data
    tree, status_code = descargar_pagina(e[4])
    logging.info("Scraping %s Id: %s", e[4], activo_id)
    logging.info('Status code: %s', str(status_code))
    if status_code == 404:
        data = ['Error', 'La página no existe. Status_code: 404', activo_id]
        logging.info('%s %s %s', str(data[0]), str(data[1]), str(data[2]))
        return data
    data = variantes(e[3], tree)

    if '-' in data[1]:
        data = ['Error', 'VL es un -. Status_code:' + status_code, activo_id]
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
        logging.info('-----------------------------------------------------------------')
        scrape(e)
