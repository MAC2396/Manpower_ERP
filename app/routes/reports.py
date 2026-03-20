from flask import Blueprint, render_template, request, send_file
from app import db
from app.models.client import Company
from app.models.worker import Worker
from app.models.salary import Salary, Compliance
from app.models.deployment import Deployment
from datetime import date
from app.routes.auth import (login_required,
                              permission_required)
import io

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
@permission_required('reports', 'view')
def index():
    companies = Company.query.all()
    current_month = date.today().month
    current_year  = date.today().year
    return render_template('reports/index.html',
                           companies=companies,
                           current_month=current_month,
                           current_year=current_year)

@reports_bp.route('/reports/export-salary-excel', methods=['POST'])
def export_salary_excel():
    from app.utils.export import export_salary_to_excel
    month      = int(request.form['month'])
    year       = int(request.form['year'])
    company_id = request.form.get('company_id')

    query = Salary.query.filter_by(month=month, year=year)
    if company_id:
        query = query.filter_by(company_id=company_id)
    salaries = query.all()

    output = export_salary_to_excel(salaries, month, year)
    filename = f'Salary_Register_{month:02d}_{year}.xlsx'
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@reports_bp.route('/reports/export-compliance-excel', methods=['POST'])
def export_compliance_excel():
    from app.utils.export import export_compliance_to_excel
    month      = int(request.form['month'])
    year       = int(request.form['year'])
    company_id = request.form.get('company_id')

    query = Compliance.query.filter_by(month=month, year=year)
    if company_id:
        query = query.filter_by(company_id=company_id)
    records = query.all()

    output = export_compliance_to_excel(records, month, year)
    filename = f'PF_ESIC_Compliance_{month:02d}_{year}.xlsx'
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@reports_bp.route('/reports/export-workers-excel')
def export_workers_excel():
    from app.utils.export import export_workers_to_excel
    workers = Worker.query.all()
    output  = export_workers_to_excel(workers)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='Workers_KYC_Report.xlsx'
    )

@reports_bp.route('/reports/export-deployment-excel', methods=['POST'])
def export_deployment_excel():
    from app.utils.export import export_deployment_to_excel
    from app.models.client import Requirement
    month      = int(request.form['month'])
    year       = int(request.form['year'])
    company_id = request.form.get('company_id')

    query = Requirement.query.filter_by(month=month, year=year)
    if company_id:
        query = query.filter_by(company_id=company_id)
    requirements = query.all()

    output   = export_deployment_to_excel(requirements, month, year)
    filename = f'Deployment_Report_{month:02d}_{year}.xlsx'
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@reports_bp.route('/reports/export-quarterly-excel', methods=['POST'])
def export_quarterly_excel():
    from app.utils.export import export_quarterly_to_excel
    quarter    = int(request.form['quarter'])
    year       = int(request.form['year'])
    company_id = request.form.get('company_id')

    # Get months for quarter
    months = {
        1: [1, 2, 3],
        2: [4, 5, 6],
        3: [7, 8, 9],
        4: [10, 11, 12]
    }[quarter]

    query = Salary.query.filter(
        Salary.month.in_(months),
        Salary.year == year
    )
    if company_id:
        query = query.filter_by(company_id=company_id)
    salaries = query.all()

    output   = export_quarterly_to_excel(salaries, quarter, year)
    filename = f'Quarterly_Report_Q{quarter}_{year}.xlsx'
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )