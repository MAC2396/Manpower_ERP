from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models.client import Company, Requirement

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/clients')
def index():
    companies = Company.query.all()
    return render_template('clients/index.html', companies=companies)

@clients_bp.route('/clients/add', methods=['GET', 'POST'])
def add():
    from app import db
    from app.models.client import Company
    if request.method == 'POST':
        company = Company(
            name           = request.form['name'],
            address        = request.form['address'],
            city           = request.form.get('city'),
            state          = request.form.get('state'),
            pincode        = request.form.get('pincode'),
            contact_person = request.form['contact_person'],
            contact_phone  = request.form['contact_phone'],
            email          = request.form['email'],
            gst_number     = request.form['gst_number']
        )
        db.session.add(company)
        db.session.commit()
        flash('Company added successfully!', 'success')
        return redirect(url_for('clients.index'))
    return render_template('clients/add.html')

@clients_bp.route('/clients/<int:id>')
def view(id):
    company = Company.query.get_or_404(id)
    return render_template('clients/view.html', company=company)

@clients_bp.route('/clients/<int:id>/edit',
                  methods=['GET', 'POST'])
def edit(id):
    from app import db
    from app.models.client import Company
    company = Company.query.get_or_404(id)
    if request.method == 'POST':
        company.name           = request.form['name']
        company.address        = request.form['address']
        company.city           = request.form.get('city')
        company.state          = request.form.get('state')
        company.pincode        = request.form.get('pincode')
        company.contact_person = request.form['contact_person']
        company.contact_phone  = request.form['contact_phone']
        company.email          = request.form['email']
        company.gst_number     = request.form['gst_number']
        db.session.commit()
        flash('Company updated successfully!', 'success')
        return redirect(url_for('clients.view', id=company.id))
    return render_template('clients/edit.html',
                           company=company)

@clients_bp.route('/clients/<int:id>/delete')
def delete(id):
    from app import db
    from app.models.client import Company, Requirement
    from app.models.deployment import Deployment
    from app.models.worker import Worker

    company = Company.query.get_or_404(id)

    # Check active deployments
    active_deployments = Deployment.query.filter_by(
        company_id=id, is_active=True
    ).count()

    # Check any deployments ever
    total_deployments = Deployment.query.filter_by(
        company_id=id
    ).count()

    # Check salary records
    from app.models.salary import Salary
    salary_records = Salary.query.filter_by(
        company_id=id
    ).count()

    if active_deployments > 0:
        flash(
            f'Cannot delete "{company.name}" — '
            f'{active_deployments} employee(s) are currently '
            f'deployed here. Remove all deployments first.',
            'danger'
        )
        return redirect(url_for('clients.index'))

    if total_deployments > 0:
        flash(
            f'Cannot delete "{company.name}" — '
            f'This company has deployment history records. '
            f'Deletion not allowed to preserve records.',
            'danger'
        )
        return redirect(url_for('clients.index'))

    if salary_records > 0:
        flash(
            f'Cannot delete "{company.name}" — '
            f'Salary records exist for this company.',
            'danger'
        )
        return redirect(url_for('clients.index'))

    # Safe to delete
    Requirement.query.filter_by(company_id=id).delete()
    db.session.delete(company)
    db.session.commit()
    flash(
        f'Company "{company.name}" deleted successfully!',
        'success'
    )
    return redirect(url_for('clients.index'))
