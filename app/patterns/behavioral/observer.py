from app.models.user import Notification
from app import db
from datetime import datetime
from abc import ABC, abstractmethod

class Observer(ABC):
    """
    Observer interface for the Observer pattern.
    
    This interface defines methods that observers must implement.
    """
    
    @abstractmethod
    def on_low_balance(self, account):
        """
        Called when an account has a low balance.
        
        Args:
            account: The account with a low balance
        """
        pass
    
    @abstractmethod
    def on_suspicious_transaction(self, account, transaction):
        """
        Called when a suspicious transaction is detected.
        
        Args:
            account: The account with a suspicious transaction
            transaction: The suspicious transaction
        """
        pass
    
    @abstractmethod
    def on_loan_due(self, loan):
        """
        Called when a loan is due.
        
        Args:
            loan: The loan that is due
        """
        pass
    
    @abstractmethod
    def on_transaction_created(self, transaction):
        """
        Called when a transaction is created.
        
        Args:
            transaction: The created transaction
        """
        pass
    
    @abstractmethod
    def on_transaction_completed(self, transaction):
        """
        Called when a transaction is completed.
        
        Args:
            transaction: The completed transaction
        """
        pass
    
    @abstractmethod
    def on_transaction_failed(self, transaction, reason):
        """
        Called when a transaction fails.
        
        Args:
            transaction: The failed transaction
            reason: The reason for the failure
        """
        pass

class NotificationObserver(Observer):
    """
    Observer Pattern Implementation
    
    This class notifies users of important events such as low balances,
    suspicious transactions, and loan repayment deadlines.
    """
    
    def __init__(self):
        # Keep track of accounts that have already received low balance notifications
        # to prevent duplicate notifications
        self.notified_accounts = set()
    
    def on_low_balance(self, account):
        """
        Called when an account has a low balance.
        
        Args:
            account: The account with a low balance
        """
        return self.notify_low_balance(account)
    
    def on_suspicious_transaction(self, account, transaction):
        """
        Called when a suspicious transaction is detected.
        
        Args:
            account: The account with a suspicious transaction
            transaction: The suspicious transaction
        """
        return self.notify_suspicious_transaction(account, transaction)
    
    def on_loan_due(self, loan):
        """
        Called when a loan is due.
        
        Args:
            loan: The loan that is due
        """
        return self.notify_loan_due(loan)
    
    def on_transaction_created(self, transaction):
        """
        Called when a transaction is created.
        
        Args:
            transaction: The created transaction
        """
        # No notification needed for transaction creation
        return True
    
    def on_transaction_completed(self, transaction):
        """
        Called when a transaction is completed.
        
        Args:
            transaction: The completed transaction
        """
        # This method is now handled directly in the routes for more precise control
        # The notification will be triggered for withdrawals and transfers ≥300 hours
        return True
    
    def on_transaction_failed(self, transaction, reason):
        """
        Called when a transaction fails.
        
        Args:
            transaction: The failed transaction
            reason: The reason for the failure
        """
        if transaction.source_account_id:
            return self.notify_failed_transaction(transaction, reason)
        return True
    
    def notify_low_balance(self, account):
        """
        Notify a user when their account balance is low.
        
        Args:
            account: The account with a low balance
            
        Returns:
            bool: True if the notification was sent successfully, False otherwise
        """
        try:
            user = account.user
            
            # Create a notification in the database
            notification = Notification(
                user_id=user.id,
                title="Low Balance Alert",
                message=f"Your account {account.account_number} has a low balance of {account.format_balance()}.",
                is_read=False,
                created_at=datetime.utcnow()
            )
            
            db.session.add(notification)
            db.session.commit()
            
            return True
        except Exception as e:
            print(f"Error creating low balance notification: {str(e)}")
            return False
            
    def check_low_balance_threshold(self, account):
        """
        Check if an account balance is below the 3-hour threshold (10800 seconds).
        If it is, send a notification to the user.
        
        Args:
            account: The account to check
            
        Returns:
            bool: True if a notification was sent, False otherwise
        """
        # 3 hours = 10800 seconds
        LOW_BALANCE_THRESHOLD = 10800
        
        # Check if the account balance is below the threshold
        if account.balance < LOW_BALANCE_THRESHOLD:
            # Check if we've already notified this account
            account_key = f"{account.id}_{account.updated_at.strftime('%Y%m%d%H%M')}"
            
            # If we haven't notified this account in this time period, send a notification
            if account_key not in self.notified_accounts:
                self.notified_accounts.add(account_key)
                return self.notify_low_balance(account)
                
            # If we've already notified this account, don't send another notification
            return False
        else:
            # If the account balance is above the threshold, remove it from the notified accounts
            # so that if it drops below the threshold again, we'll send a new notification
            for key in list(self.notified_accounts):
                if key.startswith(f"{account.id}_"):
                    self.notified_accounts.remove(key)
        
        return False
    
    def notify_suspicious_transaction(self, account, transaction):
        """
        Notify a user of a suspicious transaction.
        
        Args:
            account: The account with a suspicious transaction
            transaction: The suspicious transaction
            
        Returns:
            bool: True if the notification was sent successfully, False otherwise
        """
        try:
            user = account.user
            
            # Create a notification in the database
            notification = Notification(
                user_id=user.id,
                title="Suspicious Transaction Alert",
                message=f"A suspicious transaction of {transaction.format_amount()} was detected on your account {account.account_number}.",
                is_read=False,
                created_at=datetime.utcnow()
            )
            
            db.session.add(notification)
            db.session.commit()
            
            return True
        except Exception as e:
            print(f"Error creating suspicious transaction notification: {str(e)}")
            return False
    
    def notify_loan_due(self, loan):
        """
        Notify a user of an upcoming loan repayment deadline.
        
        Args:
            loan: The loan with an upcoming deadline
            
        Returns:
            bool: True if the notification was sent successfully, False otherwise
        """
        try:
            account = loan.account
            user = account.user
            
            # Create a notification in the database
            notification = Notification(
                user_id=user.id,
                title="Loan Repayment Reminder",
                message=f"Your loan repayment of {loan.format_remaining()} is due on {loan.due_date.strftime('%Y-%m-%d')}.",
                is_read=False,
                created_at=datetime.utcnow()
            )
            
            db.session.add(notification)
            db.session.commit()
            
            return True
        except Exception as e:
            print(f"Error creating loan due notification: {str(e)}")
            return False
    
    def notify_large_transaction(self, transaction):
        """
        Notify a user of a large transaction.
        
        Args:
            transaction: The large transaction
            
        Returns:
            bool: True if the notification was sent successfully, False otherwise
        """
        try:
            source_account = transaction.source_account
            user = source_account.user
            
            # Create a notification in the database
            notification = Notification(
                user_id=user.id,
                title="Large Transaction Alert",
                message=f"A large transaction of {transaction.format_amount()} was processed on your account {source_account.account_number}.",
                is_read=False,
                created_at=datetime.utcnow()
            )
            
            db.session.add(notification)
            db.session.commit()
            
            return True
        except Exception as e:
            print(f"Error creating large transaction notification: {str(e)}")
            return False
    
    def notify_failed_transaction(self, transaction, reason):
        """
        Notify a user of a failed transaction.
        
        Args:
            transaction: The failed transaction
            reason: The reason for the failure
            
        Returns:
            bool: True if the notification was sent successfully, False otherwise
        """
        try:
            source_account = transaction.source_account
            user = source_account.user
            
            # Create a notification in the database
            notification = Notification(
                user_id=user.id,
                title="Transaction Failed",
                message=f"A transaction of {transaction.format_amount()} from your account {source_account.account_number} failed: {reason}",
                is_read=False,
                created_at=datetime.utcnow()
            )
            
            db.session.add(notification)
            db.session.commit()
            
            return True
        except Exception as e:
            print(f"Error creating failed transaction notification: {str(e)}")
            return False
