from datetime import datetime, date
from app.extensions import db


class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    baby_id = db.Column(db.Integer, db.ForeignKey('baby_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    consultation_type = db.Column(db.String(40), default='In-Clinic')  # 'In-Clinic', 'Teleconsultation'
    reason_for_visit = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default='Pending', index=True)  # 'Pending', 'Confirmed', 'Rejected', 'Cancelled', 'Completed'
    doctor_notes = db.Column(db.Text, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Composite unique index constraint or validation to prevent double booking active slots
    __table_args__ = (
        db.Index('idx_doctor_slot', 'doctor_id', 'appointment_date', 'appointment_time'),
    )

    @property
    def is_upcoming(self):
        if self.appointment_date and self.status in ['Pending', 'Confirmed']:
            return self.appointment_date >= date.today()
        return False

    @property
    def formatted_datetime(self):
        return f"{self.appointment_date.strftime('%b %d, %Y')} at {self.appointment_time.strftime('%I:%M %p')}"

    @property
    def status_badge_class(self):
        badges = {
            'Pending': 'warning',
            'Confirmed': 'success',
            'Completed': 'info',
            'Rejected': 'danger',
            'Cancelled': 'secondary'
        }
        return badges.get(self.status, 'primary')

    def __repr__(self):
        return f"<Appointment #{self.id} Doctor:{self.doctor_id} Baby:{self.baby_id} Status:{self.status}>"
