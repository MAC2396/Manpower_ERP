from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, session)
from app import db
from app.routes.auth import login_required, hr_required
from datetime import date, datetime

approval_bp = Blueprint('approval', __name__)


@approval_bp.route('/approval')
@login_required
def index():
    from app.models.deployment_request import DeploymentRequest
    from app.models.user import User
    user = User.query.get(session['user_id'])

    if user.is_hr():
        requests = DeploymentRequest.query.order_by(
            DeploymentRequest.submitted_at.desc()
        ).all()
    else:
        requests = DeploymentRequest.query.filter_by(
            submitted_by=user.id
        ).order_by(
            DeploymentRequest.submitted_at.desc()
        ).all()

    return render_template('approval/index.html',
                           requests=requests,
                           user=user)


@approval_bp.route('/approval/submit',
                   methods=['GET', 'POST'])
@login_required
def submit():
    from app.models.deployment_request import DeploymentRequest
    from app.models.user import User, SupervisorAssignment
    from app.models.client import Company
    from app.models.worker import Worker

    user = User.query.get(session['user_id'])

    # Supervisor only sees their assigned company
    if user.is_supervisor():
        assignment = SupervisorAssignment.query.filter_by(
            supervisor_id=user.id
        ).first()
        if not assignment:
            flash('You are not assigned to any company yet.',
                  'warning')
            return redirect(url_for('approval.index'))
        companies = [assignment.company]
        # Workers for this company only
        from app.models.deployment import Deployment
        deployed_ids = [
            d.worker_id for d in
            Deployment.query.filter_by(
                company_id=assignment.company_id
            ).all()
        ]
        workers = Worker.query.filter_by(is_active=True).all()
    else:
        companies = Company.query.all()
        workers   = Worker.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        date_from = datetime.strptime(
            request.form['date_from'], '%Y-%m-%d'
        ).date()

        req = DeploymentRequest(
            worker_id    = int(request.form['worker_id']),
            company_id   = int(request.form['company_id']),
            post         = request.form['post'],
            date_from    = date_from,
            notes        = request.form.get('notes'),
            submitted_by = user.id,
            status       = 'pending'
        )
        db.session.add(req)
        db.session.commit()
        flash('Deployment request submitted for approval!',
              'success')
        return redirect(url_for('approval.index'))

    return render_template('approval/submit.html',
                           companies=companies,
                           workers=workers,
                           today=date.today().isoformat(),
                           user=user)


@approval_bp.route('/approval/review/<int:id>',
                   methods=['GET', 'POST'])
@hr_required
def review(id):
    from app.models.deployment_request import DeploymentRequest
    from app.models.deployment import Deployment
    from app.models.client import Company
    from app.models.user import User

    req  = DeploymentRequest.query.get_or_404(id)
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        action = request.form['action']
        req.reviewed_by  = user.id
        req.reviewed_at  = datetime.utcnow()
        req.review_notes = request.form.get('review_notes')
        req.post         = request.form.get('post', req.post)
        req.company_id   = int(request.form.get(
                               'company_id', req.company_id))

        date_str = request.form.get('date_from')
        if date_str:
            req.date_from = datetime.strptime(
                date_str, '%Y-%m-%d').date()

        if action == 'approve':
            req.status = 'approved'
            # Deactivate existing deployment if any
            old = Deployment.query.filter_by(
                worker_id=req.worker_id,
                is_active=True
            ).first()
            if old:
                old.is_active = False
                old.date_to   = date.today()

            dep = Deployment(
                worker_id  = req.worker_id,
                company_id = req.company_id,
                post       = req.post,
                date_from  = req.date_from,
                is_active  = True
            )
            db.session.add(dep)
            db.session.flush()
            req.deployment_id = dep.id
            flash(f'Deployment approved for '
                  f'{req.worker.full_name}!', 'success')

        elif action == 'reject':
            req.status = 'rejected'
            flash('Deployment request rejected.', 'warning')

        db.session.commit()
        return redirect(url_for('approval.index'))

    companies = Company.query.all()
    return render_template('approval/review.html',
                           req=req,
                           companies=companies,
                           user=user)
