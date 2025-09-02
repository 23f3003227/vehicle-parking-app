from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    fullname = db.Column(db.String(120))
    address = db.Column(db.String(200))
    pin_code = db.Column(db.String(10))

    reservations = db.relationship('Reservation', backref='reserving_user',cascade='all, delete-orphan',lazy=True)
    user_occupied_spot = db.relationship('ParkingSpot', backref='occupied_by_user', uselist=False, foreign_keys='ParkingSpot.user_id',lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return f"user_{self.id}"

    def __repr__(self):
        return f"User('{self.email_id}', '{self.fullname}')"

class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    fullname = db.Column(db.String(120))
    address = db.Column(db.String(200))
    pin_code = db.Column(db.String(10))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return f"admin_{self.id}"

    def __repr__(self):
        return f"Admin('{self.email_id}', '{self.fullname}')"

class ParkingLot(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    prime_location_name = db.Column(db.String(120),nullable=False,unique=True)
    price_per_unit_time = db.Column(db.Float,nullable=False)
    address = db.Column(db.String(200),nullable=False)
    pin_code = db.Column(db.String(10),nullable=False)
    maximum_number_of_spots = db.Column(db.Integer,nullable=False)

    spots = db.relationship('ParkingSpot',backref = 'parking_lot', lazy = True, cascade = 'all, delete-orphan')

    def __repr__(self):
        return f"ParkingLot('{self.prime_location_name}','{self.address}',Capacity: {self.maximum_number_of_spots})" 
    
class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    spot_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='available')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    reservations = db.relationship('Reservation', backref='parking_spot', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"ParkingSpot(Lot: {self.lot_id}, Spot: {self.spot_number}, Status: {self.status}, User: {self.user_id})"
    
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parking_timestamp = db.Column(db.DateTime,nullable=False, default=datetime.now)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)
    parking_cost_per_unit_time = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"Reservation(User: {self.user_id}, Spot: {self.spot_id}, Start: {self.parking_timestamp.strftime('%Y-%m-%d %H:%M')}, End: {self.leaving_timestamp.strftime('%Y-%m-%d %H:%M') if self.leaving_timestamp else 'N/A'})"