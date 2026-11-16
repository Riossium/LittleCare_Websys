import os
import uuid
from functools import wraps
from flask import abort, session, current_app, redirect, url_for, flash
from flask_login import current_user
from werkzeug.utils import secure_filename
from app.models.baby import BabyProfile


def role_required(*roles):
    """Decorator to enforce role-based access control."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                flash("Access denied: You do not have permission to view this page.", "danger")
                if current_user.is_parent:
                    return redirect(url_for('parent.dashboard'))
                elif current_user.is_doctor:
                    return redirect(url_for('doctors.dashboard'))
                elif current_user.is_admin:
                    return redirect(url_for('admin.dashboard'))
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def parent_required(f):
    return role_required('parent')(f)


def doctor_required(f):
    return role_required('doctor')(f)


def admin_required(f):
    return role_required('admin')(f)


def get_active_baby():
    """
    Retrieves the currently selected baby for the logged-in parent.
    Checks session['active_baby_id'], otherwise defaults to the first baby profile.
    """
    if not current_user.is_authenticated or not current_user.is_parent:
        return None

    active_id = session.get('active_baby_id')
    if active_id:
        baby = BabyProfile.query.filter_by(id=active_id, parent_id=current_user.id, is_active=True).first()
        if baby:
            return baby

    # Default to first active baby
    first_baby = current_user.baby_profiles.filter_by(is_active=True).first()
    if first_baby:
        session['active_baby_id'] = first_baby.id
        return first_baby

    return None


def save_uploaded_file(file_storage, folder_name='babies'):
    """Securely saves an uploaded file and returns its generated unique filename."""
    if not file_storage or not hasattr(file_storage, 'filename') or not file_storage.filename:
        return None

    original_name = secure_filename(file_storage.filename)
    ext = os.path.splitext(original_name)[1].lower()
    unique_name = f"{uuid.uuid4().hex[:12]}_{original_name}"
    
    dest_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], folder_name)
    os.makedirs(dest_dir, exist_ok=True)
    
    file_path = os.path.join(dest_dir, unique_name)
    file_storage.save(file_path)
    return unique_name


def log_audit(user_id, action, details=None, ip_address=None):
    """Logs system security and privacy actions for compliance with data privacy regulations."""
    from app.extensions import db
    from app.models.permission_audit import AuditLog
    
    log = AuditLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address
    )
    db.session.add(log)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    return log

