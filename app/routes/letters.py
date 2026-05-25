from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from app import db
from app.models.worker import Worker
from app.models.client import Company
from app.models.deployment import Deployment
from app.models.attendance import Attendance
from app.models.salary import Salary
from app.routes.auth import login_required, permission_required
from datetime import date, datetime
import calendar
import io

letters_bp = Blueprint('letters', __name__)

MONTH_NAMES = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April',
    5: 'May', 6: 'June', 7: 'July', 8: 'August',
    9: 'September', 10: 'October', 11: 'November', 12: 'December'
}


@letters_bp.route('/letters')
@login_required
@permission_required('letters', 'view')
def index():
    """Letters main page with filters"""
    # Get filter parameters
    employee_id = request.args.get('employee_id', '')
    company_id = request.args.get('company_id', '')
    post = request.args.get('post', '')
    
    # Get all companies for filter
    companies = Company.query.all()
    
    # Get unique posts from deployments
    unique_posts = db.session.query(Deployment.post).distinct().all()
    post_list = sorted([p[0] for p in unique_posts if p[0]])
    
    # Build worker query
    query = Worker.query.filter_by(is_active=True)
    
    # Apply filters
    if employee_id:
        query = query.filter(Worker.employee_id.ilike(f'%{employee_id}%'))
    
    # Filter by company via deployments
    workers = query.all()
    
    if company_id or post:
        filtered_workers = []
        for worker in workers:
            # Get current deployment
            deployment = Deployment.query.filter_by(
                worker_id=worker.id, 
                is_active=True
            ).first()
            
            if deployment:
                if company_id and deployment.company_id != int(company_id):
                    continue
                if post and deployment.post != post:
                    continue
                worker.current_deployment = deployment
            filtered_workers.append(worker)
        workers = filtered_workers
    else:
        # Add deployment info to workers
        for worker in workers:
            worker.current_deployment = Deployment.query.filter_by(
                worker_id=worker.id, 
                is_active=True
            ).first()
    
    return render_template('letters/index.html',
                         workers=workers,
                         companies=companies,
                         post_list=post_list,
                         selected_employee=employee_id,
                         selected_company=company_id,
                         selected_post=post)


@letters_bp.route('/letters/employee/<int:worker_id>')
@login_required
@permission_required('letters', 'view')
def employee_details(worker_id):
    """Show complete employee details for letter generation"""
    worker = Worker.query.get_or_404(worker_id)
    
    # Get current deployment
    current_deployment = Deployment.query.filter_by(
        worker_id=worker_id, 
        is_active=True
    ).first()
    
    # Get deployment history
    deployment_history = Deployment.query.filter_by(
        worker_id=worker_id
    ).order_by(Deployment.date_from.desc()).all()
    
    # Get salary history (last 12 months)
    current_year = date.today().year
    salary_history = []
    for month in range(1, 13):
        salary = Salary.query.filter_by(
            worker_id=worker_id,
            month=month,
            year=current_year
        ).first()
        if salary:
            salary_history.append(salary)
    
    # Get attendance summary for current year
    attendance_summary = []
    for month in range(1, 13):
        days_in_month = calendar.monthrange(current_year, month)[1]
        records = Attendance.query.filter_by(worker_id=worker_id).filter(
            db.extract('month', Attendance.date) == month,
            db.extract('year', Attendance.date) == current_year
        ).all()
        
        present = sum(1 for r in records if r.status == 'P')
        absent = sum(1 for r in records if r.status == 'A')
        halfday = sum(1 for r in records if r.status == 'H')
        
        if records:
            attendance_summary.append({
                'month': month,
                'month_name': MONTH_NAMES[month],
                'present': present,
                'absent': absent,
                'halfday': halfday,
                'total_days': days_in_month,
                'attendance_percent': round(((present + halfday * 0.5) / days_in_month) * 100, 1) if days_in_month > 0 else 0
            })
    
    return render_template('letters/employee_details.html',
                         worker=worker,
                         current_deployment=current_deployment,
                         deployment_history=deployment_history,
                         salary_history=salary_history,
                         attendance_summary=attendance_summary,
                         current_year=current_year,
                         MONTH_NAMES=MONTH_NAMES)


@letters_bp.route('/letters/generate/joining/<int:worker_id>')
@login_required
@permission_required('letters', 'generate')
def generate_joining_letter(worker_id):
    """Generate Joining Letter for employee"""
    worker = Worker.query.get_or_404(worker_id)
    deployment = Deployment.query.filter_by(worker_id=worker_id, is_active=True).first()
    company = deployment.company if deployment else None
    today = date.today()
    
    return render_template('letters/joining_letter.html',
                         worker=worker,
                         company=company,
                         deployment=deployment,
                         today=today)


@letters_bp.route('/letters/generate/experience/<int:worker_id>')
@login_required
@permission_required('letters', 'generate')
def generate_experience_letter(worker_id):
    """Generate Experience Letter for employee"""
    worker = Worker.query.get_or_404(worker_id)
    deployment = Deployment.query.filter_by(worker_id=worker_id, is_active=True).first()
    company = deployment.company if deployment else None
    
    # Calculate total experience
    all_deployments = Deployment.query.filter_by(worker_id=worker_id).order_by(Deployment.date_from).all()
    
    total_days = 0
    if all_deployments:
        for dep in all_deployments:
            start = dep.date_from
            end = dep.date_to if dep.date_to else date.today()
            total_days += (end - start).days
    
    years = total_days // 365
    months = (total_days % 365) // 30
    days = (total_days % 365) % 30
    
    experience = {
        'years': years,
        'months': months,
        'days': days,
        'total_days': total_days
    }
    
    return render_template('letters/experience_letter.html',
                         worker=worker,
                         company=company,
                         deployment=deployment,
                         experience=experience,
                         today=date.today())


@letters_bp.route('/letters/generate/form16/<int:worker_id>/<int:year>')
@login_required
@permission_required('letters', 'generate')
def generate_form16(worker_id, year):
    """Generate Form 16 for employee for a specific financial year"""
    worker = Worker.query.get_or_404(worker_id)
    deployment = Deployment.query.filter_by(worker_id=worker_id, is_active=True).first()
    company = deployment.company if deployment else None
    
    # Get all salary records for the year
    salaries = Salary.query.filter_by(
        worker_id=worker_id,
        year=year
    ).order_by(Salary.month).all()
    
    # Calculate totals
    total_salary = sum(s.gross_salary or 0 for s in salaries)
    total_deductions = sum((s.tds_deduction or 0) + (s.other_deductions or 0) for s in salaries)
    total_net_paid = total_salary - total_deductions
    
    # Monthly breakdown for Form 16
    monthly_breakdown = []
    for month in range(1, 13):
        salary = next((s for s in salaries if s.month == month), None)
        monthly_breakdown.append({
            'month': month,
            'month_name': MONTH_NAMES[month],
            'salary': salary.gross_salary if salary else 0,
            'tds': salary.tds_deduction if salary else 0,
            'net': (salary.gross_salary or 0) - (salary.tds_deduction or 0) if salary else 0
        })
    
    return render_template('letters/form16.html',
                         worker=worker,
                         company=company,
                         year=year,
                         salaries=salaries,
                         monthly_breakdown=monthly_breakdown,
                         total_salary=total_salary,
                         total_deductions=total_deductions,
                         total_net_paid=total_net_paid,
                         today=date.today(),
                         MONTH_NAMES=MONTH_NAMES)


@letters_bp.route('/letters/generate/salary-statement/<int:worker_id>/<int:year>')
@login_required
@permission_required('letters', 'generate')
def generate_salary_statement(worker_id, year):
    """Generate Annual Salary Statement for employee"""
    worker = Worker.query.get_or_404(worker_id)
    deployment = Deployment.query.filter_by(worker_id=worker_id, is_active=True).first()
    company = deployment.company if deployment else None
    
    # Get all salary records for the year
    salaries = Salary.query.filter_by(
        worker_id=worker_id,
        year=year
    ).order_by(Salary.month).all()
    
    # Calculate yearly totals
    yearly_totals = {
        'basic': 0,
        'hra': 0,
        'da': 0,
        'conveyance': 0,
        'medical': 0,
        'special_allowance': 0,
        'bonus': 0,
        'gross': 0,
        'tds': 0,
        'esi': 0,
        'pf': 0,
        'professional_tax': 0,
        'other_deductions': 0,
        'net': 0
    }
    
    monthly_data = []
    for month in range(1, 13):
        salary = next((s for s in salaries if s.month == month), None)
        if salary:
            monthly_data.append({
                'month': month,
                'month_name': MONTH_NAMES[month],
                'basic': salary.basic or 0,
                'hra': salary.hra or 0,
                'da': salary.da or 0,
                'conveyance': salary.conveyance or 0,
                'medical': salary.medical or 0,
                'special_allowance': salary.special_allowance or 0,
                'bonus': salary.bonus or 0,
                'gross': salary.gross_salary or 0,
                'tds': salary.tds_deduction or 0,
                'esi': salary.esi_deduction or 0,
                'pf': salary.pf_deduction or 0,
                'professional_tax': salary.professional_tax or 0,
                'other': salary.other_deductions or 0,
                'net': salary.net_salary or 0
            })
            
            # Add to totals
            yearly_totals['basic'] += salary.basic or 0
            yearly_totals['hra'] += salary.hra or 0
            yearly_totals['da'] += salary.da or 0
            yearly_totals['conveyance'] += salary.conveyance or 0
            yearly_totals['medical'] += salary.medical or 0
            yearly_totals['special_allowance'] += salary.special_allowance or 0
            yearly_totals['bonus'] += salary.bonus or 0
            yearly_totals['gross'] += salary.gross_salary or 0
            yearly_totals['tds'] += salary.tds_deduction or 0
            yearly_totals['esi'] += salary.esi_deduction or 0
            yearly_totals['pf'] += salary.pf_deduction or 0
            yearly_totals['professional_tax'] += salary.professional_tax or 0
            yearly_totals['other_deductions'] += salary.other_deductions or 0
            yearly_totals['net'] += salary.net_salary or 0
    
    return render_template('letters/salary_statement.html',
                         worker=worker,
                         company=company,
                         year=year,
                         monthly_data=monthly_data,
                         yearly_totals=yearly_totals,
                         today=date.today(),
                         MONTH_NAMES=MONTH_NAMES)


@letters_bp.route('/letters/generate/all-salaries/<int:worker_id>')
@login_required
@permission_required('letters', 'generate')
def generate_all_salaries(worker_id):
    """Generate complete salary history for employee"""
    worker = Worker.query.get_or_404(worker_id)
    
    # Get all salary records
    all_salaries = Salary.query.filter_by(worker_id=worker_id).order_by(
        Salary.year.desc(), Salary.month.desc()
    ).all()
    
    return render_template('letters/all_salaries.html',
                         worker=worker,
                         all_salaries=all_salaries,
                         today=date.today(),
                         MONTH_NAMES=MONTH_NAMES)