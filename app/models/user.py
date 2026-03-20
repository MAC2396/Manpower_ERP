from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__: str = 'users'

    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(50), unique=True, nullable=False)
    full_name    = db.Column(db.String(150), nullable=False)
    email        = db.Column(db.String(100))
    mobile       = db.Column(db.String(15))
    password     = db.Column(db.String(255), nullable=False)
    role         = db.Column(db.String(20), nullable=False,
                             default='supervisor')
    is_active    = db.Column(db.Boolean, default=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    assignments  = db.relationship('SupervisorAssignment',
                                   backref='supervisor',
                                   lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_admin(self):
        return self.role == 'admin'

    def is_hr(self):
        return self.role in ['admin', 'hr']

    def is_supervisor(self):
        return self.role == 'supervisor'

    def get_assigned_company(self):
        assignment = SupervisorAssignment.query.filter_by(
            supervisor_id=self.id
        ).first()
        return assignment.company if assignment else None

    def __repr__(self):
        return f'<User {self.username} - {self.role}>'


class SupervisorAssignment(db.Model):
    __tablename__: str = 'supervisor_assignments'

    id            = db.Column(db.Integer, primary_key=True)
    supervisor_id = db.Column(db.Integer,
                              db.ForeignKey('users.id'),
                              nullable=False)
    company_id    = db.Column(db.Integer,
                              db.ForeignKey('companies.id'),
                              nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    company = db.relationship('Company',
                              backref='supervisor_assignments',
                              lazy=True)

    def __repr__(self):
        return f'<Assignment Supervisor:{self.supervisor_id} Company:{self.company_id}>'
    
class UserPermission(db.Model):
    __tablename__: str = 'user_permissions'

    id           = db.Column(db.Integer,
                             primary_key=True)
    user_id      = db.Column(db.Integer,
                             db.ForeignKey('users.id'),
                             nullable=False)
    module       = db.Column(db.String(50),
                             nullable=False)
    can_view     = db.Column(db.Boolean, default=True)
    can_add      = db.Column(db.Boolean, default=False)
    can_edit     = db.Column(db.Boolean, default=False)
    can_delete   = db.Column(db.Boolean, default=False)
    can_export   = db.Column(db.Boolean, default=False)

    user = db.relationship('User',
                           backref='permissions',
                           lazy=True)

    def __repr__(self):
        return f'<Permission {self.user_id} {self.module}>'
    