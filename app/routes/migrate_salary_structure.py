from app import create_app, db
from app.models.salary_structure import SalaryStructure, EmployeeSalaryDetail

app = create_app()

with app.app_context():
    # Create tables
    db.create_all()
    print("✅ Salary structure tables created successfully!")
    
    # Check if tables exist
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    if 'salary_structures' in tables:
        print("✅ salary_structures table exists")
    if 'employee_salary_details' in tables:
        print("✅ employee_salary_details table exists")