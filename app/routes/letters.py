from flask import (Blueprint, render_template, request,
                   make_response, redirect, url_for)
from app.models.worker import Worker
from app.models.client import Company
from app.models.deployment import Deployment
from datetime import date
from app.routes.auth import (login_required,
                              permission_required)

letters_bp = Blueprint('letters', __name__)


@letters_bp.route('/letters')
@login_required
@permission_required('letters', 'view')
def index():
    workers   = Worker.query.filter_by(
                    is_active=True).all()
    companies = Company.query.all()
    return render_template('letters/index.html',
                           workers=workers,
                           companies=companies)


@letters_bp.route('/letters/joining/<int:worker_id>')
def joining(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    dep    = Deployment.query.filter_by(
        worker_id=worker_id,
        is_active=True
    ).first()
    today  = date.today()
    return render_template('letters/joining.html',
                           worker=worker,
                           dep=dep,
                           today=today)


@letters_bp.route('/letters/experience/<int:worker_id>')
def experience(worker_id):
    worker = Worker.query.get_or_404(worker_id)
    dep    = Deployment.query.filter_by(
        worker_id=worker_id
    ).order_by(Deployment.id.desc()).first()
    today  = date.today()
    return render_template('letters/experience.html',
                           worker=worker,
                           dep=dep,
                           today=today)
