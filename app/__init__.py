from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
import logging

db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
    # app.config['MAIL_SERVER'] = 'smtp.thehexaa.com'
    # app.config['MAIL_PORT'] = 587
    # app.config['MAIL_USE_TLS'] = True
    # app.config['MAIL_USERNAME'] = os.getenv('EMAIL_HOST')
    # app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASSWORD')

    # Configure Flask-Mail
    app.config['MAIL_SERVER'] = 'mail.thehexaa.com'
    app.config['MAIL_PORT'] = 25
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = None
    app.config['MAIL_PASSWORD'] = None
    app.config['MAIL_DEFAULT_SENDER'] = 'daily-reports@thehexaa.com'

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    migrate = Migrate(app, db)
    
    login_manager.login_view = 'main.login'
    login_manager.init_app(app)

    from .models import User  # Import after db is initialized

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    app.logger.addHandler(handler)

    return app
