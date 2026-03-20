from app import db
from datetime import datetime

class Salary(db.Model):
    __tablename__ = 'salaries'

    id               = db.Column(db.Integer, primary_key=True)
    worker_id        = db.Column(db.Integer, db.ForeignKey('workers.id'), nullable=False)
    company_id       = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    month            = db.Column(db.Integer, nullable=False)
    year             = db.Column(db.Integer, nullable=False)

    # Earnings
    basic            = db.Column(db.Float, default=0)
    da               = db.Column(db.Float, default=0)
    hra              = db.Column(db.Float, default=0)
    special_allowance = db.Column(db.Float, default=0)
    overtime         = db.Column(db.Float, default=0)
    gross            = db.Column(db.Float, default=0)

    # Deductions
    pf_employee      = db.Column(db.Float, default=0)
    esic_employee    = db.Column(db.Float, default=0)
    advance          = db.Column(db.Float, default=0)
    other_deductions = db.Column(db.Float, default=0)
    total_deductions = db.Column(db.Float, default=0)

    # Net Pay
    net_pay          = db.Column(db.Float, default=0)
    days_present     = db.Column(db.Integer, default=0)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships — backref names must be unique across all models
    worker  = db.relationship('Worker',  backref='sal_worker',  lazy=True)
    company = db.relationship('Company', backref='sal_company', lazy=True)

    def __repr__(self):
        return f'<Salary Worker:{self.worker_id} {self.month}/{self.year}>'


class Compliance(db.Model):
    __tablename__ = 'compliance'

    id             = db.Column(db.Integer, primary_key=True)
    worker_id      = db.Column(db.Integer, db.ForeignKey('workers.id'), nullable=False)
    company_id     = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    month          = db.Column(db.Integer, nullable=False)
    year           = db.Column(db.Integer, nullable=False)

    pf_employee    = db.Column(db.Float, default=0)
    pf_employer    = db.Column(db.Float, default=0)
    esic_employee  = db.Column(db.Float, default=0)
    esic_employer  = db.Column(db.Float, default=0)
    bonus          = db.Column(db.Float, default=0)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships — backref names must be unique across all models
    worker  = db.relationship('Worker',  backref='comp_worker',  lazy=True)
    company = db.relationship('Company', backref='comp_company', lazy=True)

    def __repr__(self):
        return f'<Compliance Worker:{self.worker_id} {self.month}/{self.year}>'
    
class SalaryStructure(db.Model):
    __tablename__: str = 'salary_structures'

    id              = db.Column(db.Integer, primary_key=True)
    company_id      = db.Column(db.Integer,
                        db.ForeignKey('companies.id'),
                        nullable=True)
    post            = db.Column(db.String(100), nullable=False)

    # Basic Salary
    basic           = db.Column(db.Float, default=0)

    # DA — can be percentage or fixed amount
    da_type         = db.Column(db.String(10), default='percent')
    da_value        = db.Column(db.Float, default=10)

    # HRA — can be percentage or fixed amount
    hra_type        = db.Column(db.String(10), default='percent')
    hra_value       = db.Column(db.Float, default=20)

    # Special Allowance — can be percentage or fixed
    special_type    = db.Column(db.String(10), default='percent')
    special_value   = db.Column(db.Float, default=5)

    # Bonus
    bonus_type      = db.Column(db.String(10), default='percent')
    bonus_value     = db.Column(db.Float, default=0)

    # Statutory
    epf_applicable  = db.Column(db.Boolean, default=True)
    esic_applicable = db.Column(db.Boolean, default=True)

    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    company = db.relationship('Company',
                backref='salary_structures', lazy=True)

    def calc_component(self, ctype, cvalue, basic):
        if ctype == 'percent':
            return round(basic * cvalue / 100, 2)
        else:
            return round(cvalue, 2)

    def __repr__(self):
        return f'<SalaryStructure {self.post}>'

class Advance(db.Model):
    __tablename__: str = 'advances'

    id              = db.Column(db.Integer, primary_key=True)
    worker_id       = db.Column(db.Integer, db.ForeignKey('workers.id'), nullable=False)
    company_id      = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    amount          = db.Column(db.Float, nullable=False)
    date_given      = db.Column(db.Date, nullable=False)
    reason          = db.Column(db.String(255))
    month           = db.Column(db.Integer)   # month to deduct from
    year            = db.Column(db.Integer)   # year to deduct from
    is_deducted     = db.Column(db.Boolean, default=False)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    worker  = db.relationship('Worker',  backref='advances', lazy=True)
    company = db.relationship('Company', backref='advances', lazy=True)

    def __repr__(self):
        return f'<Advance Worker:{self.worker_id} ₹{self.amount}>'
    
class SalaryPayment(db.Model):
    __tablename__: str = 'salary_payments'

    id           = db.Column(db.Integer, primary_key=True)
    company_id   = db.Column(db.Integer,
                             db.ForeignKey('companies.id'),
                             nullable=False)
    month        = db.Column(db.Integer, nullable=False)
    year         = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, default=0)
    total_workers = db.Column(db.Integer, default=0)
    paid_by      = db.Column(db.Integer,
                             db.ForeignKey('users.id'),
                             nullable=True)
    paid_at      = db.Column(db.DateTime, nullable=True)
    status       = db.Column(db.String(20), default='pending')
    notes        = db.Column(db.Text)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    company  = db.relationship('Company',
                               backref='payments', lazy=True)

    def __repr__(self):
        return f'<Payment {self.company_id} {self.month}/{self.year}>'
    
class SalaryComponent(db.Model):
    __tablename__: str = 'salary_components'

    id           = db.Column(db.Integer,
                             primary_key=True)
    structure_id = db.Column(db.Integer,
                             db.ForeignKey(
                                 'salary_structures.id'),
                             nullable=False)
    name         = db.Column(db.String(100),
                             nullable=False)
    comp_type    = db.Column(db.String(10),
                             default='percent')
    value        = db.Column(db.Float, default=0)
    created_at   = db.Column(db.DateTime,
                             default=datetime.utcnow)

    structure = db.relationship('SalaryStructure',
                                backref='custom_components',
                                lazy=True)

    def __repr__(self):
        return f'<Component {self.name}>'
    