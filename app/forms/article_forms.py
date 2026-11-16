from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SelectField, TextAreaField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class ArticleForm(FlaskForm):
    title = StringField('Article Title', validators=[DataRequired(), Length(min=5, max=220)])
    category = SelectField('Category', choices=[
        ('Baby Nutrition', 'Baby Nutrition'),
        ('Vaccination Guide', 'Vaccination Guide'),
        ('Baby Growth and Development', 'Baby Growth and Development'),
        ('Common Baby Health Concerns', 'Common Baby Health Concerns'),
        ('Baby Hygiene and Safety', 'Baby Hygiene and Safety'),
        ('Parenting Tips', 'Parenting Tips')
    ], validators=[DataRequired()])
    short_description = TextAreaField('Short Summary (Teaser)', validators=[
        DataRequired(),
        Length(min=10, max=500)
    ])
    content = TextAreaField('Full Article Content (Markdown or HTML supported)', validators=[
        DataRequired(),
        Length(min=30)
    ])
    author_name = StringField('Author / Medical Reviewer', default='LittleCare Pediatric Team', validators=[DataRequired(), Length(max=120)])
    medical_references = TextAreaField('Medical References & Sources (WHO, CDC, PPS)', validators=[Optional(), Length(max=1000)])
    reading_time_minutes = IntegerField('Estimated Reading Time (Minutes)', default=3, validators=[DataRequired(), NumberRange(min=1, max=60)])
    featured_image = FileField('Featured Cover Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Only image files (jpg, png, webp) are permitted.')
    ])
    is_published = BooleanField('Publish this article immediately', default=True)
    submit = SubmitField('Save Article')
