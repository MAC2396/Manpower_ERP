from flask import (Flask, render_template, session,
                   redirect, url_for)
from flask_sqlalchemy import SQLAlchemy
from config import Config
import time

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from app.routes.clients    import clients_bp
    from app.routes.workers    import workers_bp
    from app.routes.deployment import deployment_bp
    from app.routes.salary     import salary_bp
    from app.routes.reports    import reports_bp
    from app.routes.attendance import attendance_bp
    from app.routes.structure  import structure_bp
    from app.routes.advance    import advance_bp
    from app.routes.auth       import auth_bp
    from app.routes.users      import users_bp
    from app.routes.approval   import approval_bp
    from app.routes.letters    import letters_bp

    app.register_blueprint(clients_bp)
    app.register_blueprint(workers_bp)
    app.register_blueprint(deployment_bp)
    app.register_blueprint(salary_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(structure_bp)
    app.register_blueprint(advance_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(approval_bp)
    app.register_blueprint(letters_bp)

    # Serve uploaded files
    from flask import send_from_directory
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(
            app.config['UPLOAD_FOLDER'], filename)

    # Make check_permission available in all templates
    from app.routes.auth import check_permission
    app.jinja_env.globals['check_permission'] = \
        check_permission

    # Simple dashboard cache
    dashboard_cache = {}

    @app.route('/')
    def dashboard():
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))

        from app.models.client import Company, Requirement
        from app.models.worker import Worker
        from app.models.salary import Advance
        from app.models.deployment import Deployment
        from app.models.deployment_request import \
            DeploymentRequest
        from app.models.user import User
        from app.routes.auth import check_permission
        from datetime import date, datetime

        current_month = date.today().month
        current_year  = date.today().year
        current_user  = User.query.get(
                            session['user_id'])
        now           = datetime.now()

        # Cache key per user per month
        cache_key = (
            f"{session['user_id']}_"
            f"{current_month}_{current_year}"
        )

        # Use cache if less than 60 seconds old
        cached = dashboard_cache.get(cache_key)
        if cached and time.time() - cached['ts'] < 60:
            stats = cached['stats']
        else:
            stats = {
                'companies':
                    Company.query.count()
                    if check_permission('clients')
                    else None,

                'workers':
                    Worker.query.filter_by(
                        is_active=True).count()
                    if check_permission('workers')
                    else None,

                'kyc_pending':
                    sum(1 for w in Worker.query.all()
                        if not w.kyc_complete())
                    if check_permission('workers')
                    else None,

                'requirements':
                    Requirement.query.filter_by(
                        month=current_month,
                        year=current_year).count()
                    if check_permission('deployment')
                    else None,

                'active_deployments':
                    Deployment.query.filter_by(
                        is_active=True).count()
                    if check_permission('deployment')
                    else None,

                'pending_advances':
                    sum(a.amount for a in
                        Advance.query.filter_by(
                            is_deducted=False).all())
                    if check_permission('advance')
                    else None,

                'pending_approvals':
                    DeploymentRequest.query.filter_by(
                        status='pending').count()
                    if check_permission('approval')
                    else None,
            }

            # Save to cache
            dashboard_cache[cache_key] = {
                'stats': stats,
                'ts'   : time.time()
            }

        # Recent workers
        recent_workers = Worker.query.order_by(
            Worker.id.desc()).limit(5).all() \
            if check_permission('workers') else []

        return render_template(
            'dashboard.html',
            stats=stats,
            recent_workers=recent_workers,
            current_user=current_user,
            now=now
        )

    return app
