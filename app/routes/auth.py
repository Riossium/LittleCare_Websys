from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User
from app.models.doctor import DoctorProfile
from app.forms.auth_forms import (
    LoginForm, ParentRegistrationForm, DoctorRegistrationForm,
    ForgotPasswordForm, ResetPasswordForm, ProfileUpdateForm
)
from app.utils import save_uploaded_file, log_audit

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Module 2: Parent Registration"""
    if current_user.is_authenticated:
        return redirect_to_role_dashboard(current_user)

    form = ParentRegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data.lower().strip(),
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            phone=form.phone.data.strip() if form.phone.data else None,
            role='parent',
            is_active=True
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        log_audit(user.id, 'USER_REGISTER_PARENT', f"Parent account registered: {user.email}", request.remote_addr)
        login_user(user)
        flash(f"Welcome to LittleCare, {user.first_name}! Let's create your baby's health profile to get started.", "success")
        return redirect(url_for('parent.dashboard'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/register/doctor', methods=['GET', 'POST'])
def register_doctor():
    """Module 2: Doctor Registration with License Credentials"""
    if current_user.is_authenticated:
        return redirect_to_role_dashboard(current_user)

    form = DoctorRegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data.lower().strip(),
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            phone=form.phone.data.strip(),
            role='doctor',
            is_active=True
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        doctor_prof = DoctorProfile(
            user_id=user.id,
            specialty=form.specialty.data,
            license_number=form.license_number.data.strip(),
            ptr_number=form.ptr_number.data.strip() if form.ptr_number.data else None,
            clinic_affiliation=form.clinic_affiliation.data.strip(),
            clinic_address=form.clinic_address.data.strip() if form.clinic_address.data else None,
            experience_years=form.experience_years.data or 1,
            consultation_types=form.consultation_types.data,
            bio=form.bio.data.strip() if form.bio.data else None,
            is_verified=False  # Must be approved by administrator
        )
        db.session.add(doctor_prof)
        db.session.commit()

        log_audit(user.id, 'DOCTOR_REGISTRATION', f"Doctor submitted credentials for license {doctor_prof.license_number}", request.remote_addr)
        flash("Registration submitted! Your medical credentials (PRC license) have been received and are pending administrator verification. You will be notified once activated.", "info")
        return redirect(url_for('auth.login'))

    return render_template('auth/register_doctor.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Module 2: Unified Login with Role-based Redirects"""
    if current_user.is_authenticated:
        return redirect_to_role_dashboard(current_user)

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("Your account is currently disabled. Please contact LittleCare support.", "danger")
                return render_template('auth/login.html', form=form)

            login_user(user, remember=form.remember_me.data)
            log_audit(user.id, 'USER_LOGIN', f"User logged in from {request.remote_addr}", request.remote_addr)

            # Check next URL if safe
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)

            return redirect_to_role_dashboard(user)
        else:
            flash("Invalid email or password. Please verify your credentials and try again.", "danger")

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Module 2: Logout"""
    user_id = current_user.id
    logout_user()
    session.pop('active_baby_id', None)
    log_audit(user_id, 'USER_LOGOUT', "User signed out", request.remote_addr)
    flash("You have been signed out successfully. Take care of your little one!", "info")
    return redirect(url_for('main.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Module 2: Forgot Password Workflow"""
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user:
            session['reset_email'] = user.email
            flash(f"Password reset instructions have been generated for {user.email}. In this development environment, you can now enter your new password below.", "success")
            return redirect(url_for('auth.reset_password'))
        else:
            flash("If an account exists with that email address, reset instructions have been dispatched.", "info")
            return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Module 2: Reset Password Action"""
    reset_email = session.get('reset_email')
    if not reset_email:
        flash("Password reset session expired. Please submit a new request.", "warning")
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=reset_email).first()
        if user:
            user.set_password(form.password.data)
            db.session.commit()
            session.pop('reset_email', None)
            log_audit(user.id, 'PASSWORD_RESET', "Password reset successfully", request.remote_addr)
            flash("Your password has been reset successfully! Please sign in with your new password.", "success")
            return redirect(url_for('auth.login'))
        flash("User not found.", "danger")
        return redirect(url_for('auth.forgot_password'))

    return render_template('auth/reset_password.html', form=form, email=reset_email)


def redirect_to_role_dashboard(user):
    """Directs user to their appropriate role-based dashboard."""
    if user.is_admin:
        return redirect(url_for('admin.dashboard'))
    elif user.is_doctor:
        return redirect(url_for('doctors.dashboard'))
    else:
        return redirect(url_for('parent.dashboard'))
