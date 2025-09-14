from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, Admin, ParkingLot, ParkingSpot, Reservation
from datetime import datetime, timezone, timedelta

# Create a Blueprint to organize routes
main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('home.html')

@main.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        if isinstance(current_user, Admin):
            return redirect(url_for('main.admin_dashboard'))
        else:
            return redirect(url_for('main.user_dashboard'))
    
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
                return redirect(url_for('main.login'))
            except Exception as e:
                db.session.rollback()
                flash(f'An error occured during registration. Please try again. ({e})','danger')
                return render_template('register.html',email=email,fullname=fullname,address=address,pin_code=pin_code)
    return render_template('register.html')


@main.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.','info')
        if isinstance(current_user,Admin):
            return redirect(url_for('main.admin_dashboard'))
        else:
            return redirect(url_for('main.user_dashboard'))
    
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
                return redirect(url_for('main.admin_dashboard'))
            else:
                return redirect(url_for('main.user_dashboard'))
        
        else:
            flash('Login Failed. Check email or password','danger')
            return render_template('login.html',email=email )
        
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.','info')
    return redirect(url_for('main.home'))

@main.route('/user_dashboard')
@login_required
def user_dashboard():
    if isinstance(current_user,Admin):
        flash('Admin cannot access user dashboard directly','danger')
        return redirect(url_for('main.admin_dashboard'))
    
    current_spot = ParkingSpot.query.filter(
        (ParkingSpot.user_id == current_user.id) &
        ((ParkingSpot.status == 'occupied') | (ParkingSpot.status == 'reserved'))
    ).first()

    current_reservation = None
    if current_spot:
        current_reservation = Reservation.query.filter_by(
            user_id=current_user.id,
            spot_id=current_spot.id,
            leaving_timestamp=None
        ).order_by(Reservation.parking_timestamp.desc()).first()

    return render_template('user_dashboard.html', current_spot=current_spot, current_reservation=current_reservation)

@main.route('/user/parking_lots')
@login_required
def user_view_parking_lots():
    if isinstance(current_user,Admin):
        flash('Admin cannot access user dashboard directly.','danger')
        return redirect(url_for('main.admin_dashboard'))
    
    parking_lots = ParkingLot.query.all()

    parking_lot_data = []
    for lot in parking_lots:
        available_spots_count = ParkingSpot.query.filter_by(lot_id=lot.id, status='available').count()
        total_spots_created = len(lot.spots)

        parking_lot_data.append({
            'lot_id': lot.id,
            'prime_location_name': lot.prime_location_name,
            'address': lot.address,
            'pin_code': lot.pin_code,
            'price_per_unit_time': lot.price_per_unit_time,
            'total_capacity': lot.maximum_number_of_spots,
            'total_spots_created': total_spots_created,
            'available_spots': available_spots_count
        })

    return render_template('user_view_parking_lots.html', parking_lot_data=parking_lot_data)

@main.route('/user/reserve_spot/<int:lot_id>', methods=['POST'])
@login_required
def reserve_spot(lot_id):
    if isinstance(current_user, Admin):
        flash('Admins cannot reserve spots.','danger')
        return redirect(url_for('main.admin_dashboard'))
    
    existing_occupied_spot = ParkingSpot.query.filter_by(user_id=current_user.id, status='occupied').first()
    existing_reserved_spot = ParkingSpot.query.filter_by(user_id=current_user.id, status='reserved').first()

    if existing_occupied_spot:
        flash(f'You currently occupy spot {existing_occupied_spot.spot_number} in {existing_occupied_spot.parking_lot.prime_location_name}. Please release it first.','warning')
        return redirect(url_for('main.user_dashboard'))
    
    if existing_reserved_spot:
        flash(f'You already have spot {existing_reserved_spot.spot_number} in {existing_reserved_spot.parking_lot.prime_location_name} reserved. Please occupy or release it','warning')
        return redirect(url_for('main.user_dashboard'))
    
    parking_lot = ParkingLot.query.get_or_404(lot_id)

    available_spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='available').order_by(ParkingSpot.spot_number.asc()).first()

    if available_spot:
        try:
            available_spot.status = 'reserved'
            available_spot.user_id = current_user.id

            new_reservation = Reservation(
                spot_id=available_spot.id,
                user_id=current_user.id,
                parking_timestamp=datetime.now(),
                parking_cost_per_unit_time=parking_lot.price_per_unit_time
            )
            db.session.add(new_reservation)
            db.session.commit()

            flash(f'Spot {available_spot.spot_number} in {parking_lot.prime_location_name} has been reserved for you!','success')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occured during reservation: {e}','danger')
    else:
        flash(f'No available spots found in {parking_lot.prime_location_name}. Please try another lot.','warning')

    return redirect(url_for('main.user_view_parking_lots'))
    
@main.route('/user/occupy_spot/<int:spot_id>',methods=['POST'])
@login_required
def occupy_spot(spot_id):
    if isinstance(current_user, Admin):
        flash('Admin cannot occupy spots.','danger')
        return redirect(url_for('main.admin_dashboard'))
    
    spot=ParkingSpot.query.get_or_404(spot_id)

    if spot.status == 'reserved' and spot.user_id == current_user.id:
        try:
            spot.status = 'occupied'

            current_reservation=Reservation.query.filter_by(
                spot_id=spot.id,
                user_id=current_user.id,
                leaving_timestamp=None
            ).order_by(Reservation.parking_timestamp.desc()).first()

            if current_reservation:
                current_reservation.parking_timestamp=datetime.now()
                db.session.commit()
                flash(f'Spot {spot.spot_number} in {spot.parking_lot.prime_location_name} is now occupied','success')
            else:
                flash('Error: No active reservation found for this spot.','danger')
                db.session.rollback()
        except Exception as e:
            db.session.rollback()
            flash(f'An error occured while occupying the spot: {e}','danger')
    elif spot.status == 'occupied' and spot.user_id == current_user.id:
        flash(f'Spot {spot.spot_number} is already occupied by you.','info')
    else:
        flash(f'Spot {spot.spot_number} cannot be occupied. It is not reserved by you or is unavailable.','warning')
    return redirect(url_for('main.user_dashboard'))

@main.route('/user/release_spot/<int:spot_id>',methods=['POST'])
@login_required
def release_spot(spot_id):
    if isinstance(current_user, Admin):
        flash('Administrators cannot release spots.','danger')
        return redirect(url_for('main.admin_dashboard'))
    
    spot = ParkingSpot.query.get_or_404(spot_id)

    if spot.status == 'occupied' and spot.user_id == current_user.id:
        try:
            spot.status='available'
            spot.user_id=None

            current_reservation=Reservation.query.filter_by(
                spot_id=spot.id,
                user_id=current_user.id,
                leaving_timestamp=None
            ).order_by(Reservation.parking_timestamp.desc()).first()

            if current_reservation:
                current_reservation.leaving_timestamp=datetime.now()
                db.session.commit()
                flash(f'Spot {spot.spot_number} in {spot.parking_lot.prime_location_name} has been released.','success')
            else:
                flash('Error: No active reservation found to release for this spot.','danger')
                db.session.rollback()
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while releasing the spot: {e}','danger')
    else:
        flash(f'Spot {spot.spot_number} cannot be released. It is not occupied by you.','warning')
    return redirect(url_for('main.user_dashboard'))

@main.route('/user/parking_history')
@login_required
def user_parking_history():
    if isinstance(current_user, Admin):
        flash('Administrator do not have parking history.','danger')
        return redirect(url_for('main.admin_dashboard'))
    
    user_reservations = Reservation.query.filter_by(user_id=current_user.id).order_by(Reservation.parking_timestamp.desc()).all()

    history_data = []
    for res in user_reservations:
        spot = ParkingSpot.query.get(res.spot_id)
        lot_name = 'N/A'
        spot_number = 'N/A'
        if spot:
            lot_name=spot.parking_lot.prime_location_name
            spot_number=spot.spot_number

        duration_str = 'N/A'
        total_cost = 'N/A'

        if res.leaving_timestamp:
            duration=res.leaving_timestamp - res.parking_timestamp
            total_seconds=int(duration.total_seconds())
            total_minutes = total_seconds / 60.0 
            total_cost_value = total_minutes * res.parking_cost_per_unit_time 
            total_cost = f"₹{total_cost_value:.2f}" 

            hours=total_seconds//3600
            minutes=(total_seconds % 3600) // 60
            seconds=total_seconds % 60
            
            duration_parts = []
            if hours > 0:
                duration_parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
            if minutes > 0:
                duration_parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
            if seconds > 0 and (not hours and not minutes or (hours > 0 or minutes > 0)):
                duration_parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")
            
            duration_str = ", ".join(duration_parts) if duration_parts else "Less than a minute"
            
        history_data.append({
            'reservation_id': res.id,
            'lot_name': lot_name,
            'spot_number': spot_number,
            'parking_timestamp': res.parking_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'leaving_timestamp': res.leaving_timestamp.strftime('%Y-%m-%d %H:%M:%S') if res.leaving_timestamp else 'Current',
            'duration': duration_str,
            'cost_per_unit_time': f"₹{res.parking_cost_per_unit_time:.2f} / minute",
            'total_cost': total_cost
        })

    return render_template('user_parking_history.html', history_data=history_data)

@main.route('/admin/all_reservations')
@login_required
def admin_all_reservations():
    if not isinstance(current_user, Admin):
        flash('You must be an administrator to access this page.','danger')
        return redirect(url_for('main.user_dashboard'))
    
    all_reservations = Reservation.query.order_by(Reservation.parking_timestamp.desc()).all()

    all_reservations_data = []
    for res in all_reservations:
        spot = ParkingSpot.query.get(res.spot_id)
        user = User.query.get(res.user_id)

        lot_name = 'N/A'
        spot_number = 'N/A'
        user_email = 'N/A'

        if spot:
            lot_name = spot.parking_lot.prime_location_name
            spot_number = spot.spot_number

        if user:
            user_email = user.email_id

        duration_str = 'N/A'
        total_cost = 'N/A'

        if res.leaving_timestamp:
            duration = res.leaving_timestamp - res.parking_timestamp 
            total_seconds = int(duration.total_seconds())
            
            total_minutes = duration.total_seconds() / 60.0
            total_cost_value = total_minutes * res.parking_cost_per_unit_time
            total_cost = f"₹{total_cost_value:.2f}"

            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            duration_parts = []

            if hours > 0:
                duration_parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
            if minutes > 0:
                duration_parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
            if seconds > 0 and (not hours and not minutes or (hours > 0 or minutes > 0)):
                duration_parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")
             
            duration_str = ", ".join(duration_parts) if duration_parts else "Less than a minute." 
            
        all_reservations_data.append({
            'reservation_id': res.id,
            'user_email': user_email,
            'lot_name': lot_name,
            'spot_number': spot_number,
            'parking_timestamp': res.parking_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'leaving_timestamp': res.leaving_timestamp.strftime('%Y-%m-%d %H:%M:%S') if res.leaving_timestamp else 'Current',
            'duration': duration_str,
            'cost_per_unit_time': f"₹{res.parking_cost_per_unit_time:.2f} / minute",
            'total_cost': total_cost
        })
    
    return render_template('admin_all_reservations.html', all_reservations_data=all_reservations_data)
    

@main.route('/admin/users')
@login_required
def admin_view_users():
    if not isinstance(current_user, Admin):
        flash('You must be an administrator to access this page.','danger')
        return redirect(url_for('main.user_dashboard'))
    
    all_users = User.query.order_by(User.id.asc()).all()

    return render_template('admin_view_users.html', all_users_data=all_users)


@main.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not isinstance(current_user, Admin):
        flash('You must be administrator to access this page.','danger')
        return redirect(url_for('main.user_dashboard'))
    
    parking_lots = ParkingLot.query.all()

    lot_summaries = []
    for lot in parking_lots:
        total_spots_created = len(lot.spots)
        occupied_spots = len([s for s in lot.spots if s.status == 'occupied'])
        available_spots = len([s for s in lot.spots if s.status == 'available'])
        reserved_spots = len([s for s in lot.spots if s.status == 'reserved'])

        lot_summaries.append({
            'lot_id': lot.id,
            'prime_location_name': lot.prime_location_name,
            'address': lot.address,
            'maximum_number_of_spots': lot.maximum_number_of_spots,
            'total_spots_created': total_spots_created,
            'occupied_spots': occupied_spots,
            'available_spots': available_spots,
            'reserved_spots': reserved_spots,
            'price_per_unit_time': lot.price_per_unit_time,
            'pin_code': lot.pin_code
        })
    
    return render_template('admin_dashboard.html',lot_summaries=lot_summaries)

@main.route('/admin/parking_lot/create', methods = ['GET','POST'])
@login_required
def create_parking_lot():
    if not isinstance(current_user, Admin):
        flash('You must be administrator to access this page.','danger')
        return redirect(url_for('main.user_dashboard'))
    
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
            return redirect(url_for('main.admin_dashboard'))
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

@main.route('/admin/parking_lot/edit/<int:lot_id>', methods=['GET','POST'])
@login_required
def edit_parking_lot(lot_id):
    if not isinstance(current_user, Admin):
        flash('You must be an administrator to access this page.','danger')
        return redirect(url_for('main.user_dashboard'))
    
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
            return redirect(url_for('main.admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during parking lot update: {e}','danger')
    return render_template('edit_parking_lot.html',parking_lot=parking_lot)

@main.route('/admin/parking_lot/delete/<int:lot_id>', methods=['POST'])
@login_required
def delete_parking_lot(lot_id):
    if not isinstance(current_user, Admin):
        flash('You must be an administrator to access this page.','danger')
        return redirect(url_for('main.user_dashboard'))
    
    parking_lot = ParkingLot.query.get_or_404(lot_id)

    try:
        db.session.delete(parking_lot)
        db.session.commit()
        flash(f'Parking lot "{parking_lot.prime_location_name}" and all its spots and reservations have been deleted successfully','success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occured during parking lot deletion: {e}','danger')

    # Ensure a redirect happens even if an exception occurs
    return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/parking_lot/<int:lot_id>/spot')
@login_required
def view_parking_spot(lot_id):
    if not isinstance(current_user, Admin):
        flash('You must be an administrator to access this page.','danger')
        return redirect(url_for('main.user_dashboard'))

    parking_lot = ParkingLot.query.get_or_404(lot_id)
    parking_spots = ParkingSpot.query.filter_by(lot_id=lot_id).order_by(ParkingSpot.spot_number.asc()).all()

    spots_data = []
    for spot in parking_spots:
        user_email = "N/A"
        
        if spot.user_id:
            if spot.occupied_by_user:
                user_email = spot.occupied_by_user.email_id
            else:
                user_email = "User not found"

        spots_data.append({
            'spot_id': spot.id,
            'spot_number': spot.spot_number,
            'status': spot.status,
            'occupied_by': user_email,
        })

    return render_template('view_parking_spot.html',
                           parking_lot=parking_lot, 
                           spots_data=spots_data)

# --- Database Initialization and Admin Seeding ---