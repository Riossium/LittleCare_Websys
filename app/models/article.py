from datetime import datetime
import re
from app.extensions import db


class Article(db.Model):
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(220), nullable=False)
    slug = db.Column(db.String(250), unique=True, nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False, index=True)
    short_description = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    featured_image = db.Column(db.String(255), default='default-article.jpg')
    author_name = db.Column(db.String(120), default='LittleCare Pediatric Team')
    medical_references = db.Column(db.Text, nullable=True)
    reading_time_minutes = db.Column(db.Integer, default=3)
    is_published = db.Column(db.Boolean, default=True)
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def generate_slug(title):
        clean = re.sub(r'[^\w\s-]', '', title.lower()).strip()
        slug = re.sub(r'[-\s]+', '-', clean)
        return slug

    def __repr__(self):
        return f"<Article {self.title} ({self.category}) Published:{self.is_published}>"
