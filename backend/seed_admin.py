from app import create_app
from extensions import db, bcrypt
from models.user import User

app = create_app()

with app.app_context():
    # Check if admin already exists
    admin_user = User.query.filter_by(username='admin').first()
    
    if not admin_user:
        hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = User(username='admin', password_hash=hashed_password, role='admin')
        db.session.add(admin)
        db.session.commit()
        print("Super Admin created successfully!")
        print("Username: admin")
        print("Password: admin123")
    else:
        print("Admin user already exists.")
