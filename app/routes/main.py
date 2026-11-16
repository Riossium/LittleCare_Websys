from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models.article import Article
from app.models.doctor import DoctorProfile

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Module 1: Public Landing Page"""
    recent_articles = Article.query.filter_by(is_published=True).order_by(Article.published_at.desc()).limit(3).all()
    featured_doctors = DoctorProfile.query.filter_by(is_verified=True).limit(4).all()
    return render_template('main/index.html', recent_articles=recent_articles, featured_doctors=featured_doctors)


@main_bp.route('/about')
def about():
    """About Us Page"""
    return render_template('main/about.html')


@main_bp.route('/services')
def services():
    """Healthcare Services Page"""
    return render_template('main/services.html')


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact Us Page with form"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        flash(f"Thank you, {name}! Your message regarding '{subject}' has been received. Our clinical support team will get back to you at {email}.", "success")
        return redirect(url_for('main.contact'))
    return render_template('main/contact.html')


@main_bp.route('/privacy')
def privacy():
    """Philippine Data Privacy Act 2012 compliance & privacy information"""
    return render_template('main/privacy.html')
