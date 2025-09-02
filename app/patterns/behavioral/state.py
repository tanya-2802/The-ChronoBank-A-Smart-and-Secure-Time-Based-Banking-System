from abc import ABC, abstractmethod
from app import db
from datetime import datetime
from app.services.notification_service import NotificationService

class AccountState(ABC):
    """
    State Pattern Implementation
    
    This abstract class defines the interface for account states.
    """
    
    @abstractmethod
    def deposit(self, account, amount):
        """
        Deposit time into the account.
        
        Args:
            account: The account to deposit into
            amount: The amount of time to deposit
            
        Returns:
            bool: True if the deposit was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def withdraw(self, account, amount):
        """
        Withdraw time from the account.
        
        Args:
            account: The account to withdraw from
            amount: The amount of time to withdraw
            
        Returns:
            bool: True if the withdrawal was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def transfer(self, account, destination_account, amount):
        """
        Transfer time from the account to another account.
        
        Args:
            account: The account to transfer from
            destination_account: The account to transfer to
            amount: The amount of time to transfer
            
        Returns:
            bool: True if the transfer was successful, False otherwise
        """
        pass

class ActiveState(AccountState):
    """
    Active state implementation.
    
    This state represents an account that is active and can perform all operations.
    """
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def deposit(self, account, amount):
        """
        Deposit time into an active account.
        
        Args:
            account: The account to deposit into
            amount: The amount of time to deposit
            
        Returns:
            bool: True if the deposit was successful, False otherwise
        """
        if amount <= 0:
            return False
        
        account.balance += amount
        account.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Check if the account balance is still below the threshold after deposit
        self.notification_service.check_balance_threshold(account)
        
        return True
    
    def withdraw(self, account, amount):
        """
        Withdraw time from an active account.
        
        Args:
            account: The account to withdraw from
            amount: The amount of time to withdraw
            
        Returns:
            bool: True if the withdrawal was successful, False otherwise
        """
        if amount <= 0 or account.balance < amount:
            return False
        
        account.balance -= amount
        account.updated_at = datetime.utcnow()
        
        # Check if the account should be overdrawn
        if account.balance < account.account_type.min_balance:
            account.status = 'OVERDRAWN'
            account.state = OverdrawnState()
        
        db.session.commit()
        
        # Check if the account balance is below the threshold after withdrawal
        self.notification_service.check_balance_threshold(account)
        
        return True
    
    def transfer(self, account, destination_account, amount):
        """
        Transfer time from an active account to another account.
        
        Args:
            account: The account to transfer from
            destination_account: The account to transfer to
            amount: The amount of time to transfer
            
        Returns:
            bool: True if the transfer was successful, False otherwise
        """
        if amount <= 0 or account.balance < amount:
            return False
        
        if destination_account.status == 'FROZEN':
            return False
        
        # Manually handle the transfer instead of calling withdraw to avoid duplicate notifications
        account.balance -= amount
        account.updated_at = datetime.utcnow()
        
        # Check if the account should be overdrawn
        if account.balance < account.account_type.min_balance:
            account.status = 'OVERDRAWN'
            account.state = OverdrawnState()
        
        # Deposit to destination account
        destination_state = get_account_state(destination_account.status)
        if not destination_state.deposit(destination_account, amount):
            # Rollback the withdrawal
            account.balance += amount
            account.updated_at = datetime.utcnow()
            
            if account.status == 'OVERDRAWN' and account.balance >= account.account_type.min_balance:
                account.status = 'ACTIVE'
                account.state = ActiveState()
            
            db.session.commit()
            return False
        
        db.session.commit()
        
        # Check if the source account balance is below the threshold after transfer
        self.notification_service.check_balance_threshold(account)
        
        return True

class OverdrawnState(AccountState):
    """
    Overdrawn state implementation.
    
    This state represents an account that is overdrawn and has limited operations.
    """
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def deposit(self, account, amount):
        """
        Deposit time into an overdrawn account.
        
        Args:
            account: The account to deposit into
            amount: The amount of time to deposit
            
        Returns:
            bool: True if the deposit was successful, False otherwise
        """
        if amount <= 0:
            return False
        
        account.balance += amount
        account.updated_at = datetime.utcnow()
        
        # Check if the account should be active
        if account.balance >= account.account_type.min_balance:
            account.status = 'ACTIVE'
            account.state = ActiveState()
        
        db.session.commit()
        
        # Check if the account balance is still below the threshold after deposit
        self.notification_service.check_balance_threshold(account)
        
        return True
    
    def withdraw(self, account, amount):
        """
        Withdraw time from an overdrawn account.
        
        Args:
            account: The account to withdraw from
            amount: The amount of time to withdraw
            
        Returns:
            bool: True if the withdrawal was successful, False otherwise
        """
        # Cannot withdraw from an overdrawn account
        return False
    
    def transfer(self, account, destination_account, amount):
        """
        Transfer time from an overdrawn account to another account.
        
        Args:
            account: The account to transfer from
            destination_account: The account to transfer to
            amount: The amount of time to transfer
            
        Returns:
            bool: True if the transfer was successful, False otherwise
        """
        # Cannot transfer from an overdrawn account
        return False

class FrozenState(AccountState):
    """
    Frozen state implementation.
    
    This state represents an account that is frozen and cannot perform any operations.
    """
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def deposit(self, account, amount):
        """
        Deposit time into a frozen account.
        
        Args:
            account: The account to deposit into
            amount: The amount of time to deposit
            
        Returns:
            bool: True if the deposit was successful, False otherwise
        """
        # Cannot deposit to a frozen account
        return False
    
    def withdraw(self, account, amount):
        """
        Withdraw time from a frozen account.
        
        Args:
            account: The account to withdraw from
            amount: The amount of time to withdraw
            
        Returns:
            bool: True if the withdrawal was successful, False otherwise
        """
        # Cannot withdraw from a frozen account
        return False
    
    def transfer(self, account, destination_account, amount):
        """
        Transfer time from a frozen account to another account.
        
        Args:
            account: The account to transfer from
            destination_account: The account to transfer to
            amount: The amount of time to transfer
            
        Returns:
            bool: True if the transfer was successful, False otherwise
        """
        # Cannot transfer from a frozen account
        return False

def get_account_state(status):
    """
    Get the account state based on the status.
    
    Args:
        status: The status of the account
        
    Returns:
        AccountState: The account state
    """
    states = {
        'ACTIVE': ActiveState(),
        'OVERDRAWN': OverdrawnState(),
        'FROZEN': FrozenState()
    }
    
    return states.get(status, ActiveState())
