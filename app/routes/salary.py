from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, send_file, session)
from app import db
from app.models.client import Company
from app.models.worker import Worker
from app.models.deployment import Deployment
from app.models.attendance import Attendance
from app.models.salary import Salary, Compliance, SalaryPayment
from app.utils.salary_engine import MONTH_DAYS, MONTH_NAMES
from datetime import date
from app.routes.auth import (login_required,
                              permission_required)
import io

salary_bp = Blueprint('salary', __name__)


@salary_bp.route('/salary')
@login_required
@permission_required('salary', 'view')
def index():
    month      = int(request.args.get('month', date.today().month))
    year       = int(request.args.get('year',  date.today().year))
    company_id = request.args.get('company_id', '')
    companies  = Company.query.all()

    query = Salary.query.filter_by(month=month, year=year)
    if company_id:
        query = query.filter_by(company_id=int(company_id))
    salaries = query.order_by(Salary.company_id,
                              Salary.worker_id).all()

    # Summary stats
    total_gross  = sum(s.gross   for s in salaries)
    total_net    = sum(s.net_pay for s in salaries)
    total_pf     = sum(s.pf_employee for s in salaries)
    total_esic   = sum(s.esic_employee for s in salaries)
    total_workers = len(salaries)

    # Check payment status
    payment = None
    if company_id:
        payment = SalaryPayment.query.filter_by(
            company_id = int(company_id),
            month      = month,
            year       = year
        ).first()

    return render_template('salary/index.html',
                           salaries=salaries,
                           month=month, year=year,
                           month_name=MONTH_NAMES[month],
                           companies=companies,
                           company_id=company_id,
                           total_gross=total_gross,
                           total_net=total_net,
                           total_pf=total_pf,
                           total_esic=total_esic,
                           total_workers=total_workers,
                           payment=payment)


@salary_bp.route('/salary/generate', methods=['GET', 'POST'])
def generate():
    companies = Company.query.all()
    workers   = Worker.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        month         = int(request.form['month'])
        year          = int(request.form['year'])
        company_id    = int(request.form['company_id'])
        days_in_month = MONTH_DAYS.get(month, 30)

        deployments = Deployment.query.filter_by(
            company_id=company_id, is_active=True
        ).all()

        count = 0
        for dep in deployments:
            worker = dep.worker

            # Count attendance
            days_present = Attendance.query.filter_by(
                worker_id=dep.worker_id
            ).filter(
                db.func.strftime('%m', Attendance.date)
                    == '%02d' % month,
                db.func.strftime('%Y', Attendance.date)
                    == str(year),
                Attendance.status == 'P'
            ).count()

            # Add half days as 0.5
            half_days = Attendance.query.filter_by(
                worker_id=dep.worker_id
            ).filter(
                db.func.strftime('%m', Attendance.date)
                    == '%02d' % month,
                db.func.strftime('%Y', Attendance.date)
                    == str(year),
                Attendance.status == 'H'
            ).count()

            days_present = days_present + (half_days * 0.5)

            if days_present == 0:
                days_present = days_in_month

            # Get salary structure
            from app.models.salary import SalaryStructure
            from app.utils.salary_engine import calculate_salary

            structure = SalaryStructure.query.filter_by(
                company_id=company_id,
                post=worker.post
            ).first()
            if not structure:
                structure = SalaryStructure.query.filter_by(
                    company_id=None,
                    post=worker.post
                ).first()

            if structure:
                basic = structure.basic
                result = calculate_salary(
                    structure, basic,
                    days_in_month, days_present
                )
            else:
                class DefaultStructure:
                    da_type='percent'; da_value=10
                    hra_type='percent'; hra_value=20
                    special_type='percent'; special_value=5
                    bonus_type='percent'; bonus_value=0
                    epf_applicable=True; esic_applicable=True
                basic  = 10000
                result = calculate_salary(
                    DefaultStructure(), basic,
                    days_in_month, days_present
                )

            # Check existing salary record
            existing = Salary.query.filter_by(
                worker_id=dep.worker_id,
                company_id=company_id,
                month=month, year=year
            ).first()

            if existing:
                sal = existing
            else:
                sal = Salary(
                    worker_id=dep.worker_id,
                    company_id=company_id,
                    month=month, year=year
                )
                db.session.add(sal)

            sal.basic             = result['earned_basic']
            sal.da                = result['da']
            sal.hra               = result['hra']
            sal.special_allowance = result['special']
            sal.gross             = result['gross']
            sal.pf_employee       = result['pf_employee']
            sal.esic_employee     = result['esic_employee']
            sal.total_deductions  = result['total_deductions']
            sal.net_pay           = result['net_pay']
            sal.days_present      = int(days_present)

            # Deduct pending advances
            from app.models.salary import Advance
            pending_advances = Advance.query.filter_by(
                worker_id=dep.worker_id,
                company_id=company_id,
                month=month, year=year,
                is_deducted=False
            ).all()

            total_advance = sum(
                a.amount for a in pending_advances)
            sal.advance          = total_advance
            sal.total_deductions = round(
                result['total_deductions'] + total_advance, 2)
            sal.net_pay = round(
                sal.gross - sal.total_deductions, 2)

            for a in pending_advances:
                a.is_deducted = True

            # Save compliance
            comp = Compliance.query.filter_by(
                worker_id=dep.worker_id,
                company_id=company_id,
                month=month, year=year
            ).first()
            if not comp:
                comp = Compliance(
                    worker_id=dep.worker_id,
                    company_id=company_id,
                    month=month, year=year
                )
                db.session.add(comp)

            comp.pf_employee   = result['pf_employee']
            comp.pf_employer   = result['pf_employer']
            comp.esic_employee = result['esic_employee']
            comp.esic_employer = result['esic_employer']

            count += 1

        db.session.commit()
        flash(f'Salary generated for {count} workers!',
              'success')
        return redirect(url_for('salary.index',
                                month=month, year=year,
                                company_id=company_id))

    return render_template('salary/generate.html',
                           companies=companies,
                           workers=workers,
                           current_month=date.today().month,
                           current_year=date.today().year)


@salary_bp.route('/salary/slip/<int:id>')
def slip(id):
    sal = Salary.query.get_or_404(id)
    return render_template('salary/slip.html', sal=sal)


@salary_bp.route('/salary/pay', methods=['POST'])
def pay():
    month      = int(request.form['month'])
    year       = int(request.form['year'])
    company_id = int(request.form['company_id'])

    # Get selected salary IDs or all for company
    selected_ids = request.form.getlist('selected_ids')

    if selected_ids:
        salaries = Salary.query.filter(
            Salary.id.in_([int(i) for i in selected_ids])
        ).all()
    else:
        salaries = Salary.query.filter_by(
            company_id=company_id,
            month=month,
            year=year
        ).all()

    if not salaries:
        flash('No salary records found!', 'warning')
        return redirect(url_for('salary.index'))

    # Create or update payment record
    payment = SalaryPayment.query.filter_by(
        company_id=company_id,
        month=month,
        year=year
    ).first()

    if not payment:
        payment = SalaryPayment(
            company_id=company_id,
            month=month,
            year=year
        )
        db.session.add(payment)

    from datetime import datetime
    payment.total_amount  = sum(s.net_pay for s in salaries)
    payment.total_workers = len(salaries)
    payment.paid_by       = session.get('user_id')
    payment.paid_at       = datetime.utcnow()
    payment.status        = 'paid'
    payment.notes         = request.form.get('notes', '')
    db.session.commit()

    flash(f'Salary marked as paid for {len(salaries)} '
          f'employees! Total: ₹{payment.total_amount:,.2f}',
          'success')
    return redirect(url_for('salary.payment_sheet',
                            month=month, year=year,
                            company_id=company_id))


@salary_bp.route('/salary/payment-sheet')
@login_required
@permission_required('payment', 'view')
def payment_sheet():
    month      = int(request.args.get('month',
                     date.today().month))
    year       = int(request.args.get('year',
                     date.today().year))
    company_id = request.args.get('company_id', '')
    companies  = Company.query.all()

    query = Salary.query.filter_by(month=month, year=year)
    if company_id:
        query = query.filter_by(company_id=int(company_id))
    salaries = query.order_by(Salary.worker_id).all()

    payment = None
    if company_id:
        payment = SalaryPayment.query.filter_by(
            company_id=int(company_id),
            month=month,
            year=year
        ).first()

    return render_template('salary/payment_sheet.html',
                           salaries=salaries,
                           month=month, year=year,
                           month_name=MONTH_NAMES[month],
                           companies=companies,
                           company_id=company_id,
                           payment=payment)


@salary_bp.route('/salary/export-payment-excel')
def export_payment_excel():
    from app.utils.export import export_payment_to_excel
    month      = int(request.args.get('month',
                     date.today().month))
    year       = int(request.args.get('year',
                     date.today().year))
    company_id = request.args.get('company_id', '')

    query = Salary.query.filter_by(month=month, year=year)
    if company_id:
        query = query.filter_by(company_id=int(company_id))
    salaries = query.all()

    output   = export_payment_to_excel(salaries, month, year)
    filename = f'Payment_Sheet_{MONTH_NAMES[month]}_{year}.xlsx'
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@salary_bp.route('/salary/slips')
@login_required
@permission_required('slips', 'view')
def slips():
    month      = int(request.args.get('month',
                     date.today().month))
    year       = int(request.args.get('year',
                     date.today().year))
    company_id = request.args.get('company_id', '')
    search     = request.args.get('search', '').strip()
    companies  = Company.query.all()

    query = Salary.query.filter_by(
        month=month, year=year
    )
    if company_id:
        query = query.filter_by(
            company_id=int(company_id))
    salaries = query.all()

    # Filter by employee search
    if search:
        salaries = [
            s for s in salaries
            if search.lower() in
               s.worker.full_name.lower()
            or search.lower() in
               (s.worker.employee_id or '').lower()
        ]

    return render_template('salary/slips.html',
                           salaries=salaries,
                           month=month, year=year,
                           month_name=MONTH_NAMES[month],
                           companies=companies,
                           company_id=company_id,
                           search=search)

@salary_bp.route('/salary/export-slips-pdf', methods=['POST'])
def export_slips_pdf():
    from app.utils.export import export_slips_to_excel
    month      = int(request.form['month'])
    year       = int(request.form['year'])
    company_id = request.form.get('company_id', '')
    worker_ids = request.form.getlist('worker_ids')

    query = Salary.query.filter_by(month=month, year=year)
    if company_id:
        query = query.filter_by(company_id=int(company_id))
    if worker_ids:
        query = query.filter(
            Salary.worker_id.in_(
                [int(i) for i in worker_ids]
            )
        )
    salaries = query.all()

    if not salaries:
        flash('No salary records found!', 'warning')
        return redirect(url_for('salary.slips'))

    output   = export_slips_to_excel(salaries, month, year)
    filename = f'Salary_Slips_{MONTH_NAMES[month]}_{year}.xlsx'
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )
