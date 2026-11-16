from datetime import date, datetime, timedelta
from app.extensions import db
from app.models.notification import Notification
from app.models.permission_audit import AuditLog
from app.models.appointment import Appointment
from app.models.health_record import VaccinationRecord


def create_notification(user_id, title, message, notif_type='system', link=None):
    """Creates an in-app notification for a specific user."""
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notif_type,
        link=link
    )
    db.session.add(notif)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    return notif


def log_audit(user_id, action, details=None, ip_address=None):
    """Logs system security and privacy actions for compliance with data privacy regulations."""
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


def check_and_generate_due_reminders(user):
    """
    Checks upcoming appointments and vaccination schedules for the user's active baby profiles
    and automatically pushes reminders if not yet generated today.
    """
    if not user or not user.is_parent:
        return

    today = date.today()

    # Check upcoming appointments within the next 48 hours
    upcoming_appointments = Appointment.query.filter(
        Appointment.parent_id == user.id,
        Appointment.status == 'Confirmed',
        Appointment.appointment_date >= today,
        Appointment.appointment_date <= today + timedelta(days=2)
    ).all()

    for apt in upcoming_appointments:
        title = f"Upcoming Consultation Reminder"
        msg = f"Reminder: {apt.baby.name} has a scheduled consultation with {apt.doctor.doctor_name} on {apt.formatted_datetime}."
        # Avoid duplicate reminder today
        existing = Notification.query.filter(
            Notification.user_id == user.id,
            Notification.type == 'appointment',
            Notification.title == title,
            Notification.created_at >= datetime.combine(today, datetime.min.time())
        ).first()

        if not existing:
            create_notification(
                user_id=user.id,
                title=title,
                message=msg,
                notif_type='appointment',
                link=f'/appointments/{apt.id}'
            )

    # Check due vaccinations across all parent's babies
    for baby in user.baby_profiles:
        due_vaccines = baby.vaccination_records.filter(
            VaccinationRecord.status.in_(['scheduled', 'pending']),
            VaccinationRecord.next_scheduled_date <= today + timedelta(days=7),
            VaccinationRecord.next_scheduled_date >= today - timedelta(days=3)
        ).all()

        for v in due_vaccines:
            title = f"Vaccination Due: {v.vaccine_name}"
            msg = f"{baby.name} has a scheduled dose of {v.vaccine_name} due around {v.next_scheduled_date.strftime('%b %d, %Y')}."
            existing = Notification.query.filter(
                Notification.user_id == user.id,
                Notification.type == 'vaccination',
                Notification.title == title,
                Notification.created_at >= datetime.combine(today - timedelta(days=3), datetime.min.time())
            ).first()

            if not existing:
                create_notification(
                    user_id=user.id,
                    title=title,
                    message=msg,
                    notif_type='vaccination',
                    link='/health/vaccinations'
                )
