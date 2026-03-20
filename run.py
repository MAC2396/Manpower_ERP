from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    #app.run(debug=True)
    app.run(debug=False, host='0.0.0.0', port=5000)

#cd C:\Users\Lenovo\manpower_payroll
#venv\Scripts\activate
#py run.py
