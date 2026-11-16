from app.forms.auth_forms import (
    LoginForm, ParentRegistrationForm, DoctorRegistrationForm,
    ForgotPasswordForm, ResetPasswordForm, ProfileUpdateForm
)
from app.forms.baby_forms import BabyProfileForm
from app.forms.health_forms import GrowthRecordForm, VaccinationRecordForm, MedicalCheckupRecordForm
from app.forms.appointment_forms import AppointmentBookingForm, DoctorAvailabilityForm, DoctorAppointmentActionForm
from app.forms.article_forms import ArticleForm

__all__ = [
    'LoginForm',
    'ParentRegistrationForm',
    'DoctorRegistrationForm',
    'ForgotPasswordForm',
    'ResetPasswordForm',
    'ProfileUpdateForm',
    'BabyProfileForm',
    'GrowthRecordForm',
    'VaccinationRecordForm',
    'MedicalCheckupRecordForm',
    'AppointmentBookingForm',
    'DoctorAvailabilityForm',
    'DoctorAppointmentActionForm',
    'ArticleForm'
]
