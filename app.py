from flask import Flask, request, redirect, url_for, render_template, flash #Core Flask import for web application functionality.
from flask_sqlalchemy import SQLAlchemy # Database ORM for Flask.
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required # Handles user session management and authentication.
from werkzeug.security import generate_password_hash, check_password_hash # For secure password hashing
import os # Provides functions for interacting with the operating system.

app = Flask(__name__) # Initializes the Flask web application.

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY','a_very_secret_key') # Sets a secret key for the Flask application.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'site.db') # Configures the database URI (Uniform Resource Identifier) for SQLAlchemy.
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
    pin_code = db.Column(db.String(10))

    reservations = db.relationship('Reservation', backref='reserving_user',cascade='all, delete-orphan',lazy=True)

    user_occupied_spot = db.relationship('ParkingSpot', backref='occupied_by_user', uselist=False, foreign_keys='ParkingSpot.user_id',lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self.id)

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
        return str(self.id)

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

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        if isinstance(current_user, Admin):
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        fullname=request.form['fullname']
        address=request.form['address']
        pin_code=request.form['pincode']

        existing_user=User.query.filter_by(email_id=email).first()
        existing_admin=Admin.query.filter_by(email_id=email).first()

        if existing_user or existing_admin:
            flash('That email is already registered. Please use a different email or log in')
            return render_template('register.html', email=email,fullname=fullname,address=address,pin_code=pin_code)
        else:
            new_user=User(email_id=email,fullname=fullname,address=address,pin_code=pin_code)
            new_user.set_password(password)
            try:
                db.session.add(new_user)
                db.session.commit()
                flash('Registration Successfull! Please log in.','success')
            except Exception as e:
                db.session.rollback()
                flash(f'An error occured during registration. Please try again. ({e})','danger')
                return render_template('register.html',email=email,fullname=fullname,address=address,pin_code=pin_code)
    return render_template('register.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.','info')
        if isinstance(current_user,Admin):
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        remember_me=request.form.get('remember_me')

        user=User.query.filter_by(email_id=email).first()
        admin=Admin.query.filter_by(email_id=email).first()

        authenticated_user=None

        if user and user.check_password(password):
            authenticated_user=user
        elif admin and admin.check_password(password):
            authenticated_user=admin

        if authenticated_user:
            login_user(authenticated_user,remember=remember_me)
            flash(f'Welcome {authenticated_user.fullname}!','success')

            if isinstance(authenticated_user,Admin):
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        
        else:
            flash('Login Failed. Check email or password','danger')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.','info')
    return redirect(url_for('home'))

@app.route('/user_dashboard')
@login_required
def user_dashboard():
    if isinstance(current_user,Admin):
        flash('Admin cannot access user dashboard directly','danger')
        return redirect(url_for('admin_dashboard'))
    return render_template('user_dashboard.html')

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not isinstance(current_user,Admin):
        flash('You must be an admin to access this page','danger')
        return redirect(url_for('user_dashboard'))
    return render_template('admin_dashboard')

@app.route('/admin/parking_lot/create', methods = ['GET','POST'])
@login_required
def create_parking_lot():
    if not isinstance(current_user, Admin):
        flash('You must be administrator to access this page.','danger')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':

        prime_location = request.form['prime_location_name']
        price = float(request.form['price_per_unit_time'])
        address = request.form['address']
        pin_code = request.form['pin_code']
        maximum_no_of_spots = int(request.form['maximum_number_of_spots'])

        try: 

            existing_lot = ParkingLot.query.filter_by(prime_location_name=prime_location).first()

            if existing_lot:
                flash('A parking lot with this location name already exists.','warning')

                return render_template('create_parking_lot.html',
                 prime_location_name=prime_location,
                 price_per_unit_time=price,
                 address=address,
                 pin_code=pin_code,
                 maximum_number_of_spots=maximum_no_of_spots)
            
            parking_lot = ParkingLot(prime_location_name=prime_location,price_per_unit_time=price,address=address,pin_code=pin_code,maximum_number_of_spots=maximum_no_of_spots)
            db.session.add(parking_lot)
            db.session.commit()

            #Creating Spots
            for i in range(1,maximum_no_of_spots+1):
                spot = ParkingSpot(lot_id=parking_lot.id,spot_number=i,status='available')
                db.session.add(spot)
            db.session.commit()
            flash('Parking lot created successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'An Error occured : {e}','danger')
            return render_template('create_parking_lot.html',
                 prime_location_name=prime_location,
                 price_per_unit_time=price,
                 address=address,
                 pin_code=pin_code,
                 maximum_number_of_spots=maximum_no_of_spots)
    return render_template('create_parking_lot.html')

@app.route('/admin/parking_lot/edit/<int:lot_id>', methods=['GET','POST'])
@login_required
def edit_parking_lot(lot_id):
    if not isinstance(current_user, Admin):
        flash('You must be an administrator to access this page.','danger')
        return redirect(url_for('user_dashboard'))
    
    parking_lot = ParkingLot.query.get_or_404(lot_id)

    if request.method == 'POST':
        try:
            original_max_spots = parking_lot.maximum_number_of_spots

            parking_lot.prime_location_name = request.form['prime_location_name']
            parking_lot.price_per_unit_time = float(request.form['price_per_unit_time'])
            parking_lot.address = request.form['address']
            parking_lot.pin_code = request.form['pin_code']
            parking_lot.maximum_number_of_spots = int(request.form['maximum_number_of_spots'])

            db.session.commit()

            new_max_spots = parking_lot.maximum_number_of_spots
            if new_max_spots > original_max_spots:
                for i in range(original_max_spots + 1, new_max_spots + 1):
                    spot = ParkingSpot(lot_id=parking_lot.id, spot_number=i, status='available')
                    db.session.add(spot)
                flash(f'Added {new_max_spots - original_max_spots} new parking spots','info')
            elif new_max_spots < original_max_spots:
                spots_to_delete = ParkingSpot.query.filter_by(lot_id=parking_lot.id).filter(ParkingSpot.spot_number>new_max_spots).all()

                for spot in spots_to_delete:
                    if spot.status in ['occupied','reserved']:
                        flash(f'Warning: Spot {spot.spot_number} was {spot.status} and will be deleted. Ensure no active reservations/occupancies on deleted spots.','warning')
                    db.session.delete(spot)
                flash(f'Removed {original_max_spots - new_max_spots} parking spots.','info')
            
            db.session.commit()

            flash('Parking lot updated successfully!','success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during parking lot update: {e}','danger')
    return render_template('edit_parking_lot.html',parking_lot=parking_lot)



# Database intialisation & admin seeding/ creation.
def create_db_and_seed_admin():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database tables created.")

        # Seed predefined admin if not exists
        if not Admin.query.filter_by(email_id='admin@example.com').first():
            # Use the specified fields for the admin
            admin_user = Admin(
                email_id='admin@example.com', # Standard admin email
                fullname='System Administrator',
                address='Admin HQ, 123 Main St',
                pin_code='110001' # Pin code as String
            )
            admin_user.set_password('superadminpass') # Stronger default password for admin! CHANGE THIS IN PRODUCTION!
            db.session.add(admin_user)
            db.session.commit()
            print("Predefined admin user created: admin@example.com / superadminpass")
        else:
            print("Admin user already exists.")
# Run the Application
if __name__=='__main__':
    create_db_and_seed_admin()
    app.run(debug=True)