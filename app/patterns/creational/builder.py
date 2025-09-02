from app.models.account import Account, AccountType
from app import db

class AccountBuilder:
    """
    Builder Pattern Implementation
    
    This class allows users to customize their account preferences step by step.
    """
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.account_type_id = None
        self.initial_balance = 0
        self.transaction_limit = None
        self.interest_rate = None
        
    def with_account_type(self, account_type_name):
        """Set the account type."""
        account_type = AccountType.query.filter_by(name=account_type_name).first()
        
        if not account_type:
            raise ValueError(f"Account type '{account_type_name}' not found")
        
        self.account_type_id = account_type.id
        return self
    
    def with_initial_balance(self, balance):
        """Set the initial balance."""
        if balance < 0:
            raise ValueError("Initial balance cannot be negative")
        
        self.initial_balance = balance
        return self
    
    def with_transaction_limit(self, limit):
        """Set a custom transaction limit."""
        if limit <= 0:
            raise ValueError("Transaction limit must be positive")
        
        self.transaction_limit = limit
        return self
    
    def with_interest_rate(self, rate):
        """Set a custom interest rate."""
        if rate < 0:
            raise ValueError("Interest rate cannot be negative")
        
        self.interest_rate = rate
        return self
    
    def build(self):
        """Build and return the customized account."""
        if not self.account_type_id:
            raise ValueError("Account type must be specified")
        
        # Create the account
        account = Account(
            user_id=self.user_id,
            account_type_id=self.account_type_id,
            account_number=Account.generate_account_number(),
            balance=self.initial_balance,
            status='ACTIVE'
        )
        
        # Add to database
        db.session.add(account)
        
        # Update account type if custom settings were provided
        if self.transaction_limit is not None or self.interest_rate is not None:
            account_type = AccountType.query.get(self.account_type_id)
            
            if self.transaction_limit is not None:
                account_type.transaction_limit = self.transaction_limit
            
            if self.interest_rate is not None:
                account_type.interest_rate = self.interest_rate
        
        db.session.commit()
        
        return account
