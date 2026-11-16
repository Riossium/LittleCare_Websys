from datetime import datetime
import json
from app.extensions import db


class AIConversation(db.Model):
    __tablename__ = 'ai_conversations'

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    baby_id = db.Column(db.Integer, db.ForeignKey('baby_profiles.id', ondelete='SET NULL'), nullable=True, index=True)
    title = db.Column(db.String(180), default='New Healthcare Inquiry')
    authorized_record_access = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to baby
    baby = db.relationship('BabyProfile', backref='ai_conversations')
    messages = db.relationship('AIMessage', backref='conversation', lazy='dynamic', cascade='all, delete-orphan', order_by='AIMessage.created_at.asc()')

    def __repr__(self):
        return f"<AIConversation #{self.id} Parent:{self.parent_id} Baby:{self.baby_id}>"


class AIMessage(db.Model):
    __tablename__ = 'ai_messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('ai_conversations.id', ondelete='CASCADE'), nullable=False, index=True)
    sender = db.Column(db.String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = db.Column(db.Text, nullable=False)
    suggested_actions_json = db.Column(db.Text, nullable=True)  # JSON-encoded array of action dicts
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def suggested_actions(self):
        if self.suggested_actions_json:
            try:
                return json.loads(self.suggested_actions_json)
            except Exception:
                return []
        return []

    @suggested_actions.setter
    def suggested_actions(self, value):
        if value:
            self.suggested_actions_json = json.dumps(value)
        else:
            self.suggested_actions_json = None

    def __repr__(self):
        return f"<AIMessage #{self.id} Sender:{self.sender} Conv:{self.conversation_id}>"


class Recommendation(db.Model):
    __tablename__ = 'recommendations'

    id = db.Column(db.Integer, primary_key=True)
    baby_id = db.Column(db.Integer, db.ForeignKey('baby_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    category = db.Column(db.String(60), nullable=False)  # Growth Monitoring, Vaccination, Milestone, Nutrition, Doctor Consultation, Missing Records
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False)
    urgency = db.Column(db.String(30), default='info')  # 'info', 'normal', 'important', 'action_required'
    action_url = db.Column(db.String(255), nullable=True)
    action_label = db.Column(db.String(100), nullable=True)
    is_dismissed = db.Column(db.Boolean, default=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def badge_class(self):
        badges = {
            'info': 'info',
            'normal': 'primary',
            'important': 'warning',
            'action_required': 'danger'
        }
        return badges.get(self.urgency, 'primary')

    def __repr__(self):
        return f"<Recommendation Baby:{self.baby_id} [{self.category}] {self.title}>"
