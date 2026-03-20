from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, jsonify)
from app import db
from app.models.salary import SalaryStructure, SalaryComponent
from app.models.client import Company

structure_bp = Blueprint('structure', __name__)


@structure_bp.route('/structure')
def index():
    structures = SalaryStructure.query.order_by(
        SalaryStructure.company_id,
        SalaryStructure.post
    ).all()
    return render_template('structure/index.html',
                           structures=structures)


@structure_bp.route('/structure/add',
                    methods=['GET', 'POST'])
def add():
    companies = Company.query.all()
    if request.method == 'POST':
        company_id = request.form.get('company_id') or None
        if company_id:
            company_id = int(company_id)

        existing = SalaryStructure.query.filter_by(
            company_id=company_id,
            post=request.form['post']
        ).first()
        if existing:
            flash('Structure already exists!', 'warning')
            return redirect(url_for('structure.index'))

        s = SalaryStructure(
            company_id      = company_id,
            post            = request.form['post'],
            basic           = float(request.form['basic']),
            da_type         = request.form.get(
                                  'da_type', 'percent'),
            da_value        = float(request.form.get(
                                  'da_value', 10)),
            hra_type        = request.form.get(
                                  'hra_type', 'percent'),
            hra_value       = float(request.form.get(
                                  'hra_value', 20)),
            special_type    = request.form.get(
                                  'special_type', 'percent'),
            special_value   = float(request.form.get(
                                  'special_value', 5)),
            bonus_type      = request.form.get(
                                  'bonus_type', 'percent'),
            bonus_value     = float(request.form.get(
                                  'bonus_value', 0)),
            epf_applicable  = 'epf_applicable' in request.form,
            esic_applicable = 'esic_applicable' in request.form
        )
        db.session.add(s)
        db.session.flush()

        # Save custom components
        names  = request.form.getlist('comp_name[]')
        types  = request.form.getlist('comp_type[]')
        values = request.form.getlist('comp_value[]')

        for name, ctype, value in zip(names, types, values):
            if name.strip() and value:
                comp = SalaryComponent(
                    structure_id = s.id,
                    name         = name.strip(),
                    comp_type    = ctype,
                    value        = float(value)
                )
                db.session.add(comp)

        db.session.commit()
        flash('Salary structure added!', 'success')
        return redirect(url_for('structure.index'))

    return render_template('structure/add.html',
                           companies=companies)


@structure_bp.route('/structure/edit/<int:id>',
                    methods=['GET', 'POST'])
def edit(id):
    s         = SalaryStructure.query.get_or_404(id)
    companies = Company.query.all()

    if request.method == 'POST':
        company_id = request.form.get('company_id') or None
        if company_id:
            company_id = int(company_id)

        s.company_id      = company_id
        s.post            = request.form['post']
        s.basic           = float(request.form['basic'])
        s.da_type         = request.form.get(
                                'da_type', 'percent')
        s.da_value        = float(request.form.get(
                                'da_value', 10))
        s.hra_type        = request.form.get(
                                'hra_type', 'percent')
        s.hra_value       = float(request.form.get(
                                'hra_value', 20))
        s.special_type    = request.form.get(
                                'special_type', 'percent')
        s.special_value   = float(request.form.get(
                                'special_value', 5))
        s.bonus_type      = request.form.get(
                                'bonus_type', 'percent')
        s.bonus_value     = float(request.form.get(
                                'bonus_value', 0))
        s.epf_applicable  = 'epf_applicable' in request.form
        s.esic_applicable = 'esic_applicable' in request.form

        # Delete old custom components and re-save
        SalaryComponent.query.filter_by(
            structure_id=s.id
        ).delete()

        names  = request.form.getlist('comp_name[]')
        types  = request.form.getlist('comp_type[]')
        values = request.form.getlist('comp_value[]')

        for name, ctype, value in zip(names, types, values):
            if name.strip() and value:
                comp = SalaryComponent(
                    structure_id = s.id,
                    name         = name.strip(),
                    comp_type    = ctype,
                    value        = float(value)
                )
                db.session.add(comp)

        db.session.commit()
        flash('Structure updated!', 'success')
        return redirect(url_for('structure.index'))

    return render_template('structure/edit.html',
                           s=s, companies=companies)


@structure_bp.route('/structure/delete/<int:id>')
def delete(id):
    s = SalaryStructure.query.get_or_404(id)
    SalaryComponent.query.filter_by(
        structure_id=s.id
    ).delete()
    db.session.delete(s)
    db.session.commit()
    flash('Structure deleted.', 'info')
    return redirect(url_for('structure.index'))
