"""
Comprehensive Automated Test Suite for LittleCare
Verifies Authentication, Baby CRUD, Health Records, Growth Charts,
AI Healthcare Assistant, Recommendations, Doctor Bookings, and Security.
"""

import unittest
from datetime import date, time, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.baby import BabyProfile
from app.models.doctor import DoctorProfile
from app.models.health_record import GrowthRecord, VaccinationRecord, MedicalCheckupRecord
from app.models.appointment import Appointment
from app.models.article import Article
from app.models.notification import Notification
from app.services.ai_service import ask_ai_assistant, build_baby_context
from app.services.recommendation_service import generate_baby_recommendations


class LittleCareSystemTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('development')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for unit testing
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def login(self, email, password):
        return self.client.post('/auth/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)

    def logout(self):
        return self.client.get('/auth/logout', follow_redirects=True)

    # 1. TEST PUBLIC PAGES
    def test_public_pages(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Caring for Your Little One", res.data)

        res = self.client.get('/about')
        self.assertEqual(res.status_code, 200)

        res = self.client.get('/services')
        self.assertEqual(res.status_code, 200)

        res = self.client.get('/articles/')
        self.assertEqual(res.status_code, 200)

        res = self.client.get('/doctors/')
        self.assertEqual(res.status_code, 200)

    # 2. TEST AUTHENTICATION & ROLE-BASED ACCESS
    def test_authentication(self):
        # Admin login
        res = self.login('admin@littlecare.health', 'Admin123!')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Administrative Control Center", res.data)
        self.logout()

        # Doctor login
        res = self.login('doctor.santos@littlecare.health', 'Doctor123!')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Clinic Portal", res.data)
        self.logout()

        # Parent login
        res = self.login('parent@littlecare.health', 'Parent123!')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Sophia Rivera", res.data)
        self.logout()

    def test_unauthorized_access_prevention(self):
        # Unauthenticated access to admin dashboard should redirect to login
        res = self.client.get('/admin/dashboard', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/auth/login', res.headers['Location'])

        # Parent attempting to access admin route
        self.login('parent@littlecare.health', 'Parent123!')
        res = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b"Access denied", res.data)
        self.logout()

    # 3. TEST BABY PROFILE CRUD
    def test_baby_profile_crud(self):
        self.login('parent@littlecare.health', 'Parent123!')
        
        # Create new baby
        res = self.client.post('/baby/create', data={
            'name': 'Baby Noah',
            'date_of_birth': date.today().strftime('%Y-%m-%d'),
            'gender': 'male',
            'blood_type': 'O+',
            'birth_weight': 3.4,
            'birth_height': 50.5,
            'allergies': 'None'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Baby Noah", res.data)

        # Query baby
        noah = BabyProfile.query.filter_by(name='Baby Noah').first()
        self.assertIsNotNone(noah)
        self.assertEqual(noah.gender, 'male')

        # Edit baby
        res = self.client.post(f'/baby/{noah.id}/edit', data={
            'name': 'Noah Gabriel Rivera',
            'date_of_birth': date.today().strftime('%Y-%m-%d'),
            'gender': 'male',
            'blood_type': 'O+',
            'birth_weight': 3.6,
            'birth_height': 51.0,
            'allergies': 'None'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        
        updated_noah = BabyProfile.query.get(noah.id)
        self.assertEqual(updated_noah.name, 'Noah Gabriel Rivera')

        self.logout()

    # 4. TEST HEALTH RECORDS CRUD & GROWTH API
    def test_health_records(self):
        self.login('parent@littlecare.health', 'Parent123!')
        sophia = BabyProfile.query.filter_by(name='Sophia Rivera').first()
        self.assertIsNotNone(sophia)

        # Add growth record
        res = self.client.post('/health/growth/add', data={
            'recorded_date': date.today().strftime('%Y-%m-%d'),
            'weight_kg': 8.1,
            'height_cm': 68.5,
            'head_circumference_cm': 43.5,
            'notes': 'Unit test growth entry'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Test Growth Chart Data API
        res = self.client.get(f'/health/api/growth-data/{sophia.id}')
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertIn('records', json_data)
        self.assertIn('who_reference', json_data)
        self.assertGreaterEqual(len(json_data['records']['weights']), 1)

        # Add vaccination record
        res = self.client.post('/health/vaccinations/add', data={
            'vaccine_name': 'Influenza (Flu Shot)',
            'dose_number': 1,
            'date_administered': date.today().strftime('%Y-%m-%d'),
            'status': 'completed',
            'administered_by': 'Test Clinic'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        self.logout()

    # 5. TEST AI HEALTHCARE ASSISTANT & SAFETY GUARDRAILS
    def test_ai_healthcare_assistant(self):
        sophia = BabyProfile.query.filter_by(name='Sophia Rivera').first()
        
        # Test context builder
        context = build_baby_context(sophia, include_records=True)
        self.assertIn("Sophia Rivera", context)
        self.assertIn("AUTHORIZED BABY RECORD SUMMARY", context)

        # Test emergency response trigger
        emergency_result = ask_ai_assistant("My baby has blue lips and cannot breathe", baby=sophia, authorize_records=True)
        self.assertIn("EMERGENCY", emergency_result['answer'])

        # Test standard advice with fallback engine
        advice_result = ask_ai_assistant("What should I prepare for baby vaccination?", baby=sophia, authorize_records=True)
        self.assertIsNotNone(advice_result['answer'])
        self.assertIn('suggested_actions', advice_result)
        self.assertGreater(len(advice_result['suggested_actions']), 0)

    # 6. TEST SMART RECOMMENDATIONS GENERATION
    def test_smart_recommendations(self):
        sophia = BabyProfile.query.filter_by(name='Sophia Rivera').first()
        recommendations = generate_baby_recommendations(sophia)
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

    # 7. TEST DOCTOR BOOKING & DOUBLE-BOOKING PREVENTION
    def test_doctor_booking_and_double_booking_prevention(self):
        self.login('parent@littlecare.health', 'Parent123!')
        sophia = BabyProfile.query.filter_by(name='Sophia Rivera').first()
        doctor = DoctorProfile.query.first()
        test_date = (date.today() + timedelta(days=5)).strftime('%Y-%m-%d')
        test_time = '11:00'

        # Initial booking
        res = self.client.post(f'/appointments/book/{doctor.id}', data={
            'baby_id': sophia.id,
            'appointment_date': test_date,
            'appointment_time': test_time,
            'consultation_type': 'In-Clinic',
            'reason_for_visit': 'Routine milestone evaluation for infant.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Your consultation request for Sophia Rivera", res.data)

        # Attempt to DOUBLE-BOOK the exact same doctor and slot
        res_double = self.client.post(f'/appointments/book/{doctor.id}', data={
            'baby_id': sophia.id,
            'appointment_date': test_date,
            'appointment_time': test_time,
            'consultation_type': 'In-Clinic',
            'reason_for_visit': 'Attempting second booking at same slot.'
        }, follow_redirects=True)
        self.assertEqual(res_double.status_code, 200)
        self.assertIn(b"already booked", res_double.data)

        self.logout()


if __name__ == '__main__':
    unittest.main()
