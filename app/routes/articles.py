from flask import Blueprint, render_template, request
from app.extensions import db
from app.models.article import Article

articles_bp = Blueprint('articles', __name__, url_prefix='/articles')


@articles_bp.route('/')
def index():
    """Module 10: Searchable Healthcare Library"""
    search = request.args.get('q', '').strip()
    selected_category = request.args.get('category', '').strip()

    query = Article.query.filter_by(is_published=True)

    if search:
        query = query.filter(
            db.or_(
                Article.title.ilike(f"%{search}%"),
                Article.short_description.ilike(f"%{search}%"),
                Article.content.ilike(f"%{search}%")
            )
        )

    if selected_category:
        query = query.filter_by(category=selected_category)

    articles = query.order_by(Article.published_at.desc()).all()

    categories = [
        'Baby Nutrition',
        'Vaccination Guide',
        'Baby Growth and Development',
        'Common Baby Health Concerns',
        'Baby Hygiene and Safety',
        'Parenting Tips'
    ]

    return render_template(
        'articles/index.html',
        articles=articles,
        categories=categories,
        search=search,
        selected_category=selected_category
    )


@articles_bp.route('/<string:slug>')
def detail(slug):
    """Module 10: Article Detail Page"""
    article = Article.query.filter_by(slug=slug, is_published=True).first_or_404()
    related_articles = Article.query.filter(
        Article.category == article.category,
        Article.id != article.id,
        Article.is_published == True
    ).limit(3).all()

    return render_template('articles/detail.html', article=article, related_articles=related_articles)
