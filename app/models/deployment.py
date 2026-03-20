from app import db
from datetime import datetime

class Deployment(db.Model):
    __tablename__ = 'deployments'

    id            = db.Column(db.Integer, primary_key=True)
    worker_id     = db.Column(db.Integer, db.ForeignKey('workers.id'), nullable=False)
    company_id    = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    post          = db.Column(db.String(100), nullable=False)
    date_from     = db.Column(db.Date, nullable=False)
    date_to       = db.Column(db.Date)               # Null means currently deployed
    is_active     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Deployment Worker:{self.worker_id} Company:{self.company_id}>' 
