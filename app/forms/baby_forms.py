from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, DateField, SelectField, FloatField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, Length


class BabyProfileForm(FlaskForm):
    name = StringField('Baby Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[DataRequired()])
    gender = SelectField('Sex', choices=[('male', 'Boy (Male)'), ('female', 'Girl (Female)')], validators=[DataRequired()])
    blood_type = SelectField('Blood Type (Optional)', choices=[
        ('', 'Select Blood Type (Optional)'),
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-')
    ], validators=[Optional()])
    birth_weight = FloatField('Birth Weight (kg)', validators=[
        Optional(),
        NumberRange(min=0.5, max=10.0, message='Please enter a valid weight in kg (e.g. 3.2)')
    ])
    birth_height = FloatField('Birth Length / Height (cm)', validators=[
        Optional(),
        NumberRange(min=20.0, max=80.0, message='Please enter a valid length in cm (e.g. 50.0)')
    ])
    birth_head_circumference = FloatField('Birth Head Circumference (cm)', validators=[
        Optional(),
        NumberRange(min=20.0, max=60.0, message='Please enter a valid head circumference in cm')
    ])
    allergies = TextAreaField('Known Allergies or Sensitivities (Optional)', validators=[Optional(), Length(max=500)])
    pediatrician_notes = TextAreaField('Notes or Special Birth Considerations', validators=[Optional(), Length(max=1000)])
    profile_photo = FileField('Baby Photo', validators=[
        Optional(),
        FileAllowed(['jpg', 'png', 'jpeg', 'webp'], 'Only images are allowed (JPG, PNG, WebP).')
    ])
    submit = SubmitField('Save Baby Profile')
