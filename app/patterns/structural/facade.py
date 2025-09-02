from app.models.account import Account
from app.models.transaction import Transaction, TransactionType
from app.models.loan import Loan, Investment
from app.patterns.creational.singleton import TransactionLedger
from app.services.fraud_detection import FraudDetectionService
from app import db
from datetime import datetime

class BankingFacade:
    """
    Facade Pattern Implementation
    
    This class provides a simplified interface for banking operations,
    hiding the complex interactions between different components.
    """
    
    def __init__(self):
        self.ledger = TransactionLedger()
        self.fraud_service = FraudDetectionService()
    
    def transfer_time(self, source_account_id, destination_account_id, amount, description, user_id=None, ip_address=None):
        """
        Transfer time from one account to another.
        
        Args:
            source_account_id (int): The ID of the source account
            destination_account_id (int): The ID of the destination account
            amount (int): The amount of time in seconds
            description (str): A description of the transfer
            user_id (int, optional): The ID of the user who initiated the transfer
            ip_address (str, optional): The IP address of the user who initiated the transfer
            
        Returns:
            dict: A dictionary containing the status and details of the transfer
        """
        try:
            # Get the accounts
            source_account = Account.query.get(source_account_id)
            destination_account = Account.query.get(destination_account_id)
            
            if not source_account or not destination_account:
                return {"success": False, "message": "One or both accounts not found"}
            
            # Check account status
            if source_account.status != 'ACTIVE':
                return {"success": False, "message": f"Source account is {source_account.status.lower()}"}
            
            if destination_account.status != 'ACTIVE':
                return {"success": False, "message": f"Destination account is {destination_account.status.lower()}"}
            
            # Check for sufficient balance
            if source_account.balance < amount:
                return {"success": False, "message": "Insufficient balance"}
            
            # Check for transaction limits
            if amount > source_account.account_type.transaction_limit:
                return {"success": False, "message": "Transaction exceeds limit"}
            
            # Check for fraud
            fraud_check = self.fraud_service.check_transaction(source_account_id, destination_account_id, amount)
            if not fraud_check["is_safe"]:
                return {"success": False, "message": f"Fraud detected: {fraud_check['reason']}"}
            
            # Get the transfer transaction type
            transfer_type = TransactionType.query.filter_by(name='Transfer').first()
            
            # Record the transaction
            transaction = self.ledger.record_transaction(
                transaction_type_id=transfer_type.id,
                source_account_id=source_account_id,
                destination_account_id=destination_account_id,
                amount=amount,
                description=description,
                user_id=user_id,
                ip_address=ip_address
            )
            
            # Perform the transfer
            source_account.transfer(destination_account, amount)
            
            # Update transaction status
            transaction.status = 'COMPLETED'
            transaction.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                "success": True, 
                "message": "Transfer completed successfully",
                "transaction_id": transaction.id,
                "reference_code": transaction.reference_code
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}
    
    def create_loan(self, account_id, amount, term_days, repayment_strategy='FIXED', user_id=None, ip_address=None):
        """
        Create a new loan for an account.
        
        Args:
            account_id (int): The ID of the account
            amount (int): The amount of time in seconds
            term_days (int): The term of the loan in days
            repayment_strategy (str): The repayment strategy ('FIXED' or 'DYNAMIC')
            user_id (int, optional): The ID of the user who initiated the loan
            ip_address (str, optional): The IP address of the user who initiated the loan
            
        Returns:
            dict: A dictionary containing the status and details of the loan
        """
        try:
            # Get the account
            account = Account.query.get(account_id)
            
            if not account:
                return {"success": False, "message": "Account not found"}
            
            # Check account status
            if account.status != 'ACTIVE':
                return {"success": False, "message": f"Account is {account.status.lower()}"}
            
            # Get the loan transaction type
            loan_type = TransactionType.query.filter_by(name='Loan').first()
            
            # Record the transaction
            transaction = self.ledger.record_transaction(
                transaction_type_id=loan_type.id,
                source_account_id=None,
                destination_account_id=account_id,
                amount=amount,
                description=f"Loan for {term_days} days",
                user_id=user_id,
                ip_address=ip_address
            )
            
            # Get the interest rate from the account type
            interest_rate = account.account_type.interest_rate
            
            # Create the loan
            loan = Loan(
                account_id=account_id,
                amount=amount,
                interest_rate=interest_rate,
                term_days=term_days,
                repayment_strategy=repayment_strategy
            )
            
            # Add to database
            db.session.add(loan)
            
            # Add the loan amount to the account
            account.deposit(amount)
            
            # Update transaction status
            transaction.status = 'COMPLETED'
            transaction.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                "success": True, 
                "message": "Loan created successfully",
                "loan_id": loan.id,
                "transaction_id": transaction.id,
                "reference_code": transaction.reference_code
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}
    
    def create_investment(self, account_id, amount, term_days, user_id=None, ip_address=None):
        """
        Create a new investment for an account.
        
        Args:
            account_id (int): The ID of the account
            amount (int): The amount of time in seconds
            term_days (int): The term of the investment in days
            user_id (int, optional): The ID of the user who initiated the investment
            ip_address (str, optional): The IP address of the user who initiated the investment
            
        Returns:
            dict: A dictionary containing the status and details of the investment
        """
        try:
            # Get the account
            account = Account.query.get(account_id)
            
            if not account:
                return {"success": False, "message": "Account not found"}
            
            # Check account status
            if account.status != 'ACTIVE':
                return {"success": False, "message": f"Account is {account.status.lower()}"}
            
            # Check for sufficient balance
            if account.balance < amount:
                return {"success": False, "message": "Insufficient balance"}
            
            # Get the investment transaction type
            investment_type = TransactionType.query.filter_by(name='Investment').first()
            
            # Record the transaction
            transaction = self.ledger.record_transaction(
                transaction_type_id=investment_type.id,
                source_account_id=account_id,
                destination_account_id=None,
                amount=amount,
                description=f"Investment for {term_days} days",
                user_id=user_id,
                ip_address=ip_address
            )
            
            # Get the interest rate from the account type (higher for investments)
            interest_rate = account.account_type.interest_rate * 1.5  # 50% higher than loan rate
            
            # Create the investment
            investment = Investment(
                account_id=account_id,
                amount=amount,
                interest_rate=interest_rate,
                term_days=term_days
            )
            
            # Add to database
            db.session.add(investment)
            
            # Remove the investment amount from the account
            account.withdraw(amount)
            
            # Update transaction status
            transaction.status = 'COMPLETED'
            transaction.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                "success": True, 
                "message": "Investment created successfully",
                "investment_id": investment.id,
                "transaction_id": transaction.id,
                "reference_code": transaction.reference_code
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}
