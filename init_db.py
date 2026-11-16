"""
LittleCare Database Initializer and Seeder
Populates initial Admin, Verified Doctors, Sample Parent, Babies,
Growth Records, Immunizations, Published Articles, Schedules, and Notifications.
"""

import os
from datetime import date, datetime, timedelta, time
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.baby import BabyProfile
from app.models.doctor import DoctorProfile, DoctorAvailability
from app.models.health_record import GrowthRecord, VaccinationRecord, MedicalCheckupRecord
from app.models.appointment import Appointment
from app.models.article import Article
from app.models.notification import Notification
from app.models.ai_chat import AIConversation, AIMessage
from app.services.recommendation_service import generate_baby_recommendations

app = create_app('development')


def seed_database():
    with app.app_context():
        print("Creating all database tables...")
        db.create_all()

        # Check if already seeded
        if User.query.filter_by(email='admin@littlecare.health').first():
            print("Database already contains seed data. Skipping seeding.")
            return

        print("Seeding initial administrator account...")
        admin = User(
            email='admin@littlecare.health',
            first_name='Admin',
            last_name='LittleCare',
            phone='0917-000-0001',
            role='admin',
            is_active=True
        )
        admin.set_password('Admin123!')
        db.session.add(admin)

        print("Seeding verified pediatricians...")
        doctors_data = [
            {
                'email': 'doctor.santos@littlecare.health',
                'first_name': 'Maria Elena',
                'last_name': 'Santos',
                'phone': '0917-888-1001',
                'specialty': 'General Pediatrics',
                'license': '108492',
                'ptr': 'PTR-77291',
                'clinic': 'St. Luke\'s Medical Center - Global City',
                'address': 'Room 502, Medical Arts Building, BGC, Taguig',
                'exp': 12,
                'bio': 'Dr. Maria Elena Santos is a board-certified pediatrician with over 12 years of clinical practice in well-baby care, neonatal development, and infant nutrition counseling.'
            },
            {
                'email': 'doctor.reyes@littlecare.health',
                'first_name': 'Carlos Miguel',
                'last_name': 'Reyes',
                'phone': '0917-888-1002',
                'specialty': 'Pediatric Neonatology',
                'license': '094821',
                'ptr': 'PTR-88310',
                'clinic': 'The Medical City - Ortigas',
                'address': 'Suite 712, Medical Arts Tower, Ortigas Ave, Pasig',
                'exp': 15,
                'bio': 'Dr. Carlos Miguel Reyes specializes in newborn intensive care, premature infant milestone monitoring, and comprehensive preventative immunization programs.'
            },
            {
                'email': 'doctor.cruz@littlecare.health',
                'first_name': 'Angelica Joy',
                'last_name': 'Cruz',
                'phone': '0917-888-1003',
                'specialty': 'Developmental Pediatrics',
                'license': '119284',
                'ptr': 'PTR-99124',
                'clinic': 'Philippine Children\'s Medical Center',
                'address': 'Quezon Avenue corner Agham Road, Quezon City',
                'exp': 8,
                'bio': 'Dr. Angelica Joy Cruz provides clinical evaluations for motor skills development, early speech milestones, sensory processing, and positive parent-child interaction.'
            }
        ]

        doctors_profiles = []
        for d in doctors_data:
            doc_user = User(
                email=d['email'],
                first_name=d['first_name'],
                last_name=d['last_name'],
                phone=d['phone'],
                role='doctor',
                is_active=True
            )
            doc_user.set_password('Doctor123!')
            db.session.add(doc_user)
            db.session.flush()

            profile = DoctorProfile(
                user_id=doc_user.id,
                specialty=d['specialty'],
                license_number=d['license'],
                ptr_number=d['ptr'],
                clinic_affiliation=d['clinic'],
                clinic_address=d['address'],
                experience_years=d['exp'],
                bio=d['bio'],
                consultation_types='In-Clinic & Teleconsultation',
                is_verified=True,
                verification_date=datetime.utcnow() - timedelta(days=30),
                verification_notes='Verified with PRC Physician Registry'
            )
            db.session.add(profile)
            db.session.flush()
            doctors_profiles.append(profile)

            # Add published availability for each doctor for next 7 days
            today = date.today()
            for day_offset in [1, 2, 4, 6]:
                avail = DoctorAvailability(
                    doctor_profile_id=profile.id,
                    available_date=today + timedelta(days=day_offset),
                    start_time=time(9, 0),
                    end_time=time(12, 0),
                    slot_duration_minutes=30,
                    max_patients=6,
                    is_active=True
                )
                db.session.add(avail)

        print("Seeding sample parent account...")
        parent = User(
            email='parent@littlecare.health',
            first_name='Carmela',
            last_name='Rivera',
            phone='0917-555-1234',
            role='parent',
            is_active=True
        )
        parent.set_password('Parent123!')
        db.session.add(parent)
        db.session.flush()

        print("Seeding baby profiles...")
        today = date.today()
        # Sophia Rivera: ~6 months old
        sophia_dob = today - timedelta(days=185)
        sophia = BabyProfile(
            parent_id=parent.id,
            name='Sophia Rivera',
            date_of_birth=sophia_dob,
            gender='female',
            blood_type='A+',
            birth_weight=3.2,
            birth_height=49.5,
            birth_head_circumference=34.0,
            allergies='No known food or drug allergies',
            pediatrician_notes='Full term delivery at 39 weeks. Excellent APGAR scores (9/10). Attending pediatrician: Dr. Maria Elena Santos.',
            is_active=True
        )
        db.session.add(sophia)

        # Lucas Rivera: ~18 months old
        lucas_dob = today - timedelta(days=540)
        lucas = BabyProfile(
            parent_id=parent.id,
            name='Lucas Rivera',
            date_of_birth=lucas_dob,
            gender='male',
            blood_type='O+',
            birth_weight=3.5,
            birth_height=51.0,
            birth_head_circumference=35.0,
            allergies='Mild skin eczema triggered by dry weather',
            pediatrician_notes='Regular well-child milestones following expected curve.',
            is_active=True
        )
        db.session.add(lucas)
        db.session.flush()

        print("Seeding growth records for Sophia...")
        growth_data = [
            (sophia_dob, 3.2, 49.5, 34.0, 'Birth measurement at hospital'),
            (sophia_dob + timedelta(days=30), 4.3, 53.5, 36.5, '1-month well baby check'),
            (sophia_dob + timedelta(days=60), 5.4, 57.0, 38.5, '2-month routine measurement'),
            (sophia_dob + timedelta(days=120), 6.9, 63.5, 41.5, '4-month milestone measurement'),
            (today - timedelta(days=5), 7.8, 67.0, 43.0, '6-month measurement, following 50th percentile')
        ]
        for g_date, wt, ht, hc, note in growth_data:
            rec = GrowthRecord(
                baby_id=sophia.id,
                recorded_date=g_date,
                weight_kg=wt,
                height_cm=ht,
                head_circumference_cm=hc,
                notes=note,
                recorded_by='Parent (Carmela Rivera)'
            )
            db.session.add(rec)

        print("Seeding vaccination records for Sophia...")
        vaccines_data = [
            ('BCG (Tuberculosis)', 1, sophia_dob, None, 'completed', 'Hospital Delivery Nursery', 'BCG-9021'),
            ('Hepatitis B (Birth Dose)', 1, sophia_dob, None, 'completed', 'Hospital Delivery Nursery', 'HEPB-104'),
            ('Pentavalent (DTP-HepB-Hib) Dose 1', 1, sophia_dob + timedelta(days=45), None, 'completed', 'St. Luke\'s Medical Center', 'PENTA-441'),
            ('Oral Polio Vaccine (OPV) Dose 1', 1, sophia_dob + timedelta(days=45), None, 'completed', 'St. Luke\'s Medical Center', 'OPV-882'),
            ('Pneumococcal Conjugate Vaccine (PCV) Dose 1', 1, sophia_dob + timedelta(days=45), None, 'completed', 'St. Luke\'s Medical Center', 'PCV-120'),
            ('Pentavalent (DTP-HepB-Hib) Dose 2', 2, sophia_dob + timedelta(days=75), None, 'completed', 'St. Luke\'s Medical Center', 'PENTA-502'),
            ('Oral Polio Vaccine (OPV) Dose 2', 2, sophia_dob + timedelta(days=75), None, 'completed', 'St. Luke\'s Medical Center', 'OPV-912'),
            ('Pneumococcal Conjugate Vaccine (PCV) Dose 2', 2, sophia_dob + timedelta(days=75), None, 'completed', 'St. Luke\'s Medical Center', 'PCV-133'),
            ('Pentavalent (DTP-HepB-Hib) Dose 3', 3, sophia_dob + timedelta(days=105), None, 'completed', 'St. Luke\'s Medical Center', 'PENTA-612'),
            ('Oral Polio Vaccine (OPV) Dose 3', 3, sophia_dob + timedelta(days=105), None, 'completed', 'St. Luke\'s Medical Center', 'OPV-980'),
            ('Inactivated Polio Vaccine (IPV)', 1, sophia_dob + timedelta(days=105), None, 'completed', 'St. Luke\'s Medical Center', 'IPV-024'),
            ('Influenza (Flu Shot)', 1, None, today + timedelta(days=10), 'scheduled', 'St. Luke\'s Clinic', None),
            ('Measles Vaccine (MCV1)', 1, None, today + timedelta(days=90), 'scheduled', 'St. Luke\'s Clinic', None)
        ]
        for v_name, dose, d_admin, d_next, stat, admin_by, batch in vaccines_data:
            v_rec = VaccinationRecord(
                baby_id=sophia.id,
                vaccine_name=v_name,
                dose_number=dose,
                date_administered=d_admin,
                next_scheduled_date=d_next,
                status=stat,
                administered_by=admin_by,
                batch_number=batch
            )
            db.session.add(v_rec)

        print("Seeding medical checkup records...")
        checkup = MedicalCheckupRecord(
            baby_id=sophia.id,
            checkup_date=today - timedelta(days=5),
            visit_type='Routine Well-Baby Checkup',
            provider_name='Dr. Maria Elena Santos, MD',
            diagnosis='Healthy 6-month infant progressing along expected developmental milestones.',
            treatment_summary='Continue breastfeeding or infant formula on demand. Begin complementary single-ingredient soft purees (mashed avocado, squash, sweet potato) once or twice daily. Continue Vitamin D drops.',
            clinical_notes='Infant is alert, socially interactive, smiling, tracks objects smoothly across 180 degrees, rolls easily back to belly and belly to back.'
        )
        db.session.add(checkup)

        print("Seeding sample appointments...")
        doc1 = doctors_profiles[0]
        # Upcoming confirmed appointment
        apt1 = Appointment(
            parent_id=parent.id,
            doctor_id=doc1.id,
            baby_id=sophia.id,
            appointment_date=today + timedelta(days=3),
            appointment_time=time(10, 0),
            consultation_type='In-Clinic',
            reason_for_visit='Follow-up growth checkup and 6-month influenza vaccine consultation.',
            status='Confirmed'
        )
        db.session.add(apt1)

        print("Seeding healthcare library educational articles...")
        articles_data = [
            {
                'title': 'Starting Solid Foods: A Pediatrician\'s Step-by-Step Guide for 6-Month-Olds',
                'slug': 'starting-solid-foods-pediatrician-guide-6-months',
                'category': 'Baby Nutrition',
                'summary': 'Learn the signs of developmental readiness for complementary foods, ideal first purees, and safety precautions.',
                'content': """
<p>Reaching the 6-month milestone is an exciting developmental leap. The World Health Organization (WHO) and pediatric societies globally recommend exclusive breastfeeding or formula feeding for the first six months of life, followed by the introduction of nutrient-dense complementary foods.</p>
<h4>Signs of Developmental Readiness</h4>
<p>Before introducing solids, confirm that your baby displays the following milestones:</p>
<ul>
    <li>Can sit upright with minimal support and has solid head and neck control.</li>
    <li>Has lost the tongue-thrust reflex (no longer pushes solid objects out of the mouth automatically).</li>
    <li>Shows clear curiosity about food by watching you eat, leaning forward, or reaching out.</li>
</ul>
<h4>Best First Foods</h4>
<p>Begin with single-ingredient soft foods pureed or mashed to a smooth texture: avocado, squash, sweet potato, pureed cooked carrots, and iron-fortified baby cereals mixed with breastmilk or formula. Introduce one new food every 3 to 5 days to monitor for any allergic sensitivities.</p>
<h4>Safety and Texture Guidelines</h4>
<p>Never add salt, sugar, honey, or artificial flavorings to infant foods. Honey is strictly contraindicated for infants under 12 months due to the risk of infant botulism.</p>
""",
                'author': 'Dr. Maria Elena Santos, MD (Pediatrics)',
                'refs': 'WHO Guidelines on Complementary Feeding (2023); Philippine Pediatric Society Nutrition Committee Guidelines.',
                'read_time': 4
            },
            {
                'title': 'Understanding Childhood Immunizations: Philippine & WHO Schedules Explained',
                'slug': 'understanding-childhood-immunizations-philippine-who-schedule',
                'category': 'Vaccination Guide',
                'summary': 'A complete guide to why vaccines are scheduled at specific weeks and how each dose protects against severe infections.',
                'content': """
<p>Immunization remains one of medicine\'s greatest achievements, safeguarding vulnerable infants against life-threatening childhood illnesses. Understanding the rationale behind vaccine schedules empowers parents to protect their children effectively.</p>
<h4>Birth to 14 Weeks: Foundation of Immunity</h4>
<ul>
    <li><strong>BCG & Hepatitis B (Birth):</strong> Administered within 24 hours of life to protect against extrapulmonary tuberculosis meningitis and perinatal Hepatitis B infection.</li>
    <li><strong>Pentavalent (6, 10, 14 Weeks):</strong> Combines protection against Diphtheria, Tetanus, Pertussis (whooping cough), Hepatitis B, and Haemophilus influenzae type b.</li>
    <li><strong>Oral & Inactivated Polio (OPV / IPV):</strong> Eradicates the risk of paralytic poliomyelitis through mucosal and systemic antibody stimulation.</li>
    <li><strong>Pneumococcal Conjugate (PCV):</strong> Shields against severe invasive pneumococcal pneumonia and bacterial meningitis.</li>
</ul>
<h4>Managing Post-Vaccination Reactions</h4>
<p>Mild swelling, tenderness at the injection site, and a low-grade temperature are common, normal signs that the immune system is actively building protective antibodies. Dress your baby in loose, airy clothing, offer extra comfort feedings, and consult your pediatrician if fever exceeds 38.5°C.</p>
""",
                'author': 'Dr. Carlos Miguel Reyes, MD (Neonatology)',
                'refs': 'Department of Health Expanded Programme on Immunization (EPI); WHO Global Vaccine Action Plan.',
                'read_time': 5
            },
            {
                'title': 'Decoding Infant Growth Percentiles: Why Every Baby Grows Differently',
                'slug': 'decoding-infant-growth-percentiles-who-curves',
                'category': 'Baby Growth and Development',
                'summary': 'Why individual growth curve consistency is much more significant than comparison against other babies.',
                'content': """
<p>When pediatricians measure an infant\'s weight, length, and head circumference, they plot these values on World Health Organization (WHO) Child Growth Standards curves. But what do percentiles actually mean?</p>
<h4>Understanding the Percentile Concept</h4>
<p>A percentile simply reflects where your child falls among a healthy reference group of 100 breastfed children of the same age and sex. If your baby is at the 50th percentile for weight, it means 50 out of 100 babies weigh less, and 50 weigh more. A baby at the 15th percentile is not "underweight" or "failing"—they may naturally be a leaner or more petite child!</p>
<h4>The Golden Rule: Following Their Own Curve</h4>
<p>What pediatricians evaluate closely is trajectory continuity. A healthy baby who stays steadily along their 25th percentile curve from month to month is thriving wonderfully. Sharp downward drops across multiple major percentile lines or sudden plateaus over consecutive visits are what prompt clinical assessment.</p>
""",
                'author': 'Dr. Angelica Joy Cruz, MD (Developmental Pediatrics)',
                'refs': 'WHO Child Growth Standards (2006); American Academy of Pediatrics Physical Growth Guidelines.',
                'read_time': 4
            },
            {
                'title': 'Managing Infant Fever at Home: When to Observe and When to Seek Emergency Care',
                'slug': 'managing-infant-fever-home-care-emergency-flags',
                'category': 'Common Baby Health Concerns',
                'summary': 'Vital guidelines for assessing infant fever, comfort measures, and critical red-flag symptoms requiring emergency evaluation.',
                'content': """
<p>Fever is one of the most common reasons parents seek medical advice. It is essential to recognize that fever itself is not an illness—it is the body\'s natural, beneficial defense mechanism to fight off bacterial or viral infections.</p>
<h4>Critical Age-Specific Red Flags</h4>
<ul>
    <li><strong>Infants Under 3 Months:</strong> Any rectal temperature of 38.0°C (100.4°F) or higher in a baby under 3 months is a pediatric medical emergency requiring immediate emergency room evaluation, regardless of how well the baby appears.</li>
    <li><strong>Difficulty Breathing:</strong> Rapid breathing, flaring nostrils, or chest retractions (skin sucking in between ribs).</li>
    <li><strong>Dehydration Signs:</strong> Less than 3 wet diapers in 24 hours, lack of tears when crying, sunken soft spot (fontanelle).</li>
    <li><strong>Lethargy:</strong> Difficulty waking the baby, extreme weakness, or unresponsiveness.</li>
</ul>
<h4>Home Care for Mild Fevers (Older Babies)</h4>
<p>Ensure generous fluid intake (breastmilk or formula). Dress the baby in one layer of light, breathable cotton. Keep room temperatures comfortable (22-24°C). Never give aspirin to infants or children.</p>
""",
                'author': 'Dr. Maria Elena Santos, MD',
                'refs': 'Pediatric Infectious Disease Society Guidelines; Nelson Textbook of Pediatrics.',
                'read_time': 5
            },
            {
                'title': 'Creating a Safe Sleep Environment: Essential SIDS Prevention Guidelines',
                'slug': 'creating-safe-sleep-environment-sids-prevention',
                'category': 'Baby Hygiene and Safety',
                'summary': 'Evidence-based sleep guidelines: Back to sleep, firm surfaces, and eliminating crib hazards for infant safety.',
                'content': """
<p>Sudden Infant Death Syndrome (SIDS) and sleep-related infant deaths can be significantly reduced by following verified safe sleep protocols.</p>
<h4>The ABCs of Safe Sleep</h4>
<ul>
    <li><strong>A - ALONE:</strong> The baby should sleep in their own crib, bassinet, or play yard, never in an adult bed, couch, or armchair. Room-sharing without bed-sharing is recommended for the first 6 to 12 months.</li>
    <li><strong>B - On their BACK:</strong> Always place your baby on their back for every sleep—naps and nighttime—until they turn 1 year old.</li>
    <li><strong>C - In a Clear CRIB:</strong> Use a firm, flat mattress covered tightly by a fitted sheet. Keep pillows, plush toys, quilts, bumper pads, and loose blankets completely out of the sleep space.</li>
</ul>
""",
                'author': 'LittleCare Pediatric Safety Committee',
                'refs': 'AAP Task Force on Sudden Infant Death Syndrome (2022 Guidelines).',
                'read_time': 3
            }
        ]

        for art in articles_data:
            article = Article(
                title=art['title'],
                slug=art['slug'],
                category=art['category'],
                short_description=art['summary'],
                content=art['content'],
                author_name=art['author'],
                medical_references=art['refs'],
                reading_time_minutes=art['read_time'],
                is_published=True
            )
            db.session.add(article)

        print("Seeding initial notifications...")
        notif1 = Notification(
            user_id=parent.id,
            title="Welcome to LittleCare!",
            message="Your parent account has been successfully created. Explore growth curves, track vaccinations, or ask our pediatric AI assistant.",
            type='system',
            link='/parent/dashboard'
        )
        notif2 = Notification(
            user_id=parent.id,
            title="Upcoming Consultation Reminder",
            message=f"Reminder: Sophia has an upcoming appointment with Dr. Maria Elena Santos on {(today + timedelta(days=3)).strftime('%b %d')} at 10:00 AM.",
            type='appointment',
            link=f'/appointments/{apt1.id}'
        )
        db.session.add_all([notif1, notif2])

        db.session.commit()

        # Generate initial smart recommendations for Sophia
        print("Generating smart recommendations for Sophia...")
        generate_baby_recommendations(sophia)

        print("\n========================================================")
        print(" LittleCare Database Initialized and Seeded Successfully! ")
        print("========================================================")
        print(" DEMO ACCOUNTS:")
        print(" Admin:   admin@littlecare.health   / Admin123!")
        print(" Parent:  parent@littlecare.health  / Parent123!")
        print(" Doctor:  doctor.santos@littlecare.health / Doctor123!")
        print("========================================================\n")


if __name__ == '__main__':
    seed_database()
