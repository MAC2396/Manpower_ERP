from app import create_app, db
from app.models.user import UserPermission

app = create_app()

with app.app_context():
    db.create_all()
    print("UserPermission table created!")
    