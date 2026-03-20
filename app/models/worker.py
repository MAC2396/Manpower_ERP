from app import db
from datetime import datetime

class Worker(db.Model):
    __tablename__ = 'workers'

    id              = db.Column(db.Integer, primary_key=True)
    employee_id     = db.Column(db.String(20), unique=True)
    full_name       = db.Column(db.String(150), nullable=False)

    # Basic Info
    full_name       = db.Column(db.String(150), nullable=False)
    father_name     = db.Column(db.String(150))
    date_of_birth   = db.Column(db.Date)
    gender          = db.Column(db.String(10))
    mobile          = db.Column(db.String(15))
    address         = db.Column(db.Text)
    post            = db.Column(db.String(100))

    # KYC Documents
    aadhaar_number  = db.Column(db.String(20))
    pan_number      = db.Column(db.String(20))
    aadhaar_doc     = db.Column(db.String(255))
    pan_doc         = db.Column(db.String(255))
    photo           = db.Column(db.String(255))

    # Bank Details
    bank_name       = db.Column(db.String(100))
    account_number  = db.Column(db.String(30))
    ifsc_code       = db.Column(db.String(20))
    bank_passbook   = db.Column(db.String(255))

    # Status
    is_active       = db.Column(db.Boolean, default=True)
    date_joined     = db.Column(db.Date, default=datetime.utcnow)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships — NO backref on salaries/compliance
    # because Salary and Compliance models define their own relationships
    family_members  = db.relationship('FamilyMember', backref='worker', lazy=True)
    deployments     = db.relationship('Deployment',   backref='worker', lazy=True)

    def kyc_complete(self):
        return all([
            self.aadhaar_number, self.pan_number,
            self.account_number, self.photo
        ])

    def __repr__(self):
        return f'<Worker {self.full_name}>'
    def generate_employee_id(self):
        return f'EMP{self.id:04d}'


class FamilyMember(db.Model):
    __tablename__ = 'family_members'

    id            = db.Column(db.Integer, primary_key=True)
    worker_id     = db.Column(db.Integer, db.ForeignKey('workers.id'), nullable=False)
    name          = db.Column(db.String(150), nullable=False)
    relation      = db.Column(db.String(50))
    date_of_birth = db.Column(db.Date)
    mobile        = db.Column(db.String(15))

    def __repr__(self):
        return f'<FamilyMember {self.name} - {self.relation}>'
    