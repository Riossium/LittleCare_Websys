from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, DateField, FloatField, IntegerField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, Length
from datetime import date


class GrowthRecordForm(FlaskForm):
    recorded_date = DateField('Measurement Date', default=date.today, format='%Y-%m-%d', validators=[DataRequired()])
    weight_kg = FloatField('Weight (kg)', validators=[
        DataRequired(),
        NumberRange(min=0.5, max=40.0, message='Please enter a valid weight in kg (e.g., 6.8)')
    ])
    height_cm = FloatField('Length / Height (cm)', validators=[
        DataRequired(),
        NumberRange(min=20.0, max=150.0, message='Please enter a valid height in cm (e.g., 64.5)')
    ])
    head_circumference_cm = FloatField('Head Circumference (cm) - Optional', validators=[
        Optional(),
        NumberRange(min=20.0, max=80.0, message='Please enter a valid head circumference in cm')
    ])
    notes = TextAreaField('Clinical or Observational Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Growth Record')


class VaccinationRecordForm(FlaskForm):
    vaccine_name = SelectField('Vaccine Name', choices=[
        ('BCG', 'BCG (Tuberculosis)'),
        ('Hepatitis B (Birth Dose)', 'Hepatitis B (Birth Dose)'),
        ('Pentavalent (DTP-HepB-Hib) Dose 1', 'Pentavalent (DTP-HepB-Hib) Dose 1'),
        ('Oral Polio Vaccine (OPV) Dose 1', 'Oral Polio Vaccine (OPV) Dose 1'),
        ('Pneumococcal Conjugate Vaccine (PCV) Dose 1', 'Pneumococcal Conjugate Vaccine (PCV) Dose 1'),
        ('Pentavalent (DTP-HepB-Hib) Dose 2', 'Pentavalent (DTP-HepB-Hib) Dose 2'),
        ('Oral Polio Vaccine (OPV) Dose 2', 'Oral Polio Vaccine (OPV) Dose 2'),
        ('Pneumococcal Conjugate Vaccine (PCV) Dose 2', 'Pneumococcal Conjugate Vaccine (PCV) Dose 2'),
        ('Pentavalent (DTP-HepB-Hib) Dose 3', 'Pentavalent (DTP-HepB-Hib) Dose 3'),
        ('Oral Polio Vaccine (OPV) Dose 3', 'Oral Polio Vaccine (OPV) Dose 3'),
        ('Inactivated Polio Vaccine (IPV)', 'Inactivated Polio Vaccine (IPV)'),
        ('Pneumococcal Conjugate Vaccine (PCV) Dose 3', 'Pneumococcal Conjugate Vaccine (PCV) Dose 3'),
        ('Rotavirus Dose 1', 'Rotavirus Dose 1'),
        ('Rotavirus Dose 2', 'Rotavirus Dose 2'),
        ('Influenza (Flu Shot)', 'Influenza (Flu Shot)'),
        ('Measles Vaccine (MCV1)', 'Measles Vaccine (MCV1)'),
        ('Measles, Mumps, Rubella (MMR) Dose 1', 'Measles, Mumps, Rubella (MMR) Dose 1'),
        ('Varicella (Chickenpox) Dose 1', 'Varicella (Chickenpox) Dose 1'),
        ('Hepatitis A Dose 1', 'Hepatitis A Dose 1'),
        ('Other Pediatric Vaccine', 'Other Pediatric Vaccine')
    ], validators=[DataRequired()])
    dose_number = IntegerField('Dose Number', default=1, validators=[DataRequired(), NumberRange(min=1, max=10)])
    date_administered = DateField('Date Administered (if completed)', format='%Y-%m-%d', validators=[Optional()])
    next_scheduled_date = DateField('Next Scheduled Date (if applicable)', format='%Y-%m-%d', validators=[Optional()])
    status = SelectField('Immunization Status', choices=[
        ('completed', 'Completed / Administered'),
        ('scheduled', 'Scheduled / Upcoming'),
        ('pending', 'Pending / Waiting Window'),
        ('missed', 'Missed / Delayed')
    ], default='completed', validators=[DataRequired()])
    administered_by = StringField('Healthcare Provider or Clinic', validators=[Optional(), Length(max=150)])
    batch_number = StringField('Vaccine Lot / Batch No. (Optional)', validators=[Optional(), Length(max=60)])
    notes = TextAreaField('Observations or Side Effects (Optional)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Vaccination Record')


class MedicalCheckupRecordForm(FlaskForm):
    checkup_date = DateField('Visit Date', default=date.today, format='%Y-%m-%d', validators=[DataRequired()])
    visit_type = SelectField('Type of Visit', choices=[
        ('Routine Well-Baby Checkup', 'Routine Well-Baby Checkup'),
        ('Developmental Milestone Evaluation', 'Developmental Milestone Evaluation'),
        ('Sick Child Visit', 'Sick Child Visit'),
        ('Pediatric Specialist Consultation', 'Pediatric Specialist Consultation'),
        ('Post-Hospitalization Follow-up', 'Post-Hospitalization Follow-up')
    ], default='Routine Well-Baby Checkup', validators=[DataRequired()])
    provider_name = StringField('Attending Pediatrician / Clinic', validators=[Optional(), Length(max=150)])
    diagnosis = TextAreaField('Physician Assessment or Clinical Findings', validators=[Optional(), Length(max=800)])
    treatment_summary = TextAreaField('Treatment Plan, Care Instructions, or Regimen', validators=[Optional(), Length(max=800)])
    clinical_notes = TextAreaField('Parent Observations & Dietary/Care Notes', validators=[Optional(), Length(max=1000)])
    document = FileField('Upload Medical Document (Prescription, Lab, Certificate - Optional)', validators=[
        Optional(),
        FileAllowed(['pdf', 'jpg', 'png', 'jpeg'], 'Allowed files: PDF, JPG, PNG')
    ])
    submit = SubmitField('Save Checkup Record')
