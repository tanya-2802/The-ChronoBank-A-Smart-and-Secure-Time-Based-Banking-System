from app import create_app, db
from app.models.account import AccountType

def update_database():
    """Add the SavingsAccount type if it doesn't exist."""
    app = create_app()
    with app.app_context():
        # Check if SavingsAccount already exists
        savings_account = AccountType.query.filter_by(name='SavingsAccount').first()
        
        if not savings_account:
            print("Adding SavingsAccount type to the database...")
            savings_account = AccountType(
                name='SavingsAccount',
                description='High-interest account for saving time with bonus rewards',
                min_balance=3600,  # 1 hour minimum balance
                interest_rate=0.07,
                transaction_limit=3000
            )
            db.session.add(savings_account)
            db.session.commit()
            print("SavingsAccount type added successfully!")
        else:
            print("SavingsAccount type already exists in the database.")

if __name__ == '__main__':
    update_database()