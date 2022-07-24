# python3

import sqlite3
import time
from scrape_one import scrape
import os
from config import Config

path = 'data/app.db'
scriptdir = os.path.dirname(__file__)
db_path = Config.DB_PATH


def look_for_data():
    print('****************************************************************', flush=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Se descargan los activos que tienen un tipo >=0
    candidates = []
    # for row in c.execute("SELECT * FROM activo WHERE descargar =?", '1'):
    for row in c.execute("SELECT * FROM activo WHERE tipo >=?", '0'):
        # 0: Id, 3:tipo, 4:url
        candidates.append(row[0])
    
    hora_de_inicio = time.time()
    if len(candidates) == 1:
        print('Scrapeando ', len(candidates), 'valor.', flush=True)
    else:
        print('Scrapeando ', len(candidates), 'valores.', flush=True)
    for candidate in candidates:
        data = scrape(candidate)
        if len(data) == 6:
            c.execute("INSERT OR REPLACE INTO cotizacion (fecha, VL, activo_id) VALUES (?, ?, ?)",
                        (data[2], data[3], data[-1],))
            conn.commit()
        if len(data) >= 4:
            c.execute("INSERT OR REPLACE INTO cotizacion (fecha, VL, activo_id) VALUES (?, ?, ?)",
                        (data[0], data[1], data[-1],))
            conn.commit()
    duracion = (time.time() - hora_de_inicio) / 60
    if duracion < 1:
        duracion = duracion * 60
        print('Duración de la descarga: ', '{:.2f}'.format(duracion), 'segundos', flush=True)
    else:
        print('Duración de la descarga: ', '{:.2f}'.format(duracion), 'minutos', flush=True)

    current_time = time.time()
    c.execute("INSERT OR REPLACE INTO variables (name, value) VALUES (?,?)", ("last_scrape", current_time))
    conn.commit()
    print('Scrape finished', flush=True)


if __name__ == "__main__":
    look_for_data()