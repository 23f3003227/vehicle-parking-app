from flask import Flask, request, redirect, url_for, render_template, flash #Core Flask import for web application functionality.
from flask_sqlalchemy import SQLAlchemy # Database ORM for Flask.
from flask_login import LoginManager, UserMixin # Handles user session management and authentication.
from werkzeug.security import generate_password_hash, check_password_hash # For secure password hashing
import os # Provides functions for interacting with the operating system.

app = Flask(__name__) # Initializes the Flask web application.

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY','a_very_secret_key') # Sets a secret key for the Flask application.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db' # Configures the database URI (Uniform Resource Identifier) for SQLAlchemy.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Disables SQLAlchemy's event system for tracking modifications.

db=SQLAlchemy(app) # Initializes the database connection with the Flask app.

login_manager = LoginManager(app) # This object manages the entire user session process.
login_manager.login_view = 'login' # Tells Flask-Login which view function (route) handles user logins.
login_manager.login_message_category = 'info' # Sets the message category for the default "Please log in to access this page."

@login_manager.user_loader
def load_user(user_id):
    user=User.query.get(int(user_id))
    if user:
        return user
    return Admin.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    fullname = db.Column(db.String(120))
    address = db.Column(db.String(200))
    pin_code = db.Column(db.Integer)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"User('{self.email_id}', '{self.fullname}')"

class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    fullname = db.Column(db.String(120))
    address = db.Column(db.String(200))
    pin_code = db.Column(db.Integer)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"Admin('{self.email_id}', '{self.fullname}')"

def create_db_and_seed_admin():
    with app.app_context():
        db.create_all()
        print("Database tables created.")

        if not Admin.query.filter_by(email_id='admin@example.com').first():
            admin_user = Admin(
                email_id='admin@example.com',
                fullname='System Admin',
                address='Admin HQ, Haryana',
                pin_code=411019
            )
            admin_user.set_password('superadminpass')
            db.session.add(admin_user)
            db.session.commit()
            print('Predefined admin user created: admin@example.com / superadminpass')
        else:
            print('Admin user already exists.')

if __name__=='__main__':
    create_db_and_seed_admin()
    app.run(debug=True)