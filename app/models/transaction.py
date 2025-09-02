from app import db
from datetime import datetime
import uuid

class TransactionType(db.Model):
    __tablename__ = 'transaction_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='transaction_type', lazy=True)
    
    def __repr__(self):
        return f"<TransactionType {self.name}>"

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_type_id = db.Column(db.Integer, db.ForeignKey('transaction_types.id'), nullable=False)
    source_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    destination_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    amount = db.Column(db.Integer, nullable=False)  # Time in seconds
    status = db.Column(db.String(20), default='PENDING', nullable=False)  # PENDING, COMPLETED, FAILED, REVERSED
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    description = db.Column(db.Text)
    reference_code = db.Column(db.String(50), unique=True, nullable=False)
    
    # Relationships
    fraud_alerts = db.relationship('FraudAlert', backref='transaction', lazy=True)
    
    @staticmethod
    def generate_reference_code():
        """Generate a unique reference code for the transaction."""
        return f"TRX-{uuid.uuid4().hex[:12].upper()}"
    
    def format_amount(self):
        """Format the transaction amount in hours only."""
        # Convert seconds to hours (including decimal)
        hours = self.amount / 3600
        
        # Format with 2 decimal places
        return f"{hours:.2f} hour{'s' if hours != 1 else ''}"
    
    def reverse(self):
        """Reverse a completed transaction."""
        if self.status != 'COMPLETED':
            raise ValueError("Only completed transactions can be reversed")
        
        # Reverse the transaction
        if self.source_account_id and self.destination_account_id:
            # For transfers, return money to source from destination
            source_account = self.source_account
            destination_account = self.destination_account
            
            destination_account.withdraw(self.amount)
            source_account.deposit(self.amount)
        elif self.destination_account_id:
            # For deposits, remove from destination
            destination_account = self.destination_account
            destination_account.withdraw(self.amount)
        elif self.source_account_id:
            # For withdrawals, return to source
            source_account = self.source_account
            source_account.deposit(self.amount)
        
        self.status = 'REVERSED'
        self.updated_at = datetime.utcnow()
        
        return True
    
    def __repr__(self):
        return f"<Transaction {self.reference_code} Amount: {self.format_amount()} Status: {self.status}>"

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<AuditLog {self.id} Action: {self.action}>"
