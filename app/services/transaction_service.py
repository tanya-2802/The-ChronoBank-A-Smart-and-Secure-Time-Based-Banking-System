from app.models.transaction import Transaction, TransactionType
from app.models.account import Account
from app.patterns.creational.singleton import TransactionLedger
from app.patterns.behavioral.command import TransferCommand, DepositCommand
from app.patterns.structural.decorator import TransactionDecorator
from app.services.notification_service import NotificationService
from app.services.fraud_detection import FraudDetectionService
from app import db
from datetime import datetime

class TransactionService:
    """
    Service for managing transactions.
    """
    
    def __init__(self):
        self.ledger = TransactionLedger()
        self.notification_service = NotificationService()
        self.fraud_service = FraudDetectionService()
    
    def get_transaction_by_id(self, transaction_id):
        """Get a transaction by ID."""
        return Transaction.query.get(transaction_id)
    
    def get_transaction_by_reference(self, reference_code):
        """Get a transaction by reference code."""
        return self.ledger.get_transaction_by_reference(reference_code)
    
    def get_transactions_by_account(self, account_id):
        """Get all transactions for an account."""
        return self.ledger.get_transactions_by_account(account_id)
    
    @TransactionDecorator.transaction_logging
    @TransactionDecorator.apply_tax(2)  # Apply a 2% tax on transfers
    def transfer(self, source_account_id, destination_account_id, amount, description, user_id=None, ip_address=None):
        """Transfer time from one account to another using the command pattern."""
        # Get the accounts
        source_account = Account.query.get(source_account_id)
        destination_account = Account.query.get(destination_account_id)
        
        if not source_account or not destination_account:
            return {"success": False, "message": "One or both accounts not found"}
        
        # Check if the source account is frozen
        if source_account.status == 'FROZEN':
            return {"success": False, "message": "Your account is frozen due to suspicious activity. Please contact customer support."}
        
        # Check for fraud before processing the transaction
        fraud_check = self.fraud_service.check_transaction(source_account_id, destination_account_id, amount)
        
        if not fraud_check.get("is_safe", True):
            # If the transaction is flagged as potentially fraudulent, return an error
            return {
                "success": False, 
                "message": "Transaction flagged as potentially fraudulent. Please check your fraud alerts.",
                "fraud_detected": True,
                "risk_score": fraud_check.get("risk_score", 0),
                "risk_factors": fraud_check.get("risk_factors", [])
            }
        
        # Create the transfer command
        command = TransferCommand(source_account, destination_account, amount, description)
        
        # Notify that a transaction is being created
        transaction = Transaction(
            transaction_type_id=1,  # Assuming 1 is the ID for Transfer
            source_account_id=source_account_id,
            destination_account_id=destination_account_id,
            amount=amount,
            status='PENDING',
            description=description,
            reference_code=Transaction.generate_reference_code()
        )
        self.notification_service.notify_transaction_created(transaction)
        
        # Execute the command
        result = command.execute()
        
        # Notify of the result
        if result.get("success", False):
            # Get the transaction from the result
            transaction_id = result.get("transaction_id")
            transaction = self.get_transaction_by_id(transaction_id)
            self.notification_service.notify_transaction_completed(transaction)
            
            # Check if the source account has a low balance after the transfer
            if source_account.balance < source_account.account_type.min_balance * 2:
                self.notification_service.notify_low_balance(source_account)
            
            # Update user reputation score for successful transaction
            source_account.user.reputation_score = min(100, source_account.user.reputation_score + 0.1)
            db.session.commit()
            
            # Include the transaction in the result
            result["transaction"] = transaction
        else:
            self.notification_service.notify_transaction_failed(transaction, result.get("message", "Unknown error"))
            
            # Decrease user reputation score for failed transaction
            source_account.user.reputation_score = max(0, source_account.user.reputation_score - 0.5)
            db.session.commit()
        
        return result
    
    @TransactionDecorator.transaction_logging
    @TransactionDecorator.apply_bonus(5)  # 5% bonus on regular deposits
    def deposit(self, account_id, amount, description, user_id=None, ip_address=None):
        """Deposit time into an account using the command pattern."""
        # Get the account
        account = Account.query.get(account_id)
        
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
        
        # Check if this is a SavingsAccount and use the special method
        if account.account_type.name == 'SavingsAccount':
            return self.deposit_to_savings(account_id, amount, description, user_id, ip_address)
        
        # Create the deposit command
        command = DepositCommand(account, amount, description)
        
        # Notify that a transaction is being created
        transaction = Transaction(
            transaction_type_id=2,  # Assuming 2 is the ID for Deposit
            source_account_id=None,
            destination_account_id=account_id,
            amount=amount,
            status='PENDING',
            description=description,
            reference_code=Transaction.generate_reference_code()
        )
        self.notification_service.notify_transaction_created(transaction)
        
        # Execute the command
        result = command.execute()
        
        # Notify of the result
        if result.get("success", False):
            # Get the transaction from the result
            transaction_id = result.get("transaction_id")
            transaction = self.get_transaction_by_id(transaction_id)
            self.notification_service.notify_transaction_completed(transaction)
            
            # Update user reputation score for successful deposit
            account.user.reputation_score = min(100, account.user.reputation_score + 0.1)
            db.session.commit()
        else:
            self.notification_service.notify_transaction_failed(transaction, result.get("message", "Unknown error"))
        
        return result
        
    @TransactionDecorator.transaction_logging
    @TransactionDecorator.apply_bonus(10)  # 10% bonus on savings account deposits
    def deposit_to_savings(self, account_id, amount, description, user_id=None, ip_address=None):
        """Deposit time into a savings account with higher bonus."""
        # Get the account
        account = Account.query.get(account_id)
        
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
        
        # Create the deposit command
        command = DepositCommand(account, amount, description + " (Savings Account)")
        
        # Notify that a transaction is being created
        transaction = Transaction(
            transaction_type_id=2,  # Assuming 2 is the ID for Deposit
            source_account_id=None,
            destination_account_id=account_id,
            amount=amount,
            status='PENDING',
            description=description + " (Savings Account)",
            reference_code=Transaction.generate_reference_code()
        )
        self.notification_service.notify_transaction_created(transaction)
        
        # Execute the command
        result = command.execute()
        
        # Notify of the result
        if result.get("success", False):
            # Get the transaction from the result
            transaction_id = result.get("transaction_id")
            transaction = self.get_transaction_by_id(transaction_id)
            self.notification_service.notify_transaction_completed(transaction)
            
            # Update user reputation score for successful deposit
            account.user.reputation_score = min(100, account.user.reputation_score + 0.1)
            db.session.commit()
        else:
            self.notification_service.notify_transaction_failed(transaction, result.get("message", "Unknown error"))
        
        return result
    
    def undo_transaction(self, transaction_id):
        """Undo a transaction."""
        transaction = self.get_transaction_by_id(transaction_id)
        
        if not transaction:
            return {"success": False, "message": "Transaction not found"}
        
        try:
            # Reverse the transaction
            transaction.reverse()
            
            # Notify that the transaction was reversed
            self.notification_service.notify_transaction_completed(transaction)
            
            return {
                "success": True, 
                "message": "Transaction reversed successfully",
                "transaction_id": transaction.id,
                "reference_code": transaction.reference_code
            }
            
        except Exception as e:
            db.session.rollback()
            self.notification_service.notify_transaction_failed(transaction, str(e))
            return {"success": False, "message": str(e)}
    
    def get_transaction_types(self):
        """Get all transaction types."""
        return TransactionType.query.all()
