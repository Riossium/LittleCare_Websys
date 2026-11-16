from datetime import datetime, date
from app.extensions import db


class GrowthRecord(db.Model):
    __tablename__ = 'growth_records'

    id = db.Column(db.Integer, primary_key=True)
    baby_id = db.Column(db.Integer, db.ForeignKey('baby_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    recorded_date = db.Column(db.Date, nullable=False, default=date.today)
    weight_kg = db.Column(db.Float, nullable=False)
    height_cm = db.Column(db.Float, nullable=False)
    head_circumference_cm = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    recorded_by = db.Column(db.String(80), default='Parent')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def bmi(self):
        """Calculates BMI (kg / m^2)"""
        if self.height_cm and self.height_cm > 0:
            height_m = self.height_cm / 100.0
            return round(self.weight_kg / (height_m * height_m), 1)
        return None

    def __repr__(self):
        return f"<GrowthRecord Baby:{self.baby_id} Date:{self.recorded_date} W:{self.weight_kg}kg H:{self.height_cm}cm>"


class VaccinationRecord(db.Model):
    __tablename__ = 'vaccination_records'

    id = db.Column(db.Integer, primary_key=True)
    baby_id = db.Column(db.Integer, db.ForeignKey('baby_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    vaccine_name = db.Column(db.String(120), nullable=False)
    dose_number = db.Column(db.Integer, default=1)
    date_administered = db.Column(db.Date, nullable=True)
    next_scheduled_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(30), default='completed')  # 'completed', 'scheduled', 'missed', 'pending'
    administered_by = db.Column(db.String(150), nullable=True)
    batch_number = db.Column(db.String(60), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_due_soon(self):
        if self.next_scheduled_date and self.status in ['scheduled', 'pending']:
            diff = (self.next_scheduled_date - date.today()).days
            return 0 <= diff <= 14
        return False

    @property
    def is_overdue(self):
        if self.next_scheduled_date and self.status in ['scheduled', 'pending']:
            return (date.today() - self.next_scheduled_date).days > 0
        return False

    def __repr__(self):
        return f"<VaccinationRecord Baby:{self.baby_id} {self.vaccine_name} ({self.status})>"


class MedicalCheckupRecord(db.Model):
    __tablename__ = 'medical_checkup_records'

    id = db.Column(db.Integer, primary_key=True)
    baby_id = db.Column(db.Integer, db.ForeignKey('baby_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    checkup_date = db.Column(db.Date, nullable=False, default=date.today)
    visit_type = db.Column(db.String(80), nullable=False, default='Routine Checkup')
    provider_name = db.Column(db.String(150), nullable=True)
    diagnosis = db.Column(db.Text, nullable=True)
    treatment_summary = db.Column(db.Text, nullable=True)
    clinical_notes = db.Column(db.Text, nullable=True)
    document_filename = db.Column(db.String(255), nullable=True)
    document_original_name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<MedicalCheckupRecord Baby:{self.baby_id} {self.visit_type} on {self.checkup_date}>"
