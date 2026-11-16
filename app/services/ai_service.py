import os
import json
import logging
from datetime import date
from flask import current_app
from app.models.article import Article
from app.models.health_record import GrowthRecord, VaccinationRecord, MedicalCheckupRecord

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are LittleCare AI, an empathetic, highly trained pediatric healthcare assistant designed to support parents and guardians with reliable educational information and guidance for infant and baby healthcare.

CRITICAL HEALTHCARE SAFETY RULES:
1. NEVER claim to provide a definitive medical diagnosis. State that only a licensed pediatrician or healthcare professional who physically examines the child can diagnose medical conditions.
2. NEVER prescribe prescription medication, antibiotics, or specific drug dosages.
3. NEVER replace professional pediatric consultations or emergency medical services.
4. EMERGENCY RED FLAGS: If the user describes emergency symptoms (such as infant fever > 38.5°C in babies younger than 3 months, labored breathing or retractions, extreme lethargy or unresponsiveness, signs of severe dehydration, seizure, cyanosis/blue lips), you MUST immediately and prominently advise them to seek emergency medical care at the nearest hospital or pediatric emergency room.
5. CONTEXTUAL REASONING: When authorized baby health records are provided in the context below, utilize them respectfully and accurately to answer specific questions (e.g., checking if growth percentiles are progressing or if upcoming vaccines are due), while clearly stating what comes from the records versus general pediatric references.
6. TONE: Warm, reassuring, clear, and scientifically grounded in WHO, CDC, and Philippine Pediatric Society pediatric guidelines.
"""


def build_baby_context(baby, include_records=True):
    """Safely extracts context from authorized baby records."""
    if not baby or not include_records:
        return "No specific baby profile authorized. Providing general pediatric educational information."

    ctx = [
        f"AUTHORIZED BABY RECORD SUMMARY:",
        f"- Baby Name: {baby.name}",
        f"- Age: {baby.age_display} (DOB: {baby.date_of_birth.strftime('%Y-%m-%d')}, Sex: {baby.gender})",
        f"- Blood Type: {baby.blood_type or 'Not recorded'}",
        f"- Known Allergies: {baby.allergies or 'None reported'}",
        f"- Birth Info: Weight {baby.birth_weight or 'N/A'} kg, Height {baby.birth_height or 'N/A'} cm"
    ]

    # Latest growth record
    latest_growth = baby.latest_growth
    if latest_growth:
        ctx.append(
            f"- Latest Growth ({latest_growth.recorded_date}): Weight: {latest_growth.weight_kg} kg, "
            f"Height: {latest_growth.height_cm} cm, Head Circumference: {latest_growth.head_circumference_cm or 'N/A'} cm"
        )
    else:
        ctx.append("- Latest Growth: No growth measurements recorded yet.")

    # Vaccinations summary
    vaccines = baby.vaccination_records.all()
    if vaccines:
        completed = [v.vaccine_name for v in vaccines if v.status == 'completed']
        scheduled = [f"{v.vaccine_name} (due {v.next_scheduled_date or 'soon'})" for v in vaccines if v.status in ['scheduled', 'pending']]
        if completed:
            ctx.append(f"- Administered Vaccines: {', '.join(completed[:8])}")
        if scheduled:
            ctx.append(f"- Upcoming/Scheduled Vaccines: {', '.join(scheduled[:5])}")
    else:
        ctx.append("- Vaccinations: No vaccination records logged yet.")

    # Latest checkup summary
    latest_checkup = baby.latest_checkup
    if latest_checkup:
        ctx.append(f"- Recent Checkup ({latest_checkup.checkup_date}): {latest_checkup.visit_type} by {latest_checkup.provider_name or 'Provider'}. Notes: {latest_checkup.clinical_notes or 'Routine evaluation'}")

    return "\n".join(ctx)


def get_relevant_articles(user_prompt):
    """Finds 1-3 matching educational articles from the LittleCare database."""
    prompt_lower = user_prompt.lower()
    articles = Article.query.filter_by(is_published=True).all()
    matched = []

    for art in articles:
        # Check title, category, and keywords
        if any(word in art.title.lower() or word in art.category.lower() or word in art.short_description.lower()
               for word in prompt_lower.split() if len(word) > 3):
            matched.append(art)
        if len(matched) >= 3:
            break

    if not matched:
        # Fallback to recent articles
        matched = Article.query.filter_by(is_published=True).order_by(Article.published_at.desc()).limit(2).all()

    return matched


def generate_suggested_actions(user_prompt, baby=None):
    """Produces intelligent interactive action buttons for the parent."""
    actions = []
    p = user_prompt.lower()

    if any(k in p for k in ['vaccin', 'shot', 'immuniz', 'schedule']):
        actions.append({
            'label': 'View Vaccination Schedule',
            'url': '/health/vaccinations',
            'icon': 'bi-shield-check'
        })
        actions.append({
            'label': 'Vaccination Guide Article',
            'url': '/articles?category=Vaccination+Guide',
            'icon': 'bi-journal-bookmark'
        })
    elif any(k in p for k in ['growth', 'weight', 'height', 'percentile', 'small', 'heavy', 'tall']):
        actions.append({
            'label': 'Open Growth Charts',
            'url': '/health/growth',
            'icon': 'bi-graph-up'
        })
        actions.append({
            'label': 'Log New Measurement',
            'url': '/health/growth/add',
            'icon': 'bi-plus-circle'
        })
    elif any(k in p for k in ['food', 'milk', 'feed', 'breastfeed', 'formula', 'solid', 'nutrition', 'eat']):
        actions.append({
            'label': 'Baby Nutrition Library',
            'url': '/articles?category=Baby+Nutrition',
            'icon': 'bi-egg-fried'
        })
    elif any(k in p for k in ['fever', 'cough', 'cold', 'sick', 'rash', 'vomit', 'poop', 'diarrhea', 'crying']):
        actions.append({
            'label': 'Book Pediatrician Consultation',
            'url': '/doctors',
            'icon': 'bi-person-badge'
        })
        actions.append({
            'label': 'Common Baby Concerns',
            'url': '/articles?category=Common+Baby+Health+Concerns',
            'icon': 'bi-heart-pulse'
        })

    # Always provide consultation option if medical concern
    if not any(a['url'] == '/doctors' for a in actions):
        actions.append({
            'label': 'Consult a Doctor',
            'url': '/doctors',
            'icon': 'bi-calendar2-plus'
        })

    return actions[:3]


def generate_rule_based_ai_response(user_prompt, baby_context, baby=None):
    """Provides high-quality, scientifically grounded pediatric responses when OpenAI key is absent or offline."""
    p = user_prompt.lower()
    baby_name = baby.name if baby else "your baby"
    age_str = f" ({baby.age_display})" if baby and hasattr(baby, 'age_display') else ""

    # Check for emergency keywords
    if any(k in p for k in ['blue lips', 'seizure', 'cannot breathe', 'hard to breathe', 'unresponsive', 'unconscious']):
        return (
            "🚨 **URGENT EMERGENCY WARNING**:\n\n"
            "The symptoms you described may be a life-threatening medical emergency. "
            "Please **immediately call emergency medical services (such as 911 or your local emergency hotline)** "
            "or transport your child to the nearest emergency hospital immediately.\n\n"
            "While waiting for medical help, keep the baby calm, do not give any oral fluids or medication if they are unconscious or having difficulty breathing, "
            "and ensure their airway remains clear."
        )

    if any(k in p for k in ['fever', 'temperature', 'hot', 'thermometer']):
        return (
            f"### Understanding Infant Fever\n\n"
            f"Fever is a natural immune response to help fight infections. For **{baby_name}**{age_str}, here are key pediatric guidelines:\n\n"
            "**When to seek immediate pediatric care:**\n"
            "- Any baby under 3 months with a rectal temperature of 38.0°C (100.4°F) or higher requires **immediate physical evaluation by a pediatrician**.\n"
            "- Babies showing extreme irritability, lethargy, decreased wet diapers (dehydration), or rapid breathing.\n\n"
            "**General Comfort Measures:**\n"
            "- Offer frequent feedings (breastmilk or formula) to maintain optimal hydration.\n"
            "- Dress the baby in a single layer of lightweight, comfortable clothing.\n"
            "- Keep the room well-ventilated at a comfortable temperature.\n"
            "- *Never give aspirin to infants or children.* Always confirm paracetamol dosages with your pediatrician before administration."
        )

    if any(k in p for k in ['vaccin', 'shot', 'immuniz']):
        return (
            f"### Vaccination Preparation & Schedule for {baby_name}\n\n"
            "Vaccines are among the safest and most effective ways to protect your little one from serious childhood diseases. "
            "Standard immunization schedules (WHO & Philippine Pediatric Society) protect against Tuberculosis (BCG), Hepatitis B, "
            "Diphtheria, Tetanus, Pertussis, Polio, Hib, Pneumococcal Disease (PCV), Rotavirus, and Measles/Mumps/Rubella (MMR).\n\n"
            "**Preparation Tips:**\n"
            "1. **Bring Baby Records:** Have your LittleCare vaccination record or baby book ready for your doctor's review.\n"
            "2. **Dress for Comfort:** Loose, easy-to-remove clothing helps make thigh or arm injections smoother.\n"
            "3. **Post-Vaccine Care:** It is normal for babies to have mild tenderness, low-grade fever, or fussiness for 24-48 hours. Offer plenty of cuddles and extra feedings."
        )

    if any(k in p for k in ['growth', 'weight', 'height', 'percentile', 'gain']):
        return (
            f"### Monitoring Baby Growth and Development\n\n"
            f"Tracking growth for **{baby_name}**{age_str} helps monitor consistent, healthy developmental progression along their individual growth curve.\n\n"
            "**Pediatric Growth Insights:**\n"
            "- Babies typically regain their birth weight by 10 to 14 days of life.\n"
            "- Most healthy infants double their birth weight by approximately 5 to 6 months and triple it by 1 year.\n"
            "- Growth occurs in spurts—consistent progress along their own percentile line is much more important than comparing against other babies.\n\n"
            "You can review WHO percentile charts under the **Growth Records** section of LittleCare to visualize your baby's milestones."
        )

    if any(k in p for k in ['food', 'solid', 'feed', 'breastfeed', 'formula', 'eat', 'puree']):
        return (
            f"### Infant Feeding and Nutrition Guidelines\n\n"
            "Healthy nutrition is the foundation of infant growth and brain development:\n\n"
            "- **0 to 6 Months:** The World Health Organization strongly recommends exclusive breastfeeding or infant formula for the first 6 months. No water, tea, or solid foods are needed during this stage.\n"
            "- **At 6 Months:** When your baby can sit with support and shows good head control, you can begin introducing single-ingredient soft purees or mashed foods (such as avocado, iron-fortified cereals, mashed squash, sweet potato) alongside continued milk feedings.\n"
            "- **Allergen Introduction:** Pediatric guidelines recommend introducing common allergens (like egg, peanut butter thinned with milk, fish) one at a time after 6 months while monitoring for any allergic reactions."
        )

    # General supportive answer
    return (
        f"### LittleCare Healthcare Guidance for {baby_name}\n\n"
        f"Thank you for reaching out regarding your baby's healthcare! Caring for a little one brings many questions, and having structured records and verified pediatric insights makes a wonderful difference.\n\n"
        f"**Key Insights:**\n"
        f"- Always ensure consistent sleep, responsive feeding, and regular well-baby checkups.\n"
        f"- Keep your LittleCare profile updated with recent measurements and immunizations so our recommendation engine can provide timely reminders.\n"
        f"- If you observe concerning physical changes or sudden shifts in feeding or behavior, we encourage booking a consultation with one of our verified pediatricians."
    )


def ask_ai_assistant(user_prompt, baby=None, authorize_records=False, conversation_history=None):
    """Processes question via OpenAI if configured, otherwise falls back smoothly to pediatric engine."""
    api_key = current_app.config.get('OPENAI_API_KEY')
    model = current_app.config.get('OPENAI_MODEL', 'gpt-4o-mini')

    baby_context = build_baby_context(baby, include_records=authorize_records)
    relevant_articles = get_relevant_articles(user_prompt)
    suggested_actions = generate_suggested_actions(user_prompt, baby)

    # If OpenAI API Key is configured and not empty
    if api_key and api_key.strip():
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": f"HEALTH RECORD CONTEXT:\n{baby_context}"}
            ]

            # Add previous messages from conversation if available
            if conversation_history:
                for msg in conversation_history[-6:]:  # last 3 turns
                    role = "user" if msg.sender == "user" else "assistant"
                    messages.append({"role": role, "content": msg.content})

            messages.append({"role": "user", "content": user_prompt})

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            ai_content = response.choices[0].message.content
            return {
                'answer': ai_content,
                'articles': [{'id': a.id, 'title': a.title, 'slug': a.slug, 'category': a.category, 'short_description': a.short_description} for a in relevant_articles],
                'suggested_actions': suggested_actions,
                'source': 'openai'
            }
        except Exception as e:
            logger.warning(f"OpenAI API call failed: {e}. Falling back to internal pediatric engine.")

    # Graceful fallback response
    ai_content = generate_rule_based_ai_response(user_prompt, baby_context, baby=baby)
    return {
        'answer': ai_content,
        'articles': [{'id': a.id, 'title': a.title, 'slug': a.slug, 'category': a.category, 'short_description': a.short_description} for a in relevant_articles],
        'suggested_actions': suggested_actions,
        'source': 'pediatric_engine'
    }
