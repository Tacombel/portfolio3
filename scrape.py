# python3

import sqlite3
import time
from scrape_one import scrape
import concurrent.futures


def look_for_data():
    print('****************************************************************', flush=True)
    conn = sqlite3.connect('app.db')
    c = conn.cursor()

    # Se descargan los activos que tienen un tipo >=0
    candidates = []
    # for row in c.execute("SELECT * FROM activo WHERE descargar =?", '1'):
    for row in c.execute("SELECT * FROM activo WHERE tipo >=?", '0'):
        # 0: Id, 3:tipo, 4:url
        candidates.append(row[0])

    n = 1

    # maxworkers=3 para la raspberry. No puede con mas
    # En otros equipos probar.

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        while True:
            hora_de_inicio = time.time()
            if len(candidates) == 1:
                print('Scrapeando ', len(candidates), 'valor. Intento número', n, flush=True)
            else:
                print('Scrapeando ', len(candidates), 'valores. Intento número', n, flush=True)
            wait_for = []
            for candidate in candidates:
                wait_for.append(executor.submit(scrape, candidate))
            for future in concurrent.futures.as_completed(wait_for):
                future = future.result()
                print(future, flush=True)
                if len(future) == 6:
                    c.execute("INSERT OR REPLACE INTO cotizacion (fecha, VL, activo_id) VALUES (?, ?, ?)",
                              (future[2], future[3], future[-1],))
                    conn.commit()
                if len(future) >= 4:
                    c.execute("INSERT OR REPLACE INTO cotizacion (fecha, VL, activo_id) VALUES (?, ?, ?)",
                              (future[0], future[1], future[-1],))
                    conn.commit()
                    candidates.remove(future[-1])
                if len(future) == 3:
                    candidates.remove(future[-1])
            duracion = (time.time() - hora_de_inicio) / 60
            if duracion < 1:
                duracion = duracion * 60
                print('Duración de la descarga: ', '{:.2f}'.format(duracion), 'segundos', flush=True)
            else:
                print('Duración de la descarga: ', '{:.2f}'.format(duracion), 'minutos', flush=True)

            if len(candidates) == 0:
                break
            n += 1
            if n < 4:
                print('---Los siguientes valores han dado error y se volvera a intentar: ', candidates, flush=True)
            else:
                print('Demasiados reintentos. Abortando', flush=True)
                break
            time.sleep(30)

    current_time = time.time()
    c.execute("INSERT OR REPLACE INTO variables (name, value) VALUES (?,?)", ("last_scrape", current_time))
    conn.commit()
    print('Scrape finished', flush=True)


if __name__ == "__main__":
    look_for_data()