from datetime import datetime, date
from app.extensions import db


class BabyProfile(db.Model):
    __tablename__ = 'baby_profiles'

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # 'male' or 'female'
    blood_type = db.Column(db.String(10), nullable=True)
    birth_weight = db.Column(db.Float, nullable=True)  # in kg
    birth_height = db.Column(db.Float, nullable=True)  # in cm
    birth_head_circumference = db.Column(db.Float, nullable=True)  # in cm
    allergies = db.Column(db.Text, nullable=True)
    pediatrician_notes = db.Column(db.Text, nullable=True)
    profile_photo = db.Column(db.String(255), default='default-baby.png')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    growth_records = db.relationship('GrowthRecord', backref='baby', lazy='dynamic', cascade='all, delete-orphan', order_by='GrowthRecord.recorded_date.asc()')
    vaccination_records = db.relationship('VaccinationRecord', backref='baby', lazy='dynamic', cascade='all, delete-orphan', order_by='VaccinationRecord.date_administered.asc()')
    checkup_records = db.relationship('MedicalCheckupRecord', backref='baby', lazy='dynamic', cascade='all, delete-orphan', order_by='MedicalCheckupRecord.checkup_date.desc()')
    appointments = db.relationship('Appointment', backref='baby', lazy='dynamic', cascade='all, delete-orphan')
    recommendations = db.relationship('Recommendation', backref='baby', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def age_in_days(self):
        if not self.date_of_birth:
            return 0
        today = date.today()
        return (today - self.date_of_birth).days

    @property
    def age_in_months(self):
        if not self.date_of_birth:
            return 0
        today = date.today()
        months = (today.year - self.date_of_birth.year) * 12 + (today.month - self.date_of_birth.month)
        if today.day < self.date_of_birth.day:
            months -= 1
        return max(0, months)

    @property
    def age_display(self):
        if not self.date_of_birth:
            return "Unknown age"
        today = date.today()
        years = today.year - self.date_of_birth.year
        months = today.month - self.date_of_birth.month
        days = today.day - self.date_of_birth.day

        if days < 0:
            months -= 1
            # approximate days in previous month
            days += 30
        if months < 0:
            years -= 1
            months += 12

        parts = []
        if years > 0:
            parts.append(f"{years} {'yr' if years == 1 else 'yrs'}")
        if months > 0:
            parts.append(f"{months} {'mo' if months == 1 else 'mos'}")
        if days > 0 or not parts:
            parts.append(f"{days} {'day' if days == 1 else 'days'}")

        return " ".join(parts)

    @property
    def latest_growth(self):
        return self.growth_records.order_by(db.desc('recorded_date')).first()

    @property
    def latest_checkup(self):
        return self.checkup_records.order_by(db.desc('checkup_date')).first()

    @property
    def completed_vaccines_count(self):
        return self.vaccination_records.filter_by(status='completed').count()

    @property
    def pending_vaccines_count(self):
        return self.vaccination_records.filter(db.or_(db.text("status = 'scheduled'"), db.text("status = 'pending'"))).count()

    def __repr__(self):
        return f"<BabyProfile {self.name} (DOB: {self.date_of_birth})>"
