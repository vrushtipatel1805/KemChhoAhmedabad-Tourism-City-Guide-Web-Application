# KemChhoAhmedabad-Tourism-City-Guide-Web-Application
Kem Chho Ahmedabad is a full-stack web application designed to help users explore Ahmedabad, book photography services, and arrange local rides. The platform provides separate interfaces for users, photographers, drivers, and administrators, with booking, payment, and management features integrated into the system.

# Technologies Used
**Frontend:**	HTML5, CSS3, JavaScript, Bootstrap

**Backend:**	Python, Flask

**ORM:** Flask-SQLAlchemy

**Database:**	SQLite

**JavaScript Runtime / Package Manager:**	Node.js, npm

**Payment:**	Online Payment Integration

# Key Features
👤 User Registration & Login
🔐 Role-based Login
📍 Explore Ahmedabad Tourist Locations
📸 Photographer Search & Booking
📷 Photoshoot Package Selection
🚗 Local Ride Booking
👨‍💼 Driver Management
📅 Photoshoot & Ride Booking Management
💳 Payment Management
🧾 Transaction ID Generation
📊 Admin Dashboard
👥 User Management
📸 Photographer Management
🚘 Driver Management
🔄 Booking Status Tracking
⭐ Driver Rating & Ride Tracking
📱 Responsive Web Interface

# Project Structure
```text
Kem-Chho-Ahmedabad/
│
├── app.py
│
├── home.html
├── login1.html
├── signup1.html
├── Ahmedabad_info_page.html
├── photoshoot.html
├── customise.html
├── onlinepayment.html
├── conformbooking.html
│
├── admin_panel.html
├── photographer_panel.html
├── driver_panel.html
│
├── check_photographer.py
├── check_photographers.py
├── delete_photographer.py
├── promote_admin.py
├── verify_admin.py
├── debug_db.py
├── debug_completion.py
├── reset_db.py
│
├── nm.js
├── package.json
├── package-lock.json
│
├── images/
│   └── Project images
│
└── README.md
```
# Database Relationships

The project uses SQLite with Flask-SQLAlchemy.
```text
User
 ├── Photoshoot Bookings
 │       └── Photographer
 │
 └── Ride Bookings
         └── Driver

Photoshoot Booking ── Payment
Ride Booking ──────── Payment
```
