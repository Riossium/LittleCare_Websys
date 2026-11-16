import os
from flask import Flask, render_template, session
from flask_login import current_user
from config import config
from app.extensions import db, login_manager, csrf
from app.models.baby import BabyProfile


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Ensure upload folders exist
    uploads_base = app.config['UPLOAD_FOLDER']
    for folder in ['babies', 'doctors', 'articles', 'documents']:
        os.makedirs(os.path.join(uploads_base, folder), exist_ok=True)

    # Register blueprints
    from app.routes import (
        main_bp, auth_bp, parent_bp, baby_bp, health_bp,
        ai_bp, recommendations_bp, doctors_bp, appointments_bp,
        articles_bp, notifications_bp, admin_bp
    )

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(parent_bp)
    app.register_blueprint(baby_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(doctors_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(articles_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(admin_bp)

    # Context processors for templates
    @app.context_processor
    def inject_global_data():
        active_baby = None
        unread_count = 0

        if current_user.is_authenticated:
            unread_count = current_user.unread_notifications_count()

            if current_user.is_parent:
                active_id = session.get('active_baby_id')
                if active_id:
                    active_baby = BabyProfile.query.filter_by(id=active_id, parent_id=current_user.id, is_active=True).first()
                if not active_baby:
                    active_baby = current_user.baby_profiles.filter_by(is_active=True).first()
                    if active_baby:
                        session['active_baby_id'] = active_baby.id

        return {
            'active_baby': active_baby,
            'unread_notifications_count': unread_count
        }

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('components/error.html', code=403, title="Access Forbidden", message="You do not have authorization to view this medical record or page."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('components/error.html', code=404, title="Page Not Found", message="The requested healthcare resource or profile could not be located."), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('components/error.html', code=500, title="System Error", message="An unexpected error occurred. Our engineering team has been notified."), 500

    return app
