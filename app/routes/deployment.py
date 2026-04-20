from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models.client import Company, Requirement
from app.models.worker import Worker
from app.models.deployment import Deployment
from datetime import date

deployment_bp = Blueprint('deployment', __name__)

@deployment_bp.route('/deployment')
def index():
    # Get all requirements with deployment counts
    companies  = Company.query.all()
    requirements = Requirement.query.order_by(
        Requirement.year.desc(), Requirement.month.desc()
    ).all()

    # For each requirement calculate deployed vs required
    req_data = []
    for req in requirements:
        deployed = Deployment.query.filter_by(
            company_id = req.company_id,
            post       = req.post,
            is_active  = True
        ).count()
        req_data.append({
            'req'      : req,
            'deployed' : deployed,
            'diff'     : deployed - req.required_count,
            'status'   : 'ok' if deployed == req.required_count
                         else ('short' if deployed < req.required_count else 'excess')
        })

    return render_template('deployment/index.html',
                           req_data=req_data, companies=companies)


@deployment_bp.route('/deployment/add-requirement', methods=['GET', 'POST'])
def add_requirement():
    companies = Company.query.all()
    if request.method == 'POST':
        req = Requirement(
            company_id     = request.form['company_id'],
            post           = request.form['post'],
            required_count = request.form['required_count'],
            month          = request.form['month'],
            year           = request.form['year'],
            shift          = request.form['shift'],
            notes          = request.form['notes']
        )
        db.session.add(req)
        db.session.commit()
        flash('Requirement added successfully!', 'success')
        return redirect(url_for('deployment.index'))
    return render_template('deployment/add_requirement.html',
                           companies=companies,
                           current_month=date.today().month,
                           current_year=date.today().year)


@deployment_bp.route('/deployment/add', methods=['GET', 'POST'])
def add():
    companies = Company.query.all()
    workers   = Worker.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        # Convert date string to Python date object
        from datetime import datetime
        date_from_str = request.form['date_from']
        date_from_obj = datetime.strptime(date_from_str, '%Y-%m-%d').date()

        # Deactivate previous deployment of this worker if any
        old = Deployment.query.filter_by(
            worker_id=request.form['worker_id'], is_active=True
        ).first()
        if old:
            old.is_active = False
            old.date_to   = date.today()

        dep = Deployment(
            worker_id  = request.form['worker_id'],
            company_id = request.form['company_id'],
            post       = request.form['post'],
            date_from  = date_from_obj,
            is_active  = True
        )
        db.session.add(dep)
        db.session.commit()
        flash('Worker deployed successfully!', 'success')
        return redirect(url_for('deployment.index'))
    return render_template('deployment/add.html',
                           companies=companies, workers=workers,
                           today=date.today().isoformat())


@deployment_bp.route('/deployment/end/<int:id>')
def end(id):
    dep = Deployment.query.get_or_404(id)
    dep.is_active = False
    dep.date_to   = date.today()
    db.session.commit()
    flash('Deployment ended.', 'info')
    return redirect(url_for('deployment.index'))


@deployment_bp.route('/deployment/bulk-add',
                     methods=['GET', 'POST'])
def bulk_add():
    from app import db
    from app.models.worker import Worker
    from app.models.client import Company
    from app.models.deployment import Deployment
    from datetime import datetime, date

    companies = Company.query.all()
    workers   = Worker.query.filter_by(
                    is_active=True).all()

    if request.method == 'POST':
        company_id  = int(request.form['company_id'])
        post        = request.form['post']
        date_from   = datetime.strptime(
            request.form['date_from'], '%Y-%m-%d'
        ).date()
        worker_ids  = request.form.getlist(
            'worker_ids')

        if not worker_ids:
            flash('Please select at least one employee!',
                  'warning')
            return redirect(
                url_for('deployment.bulk_add'))

        count = 0
        for wid in worker_ids:
            wid = int(wid)
            # Deactivate existing deployment
            old = Deployment.query.filter_by(
                worker_id=wid,
                is_active=True
            ).first()
            if old:
                old.is_active = False
                old.date_to   = date.today()

            dep = Deployment(
                worker_id  = wid,
                company_id = company_id,
                post       = post,
                date_from  = date_from,
                is_active  = True
            )
            db.session.add(dep)
            count += 1

        db.session.commit()
        flash(
            f'{count} employee(s) deployed '
            f'successfully!', 'success'
        )
        return redirect(url_for('deployment.index'))

    return render_template(
        'deployment/bulk_add.html',
        companies=companies,
        workers=workers,
        today=date.today().isoformat()
    )