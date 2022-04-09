from . import db
from flask_login import UserMixin


class Userstudio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    studio_id = db.Column(db.Integer, db.ForeignKey('studio.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name_surname = db.Column(db.String(150))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    address = db.Column(db.String(500), nullable=True)
    country = db.Column(db.String(50), nullable=True)
    postalcode = db.Column(db.Integer(), nullable=True)
    iban = db.Column(db.String(50), nullable=True)
    # studio_id = db.relationship('Studio',secondary=userstudio,backref='studios')


class Studio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    studio_name = db.Column(db.String(50))
    studio_owner = db.Column(db.String(50))
    description = db.Column(db.String(1000))
    country = db.Column(db.String(20))
    city = db.Column(db.String(10))
    street = db.Column(db.String(50))
    surface = db.Column(db.String(50))
    price = db.Column(db.Integer())
    # picture_name = db.Column(db.Text)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    active = db.Column(db.Integer())


class Reservations(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    studio_id = db.Column(db.Integer, db.ForeignKey('studio.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    studio_busy_date = db.Column(db.String)
    studio_busy_time = db.Column(db.String)
    studio_check_out_time = db.Column(db.String)
    reservation_date = db.Column(db.String)
    active = db.Column(db.Integer())


class Pictures(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    studio_name = db.Column(db.String(50))
    studio_id = db.Column(db.Integer, db.ForeignKey('studio.id'))
    pictures = db.Column(db.String)
