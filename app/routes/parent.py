from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from datetime import date
from app.extensions import db
from app.models.baby import BabyProfile
from app.models.appointment import Appointment
from app.models.article import Article
from app.models.health_record import GrowthRecord, VaccinationRecord, MedicalCheckupRecord
from app.forms.auth_forms import ProfileUpdateForm
from app.utils import parent_required, get_active_baby, save_uploaded_file, log_audit
from app.services.recommendation_service import generate_baby_recommendations
from app.services.reminder_service import check_and_generate_due_reminders

parent_bp = Blueprint('parent', __name__, url_prefix='/parent')


@parent_bp.route('/dashboard')
@login_required
@parent_required
def dashboard():
    """Module 3: Comprehensive Parent Healthcare Dashboard"""
    # Trigger automated reminder checks
    check_and_generate_due_reminders(current_user)

    active_baby = get_active_baby()
    all_babies = current_user.baby_profiles.filter_by(is_active=True).all()

    # If baby exists, refresh recommendations
    recommendations = []
    latest_growth = None
    recent_checkups = []
    vaccine_summary = {'completed': 0, 'pending': 0, 'due_soon': []}

    if active_baby:
        recommendations = generate_baby_recommendations(active_baby)
        latest_growth = active_baby.latest_growth
        recent_checkups = active_baby.checkup_records.limit(3).all()

        vaccines = active_baby.vaccination_records.all()
        vaccine_summary['completed'] = sum(1 for v in vaccines if v.status == 'completed')
        vaccine_summary['pending'] = sum(1 for v in vaccines if v.status in ['scheduled', 'pending'])
        vaccine_summary['due_soon'] = [v for v in vaccines if v.is_due_soon or v.is_overdue]

    # Appointments
    today = date.today()
    upcoming_appointments = Appointment.query.filter(
        Appointment.parent_id == current_user.id,
        Appointment.status.in_(['Pending', 'Confirmed']),
        Appointment.appointment_date >= today
    ).order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).limit(3).all()

    pending_requests = Appointment.query.filter_by(
        parent_id=current_user.id,
        status='Pending'
    ).count()

    # Recommended articles based on baby's age stage or general baby care
    if active_baby and active_baby.age_in_months < 6:
        articles = Article.query.filter(
            Article.is_published == True,
            Article.category.in_(['Baby Nutrition', 'Vaccination Guide', 'Parenting Tips'])
        ).limit(3).all()
    else:
        articles = Article.query.filter_by(is_published=True).order_by(Article.published_at.desc()).limit(3).all()

    return render_template(
        'parent/dashboard.html',
        active_baby=active_baby,
        all_babies=all_babies,
        latest_growth=latest_growth,
        recent_checkups=recent_checkups,
        vaccine_summary=vaccine_summary,
        upcoming_appointments=upcoming_appointments,
        pending_requests=pending_requests,
        recommendations=recommendations,
        articles=articles
    )


@parent_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@parent_required
def profile():
    """Parent Account & Profile Settings"""
    form = ProfileUpdateForm(obj=current_user)
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data.strip()
        current_user.last_name = form.last_name.data.strip()
        current_user.phone = form.phone.data.strip() if form.phone.data else None

        if form.profile_image.data:
            img_filename = save_uploaded_file(form.profile_image.data, folder_name='babies')
            if img_filename:
                current_user.profile_image = img_filename

        db.session.commit()
        log_audit(current_user.id, 'PROFILE_UPDATE', "Parent updated profile info", request.remote_addr)
        flash("Your profile information has been updated successfully.", "success")
        return redirect(url_for('parent.profile'))

    return render_template('parent/profile.html', form=form)
