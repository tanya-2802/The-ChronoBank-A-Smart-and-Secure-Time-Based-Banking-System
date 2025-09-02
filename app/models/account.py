from app import db
from datetime import datetime
import uuid

class AccountType(db.Model):
    __tablename__ = 'account_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    min_balance = db.Column(db.Integer, default=0)  # Minimum time balance in seconds
    interest_rate = db.Column(db.Float, default=0.0)
    transaction_limit = db.Column(db.Integer, default=1000)  # Maximum transaction amount
    
    # Relationships
    accounts = db.relationship('Account', backref='account_type', lazy=True)
    
    def __repr__(self):
        return f"<AccountType {self.name}>"

class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_type_id = db.Column(db.Integer, db.ForeignKey('account_types.id'), nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    balance = db.Column(db.Integer, default=0, nullable=False)  # Time in seconds
    status = db.Column(db.String(20), default='ACTIVE', nullable=False)  # ACTIVE, OVERDRAWN, FROZEN
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    outgoing_transactions = db.relationship('Transaction', foreign_keys='Transaction.source_account_id', backref='source_account', lazy=True)
    incoming_transactions = db.relationship('Transaction', foreign_keys='Transaction.destination_account_id', backref='destination_account', lazy=True)
    loans = db.relationship('Loan', backref='account', lazy=True)
    investments = db.relationship('Investment', backref='account', lazy=True)
    fraud_alerts = db.relationship('FraudAlert', backref='account', lazy=True)
    
    @staticmethod
    def generate_account_number():
        """Generate a unique account number."""
        return f"CB-{uuid.uuid4().hex[:12].upper()}"
    
    def deposit(self, amount):
        """Add time to the account."""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        
        self.balance += amount
        self.updated_at = datetime.utcnow()
        return True
    
    def withdraw(self, amount):
        """Remove time from the account if sufficient balance exists."""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        
        if self.balance < amount:
            raise ValueError("Insufficient balance")
        
        self.balance -= amount
        self.updated_at = datetime.utcnow()
        
        # Update account status if necessary
        if self.balance < self.account_type.min_balance:
            self.status = 'OVERDRAWN'
        
        return True
    
    def transfer(self, destination_account, amount):
        """Transfer time from this account to another account."""
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        
        if self.balance < amount:
            raise ValueError("Insufficient balance")
        
        # Withdraw from source account
        self.withdraw(amount)
        
        # Deposit to destination account
        destination_account.deposit(amount)
        
        return True
    
    def freeze(self):
        """Freeze the account due to suspicious activity."""
        self.status = 'FROZEN'
        self.updated_at = datetime.utcnow()
        return True
    
    def unfreeze(self):
        """Unfreeze a previously frozen account."""
        if self.balance < self.account_type.min_balance:
            self.status = 'OVERDRAWN'
        else:
            self.status = 'ACTIVE'
        
        self.updated_at = datetime.utcnow()
        return True
    
    def format_balance(self):
        """Format the balance in hours only."""
        # Convert seconds to hours (including decimal)
        hours = self.balance / 3600
        
        # Format with 2 decimal places
        return f"{hours:.2f} hour{'s' if hours != 1 else ''}"
    
    def __repr__(self):
        return f"<Account {self.account_number} Balance: {self.format_balance()}>"

class FraudAlert(db.Model):
    __tablename__ = 'fraud_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True)
    risk_score = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='OPEN', nullable=False)  # OPEN, RESOLVED, FALSE_POSITIVE
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f"<FraudAlert {self.id} for Account {self.account_id}>"
