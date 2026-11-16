from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from datetime import datetime, date, time, timedelta
from app.extensions import db
from app.models.doctor import DoctorProfile, DoctorAvailability
from app.models.baby import BabyProfile
from app.models.appointment import Appointment
from app.forms.appointment_forms import AppointmentBookingForm
from app.utils import parent_required, log_audit
from app.services.reminder_service import create_notification

appointments_bp = Blueprint('appointments', __name__, url_prefix='/appointments')


@appointments_bp.route('/book/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
@parent_required
def book(doctor_id):
    """Module 8: Doctor Consultation Booking Workflow"""
    doctor = DoctorProfile.query.filter_by(id=doctor_id, is_verified=True).first_or_404()
    babies = current_user.baby_profiles.filter_by(is_active=True).all()

    if not babies:
        flash("Please create a baby profile before booking a doctor consultation.", "warning")
        return redirect(url_for('baby.create'))

    form = AppointmentBookingForm()
    form.baby_id.choices = [(b.id, f"{b.name} ({b.age_display})") for b in babies]

    # Dynamically generate time slot choices
    # Default slots if not yet loaded via date selection
    default_slots = [
        ('09:00', '09:00 AM'), ('09:30', '09:30 AM'),
        ('10:00', '10:00 AM'), ('10:30', '10:30 AM'),
        ('11:00', '11:00 AM'), ('11:30', '11:30 AM'),
        ('14:00', '02:00 PM'), ('14:30', '02:30 PM'),
        ('15:00', '03:00 PM'), ('15:30', '03:30 PM'),
        ('16:00', '04:00 PM'), ('16:30', '04:30 PM')
    ]
    form.appointment_time.choices = default_slots

    if form.validate_on_submit():
        apt_date = form.appointment_date.data
        time_str = form.appointment_time.data
        apt_time = datetime.strptime(time_str, '%H:%M').time()

        # Check date not in the past
        if apt_date < date.today():
            flash("You cannot book an appointment for a past date.", "danger")
            return render_template('appointments/book.html', doctor=doctor, form=form)

        # PREVENT DOUBLE-BOOKING: Check if doctor already has an active appointment in this slot
        existing = Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.appointment_date == apt_date,
            Appointment.appointment_time == apt_time,
            Appointment.status.in_(['Pending', 'Confirmed'])
        ).first()

        if existing:
            flash(f"Dr. {doctor.doctor_name} is already booked at {apt_time.strftime('%I:%M %p')} on {apt_date.strftime('%b %d, %Y')}. Please choose another time slot.", "danger")
            return render_template('appointments/book.html', doctor=doctor, form=form)

        # Create appointment
        baby = BabyProfile.query.filter_by(id=form.baby_id.data, parent_id=current_user.id).first_or_404()
        appointment = Appointment(
            parent_id=current_user.id,
            doctor_id=doctor.id,
            baby_id=baby.id,
            appointment_date=apt_date,
            appointment_time=apt_time,
            consultation_type=form.consultation_type.data,
            reason_for_visit=form.reason_for_visit.data.strip(),
            status='Pending'
        )
        db.session.add(appointment)
        db.session.commit()

        # Send in-app notification to Doctor
        create_notification(
            user_id=doctor.user_id,
            title="New Consultation Request",
            message=f"{current_user.full_name} requested a consultation for {baby.name} on {appointment.formatted_datetime}.",
            notif_type='appointment',
            link=f'/doctors/appointment/{appointment.id}/review'
        )

        log_audit(current_user.id, 'APPOINTMENT_REQUESTED', f"Booked consultation with {doctor.doctor_name} for {baby.name}", request.remote_addr)
        flash(f"Your consultation request for {baby.name} with {doctor.doctor_name} has been submitted! You will receive a notification once confirmed.", "success")
        return redirect(url_for('appointments.my_appointments'))

    # Load doctor's published availability dates for the parent's reference
    available_schedules = doctor.availabilities.filter(
        DoctorAvailability.is_active == True,
        DoctorAvailability.available_date >= date.today()
    ).order_by(DoctorAvailability.available_date.asc()).all()

    return render_template('appointments/book.html', doctor=doctor, form=form, available_schedules=available_schedules)


@appointments_bp.route('/my-appointments')
@login_required
@parent_required
def my_appointments():
    """Module 8: Parent's Consultation List & Status Tracker"""
    status_filter = request.args.get('status', 'all')
    query = Appointment.query.filter_by(parent_id=current_user.id)

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    appointments = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
    return render_template('appointments/my_appointments.html', appointments=appointments, current_status=status_filter)


@appointments_bp.route('/<int:appointment_id>')
@login_required
def detail(appointment_id):
    """Module 8: Appointment Detail View"""
    apt = Appointment.query.get_or_404(appointment_id)

    # Permission check: Parent or Doctor or Admin
    if apt.parent_id != current_user.id and (not current_user.is_doctor or current_user.doctor_profile.id != apt.doctor_id) and not current_user.is_admin:
        abort(403)

    return render_template('appointments/detail.html', appointment=apt)


@appointments_bp.route('/<int:appointment_id>/cancel', methods=['POST'])
@login_required
@parent_required
def cancel(appointment_id):
    """Module 8: Parent Cancels Appointment"""
    apt = Appointment.query.filter_by(id=appointment_id, parent_id=current_user.id).first_or_404()
    if apt.status in ['Completed', 'Rejected']:
        flash(f"Cannot cancel an appointment that is already {apt.status.lower()}.", "warning")
        return redirect(url_for('appointments.my_appointments'))

    apt.status = 'Cancelled'
    db.session.commit()

    # Notify doctor
    create_notification(
        user_id=apt.doctor.user_id,
        title="Consultation Cancelled",
        message=f"{current_user.full_name} has cancelled the appointment for {apt.baby.name} on {apt.formatted_datetime}.",
        notif_type='appointment',
        link=f'/doctors/dashboard'
    )

    log_audit(current_user.id, 'APPOINTMENT_CANCELLED', f"Cancelled appointment #{apt.id}", request.remote_addr)
    flash("Your appointment has been cancelled.", "info")
    return redirect(url_for('appointments.my_appointments'))


@appointments_bp.route('/api/available-slots/<int:doctor_id>/<string:selected_date>')
@login_required
def get_slots(doctor_id, selected_date):
    """API: Returns free time slots for a given doctor on a date, filtering out already booked ones."""
    doctor = DoctorProfile.query.get_or_404(doctor_id)
    try:
        dt = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # Get booked slots for this doctor on that date
    booked = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date == dt,
        Appointment.status.in_(['Pending', 'Confirmed'])
    ).all()
    booked_times = [b.appointment_time.strftime('%H:%M') for b in booked]

    # Standard clinic slots
    standard_slots = [
        {'time': '09:00', 'label': '09:00 AM'},
        {'time': '09:30', 'label': '09:30 AM'},
        {'time': '10:00', 'label': '10:00 AM'},
        {'time': '10:30', 'label': '10:30 AM'},
        {'time': '11:00', 'label': '11:00 AM'},
        {'time': '11:30', 'label': '11:30 AM'},
        {'time': '14:00', 'label': '02:00 PM'},
        {'time': '14:30', 'label': '02:30 PM'},
        {'time': '15:00', 'label': '03:00 PM'},
        {'time': '15:30', 'label': '03:30 PM'},
        {'time': '16:00', 'label': '04:00 PM'},
        {'time': '16:30', 'label': '04:30 PM'}
    ]

    available = [s for s in standard_slots if s['time'] not in booked_times]
    return jsonify({'slots': available})
