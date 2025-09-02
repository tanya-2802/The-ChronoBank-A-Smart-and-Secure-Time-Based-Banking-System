from app.models.account import Account, AccountType
from app import db

class AccountFactory:
    """
    Factory Pattern Implementation
    
    This class is responsible for creating different types of accounts
    based on the account type requested.
    """
    
    @staticmethod
    def create_account(user_id, account_type_name):
        """
        Create a new account of the specified type for the given user.
        
        Args:
            user_id (int): The ID of the user who owns the account
            account_type_name (str): The name of the account type to create
            
        Returns:
            Account: The newly created account
        
        Raises:
            ValueError: If the account type is not found
        """
        # Find the account type
        account_type = AccountType.query.filter_by(name=account_type_name).first()
        
        if not account_type:
            raise ValueError(f"Account type '{account_type_name}' not found")
        
        # Create a new account
        account = Account(
            user_id=user_id,
            account_type_id=account_type.id,
            account_number=Account.generate_account_number(),
            balance=0,
            status='ACTIVE'
        )
        
        # Add to database
        db.session.add(account)
        db.session.commit()
        
        return account
