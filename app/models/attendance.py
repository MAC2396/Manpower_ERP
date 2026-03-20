from app import db
from datetime import datetime

class Attendance(db.Model):
    __tablename__ = 'attendance'

    id          = db.Column(db.Integer, primary_key=True)
    worker_id   = db.Column(db.Integer, db.ForeignKey('workers.id'), nullable=False)
    date        = db.Column(db.Date, nullable=False)
    status      = db.Column(db.String(10), default='P')  # P=Present A=Absent H=Half-day
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Attendance {self.worker_id} {self.date} {self.status}>' 
