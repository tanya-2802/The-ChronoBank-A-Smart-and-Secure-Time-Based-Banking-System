from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.transaction import Transaction
from app.services.transaction_service import TransactionService
from app.services.account_service import AccountService
from app import db
from datetime import datetime

transaction_bp = Blueprint('transaction', __name__)
transaction_service = TransactionService()
account_service = AccountService()

@transaction_bp.route('/transactions')
@login_required
def transactions():
    """Render the transactions page."""
    accounts = account_service.get_accounts_by_user(current_user.id)
    
    # Get all transactions for all accounts
    all_transactions = []
    for account in accounts:
        account_transactions = transaction_service.get_transactions_by_account(account.id)
        all_transactions.extend(account_transactions)
    
    # Sort transactions by date (newest first)
    all_transactions.sort(key=lambda x: x.created_at, reverse=True)
    
    return render_template('transactions.html', transactions=all_transactions)

@transaction_bp.route('/transactions/<int:transaction_id>')
@login_required
def view_transaction(transaction_id):
    """Render the transaction details page."""
    from datetime import datetime
    
    transaction = transaction_service.get_transaction_by_id(transaction_id)
    
    if not transaction:
        flash('Transaction not found', 'danger')
        return redirect(url_for('transaction.transactions'))
    
    # Check if the user owns either the source or destination account
    user_accounts = account_service.get_accounts_by_user(current_user.id)
    user_account_ids = [account.id for account in user_accounts]
    
    if (transaction.source_account_id not in user_account_ids and 
        transaction.destination_account_id not in user_account_ids):
        flash('Transaction not found', 'danger')
        return redirect(url_for('transaction.transactions'))
    
    return render_template('transaction.html', transaction=transaction, now=datetime.utcnow())

@transaction_bp.route('/transactions/<int:transaction_id>/undo', methods=['POST'])
@login_required
def undo_transaction(transaction_id):
    """Handle transaction undo."""
    transaction = transaction_service.get_transaction_by_id(transaction_id)
    
    if not transaction:
        flash('Transaction not found', 'danger')
        return redirect(url_for('transaction.transactions'))
    
    # Check if the user owns the source account
    user_accounts = account_service.get_accounts_by_user(current_user.id)
    user_account_ids = [account.id for account in user_accounts]
    
    if transaction.source_account_id not in user_account_ids:
        flash('You can only undo transactions from your own accounts', 'danger')
        return redirect(url_for('transaction.view_transaction', transaction_id=transaction_id))
    
    result = transaction_service.undo_transaction(transaction_id)
    
    if result.get('success', False):
        flash('Transaction undone successfully', 'success')
    else:
        flash(result.get('message', 'Failed to undo transaction'), 'danger')
    
    return redirect(url_for('transaction.view_transaction', transaction_id=transaction_id))

@transaction_bp.route('/transactions/search', methods=['GET', 'POST'])
@login_required
def search_transactions():
    """Handle transaction search."""
    if request.method == 'POST':
        reference_code = request.form.get('reference_code')
        
        transaction = transaction_service.get_transaction_by_reference(reference_code)
        
        if not transaction:
            flash('Transaction not found', 'danger')
            return render_template('search_transaction.html')
        
        # Check if the user owns either the source or destination account
        user_accounts = account_service.get_accounts_by_user(current_user.id)
        user_account_ids = [account.id for account in user_accounts]
        
        if (transaction.source_account_id not in user_account_ids and 
            transaction.destination_account_id not in user_account_ids):
            flash('Transaction not found', 'danger')
            return render_template('search_transaction.html')
        
        return redirect(url_for('transaction.view_transaction', transaction_id=transaction.id))
    
    return render_template('search_transaction.html')
