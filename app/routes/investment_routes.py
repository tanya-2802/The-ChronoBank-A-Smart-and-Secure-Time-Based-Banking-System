from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.services.investment_service import InvestmentService
from app.services.account_service import AccountService
from app.forms.investment_form import InvestmentForm
from datetime import datetime

investment_bp = Blueprint('investment', __name__)
investment_service = InvestmentService()
account_service = AccountService()

@investment_bp.route('/investments')
@login_required
def investments():
    """Render the investments page."""
    # Get all accounts for the current user
    all_accounts = account_service.get_accounts_by_user(current_user.id)
    
    # Filter accounts to only include InvestorAccount type
    investor_accounts = [account for account in all_accounts if account.account_type.name == 'InvestorAccount']
    
    # Get all investments for investor accounts
    all_investments = []
    for account in investor_accounts:
        investments = investment_service.get_investments_by_account(account.id)
        all_investments.extend(investments)
    
    # Sort investments by creation date (newest first)
    all_investments.sort(key=lambda x: x.created_at, reverse=True)
    
    return render_template('investments/index.html', investments=all_investments, accounts=investor_accounts)

@investment_bp.route('/investments/active')
@login_required
def active_investments():
    """Render the active investments page."""
    # Get all accounts for the current user
    all_accounts = account_service.get_accounts_by_user(current_user.id)
    
    # Filter accounts to only include InvestorAccount type
    investor_accounts = [account for account in all_accounts if account.account_type.name == 'InvestorAccount']
    
    # Get active investments for investor accounts
    active_investments = []
    for account in investor_accounts:
        investments = investment_service.get_investments_by_account(account.id, status='ACTIVE')
        active_investments.extend(investments)
    
    # Sort investments by maturity date (soonest first)
    active_investments.sort(key=lambda x: x.maturity_date)
    
    return render_template('investments/active.html', investments=active_investments, accounts=investor_accounts)

@investment_bp.route('/investments/<int:investment_id>')
@login_required
def investment_details(investment_id):
    """Render the investment details page."""
    # Get the investment
    investment = investment_service.get_investment_by_id(investment_id)
    
    if not investment:
        flash('Investment not found', 'danger')
        return redirect(url_for('investment.investments'))
    
    # Get the account
    account = account_service.get_account_by_id(investment.account_id)
    
    # Check if the account belongs to the current user
    if account.user_id != current_user.id:
        flash('You do not have permission to view this investment', 'danger')
        return redirect(url_for('investment.investments'))
    
    # Calculate expected return
    return_result = investment_service.calculate_return(investment_id)
    
    return render_template(
        'investments/details.html',
        investment=investment,
        account=account,
        return_result=return_result,
        divmod=divmod,  # Add the divmod function to the template context
        now=datetime.utcnow()  # Also add the current time for progress calculation
    )

@investment_bp.route('/accounts/<int:account_id>/invest')
@login_required
def create_investment(account_id):
    """Render the investment creation page."""
    # Get the account
    account = account_service.get_account_by_id(account_id)
    
    if not account:
        flash('Account not found', 'danger')
        return redirect(url_for('account.accounts'))
    
    # Check if the account belongs to the current user
    if account.user_id != current_user.id:
        flash('You do not have permission to invest from this account', 'danger')
        return redirect(url_for('account.accounts'))
    
    # Check if the account is an investor account
    if account.account_type.name != 'InvestorAccount':
        flash('Only investor accounts can make investments', 'danger')
        return redirect(url_for('account.account_details', account_id=account_id))
    
    # Create an investment form
    form = InvestmentForm()
    form.account_id.data = account.id
    
    return render_template('investments/create.html', form=form, account=account)

@investment_bp.route('/accounts/<int:account_id>/invest', methods=['POST'])
@login_required
def submit_investment(account_id):
    """Process an investment creation."""
    # Get the account
    account = account_service.get_account_by_id(account_id)
    
    if not account:
        flash('Account not found', 'danger')
        return redirect(url_for('account.accounts'))
    
    # Check if the account belongs to the current user
    if account.user_id != current_user.id:
        flash('You do not have permission to invest from this account', 'danger')
        return redirect(url_for('account.accounts'))
    
    # Check if the account is an investor account
    if account.account_type.name != 'InvestorAccount':
        flash('Only investor accounts can make investments', 'danger')
        return redirect(url_for('account.account_details', account_id=account_id))
    
    # Create an investment form
    form = InvestmentForm()
    
    if form.validate_on_submit():
        # Convert amount from hours to seconds
        amount_seconds = int(form.amount.data * 3600)
        
        # Create the investment
        result = investment_service.create_investment(
            account_id=account.id,
            amount=amount_seconds,
            term_days=form.term_days.data,
            user_id=current_user.id,
            ip_address=request.remote_addr
        )
        
        if result.get('success', False):
            flash(f"Investment created successfully! You've invested {form.amount.data} hours for {form.term_days.data} days.", 'success')
            return redirect(url_for('investment.investment_details', investment_id=result.get('investment_id')))
        else:
            flash(result.get('message', 'Failed to create investment'), 'danger')
    
    return render_template('investments/create.html', form=form, account=account)

@investment_bp.route('/investments/<int:investment_id>/withdraw', methods=['POST'])
@login_required
def withdraw_investment(investment_id):
    """Withdraw an investment."""
    # Get the investment
    investment = investment_service.get_investment_by_id(investment_id)
    
    if not investment:
        flash('Investment not found', 'danger')
        return redirect(url_for('investment.investments'))
    
    # Get the account
    account = account_service.get_account_by_id(investment.account_id)
    
    # Check if the account belongs to the current user
    if account.user_id != current_user.id:
        flash('You do not have permission to withdraw this investment', 'danger')
        return redirect(url_for('investment.investments'))
    
    # Withdraw the investment
    result = investment_service.withdraw_investment(investment_id)
    
    if result.get('success', False):
        flash(result.get('message', 'Investment withdrawn successfully'), 'success')
    else:
        flash(result.get('message', 'Failed to withdraw investment'), 'danger')
    
    return redirect(url_for('investment.investments'))