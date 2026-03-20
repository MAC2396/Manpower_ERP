from app import create_app, db
from app.models.user import User, SupervisorAssignment
from app.models.deployment_request import DeploymentRequest

app = create_app()

with app.app_context():
    # This creates all missing tables without touching existing ones
    db.create_all()
    print("All new tables created successfully!")
    print("Tables created:")
    print("  - users")
    print("  - supervisor_assignments")
    print("  - deployment_requests")
    