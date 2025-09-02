from app.models.transaction import Transaction, AuditLog
from app import db
from datetime import datetime

class TransactionLedger:
    """
    Singleton Pattern Implementation
    
    This class ensures a single central ledger that records all time transactions securely.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TransactionLedger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._transaction_count = 0
    
    def record_transaction(self, transaction_type_id, source_account_id, destination_account_id, 
                          amount, description, user_id=None, ip_address=None):
        """
        Record a new transaction in the ledger.
        
        Args:
            transaction_type_id (int): The ID of the transaction type
            source_account_id (int): The ID of the source account (can be None for deposits)
            destination_account_id (int): The ID of the destination account (can be None for withdrawals)
            amount (int): The amount of time in seconds
            description (str): A description of the transaction
            user_id (int, optional): The ID of the user who initiated the transaction
            ip_address (str, optional): The IP address of the user who initiated the transaction
            
        Returns:
            Transaction: The newly created transaction
        """
        # Create a new transaction
        transaction = Transaction(
            transaction_type_id=transaction_type_id,
            source_account_id=source_account_id,
            destination_account_id=destination_account_id,
            amount=amount,
            status='PENDING',
            description=description,
            reference_code=Transaction.generate_reference_code()
        )
        
        # Add to database
        db.session.add(transaction)
        
        # Create an audit log entry
        audit_log = AuditLog(
            user_id=user_id,
            action='CREATE_TRANSACTION',
            entity_type='Transaction',
            entity_id=None,  # Will be updated after commit
            details=f"Created transaction of {amount} seconds",
            ip_address=ip_address,
            created_at=datetime.utcnow()
        )
        
        db.session.add(audit_log)
        db.session.flush()  # Flush to get the transaction ID
        
        # Update the audit log with the transaction ID
        audit_log.entity_id = transaction.id
        
        # Commit the changes
        db.session.commit()
        
        # Increment the transaction count
        self._transaction_count += 1
        
        return transaction
    
    def get_transaction_count(self):
        """Get the total number of transactions recorded."""
        return self._transaction_count
    
    def get_transaction_by_reference(self, reference_code):
        """Get a transaction by its reference code."""
        return Transaction.query.filter_by(reference_code=reference_code).first()
    
    def get_transactions_by_account(self, account_id):
        """Get all transactions for a specific account."""
        return Transaction.query.filter(
            (Transaction.source_account_id == account_id) | 
            (Transaction.destination_account_id == account_id)
        ).order_by(Transaction.created_at.desc()).all()
