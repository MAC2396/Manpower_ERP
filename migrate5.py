from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:

        # List of columns to add to salary_structures
        cols = [
            ('da_type',         "VARCHAR(10) DEFAULT 'percent'"),
            ('hra_type',        "VARCHAR(10) DEFAULT 'percent'"),
            ('special_type',    "VARCHAR(10) DEFAULT 'percent'"),
            ('bonus_type',      "VARCHAR(10) DEFAULT 'percent'"),
            ('bonus_value',     "FLOAT DEFAULT 0"),
            ('da_value',        "FLOAT DEFAULT 10"),
            ('hra_value',       "FLOAT DEFAULT 20"),
            ('special_value',   "FLOAT DEFAULT 5"),
            ('epf_applicable',  "BOOLEAN DEFAULT 1"),
            ('esic_applicable', "BOOLEAN DEFAULT 1"),
        ]

        for col, coltype in cols:
            try:
                conn.execute(text(
                    f'ALTER TABLE salary_structures '
                    f'ADD COLUMN {col} {coltype}'
                ))
                print(f"Added column: {col}")
            except Exception as e:
                print(f"Skip {col} (already exists)")

        # Copy old percent values to new value columns
        try:
            conn.execute(text(
                'UPDATE salary_structures '
                'SET da_value = da_percent '
                'WHERE da_value IS NULL OR da_value = 0'
            ))
            print("Copied da_percent to da_value")
        except Exception as e:
            print(f"da copy note: {e}")

        try:
            conn.execute(text(
                'UPDATE salary_structures '
                'SET hra_value = hra_percent '
                'WHERE hra_value IS NULL OR hra_value = 0'
            ))
            print("Copied hra_percent to hra_value")
        except Exception as e:
            print(f"hra copy note: {e}")

        try:
            conn.execute(text(
                'UPDATE salary_structures '
                'SET special_value = special_percent '
                'WHERE special_value IS NULL '
                'OR special_value = 0'
            ))
            print("Copied special_percent to special_value")
        except Exception as e:
            print(f"special copy note: {e}")

        conn.commit()
        print("Migration 5 complete!")
        