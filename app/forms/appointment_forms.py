from flask_wtf import FlaskForm
from wtforms import DateField, TimeField, SelectField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from datetime import date


class AppointmentBookingForm(FlaskForm):
    baby_id = SelectField('Select Baby Profile', coerce=int, validators=[DataRequired(message='Please choose which baby the consultation is for')])
    appointment_date = DateField('Preferred Date', format='%Y-%m-%d', validators=[DataRequired(message='Please select a consultation date')])
    appointment_time = SelectField('Preferred Time Slot', choices=[], validators=[DataRequired(message='Please choose an available time slot')])
    consultation_type = SelectField('Consultation Format', choices=[
        ('In-Clinic', 'In-Clinic Physical Visit'),
        ('Teleconsultation', 'Teleconsultation / Online Advice')
    ], default='In-Clinic', validators=[DataRequired()])
    reason_for_visit = TextAreaField('Reason for Consultation & Symptoms', validators=[
        DataRequired(message='Please describe your baby’s symptoms or the reason for this visit'),
        Length(min=10, max=1000, message='Please provide at least 10 characters detailing the reason')
    ])
    submit = SubmitField('Confirm & Request Appointment')


class DoctorAvailabilityForm(FlaskForm):
    available_date = DateField('Available Date', default=date.today, format='%Y-%m-%d', validators=[DataRequired()])
    start_time = TimeField('Start Time (e.g. 09:00)', format='%H:%M', validators=[DataRequired()])
    end_time = TimeField('End Time (e.g. 12:00)', format='%H:%M', validators=[DataRequired()])
    slot_duration_minutes = SelectField('Slot Duration', choices=[
        (15, '15 Minutes'),
        (20, '20 Minutes'),
        (30, '30 Minutes'),
        (45, '45 Minutes'),
        (60, '60 Minutes')
    ], coerce=int, default=30, validators=[DataRequired()])
    max_patients = IntegerField('Maximum Patients', default=8, validators=[DataRequired(), NumberRange(min=1, max=30)])
    submit = SubmitField('Publish Availability Schedule')


class DoctorAppointmentActionForm(FlaskForm):
    status = SelectField('Update Status', choices=[
        ('Confirmed', 'Accept & Confirm Appointment'),
        ('Rejected', 'Decline Request'),
        ('Completed', 'Mark as Completed'),
        ('Cancelled', 'Cancel Appointment')
    ], validators=[DataRequired()])
    doctor_notes = TextAreaField('Consultation Notes / Medical Advice / Instructions for Parent', validators=[Optional(), Length(max=1500)])
    rejection_reason = TextAreaField('Reason for Rejection / Rescheduling Note', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Update Appointment')
