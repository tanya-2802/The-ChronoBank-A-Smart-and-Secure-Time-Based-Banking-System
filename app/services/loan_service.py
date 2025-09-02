from app.models.loan import Loan
from app.models.account import Account
from app.patterns.behavioral.loan_strategy import LoanStrategyFactory
from app.services.notification_service import NotificationService
from app import db
from datetime import datetime, timedelta
import random

class LoanService:
    """
    Service for managing loans.
    """
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def get_loan_by_id(self, loan_id):
        """
        Get a loan by ID.
        
        Args:
            loan_id: The ID of the loan
            
        Returns:
            Loan: The loan with the specified ID
        """
        return Loan.query.get(loan_id)
    
    def get_loans_by_account(self, account_id, status=None):
        """
        Get all loans for an account, optionally filtered by status.
        
        Args:
            account_id: The ID of the account
            status: The status to filter by
            
        Returns:
            list: A list of loans
        """
        query = Loan.query.filter_by(account_id=account_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(Loan.created_at.desc()).all()
    
    def create_loan(self, account_id, amount, term_days, repayment_strategy='FIXED'):
        """
        Create a new loan.
        
        Args:
            account_id: The ID of the account to create the loan for
            amount: The amount of the loan in seconds
            term_days: The term of the loan in days
            repayment_strategy: The repayment strategy to use (FIXED, DYNAMIC, EARLY)
            
        Returns:
            dict: A dictionary containing the result of the operation
        """
        # Get the account
        account = Account.query.get(account_id)
        
        if not account:
            return {"success": False, "message": "Account not found"}
        
        # Check if the account is eligible for a loan
        if account.status != 'ACTIVE':
            return {"success": False, "message": "Account is not active"}
        
        # Check if the account has too many active loans
        active_loans = Loan.query.filter_by(account_id=account_id, status='ACTIVE').count()
        if active_loans >= 3:
            return {"success": False, "message": "Account has too many active loans"}
        
        # Calculate interest rate based on account reputation and market conditions
        base_interest_rate = 0.05  # 5% base interest rate
        
        # Adjust based on account reputation
        reputation_adjustment = (100 - account.user.reputation_score) / 1000  # 0-10% adjustment
        
        # Adjust based on loan term
        term_adjustment = term_days / 365 * 0.02  # Longer terms have higher rates
        
        # Adjust based on loan amount
        amount_adjustment = amount / 86400 / 30 * 0.01  # Larger loans have higher rates
        
        # Calculate final interest rate
        interest_rate = base_interest_rate + reputation_adjustment + term_adjustment + amount_adjustment
        
        # Ensure interest rate is reasonable
        interest_rate = max(0.01, min(0.25, interest_rate))
        
        # Create the loan
        loan = Loan(
            account_id=account_id,
            amount=amount,
            interest_rate=interest_rate,
            term_days=term_days,
            repayment_strategy=repayment_strategy,
            status='ACTIVE',
            created_at=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=term_days)
        )
        
        # Calculate remaining amount based on the repayment strategy
        strategy = LoanStrategyFactory.create_strategy(repayment_strategy)
        loan.remaining_amount = strategy.calculate_repayment_amount(loan)
        
        try:
            # Add the loan to the database
            db.session.add(loan)
            
            # Add the loan amount to the account balance
            account.balance += amount
            account.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Schedule a notification for when the loan is due
            self.schedule_loan_due_notification(loan)
            
            return {
                "success": True,
                "message": "Loan created successfully",
                "loan_id": loan.id,
                "amount": loan.format_amount(),
                "interest_rate": f"{loan.interest_rate:.2%}",
                "term_days": loan.term_days,
                "due_date": loan.due_date.strftime('%Y-%m-%d'),
                "repayment_amount": loan.format_remaining()
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}
    
    def make_payment(self, loan_id, payment_amount):
        """
        Make a payment towards a loan.
        
        Args:
            loan_id: The ID of the loan
            payment_amount: The amount of the payment in seconds
            
        Returns:
            dict: A dictionary containing the result of the operation
        """
        # Get the loan
        loan = self.get_loan_by_id(loan_id)
        
        if not loan:
            return {"success": False, "message": "Loan not found"}
        
        # Get the account
        account = Account.query.get(loan.account_id)
        
        if not account:
            return {"success": False, "message": "Account not found"}
        
        # Check if the account has enough balance
        if account.balance < payment_amount:
            return {"success": False, "message": "Insufficient balance"}
        
        try:
            # Create the appropriate strategy
            strategy = LoanStrategyFactory.create_strategy(loan.repayment_strategy)
            
            # Apply the payment using the strategy
            strategy.apply_payment(loan, payment_amount)
            
            # Deduct the payment from the account balance
            account.balance -= payment_amount
            account.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                "success": True,
                "message": "Payment made successfully",
                "remaining_amount": loan.format_remaining(),
                "status": loan.status
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}
    
    def get_payment_schedule(self, loan_id):
        """
        Get the payment schedule for a loan.
        
        Args:
            loan_id: The ID of the loan
            
        Returns:
            dict: A dictionary containing the payment schedule
        """
        # Get the loan
        loan = self.get_loan_by_id(loan_id)
        
        if not loan:
            return {"success": False, "message": "Loan not found"}
        
        # Create the appropriate strategy
        strategy = LoanStrategyFactory.create_strategy(loan.repayment_strategy)
        
        # Calculate the payment schedule
        schedule = strategy.calculate_payment_schedule(loan)
        
        return {
            "success": True,
            "loan_id": loan.id,
            "amount": loan.format_amount(),
            "interest_rate": f"{loan.interest_rate:.2%}",
            "term_days": loan.term_days,
            "due_date": loan.due_date.strftime('%Y-%m-%d'),
            "repayment_amount": loan.format_remaining(),
            "status": loan.status,
            "schedule": schedule
        }
    
    def check_overdue_loans(self):
        """
        Check for overdue loans and update their status.
        
        Returns:
            int: The number of overdue loans
        """
        # Get all active loans that are past their due date
        overdue_loans = Loan.query.filter(
            Loan.status == 'ACTIVE',
            Loan.due_date < datetime.utcnow()
        ).all()
        
        for loan in overdue_loans:
            # Mark the loan as defaulted
            loan.status = 'DEFAULTED'
            loan.updated_at = datetime.utcnow()
            
            # Notify the user
            self.notification_service.notify_loan_due(loan)
        
        if overdue_loans:
            db.session.commit()
        
        return len(overdue_loans)
    
    def schedule_loan_due_notification(self, loan):
        """
        Schedule a notification for when a loan is due.
        
        Args:
            loan: The loan to schedule a notification for
        """
        # In a real application, you would use a task scheduler like Celery
        # For now, we'll just check if the loan is due soon
        days_until_due = (loan.due_date - datetime.utcnow()).days
        
        if days_until_due <= 7:
            # Notify the user if the loan is due within a week
            self.notification_service.notify_loan_due(loan)
    
from app.models.loan import Loan
from app.models.account import Account
from app.patterns.behavioral.loan_strategy import LoanStrategyFactory
from app.services.notification_service import NotificationService
from app import db
from datetime import datetime, timedelta
import random

class LoanService:
    """
    Service for managing loans.
    """
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def get_loan_by_id(self, loan_id):
        """
        Get a loan by ID.
        
        Args:
            loan_id: The ID of the loan
            
        Returns:
            Loan: The loan with the specified ID
        """
        return Loan.query.get(loan_id)
    
    def get_loans_by_account(self, account_id, status=None):
        """
        Get all loans for an account, optionally filtered by status.
        
        Args:
            account_id: The ID of the account
            status: The status to filter by
            
        Returns:
            list: A list of loans
        """
        query = Loan.query.filter_by(account_id=account_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(Loan.created_at.desc()).all()
    
    def create_loan(self, account_id, amount, term_days, repayment_strategy='FIXED'):
        """
        Create a new loan.
        
        Args:
            account_id: The ID of the account to create the loan for
            amount: The amount of the loan in seconds
            term_days: The term of the loan in days
            repayment_strategy: The repayment strategy to use (FIXED, DYNAMIC, EARLY)
            
        Returns:
            dict: A dictionary containing the result of the operation
        """
        # Get the account
        account = Account.query.get(account_id)
        
        if not account:
            return {"success": False, "message": "Account not found"}
        
        # Check if the account is eligible for a loan
        if account.status != 'ACTIVE':
            return {"success": False, "message": "Account is not active"}
        
        # Check if the account has too many active loans
        active_loans = Loan.query.filter_by(account_id=account_id, status='ACTIVE').count()
        if active_loans >= 3:
            return {"success": False, "message": "Account has too many active loans"}
        
        # Calculate interest rate based on account reputation and market conditions
        base_interest_rate = 0.05  # 5% base interest rate
        
        # Adjust based on account reputation
        reputation_adjustment = (100 - account.user.reputation_score) / 1000  # 0-10% adjustment
        
        # Adjust based on loan term
        term_adjustment = term_days / 365 * 0.02  # Longer terms have higher rates
        
        # Adjust based on loan amount
        amount_adjustment = amount / 86400 / 30 * 0.01  # Larger loans have higher rates
        
        # Calculate final interest rate
        interest_rate = base_interest_rate + reputation_adjustment + term_adjustment + amount_adjustment
        
        # Ensure interest rate is reasonable
        interest_rate = max(0.01, min(0.25, interest_rate))
        
        # Create the loan
        loan = Loan(
            account_id=account_id,
            amount=amount,
            interest_rate=interest_rate,
            term_days=term_days,
            repayment_strategy=repayment_strategy,
            status='ACTIVE',
            created_at=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=term_days)
        )
        
        # Calculate remaining amount based on the repayment strategy
        strategy = LoanStrategyFactory.create_strategy(repayment_strategy)
        loan.remaining_amount = strategy.calculate_repayment_amount(loan)
        
        try:
            # Add the loan to the database
            db.session.add(loan)
            
            # Add the loan amount to the account balance
            account.balance += amount
            account.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Schedule a notification for when the loan is due
            self.schedule_loan_due_notification(loan)
            
            return {
                "success": True,
                "message": "Loan created successfully",
                "loan_id": loan.id,
                "amount": loan.format_amount(),
                "interest_rate": f"{loan.interest_rate:.2%}",
                "term_days": loan.term_days,
                "due_date": loan.due_date.strftime('%Y-%m-%d'),
                "repayment_amount": loan.format_remaining()
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}
    
    def make_payment(self, loan_id, payment_amount):
        """
        Make a payment towards a loan.
        
        Args:
            loan_id: The ID of the loan
            payment_amount: The amount of the payment in seconds
            
        Returns:
            dict: A dictionary containing the result of the operation
        """
        # Get the loan
        loan = self.get_loan_by_id(loan_id)
        
        if not loan:
            return {"success": False, "message": "Loan not found"}
        
        # Get the account
        account = Account.query.get(loan.account_id)
        
        if not account:
            return {"success": False, "message": "Account not found"}
        
        # Check if the account has enough balance
        if account.balance < payment_amount:
            return {"success": False, "message": "Insufficient balance"}
        
        try:
            # Create the appropriate strategy
            strategy = LoanStrategyFactory.create_strategy(loan.repayment_strategy)
            
            # Apply the payment using the strategy
            strategy.apply_payment(loan, payment_amount)
            
            # Deduct the payment from the account balance
            account.balance -= payment_amount
            account.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                "success": True,
                "message": "Payment made successfully",
                "remaining_amount": loan.format_remaining(),
                "status": loan.status
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}
    
    def get_payment_schedule(self, loan_id):
        """
        Get the payment schedule for a loan.
        
        Args:
            loan_id: The ID of the loan
            
        Returns:
            dict: A dictionary containing the payment schedule
        """
        # Get the loan
        loan = self.get_loan_by_id(loan_id)
        
        if not loan:
            return {"success": False, "message": "Loan not found"}
        
        # Create the appropriate strategy
        strategy = LoanStrategyFactory.create_strategy(loan.repayment_strategy)
        
        # Calculate the payment schedule
        schedule = strategy.calculate_payment_schedule(loan)
        
        return {
            "success": True,
            "loan_id": loan.id,
            "amount": loan.format_amount(),
            "interest_rate": f"{loan.interest_rate:.2%}",
            "term_days": loan.term_days,
            "due_date": loan.due_date.strftime('%Y-%m-%d'),
            "repayment_amount": loan.format_remaining(),
            "status": loan.status,
            "schedule": schedule
        }
    
    def check_overdue_loans(self):
        """
        Check for overdue loans and update their status.
        
        Returns:
            int: The number of overdue loans
        """
        # Get all active loans that are past their due date
        overdue_loans = Loan.query.filter(
            Loan.status == 'ACTIVE',
            Loan.due_date < datetime.utcnow()
        ).all()
        
        for loan in overdue_loans:
            # Mark the loan as defaulted
            loan.status = 'DEFAULTED'
            loan.updated_at = datetime.utcnow()
            
            # Notify the user
            self.notification_service.notify_loan_due(loan)
        
        if overdue_loans:
            db.session.commit()
        
        return len(overdue_loans)
    
    def schedule_loan_due_notification(self, loan):
        """
        Schedule a notification for when a loan is due.
        
        Args:
            loan: The loan to schedule a notification for
        """
        # In a real application, you would use a task scheduler like Celery
        # For now, we'll just check if the loan is due soon
        days_until_due = (loan.due_date - datetime.utcnow()).days
        
        if days_until_due <= 7:
            # Notify the user if the loan is due within a week
            self.notification_service.notify_loan_due(loan)
    
    def adjust_market_rates(self):
        """
        Adjust market interest rates based on economic conditions.
        
        Returns:
            float: The market rate adjustment
        """
        # In a real application, this would be based on economic indicators
        # For now, we'll just use a random adjustment
        market_adjustment = random.uniform(-0.02, 0.02)  # -2% to +2%
        
        # Update all dynamic-rate loans
        dynamic_loans = Loan.query.filter_by(
            repayment_strategy='DYNAMIC',
            status='ACTIVE'
        ).all()
        
        for loan in dynamic_loans:
            # Recalculate the remaining amount with the new market rate
            strategy = LoanStrategyFactory.create_strategy(
                'DYNAMIC',
                market_rate_adjustment=market_adjustment
            )
            
            # Only adjust if the loan was recently created
            if (datetime.utcnow() - loan.created_at).days <= 7:
                new_remaining = strategy.calculate_repayment_amount(loan)
                
                # Ensure the adjustment is not too drastic
                max_adjustment = loan.remaining_amount * 0.05  # Max 5% change
                adjustment = new_remaining - loan.remaining_amount
                
                if abs(adjustment) > max_adjustment:
                    adjustment = max_adjustment if adjustment > 0 else -max_adjustment
                
                loan.remaining_amount += adjustment
                loan.updated_at = datetime.utcnow()
        
        if dynamic_loans:
            db.session.commit()
        
        return market_adjustment