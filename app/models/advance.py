from app import db
from datetime import datetime

class Advance(db.Model):
    __tablename__ = 'advances'
    
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    request_date = db.Column(db.Date, default=datetime.utcnow)
    approved_date = db.Column(db.Date, nullable=True)
    is_deducted = db.Column(db.Boolean, default=False)
    deduction_start_month = db.Column(db.Integer, nullable=True)
    deduction_start_year = db.Column(db.Integer, nullable=True)
    monthly_deduction = db.Column(db.Float, nullable=True)
    remaining_amount = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, completed
    reason = db.Column(db.Text, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    worker = db.relationship('Worker', backref='advances')
    approver = db.relationship('User', backref='approved_advances')
    
    def __repr__(self):
        return f'<Advance {self.worker_id} - {self.amount}>'