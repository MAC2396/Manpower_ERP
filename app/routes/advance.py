from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import date

advance_bp = Blueprint('advance', __name__)


@advance_bp.route('/advance')
def index():
    from app import db
    from app.models.salary import Advance
    from app.routes.auth import check_permission
    if not check_permission('advance', 'view'):
        flash('Access denied!', 'danger')
        from flask import redirect
        return redirect('/')
    advances = Advance.query.order_by(
        Advance.date_given.desc()).all()
    return render_template('advance/index.html',
                           advances=advances)


@advance_bp.route('/advance/add', methods=['GET', 'POST'])
def add():
    from app import db
    from app.models.salary import Advance
    from app.models.client import Company
    from app.models.worker import Worker

    companies = Company.query.all()
    workers   = Worker.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        from datetime import datetime
        date_given = datetime.strptime(
            request.form['date_given'], '%Y-%m-%d'
        ).date()

        adv = Advance(
            worker_id  = int(request.form['worker_id']),
            company_id = int(request.form['company_id']),
            amount     = float(request.form['amount']),
            date_given = date_given,
            reason     = request.form['reason'],
            month      = int(request.form['month']),
            year       = int(request.form['year']),
            is_deducted = False
        )
        db.session.add(adv)
        db.session.commit()
        flash(f'Advance of ₹{adv.amount} recorded for '
              f'{adv.worker.full_name}!', 'success')
        return redirect(url_for('advance.index'))

    return render_template('advance/add.html',
                           companies=companies,
                           workers=workers,
                           today=date.today().isoformat(),
                           current_month=date.today().month,
                           current_year=date.today().year)


@advance_bp.route('/advance/delete/<int:id>')
def delete(id):
    from app import db
    from app.models.salary import Advance
    adv = Advance.query.get_or_404(id)
    if adv.is_deducted:
        flash('Cannot delete — advance already deducted from salary!',
              'warning')
        return redirect(url_for('advance.index'))
    db.session.delete(adv)
    db.session.commit()
    flash('Advance record deleted.', 'info')
    return redirect(url_for('advance.index'))
