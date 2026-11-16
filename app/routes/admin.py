from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime
from app.extensions import db
from app.models.user import User
from app.models.baby import BabyProfile
from app.models.doctor import DoctorProfile
from app.models.appointment import Appointment
from app.models.article import Article
from app.models.permission_audit import AuditLog
from app.forms.article_forms import ArticleForm
from app.utils import admin_required, save_uploaded_file, log_audit
from app.services.reminder_service import create_notification

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Module 12: Admin Analytics & System Dashboard"""
    total_parents = User.query.filter_by(role='parent').count()
    total_doctors = DoctorProfile.query.count()
    pending_doctors = DoctorProfile.query.filter_by(is_verified=False).count()
    total_babies = BabyProfile.query.filter_by(is_active=True).count()
    total_appointments = Appointment.query.count()
    total_articles = Article.query.count()

    recent_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(5).all()
    pending_doctor_list = DoctorProfile.query.filter_by(is_verified=False).limit(5).all()
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(8).all()

    return render_template(
        'admin/dashboard.html',
        total_parents=total_parents,
        total_doctors=total_doctors,
        pending_doctors=pending_doctors,
        total_babies=total_babies,
        total_appointments=total_appointments,
        total_articles=total_articles,
        recent_appointments=recent_appointments,
        pending_doctor_list=pending_doctor_list,
        recent_logs=recent_logs
    )


# =========================================================================
# DOCTOR CREDENTIAL VERIFICATION
# =========================================================================

@admin_bp.route('/doctors')
@login_required
@admin_required
def doctors():
    """Module 12: Doctor Verification & Management"""
    status_filter = request.args.get('status', 'all')
    if status_filter == 'pending':
        doctors_list = DoctorProfile.query.filter_by(is_verified=False).all()
    elif status_filter == 'verified':
        doctors_list = DoctorProfile.query.filter_by(is_verified=True).all()
    else:
        doctors_list = DoctorProfile.query.all()

    return render_template('admin/doctor_verifications.html', doctors=doctors_list, current_status=status_filter)


@admin_bp.route('/doctors/<int:doctor_id>/verify', methods=['POST'])
@login_required
@admin_required
def verify_doctor(doctor_id):
    """Module 12: Approve and Verify Doctor Credentials"""
    doctor = DoctorProfile.query.get_or_404(doctor_id)
    doctor.is_verified = True
    doctor.verification_date = datetime.utcnow()
    doctor.verification_notes = f"Verified by Administrator {current_user.full_name} on {datetime.utcnow().strftime('%Y-%m-%d')}"
    db.session.commit()

    # Notify doctor
    create_notification(
        user_id=doctor.user_id,
        title="Medical Credentials Verified",
        message="Congratulations! Your physician credentials have been approved by the LittleCare medical administration. You can now publish your schedule and accept consultations.",
        notif_type='system',
        link='/doctors/dashboard'
    )

    log_audit(current_user.id, 'DOCTOR_VERIFIED', f"Administrator verified doctor {doctor.doctor_name} (License {doctor.license_number})", request.remote_addr)
    flash(f"{doctor.doctor_name} has been verified and activated successfully!", "success")
    return redirect(url_for('admin.doctors'))


@admin_bp.route('/doctors/<int:doctor_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_doctor(doctor_id):
    """Module 12: Reject / Suspend Doctor Verification"""
    doctor = DoctorProfile.query.get_or_404(doctor_id)
    reason = request.form.get('reason', 'Credentials could not be verified with PRC database')
    doctor.is_verified = False
    doctor.verification_notes = f"Rejected: {reason}"
    db.session.commit()

    create_notification(
        user_id=doctor.user_id,
        title="Credential Verification Update",
        message=f"Your doctor verification request was updated: {reason}. Please contact administration.",
        notif_type='system',
        link='/doctors/dashboard'
    )

    log_audit(current_user.id, 'DOCTOR_VERIFICATION_REJECTED', f"Doctor {doctor.doctor_name} rejected: {reason}", request.remote_addr)
    flash(f"Verification status updated for {doctor.doctor_name}.", "warning")
    return redirect(url_for('admin.doctors'))


# =========================================================================
# USER MANAGEMENT
# =========================================================================

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Module 12: Manage Parent and System Accounts"""
    role = request.args.get('role', 'all')
    query = User.query

    if role != 'all':
        query = query.filter_by(role=role)

    all_users = query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users, current_role=role)


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Module 12: Enable / Disable User Account"""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own administrative account.", "danger")
        return redirect(url_for('admin.users'))

    user.is_active = not user.is_active
    db.session.commit()

    action_label = "activated" if user.is_active else "deactivated"
    log_audit(current_user.id, 'USER_STATUS_TOGGLED', f"User {user.email} was {action_label}", request.remote_addr)
    flash(f"User {user.email} has been {action_label}.", "info")
    return redirect(url_for('admin.users'))


# =========================================================================
# ARTICLE MANAGEMENT
# =========================================================================

@admin_bp.route('/articles')
@login_required
@admin_required
def articles():
    """Module 12: Healthcare Articles Manager"""
    articles_list = Article.query.order_by(Article.created_at.desc()).all()
    return render_template('admin/articles.html', articles=articles_list)


@admin_bp.route('/articles/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_article():
    """Module 12: Add New Educational Article"""
    form = ArticleForm()
    if form.validate_on_submit():
        slug = Article.generate_slug(form.title.data)
        # Check uniqueness
        if Article.query.filter_by(slug=slug).first():
            slug = f"{slug}-{datetime.utcnow().strftime('%y%m%d%H%M')}"

        article = Article(
            title=form.title.data.strip(),
            slug=slug,
            category=form.category.data,
            short_description=form.short_description.data.strip(),
            content=form.content.data.strip(),
            author_name=form.author_name.data.strip(),
            medical_references=form.medical_references.data.strip() if form.medical_references.data else None,
            reading_time_minutes=form.reading_time_minutes.data,
            is_published=form.is_published.data
        )

        if form.featured_image.data:
            img = save_uploaded_file(form.featured_image.data, folder_name='articles')
            if img:
                article.featured_image = img

        db.session.add(article)
        db.session.commit()

        log_audit(current_user.id, 'ARTICLE_CREATED', f"Published article: {article.title}", request.remote_addr)
        flash(f"Article '{article.title}' created successfully!", "success")
        return redirect(url_for('admin.articles'))

    return render_template('admin/article_form.html', form=form, is_edit=False)


@admin_bp.route('/articles/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_article(article_id):
    """Module 12: Edit Healthcare Article"""
    article = Article.query.get_or_404(article_id)
    form = ArticleForm(obj=article)

    if form.validate_on_submit():
        article.title = form.title.data.strip()
        article.category = form.category.data
        article.short_description = form.short_description.data.strip()
        article.content = form.content.data.strip()
        article.author_name = form.author_name.data.strip()
        article.medical_references = form.medical_references.data.strip() if form.medical_references.data else None
        article.reading_time_minutes = form.reading_time_minutes.data
        article.is_published = form.is_published.data

        if form.featured_image.data:
            img = save_uploaded_file(form.featured_image.data, folder_name='articles')
            if img:
                article.featured_image = img

        db.session.commit()
        log_audit(current_user.id, 'ARTICLE_UPDATED', f"Updated article #{article.id}", request.remote_addr)
        flash(f"Article '{article.title}' updated successfully.", "success")
        return redirect(url_for('admin.articles'))

    return render_template('admin/article_form.html', form=form, article=article, is_edit=True)


@admin_bp.route('/articles/<int:article_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_article(article_id):
    """Module 12: Delete Article"""
    article = Article.query.get_or_404(article_id)
    title = article.title
    db.session.delete(article)
    db.session.commit()
    log_audit(current_user.id, 'ARTICLE_DELETED', f"Deleted article {title}", request.remote_addr)
    flash(f"Article '{title}' deleted.", "info")
    return redirect(url_for('admin.articles'))


# =========================================================================
# SYSTEM APPOINTMENTS OVERVIEW & AUDIT LOGS
# =========================================================================

@admin_bp.route('/appointments')
@login_required
@admin_required
def appointments():
    """Module 12: Global Appointments Monitoring"""
    all_appointments = Appointment.query.order_by(Appointment.created_at.desc()).all()
    return render_template('admin/appointments.html', appointments=all_appointments)


@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    """Module 12: System Security and Privacy Audit Trail"""
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    return render_template('admin/audit_logs.html', logs=logs)
