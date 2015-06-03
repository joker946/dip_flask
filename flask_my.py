from flask import Flask
from flask import request
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
    proj['id'] = r['id']
    proj['title'] = r['title']
    proj['date_created'] = r['date_created']
    proj['url'] = r['url']
    proj['expiration_date'] = r['expiration_date']
    return proj


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
            body['obj'] = array
            return json.dumps(body)
    elif request.method == 'POST':
        json_body = request.json
        new_project = {}
        new_project['title'] = json_body.get('title', '')
        new_project['date_created'] = json_body.get('date_created',
                                                    datetime.datetime.now())
        new_project['url'] = json_body.get('url', '')
        new_project['expiration_date'] = json_body.get('expiration_date', None)
        with Connection() as db:
            try:
                db.execute('INSERT INTO project (title, date_created, url, '
                           'expiration_date) VALUES (%s, %s, %s, %s)',
                           [new_project['title'], new_project['date_created'],
                            new_project['url'], new_project['expiration_date']
                            ])
                return 'project row added'
            except Exception:
                return 'error'


@app.route('/login/', methods=['GET', 'POST'])
def get_authorize():
    json_body = request.json
    if auth(json_body['user'], json_body['password']):
        return 'true'
    return 'error'


@app.route('/users/', methods=['GET', 'POST'])
def get_users():
    if request.method == 'POST':
        json_body = request.json
        new_user = {}
        new_user['login_name'] = json_body.get('login_name', '')
        new_user['first_name'] = json_body.get('first_name', '')
        new_user['last_name'] = json_body.get('last_name', '')
        new_user['email'] = json_body.get('email', '')
        new_user['password'] = json_body.get('password', '')
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
    with Connection() as db:
        db.execute('SELECT * FROM project WHERE id=%s', [project_id])
        res = db.fetchone()
    if res:
        proj = request_to_project_model(res)
        dthandler = lambda obj: obj.isoformat() if isinstance(
            obj, datetime.datetime) else None
        return json.dumps(proj, default=dthandler)
    return 'Not found'

if __name__ == '__main__':
    app.debug = True
    app.run(host='192.168.10.104')
