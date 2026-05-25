from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models.client import Company
from app.models.worker import Worker
from app.models.salary import SalaryStructure, EmployeeSalaryDetail
from app.routes.auth import login_required, permission_required
from datetime import date, datetime
import json
import calendar

structure_bp = Blueprint('structure', __name__)

MONTH_NAMES = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April',
    5: 'May', 6: 'June', 7: 'July', 8: 'August',
    9: 'September', 10: 'October', 11: 'November', 12: 'December'
}


@structure_bp.route('/structure')
@login_required
@permission_required('structure', 'view')
def index():
    """Salary Structure main page"""
    structures = SalaryStructure.query.filter_by(is_active=True).all()
    companies = Company.query.all()
    return render_template('structure/index.html', 
                         structures=structures, 
                         companies=companies)


@structure_bp.route('/structure/add', methods=['GET', 'POST'])
@login_required
@permission_required('structure', 'add')
def add():
    """Add new salary structure for a company"""
    companies = Company.query.all()
    
    if request.method == 'POST':
        try:
            # Get experience increments from form
            exp_years = request.form.getlist('exp_years[]')
            exp_increases = request.form.getlist('exp_increases[]')
            experience_increments = []
            for i in range(len(exp_years)):
                if exp_years[i] and exp_increases[i]:
                    experience_increments.append({
                        'years': int(exp_years[i]),
                        'increase': float(exp_increases[i])
                    })
            
            structure = SalaryStructure(
                company_id=int(request.form['company_id']),
                name=request.form['name'],
                basic_percent=float(request.form.get('basic_percent', 40)),
                da_percent=float(request.form.get('da_percent', 10)),
                hra_percent=float(request.form.get('hra_percent', 15)),
                conveyance_percent=float(request.form.get('conveyance_percent', 5)),
                medical_percent=float(request.form.get('medical_percent', 5)),
                special_allowance_percent=float(request.form.get('special_allowance_percent', 25)),
                epf_calculation_base=request.form.get('epf_calculation_base', 'basic'),
                epf_employee_rate=float(request.form.get('epf_employee_rate', 12)),
                epf_employer_rate=float(request.form.get('epf_employer_rate', 12)),
                epf_max_limit=float(request.form.get('epf_max_limit', 15000)),
                esic_calculation_base=request.form.get('esic_calculation_base', 'basic'),
                esic_employee_rate=float(request.form.get('esic_employee_rate', 0.75)),
                esic_employer_rate=float(request.form.get('esic_employer_rate', 3.25)),
                esic_max_limit=float(request.form.get('esic_max_limit', 21000)),
                experience_increments=json.dumps(experience_increments),
                professional_tax_enabled=request.form.get('professional_tax_enabled') == 'on'
            )
            
            db.session.add(structure)
            db.session.commit()
            flash(f'Salary structure "{structure.name}" added successfully!', 'success')
            return redirect(url_for('structure.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('structure/add.html', companies=companies)


@structure_bp.route('/structure/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required('structure', 'edit')
def edit(id):
    """Edit salary structure"""
    structure = SalaryStructure.query.get_or_404(id)
    companies = Company.query.all()
    
    # Load experience increments
    exp_increments = json.loads(structure.experience_increments) if structure.experience_increments else []
    
    if request.method == 'POST':
        try:
            exp_years = request.form.getlist('exp_years[]')
            exp_increases = request.form.getlist('exp_increases[]')
            experience_increments = []
            for i in range(len(exp_years)):
                if exp_years[i] and exp_increases[i]:
                    experience_increments.append({
                        'years': int(exp_years[i]),
                        'increase': float(exp_increases[i])
                    })
            
            structure.company_id = int(request.form['company_id'])
            structure.name = request.form['name']
            structure.basic_percent = float(request.form.get('basic_percent', 40))
            structure.da_percent = float(request.form.get('da_percent', 10))
            structure.hra_percent = float(request.form.get('hra_percent', 15))
            structure.conveyance_percent = float(request.form.get('conveyance_percent', 5))
            structure.medical_percent = float(request.form.get('medical_percent', 5))
            structure.special_allowance_percent = float(request.form.get('special_allowance_percent', 25))
            structure.epf_calculation_base = request.form.get('epf_calculation_base', 'basic')
            structure.epf_employee_rate = float(request.form.get('epf_employee_rate', 12))
            structure.epf_employer_rate = float(request.form.get('epf_employer_rate', 12))
            structure.epf_max_limit = float(request.form.get('epf_max_limit', 15000))
            structure.esic_calculation_base = request.form.get('esic_calculation_base', 'basic')
            structure.esic_employee_rate = float(request.form.get('esic_employee_rate', 0.75))
            structure.esic_employer_rate = float(request.form.get('esic_employer_rate', 3.25))
            structure.esic_max_limit = float(request.form.get('esic_max_limit', 21000))
            structure.experience_increments = json.dumps(experience_increments)
            structure.professional_tax_enabled = request.form.get('professional_tax_enabled') == 'on'
            
            db.session.commit()
            flash(f'Salary structure "{structure.name}" updated successfully!', 'success')
            return redirect(url_for('structure.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('structure/edit.html', 
                         structure=structure, 
                         companies=companies,
                         exp_increments=exp_increments)


@structure_bp.route('/structure/assign/<int:worker_id>', methods=['GET', 'POST'])
@login_required
@permission_required('structure', 'assign')
def assign_to_employee(worker_id):
    """Assign salary structure to employee"""
    worker = Worker.query.get_or_404(worker_id)
    structures = SalaryStructure.query.filter_by(is_active=True).all()
    
    # Get existing assignment
    existing = EmployeeSalaryDetail.query.filter_by(worker_id=worker_id).first()
    
    if request.method == 'POST':
        try:
            if existing:
                # Update existing
                existing.structure_id = int(request.form['structure_id'])
                existing.custom_basic = float(request.form.get('custom_basic', 0))
                existing.custom_da = float(request.form.get('custom_da', 0))
                existing.custom_hra = float(request.form.get('custom_hra', 0))
                existing.custom_conveyance = float(request.form.get('custom_conveyance', 0))
                existing.custom_medical = float(request.form.get('custom_medical', 0))
                existing.custom_special = float(request.form.get('custom_special', 0))
                existing.joining_date = datetime.strptime(request.form['joining_date'], '%Y-%m-%d').date()
            else:
                # Create new
                detail = EmployeeSalaryDetail(
                    worker_id=worker_id,
                    structure_id=int(request.form['structure_id']),
                    custom_basic=float(request.form.get('custom_basic', 0)),
                    custom_da=float(request.form.get('custom_da', 0)),
                    custom_hra=float(request.form.get('custom_hra', 0)),
                    custom_conveyance=float(request.form.get('custom_conveyance', 0)),
                    custom_medical=float(request.form.get('custom_medical', 0)),
                    custom_special=float(request.form.get('custom_special', 0)),
                    joining_date=datetime.strptime(request.form['joining_date'], '%Y-%m-%d').date()
                )
                db.session.add(detail)
            
            db.session.commit()
            flash(f'Salary structure assigned to {worker.full_name}!', 'success')
            return redirect(url_for('workers.view', id=worker_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('structure/assign.html',
                         worker=worker,
                         structures=structures,
                         existing=existing)


@structure_bp.route('/structure/calculate/<int:worker_id>/<int:month>/<int:year>')
def calculate_salary(worker_id, month, year):
    """Calculate salary for an employee based on structure"""
    from app.models.salary import Salary
    from app.models.attendance import Attendance
    
    worker = Worker.query.get_or_404(worker_id)
    salary_detail = EmployeeSalaryDetail.query.filter_by(worker_id=worker_id).first()
    
    if not salary_detail:
        return jsonify({'error': 'No salary structure assigned'}), 400
    
    structure = SalaryStructure.query.get(salary_detail.structure_id)
    
    # Calculate experience-based increment
    years_of_service = (date.today() - salary_detail.joining_date).days // 365
    experience_multiplier = 1.0
    
    if structure.experience_increments:
        increments = json.loads(structure.experience_increments)
        for inc in sorted(increments, key=lambda x: x['years'], reverse=True):
            if years_of_service >= inc['years']:
                experience_multiplier = 1 + (inc['increase'] / 100)
                break
    
    # Calculate base gross (you can get this from deployment or custom)
    deployment = Deployment.query.filter_by(worker_id=worker_id, is_active=True).first()
    base_gross = deployment.salary_per_month if deployment else 25000
    
    # Calculate components
    basic = (salary_detail.custom_basic if salary_detail.custom_basic > 0 
             else base_gross * (structure.basic_percent / 100)) * experience_multiplier
    
    da = (salary_detail.custom_da if salary_detail.custom_da > 0 
          else base_gross * (structure.da_percent / 100)) * experience_multiplier
    
    hra = (salary_detail.custom_hra if salary_detail.custom_hra > 0 
           else base_gross * (structure.hra_percent / 100)) * experience_multiplier
    
    conveyance = (salary_detail.custom_conveyance if salary_detail.custom_conveyance > 0 
                  else base_gross * (structure.conveyance_percent / 100)) * experience_multiplier
    
    medical = (salary_detail.custom_medical if salary_detail.custom_medical > 0 
               else base_gross * (structure.medical_percent / 100)) * experience_multiplier
    
    special = (salary_detail.custom_special if salary_detail.custom_special > 0 
               else base_gross * (structure.special_allowance_percent / 100)) * experience_multiplier
    
    gross_salary = basic + da + hra + conveyance + medical + special
    
    # Calculate EPF wages based on configuration
    epf_wage = 0
    if structure.epf_calculation_base == 'basic':
        epf_wage = basic
    elif structure.epf_calculation_base == 'basic_da':
        epf_wage = basic + da
    elif structure.epf_calculation_base == 'basic_da_allowances':
        epf_wage = basic + da + hra + conveyance + medical + special
    
    epf_wage = min(epf_wage, structure.epf_max_limit)
    employee_pf = epf_wage * (structure.epf_employee_rate / 100)
    employer_pf = epf_wage * (structure.epf_employer_rate / 100)
    
    # Calculate ESIC
    esic_wage = basic + da + hra + conveyance + medical + special
    esic_wage = min(esic_wage, structure.esic_max_limit)
    employee_esic = esic_wage * (structure.esic_employee_rate / 100) if esic_wage <= structure.esic_max_limit else 0
    employer_esic = esic_wage * (structure.esic_employer_rate / 100) if esic_wage <= structure.esic_max_limit else 0
    
    # Get attendance for deduction
    days_in_month = calendar.monthrange(year, month)[1]
    attendance = Attendance.query.filter_by(worker_id=worker_id).filter(
        db.extract('month', Attendance.date) == month,
        db.extract('year', Attendance.date) == year
    ).all()
    
    present_days = sum(1 for a in attendance if a.status == 'P')
    half_days = sum(1 for a in attendance if a.status == 'H')
    
    daily_rate = gross_salary / days_in_month
    effective_days = present_days + (half_days * 0.5)
    attendance_deduction = daily_rate * (days_in_month - effective_days)
    
    net_salary = gross_salary - attendance_deduction - employee_pf - employee_esic
    
    return jsonify({
        'worker_name': worker.full_name,
        'month': MONTH_NAMES[month],
        'year': year,
        'years_of_service': years_of_service,
        'experience_multiplier': experience_multiplier,
        'components': {
            'basic': round(basic, 2),
            'da': round(da, 2),
            'hra': round(hra, 2),
            'conveyance': round(conveyance, 2),
            'medical': round(medical, 2),
            'special_allowance': round(special, 2)
        },
        'gross_salary': round(gross_salary, 2),
        'epf_wage': round(epf_wage, 2),
        'employee_pf': round(employee_pf, 2),
        'employer_pf': round(employer_pf, 2),
        'employee_esic': round(employee_esic, 2),
        'employer_esic': round(employer_esic, 2),
        'attendance': {
            'present_days': present_days,
            'half_days': half_days,
            'total_days': days_in_month,
            'deduction': round(attendance_deduction, 2)
        },
        'net_salary': round(net_salary, 2)
    })
@structure_bp.route('/structure/view/<int:id>')
def view_structure_json(id):
    """Return structure details as JSON for modal view"""
    structure = SalaryStructure.query.get_or_404(id)
    
    epf_base_map = {
        'basic': 'Basic Only',
        'basic_da': 'Basic + DA',
        'basic_da_allowances': 'Basic + DA + All Allowances'
    }
    
    esic_base_map = {
        'basic': 'Basic Only',
        'basic_da': 'Basic + DA',
        'basic_da_allowances': 'Basic + DA + All Allowances'
    }
    
    return jsonify({
        'name': structure.name,
        'company': structure.company.name,
        'basic_percent': structure.basic_percent,
        'da_percent': structure.da_percent,
        'hra_percent': structure.hra_percent,
        'conveyance_percent': structure.conveyance_percent,
        'medical_percent': structure.medical_percent,
        'special_allowance_percent': structure.special_allowance_percent,
        'epf_base': epf_base_map.get(structure.epf_calculation_base, 'Basic Only'),
        'epf_employee_rate': structure.epf_employee_rate,
        'epf_employer_rate': structure.epf_employer_rate,
        'epf_max_limit': structure.epf_max_limit,
        'esic_base': esic_base_map.get(structure.esic_calculation_base, 'Basic Only'),
        'esic_employee_rate': structure.esic_employee_rate,
        'esic_employer_rate': structure.esic_employer_rate,
        'esic_max_limit': structure.esic_max_limit
    })

@structure_bp.route('/structure/preview/<int:id>')
def preview_structure(id):
    """Return structure preview for assignment page"""
    structure = SalaryStructure.query.get_or_404(id)
    
    epf_base_map = {
        'basic': 'Basic Only',
        'basic_da': 'Basic + DA',
        'basic_da_allowances': 'Basic + DA + All Allowances'
    }
    
    return jsonify({
        'basic_percent': structure.basic_percent,
        'da_percent': structure.da_percent,
        'hra_percent': structure.hra_percent,
        'conveyance_percent': structure.conveyance_percent,
        'medical_percent': structure.medical_percent,
        'special_allowance_percent': structure.special_allowance_percent,
        'epf_base': epf_base_map.get(structure.epf_calculation_base, 'Basic Only'),
        'epf_employee_rate': structure.epf_employee_rate,
        'epf_employer_rate': structure.epf_employer_rate,
        'epf_max_limit': structure.epf_max_limit,
        'esic_employee_rate': structure.esic_employee_rate,
        'esic_employer_rate': structure.esic_employer_rate,
        'esic_max_limit': structure.esic_max_limit
    })