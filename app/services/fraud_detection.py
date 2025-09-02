from app.models.account import Account, FraudAlert
from app.models.transaction import Transaction
from app.config import Config
from app import db
from datetime import datetime, timedelta

class FraudDetectionService:
    """
    Service for detecting fraudulent transactions.
    """
    
    def __init__(self):
        self.config = Config()
        # Import here to avoid circular imports
        from app.services.notification_service import NotificationService
        self.notification_service = NotificationService()
    
    def check_transaction(self, source_account_id, destination_account_id, amount):
        """
        Check if a transaction is potentially fraudulent.
        
        Args:
            source_account_id: The ID of the source account
            destination_account_id: The ID of the destination account
            amount: The amount of the transaction
            
        Returns:
            dict: A dictionary containing the fraud check result
        """
        # Get the accounts
        source_account = Account.query.get(source_account_id) if source_account_id else None
        destination_account = Account.query.get(destination_account_id) if destination_account_id else None
        
        # Initialize risk score
        risk_score = 0.0
        risk_factors = []
        
        # Check for unusually large transactions - more aggressive detection - more aggressive detection
        if amount > self.config.MAX_TRANSACTION_AMOUNT:
            risk_score += 0.4  # Increased from 0.5  # Increased from 0.5  # Increased from 0.4
            risk_factors.append("Unusually large transaction")
        
        # Check for source account issues
        if source_account:
            # Check for rapid depletion of balance - more aggressive detection - more sensitive detection
            if amount > source_account.balance * 0.5:  # Reduced from 0.8 to 0.5
                risk_score += 0.4  # Increased from 0.5  # Reduced from 0.8 to 0.5
                risk_factors.append("Rapid depletion of balance")  # more aggressive detection
            
            # Check for unusual transaction patterns - more sensitive detection
            recent_transactions = Transaction.query.filter_by(
                source_account_id=source_account_id  # Reduced from 5 to 2
            ).filter(
                Transaction.created_at > datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            if recent_transactions > 2:  # Reduced from 5 to 2
                risk_score += 0.3  # Increased from 0.3  # Increased from 0.3  # Increased from 0.2
                risk_factors.append("Unusual transaction frequency")  # Increased from 70 to 90
            
            # Check user reputation - more sensitive detection - more sensitive detection
            if source_account.user.reputation_score < 90:  # Increased from 70 to 90
                risk_score += 0.3  # Increased from 0.2
                risk_factors.append("Low user reputation")
        
        # Check for destination account issues - more sensitive detection
        if destination_account:
            # Check for unusual deposits
            recent_deposits = Transaction.query.filter_by(
                destination_account_id=destination_account_id
            ).filter(
                Transaction.created_at > datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            if recent_deposits > 2:  # Reduced from 5 to 2
                risk_score += 0.2  # Increased from 0.3  # Increased from 0.3  # Increased from 0.2
                risk_factors.append("Unusual deposit frequency")
            
            # Check user reputation
            if destination_account.user.reputation_score < 90:  # Increased from 70 to 90
                risk_score += 0.2  # Increased from 0.1
                risk_factors.append("Destination has low reputation")
                
        # Add a baseline risk to ensure fraud detection is triggered more easily
        risk_score += 0.1
        risk_factors.append("Enhanced security check")
        
        # Determine if the transaction is safe
        is_safe = risk_score < self.config.FRAUD_RISK_THRESHOLD
        
        # If not safe, create a fraud alert and notify the user
        if not is_safe and source_account:
            alert = FraudAlert(
                account_id=source_account_id,
                risk_score=risk_score,
                description=", ".join(risk_factors),
                status='OPEN',
                created_at=datetime.utcnow()
            )
            
            db.session.add(alert)
            db.session.commit()
            
            # Create a transaction record for the fraud alert
            transaction = Transaction(
                transaction_type_id=1,  # Assuming 1 is the ID for Transfer
                source_account_id=source_account_id,
                destination_account_id=destination_account_id,
                amount=amount,
                status='FAILED',
                description="Potentially fraudulent transaction",
                reference_code=Transaction.generate_reference_code()
            )
            
            # Add the transaction to the database
            db.session.add(transaction)
            db.session.commit()
            
            # Update the fraud alert with the transaction ID
            alert.transaction_id = transaction.id
            db.session.commit()
            
            # Notify the user of the suspicious transaction
            self.notification_service.notify_suspicious_transaction(source_account, transaction)
        
        return {
            "is_safe": is_safe,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "reason": ", ".join(risk_factors) if risk_factors else "No risk factors detected"
        }
    
    def get_fraud_alerts(self, account_id=None, status=None):
        """
        Get fraud alerts, optionally filtered by account ID and status.
        
        Args:
            account_id: The ID of the account to filter by
            status: The status to filter by
            
        Returns:
            list: A list of fraud alerts
        """
        query = FraudAlert.query
        
        if account_id:
            query = query.filter_by(account_id=account_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(FraudAlert.created_at.desc()).all()
    
    def resolve_fraud_alert(self, alert_id, is_fraud=True):
        """
        Resolve a fraud alert.
        
        Args:
            alert_id: The ID of the alert to resolve
            is_fraud: Whether the alert is a genuine fraud or a false positive
            
        Returns:
            dict: A dictionary containing the result of the operation
        """
        alert = FraudAlert.query.get(alert_id)
        
        if not alert:
            return {"success": False, "message": "Alert not found"}
        
        if alert.status != 'OPEN':
            return {"success": False, "message": f"Alert is already {alert.status.lower()}"}
        
        # Update the alert status
        alert.status = 'RESOLVED' if is_fraud else 'FALSE_POSITIVE'
        alert.resolved_at = datetime.utcnow()
        
        # If it's a genuine fraud, freeze the account and notify the user
        if is_fraud and alert.account:
            account = alert.account
            account.status = 'FROZEN'
            account.updated_at = datetime.utcnow()
            
            # Create a notification for the account freeze
            user_id = account.user_id
            title = "Account Frozen"
            message = f"Your account {account.account_number} has been frozen due to suspicious activity. Please contact customer support."
            
            from app.models.user import Notification
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                is_read=False,
                created_at=datetime.utcnow()
            )
            
            db.session.add(notification)
        
        db.session.commit()
        
        return {"success": True, "message": "Alert resolved successfully"}
