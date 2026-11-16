from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.notification import Notification

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/')
@login_required
def index():
    """Module 11: In-Website Notifications Hub"""
    notifications = current_user.notifications.order_by(Notification.created_at.desc()).all()
    return render_template('notifications/index.html', notifications=notifications)


@notifications_bp.route('/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    """Module 11: Mark single notification as read"""
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'success'})
    
    if notif.link:
        return redirect(notif.link)
    return redirect(url_for('notifications.index'))


@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Module 11: Mark all notifications as read"""
    current_user.notifications.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    flash("All notifications marked as read.", "info")
    return redirect(url_for('notifications.index'))


@notifications_bp.route('/api/unread-count')
@login_required
def unread_count():
    """Module 11: Unread notifications counter badge API"""
    count = current_user.unread_notifications_count()
    return jsonify({'unread_count': count})
