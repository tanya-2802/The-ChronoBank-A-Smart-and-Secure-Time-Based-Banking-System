from functools import wraps
from app.models.transaction import Transaction
from app import db
from datetime import datetime

class TransactionDecorator:
    """
    Decorator Pattern Implementation
    
    This class allows dynamic transaction rules, such as time tax deductions
    or bonus time rewards.
    """
    
    @staticmethod
    def apply_tax(tax_percentage):
        """
        Decorator to apply a tax to a transaction.
        
        Args:
            tax_percentage (float): The percentage of tax to apply (0-100)
            
        Returns:
            function: The decorated function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Call the original function
                result = func(*args, **kwargs)
                
                # If the transaction was successful, apply the tax
                if result.get("success", False) and "transaction_id" in result:
                    transaction_id = result["transaction_id"]
                    transaction = Transaction.query.get(transaction_id)
                    
                    if transaction and transaction.transaction_type.name == 'Transfer':
                        # Calculate the tax amount
                        tax_amount = int(transaction.amount * (tax_percentage / 100))
                        
                        # Update the transaction description
                        transaction.description += f" (Tax: {tax_amount} seconds)"
                        
                        # If it's a transfer, deduct the tax from the destination account
                        if transaction.destination_account_id:
                            destination_account = transaction.destination_account
                            
                            # Only deduct if there's enough balance
                            if destination_account.balance >= tax_amount:
                                try:
                                    # Deduct the tax
                                    destination_account.withdraw(tax_amount)
                                    
                                    # Create a new transaction for the tax
                                    from app.patterns.creational.singleton import TransactionLedger
                                    ledger = TransactionLedger()
                                    
                                    # Get the fee transaction type
                                    from app.models.transaction import TransactionType
                                    fee_type = TransactionType.query.filter_by(name='Fee').first()
                                    
                                    if not fee_type:
                                        # If Fee type doesn't exist, use the first available type
                                        fee_type = TransactionType.query.first()
                                    
                                    # Record the tax transaction
                                    tax_transaction = Transaction(
                                        transaction_type_id=fee_type.id,
                                        source_account_id=destination_account.id,
                                        destination_account_id=None,
                                        amount=tax_amount,
                                        status='COMPLETED',
                                        description=f"Tax on transaction {transaction.reference_code}",
                                        reference_code=Transaction.generate_reference_code()
                                    )
                                    
                                    # Add to database
                                    db.session.add(tax_transaction)
                                    db.session.commit()
                                    
                                    # Add tax transaction ID to the result
                                    result["tax_transaction_id"] = tax_transaction.id
                                    result["tax_amount"] = tax_amount
                                    
                                    print(f"Tax of {tax_amount} seconds applied to transaction {transaction.reference_code}")
                                except Exception as e:
                                    print(f"Error applying tax: {str(e)}")
                                    db.session.rollback()
                        
                        db.session.commit()
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def apply_bonus(bonus_percentage):
        """
        Decorator to apply a bonus to a transaction.
        
        Args:
            bonus_percentage (float): The percentage of bonus to apply (0-100)
            
        Returns:
            function: The decorated function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Call the original function
                result = func(*args, **kwargs)
                
                # If the transaction was successful, apply the bonus
                if result.get("success", False) and "transaction_id" in result:
                    transaction_id = result["transaction_id"]
                    transaction = Transaction.query.get(transaction_id)
                    
                    if transaction and transaction.transaction_type.name == 'Deposit':
                        # Calculate the bonus amount
                        bonus_amount = int(transaction.amount * (bonus_percentage / 100))
                        
                        # Update the transaction description
                        transaction.description += f" (Bonus: {bonus_amount} seconds)"
                        
                        # If it's a deposit, add the bonus to the destination account
                        if transaction.destination_account_id:
                            destination_account = transaction.destination_account
                            
                            try:
                                # Add the bonus
                                destination_account.deposit(bonus_amount)
                                
                                # Get the deposit transaction type
                                from app.models.transaction import TransactionType
                                deposit_type = TransactionType.query.filter_by(name='Deposit').first()
                                
                                if not deposit_type:
                                    # If Deposit type doesn't exist, use the first available type
                                    deposit_type = TransactionType.query.first()
                                
                                # Create a new transaction for the bonus
                                bonus_transaction = Transaction(
                                    transaction_type_id=deposit_type.id,
                                    source_account_id=None,
                                    destination_account_id=destination_account.id,
                                    amount=bonus_amount,
                                    status='COMPLETED',
                                    description=f"Bonus on transaction {transaction.reference_code}",
                                    reference_code=Transaction.generate_reference_code()
                                )
                                
                                # Add to database
                                db.session.add(bonus_transaction)
                                db.session.commit()
                                
                                # Add bonus transaction ID to the result
                                result["bonus_transaction_id"] = bonus_transaction.id
                                result["bonus_amount"] = bonus_amount
                                
                                print(f"Bonus of {bonus_amount} seconds applied to transaction {transaction.reference_code}")
                            except Exception as e:
                                print(f"Error applying bonus: {str(e)}")
                                db.session.rollback()
                        
                        db.session.commit()
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def transaction_logging(func):
        """
        Decorator to log transaction details.
        
        Args:
            func: The function to decorate
            
        Returns:
            function: The decorated function
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get the start time
            start_time = datetime.utcnow()
            
            # Call the original function
            result = func(*args, **kwargs)
            
            # Calculate the execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Log the transaction details
            if result.get("success", False) and "transaction_id" in result:
                transaction_id = result["transaction_id"]
                
                # Create an audit log entry
                from app.models.transaction import AuditLog
                audit_log = AuditLog(
                    user_id=kwargs.get("user_id"),
                    action="TRANSACTION_EXECUTED",
                    entity_type="Transaction",
                    entity_id=transaction_id,
                    details=f"Transaction executed in {execution_time:.2f} seconds",
                    ip_address=kwargs.get("ip_address"),
                    created_at=datetime.utcnow()
                )
                
                db.session.add(audit_log)
                db.session.commit()
            
            return result
        return wrapper
