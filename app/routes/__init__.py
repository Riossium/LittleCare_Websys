from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.parent import parent_bp
from app.routes.baby import baby_bp
from app.routes.health_records import health_bp
from app.routes.ai_assistant import ai_bp
from app.routes.recommendations import recommendations_bp
from app.routes.doctors import doctors_bp
from app.routes.appointments import appointments_bp
from app.routes.articles import articles_bp
from app.routes.notifications import notifications_bp
from app.routes.admin import admin_bp

__all__ = [
    'main_bp',
    'auth_bp',
    'parent_bp',
    'baby_bp',
    'health_bp',
    'ai_bp',
    'recommendations_bp',
    'doctors_bp',
    'appointments_bp',
    'articles_bp',
    'notifications_bp',
    'admin_bp'
]
