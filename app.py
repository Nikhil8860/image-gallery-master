import os
from flask import Flask, request, render_template, send_from_directory, session, redirect
import json
import re

from flask_mysqldb import MySQL

import MySQLdb.cursors

app = Flask(__name__)
mysql = MySQL(app)
app.secret_key = 'super-secret-key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'charan_dal'

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
with open('config.json', 'r') as c:
    params = json.load(c)["params"]


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        print(username, password, email, sep='--')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password or not email:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, % s, % s, % s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg=msg)


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


if __name__ == "__main__":
    app.run(port=8080, debug=True)
