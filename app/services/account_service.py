from app.models.account import Account, AccountType
from app.models.user import User
from app.patterns.creational.factory import AccountFactory
from app.patterns.creational.builder import AccountBuilder
from app.patterns.behavioral.state import get_account_state
from app.services.notification_service import NotificationService
from app.services.fraud_detection import FraudDetectionService
from app import db
from datetime import datetime

class AccountService:
    """
    Service for managing accounts.
    """
    
    def __init__(self):
        self.notification_service = NotificationService()
        self.fraud_service = FraudDetectionService()
    
    def get_account_by_id(self, account_id):
        """Get an account by ID."""
        return Account.query.get(account_id)
    
    def get_account_by_number(self, account_number):
        """Get an account by account number."""
        return Account.query.filter_by(account_number=account_number).first()
    
    def get_accounts_by_user(self, user_id):
        """Get all accounts for a user."""
        return Account.query.filter_by(user_id=user_id).all()
    
    def create_account(self, user_id, account_type_name):
        """Create a new account using the factory pattern."""
        return AccountFactory.create_account(user_id, account_type_name)
    
    def create_custom_account(self, user_id, account_type_name, initial_balance=0, transaction_limit=None, interest_rate=None):
        """Create a custom account using the builder pattern."""
        builder = AccountBuilder(user_id)
        
        builder.with_account_type(account_type_name)
        
        if initial_balance > 0:
            builder.with_initial_balance(initial_balance)
        
        if transaction_limit is not None:
            builder.with_transaction_limit(transaction_limit)
        
        if interest_rate is not None:
            builder.with_interest_rate(interest_rate)
        
        return builder.build()
    
    def deposit(self, account_id, amount):
        """Deposit time into an account."""
        account = self.get_account_by_id(account_id)
        
        if not account:
            return {"success": False, "message": "Account not found"}
        
        # Check if the account is frozen
        if account.status == 'FROZEN':
            return {"success": False, "message": "Your account is frozen due to suspicious activity. Please contact customer support."}
        
        # Check for fraud before processing the deposit
        fraud_check = self.fraud_service.check_transaction(None, account_id, amount)
        
        if not fraud_check.get("is_safe", True):
            # If the transaction is flagged as potentially fraudulent, return an error
            return {
                "success": False, 
                "message": "Deposit flagged as potentially fraudulent. Please check your fraud alerts.",
                "fraud_detected": True,
                "risk_score": fraud_check.get("risk_score", 0),
                "risk_factors": fraud_check.get("risk_factors", [])
            }
        
        # Get the account state
        state = get_account_state(account.status)
        
        # Perform the deposit
        if state.deposit(account, amount):
            return {"success": True, "message": "Deposit successful"}
        else:
            return {"success": False, "message": "Deposit failed"}
    
    def withdraw(self, account_id, amount):
        """Withdraw time from an account."""
        account = self.get_account_by_id(account_id)
        
        if not account:
            return {"success": False, "message": "Account not found"}
        
        # Check if the account is frozen
        if account.status == 'FROZEN':
            return {"success": False, "message": "Your account is frozen due to suspicious activity. Please contact customer support."}
        
        # Check for fraud before processing the withdrawal
        fraud_check = self.fraud_service.check_transaction(account_id, None, amount)
        
        if not fraud_check.get("is_safe", True):
            # If the transaction is flagged as potentially fraudulent, return an error
            return {
                "success": False, 
                "message": "Withdrawal flagged as potentially fraudulent. Please check your fraud alerts.",
                "fraud_detected": True,
                "risk_score": fraud_check.get("risk_score", 0),
                "risk_factors": fraud_check.get("risk_factors", [])
            }
        
        # Get the account state
        state = get_account_state(account.status)
        
        # Perform the withdrawal
        if state.withdraw(account, amount):
            return {"success": True, "message": "Withdrawal successful"}
        else:
            return {"success": False, "message": "Withdrawal failed"}
    
    def transfer(self, source_account_id, destination_account_id, amount):
        """Transfer time from one account to another."""
        source_account = self.get_account_by_id(source_account_id)
        destination_account = self.get_account_by_id(destination_account_id)
        
        if not source_account or not destination_account:
            return {"success": False, "message": "One or both accounts not found"}
        
        # Get the source account state
        state = get_account_state(source_account.status)
        
        # Perform the transfer
        if state.transfer(source_account, destination_account, amount):
            return {"success": True, "message": "Transfer successful"}
        else:
            return {"success": False, "message": "Transfer failed"}
    
    def freeze_account(self, account_id):
        """Freeze an account."""
        account = self.get_account_by_id(account_id)
        
        if not account:
            return {"success": False, "message": "Account not found"}
        
        account.status = 'FROZEN'
        account.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {"success": True, "message": "Account frozen"}
    
    def unfreeze_account(self, account_id):
        """Unfreeze an account."""
        account = self.get_account_by_id(account_id)
        
        if not account:
            return {"success": False, "message": "Account not found"}
        
        if account.balance < account.account_type.min_balance:
            account.status = 'OVERDRAWN'
        else:
            account.status = 'ACTIVE'
        
        account.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {"success": True, "message": "Account unfrozen"}
    
    def get_account_types(self):
        """Get all account types."""
        return AccountType.query.all()
