from abc import ABC, abstractmethod
from app.models.transaction import Transaction
from app import db
from datetime import datetime

class TransactionCommand(ABC):
    """
    Command Pattern Implementation
    
    This abstract class defines the interface for transaction commands.
    """
    
    @abstractmethod
    def execute(self):
        """
        Execute the command.
        
        Returns:
            dict: A dictionary containing the result of the command
        """
        pass
    
    @abstractmethod
    def undo(self):
        """
        Undo the command.
        
        Returns:
            dict: A dictionary containing the result of the undo operation
        """
        pass

class TransferCommand(TransactionCommand):
    """
    Transfer command implementation.
    
    This command transfers time from one account to another.
    """
    
    def __init__(self, source_account, destination_account, amount, description):
        self.source_account = source_account
        self.destination_account = destination_account
        self.amount = amount
        self.description = description
        self.transaction = None
    
    def execute(self):
        """
        Execute the transfer command.
        
        Returns:
            dict: A dictionary containing the result of the transfer
        """
        try:
            # Check account status
            if self.source_account.status != 'ACTIVE':
                return {"success": False, "message": f"Source account is {self.source_account.status.lower()}"}
            
            if self.destination_account.status != 'ACTIVE':
                return {"success": False, "message": f"Destination account is {self.destination_account.status.lower()}"}
            
            # Check for sufficient balance
            if self.source_account.balance < self.amount:
                return {"success": False, "message": "Insufficient balance"}
            
            # Get the transfer transaction type
            from app.models.transaction import TransactionType
            transfer_type = TransactionType.query.filter_by(name='Transfer').first()
            
            # Create a new transaction
            self.transaction = Transaction(
                transaction_type_id=transfer_type.id,
                source_account_id=self.source_account.id,
                destination_account_id=self.destination_account.id,
                amount=self.amount,
                status='PENDING',
                description=self.description,
                reference_code=Transaction.generate_reference_code()
            )
            
            # Add to database
            db.session.add(self.transaction)
            
            # Perform the transfer
            self.source_account.transfer(self.destination_account, self.amount)
            
            # Update transaction status
            self.transaction.status = 'COMPLETED'
            self.transaction.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                "success": True, 
                "message": "Transfer completed successfully",
                "transaction_id": self.transaction.id,
                "reference_code": self.transaction.reference_code
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}
    
    def undo(self):
        """
        Undo the transfer command.
        
        Returns:
            dict: A dictionary containing the result of the undo operation
        """
        try:
            if not self.transaction:
                return {"success": False, "message": "No transaction to undo"}
            
            if self.transaction.status != 'COMPLETED':
                return {"success": False, "message": f"Cannot undo a {self.transaction.status.lower()} transaction"}
            
            # Reverse the transaction
            self.transaction.reverse()
            
            return {
                "success": True, 
                "message": "Transfer reversed successfully",
                "transaction_id": self.transaction.id,
                "reference_code": self.transaction.reference_code
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}

class DepositCommand(TransactionCommand):
    """
    Deposit command implementation.
    
    This command adds time to an account.
    """
    
    def __init__(self, account, amount, description):
        self.account = account
        self.amount = amount
        self.description = description
        self.transaction = None
    
    def execute(self):
        """
        Execute the deposit command.
        
        Returns:
            dict: A dictionary containing the result of the deposit
        """
        try:
            # Check account status
            if self.account.status != 'ACTIVE' and self.account.status != 'OVERDRAWN':
                return {"success": False, "message": f"Account is {self.account.status.lower()}"}
            
            # Get the deposit transaction type
            from app.models.transaction import TransactionType
            deposit_type = TransactionType.query.filter_by(name='Deposit').first()
            
            # Create a new transaction
            self.transaction = Transaction(
                transaction_type_id=deposit_type.id,
                source_account_id=None,
                destination_account_id=self.account.id,
                amount=self.amount,
                status='PENDING',
                description=self.description,
                reference_code=Transaction.generate_reference_code()
            )
            
            # Add to database
            db.session.add(self.transaction)
            
            # Perform the deposit
            self.account.deposit(self.amount)
            
            # Update account status if necessary
            if self.account.status == 'OVERDRAWN' and self.account.balance >= self.account.account_type.min_balance:
                self.account.status = 'ACTIVE'
            
            # Update transaction status
            self.transaction.status = 'COMPLETED'
            self.transaction.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                "success": True, 
                "message": "Deposit completed successfully",
                "transaction_id": self.transaction.id,
                "reference_code": self.transaction.reference_code
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}
    
    def undo(self):
        """
        Undo the deposit command.
        
        Returns:
            dict: A dictionary containing the result of the undo operation
        """
        try:
            if not self.transaction:
                return {"success": False, "message": "No transaction to undo"}
            
            if self.transaction.status != 'COMPLETED':
                return {"success": False, "message": f"Cannot undo a {self.transaction.status.lower()} transaction"}
            
            # Check if the account has sufficient balance
            if self.account.balance < self.amount:
                return {"success": False, "message": "Insufficient balance to undo deposit"}
            
            # Reverse the transaction
            self.transaction.reverse()
            
            return {
                "success": True, 
                "message": "Deposit reversed successfully",
                "transaction_id": self.transaction.id,
                "reference_code": self.transaction.reference_code
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}
