from flask import (
    Flask, render_template, request, session, url_for, redirect, abort)
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.mail import Mail, Message
from flaskext.bcrypt import Bcrypt
from flask.ext.seasurf import SeaSurf
from sqlalchemy.exc import IntegrityError
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres:///micro'
app.secret_key = 'uYV6&475#57bi^onn8B&565bB5nb5&bui%&*B^B&'

db = SQLAlchemy(app)
migrate = Migrate(app, db)


manager = Manager(app)
manager.add_command('db', MigrateCommand)

bcrypt = Bcrypt(app)

mail = Mail(app)

csrf = SeaSurf(app)

categories = db.Table('categories', db.Column(
    'category_id', db.Integer, db.ForeignKey('category.id')),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id')))


class Post(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), unique=True)
    body = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'))
    categories = (
        db.relationship('Category', secondary=categories,
                        backref=db.backref('posts', lazy='dynamic')))

    def __init__(self, title, body, categories, author_id):
        self.title = title
        self.body = body
        self.categories = categories
        self.author_id = author_id


class Author(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(500))
    email = db.Column(db.String(50), unique=True)
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    def __init__(self, name, password, email):
        self.name = name
        self.password = password  # Password already encrypted in New_author
        self.email = email


class New_author(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(500))
    email = db.Column(db.String(50), unique=True)
    conf_key = db.Column(db.String(50), unique=True)

    def __init__(self, name, password, email, conf_key):
        self.name = name
        self.password = bcrypt.generate_password_hash(password)
        self.email = email
        self.conf_key = conf_key


class Category(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

    def __init__(self, name):
        self.name = name


def create_author(name, password, email):
    conf_key = str(random.randrange(100000, 999999))
    session['conf_key'] = conf_key
    new_author = New_author(name, password, email, conf_key)
    db.session.add(new_author)
    db.session.commit()
    send_conf_email(email, conf_key)
    return new_author


def confirm_author(conf_key):
    new_author = New_author.query.filter_by(conf_key=conf_key).first()
    confirmed_author = Author(
        new_author.name, new_author.password, new_author.email)
    db.session.delete(new_author)
    session.pop('conf_key')
    db.session.add(confirmed_author)
    db.session.commit()
    return confirmed_author


def send_conf_email(email, conf_key):
    link = 'localhost:5000/confirm/' + conf_key
    msg = Message()
    msg.sender = 'microblog@microblog.registration'
    msg.add_recipient(email)
    msg.body = 'Follow the link to confirm registration: ' + link
    msg.html = ('Follow the link to confirm registration: <a href="'
                + link + '">' + link + '</a>')
    # mail.send(msg)


def create_category(name):
    cat = Category(name)
    db.session.add(cat)
    db.session.commit()
    return cat


def write_post(title, text, categories, author_id):
    cat_names = categories.split(' ')
    cat_list = []
    for cat_name in cat_names:
        category = Category.query.filter_by(name=cat_name).first()
        if not category:
            category = create_category(cat_name)
        cat_list.append(category)
    new_post = Post(title, text, cat_list, author_id)
    db.session.add(new_post)
    db.session.commit()
    return new_post


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


@app.route('/post/<int:id>')
def post_view(id):
    post = read_post(id)
    page_html = render_template('post.html', title=post.title,
                                heading=post.title, body=post.body)
    return page_html


@app.route('/post/new', methods=['GET', 'POST'])
def new_view():
    if not session.get('logged_in'):
        return 'You must be logged in to create a new post.'
    if request.method == 'POST':
        write_post(
            request.form['title'],
            request.form['body'],
            request.form['categories'],
            session.get('author_id'))
        return redirect(url_for('index'))
    else:
        page_html = render_template('new.html', title='Create',
                                    heading='Create a new microblog post:')
        return page_html


@app.route('/register', methods=['GET', 'POST'])
def register_view():
    if request.method == 'POST':
        try:
            create_author(
                request.form['username'],
                request.form['password'],
                request.form['email'])
            return ('Email confirmation not set up. <a href="/confirm/'
                    + session.get('conf_key') +
                    '">Click here</a> to confirm your registration.')
        except IntegrityError:
            return redirect(url_for('register'))
    else:
        page_html = render_template('register.html', title='Register',
                                    heading='Register a new account:')
        return page_html


@app.route('/confirm/<string:conf_key>')
def confirm_view(conf_key):
    if session.get('conf_key') == conf_key:
        confirm_author(conf_key)
        # page_html = render_template()  # Create template for success
        page_html = (
            'Registration confirmation successful. ' +
            '<a href="url_for("login_view")">Click here</a> to login.')
        return page_html
    else:
        abort(401)


@app.route('/login', methods=['GET', 'POST'])
def login_view():
    if request.method == 'POST':
        author = Author.query.filter_by(name=request.form['username']).first()
        if author:
            if bcrypt.check_password_hash(
                    author.password, request.form['password']):
                session['logged_in'] = True
                session['author_id'] = author.id
        return redirect(url_for('index'))
    else:
        page_html = render_template('login.html',
                                    title='Login', heading='Login')
        return page_html


@app.route('/logout')
def logout_view():
    session.pop('logged_in', None)
    session.pop('author_id', None)
    page_html = render_template(
        'logout.html', title='Logout',
        heading='Logout')
    return page_html


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
