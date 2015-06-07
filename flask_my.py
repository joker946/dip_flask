from flask import Flask
from flask import request
from flask import abort, make_response
import psycopg2
from psycopg2.extras import DictCursor
import json
import datetime
app = Flask(__name__)


class Connection(object):

    def __init__(self):
        self.conn = psycopg2.connect("dbname=pms user=alexchadin")

    def __enter__(self):
        self.cursor = self.conn.cursor(cursor_factory=DictCursor)
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()

authorized_users = {}
dthandler = lambda obj: obj.isoformat() if isinstance(
    obj, datetime.datetime) else None


def auth(login, password):
    if login not in authorized_users:
        with Connection() as db:
            db.execute('SELECT login_name, password FROM users '
                       'WHERE login_name = %s', [login])
            res = db.fetchone()
            if res:
                authorized_users[res['login_name']] = res['password']
    if login in authorized_users and authorized_users[login] == password:
        return True
    elif login in authorized_users and authorized_users[login] != password:
        return False
    return False


@app.route('/')
def hello_world():
    return 'Hello World!'


def request_to_project_model(r):
    proj = {}
    proj['id'] = r.get('id', '')
    proj['title'] = r.get('title', '')
    if r.get('date_created') is not None:
        proj['date_created'] = r['date_created']
    else:
        proj['date_created'] = datetime.datetime.now()
    proj['url'] = r.get('url', '')
    proj['expiration_date'] = r.get('expiration_date', '')
    proj['description'] = r.get('description', '')
    return proj


def request_to_user_model(r):
    new_user = {}
    new_user['id'] = r.get('id', '')
    new_user['login_name'] = r.get('login_name', '')
    new_user['first_name'] = r.get('first_name', '')
    new_user['last_name'] = r.get('last_name', '')
    new_user['email'] = r.get('email', '')
    new_user['password'] = r.get('password', '')
    return new_user


@app.route('/projects/', methods=['GET', 'POST'])
def get_projects():
    if request.method == 'GET':
        with Connection() as db:
            db.execute('SELECT * FROM project')
            array = []
            body = {}
            res = db.fetchall()
            for r in res:
                proj = request_to_project_model(r)
                array.append(proj)
            body['Projects'] = array
            return json.dumps(body, default=dthandler)
    elif request.method == 'POST':
        json_body = request.json
        print json_body
        new_project = request_to_project_model(json_body)
        print new_project
        with Connection() as db:
            try:
                db.execute('INSERT INTO project (title, date_created, url, '
                           'expiration_date, description) '
                           'VALUES (%s, %s, %s, %s, %s)',
                           [new_project['title'], new_project['date_created'],
                            new_project['url'], new_project['expiration_date'],
                            new_project['description']
                            ])
                return 'project row added'
            except Exception:
                return 'error'


@app.route('/login/', methods=['GET', 'POST'])
def get_authorize():
    json_body = request.json
    if auth(json_body['user'], json_body['password']):
        print 'auth'
        return 'true'
    return abort(500)


@app.route('/users/', methods=['GET', 'POST'])
def get_users():
    if request.method == 'GET':
        with Connection() as db:
            db.execute('SELECT * FROM users')
            array = []
            body = {}
            res = db.fetchall()
            for r in res:
                user = request_to_user_model(r)
                array.append(user)
            body['Users'] = array
            return json.dumps(body, default=dthandler)
    elif request.method == 'POST':
        json_body = request.json
        new_user = request_to_user_model(json_body)
        with Connection() as db:
            try:
                db.execute('INSERT INTO users (login_name, first_name,'
                           ' last_name, e_mail, password) VALUES (%s, %s, %s,'
                           ' %s, %s)', [new_user['login_name'],
                                        new_user['first_name'], new_user[
                                            'last_name'],
                                        new_user['email'],
                                        new_user['password']])
                return 'user added'
            except Exception:
                return 'error'


@app.route('/projects/<project_id>')
def get_project(project_id):
    print dir(request)
    print request.headers
    with Connection() as db:
        db.execute('SELECT * FROM project WHERE id=%s', [project_id])
        res = db.fetchone()
    if res:
        proj = request_to_project_model(res)
        return json.dumps(proj, default=dthandler)
    return make_response("{'Error': 'Happened'}", 404)

if __name__ == '__main__':
    app.debug = True
    app.run(host='192.168.10.104')
