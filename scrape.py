# python3

import sqlite3
import time
from scrape_one import scrape


def look_for_data():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    t = "1"
    candidates = []
    for row in c.execute("SELECT * FROM activo WHERE descargar =?", t):
        # 0: Id, 3:tipo, 4:url
        element = [row[0], row[3], row[4]]
        candidates.append(element)
    n = 0
    print('****************************************************************', flush=True)
    while len(candidates) > 0 and n < 4:
        print('Candidates pending:', len(candidates), flush=True)
        remove = []
        for index, e in enumerate(candidates):
            date_old = False
            if e[1] == 0 or e[1] == 2 or e[1] == 3:
                try:
                    date, VL = scrape(e[0])
                except ValueError as e:
                    print("Algo ha fallado:", e, flush=True)
                    continue
                if date == -1:
                    continue
            elif e[1] == 1 or e[1] == 4:
                try:
                    date, VL, date_old, VL_old = scrape(e[0])
                except ValueError as e:
                    print("Algo ha fallado:", e, flush=True)
                    continue
                if date == -1:
                    continue
            if date_old:
                c.execute("INSERT OR REPLACE INTO cotizacion (fecha, VL, activo_id) VALUES (?, ?, ?)", (date_old, VL_old, e[0],))
            c.execute("INSERT OR REPLACE INTO cotizacion (fecha, VL, activo_id) VALUES (?, ?, ?)", (date, VL, e[0],))

            remove.append(index)
        conn.commit()
        remove.sort(reverse=True)
        for e in remove:
            del candidates[e]
        if len(candidates) > 0:
            print('***********************************************', flush=True)
            print('The following candidates failed:', flush=True)
            for e in candidates:
                print(e[2], flush=True)
            n = n + 1
            if n > 3:
                print('Too many retries. Aborting', flush=True)
            else:
                time.sleep(60)
                print('Retry number', n, flush=True)

    current_time = time.time()
    c.execute("INSERT OR REPLACE INTO variables (name, value) VALUES (?,?)", ("last_scrape", current_time))
    conn.commit()
    print('Scrape finished', flush=True)


if __name__ == "__main__":
    look_for_data()
