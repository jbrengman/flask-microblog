from flask import (
    Flask, render_template, request, session, url_for, redirect, abort)
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flaskext.bcrypt import Bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres:///micro'
app.secret_key = 'uYV6&475#57bi^onn8B&565bB5nb5&bui%&*B^B&'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

bcrypt = Bcrypt(app)


class Post(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), unique=True)
    body = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body):
        self.title = title
        self.body = body


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(500))
    posts = db.relationship('Post', backref='user')

    def __init__(self, name, password):
        self.name = name
        self.password = bcrypt.generate_password_hash(password)


def create_user(name, password):
    new_user = User(name, password)
    db.session.add(new_user)
    db.session.commit()


def write_post(title, text):
    new_post = Post(title, text)
    db.session.add(new_post)
    db.session.commit()


def read_posts():
    posts = Post.query.all()
    posts.reverse()
    return posts


def read_post(id):
    post = Post.query.filter_by(id=id).first()
    if not post:
        raise IndexError('Post not found.')
    else:
        return post


@app.route('/', endpoint='index')
def list_view():
    posts = read_posts()
    page_html = render_template('list.html', title='Microblog posts',
                                heading='Microblog posts', posts=posts)
    return page_html


@app.route('/posts/<int:id>')
def post_view(id):
    post = read_post(id)
    page_html = render_template('post.html', title=post.title,
                                heading=post.title, body=post.body)
    return page_html


@app.route('/posts/new', methods=['GET', 'POST'])
def new_view():
    if not session.get('logged_in'):
        abort(401, 'You must be logged in to create a new post.')
    if request.method == 'POST':
        write_post(request.form['title'], request.form['body'])
        return redirect(url_for('index'))
    else:
        page_html = render_template('new.html', title='Create',
                                    heading='Create a new microblog post:')
        return page_html


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(name=request.form['username']).first()
        if user:
            if bcrypt.check_password_hash(user.password, request.form['password']):
                session['logged_in'] = True
        return redirect(url_for('index'))
    else:
        page_html = render_template('login.html',
                                    title='Login', heading='Login')
        return page_html


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(error):
    return (render_template('base.html', title='Not found',
            heading='404', body='Page not found'), 404)


@app.errorhandler(401)
def access_denied(error):
    return (render_template('base.html', title='Access Denied',
            heading='401', body='Access denied'), 401)

if __name__ == '__main__':
    manager.run()
