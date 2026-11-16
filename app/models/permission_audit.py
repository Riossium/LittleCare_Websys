from datetime import datetime
from app.extensions import db


class RecordAccessPermission(db.Model):
    __tablename__ = 'record_access_permissions'

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    baby_id = db.Column(db.Integer, db.ForeignKey('baby_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    grantee_type = db.Column(db.String(30), nullable=False)  # 'doctor', 'ai_assistant'
    grantee_id = db.Column(db.Integer, nullable=True)  # DoctorProfile ID if doctor
    purpose = db.Column(db.String(255), default='Healthcare consultation review')
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<RecordAccessPermission Parent:{self.parent_id} Baby:{self.baby_id} Grantee:{self.grantee_type}:{self.grantee_id}>"


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    action = db.Column(db.String(120), nullable=False, index=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(60), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<AuditLog User:{self.user_id} Action:{self.action} at {self.timestamp}>"
