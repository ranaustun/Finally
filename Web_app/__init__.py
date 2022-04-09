from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path

from flask_mail import Mail
import stripe
from flask_login import LoginManager

db = SQLAlchemy(session_options={"autoflush": False})
mail = Mail()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('flask.cfg')

    app.config['SECRET_KEY'] = 'My secret key'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    mail = Mail(app)

    stripe.api_key = "sk_test_51KVslAAynAO1OpqrGpQ9WcxeGW6FFOHV3BxF4PRYAmyewwGZLpTTOBQWz1mpk21yhBjNTFT84TkMqEHRk3tkDDnn00b3Wn3qnK"

    db.init_app(app)

    from .views import views
    from .auth import auth

    # registering blueprints
    app.register_blueprint(views, url_prefix='/')  # all of the urls are stored inside of these blueprints file
    app.register_blueprint(auth, url_prefix='/')

    from .models import User
    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def create_database(app):
    if not path.exists('Web_app/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database! ')
