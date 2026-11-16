from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.ai_chat import Recommendation
from app.utils import parent_required, get_active_baby
from app.services.recommendation_service import generate_baby_recommendations

recommendations_bp = Blueprint('recommendations', __name__, url_prefix='/recommendations')


@recommendations_bp.route('/')
@login_required
@parent_required
def index():
    """Module 7: Smart Healthcare Recommendations Hub"""
    baby = get_active_baby()
    if not baby:
        flash("Please create or select a baby profile to view smart healthcare recommendations.", "info")
        return redirect(url_for('baby.create'))

    # Generate or refresh recommendations
    recommendations = generate_baby_recommendations(baby)
    
    # Group by category
    categories = {}
    for rec in recommendations:
        if rec.category not in categories:
            categories[rec.category] = []
        categories[rec.category].append(rec)

    return render_template(
        'recommendations/index.html',
        baby=baby,
        recommendations=recommendations,
        categories=categories
    )


@recommendations_bp.route('/<int:rec_id>/dismiss', methods=['POST'])
@login_required
@parent_required
def dismiss(rec_id):
    """Module 7: Dismiss a Recommendation"""
    rec = Recommendation.query.get_or_404(rec_id)
    if rec.baby.parent_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    rec.is_dismissed = True
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'success'})
    
    flash("Recommendation dismissed.", "info")
    return redirect(url_for('recommendations.index'))
