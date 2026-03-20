from app import db
from datetime import datetime

class DeploymentRequest(db.Model):
    __tablename__: str = 'deployment_requests'

    id            = db.Column(db.Integer, primary_key=True)
    worker_id     = db.Column(db.Integer,
                              db.ForeignKey('workers.id'),
                              nullable=False)
    company_id    = db.Column(db.Integer,
                              db.ForeignKey('companies.id'),
                              nullable=False)
    post          = db.Column(db.String(100), nullable=False)
    date_from     = db.Column(db.Date, nullable=False)
    notes         = db.Column(db.Text)

    submitted_by  = db.Column(db.Integer,
                              db.ForeignKey('users.id'),
                              nullable=False)
    submitted_at  = db.Column(db.DateTime, default=datetime.utcnow)

    status        = db.Column(db.String(20), default='pending')

    reviewed_by   = db.Column(db.Integer,
                              db.ForeignKey('users.id'),
                              nullable=True)
    reviewed_at   = db.Column(db.DateTime, nullable=True)
    review_notes  = db.Column(db.Text)

    deployment_id = db.Column(db.Integer,
                              db.ForeignKey('deployments.id'),
                              nullable=True)

    # Relationships
    worker    = db.relationship('Worker',
                                backref='deploy_requests',
                                lazy=True)
    company   = db.relationship('Company',
                                backref='deploy_requests',
                                lazy=True)
    submitter = db.relationship('User',
                                foreign_keys=[submitted_by],
                                backref='submitted_requests',
                                lazy=True)
    reviewer  = db.relationship('User',
                                foreign_keys=[reviewed_by],
                                backref='reviewed_requests',
                                lazy=True)

    def __repr__(self):
        return f'<DeployRequest Worker:{self.worker_id} Status:{self.status}>'
    