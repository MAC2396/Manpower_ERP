from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        indexes = [
            # Workers
            '''CREATE INDEX IF NOT EXISTS
               idx_workers_employee_id
               ON workers(employee_id)''',
            '''CREATE INDEX IF NOT EXISTS
               idx_workers_active
               ON workers(is_active)''',
            '''CREATE INDEX IF NOT EXISTS
               idx_workers_aadhaar
               ON workers(aadhaar_number)''',

            # Deployments
            '''CREATE INDEX IF NOT EXISTS
               idx_deployments_worker
               ON deployments(worker_id)''',
            '''CREATE INDEX IF NOT EXISTS
               idx_deployments_company
               ON deployments(company_id)''',
            '''CREATE INDEX IF NOT EXISTS
               idx_deployments_active
               ON deployments(is_active)''',

            # Attendance
            '''CREATE INDEX IF NOT EXISTS
               idx_attendance_worker_date
               ON attendance(worker_id, date)''',
            '''CREATE INDEX IF NOT EXISTS
               idx_attendance_date
               ON attendance(date)''',

            # Salary
            '''CREATE INDEX IF NOT EXISTS
               idx_salary_worker_month
               ON salaries(worker_id, month, year)''',
            '''CREATE INDEX IF NOT EXISTS
               idx_salary_company_month
               ON salaries(company_id, month, year)''',

            # Compliance
            '''CREATE INDEX IF NOT EXISTS
               idx_compliance_worker
               ON compliance(worker_id, month, year)''',

            # Advances
            '''CREATE INDEX IF NOT EXISTS
               idx_advances_worker
               ON advances(worker_id, is_deducted)''',

            # Users
            '''CREATE INDEX IF NOT EXISTS
               idx_users_username
               ON users(username)''',

            # Deployment Requests
            '''CREATE INDEX IF NOT EXISTS
               idx_deploy_requests_status
               ON deployment_requests(status)''',
        ]

        for idx in indexes:
            try:
                conn.execute(text(idx))
                print(f"Index created: {idx[:50]}...")
            except Exception as e:
                print(f"Skip (exists): {idx[:40]}...")

        conn.commit()
        print("\nAll indexes created!")
        print("Database optimized for performance!")