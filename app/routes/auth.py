from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, session)

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def hr_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('user_role') not in ['admin', 'hr']:
            flash('Access denied. HR/Admin only.',
                  'danger')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin only.', 'danger')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated


def check_permission(module, action='view'):
    """
    Check if current logged in user has
    permission for a module and action.
    Admin and HR always have full access.
    Supervisors are checked against UserPermission table.
    """
    if 'user_id' not in session:
        return False

    role = session.get('user_role', '')

    # Admin and HR have full access always
    if role in ['admin', 'hr']:
        return True

    # Supervisor — check permissions table
    from app.models.user import UserPermission
    perm = UserPermission.query.filter_by(
        user_id=session['user_id'],
        module=module
    ).first()

    if not perm:
        return False

    return getattr(perm, f'can_{action}', False)


def permission_required(module, action='view'):
    """
    Decorator to protect routes based on permissions.
    Use like: @permission_required('salary', 'view')
    """
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            if not check_permission(module, action):
                flash(
                    f'You do not have permission to '
                    f'access this page. Contact Admin.',
                    'danger'
                )
                return redirect('/')
            return f(*args, **kwargs)
        return decorated
    return decorator


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect('/')

    if request.method == 'POST':
        from app.models.user import User
        username = request.form['username']
        password = request.form['password']
        user     = User.query.filter_by(
            username=username,
            is_active=True
        ).first()

        if user and user.check_password(password):
            session['user_id']   = user.id
            session['user_name'] = user.full_name
            session['user_role'] = user.role

            # Load permissions into session
            # for quick access
            _load_permissions_to_session(user)

            flash(f'Welcome {user.full_name}!',
                  'success')
            return redirect('/')
        else:
            flash('Invalid username or password.',
                  'danger')

    return render_template('auth/login.html')


def _load_permissions_to_session(user):
    """Load user permissions into session on login."""
    from app.models.user import UserPermission
    if user.role in ['admin', 'hr']:
        session['permissions'] = 'full'
        return

    perms = UserPermission.query.filter_by(
        user_id=user.id
    ).all()

    perm_dict = {}
    for p in perms:
        perm_dict[p.module] = {
            'view'  : p.can_view,
            'add'   : p.can_add,
            'edit'  : p.can_edit,
            'delete': p.can_delete,
            'export': p.can_export,
        }
    session['permissions'] = perm_dict


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
