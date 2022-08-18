from flask import render_template, flash, redirect, url_for, request
from app import app, db, scheduler
from app.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from werkzeug.urls import url_parse
from app.email import send_password_reset_email
import sqlite3
import XIRR
import datetime
from scrape import look_for_data
from config import Config
import os

path = 'data/app.db'
scriptdir = os.path.dirname(__file__)
db_path = Config.DB_PATH

def add_asset_units(calculation_date):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT * FROM movimiento_activo WHERE fecha<=? ORDER BY fecha DESC', (calculation_date,))
    query = c.fetchall()
    units = {}
    for q in query:
        if q[4] in units:
            units[q[4]] = units[q[4]] + q[2]
        else:
            units[q[4]] = q[2]
    for key, value in units.items():
        if value < 0.000001:
            units[key] = 0
    return units


def assets_with_units(calculation_date):
    units = add_asset_units(calculation_date)
    delete = []
    for key, value in units.items():
        if value == 0:
            delete.append(key)
    for e in delete:
        del units[e]
    return units


def date_str_to_date(fecha):
    return datetime.date(int(fecha[0:4]), int(fecha[5:7]), int(fecha[8:]))


def date_to_eu_format(fecha):
    return date_str_to_date(fecha).strftime("%d-%m-%Y")


def to_euros(value, date, currency):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    if currency == 'GBP':
        c.execute('SELECT * FROM cotizacion WHERE activo_id=? and fecha<=?  ORDER BY fecha DESC LIMIT 1', (11, date))
        query = c.fetchone()
        value_currency = query[2]
        value = value / value_currency
    elif currency == 'USD':
        c.execute('SELECT * FROM cotizacion WHERE activo_id=?  and fecha<=? ORDER BY fecha DESC LIMIT 1', (10, date))
        query = c.fetchone()
        value_currency = query[2]
        value = value / value_currency
    else:
        value = value
    return value


def npv_calculation(calculation_date):
    # The if activo_id == 15 are for an special case
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    units = assets_with_units(calculation_date)
    NPV = 0
    response = []
    for key in units:
        profit = 0
        c.execute('SELECT * FROM activo WHERE id=?', (key,))
        query = c.fetchone()
        activo_id = query[0]
        name = query[2]
        number = units[key]
        currency = query[5]
        c.execute('SELECT * FROM cotizacion WHERE activo_id=? and fecha<=? ORDER BY fecha DESC LIMIT 1', (key, calculation_date))
        query = c.fetchone()
        # Si algún activo del período no tiene al menos un movimiento antes de esta da error. Hago que coja el anterior
        if not query:
            c.execute('SELECT * FROM cotizacion WHERE activo_id=? ORDER BY fecha ASC', (key,))
            query_bis = c.fetchall()
            date = query_bis[0][1]
            VL = query_bis[0][2]
        else:
            date = query[1]
            VL = query[2]
        # XIRR
        # Esta sección está para casos como los depositos, que no varian en numero de unidades
        if number == 1:
            if key == 15:
                c.execute('SELECT * FROM investment_movements WHERE fecha<=? and cuenta=?', (calculation_date, "CajaIngenieros"))
                query = c.fetchall()
                values = []
                dates = []
                for q in query:
                    values.append(q[2])
                    dates.append(date_str_to_date(q[1]))
                c.execute('SELECT * FROM cotizacion WHERE activo_id=? and fecha<=? ORDER BY fecha DESC LIMIT 1', (key, calculation_date))
                query = c.fetchone()
                values.append(query[2])
                dates.append(date_str_to_date(query[1]))
                try:
                    rate = "{0:.2f}".format(XIRR.xirr(values, dates) * 100) + "%"
                except: # noqa
                    rate = "XIRR error"
                for v in values:
                    profit = profit + v
            elif key == 37:
                c.execute('SELECT * FROM investment_movements WHERE fecha<=? and cuenta=?',
                          (calculation_date, "eToro"))
                query = c.fetchall()
                values = []
                dates = []
                for q in query:
                    values.append(q[2])
                    dates.append(date_str_to_date(q[1]))
                c.execute('SELECT * FROM cotizacion WHERE activo_id=? and fecha<=? ORDER BY fecha DESC LIMIT 1',
                          (key, calculation_date))
                query = c.fetchone()
                valor_final_en_euros = to_euros(query[2], calculation_date, 'USD')
                values.append(valor_final_en_euros)
                dates.append(date_str_to_date(query[1]))
                try:
                    rate = "{0:.2f}".format(XIRR.xirr(values, dates) * 100) + "%"
                except:  # noqa
                    rate = "XIRR error"
                for v in values:
                    profit = profit + v
            else:
                rate = ""
        else:
            c.execute('SELECT * FROM movimiento_activo WHERE activo_id=? and fecha<=? ', (key, calculation_date))
            query = c.fetchall()
            values = []
            dates = []
            for q in query:
                number_2 = q[2] * (-1)
                price = q[3]
                date_2 = q[1]
                v = number_2 * price
                profit = profit + to_euros(v, date_2, currency)
                values.append(v)
                dates.append(date_str_to_date(date_2))
            values.append(number * VL)
            dates.append(date_str_to_date(date))
            try:
                rate = "{0:.2f}".format(XIRR.xirr(values, dates) * 100) + "%"
            except: # noqa
                rate = "XIRR error"
        # END XIRR
        if currency == 'EUR':
            value = units[key] * VL
        elif currency == 'GBP':
            c.execute('SELECT * FROM cotizacion WHERE activo_id=? and fecha<=?  ORDER BY fecha DESC LIMIT 1', (11, calculation_date))
            query = c.fetchone()
            value_currency = query[2]
            value = units[key] * VL / value_currency
        elif currency == 'USD':
            c.execute('SELECT * FROM cotizacion WHERE activo_id=?  and fecha<=? ORDER BY fecha DESC LIMIT 1', (10, calculation_date))
            query = c.fetchone()
            value_currency = query[2]
            value = number * VL / value_currency
        if key in [15, 37]:
            profit = profit
        else:
            profit = profit + value
        NPV = NPV + value
        number = "{0:.2f}".format(number)
        VL = "{0:.2f}".format(VL)
        profit = "{0:.2f}".format(profit) + "€"
        if number == "1.00":
            number = ""
            VL = ""
            if activo_id in [15, 37]:
                profit = profit
            else:
                profit = ""
        value = "{0:.2f}".format(value) + "€"
        date = date_to_eu_format(date)
        response.append([name, number, date, VL, currency, value, rate, activo_id, profit])
    return response, NPV


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    if request.method == 'POST':
        look_for_data()
        scheduler.delete_job('job1')
        scheduler.add_job('job1', look_for_data, trigger='interval', seconds=Config.JOBS[0]['seconds'])

    response = []
    c.execute('SELECT * FROM activo WHERE descargar=? ORDER BY nombre', (1,))
    query = c.fetchall()
    for q in query:
        c.execute('SELECT * FROM cotizacion WHERE activo_id=? ORDER BY fecha DESC LIMIT 2', (q[0],))
        data = c.fetchall()
        if len(data) == 2:
            ticker = q[1]
            nombre = q[2]
            fechaultima = date_to_eu_format(data[0][1])
            VLultimo = data[0][2]
            VLanterior = data[1][2]
            variation = (VLultimo - VLanterior) / VLanterior * 100
            VLultimo = "{0:.4f}".format(VLultimo)
            VLanterior = "{0:.4f}".format(VLanterior)
            fechaanterior = date_to_eu_format(data[1][1])
            variation = "{0:.2f}".format(variation)
            activo_id = q[0]
        elif len(data) == 1:
            ticker = q[1]
            nombre = q[2]
            fechaultima = date_to_eu_format(data[0][1])
            VLultimo = data[0][2]
            VLanterior = ""
            variation = ""
            VLultimo = "{0:.4f}".format(VLultimo)
            fechaanterior = ""
            activo_id = q[0]
        response.append([ticker, nombre, fechaultima, VLultimo, fechaanterior, VLanterior, variation, activo_id])

    c.execute("SELECT * from variables WHERE name=?", ("last_scrape",))
    query = c.fetchone()
    if query is None:
        last_scrape = 0
    else:
        last_scrape = int(float(query[1]))
    next_run_time_epoch = scheduler.get_job('job1').next_run_time.timestamp()
    t_last = datetime.datetime.utcfromtimestamp(last_scrape)
    t_next = datetime.datetime.utcfromtimestamp(next_run_time_epoch)
    data = [t_last, t_next]

    return render_template('index.html', title='Home', table=response, data=data)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/assets')
@login_required
def assets():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    response = []
    c.execute('SELECT * FROM activo')
    query = c.fetchall()
    for q in query:
        lista = []
        lista.append(q[0])
        lista.append(q[2])
        response.append(lista)
    response = sorted(response, key=lambda asset: asset[1])
    return render_template('assets.html', title='Assets', query=response)


@app.route('/asset/<id>')
@login_required
def asset(id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT * FROM activo WHERE id=?', (id,))
    query = c.fetchone()
    # response
    response_0 = []
    for q in query:
        response_0.append(q)
    units = add_asset_units(datetime.date.today())
    try:
        units[int(id)]
    except KeyError:
        units[int(id)] = 0
    response_0.append(units[int(id)])
    # data_1
    c.execute('SELECT * FROM cotizacion WHERE activo_id=? ORDER BY fecha DESC LIMIT 5', (id,))
    data_1 = c.fetchall()
    response_1 = []
    for d in data_1:
        line = []
        line.append(date_to_eu_format(d[1]))
        line.append(d[2])
        response_1.append(line)

    # data_2
    c.execute('SELECT * FROM movimiento_activo WHERE activo_id=? ORDER BY fecha DESC LIMIT 5', (id,))
    data_2 = c.fetchall()
    response_2 = []
    for d in data_2:
        line = []
        line.append(date_to_eu_format(d[1]))
        line.append(d[2])
        line.append(d[3])
        response_2.append(line)

    return render_template('asset.html', title='Assets', query=response_0, data_1=response_1, data_2=response_2)


@app.route('/asset/VL/<id>', methods=['POST'])
@login_required
def asset_vl(id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    fecha = request.form.get('fecha')
    VL = request.form.get('VL')
    c.execute("INSERT OR REPLACE INTO cotizacion (fecha, VL, activo_id) VALUES (?, ?, ?)", (fecha, VL, id,))
    conn.commit()
    return redirect(url_for('asset', id=id))


@app.route('/asset/movement/<id>', methods=['POST'])
@login_required
def asset_movement(id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    fecha = request.form.get('fecha')
    unidades = request.form.get('unidades')
    precio = request.form.get('precio')
    c.execute("INSERT OR REPLACE INTO movimiento_activo (fecha, unidades, precio, activo_id, user_id) VALUES (?, ?, ?, ?, ?)", (fecha, unidades, precio, id, 1,))
    conn.commit()
    return redirect(url_for('asset', id=id))


@app.route('/npv', methods=['GET', 'POST'])
@login_required
def npv():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    data = []
    if request.form.get('first_date'):
        first_date = date_str_to_date(request.form.get('first_date'))
    else:
        first_date = datetime.date(2016, 12, 31)
    if request.form.get('last_date'):
        last_date = date_str_to_date(request.form.get('last_date'))
    else:
        last_date = datetime.date.today()
    last_response, last_NPV = npv_calculation(last_date)
    response = sorted(last_response, key=lambda asset: asset[0])
    first_response, first_NPV = npv_calculation(first_date)
    difference = last_NPV - first_NPV
    data.append("{0:.2f}".format(last_NPV) + "€")
    data.append("{0:.2f}".format(first_NPV) + "€")
    data.append(first_date.strftime("%d-%m-%Y"))
    data.append(last_date.strftime("%d-%m-%Y"))
    data.append("{0:.2f}".format(difference) + "€")
    # XIRR
    c.execute('SELECT * FROM investment_movements WHERE fecha>=? and fecha<=? ', (first_date, last_date))
    query = c.fetchall()
    values = []
    dates = []
    benefit = first_NPV * (-1)
    for q in query:
        dates.append(date_str_to_date(q[1]))
        values.append(q[2])
        benefit = benefit + q[2]
    benefit = benefit + last_NPV
    values.append(first_NPV * (-1))
    values.append(last_NPV)
    dates.append(first_date)
    dates.append(last_date)
    try:
        rate = "{0:.2f}".format(XIRR.xirr(values, dates) * 100) + "%"
    except: # noqa
        rate = "XIRR error"
    data.append("{0:.2f}".format(benefit) + "€")
    data.append(rate)
    # END XIRR
    return render_template('npv.html', title='NPV', table=response, data=data)


@app.route('/investments', methods=['GET', 'POST'])
@login_required
def investments():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    if request.method == 'POST':
        a = request.form.get('fecha')
        b = request.form.get('amount')
        d = request.form.get('account')
        e = request.form.get('comments')
        c.execute("INSERT OR REPLACE INTO investment_movements (fecha, cantidad, cuenta, comments) VALUES (?, ?, ?, ?)", (a, b, d, e))
        conn.commit()
    response = []
    c.execute('SELECT * FROM investment_movements ORDER BY fecha DESC')
    query = c.fetchall()
    for q in query:
        lista = []
        lista.append(date_str_to_date(q[1]).strftime("%d-%m-%Y"))
        lista.append("{0:.2f}".format(q[2]) + "€")
        lista.append(q[3])
        lista.append(q[4])
        response.append(lista)
    return render_template('investments.html', title='Investments', table=response)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    if request.method == 'POST':
        a = int(request.form.get('value')) * 60
        c.execute('INSERT or REPLACE INTO variables (name, value) VALUES (?, ?)', ('scrape_interval', a))
        conn.commit()
    c.execute('SELECT * FROM variables where name=? LIMIT 1', ('scrape_interval',))
    query = c.fetchone()
    data = []
    data.append(int(int(query[1]) / 60))
    return render_template('settings.html', data=data)
