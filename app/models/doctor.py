from datetime import datetime, date
from app.extensions import db


class DoctorProfile(db.Model):
    __tablename__ = 'doctor_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    specialty = db.Column(db.String(120), nullable=False, default='General Pediatrics')
    license_number = db.Column(db.String(80), nullable=False)  # PRC Medical License
    ptr_number = db.Column(db.String(80), nullable=True)
    clinic_affiliation = db.Column(db.String(200), nullable=False)
    clinic_address = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    experience_years = db.Column(db.Integer, default=5)
    consultation_fee = db.Column(db.Float, default=500.0)  # Advisory only, no e-commerce checkout
    consultation_types = db.Column(db.String(120), default='In-Clinic, Teleconsultation')
    is_verified = db.Column(db.Boolean, default=False)
    verification_date = db.Column(db.DateTime, nullable=True)
    verification_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    availabilities = db.relationship('DoctorAvailability', backref='doctor', lazy='dynamic', cascade='all, delete-orphan')
    appointments = db.relationship('Appointment', backref='doctor', foreign_keys='Appointment.doctor_id', lazy='dynamic')

    @property
    def doctor_name(self):
        return f"Dr. {self.user.first_name} {self.user.last_name}"

    @property
    def full_title(self):
        return f"Dr. {self.user.first_name} {self.user.last_name}, MD"

    def __repr__(self):
        return f"<DoctorProfile {self.doctor_name} ({self.specialty}) Verified:{self.is_verified}>"


class DoctorAvailability(db.Model):
    __tablename__ = 'doctor_availabilities'

    id = db.Column(db.Integer, primary_key=True)
    doctor_profile_id = db.Column(db.Integer, db.ForeignKey('doctor_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    available_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    slot_duration_minutes = db.Column(db.Integer, default=30)
    max_patients = db.Column(db.Integer, default=8)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def date_formatted(self):
        return self.available_date.strftime('%B %d, %Y (%A)')

    @property
    def time_formatted(self):
        return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"

    def __repr__(self):
        return f"<DoctorAvailability Doc:{self.doctor_profile_id} {self.available_date} {self.time_formatted}>"
