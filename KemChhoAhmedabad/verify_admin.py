from app import app, db, User, RideBooking, PhotoshootBooking, Payment
import uuid

def verify():
    with app.app_context():
        print("1. Creating Test Admin User...")
        admin_email = "testadmin@example.com"
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(username="Test Admin", email=admin_email, password="password", role="admin")
            db.session.add(admin)
            db.session.commit()
            print("   -> Admin user created.")
        else:
            print("   -> Admin user already exists.")
            if admin.role != 'admin':
                admin.role = 'admin'
                db.session.commit()
                print("   -> User role updated to admin.")

        print("2. Creating Test Ride...")
        ride = RideBooking(
            user_id=admin.user_id,
            source="Test Source",
            destination="Test Dest",
            distance="10 km",
            price=100,
            payment_status="Pending",
            status="Pending"
        )
        db.session.add(ride)
        db.session.commit()
        print("   -> Test ride created.")

        print("3. Testing Admin Dashboard Query Logic...")
        # 1. Active Rides
        active_rides = RideBooking.query.filter(RideBooking.payment_status != 'Completed').all()
        print(f"   -> Active Rides Count: {len(active_rides)}")
        
        # 2. Pending Photoshoots
        photoshoot_requests = PhotoshootBooking.query.filter_by(payment_status='Pending').all()
        print(f"   -> Photoshoot Requests: {len(photoshoot_requests)}")
        
        # 3. Recent Rides (The one that crashed before)
        recent_rides = RideBooking.query.order_by(RideBooking.date.desc()).limit(10).all()
        print(f"   -> Recent Rides Count: {len(recent_rides)}")
        
        if recent_rides:
            r = recent_rides[0]
            print(f"   -> accessing ride.rider.username: {r.rider.username}")
            # print(f"   -> accessing ride.driver: {r.driver}") # driver might be None, validation
            if r.driver:
                print(f"   -> accessing ride.driver.username: {r.driver.username}")
            else:
                print("   -> ride.driver is None (Expected for new ride)")

        print("\nVERIFICATION SUCCESSFUL: No errors encountered.")

if __name__ == "__main__":
    verify()
