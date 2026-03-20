from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        # Try adding column (skip if already exists)
        try:
            conn.execute(text(
                'ALTER TABLE workers '
                'ADD COLUMN employee_id VARCHAR(20)'
            ))
            conn.commit()
            print("employee_id column added!")
        except Exception as e:
            print(f"Column already exists: {e}")

        # Try adding bonus column to salaries
        try:
            conn.execute(text(
                'ALTER TABLE salaries '
                'ADD COLUMN bonus FLOAT DEFAULT 0'
            ))
            conn.commit()
            print("bonus column added to salaries!")
        except Exception as e:
            print(f"Bonus column note: {e}")

    # Generate IDs for existing workers
    from app.models.worker import Worker
    workers = Worker.query.all()
    count = 0
    for w in workers:
        if not w.employee_id:
            w.employee_id = f'EMP{w.id:04d}'
            count += 1
    db.session.commit()
    print(f"Generated Employee IDs for {count} workers!")
    print("Migration 4 complete!")
    