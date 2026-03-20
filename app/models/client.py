from app import db
from datetime import datetime

class Company(db.Model):
    __tablename__ = 'companies'

    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(200), nullable=False)
    address        = db.Column(db.Text)
    city           = db.Column(db.String(100))
    state          = db.Column(db.String(100))
    pincode        = db.Column(db.String(10))
    contact_person = db.Column(db.String(100))
    contact_phone  = db.Column(db.String(20))
    email          = db.Column(db.String(100))
    gst_number     = db.Column(db.String(20))
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    requirements  = db.relationship('Requirement', backref='company', lazy=True)
    deployments   = db.relationship('Deployment', backref='company', lazy=True)

    def __repr__(self):
        return f'<Company {self.name}>'


class Requirement(db.Model):
    __tablename__ = 'requirements'

    id            = db.Column(db.Integer, primary_key=True)
    company_id    = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    post          = db.Column(db.String(100), nullable=False)  # e.g. Helper, Supervisor
    required_count = db.Column(db.Integer, nullable=False)
    month         = db.Column(db.Integer, nullable=False)      # 1-12
    year          = db.Column(db.Integer, nullable=False)
    shift         = db.Column(db.String(20), default='General') # Morning/Evening/Night
    notes         = db.Column(db.Text)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Requirement {self.post} - {self.required_count}>' 
