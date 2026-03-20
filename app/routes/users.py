from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, session)
from app import db
from app.models.user import User, SupervisorAssignment
from app.models.client import Company
from app.routes.auth import admin_required

users_bp = Blueprint('users', __name__)


@users_bp.route('/users')
@admin_required
def index():
    users = User.query.order_by(
        User.role, User.full_name
    ).all()
    return render_template('users/index.html', users=users)


@users_bp.route('/users/add', methods=['GET', 'POST'])
@admin_required
def add():
    companies = Company.query.all()
    if request.method == 'POST':
        if User.query.filter_by(
            username=request.form['username']
        ).first():
            flash('Username already exists!', 'warning')
            return redirect(url_for('users.add'))

        user = User(
            username  = request.form['username'],
            full_name = request.form['full_name'],
            email     = request.form.get('email'),
            mobile    = request.form.get('mobile'),
            role      = request.form['role']
        )
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.flush()

        # Assign ONE company to supervisor
        if user.role == 'supervisor':
            company_id = request.form.get('company_id')
            if company_id:
                assignment = SupervisorAssignment(
                    supervisor_id = user.id,
                    company_id    = int(company_id)
                )
                db.session.add(assignment)

        db.session.commit()
        flash(f'User {user.full_name} created!', 'success')
        return redirect(url_for('users.index'))

    return render_template('users/add.html',
                           companies=companies)


@users_bp.route('/users/<int:id>/toggle')
@admin_required
def toggle(id):
    from flask import session
    user = User.query.get_or_404(id)
    if user.id == session.get('user_id'):
        flash('Cannot deactivate your own account!', 'warning')
        return redirect(url_for('users.index'))
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.full_name} {status}.', 'info')
    return redirect(url_for('users.index'))


@users_bp.route('/users/<int:id>/reset-password',
                methods=['GET', 'POST'])
@admin_required
def reset_password(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.set_password(request.form['password'])
        db.session.commit()
        flash(f'Password reset for {user.full_name}!',
              'success')
        return redirect(url_for('users.index'))
    return render_template('users/reset_password.html',
                           user=user)

# All available modules
MODULES = [
    ('dashboard',   'Dashboard'),
    ('clients',     'Client Companies'),
    ('workers',     'Employee ID & KYC'),
    ('deployment',  'Deployment'),
    ('approval',    'Approvals'),
    ('attendance',  'Attendance'),
    ('letters',     'Letters'),
    ('structure',   'Salary Structure'),
    ('salary',      'Salary'),
    ('slips',       'Salary Slips'),
    ('payment',     'Payment Sheet'),
    ('advance',     'Advances'),
    ('reports',     'Reports & Export'),
]

@users_bp.route('/users/<int:id>/permissions',
                methods=['GET', 'POST'])
@admin_required
def permissions(id):
    from app.models.user import UserPermission
    user = User.query.get_or_404(id)

    if user.role in ['admin', 'hr']:
        flash(
            f'{user.role.upper()} users have full '
            f'access to all modules by default.',
            'info'
        )
        return redirect(url_for('users.index'))

    if request.method == 'POST':
        # Delete all existing permissions for this user
        UserPermission.query.filter_by(
            user_id=id
        ).delete()
        db.session.flush()

        # Save new permissions from form
        saved = 0
        for module, _ in MODULES:
            can_view   = f'{module}_view'   in request.form
            can_add    = f'{module}_add'    in request.form
            can_edit   = f'{module}_edit'   in request.form
            can_delete = f'{module}_delete' in request.form
            can_export = f'{module}_export' in request.form

            # Save even if only view is checked
            if can_view or can_add or can_edit \
               or can_delete or can_export:
                perm = UserPermission(
                    user_id    = id,
                    module     = module,
                    can_view   = can_view,
                    can_add    = can_add,
                    can_edit   = can_edit,
                    can_delete = can_delete,
                    can_export = can_export
                )
                db.session.add(perm)
                saved += 1

        db.session.commit()

        # Update session if this user is logged in
        if session.get('user_id') == id:
            from app.routes.auth import \
                _load_permissions_to_session
            _load_permissions_to_session(user)

        flash(
            f'Permissions saved for '
            f'{user.full_name}! '
            f'{saved} module(s) configured. '
            f'User must logout and login again '
            f'to see updated menu.',
            'success'
        )
        return redirect(url_for('users.index'))

    # GET — show current permissions
    existing = {
        p.module: p for p in
        UserPermission.query.filter_by(
            user_id=id
        ).all()
    }

    return render_template(
        'users/permissions.html',
        user=user,
        modules=MODULES,
        existing=existing
    )
