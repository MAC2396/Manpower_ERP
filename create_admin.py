from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    db.create_all()

    # Check if admin already exists
    existing = User.query.filter_by(username='admin').first()
    if not existing:
        admin = User(
            username  = 'admin',
            full_name = 'System Administrator',
            role      = 'admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("===================================")
        print("Admin user created successfully!")
        print("Username : admin")
        print("Password : admin123")
        print("===================================")
    else:
        print("Admin user already exists!")
