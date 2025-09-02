from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.services.loan_service import LoanService
from app.services.account_service import AccountService
from app.forms.loan_form import LoanApplicationForm, LoanPaymentForm

loan_bp = Blueprint('loan', __name__)
loan_service = LoanService()
account_service = AccountService()

@loan_bp.route('/loans')
@login_required
def loans():
    """Render the loans page."""
    # Get all accounts for the current user
    all_accounts = account_service.get_accounts_by_user(current_user.id)
    
    # Filter accounts to only include LoanAccount type
    loan_accounts = [account for account in all_accounts if account.account_type.name == 'LoanAccount']
    
    # Get all loans for loan accounts
    all_loans = []
    for account in loan_accounts:
        loans = loan_service.get_loans_by_account(account.id)
        all_loans.extend(loans)
    
    # Sort loans by creation date (newest first)
    all_loans.sort(key=lambda x: x.created_at, reverse=True)
    
    return render_template('loans/index.html', loans=all_loans, accounts=loan_accounts)

@loan_bp.route('/loans/active')
@login_required
def active_loans():
    """Render the active loans page."""
    # Get all accounts for the current user
    all_accounts = account_service.get_accounts_by_user(current_user.id)
    
    # Filter accounts to only include LoanAccount type
    loan_accounts = [account for account in all_accounts if account.account_type.name == 'LoanAccount']
    
    # Get active loans for loan accounts
    active_loans = []
    for account in loan_accounts:
        loans = loan_service.get_loans_by_account(account.id, status='ACTIVE')
        active_loans.extend(loans)
    
    # Sort loans by due date (soonest first)
    active_loans.sort(key=lambda x: x.due_date)
    
    return render_template('loans/active.html', loans=active_loans, accounts=loan_accounts)

@loan_bp.route('/loans/<int:loan_id>')
@login_required
def loan_details(loan_id):
    """Render the loan details page."""
    # Get the loan
    loan = loan_service.get_loan_by_id(loan_id)
    
    if not loan:
        flash('Loan not found', 'danger')
        return redirect(url_for('loan.loans'))
    
    # Get the account
    account = account_service.get_account_by_id(loan.account_id)
    
    # Check if the account belongs to the current user
    if account.user_id != current_user.id:
        flash('You do not have permission to view this loan', 'danger')
        return redirect(url_for('loan.loans'))
    
    # Get the payment schedule
    schedule_result = loan_service.get_payment_schedule(loan_id)
    
    if not schedule_result.get('success', False):
        flash(schedule_result.get('message', 'Failed to get payment schedule'), 'danger')
        schedule = []
    else:
        schedule = schedule_result.get('schedule', [])
    
    # Create a payment form
    payment_form = LoanPaymentForm()
    payment_form.account_id.data = account.id
    
    return render_template(
        'loans/details.html',
        loan=loan,
        account=account,
        schedule=schedule,
        payment_form=payment_form
    )

@loan_bp.route('/accounts/<int:account_id>/apply')
@login_required
def apply_for_loan(account_id):
    """Render the loan application page."""
    # Get the account
    account = account_service.get_account_by_id(account_id)
    
    if not account:
        flash('Account not found', 'danger')
        return redirect(url_for('account.accounts'))
    
    # Check if the account belongs to the current user
    if account.user_id != current_user.id:
        flash('You do not have permission to apply for a loan on this account', 'danger')
        return redirect(url_for('account.accounts'))
    
    # Create a loan application form
    form = LoanApplicationForm()
    form.account_id.data = account.id
    
    return render_template('loans/apply.html', form=form, account=account)

@loan_bp.route('/accounts/<int:account_id>/apply', methods=['POST'])
@login_required
def submit_loan_application(account_id):
    """Process a loan application."""
    # Get the account
    account = account_service.get_account_by_id(account_id)
    
    if not account:
        flash('Account not found', 'danger')
        return redirect(url_for('account.accounts'))
    
    # Check if the account belongs to the current user
    if account.user_id != current_user.id:
        flash('You do not have permission to apply for a loan on this account', 'danger')
        return redirect(url_for('account.accounts'))
    
    # Create a loan application form
    form = LoanApplicationForm()
    
    if form.validate_on_submit():
        # Convert amount from hours to seconds
        amount_seconds = int(form.amount.data * 3600)
        
        # Create the loan
        result = loan_service.create_loan(
            account_id=account.id,
            amount=amount_seconds,
            term_days=form.term_days.data,
            repayment_strategy=form.repayment_strategy.data
        )
        
        if result.get('success', False):
            flash(f"Loan created successfully! You've borrowed {result.get('amount')} at {result.get('interest_rate')} interest.", 'success')
            return redirect(url_for('loan.loan_details', loan_id=result.get('loan_id')))
        else:
            flash(result.get('message', 'Failed to create loan'), 'danger')
    
    return render_template('loans/apply.html', form=form, account=account)

@loan_bp.route('/loans/<int:loan_id>/pay', methods=['POST'])
@login_required
def make_payment(loan_id):
    """Make a payment towards a loan."""
    # Get the loan
    loan = loan_service.get_loan_by_id(loan_id)
    
    if not loan:
        flash('Loan not found', 'danger')
        return redirect(url_for('loan.loans'))
    
    # Get the account
    account = account_service.get_account_by_id(loan.account_id)
    
    # Check if the account belongs to the current user
    if account.user_id != current_user.id:
        flash('You do not have permission to make a payment on this loan', 'danger')
        return redirect(url_for('loan.loans'))
    
    # Create a payment form
    form = LoanPaymentForm()
    
    if form.validate_on_submit():
        # Convert amount from hours to seconds
        payment_amount = int(form.amount.data * 3600)
        
        # Make the payment
        result = loan_service.make_payment(loan_id, payment_amount)
        
        if result.get('success', False):
            flash(f"Payment made successfully! Remaining balance: {result.get('remaining_amount')}", 'success')
        else:
            flash(result.get('message', 'Failed to make payment'), 'danger')
    
    return redirect(url_for('loan.loan_details', loan_id=loan_id))