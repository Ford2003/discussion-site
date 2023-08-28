import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import logging
import sys
from flask_mail import Mail
from mathdown import MathDown
from dotenv import load_dotenv

load_dotenv('var.env')

# Set up app and config
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET')
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASS")}@127.0.0.1:5432/data'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.update(dict(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_TLS=False,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=os.getenv('MAIL_USER'),
    MAIL_PASSWORD=os.getenv('MAIL_PASS'),
    MAIL_DEFAULT_SENDER=os.getenv('MAIL_USER')
))

# Set up database and migration
# To migrate the db run flask db migrate, check code in most recent migration in /migrations for correct changes
# Then run flask db upgrade
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Set up login manager
login_manager = LoginManager()
login_manager.init_app(app)

# Set up logger
logger = logging.getLogger(__name__)

stream_handler = logging.StreamHandler(sys.stderr)
file_handler = logging.FileHandler('logs/app.log')

formatter = logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s - %(message)s')

stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

mail = Mail()
mail.init_app(app)

mathdown = MathDown(app)

import routes
import models
import api

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
