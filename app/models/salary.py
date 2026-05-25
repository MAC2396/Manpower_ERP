from app import db
from datetime import datetime

class SalaryStructure(db.Model):
    __tablename__ = 'salary_structures'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    basic_percent = db.Column(db.Float, default=40)
    da_percent = db.Column(db.Float, default=10)
    hra_percent = db.Column(db.Float, default=15)
    conveyance_percent = db.Column(db.Float, default=5)
    medical_percent = db.Column(db.Float, default=5)
    special_allowance_percent = db.Column(db.Float, default=25)
    fixed_basic = db.Column(db.Float, default=0)
    fixed_da = db.Column(db.Float, default=0)
    fixed_hra = db.Column(db.Float, default=0)
    fixed_conveyance = db.Column(db.Float, default=0)
    fixed_medical = db.Column(db.Float, default=0)
    fixed_special = db.Column(db.Float, default=0)
    epf_calculation_base = db.Column(db.String(50), default='basic')
    epf_custom_components = db.Column(db.String(200), default='')
    epf_employee_rate = db.Column(db.Float, default=12)
    epf_employer_rate = db.Column(db.Float, default=12)
    epf_max_limit = db.Column(db.Float, default=15000)
    esic_calculation_base = db.Column(db.String(50), default='basic')
    esic_employee_rate = db.Column(db.Float, default=0.75)
    esic_employer_rate = db.Column(db.Float, default=3.25)
    esic_max_limit = db.Column(db.Float, default=21000)
    experience_increments = db.Column(db.Text, default='')
    professional_tax_enabled = db.Column(db.Boolean, default=True)
    professional_tax_slab = db.Column(db.Text, default='')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    company = db.relationship('Company', backref='salary_structures')

class EmployeeSalaryDetail(db.Model):
    __tablename__ = 'employee_salary_details'
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id'), nullable=False)
    structure_id = db.Column(db.Integer, db.ForeignKey('salary_structures.id'), nullable=False)
    custom_basic = db.Column(db.Float, default=0)
    custom_da = db.Column(db.Float, default=0)
    custom_hra = db.Column(db.Float, default=0)
    custom_conveyance = db.Column(db.Float, default=0)
    custom_medical = db.Column(db.Float, default=0)
    custom_special = db.Column(db.Float, default=0)
    custom_allowances = db.Column(db.Text, default='{}')
    joining_date = db.Column(db.Date, nullable=False)
    last_increment_date = db.Column(db.Date)
    last_increment_percent = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    worker = db.relationship('Worker', backref='salary_detail')
    structure = db.relationship('SalaryStructure', backref='employee_details')

class Salary(db.Model):
    __tablename__ = 'salaries'
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    gross_salary = db.Column(db.Float, default=0)
    net_salary = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='generated')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    worker = db.relationship('Worker', backref='salaries')

class Compliance(db.Model):
    __tablename__ = 'compliance'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    epf_submitted = db.Column(db.Boolean, default=False)
    esic_submitted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    company = db.relationship('Company', backref='compliance_records')

class SalaryPayment(db.Model):
    __tablename__ = 'salary_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    salary_id = db.Column(db.Integer, db.ForeignKey('salaries.id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    payment_mode = db.Column(db.String(50), default='bank_transfer')  # cash, cheque, bank_transfer
    transaction_id = db.Column(db.String(100), nullable=True)
    bank_name = db.Column(db.String(100), nullable=True)
    cheque_number = db.Column(db.String(50), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='completed')  # pending, completed, failed
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    salary = db.relationship('Salary', backref='payments')
    creator = db.relationship('User', backref='salary_payments')
    
    def __repr__(self):
        return f'<SalaryPayment {self.id} - {self.amount}>'