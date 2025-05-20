from flask import Flask, request, render_template, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
db=SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    email_id = db.Column(db.String(120), nullable = False, unique = True)
    password = db.Column(db.String(60), nullable = False)
    fullname = db.Column(db.String(120), nullable = False)
    address = db.Column(db.String(200), nullable = False)
    pin_code = db.Column(db.Integer, nullable = False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    email_id = db.Column(db.String(120), nullable = False, unique = True)
    password = db.Column(db.String(60), nullable = False)

class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    prime_location_name = db.Column(db.String(100), nullable = False)
    price = db.Column(db.Float, nullable = False)
    address = db.Column(db.String(200), nullable = False)
    pin_code = db.Column(db.Integer, nullable = False)
    max_no_of_spots = db.Column(db.Integer, nullable = False)

class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parkinglot.id'), nullable = False)
    status = db.Column(db.String(1), nullable = False, default = 'A')

class ReserveParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parkingspot.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    parking_timestamp = db.Column(db.DateTime, nullable = False)
    leaving_timestamp = db.Column(db.DateTime, nullable=False)
    parking_cost_per_unit_time = db.Column(db.Float, nullable=False)

if __name__ == "__main__":
    app.run(debug=True)
