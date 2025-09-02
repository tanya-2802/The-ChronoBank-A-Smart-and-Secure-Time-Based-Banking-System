from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.services.notification_service import NotificationService

notification_bp = Blueprint('notification', __name__)
notification_service = NotificationService()

@notification_bp.route('/notifications')
@login_required
def notifications():
    """Render the notifications page."""
    notifications = notification_service.get_notifications_by_user(current_user.id)
    return render_template('notifications.html', notifications=notifications)

@notification_bp.route('/notifications/unread')
@login_required
def unread_notifications():
    """Render the unread notifications page."""
    notifications = notification_service.get_notifications_by_user(current_user.id, is_read=False)
    return render_template('notifications.html', notifications=notifications, unread_only=True)

@notification_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """Mark a notification as read."""
    result = notification_service.mark_notification_as_read(notification_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(result)
    
    if result.get('success', False):
        flash('Notification marked as read', 'success')
    else:
        flash(result.get('message', 'Failed to mark notification as read'), 'danger')
    
    return redirect(url_for('notification.notifications'))

@notification_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_as_read():
    """Mark all notifications as read."""
    result = notification_service.mark_all_notifications_as_read(current_user.id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(result)
    
    if result.get('success', False):
        flash(result.get('message', 'All notifications marked as read'), 'success')
    else:
        flash('Failed to mark notifications as read', 'danger')
    
    return redirect(url_for('notification.notifications'))

@notification_bp.route('/notifications/count')
@login_required
def notification_count():
    """Get the count of unread notifications."""
    notifications = notification_service.get_notifications_by_user(current_user.id, is_read=False)
    count = len(notifications)
    
    return jsonify({'count': count})