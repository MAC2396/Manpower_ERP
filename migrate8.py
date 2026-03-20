from app import create_app, db
from app.models.salary import SalaryComponent

app = create_app()

with app.app_context():
    db.create_all()
    print("SalaryComponent table created!")
    