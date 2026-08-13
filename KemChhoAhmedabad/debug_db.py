from app import app, db, Photographer, PhotoshootBooking, Driver

with app.app_context():
    print("\n--- PHOTOGRAPHERS ---")
    for p in Photographer.query.all():
        print(f"ID: {p.id} | User: {p.username} | Available: {p.is_available}")

    print("\n--- PHOTOSHOOT BOOKINGS ---")
    for b in PhotoshootBooking.query.all():
        assigned_name = b.assigned_photographer.username if b.assigned_photographer else "None"
        print(f"ID: {b.id} | Status: {b.status} | PhotographerID: {b.photographer_id} ({assigned_name}) | Loc: {b.location_name}")
        
    print("\n--- DRIVERS ---")
    for d in Driver.query.all():
        print(f"ID: {d.id} | User: {d.username}")
