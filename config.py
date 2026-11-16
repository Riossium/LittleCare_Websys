import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """Base Configuration for LittleCare Healthcare Management System"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'littlecare-secret-key-super-secure-dev-2026')
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Upload configurations
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

    # OpenAI API Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

    # Database Configuration with MySQL priority & automatic SQLite fallback if MySQL is offline
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASS = os.getenv('DB_PASS', '')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'littlecare_db')
    
    # Check if custom DATABASE_URL is provided
    custom_db_url = os.getenv('DATABASE_URL')
    
    if custom_db_url:
        SQLALCHEMY_DATABASE_URI = custom_db_url
    else:
        # Default MySQL connection string
        mysql_uri = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
        
        # Test if MySQL is reachable; if not, fall back to SQLite for robust local execution
        try:
            import pymysql
            conn = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASS,
                port=int(DB_PORT),
                connect_timeout=2
            )
            # Create DB if it does not exist
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.commit()
            conn.close()
            SQLALCHEMY_DATABASE_URI = mysql_uri
        except Exception:
            # Fall back to SQLite if MySQL daemon is not running or unreachable
            sqlite_path = os.path.join(basedir, 'littlecare.db')
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{sqlite_path}"

    # Flask-WTF CSRF — accept token from X-CSRFToken header (needed for AJAX/JSON fetch requests)
    WTF_CSRF_TIME_LIMIT = None  # Don't expire CSRF tokens (for long-lived chat sessions)
    WTF_CSRF_HEADERS = ['X-CSRFToken', 'X-CSRF-Token']

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
