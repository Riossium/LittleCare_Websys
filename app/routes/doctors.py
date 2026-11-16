from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import date, datetime
from app.extensions import db
from app.models.doctor import DoctorProfile, DoctorAvailability
from app.models.appointment import Appointment
from app.models.health_record import GrowthRecord
from app.forms.appointment_forms import DoctorAvailabilityForm, DoctorAppointmentActionForm
from app.utils import doctor_required, log_audit
from app.services.reminder_service import create_notification

doctors_bp = Blueprint('doctors', __name__, url_prefix='/doctors')


@doctors_bp.route('/')
def directory():
    """Module 8: Doctor Directory & Search"""
    search = request.args.get('search', '').strip()
    specialty = request.args.get('specialty', '').strip()
    consultation_type = request.args.get('type', '').strip()

    query = DoctorProfile.query.filter_by(is_verified=True)

    if search:
        query = query.join(DoctorProfile.user).filter(
            db.or_(
                DoctorProfile.user.has(first_name=search),
                DoctorProfile.clinic_affiliation.ilike(f"%{search}%"),
                DoctorProfile.specialty.ilike(f"%{search}%")
            )
        )

    if specialty:
        query = query.filter_by(specialty=specialty)

    if consultation_type:
        query = query.filter(DoctorProfile.consultation_types.ilike(f"%{consultation_type}%"))

    doctors = query.all()
    specialties = [
        'General Pediatrics',
        'Pediatric Neonatology',
        'Developmental Pediatrics',
        'Pediatric Cardiology',
        'Pediatric Pulmonology',
        'Pediatric Allergy & Immunology'
    ]

    return render_template(
        'doctors/directory.html',
        doctors=doctors,
        search=search,
        selected_specialty=specialty,
        selected_type=consultation_type,
        specialties=specialties
    )


@doctors_bp.route('/<int:doctor_id>')
def detail(doctor_id):
    """Module 8: Doctor Professional Profile Detail"""
    doctor = DoctorProfile.query.filter_by(id=doctor_id, is_verified=True).first_or_404()
    availabilities = doctor.availabilities.filter(
        DoctorAvailability.is_active == True,
        DoctorAvailability.available_date >= date.today()
    ).order_by(DoctorAvailability.available_date.asc()).all()

    return render_template('doctors/detail.html', doctor=doctor, availabilities=availabilities)


# =========================================================================
# MODULE 9: DOCTOR DASHBOARD & CLINICAL MANAGEMENT
# =========================================================================

@doctors_bp.route('/dashboard')
@login_required
@doctor_required
def dashboard():
    """Module 9: Doctor Clinical Dashboard"""
    doctor = current_user.doctor_profile
    if not doctor:
        abort(404)

    today = date.today()

    # Today's appointments
    today_appointments = doctor.appointments.filter(
        Appointment.appointment_date == today
    ).order_by(Appointment.appointment_time.asc()).all()

    # Pending requests
    pending_appointments = doctor.appointments.filter_by(
        status='Pending'
    ).order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).all()

    # Upcoming confirmed appointments
    upcoming_appointments = doctor.appointments.filter(
        Appointment.status == 'Confirmed',
        Appointment.appointment_date > today
    ).order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).limit(5).all()

    # Active schedules count
    active_schedules = doctor.availabilities.filter(
        DoctorAvailability.is_active == True,
        DoctorAvailability.available_date >= today
    ).count()

    return render_template(
        'doctors/dashboard.html',
        doctor=doctor,
        today_appointments=today_appointments,
        pending_appointments=pending_appointments,
        upcoming_appointments=upcoming_appointments,
        active_schedules=active_schedules
    )


@doctors_bp.route('/availability', methods=['GET', 'POST'])
@login_required
@doctor_required
def availability():
    """Module 9: Manage Doctor Availability Schedules"""
    doctor = current_user.doctor_profile
    form = DoctorAvailabilityForm()

    if form.validate_on_submit():
        avail = DoctorAvailability(
            doctor_profile_id=doctor.id,
            available_date=form.available_date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            slot_duration_minutes=form.slot_duration_minutes.data,
            max_patients=form.max_patients.data,
            is_active=True
        )
        db.session.add(avail)
        db.session.commit()

        flash(f"Availability schedule for {avail.date_formatted} published successfully!", "success")
        return redirect(url_for('doctors.availability'))

    today = date.today()
    schedules = doctor.availabilities.filter(
        DoctorAvailability.available_date >= today
    ).order_by(DoctorAvailability.available_date.asc()).all()

    return render_template('doctors/availability.html', doctor=doctor, form=form, schedules=schedules)


@doctors_bp.route('/availability/<int:avail_id>/delete', methods=['POST'])
@login_required
@doctor_required
def delete_availability(avail_id):
    """Module 9: Delete an Availability Slot"""
    doctor = current_user.doctor_profile
    avail = DoctorAvailability.query.filter_by(id=avail_id, doctor_profile_id=doctor.id).first_or_404()
    db.session.delete(avail)
    db.session.commit()
    flash("Schedule slot removed.", "info")
    return redirect(url_for('doctors.availability'))


@doctors_bp.route('/appointment/<int:appointment_id>/review', methods=['GET', 'POST'])
@login_required
@doctor_required
def review_appointment(appointment_id):
    """Module 9: View Authorized Patient Info and Add Consultation Notes"""
    doctor = current_user.doctor_profile
    apt = Appointment.query.filter_by(id=appointment_id, doctor_id=doctor.id).first_or_404()

    form = DoctorAppointmentActionForm(obj=apt)
    if form.validate_on_submit():
        prev_status = apt.status
        apt.status = form.status.data
        if form.doctor_notes.data:
            apt.doctor_notes = form.doctor_notes.data.strip()
        if form.rejection_reason.data:
            apt.rejection_reason = form.rejection_reason.data.strip()

        db.session.commit()

        # Send notification to parent
        notif_msg = f"{doctor.doctor_name} has updated your appointment for {apt.baby.name} on {apt.formatted_datetime} to '{apt.status}'."
        create_notification(
            user_id=apt.parent_id,
            title=f"Appointment {apt.status}",
            message=notif_msg,
            notif_type='appointment',
            link=f'/appointments/{apt.id}'
        )

        log_audit(current_user.id, 'DOCTOR_APPOINTMENT_ACTION', f"Doctor updated appointment #{apt.id} from {prev_status} to {apt.status}", request.remote_addr)
        flash(f"Appointment status updated to '{apt.status}'.", "success")
        return redirect(url_for('doctors.dashboard'))

    # Retrieve authorized baby records for consultation review
    baby = apt.baby
    growth_history = baby.growth_records.order_by(db.desc('recorded_date')).limit(5).all()
    vaccines = baby.vaccination_records.order_by(db.desc('date_administered')).limit(6).all()

    # Log audit for medical record access
    log_audit(current_user.id, 'DOCTOR_ACCESSED_BABY_RECORD', f"Doctor {doctor.doctor_name} viewed clinical summary for baby {baby.name} (Apt #{apt.id})", request.remote_addr)

    return render_template(
        'doctors/consultation_notes.html',
        appointment=apt,
        baby=baby,
        growth_history=growth_history,
        vaccines=vaccines,
        form=form
    )
