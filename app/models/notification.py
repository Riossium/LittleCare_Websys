from datetime import datetime
from app.extensions import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(40), default='system')  # 'appointment', 'vaccination', 'growth', 'recommendation', 'system'
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    @property
    def icon_class(self):
        icons = {
            'appointment': 'bi-calendar-check text-primary',
            'vaccination': 'bi-shield-check text-success',
            'growth': 'bi-graph-up text-info',
            'recommendation': 'bi-lightbulb text-warning',
            'system': 'bi-bell text-secondary'
        }
        return icons.get(self.type, 'bi-bell text-primary')

    def __repr__(self):
        return f"<Notification User:{self.user_id} [{self.type}] Read:{self.is_read}>"
