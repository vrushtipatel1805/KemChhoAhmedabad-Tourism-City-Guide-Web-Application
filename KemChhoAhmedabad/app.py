# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import uuid  # To generate unique transaction IDs

app = Flask(__name__)
app.secret_key = 'kem_chho_ahmedabad_secret_key'  # Change for production

# --- DATABASE CONFIGURATION ---
basedir = os.path.abspath(os.path.dirname(__file__))
# Note: Deleting the old DB file is recommended to apply new schema changes
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'kemchho.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- IMAGE SERVING ROUTE ---
@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(os.path.join(basedir, 'images'), filename)

db = SQLAlchemy(app)

# --- 1. USERS TABLE ---
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user') # 'admin', 'user'
    phone = db.Column(db.String(20), nullable=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships to access bookings easily
    photoshoots = db.relationship('PhotoshootBooking', backref='customer', lazy=True)
    rides = db.relationship('RideBooking', backref='rider', lazy=True)

# --- 2. DRIVERS TABLE (UPDATED) ---
class Driver(db.Model):
    __tablename__ = 'drivers'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False) # Added Email field
    phone = db.Column(db.String(20), nullable=True)
    car_model = db.Column(db.String(100), nullable=True)
    car_number = db.Column(db.String(20), nullable=True)
    license_number = db.Column(db.String(50), nullable=True) # Added
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    password = db.Column(db.String(100), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    rating = db.Column(db.Float, default=5.0) # Added
    total_completed_rides = db.Column(db.Integer, default=0) # Added
    
    # Relationship to rides
    rides = db.relationship('RideBooking', backref='driver', lazy=True)

# --- 3. PHOTOSHOOT BOOKINGS TABLE ---
# --- 3. PHOTOSHOOT BOOKINGS TABLE (Updated) ---
class Photographer(db.Model):
    __tablename__ = 'photographers'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    total_shoots = db.Column(db.Integer, default=0)
    # Relationship
    bookings = db.relationship('PhotoshootBooking', backref='assigned_photographer', lazy=True)

class PhotoshootBooking(db.Model):
    __tablename__ = 'photoshoot_bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    location_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    
    # Photographer Assignment
    photographer_id = db.Column(db.Integer, db.ForeignKey('photographers.id'), nullable=True)
    
    date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_status = db.Column(db.String(20), default='Pending') # Payment Status
    status = db.Column(db.String(20), default='PENDING_APPROVAL') # Lifecycle: PENDING_APPROVAL -> CONFIRMED -> COMPLETED

# --- 4. RIDE BOOKINGS TABLE ---
class RideBooking(db.Model):
    __tablename__ = 'ride_bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=True) # Added for Driver assignment
    
    source = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(500), nullable=True) # Stores stops as text
    distance = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    
    date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_status = db.Column(db.String(20), default='Pending')
    
    # Lifecycle Status: REQUESTED -> ACCEPTED -> ONGOING -> COMPLETED (Added for Driver flow)
    status = db.Column(db.String(20), default='REQUESTED')

# --- 5. PAYMENTS TABLE ---
class Payment(db.Model):
    __tablename__ = 'payments'
    payment_id = db.Column(db.Integer, primary_key=True)
    # We store the ID of the booking (Ride or Photoshoot)
    booking_id = db.Column(db.Integer, nullable=False) 
    # 'Ride' or 'Photoshoot' to know which table to look up
    booking_type = db.Column(db.String(20), nullable=False) 
    payment_method = db.Column(db.String(20), nullable=False) # 'Card', 'UPI', 'Cash'
    amount = db.Column(db.Float, nullable=False)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    payment_status = db.Column(db.String(20), default='Success')
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

# --- HELPER FUNCTIONS ---
def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def get_current_driver():
    if 'driver_id' in session:
        return Driver.query.get(session['driver_id'])
    return None

# --- INITIALIZE DATABASE ---
with app.app_context():
    db.create_all()
    # Create a dummy driver for testing if none exists
    if not Driver.query.filter_by(username='driver1').first():
        driver = Driver(username='driver1', email='driver1@test.com', password='password123')
        db.session.add(driver)
    
    # Create dummy photographer
    if not Photographer.query.first():
        p1 = Photographer(username='LensMaster', password='password123', phone='9876543210')
        db.session.add(p1)
    
    db.session.commit()

# --- STATIC DATA (Updated Photoshoot Locations) ---
photoshoot_locations = [
    {
        "id": 1, 
        "name": "La Fabuloso", 
        "price": "65000", 
        "description": "Experience ultimate luxury and elegance for your wedding shoot.", 
        "image": "lafabuloso.jpg"
    },
    {
        "id": 2, 
        "name": "Riverfront Flower Park", 
        "price": "50000", 
        "description": "Vibrant floral backdrops with skyline views.", 
        "image": "riverfront.jpg"
    },
    {
        "id": 3, 
        "name": "Parimal Garden", 
        "price": "40000", 
        "description": "Lush greenery and serene environment for natural shots.", 
        "image": "parimal.jpg"
    },
    {
        "id": 4, 
        "name": "Adalaj Stepwell", 
        "price": "40000", 
        "description": "Ancient architecture with intricate carvings.", 
        "image": "adalaj.jpg"
    },
    {
        "id": 5, 
        "name": "Thol", 
        "price": "25000", 
        "description": "Wild beauty and lake-side views for the adventurous souls.", 
        "image": "thol.jpg"
    },
    {
        "id": 6, 
        "name": "Vintage Car Museum", 
        "price": "48000", 
        "description": "Add a touch of classic royalty with vintage car collections.", 
        "image": "vintagecar.jpg"
    }
]

# --- BEFORE REQUEST (Update Last Seen) ---
@app.before_request
def update_last_seen():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            user.last_seen = datetime.utcnow()
            db.session.commit()
    if 'driver_id' in session:
        driver = Driver.query.get(session['driver_id'])
        if driver:
            driver.last_seen = datetime.utcnow()
            db.session.commit()

# --- ROUTES ---

@app.route('/')
def root():
    if 'user_id' in session: return redirect(url_for('home'))
    if 'driver_id' in session: return redirect(url_for('driver_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'user') # 'user' or 'driver'

        if role == 'driver':
            # Driver Login Logic
            email = request.form.get('email')
            driver = Driver.query.filter_by(email=email).first() 
            if driver and driver.password == password:
                session['driver_id'] = driver.id
                session['role'] = 'driver'
                return redirect(url_for('driver_dashboard'))
            else:
                return "Invalid Driver Credentials"
        elif role == 'photographer':
            # Photographer Login Logic
            username = request.form.get('username') or request.form.get('email')
            if username:
                username = username.strip()
            
            password = request.form.get('password', '').strip()
            
            photographer = Photographer.query.filter_by(username=username).first()
            if photographer and photographer.password == password:
                session['photographer_id'] = photographer.id
                session['username'] = photographer.username
                session['role'] = 'photographer'
                return redirect(url_for('photographer_dashboard'))
            else:
                return f"Invalid Photographer Credentials. Received: {username}"
        else:
            # User Login Logic
            email = request.form.get('email')
            user = User.query.filter_by(email=email).first()
            if user and user.password == password:
                session['user_id'] = user.user_id # Note: user_id vs id
                session['username'] = user.username
                session['role'] = user.role
                
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('home'))
            else:
                return "Invalid User Credentials"
            
    return render_template('login1.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form.get('role', 'user')

        # Phone and Car details
        phone = request.form.get('phone')
        car_model = request.form.get('car_model')
        car_number = request.form.get('car_number')

        if password != confirm_password:
            return "Passwords do not match!"
        
        # Check if email exists in EITHER table to verify uniqueness
        if User.query.filter_by(email=email).first() or Driver.query.filter_by(email=email).first():
            return "Email already registered! Please login."

        if role == 'driver':
            new_driver = Driver(username=username, email=email, password=password, phone=phone, car_model=car_model, car_number=car_number)
            db.session.add(new_driver)
            db.session.commit()
        elif role == 'photographer':
            # Photographer Signup
            if Photographer.query.filter_by(username=username).first():
                 return "Username already taken for Photographer!"
            
            new_photographer = Photographer(username=username, password=password, phone=phone)
            db.session.add(new_photographer)
            db.session.commit()
        else:
            # Create User or Admin
            new_user = User(username=username, email=email, password=password, role=role, phone=phone)
            db.session.add(new_user)
            db.session.commit()
        
        return redirect(url_for('login'))
        
    return render_template('signup1.html')

@app.route('/photographer/login', methods=['GET', 'POST'])
def photographer_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        photographer = Photographer.query.filter_by(username=username).first()
        if photographer and photographer.password == password:
            session['photographer_id'] = photographer.id
            session['username'] = photographer.username # Basic display
            session['role'] = 'photographer'
            return redirect(url_for('photographer_dashboard'))
        else:
            return render_template('login1.html', role='photographer', error="Invalid Photographer Credentials")
            
    return render_template('login1.html', role='photographer')



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- MAIN PAGES ---

@app.route('/home')
def home():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # Check for active ride to show status (Optional: if you want to show active ride on home)
    current_ride = RideBooking.query.filter_by(user_id=session['user_id']).filter(RideBooking.status.in_(['REQUESTED', 'ACCEPTED', 'ONGOING'])).first()
    
    return render_template('home.html', username=session['username'], active_ride=current_ride)

@app.route('/info')
def info():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('Ahmedabad_info_page.html', username=session['username'])

# --- RIDE BOOKING LOGIC ---

@app.route('/customise')
def customise():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # RESTRICTION: Cannot book if already has active ride
    # active_ride = RideBooking.query.filter_by(user_id=session['user_id']).filter(RideBooking.status.in_(['REQUESTED', 'ACCEPTED', 'ONGOING'])).first()
    # if active_ride:
    #    return f"<h1>You have an active ride ({active_ride.status}). Please complete it first.</h1><a href='/home'>Back Home</a>"

    return render_template('customise.html', username=session['username'])

@app.route('/save_booking', methods=['POST'])
def save_booking():
    if 'user_id' not in session: return jsonify({'status': 'error', 'message': 'Not logged in'})
    
    # FIX: Clear any old confirmed booking so it doesn't show up on the receipt page
    session.pop('confirmed_booking', None)
    
    data = request.json
    # Clean price string (remove '₹' and spaces) to store as Integer
    try:
        clean_price = int(str(data.get('price')).replace('₹', '').replace(',', '').strip())
    except:
        clean_price = 0

    stops = data.get('stops')
    if isinstance(stops, list):
        stops_str = ", ".join(stops)
    else:
        stops_str = str(stops)

    session['pending_booking'] = {
        'type': 'ride',
        'start': data.get('start'),
        'stops': stops_str, 
        'distance': data.get('distance'),
        'price': clean_price
    }
    return jsonify({'status': 'success'})

# --- PHOTOSHOOT BOOKING LOGIC ---

@app.route('/photoshoot')
def photoshoot():
    if 'user_id' not in session: return redirect(url_for('login'))
    photographers = Photographer.query.all()
    return render_template('photoshoot.html', locations=photoshoot_locations, photographers=photographers)

@app.route('/save_photoshoot_booking', methods=['POST'])
def save_photoshoot_booking():
    if 'user_id' not in session: return jsonify({'status': 'error'})
    
    # FIX: Clear any old confirmed booking so it doesn't show up on the receipt page
    session.pop('confirmed_booking', None)
    
    data = request.json
    # Clean price string
    try:
        clean_price = int(str(data.get('price')).replace('₹', '').replace(',', '').strip())
    except:
        clean_price = 0

    session['pending_booking'] = {
        'type': 'photoshoot',
        'location_name': data.get('location_name'),
        'price': clean_price,
        'photographer': data.get('photographer')
    }
    return jsonify({'status': 'success'})

# --- PAYMENT & CONFIRMATION LOGIC ---

@app.route('/onlinepay')
def onlinepay():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('onlinepayment.html')

@app.route('/process_payment', methods=['POST'])
def process_payment():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    booking_data = session.get('pending_booking')
    payment_method = 'Card' if request.form.get('card_number') else 'UPI'
    
    if booking_data:
        booking_id_ref = None
        
        # 0. CHECK FOR ACTIVE RIDES (USER RESTRICTION)
        existing_ride = RideBooking.query.filter_by(user_id=session['user_id']).filter(RideBooking.status.in_(['REQUESTED', 'ACCEPTED', 'ONGOING'])).first()
        if existing_ride:
            # User already has an active ride.
            # Ideally, redirect to status page or show flash message.
            # For now, let's redirect to 'conformbooking' which handles status polling.
            session['confirmed_booking'] = {
                'type': 'ride',
                'start': existing_ride.source,
                'stops': existing_ride.destination, # Should parse back to list if needed, but display logic handles it
                'distance': existing_ride.distance,
                'price': existing_ride.price,
                'id': existing_ride.id
            }
            return redirect(url_for('conformbooking'))

        # 1. SAVE BOOKING TO DATABASE
        if booking_data['type'] == 'ride':
            new_ride = RideBooking(
                user_id=session['user_id'],
                source=booking_data['start'],
                destination=booking_data['stops'],
                distance=booking_data['distance'],
                price=booking_data['price'],
                payment_status='Paid',
                status='REQUESTED' # Explicitly set status for Driver visibility
            )
            db.session.add(new_ride)
            db.session.flush() # Flush to get the ID before commit
            booking_id_ref = new_ride.id
            session['current_ride_id'] = new_ride.id # For tracking
            
        elif booking_data['type'] == 'photoshoot':
            # Look up photographer by name (username) if provided
            photographer_name = booking_data.get('photographer')
            photographer_obj = Photographer.query.filter_by(username=photographer_name).first() if photographer_name else None
            
            new_shoot = PhotoshootBooking(
                user_id=session['user_id'],
                location_name=booking_data['location_name'],
                # photographer=booking_data['photographer'], # INVALID FIELD
                photographer_id=photographer_obj.id if photographer_obj else None,
                price=booking_data['price'],
                payment_status='Paid',
                status='PENDING_APPROVAL' # User requested waiting for approval even for online payments 
            )
            db.session.add(new_shoot)
            db.session.flush()
            booking_id_ref = new_shoot.id
        
        # 2. SAVE PAYMENT TO DATABASE
        # Generate a unique transaction ID like "TXN-12345-AB"
        txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        
        new_payment = Payment(
            booking_id=booking_id_ref,
            booking_type=booking_data['type'],
            payment_method=payment_method,
            amount=float(booking_data['price']),
            transaction_id=txn_id,
            payment_status='Success'
        )
        db.session.add(new_payment)

        # 3. COMMIT ALL CHANGES
        db.session.commit()
        
        # 4. Move to confirmed session
        booking_data['id'] = booking_id_ref
        session['confirmed_booking'] = booking_data
        session.pop('pending_booking', None)
        
        return redirect(url_for('conformbooking'))
    
    return redirect(url_for('home'))

@app.route('/conformbooking')
def conformbooking():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # 1. Check for Confirmed Booking (From Online Payment)
    raw_booking = session.get('confirmed_booking')
    
    # 2. CASH PAYMENT LOGIC (User skipped Payment Page):
    # If there is no confirmed booking, but there is a pending one,
    # it means the user clicked "Cash" in JS and bypassed /process_payment.
    if not raw_booking and session.get('pending_booking'):
        booking_data = session.get('pending_booking')
        booking_id_ref = None
        
        # Save Booking (Cash Logic)
        if booking_data['type'] == 'ride':
            
            # RACE CONDITION / RE-CHECK: User Restriction
            existing_ride = RideBooking.query.filter_by(user_id=session['user_id']).filter(RideBooking.status.in_(['REQUESTED', 'ACCEPTED', 'ONGOING'])).first()
            if existing_ride:
                 session['current_ride_id'] = existing_ride.id
                 # Don't create new one, just use existing
                 booking_id_ref = existing_ride.id
            else:
                new_ride = RideBooking(
                    user_id=session['user_id'],
                    source=booking_data['start'],
                    destination=booking_data['stops'],
                    distance=booking_data['distance'],
                    price=booking_data['price'],
                    payment_status='Pending', # Cash to be collected
                    status='REQUESTED' # Explicitly set status for Driver visibility
                )
                db.session.add(new_ride)
                db.session.flush()
                booking_id_ref = new_ride.id
                session['current_ride_id'] = new_ride.id
                
        elif booking_data['type'] == 'photoshoot':
            # Assign to a photographer (Round Robin or Random or Specific if UI allows)
            # For now, assign to the first available photographer or leave None for manual assignment?
            # Requirement: "The request must be sent to the Photographer/Driver Panel... Do NOT auto-confirm."
            # We will assign to a default photographer for demo, or leave null. 
            # Let's assign to the first available one to show it in their panel.
            photographer = Photographer.query.filter_by(is_available=True).first()
            p_id = photographer.id if photographer else None
            
            new_shoot = PhotoshootBooking(
                user_id=session['user_id'],
                location_name=booking_data['location_name'],
                price=booking_data['price'],
                photographer_id=p_id,
                payment_status='Pending',
                status='PENDING_APPROVAL'
            )
            db.session.add(new_shoot)
            db.session.flush()
            booking_id_ref = new_shoot.id
            
        # Create Cash Payment Record
        txn_id = f"CASH-{uuid.uuid4().hex[:8].upper()}"
        new_payment = Payment(
            booking_id=booking_id_ref,
            booking_type=booking_data['type'],
            payment_method='Cash',
            amount=float(booking_data['price']),
            transaction_id=txn_id,
            payment_status='Pending'
        )
        db.session.add(new_payment)
        db.session.commit()
        
        # Promote Pending to Confirmed for Display
        booking_data['id'] = booking_id_ref
        session['confirmed_booking'] = booking_data
        session.pop('pending_booking', None)
        raw_booking = booking_data

    # If still no booking (User refreshed without a session), go home
    if not raw_booking:
        return redirect(url_for('home'))
    
    # 3. Format Data for Template
    formatted_booking = {}
    if raw_booking.get('type') == 'ride':
        stops_data = raw_booking['stops']
        # Helper to clean up the string list representation from DB
        if isinstance(stops_data, str) and stops_data.startswith('['):
            stops_data = stops_data.replace('[','').replace(']','').replace("'", "").split(',')

        formatted_booking = {
            'type': 'ride',
            'id': session.get('current_ride_id'), # Pass ID for polling
            'start_location': raw_booking['start'],
            'stops': stops_data,
            'distance': raw_booking['distance'],
            'price': raw_booking['price'],
            'status': 'REQUESTED' # Helper for UI
        }
    elif raw_booking.get('type') == 'photoshoot':
        formatted_booking = {
            'type': 'photoshoot',
            'id': raw_booking.get('id'), # Pass ID for polling
            'location_name': raw_booking['location_name'],
            'photographer': raw_booking['photographer'],
            'price': raw_booking['price'],
            'package_includes': ["Next-day Pickup", "4-Hour Coverage", "Assistance Team"]
        }

    return render_template('conformbooking.html', username=session['username'], booking=formatted_booking)

# --- DRIVER DASHBOARD & API (MERGED FROM NEW APP) ---

@app.route('/driver/dashboard')
def driver_dashboard():
    if 'driver_id' not in session: return redirect(url_for('login'))
    driver = Driver.query.get(session['driver_id'])
    return render_template('driver_panel.html', driver=driver)

# API: Get list of available rides (Polling Endpoint)
@app.route('/api/driver/available_rides')
def get_available_rides():
    if 'driver_id' not in session: return jsonify([]), 401
    
    # Fetch rides that are REQUESTED and have NO driver assigned
    # Mapping new API logic to Old 'RideBooking' model
    rides = RideBooking.query.filter_by(status='REQUESTED', driver_id=None).all()
    
    rides_data = []
    for r in rides:
        # NOTE: r.destination stores stops as string. r.source is pickup.
        # Clean stops if stored as list string
        stops_display = r.destination
        if stops_display and stops_display.startswith("['"):
             stops_display = stops_display.replace("['", "").replace("']", "").replace("', '", ", ")

        rides_data.append({
            'id': r.id,
            'customer': r.rider.username, # Access via relationship
            'pickup': r.source,
            'stops': stops_display,
            'fare': f"₹{r.price}",
            'distance': r.distance
        })
    return jsonify(rides_data)

# API: Get current active ride for this driver
@app.route('/api/driver/current_ride')
def get_current_ride():
    if 'driver_id' not in session: return jsonify(None), 401
    
    # Fetch ride assigned to this driver that is NOT completed
    ride = RideBooking.query.filter_by(driver_id=session['driver_id']).filter(RideBooking.status.in_(['ACCEPTED', 'ONGOING'])).first()
    
    if ride:
        # Clean stops if stored as list string
        stops_display = ride.destination
        if stops_display and stops_display.startswith("['"):
             stops_display = stops_display.replace("['", "").replace("']", "").replace("', '", ", ")

        return jsonify({
            'id': ride.id,
            'status': ride.status,
            'customer': ride.rider.username,
            'pickup': ride.source,
            'stops': stops_display,
            'fare': f"₹{ride.price}"
        })
    return jsonify(None)

# API: Get Driver History & Earnings
@app.route('/api/driver/history')
def get_driver_history():
    if 'driver_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    # Fetch all COMPLETED rides for this driver
    completed_rides = RideBooking.query.filter_by(driver_id=session['driver_id'], status='COMPLETED').order_by(RideBooking.date.desc()).all()
    
    total_earnings = sum(ride.price for ride in completed_rides)
    
    history_data = []
    for ride in completed_rides:
        history_data.append({
            'id': ride.id,
            'date': ride.date.strftime('%d %b, %I:%M %p'),
            'customer': ride.rider.username,
            'pickup': ride.source,
            'stops': ride.destination,
            'fare': ride.price
        })
        
    return jsonify({
        'total_earnings': total_earnings,
        'completed_rides': len(completed_rides),
        'history': history_data
    })

# API: Driver Actions (Accept, Start, Complete)
@app.route('/api/driver/update_ride', methods=['POST'])
def update_ride_status():
    if 'driver_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    ride_id = data.get('ride_id')
    action = data.get('action') # 'accept', 'start', 'complete'
    
    ride = RideBooking.query.get(ride_id)
    if not ride: return jsonify({'error': 'Ride not found'}), 404
    
    if action == 'accept':
        # DRIVER RESTRICTION: Check if driver already has an active ride
        active_driver_ride = RideBooking.query.filter_by(driver_id=session['driver_id']).filter(RideBooking.status.in_(['ACCEPTED', 'ONGOING'])).first()
        if active_driver_ride:
            return jsonify({'error': 'You already have an active ride. Complete it first.'}), 409

        ride.driver_id = session['driver_id']
        ride.status = 'ACCEPTED' # Confirmed
        
    elif action == 'reject':
        # Rejecting a ride cancels it (or we could re-open it for others, but requirements say "Rejected")
        # If we just set status to REJECTED, user sees it. 
        # But race condition: if multiple drivers see it? 
        # For now, let's assume 'Requested' means broadcast to all.
        # If one rejects, does it reject for everyone? 
        # Requirement: "Driver Rejects -> Status: Rejected"
        # We will set status to REJECTED.
        if ride.status == 'REQUESTED':
             ride.status = 'REJECTED'
             
             # REFUND LOGIC
             payment = Payment.query.filter_by(booking_id=ride.id, booking_type='ride').first()
             if payment and payment.payment_status == 'Success':
                 payment.payment_status = 'Refunded'
                 # payment.amount = 0 # Optional: maintain record but status handles it

        
    elif action == 'complete':
        # if ride.driver_id != session['driver_id']: return jsonify({'error': 'Unauthorized'}), 403
        ride.status = 'COMPLETED'
        
        # CASH PAYMENT UPDATE: Mark as Success so it counts in Revenue
        payment = Payment.query.filter_by(booking_id=ride.id, booking_type='ride').first()
        if payment and payment.payment_method == 'Cash':
             payment.payment_status = 'Success'
        
    db.session.commit()
    return jsonify({'status': 'success', 'new_status': ride.status})

@app.route('/api/ride_status/<int:ride_id>')
def check_ride_status(ride_id):
    ride = RideBooking.query.get(ride_id)
    if not ride: return jsonify({'status': 'Not Found'})
    
    # Return status and driver details if assigned
    driver_name = ride.driver.username if ride.driver else None
    driver_phone = ride.driver.phone if ride.driver else None
    car_model = ride.driver.car_model if ride.driver else None
    car_number = ride.driver.car_number if ride.driver else None
    
    return jsonify({
        'status': ride.status,
        'driver': {
            'name': driver_name,
            'phone': driver_phone,
            'car_model': car_model,
            'car_number': car_number
        }
    })

@app.route('/api/shoot_status/<int:shoot_id>')
def check_shoot_status(shoot_id):
    shoot = PhotoshootBooking.query.get(shoot_id)
    if not shoot: return jsonify({'status': 'Not Found'})
    
    photographer_name = shoot.assigned_photographer.username if shoot.assigned_photographer else None
    photographer_phone = shoot.assigned_photographer.phone if shoot.assigned_photographer else None
    
    return jsonify({
        'status': shoot.status,
        'photographer': {
            'name': photographer_name,
            'phone': photographer_phone
        }
    })


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    # --- REAL-TIME STATISTICS ---
    
    # 1. Active Rides (Requests, Accepted, Ongoing)
    active_count = RideBooking.query.filter(RideBooking.status.in_(['REQUESTED', 'ACCEPTED', 'ONGOING'])).count()
    
    # 2. Pending Photoshoots
    photoshoot_count = PhotoshootBooking.query.filter_by(status='PENDING_APPROVAL').count()
    
    # 3. Total Revenue (Completed Rides + Shoots)
    # Ideally sum amounts from Payment table where status='Success'
    total_rev = db.session.query(db.func.sum(Payment.amount)).filter(Payment.payment_status=='Success').scalar() or 0.0
    
    # 4. Users Online (Activity within last 5 minutes)
    five_mins_ago = datetime.utcnow() - timedelta(minutes=5)
    users_online = User.query.filter(User.last_seen >= five_mins_ago).count()
    
    # 5. Drivers Online (Activity within last 5 minutes)
    drivers_online = Driver.query.filter(Driver.last_seen >= five_mins_ago).count()
    
    # --- DIRECTORIES ---
    all_drivers = Driver.query.all()
    all_users = User.query.order_by(User.created_at.desc()).all()
    
    # Recent Rides for Table
    recent_rides = RideBooking.query.order_by(RideBooking.date.desc()).limit(10).all()
    
    # Recent Photoshoots for Table
    recent_shoots = PhotoshootBooking.query.order_by(PhotoshootBooking.date.desc()).all()

    return render_template('admin_panel.html', 
                           active_count=active_count,
                           photoshoot_count=photoshoot_count,
                           total_rev=round(total_rev, 2),
                           users_online=users_online,
                           drivers_online=drivers_online,
                           drivers=all_drivers,
                           all_users=all_users,
                           rides=recent_rides,
                           shoots=recent_shoots,
                           now=datetime.utcnow())

# --- ADMIN ACTIONS: DRIVER MANAGEMENT ---

@app.route('/admin/driver/delete/<int:driver_id>', methods=['POST'])
def delete_driver(driver_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    driver = Driver.query.get(driver_id)
    if driver:
        db.session.delete(driver)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/driver/toggle_status/<int:driver_id>', methods=['POST'])
def toggle_driver_status(driver_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    driver = Driver.query.get(driver_id)
    if driver:
        driver.is_available = not driver.is_available
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/assign_driver', methods=['POST'])
def assign_driver():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    ride_id = request.form.get('ride_id')
    driver_id = request.form.get('driver_id')
    
    ride = RideBooking.query.get(ride_id)
    if ride:
        ride.driver_id = driver_id
        ride.status = 'ACCEPTED' # Admin forces assignment -> Accepted? Or Assigned/Requested?
        # If Admin assigns, it might skip 'Accept' step by driver? 
        # For now, let's say 'ACCEPTED' so it shows up for driver as current ride?
        # Or keep 'REQUESTED' but assigned?
        # The API `get_available_rides` checks `driver_id=None`.
        # So setting `driver_id` removes it from available pool.
        # Logic says: `get_current_ride` checks `ACCEPTED` or `ONGOING`.
        # So we should set to `ACCEPTED`.
        ride.status = 'ACCEPTED'
        db.session.commit()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/shoot/approve/<int:shoot_id>', methods=['POST'])
def approve_shoot(shoot_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    shoot = PhotoshootBooking.query.get(shoot_id)
    if shoot:
        # Admin approves -> Moves to Photographer Pool
        shoot.status = 'WAITING_FOR_PHOTOGRAPHER'
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

# --- PHOTOGRAPHER PANEL ---

@app.route('/photographer/dashboard')
def photographer_dashboard():
    if 'photographer_id' not in session: return redirect(url_for('photographer_login'))
    photographer = Photographer.query.get(session['photographer_id'])
    return render_template('photographer_panel.html', photographer=photographer)

@app.route('/api/photographer/requests')
def photographer_requests():
    if 'photographer_id' not in session: return jsonify([])
        
    # Get all requests waiting for ANY photographer
    current_photographer_id = session['photographer_id']
    requests = PhotoshootBooking.query.filter_by(status='WAITING_FOR_PHOTOGRAPHER').all()
    
    data = []
    for req in requests:
        # If specific photographer was assigned during booking (nullable=True), filter?
        # If matches current photographer or is None (pool request)
        if req.photographer_id and req.photographer_id != current_photographer_id:
            continue
            
        user = User.query.get(req.user_id)
        data.append({
            'id': req.id,
            'location': req.location_name,
            'customer': user.username if user else "Unknown",
            'date': req.date.strftime('%d %b %Y'),
            'price': req.price
        })
        
    return jsonify(data)

@app.route('/api/photographer/active')
def photographer_active_job():
    if 'photographer_id' not in session: return jsonify(None)
        
    current_photographer = Photographer.query.get(session['photographer_id'])
    
    # Find confirmed job for this photographer
    active_job = PhotoshootBooking.query.filter_by(photographer_id=current_photographer.id, status='CONFIRMED').first()
    
    if active_job:
        user = User.query.get(active_job.user_id)
        return jsonify({
            'id': active_job.id,
            'location': active_job.location_name,
            'customer': user.username if user else "Unknown",
            'price': active_job.price
        })
    return jsonify(None)

@app.route('/api/photographer/action', methods=['POST'])
def photographer_action():
    if 'photographer_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    shoot_id = data.get('shoot_id')
    action = data.get('action') # accept, reject, complete
    
    shoot = PhotoshootBooking.query.get(shoot_id)
    if not shoot: return jsonify({'error': 'Not found'}), 404
    
    current_photographer = Photographer.query.get(session['photographer_id'])
    
    if action == 'accept':
        shoot.status = 'CONFIRMED'
        shoot.photographer_id = current_photographer.id
        current_photographer.is_available = False
        
    elif action == 'reject':
        # Rejecting the request cancels it for everyone
        shoot.status = 'REJECTED'
        shoot.photographer_id = None
        
        # REFUND LOGIC
        payment = Payment.query.filter_by(booking_id=shoot.id, booking_type='photoshoot').first()
        if payment and payment.payment_status == 'Success':
            payment.payment_status = 'Refunded'
             
    elif action == 'complete':
        shoot.status = 'COMPLETED'
        current_photographer.is_available = True
        current_photographer.total_shoots = (current_photographer.total_shoots or 0) + 1
        
        # CASH PAYMENT UPDATE: Mark as Success so it counts in Revenue
        payment = Payment.query.filter_by(booking_id=shoot.id, booking_type='photoshoot').first()
        if payment and payment.payment_method == 'Cash':
             payment.payment_status = 'Success'
        
    db.session.commit()
    return jsonify({'status': 'success'})


@app.route('/admin/shoot/reject/<int:shoot_id>', methods=['POST'])
def reject_shoot(shoot_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    shoot = PhotoshootBooking.query.get(shoot_id)
    if shoot:
        shoot.status = 'REJECTED'
        
        # REFUND LOGIC
        payment = Payment.query.filter_by(booking_id=shoot.id, booking_type='photoshoot').first()
        if payment and payment.payment_status == 'Success':
            payment.payment_status = 'Refunded'
            
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)