from app import app, db, Photographer

with app.app_context():
    p = Photographer.query.filter_by(username='LensMaster').first()
    if p:
        print(f"Username: {p.username}")
        print(f"Password: {p.password}")
    else:
        print("Photographer not found")
