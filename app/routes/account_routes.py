from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.account import Account, AccountType
from app.services.account_service import AccountService
from app.services.transaction_service import TransactionService
from app import db
from datetime import datetime

account_bp = Blueprint('account', __name__)
account_service = AccountService()
transaction_service = TransactionService()

@account_bp.route('/dashboard')
@login_required
def dashboard():
    """Render the dashboard page."""
    accounts = account_service.get_accounts_by_user(current_user.id)
    return render_template('dashboard.html', accounts=accounts)

@account_bp.route('/accounts')
@login_required
def accounts():
    """Render the accounts page."""
    accounts = account_service.get_accounts_by_user(current_user.id)
    account_types = account_service.get_account_types()
    return render_template('accounts.html', accounts=accounts, account_types=account_types)

@account_bp.route('/accounts/create', methods=['GET', 'POST'])
@login_required
def create_account():
    """Handle account creation."""
    if request.method == 'POST':
        account_type_name = request.form.get('account_type')
        
        try:
            account = account_service.create_account(current_user.id, account_type_name)
            
            # Check if the account balance is below the threshold
            account_service.notification_service.check_balance_threshold(account)
            
            flash(f'Account {account.account_number} created successfully', 'success')
            return redirect(url_for('account.accounts'))
        except ValueError as e:
            flash(str(e), 'danger')
    
    account_types = account_service.get_account_types()
    return render_template('create_account.html', account_types=account_types)

@account_bp.route('/accounts/custom', methods=['GET', 'POST'])
@login_required
def create_custom_account():
    """Handle custom account creation."""
    if request.method == 'POST':
        account_type_name = request.form.get('account_type')
        
        # Convert hours to seconds
        initial_balance_hours = float(request.form.get('initial_balance', 0))
        initial_balance = int(initial_balance_hours * 3600)
        
        # Convert hours to seconds for transaction limit if provided
        transaction_limit_str = request.form.get('transaction_limit', '')
        if transaction_limit_str:
            transaction_limit_hours = float(transaction_limit_str)
            transaction_limit = int(transaction_limit_hours * 3600)
        else:
            transaction_limit = 0
            
        interest_rate = float(request.form.get('interest_rate', 0))
        
        try:
            account = account_service.create_custom_account(
                current_user.id,
                account_type_name,
                initial_balance,
                transaction_limit,
                interest_rate
            )
            
            # Check if the account balance is below the threshold
            account_service.notification_service.check_balance_threshold(account)
            
            flash(f'Custom account {account.account_number} created successfully', 'success')
            return redirect(url_for('account.accounts'))
        except ValueError as e:
            flash(str(e), 'danger')
    
    account_types = account_service.get_account_types()
    return render_template('create_custom_account.html', account_types=account_types)

@account_bp.route('/accounts/<int:account_id>')
@login_required
def view_account(account_id):
    """Render the account details page."""
    from datetime import datetime
    
    account = account_service.get_account_by_id(account_id)
    
    if not account or account.user_id != current_user.id:
        flash('Account not found', 'danger')
        return redirect(url_for('account.accounts'))
    
    transactions = transaction_service.get_transactions_by_account(account_id)
    return render_template('account.html', account=account, transactions=transactions, now=datetime.utcnow())

@account_bp.route('/accounts/<int:account_id>/deposit', methods=['GET', 'POST'])
@login_required
def deposit(account_id):
    """Handle time deposit."""
    account = account_service.get_account_by_id(account_id)
    
    if not account or account.user_id != current_user.id:
        flash('Account not found', 'danger')
        return redirect(url_for('account.accounts'))
    
    # Check if the account is frozen
    if account.status == 'FROZEN':
        flash('This account is frozen due to suspicious activity. Please contact customer support.', 'danger')
        return redirect(url_for('account.view_account', account_id=account_id))
    
    if request.method == 'POST':
        # Convert hours to seconds
        amount_hours = float(request.form.get('amount', 0))
        amount_seconds = int(amount_hours * 3600)
        description = request.form.get('description', 'Deposit')
        
        if amount_hours <= 0:
            flash('Amount must be positive', 'danger')
            return render_template('deposit.html', account=account)
        
        result = transaction_service.deposit(
            account_id,
            amount_seconds,
            description,
            current_user.id,
            request.remote_addr
        )
        
        if result.get('success', False):
            flash('Deposit successful', 'success')
            return redirect(url_for('account.view_account', account_id=account_id))
        else:
            # Check if this was a fraud detection issue
            if result.get('fraud_detected', False):
                risk_factors = result.get('risk_factors', [])
                risk_message = ", ".join(risk_factors) if risk_factors else "Unknown risk factors"
                flash(f"Deposit flagged as potentially fraudulent: {risk_message}", 'danger')
                return redirect(url_for('account.view_account', account_id=account_id))
            else:
                flash(result.get('message', 'Deposit failed'), 'danger')
    
    return render_template('deposit.html', account=account)

@account_bp.route('/accounts/<int:account_id>/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw(account_id):
    """Handle time withdrawal."""
    account = account_service.get_account_by_id(account_id)
    
    if not account or account.user_id != current_user.id:
        flash('Account not found', 'danger')
        return redirect(url_for('account.accounts'))
    
    # Check if the account is frozen
    if account.status == 'FROZEN':
        flash('This account is frozen due to suspicious activity. Please contact customer support.', 'danger')
        return redirect(url_for('account.view_account', account_id=account_id))
    
    if request.method == 'POST':
        # Convert hours to seconds
        amount_hours = float(request.form.get('amount', 0))
        amount_seconds = int(amount_hours * 3600)
        description = request.form.get('description', 'Withdrawal')
        
        if amount_hours <= 0:
            flash('Amount must be positive', 'danger')
            return render_template('withdraw.html', account=account)
        
        result = account_service.withdraw(account_id, amount_seconds)
        
        if result.get('success', False):
            # Create a transaction record
            transaction_type = transaction_service.get_transaction_types()[2]  # Withdrawal
            
            transaction = {
                'transaction_type_id': transaction_type.id,
                'source_account_id': account_id,
                'destination_account_id': None,
                'amount': amount_seconds,
                'description': description,
                'user_id': current_user.id,
                'ip_address': request.remote_addr
            }
            
            # Record the transaction
            transaction_obj = transaction_service.ledger.record_transaction(**transaction)
            
            # Update transaction status to COMPLETED
            transaction_obj.status = 'COMPLETED'
            transaction_obj.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Check if it's a large transaction (≥300 hours) and notify the user
            if amount_hours >= 300:
                # Import here to avoid circular imports
                from app.patterns.behavioral.observer import NotificationObserver
                observer = NotificationObserver()
                observer.notify_large_transaction(transaction_obj)
            
            flash('Withdrawal successful', 'success')
            return redirect(url_for('account.view_account', account_id=account_id))
        else:
            # Check if this was a fraud detection issue
            if result.get('fraud_detected', False):
                risk_factors = result.get('risk_factors', [])
                risk_message = ", ".join(risk_factors) if risk_factors else "Unknown risk factors"
                flash(f"Withdrawal flagged as potentially fraudulent: {risk_message}", 'danger')
                return redirect(url_for('account.view_account', account_id=account_id))
            else:
                flash(result.get('message', 'Withdrawal failed'), 'danger')
    
    return render_template('withdraw.html', account=account)

@account_bp.route('/accounts/<int:account_id>/transfer', methods=['GET', 'POST'])
@login_required
def transfer(account_id):
    """Handle time transfer."""
    account = account_service.get_account_by_id(account_id)
    
    if not account or account.user_id != current_user.id:
        flash('Account not found', 'danger')
        return redirect(url_for('account.accounts'))
    
    # Check if the account is frozen
    if account.status == 'FROZEN':
        flash('This account is frozen due to suspicious activity. Please contact customer support.', 'danger')
        return redirect(url_for('account.view_account', account_id=account_id))
    
    if request.method == 'POST':
        destination_account_number = request.form.get('destination_account')
        # Convert hours to seconds
        amount_hours = float(request.form.get('amount', 0))
        amount_seconds = int(amount_hours * 3600)
        description = request.form.get('description', 'Transfer')
        
        destination_account = account_service.get_account_by_number(destination_account_number)
        
        if not destination_account:
            flash('Destination account not found', 'danger')
            return render_template('transfer.html', account=account)
        
        # Check if the destination account is frozen
        if destination_account.status == 'FROZEN':
            flash('The destination account is frozen and cannot receive transfers.', 'danger')
            return render_template('transfer.html', account=account)
        
        if amount_hours <= 0:
            flash('Amount must be positive', 'danger')
            return render_template('transfer.html', account=account)
        
        # MODIFIED: Force fraud detection for testing purposes
        if amount_hours > 10:  # If amount is greater than 10 hours
            # Create a fraud detection service
            from app.services.fraud_detection import FraudDetectionService
            fraud_service = FraudDetectionService()
            
            # Directly check for fraud
            fraud_check = fraud_service.check_transaction(
                source_account_id=account_id,
                destination_account_id=destination_account.id,
                amount=amount_seconds
            )
            
            # Display fraud check results
            flash(f"Fraud check - Risk score: {fraud_check.get('risk_score', 0)}, Factors: {', '.join(fraud_check.get('risk_factors', []))}", 'info')
            
            # If fraud is detected, redirect to fraud alerts
            if not fraud_check.get('is_safe', True):
                flash('Transaction flagged as potentially fraudulent. Please check your fraud alerts.', 'warning')
                return redirect(url_for('fraud.fraud_alerts'))
        
        result = transaction_service.transfer(
            account_id,
            destination_account.id,
            amount_seconds,
            description,
            current_user.id,
            request.remote_addr
        )
        
        if result.get('success', False):
            # Check if it's a large transaction (≥300 hours) and notify the user
            if amount_hours >= 10:  # Reduced from 300 to 10 for testing
                # Get the transaction object
                transaction = result.get('transaction')
                if transaction:
                    # Import here to avoid circular imports
                    from app.patterns.behavioral.observer import NotificationObserver
                    observer = NotificationObserver()
                    observer.notify_large_transaction(transaction)
            
            flash('Transfer successful', 'success')
            return redirect(url_for('account.view_account', account_id=account_id))
        else:
            # Check if the transaction was flagged as fraudulent
            if result.get('fraud_detected', False):
                flash(result.get('message', 'Transfer failed due to fraud detection'), 'warning')
                # Redirect to fraud alerts page
                return redirect(url_for('fraud.fraud_alerts'))
            else:
                flash(result.get('message', 'Transfer failed'), 'danger')
    
    return render_template('transfer.html', account=account)
