from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        cols = [
            ('city',    'VARCHAR(100)'),
            ('state',   'VARCHAR(100)'),
            ('pincode', 'VARCHAR(10)'),
        ]
        for col, coltype in cols:
            try:
                conn.execute(text(
                    f'ALTER TABLE companies '
                    f'ADD COLUMN {col} {coltype}'
                ))
                print(f"Added: {col}")
            except Exception as e:
                print(f"Skip {col}: already exists")
        conn.commit()
        print("Migration 7 complete!")
        