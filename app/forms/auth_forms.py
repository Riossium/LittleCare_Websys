from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError
from app.models.user import User


class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me signed in')
    submit = SubmitField('Sign In')


class ParentRegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=60)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=60)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Mobile Number', validators=[Optional(), Length(max=30)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    agree_terms = BooleanField('I agree to the LittleCare Privacy Policy & Healthcare Terms', validators=[DataRequired()])
    submit = SubmitField('Create Parent Account')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError('An account with this email address is already registered.')


class DoctorRegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=60)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=60)])
    email = StringField('Professional Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Clinic / Contact Number', validators=[DataRequired(), Length(max=30)])
    specialty = SelectField('Specialty', choices=[
        ('General Pediatrics', 'General Pediatrics'),
        ('Pediatric Neonatology', 'Pediatric Neonatology'),
        ('Developmental Pediatrics', 'Developmental Pediatrics'),
        ('Pediatric Cardiology', 'Pediatric Cardiology'),
        ('Pediatric Pulmonology', 'Pediatric Pulmonology'),
        ('Pediatric Allergy & Immunology', 'Pediatric Allergy & Immunology'),
        ('Pediatric Gastroenterology', 'Pediatric Gastroenterology')
    ], validators=[DataRequired()])
    license_number = StringField('PRC Medical License Number', validators=[DataRequired(), Length(min=4, max=60)])
    ptr_number = StringField('PTR Number (Optional)', validators=[Optional(), Length(max=60)])
    clinic_affiliation = StringField('Primary Hospital or Clinic Affiliation', validators=[DataRequired(), Length(max=200)])
    clinic_address = StringField('Clinic Physical Address', validators=[Optional(), Length(max=255)])
    experience_years = IntegerField('Years in Pediatric Practice', default=5, validators=[Optional()])
    consultation_types = SelectField('Consultation Availability', choices=[
        ('In-Clinic & Teleconsultation', 'In-Clinic & Teleconsultation'),
        ('In-Clinic Only', 'In-Clinic Only'),
        ('Teleconsultation Only', 'Teleconsultation Only')
    ], validators=[DataRequired()])
    bio = TextAreaField('Professional Biography & Clinical Experience', validators=[Optional(), Length(max=1000)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    agree_terms = BooleanField('I certify that I am a licensed physician in good standing', validators=[DataRequired()])
    submit = SubmitField('Register as Doctor for Verification')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError('An account with this email address is already registered.')


class ForgotPasswordForm(FlaskForm):
    email = StringField('Registered Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Password Reset Instructions')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Reset Password')


class ProfileUpdateForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=60)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=60)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=30)])
    profile_image = FileField('Profile Photo', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'webp'], 'Images only (jpg, png, webp)')
    ])
    submit = SubmitField('Update Profile')
