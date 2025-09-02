from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.account import FraudAlert, Account
from app.services.fraud_detection import FraudDetectionService
from app.services.account_service import AccountService
from app import db
from datetime import datetime

fraud_bp = Blueprint('fraud', __name__)
fraud_service = FraudDetectionService()
account_service = AccountService()

@fraud_bp.route('/fraud-alerts')
@login_required
def fraud_alerts():
    """Render the fraud alerts page."""
    # Get all accounts owned by the user
    accounts = account_service.get_accounts_by_user(current_user.id)
    account_ids = [account.id for account in accounts]
    
    # Get all fraud alerts for these accounts
    alerts = []
    for account_id in account_ids:
        account_alerts = fraud_service.get_fraud_alerts(account_id)
        alerts.extend(account_alerts)
    
    # Sort alerts by date (newest first)
    alerts.sort(key=lambda x: x.created_at, reverse=True)
    
    return render_template('fraud_alerts.html', alerts=alerts)

@fraud_bp.route('/fraud-alerts/<int:alert_id>')
@login_required
def view_alert(alert_id):
    """Render the fraud alert details page."""
    alert = FraudAlert.query.get(alert_id)
    
    if not alert:
        flash('Alert not found', 'danger')
        return redirect(url_for('fraud.fraud_alerts'))
    
    # Check if the user owns the account
    account = alert.account
    if account.user_id != current_user.id:
        flash('Alert not found', 'danger')
        return redirect(url_for('fraud.fraud_alerts'))
    
    # Get the transaction if it exists
    transaction = alert.transaction
    
    return render_template('fraud_alert.html', alert=alert, transaction=transaction)

@fraud_bp.route('/fraud-alerts/<int:alert_id>/resolve', methods=['POST'])
@login_required
def resolve_alert(alert_id):
    """Handle fraud alert resolution."""
    alert = FraudAlert.query.get(alert_id)
    
    if not alert:
        flash('Alert not found', 'danger')
        return redirect(url_for('fraud.fraud_alerts'))
    
    # Check if the user owns the account
    account = alert.account
    if account.user_id != current_user.id:
        flash('Alert not found', 'danger')
        return redirect(url_for('fraud.fraud_alerts'))
    
    # Get the resolution type from the form
    is_fraud = request.form.get('is_fraud') == 'true'
    
    # Resolve the alert
    result = fraud_service.resolve_fraud_alert(alert_id, is_fraud)
    
    if result.get('success', False):
        if is_fraud:
            flash('Alert marked as fraud. Your account has been frozen for security.', 'warning')
        else:
            flash('Alert marked as false positive. Thank you for your feedback.', 'success')
    else:
        flash(result.get('message', 'Failed to resolve alert'), 'danger')
    
    return redirect(url_for('fraud.fraud_alerts'))

@fraud_bp.route('/api/fraud-alerts/count')
@login_required
def fraud_alert_count():
    """Get the number of open fraud alerts for the current user."""
    # Get all accounts owned by the user
    accounts = account_service.get_accounts_by_user(current_user.id)
    account_ids = [account.id for account in accounts]
    
    # Count open alerts
    count = 0
    for account_id in account_ids:
        account_alerts = fraud_service.get_fraud_alerts(account_id, status='OPEN')
        count += len(account_alerts)
    
    return jsonify({'count': count})

# Admin routes for fraud management
@fraud_bp.route('/admin/fraud-alerts')
@login_required
def admin_fraud_alerts():
    """Render the admin fraud alerts page."""
    # Check if the user is an admin
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('account.dashboard'))
    
    # Get all fraud alerts
    alerts = FraudAlert.query.order_by(FraudAlert.created_at.desc()).all()
    
    return render_template('admin/fraud_alerts.html', alerts=alerts)

@fraud_bp.route('/admin/fraud-alerts/<int:alert_id>/resolve', methods=['POST'])
@login_required
def admin_resolve_alert(alert_id):
    """Handle admin fraud alert resolution."""
    # Check if the user is an admin
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('account.dashboard'))
    
    alert = FraudAlert.query.get(alert_id)
    
    if not alert:
        flash('Alert not found', 'danger')
        return redirect(url_for('fraud.admin_fraud_alerts'))
    
    # Get the resolution type from the form
    is_fraud = request.form.get('is_fraud') == 'true'
    
    # Resolve the alert
    result = fraud_service.resolve_fraud_alert(alert_id, is_fraud)
    
    if result.get('success', False):
        if is_fraud:
            flash('Alert marked as fraud. The account has been frozen.', 'warning')
        else:
            flash('Alert marked as false positive.', 'success')
    else:
        flash(result.get('message', 'Failed to resolve alert'), 'danger')
    
    return redirect(url_for('fraud.admin_fraud_alerts'))