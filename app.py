import os
from flask import Flask, request, render_template, send_from_directory, session, redirect, flash
from flask_session import Session
import json
from flask_mysqldb import MySQL
from datetime import timedelta
import MySQLdb.cursors
import requests
import logging
import datetime
from paytm_checksum import generate_checksum, verify_checksum

app = Flask(__name__)
mysql = MySQL(app)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=1)

app.secret_key = 'super-secret-key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'charan_dal'
Session(app)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

MERCHANT_ID = ""
MERCHANT_KEY = ""
WEBSITE_NAME = "WEBSTAGING"
# WEBSITE_NAME = "http://127.0.0.1:8080/"
INDUSTRY_TYPE_ID = "Retail"
# BASE_URL = "https://securegw.paytm.in"
BASE_URL = "https://securegw-stage.paytm.in"

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
with open('config.json', 'r') as c:
    params = json.load(c)["params"]


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    print(request.form)
    if request.method == 'POST':
        first_name = request.form['fname']
        last_name = request.form['lname']
        email = request.form['email']
        phone = request.form['phone']
        msg = request.form['msg']
        dob = request.form['dob']
        city = request.form['city']
        pin_code = request.form['pincode']
        district = request.form['district']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        check_sql = "select * from register where email=" + "'" + email + "'"
        cursor.execute(check_sql)
        data = cursor.fetchone()
        if data:
            flash("User already exist")
            return render_template('register.html', msg=msg)
        sql = 'INSERT INTO register (first_name, last_name, dob, city, pincode, district, email, phone, msg ) ' \
              'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
        val = (first_name, last_name, dob, city, pin_code, district, email, phone, msg)

        cursor.execute(sql, val)
        mysql.connection.commit()
        msg = 'You have successfully registered !'
        flash(msg)
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg=msg)


@app.route('/about')
def about():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        sql = "Select * from blog"
        cursor.execute(sql)
        data = cursor.fetchall()
        return render_template('about.html', data=data)
    except (ConnectionError, MySQLdb.OperationalError):
        return "DB not Connected"


@app.route("/about/<string:about_slug>", methods=['GET'])
def post_route(about_slug):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    sql = "Select * from blog where title=" + "'" + about_slug + "'"
    print(sql)
    cursor.execute(sql)
    data = cursor.fetchone()
    return render_template('post.html', post=data)


@app.route('/blog', methods=['GET', 'POST'])
def blog():
    msg = ''
    if request.method == 'POST':
        title = request.form['title']
        descr = request.form['descr']
        print(title, descr, sep='--')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        sql = 'INSERT INTO blog (title, description) ' \
              'VALUES (%s, %s)'
        val = (title, descr)

        cursor.execute(sql, val)
        mysql.connection.commit()
        msg = 'Post Added Successfully!'
        flash(msg)
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('add-blog.html', msg=msg)


@app.route('/home')
@app.route("/")
def index():
    images = os.listdir('./images')
    return render_template("index.html", images=images)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/delete/<string:image_name>')
def delete(image_name):
    target = os.path.join(APP_ROOT, 'images/' + image_name)
    print(target)
    os.remove(target)
    return redirect('/upload')


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if ('user' in session and session['user'] == params['admin_user']):

        if request.method == "GET":
            return render_template('upload.html', images=os.listdir('./images'))
        target = os.path.join(APP_ROOT, 'images/')
        if not os.path.isdir(target):
            os.mkdir(target)
        for file in request.files.getlist("file"):
            print(file)
            filename = file.filename
            destination = "/".join([target, filename])
            print(destination)
            file.save(destination)
        return render_template("uploaded.html")
    return redirect('/dashboard')


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_user']):
        return render_template('upload.html', params=params)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == 'admin' and userpass == params['admin_user']):
            # set the session variable
            session['user'] = username
            session.permanent = True
            return redirect('/upload')

    return render_template('login.html', params=params)


@app.route('/upload/<filename>')
def send_image(filename):
    return send_from_directory("images", filename)


def send_image_for_filter(image):
    return render_template('filter.html', image=image)


@app.route("/filters")
def filter():
    return render_template('filters.html')


@app.route("/logout")
def logout():
    if ('user' in session and session['user'] == params['admin_user']):
        session.pop('user')
        return redirect('/')
    return redirect('/dashboard')


# @app.url_defaults
# def hashed_url_for_static_file(endpoint, values):
#     if 'static' == endpoint or endpoint.endswith('.static'):
#         filename = values.get('filename')
#         if filename:
#             if '.' in endpoint:  # has higher priority
#                 blueprint = endpoint.rsplit('.', 1)[0]
#             else:
#                 blueprint = request.blueprint  # can be None too
#             if blueprint:
#                 static_folder = app.blueprints[blueprint].static_folder
#             else:
#                 static_folder = app.static_folder
#             param_name = 'h'
#             while param_name in values:
#                 param_name = '_' + param_name
#             values[param_name] = static_file_hash(os.path.join(static_folder, filename))


def static_file_hash(filename):
    return int(os.stat(filename).st_mtime)


@app.route("/payment")
def payment():
    amount = 11.07
    transaction_data = {
        "MID": MERCHANT_ID,
        "WEBSITE": WEBSITE_NAME,
        "INDUSTRY_TYPE_ID": INDUSTRY_TYPE_ID,
        "ORDER_ID": str(datetime.datetime.now().timestamp()),
        "CUST_ID": "007",
        "TXN_AMOUNT": str(amount),
        "CHANNEL_ID": "WEB",
        "MOBILE_NO": "7777777777",
        "EMAIL": "example@paytm.com",
        "CALLBACK_URL": "http://127.0.0.1:8080/callback"
    }

    # Generate checksum hash
    transaction_data["CHECKSUMHASH"] = generate_checksum(transaction_data, MERCHANT_KEY)

    logging.info("Request params: {transaction_data}".format(transaction_data=transaction_data))

    url = BASE_URL + '/theia/processTransaction'
    return render_template("paytm.html", data=transaction_data, url=url)


@app.route('/callback', methods=["GET", "POST"])
def callback():
    # log the callback response payload returned:
    callback_response = request.form.to_dict()
    logging.info("Transaction response: {callback_response}".format(callback_response=callback_response))

    # verify callback response checksum:
    checksum_verification_status = verify_checksum(callback_response, MERCHANT_KEY,
                                                   callback_response.get("CHECKSUMHASH"))
    logging.info("checksum_verification_status: {check_status}".format(check_status=checksum_verification_status))

    # verify transaction status:
    transaction_verify_payload = {
        "MID": callback_response.get("MID"),
        "ORDERID": callback_response.get("ORDERID"),
        "CHECKSUMHASH": callback_response.get("CHECKSUMHASH")
    }
    url = BASE_URL + '/order/status'
    verification_response = requests.post(url=url, json=transaction_verify_payload)
    logging.info("Verification response: {verification_response}".format(
        verification_response=verification_response.json()))

    return render_template("callback.html",
                           callback_response=callback_response,
                           checksum_verification_status=checksum_verification_status,
                           verification_response=verification_response.json())


if __name__ == "__main__":
    app.run(port=8080, debug=True)
