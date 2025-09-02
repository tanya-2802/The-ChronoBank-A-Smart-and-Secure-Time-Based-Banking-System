from app.models.account import Account
from app.models.transaction import Transaction, TransactionType
from app import db
from datetime import datetime

class LegacySystemAdapter:
    """
    Adapter Pattern Implementation
    
    This class adapts legacy banking systems to work with the new time-based economy.
    """
    
    def __init__(self):
        self.time_conversion_rate = 3600  # 1 legacy currency unit = 1 hour (3600 seconds)
    
    def convert_currency_to_time(self, currency_amount):
        """
        Convert legacy currency to time.
        
        Args:
            currency_amount (float): The amount of legacy currency
            
        Returns:
            int: The equivalent amount of time in seconds
        """
        return int(currency_amount * self.time_conversion_rate)
    
    def convert_time_to_currency(self, time_amount):
        """
        Convert time to legacy currency.
        
        Args:
            time_amount (int): The amount of time in seconds
            
        Returns:
            float: The equivalent amount of legacy currency
        """
        return time_amount / self.time_conversion_rate
    
    def import_legacy_account(self, legacy_account_id, legacy_balance, user_id, account_type_name='BasicTimeAccount'):
        """
        Import a legacy account into the ChronoBank system.
        
        Args:
            legacy_account_id (str): The ID of the legacy account
            legacy_balance (float): The balance of the legacy account in legacy currency
            user_id (int): The ID of the user who owns the account
            account_type_name (str): The type of account to create
            
        Returns:
            Account: The newly created ChronoBank account
        """
        from app.patterns.creational.factory import AccountFactory
        
        # Convert legacy balance to time
        time_balance = self.convert_currency_to_time(legacy_balance)
        
        # Create a new account
        account = AccountFactory.create_account(user_id, account_type_name)
        
        # Set the initial balance
        account.balance = time_balance
        
        # Add a note about the legacy account
        description = f"Imported from legacy account {legacy_account_id}"
        
        # Get the deposit transaction type
        deposit_type = TransactionType.query.filter_by(name='Deposit').first()
        
        # Create a transaction record
        transaction = Transaction(
            transaction_type_id=deposit_type.id,
            source_account_id=None,
            destination_account_id=account.id,
            amount=time_balance,
            status='COMPLETED',
            description=description,
            reference_code=Transaction.generate_reference_code()
        )
        
        # Add to database
        db.session.add(transaction)
        db.session.commit()
        
        return account
    
    def export_to_legacy_system(self, account_id):
        """
        Export a ChronoBank account to a legacy system.
        
        Args:
            account_id (int): The ID of the ChronoBank account
            
        Returns:
            dict: A dictionary containing the legacy account details
        """
        # Get the account
        account = Account.query.get(account_id)
        
        if not account:
            raise ValueError("Account not found")
        
        # Convert time balance to legacy currency
        legacy_balance = self.convert_time_to_currency(account.balance)
        
        # Create a legacy account representation
        legacy_account = {
            "legacy_id": f"LGC-{account.account_number}",
            "balance": legacy_balance,
            "owner_name": f"{account.user.first_name} {account.user.last_name}",
            "account_type": account.account_type.name,
            "status": account.status,
            "created_at": account.created_at.isoformat()
        }
        
        return legacy_account
