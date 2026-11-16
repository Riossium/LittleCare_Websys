from datetime import date, datetime, timedelta
from app.extensions import db
from app.models.ai_chat import Recommendation
from app.models.health_record import GrowthRecord, VaccinationRecord, MedicalCheckupRecord


def generate_baby_recommendations(baby):
    """
    Analyzes baby profile, age, and existing health records to generate or refresh
    intelligent, non-alarming pediatric recommendations.
    """
    if not baby:
        return []

    # Clear previous un-dismissed recommendations for this baby to keep suggestions fresh
    Recommendation.query.filter_by(baby_id=baby.id, is_dismissed=False).delete()

    recommendations = []
    age_months = baby.age_in_months
    today = date.today()

    # 1. GROWTH MONITORING RECOMMENDATIONS
    latest_growth = baby.latest_growth
    if not latest_growth:
        recommendations.append(Recommendation(
            baby_id=baby.id,
            category='Growth Monitoring',
            title='Record First Growth Measurement',
            description=f'Tracking {baby.name}\'s weight and length helps visualize healthy physical development on pediatric growth curves.',
            urgency='important',
            action_url='/health/growth/add',
            action_label='Log Measurement'
        ))
    else:
        days_since_growth = (today - latest_growth.recorded_date).days
        if days_since_growth >= 30:
            recommendations.append(Recommendation(
                baby_id=baby.id,
                category='Growth Monitoring',
                title='Monthly Growth Update Recommended',
                description=f'It has been {days_since_growth} days since {baby.name}\'s last measurement ({latest_growth.weight_kg} kg on {latest_growth.recorded_date.strftime("%b %d")}). Monthly tracking provides consistent percentile curves.',
                urgency='normal',
                action_url='/health/growth/add',
                action_label='Update Growth Record'
            ))

    # 2. VACCINATION REMINDERS (Aligned with WHO & Philippine Pediatric Society recommendations)
    existing_vaccines = [v.vaccine_name.lower() for v in baby.vaccination_records.filter_by(status='completed').all()]

    vaccine_milestones = [
        {'min_age': 0, 'max_age': 1, 'name': 'BCG & Hepatitis B (Birth Dose)', 'key': 'bcg', 'label': 'Birth Vaccines'},
        {'min_age': 1, 'max_age': 3, 'name': 'Pentavalent 1, OPV 1, PCV 1', 'key': 'penta 1', 'label': '6-Week Immunizations'},
        {'min_age': 2, 'max_age': 4, 'name': 'Pentavalent 2, OPV 2, PCV 2', 'key': 'penta 2', 'label': '10-Week Immunizations'},
        {'min_age': 3, 'max_age': 5, 'name': 'Pentavalent 3, OPV 3, PCV 3, IPV', 'key': 'penta 3', 'label': '14-Week Immunizations'},
        {'min_age': 6, 'max_age': 8, 'name': 'Influenza (Flu Shot)', 'key': 'flu', 'label': '6-Month Flu Vaccine'},
        {'min_age': 9, 'max_age': 11, 'name': 'Measles Vaccine (MCV1)', 'key': 'measles', 'label': '9-Month Measles Dose'},
        {'min_age': 12, 'max_age': 15, 'name': 'MMR (Measles, Mumps, Rubella) Dose 1', 'key': 'mmr', 'label': '12-Month MMR Dose'}
    ]

    for v in vaccine_milestones:
        if v['min_age'] <= age_months <= v['max_age']:
            # Check if already logged
            if not any(v['key'] in name for name in existing_vaccines):
                recommendations.append(Recommendation(
                    baby_id=baby.id,
                    category='Vaccination Reminder',
                    title=f'Recommended Due: {v["name"]}',
                    description=f'{baby.name} is now in the recommended window for {v["label"]}. Timely immunizations provide critical immunity against severe pediatric infections.',
                    urgency='important',
                    action_url='/health/vaccinations/add',
                    action_label='Log Vaccine'
                ))
                break  # Recommend the primary immediate one

    # 3. NUTRITION & DEVELOPMENTAL MILESTONES
    if age_months < 6:
        recommendations.append(Recommendation(
            baby_id=baby.id,
            category='Nutrition',
            title='Exclusive Breastfeeding or Infant Formula',
            description=f'For infants under 6 months, breastmilk or certified infant formula provides all required nutrients, fluids, and immune protection. No supplementary water is recommended.',
            urgency='info',
            action_url='/articles?category=Baby+Nutrition',
            action_label='Read Nutrition Guide'
        ))
    elif 6 <= age_months <= 8:
        recommendations.append(Recommendation(
            baby_id=baby.id,
            category='Developmental Milestone',
            title='Starting Complementary Solid Foods',
            description=f'{baby.name} is at the milestone to explore single-ingredient purees (avocado, squash, iron-rich cereals) alongside continued milk feedings.',
            urgency='normal',
            action_url='/articles?category=Baby+Nutrition',
            action_label='Solid Food Tips'
        ))
    elif 9 <= age_months <= 12:
        recommendations.append(Recommendation(
            baby_id=baby.id,
            category='Developmental Milestone',
            title='Encouraging Pincer Grasp & Soft Finger Foods',
            description=f'Around 9 to 12 months, babies develop their pincer grasp. Soft, bite-sized fruit slices, well-cooked vegetable sticks, and teething crackers encourage self-feeding skills.',
            urgency='info',
            action_url='/articles?category=Baby+Growth+and+Development',
            action_label='Milestone Guide'
        ))

    # 4. MISSING PROFILE DETAILS (Non-alarming gentle prompt)
    missing_items = []
    if not baby.blood_type:
        missing_items.append('blood type')
    if not baby.birth_weight:
        missing_items.append('birth weight')
    if not baby.allergies:
        missing_items.append('allergy status')

    if missing_items:
        recommendations.append(Recommendation(
            baby_id=baby.id,
            category='Missing Records',
            title='Complete Health Profile Details',
            description=f'Consider updating {baby.name}\'s profile with {", ".join(missing_items)} so doctors and AI consultations have complete medical context.',
            urgency='info',
            action_url=f'/baby/{baby.id}/edit',
            action_label='Update Profile'
        ))

    # 5. DOCTOR CONSULTATION SUGGESTION
    latest_checkup = baby.latest_checkup
    if not latest_checkup:
        recommendations.append(Recommendation(
            baby_id=baby.id,
            category='Doctor Consultation',
            title='Schedule First Well-Baby Checkup',
            description=f'Regular physical evaluations by a pediatrician ensure developmental milestones and general infant well-being are progressing safely.',
            urgency='normal',
            action_url='/doctors',
            action_label='Find Pediatrician'
        ))
    else:
        days_since_checkup = (today - latest_checkup.checkup_date).days
        if days_since_checkup >= 60 and age_months <= 12:
            recommendations.append(Recommendation(
                baby_id=baby.id,
                category='Doctor Consultation',
                title='Well-Baby Pediatric Evaluation Due',
                description=f'It has been over 2 months since {baby.name}\'s last pediatric consultation. Routine checkups in the first year evaluate motor skills, vision, hearing, and growth.',
                urgency='normal',
                action_url='/doctors',
                action_label='Book Appointment'
            ))

    # Save recommendations to database
    for rec in recommendations:
        db.session.add(rec)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()

    return recommendations
