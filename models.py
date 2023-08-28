from app import db
import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True, unique=True)
    email = db.Column(db.String(80), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    joined_at_date = db.Column(db.DateTime(), index=True, default=datetime.datetime.utcnow())
    liked_discussion_ids = db.Column(db.String, index=True, unique=False, default='')
    disliked_discussion_ids = db.Column(db.String, index=True, unique=False, default='')
    liked_comment_ids = db.Column(db.String, index=True, unique=False, default='')
    disliked_comment_ids = db.Column(db.String, index=True, unique=False, default='')
    verified_email = db.Column(db.Boolean, index=False, unique=False, default=False)
    email_code = db.Column(db.String, index=False, unique=False)
    reset_password_code = db.Column(db.String, index=False, unique=False, default='')
    reset_password_expire_time = db.Column(db.DateTime(), index=False, unique=False, default=datetime.datetime.utcnow())
    api_key = db.Column(db.String, index=True, unique=True)

    discussions = db.relationship('Discussion', backref='poster', lazy='dynamic')
    comments = db.relationship('Comment', backref='poster', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Discussion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), index=True, unique=True)
    text = db.Column(db.String(512), index=True, unique=False)
    tags = db.Column(db.String, index=True, unique=False)
    views = db.Column(db.Integer, index=True, unique=False, default=0)
    likes = db.Column(db.Integer, index=True, unique=False, default=0)
    dislikes = db.Column(db.Integer, index=True, unique=False, default=0)

    post_date = db.Column(db.DateTime(), index=True, default=datetime.datetime.utcnow())
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'))

    comments = db.relationship('Comment', backref='discussion', lazy='dynamic', cascade='all, delete, delete-orphan')


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(512), index=True, unique=False)
    post_date = db.Column(db.DateTime(), index=True, default=datetime.datetime.utcnow())
    likes = db.Column(db.Integer, index=True, unique=False, default=0)
    dislikes = db.Column(db.Integer, index=True, unique=False, default=0)

    poster_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'))
    discussion_id = db.Column(db.Integer, db.ForeignKey('discussion.id'))
