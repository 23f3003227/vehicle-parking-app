from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# We create the extensions outside of a function so they can be accessed by models and routes.
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key_that_should_be_changed')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Now we initialize the extensions with the app instance.
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'

    # We import the models here so db.create_all() knows about them.
    from .models import User, Admin 
    
    # We import and register the routes as a Blueprint.
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # The user loader function is defined here because it needs access to both
    # the login_manager and the User/Admin models.
    @login_manager.user_loader
    def load_user(user_id_str):
        if '_' in user_id_str:
            user_type, user_id = user_id_str.split('_', 1)
            try:
                user_id = int(user_id)
            except ValueError:
                return None
            
            if user_type == 'user':
                return User.query.get(user_id)
            elif user_type == 'admin':
                return Admin.query.get(user_id)
        return None

    return app