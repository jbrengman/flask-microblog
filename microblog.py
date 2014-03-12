from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres:///micro'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)


class Post(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), unique=True)
    body = db.Column(db.Text)

    def __init__(self, title, body):
        self.title = title
        self.body = body


def write_post(title, text):
    new_post = Post(title, text)
    db.session.add(new_post)
    db.session.commit()


def read_posts():
    posts = Post.query.all()
    posts.reverse()
    return posts


def read_post(_id):
    post = Post.query.filter_by(id=_id).first()
    if not post:
        raise IndexError('Post not found.')
    else:
        return post

if __name__ == '__main__':
    manager.run()
