from app.models.user import Notification, User
from app.patterns.behavioral.observer import NotificationObserver
from app.patterns.behavioral.subject import AccountSubject, TransactionSubject
from app import db
from datetime import datetime

class NotificationService:
    """
    Service for managing notifications.
    """
    
    def __init__(self):
        self.observer = NotificationObserver()
        self.account_subject = AccountSubject()
        self.transaction_subject = TransactionSubject()
        
        # Register the observer with the subjects
        self.account_subject.attach(self.observer)
        self.transaction_subject.attach(self.observer)
    
    def get_notifications_by_user(self, user_id, is_read=None):
        """
        Get notifications for a user, optionally filtered by read status.
        
        Args:
            user_id: The ID of the user
            is_read: Whether the notifications are read or not
            
        Returns:
            list: A list of notifications
        """
        query = Notification.query.filter_by(user_id=user_id)
        
        if is_read is not None:
            query = query.filter_by(is_read=is_read)
        
        return query.order_by(Notification.created_at.desc()).all()
    
    def mark_notification_as_read(self, notification_id):
        """
        Mark a notification as read.
        
        Args:
            notification_id: The ID of the notification
            
        Returns:
            dict: A dictionary containing the result of the operation
        """
        notification = Notification.query.get(notification_id)
        
        if not notification:
            return {"success": False, "message": "Notification not found"}
        
        notification.is_read = True
        db.session.commit()
        
        return {"success": True, "message": "Notification marked as read"}
    
    def mark_all_notifications_as_read(self, user_id):
        """
        Mark all notifications for a user as read.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            dict: A dictionary containing the result of the operation
        """
        notifications = Notification.query.filter_by(user_id=user_id, is_read=False).all()
        
        for notification in notifications:
            notification.is_read = True
        
        db.session.commit()
        
        return {"success": True, "message": f"{len(notifications)} notifications marked as read"}
    
    def create_notification(self, user_id, title, message):
        """
        Create a new notification.
        
        Args:
            user_id: The ID of the user
            title: The title of the notification
            message: The message of the notification
            
        Returns:
            Notification: The newly created notification
        """
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            is_read=False,
            created_at=datetime.utcnow()
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification
    
    def notify_low_balance(self, account):
        """
        Notify observers of a low balance.
        
        Args:
            account: The account with a low balance
            
        Returns:
            bool: True if the notification was processed successfully, False otherwise
        """
        try:
            self.account_subject.notify('low_balance', account)
            return True
        except Exception as e:
            print(f"Error notifying of low balance: {str(e)}")
            return False
            
    def check_balance_threshold(self, account):
        """
        Check if an account balance is below the 30-minute threshold and notify if needed.
        This applies to all account types (basic, investor, loan).
        
        Args:
            account: The account to check
            
        Returns:
            bool: True if the notification was processed successfully, False otherwise
        """
        try:
            # Use the observer to check the balance threshold
            # The observer will handle duplicate notification prevention
            result = self.observer.check_low_balance_threshold(account)
            return result
        except Exception as e:
            print(f"Error checking balance threshold: {str(e)}")
            return False
    
    def notify_suspicious_transaction(self, account, transaction):
        """
        Notify observers of a suspicious transaction.
        
        Args:
            account: The account with a suspicious transaction
            transaction: The suspicious transaction
            
        Returns:
            bool: True if the notification was processed successfully, False otherwise
        """
        try:
            self.account_subject.notify('suspicious_transaction', account, transaction)
            return True
        except Exception as e:
            print(f"Error notifying of suspicious transaction: {str(e)}")
            return False
    
    def notify_loan_due(self, loan):
        """
        Notify observers of an upcoming loan repayment deadline.
        
        Args:
            loan: The loan with an upcoming deadline
            
        Returns:
            bool: True if the notification was processed successfully, False otherwise
        """
        try:
            self.account_subject.notify('loan_due', loan)
            return True
        except Exception as e:
            print(f"Error notifying of loan due: {str(e)}")
            return False
    
    def notify_transaction_created(self, transaction):
        """
        Notify observers of a created transaction.
        
        Args:
            transaction: The created transaction
            
        Returns:
            bool: True if the notification was processed successfully, False otherwise
        """
        try:
            self.transaction_subject.notify('transaction_created', transaction)
            return True
        except Exception as e:
            print(f"Error notifying of transaction created: {str(e)}")
            return False
    
    def notify_transaction_completed(self, transaction):
        """
        Notify observers of a completed transaction.
        
        Args:
            transaction: The completed transaction
            
        Returns:
            bool: True if the notification was processed successfully, False otherwise
        """
        try:
            self.transaction_subject.notify('transaction_completed', transaction)
            return True
        except Exception as e:
            print(f"Error notifying of transaction completed: {str(e)}")
            return False
    
    def notify_transaction_failed(self, transaction, reason):
        """
        Notify observers of a failed transaction.
        
        Args:
            transaction: The failed transaction
            reason: The reason for the failure
            
        Returns:
            bool: True if the notification was processed successfully, False otherwise
        """
        try:
            self.transaction_subject.notify('transaction_failed', transaction, reason)
            return True
        except Exception as e:
            print(f"Error notifying of transaction failed: {str(e)}")
            return False
